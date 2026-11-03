"""Audit prediction evidence without counting archived verdicts twice.

Use only actual resolution events for forecast checks. Superseded stores contain
copies of old evidence and establish version changes, not additional checks.
"""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


def analyze(directory, origin='unknown'):
    if origin not in ('unknown','model','programmatic'):
        raise ValueError('Origin must be explicit; it is not inferred from tool availability')
    stores = sorted(directory.rglob('*.prediction.json'))
    event_files = sorted(directory.rglob('*.prediction.events.jsonl'))
    games = {}
    hashes = {}
    total = Counter()
    errors = []
    formats = set()
    for path in stores:
        relative = str(path.relative_to(directory)).replace('\\','/')
        hashes[relative] = sha256(path.read_bytes()).hexdigest()
        try:
            store = json.loads(path.read_text(encoding='utf-8'))
        except ValueError:
            errors.append(dict(path=relative,reason='unreadable store'))
            continue
        ledger = store.get('ledger')
        if ledger is None:
            continue
        key = relative[:-len('.prediction.json')]
        row = dict(store=relative,events=None,counts=Counter(),feature_queries=Counter(),
                   last_question=store['question'],last_models=ledger['models'])
        row['counts']['started_game_sessions'] = 1
        row['counts']['hypothesis_versions_observed'] = 1
        row['counts']['pending_forecasts_at_snapshot'] = int(ledger.get('pending') is not None)
        row['counts']['retained_counterexamples_at_snapshot'] = sum('counterexample' in m for m in ledger['models'].values())
        row['counts']['invalidated_scopes_at_snapshot'] = int(store.get('invalidated',False))
        row['feature_queries'].update(q[0] for q in store['features'].values())
        games[key] = row
    for path in event_files:
        relative = str(path.relative_to(directory)).replace('\\','/')
        hashes[relative] = sha256(path.read_bytes()).hexdigest()
        key = relative[:-len('.prediction.events.jsonl')]
        if key not in games:
            games[key] = dict(store=None,events=None,counts=Counter(),feature_queries=Counter(),
                              last_question=None,last_models=None)
        row = games[key]
        row['events'] = relative
        pending = dispatched = None
        last_revision = -1
        explicit_starts = 0
        for number,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                errors.append(dict(path=relative,line=number,reason='unreadable event'))
                continue
            format_version = event.get('format',1)
            formats.add(format_version)
            if format_version == 2:
                if event['revision'] < last_revision:
                    errors.append(dict(path=relative,line=number,reason='event revisions went backwards'))
                last_revision = event['revision']
                kind = event['event']
                if kind == 'start':
                    explicit_starts += 1
                    pending = dispatched = None
                    continue
                if kind == 'forecast':
                    if pending is not None:
                        errors.append(dict(path=relative,line=number,reason='pending forecast overwritten'))
                    pending = event
                    dispatched = None
                    row['counts']['frozen_forecasts_logged'] += 1
                    discriminating = 0
                    known_predictions = 0
                    for forecasts in event['pending']['forecasts'].values():
                        known = [v for v in forecasts.values() if v]
                        known_predictions += len(known)
                        if any(any(json.dumps(a[k],sort_keys=True) != json.dumps(b[k],sort_keys=True)
                                   for k in a.keys() & b.keys()) for a,b in combinations(known,2)):
                            discriminating += 1
                    row['counts']['forecast_actions_with_predicted_disagreement'] += discriminating
                    row['counts']['forecasts_with_predicted_disagreement'] += int(discriminating>0)
                    row['counts']['forecasts_with_no_known_prediction'] += int(known_predictions==0)
                    continue
                if kind == 'dispatch':
                    if pending is None or event['pending'] != pending['pending']:
                        errors.append(dict(path=relative,line=number,reason='dispatch lacks identical earlier frozen forecast'))
                    elif (event['probe'] not in pending['probes']
                          or event['action'] != pending['probes'][event['probe']]['action']):
                        errors.append(dict(path=relative,line=number,reason='dispatch action differs from frozen probe'))
                    dispatched = event
                    row['counts']['dispatch_events'] += 1
                    continue
                if kind == 'cancel':
                    row['counts']['cancel_events'] += 1
                    pending = dispatched = None
                    continue
                if kind == 'resolve':
                    evidence = event['evidence']
                    if (pending is None or dispatched is None or event['step'] != pending['pending']['step']+1
                            or event['level'] != pending['pending']['level']
                            or evidence['action'] != dispatched['probe']
                            or evidence['verdicts'] != event['outcome']['verdicts']):
                        errors.append(dict(path=relative,line=number,reason='resolution lacks matching prospective dispatch/evidence'))
                    else:
                        predictions = pending['pending']['forecasts'][dispatched['probe']]
                        for name,verdict in event['outcome']['verdicts'].items():
                            prediction = predictions.get(name)
                            observed = evidence['observed']
                            if prediction is None:
                                expected = 'unknown'
                            else:
                                common = prediction.keys() & observed.keys()
                                different = any(json.dumps(prediction[k],sort_keys=True) != json.dumps(observed[k],sort_keys=True) for k in common)
                                expected = 'contradicted' if different else ('consistent' if common == prediction.keys() else 'insufficient_observation')
                            if verdict['verdict'] != expected:
                                errors.append(dict(path=relative,line=number,reason='verdict disagrees with frozen forecast and measured features'))
                    pending = dispatched = None
                elif kind != 'superseded':
                    raise ValueError(f'Unknown V2 event kind at {relative}:{number}')
            elif format_version != 1:
                raise ValueError('Unsupported prediction event format')
            if event.get('event') == 'superseded':
                # Archive is the old version, not a new set of resolutions.
                old = event['store']
                row['counts']['hypothesis_versions_observed'] += 1
                row['feature_queries'].update(q[0] for q in old['features'].values())
                if (old.get('last_outcome') or {}).get('needs_new_hypotheses'):
                    row['counts']['new_version_after_all_candidates_refuted'] += 1
                if (old.get('last_outcome') or {}).get('checked') is False:
                    row['counts']['versions_ending_with_unchecked_outcome'] += 1
                continue
            if format_version == 1 and set(event) != {'question','level','step','outcome'}:
                raise ValueError(f'Unknown prediction event schema at {relative}:{number}')
            outcome = event['outcome']
            if not outcome.get('checked'):
                raise ValueError('Resolution events must contain checked outcomes')
            row['counts']['actual_resolution_events'] += 1
            row['counts']['all_candidates_refuted_events'] += int(outcome['needs_new_hypotheses'])
            for verdict in outcome['verdicts'].values():
                name = verdict['verdict']
                if name not in ('consistent','contradicted','unknown','insufficient_observation'):
                    raise ValueError('Unknown prediction verdict')
                row['counts']['hypothesis_'+name] += 1
        if explicit_starts:
            # Explicit V2 starts are exact; V1 snapshot/archive counts are only
            # a lower bound when mixed with V2 in the same file.
            row['counts']['hypothesis_versions_observed'] = max(explicit_starts,row['counts']['hypothesis_versions_observed'])
    for row in games.values():
        total.update(row['counts'])
        row['counts'] = dict(row['counts'])
        row['feature_queries'] = dict(row['feature_queries'])
    return dict(source_origin=origin,session_store_files=len(stores),event_files=len(event_files),
        counts=dict(total),per_session=games,source_sha256=hashes,
        event_formats=sorted(formats),audit_errors=errors,
        frozen_forecast_archive_complete=formats == {2} and not errors,
        boundary='Counts establish use and measured checks only. Model origin must be established separately from real gameplay/provenance; programmatic replay is not LLM adoption. Superseded archives are not counted as new checks. V1 events do not retain all original forecasts/cancellations; V2 explicitly logs forecast-before-dispatch and measured resolution, which this audit checks for internal consistency. These logs are not an independent game-state oracle. Matching selected features is not a correct object identity, rule, goal, better decision or score improvement. New version after refutation is an observed sequence, not proof of causal learning or successful repair.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--origin',choices=['unknown','model','programmatic'],default='unknown')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = analyze(args.directory,args.origin)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('per_session','source_sha256')},indent=2))
