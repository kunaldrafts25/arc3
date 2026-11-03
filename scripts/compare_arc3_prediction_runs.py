"""Compare the frozen public pair; never promote or submit automatically."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from statistics import mean

from scripts.analyze_duck_run import analyze
from scripts.audit_general_run import score

ROOT = Path(__file__).resolve().parents[1]


def checkpoint(raw, seconds):
    start = datetime.fromisoformat(raw['start_time'])
    result = {}
    for game in raw['game_runs']:
        if sum(game['actions_per_level']) != len(game['history']):
            raise ValueError('Action history cannot locate level completions')
        if abs(score(game['actions_per_level'], game['base_actions_per_level'],
                     game['levels_completed'])-game['final_score']) > 1e-8:
            raise ValueError('Recorded final score does not reconcile')
        offset = (datetime.fromisoformat(game['started_at'])-start).total_seconds()
        times=[a['wallclock_seconds'] for a in game['history']]
        if any(t<0 for t in times) or times!=sorted(times):
            raise ValueError('Action times must identify a nonnegative chronological prefix')
        selected = [a for a in game['history'] if offset+a['wallclock_seconds'] <= seconds]
        position = levels = 0
        for count in game['actions_per_level'][:game['levels_completed']]:
            if count <= 0:
                raise ValueError('Completed level has no actions')
            position += count
            levels += int(position <= len(selected))
        tokens = sum(a['generated_tokens'] for a in selected)
        if offset+game['final_wallclock_seconds'] <= seconds:
            tokens += game['final_generated_tokens']
        result[game['game_id']] = dict(levels=levels,actions=len(selected),generated_tokens=tokens,
            score=score(game['actions_per_level'],game['base_actions_per_level'],levels))
    if len(result) != len(raw['game_runs']):
        raise ValueError('Duplicate games cannot be paired')
    return result


def usage(directory):
    tools, metadata_collisions, queries = Counter(), 0, 0
    per_game = []
    for path in sorted(directory.rglob('*.inspection.events.jsonl')):
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        duplicates = len(rows)-len({json.dumps(row,sort_keys=True) for row in rows})
        tools.update(row['tool'] for row in rows)
        queries += len(rows)
        metadata_collisions += duplicates
        per_game.append(dict(game=path.name.split('_p0_')[0],queries=len(rows),
                             repeated_identical_event_metadata=duplicates))
    replies = chars = no_action_prompts = 0
    for path in directory.rglob('transcripts/*.txt'):
        text = path.read_text(encoding='utf-8')
        lengths = [int(x) for x in re.findall(r'^reasoning_chars: (\d+)$',text,re.M)]
        replies += len(lengths)
        chars += sum(lengths)
        no_action_prompts += text.count('Your last python snippet executed NO actions (')
    return dict(inspection_tools=dict(tools),inspection_queries=queries,
        repeated_identical_event_metadata=metadata_collisions,inspection_per_game=per_game,
        transcript_replies=replies,reasoning_characters=chars,no_action_followup_prompts=no_action_prompts,
        boundary='read_cells telemetry omits requested coordinates, so identical event metadata does not establish an identical query. Repeated measurements may also occur inside one efficient computation. No-action turns can perform useful search. These counts do not identify wasted inference or establish causality.')


def compare(control, candidate, candidate_variant='prediction'):
    if candidate_variant not in ('prediction','thinkingcap','qwen27'):
        raise ValueError('Only frozen prediction, ThinkingCap or 27B comparisons are supported')
    directories = {'control':control,candidate_variant:candidate}
    plan = json.loads((ROOT/'reports/arc3/prediction-ablation/plan.json').read_text())
    variants=plan['variants']
    if candidate_variant in ('thinkingcap','qwen27'):
        package=ROOT/('notebooks/thinkingcap_matched_candidate' if candidate_variant=='thinkingcap' else 'notebooks/qwen27_matched_baseline')
        manifest=json.loads((package/'manifest.json').read_text())
        variants=[plan['variants'][0],dict(variant=candidate_variant,kernel=manifest['kernel'],
            package=str(package.relative_to(ROOT)),files=manifest['files'])]
        original=json.loads((ROOT/variants[0]['package']/'submission.ipynb').read_text())
        changed=json.loads((package/'submission.ipynb').read_text())
        if (len(original['cells'])!=len(changed['cells'])
                or [i for i,(a,b) in enumerate(zip(original['cells'],changed['cells'])) if a!=b]!=(
                    [0,6] if candidate_variant=='thinkingcap' else [0,6,14,22])):
            raise ValueError('Checkpoint comparison changed additional serving or gameplay cells')
    provenance, raw, summaries, hashes = {}, {}, {}, {}
    for variant in variants:
        name = variant['variant']
        directory = directories[name]
        launch = json.loads((directory/'launch.json').read_text())
        if (launch['phase'] != 'accepted' or launch['kernel'] != variant['kernel']
                or launch['files'] != variant['files'] or launch['hard_session_timeout_seconds'] != 7200):
            raise ValueError('Frozen exact launch and two-hour limit required')
        package = ROOT/variant['package']
        for filename,digest in variant['files'].items():
            if sha256((package/filename).read_bytes()).hexdigest() != digest:
                raise ValueError('Frozen package changed')
        provenance[name] = json.loads((package/'provenance.json').read_text())
        installed=json.loads((directory/'hydra_inspection_extension.json').read_text())
        if installed!=provenance[name]['inspection_extension']:
            raise ValueError('Actual inspection installation differs from frozen provenance')
        if name in ('thinkingcap','qwen27'):
            actual=json.loads((directory/'hydra_model_candidate.json').read_text())
            if actual!=provenance[name]:
                raise ValueError('Actual checkpoint preflight/provenance differs from frozen package')
        lifecycle = json.loads((directory/'hydra_lifecycle.json').read_text())
        if lifecycle['phase'] != 'run_finished' or lifecycle.get('error'):
            raise ValueError('Successful model/game lifecycle required')
        summaries[name] = analyze(directory)
        if not summaries[name]['model_gameplay_verified'] or summaries[name]['games'] != 25:
            raise ValueError('Substantive model gameplay on all 25 games required')
        path = directory/'benchmark.json'
        raw[name] = json.loads(path.read_text(encoding='utf-8'))
        hashes[name] = sha256(path.read_bytes()).hexdigest()
    for field in ('source_sha256','source_code_sha256','notebook_wall_budget_seconds',
                  'public_runtime_seconds','public_deadline_includes_startup','verified_planning_sha256',
                  'inspection_source_manifest'):
        if provenance['control'][field] != provenance[candidate_variant][field]:
            raise ValueError('Unmatched frozen configuration: '+field)
    durations = {name:(datetime.fromisoformat(run['end_time'])-datetime.fromisoformat(run['start_time'])).total_seconds()
                 for name,run in raw.items()}
    if min(durations.values()) <= 0:
        raise ValueError('Invalid gameplay duration')
    common = min(durations.values())
    checkpoints = {name:checkpoint(run,common) for name,run in raw.items()}
    if checkpoints['control'].keys() != checkpoints[candidate_variant].keys():
        raise ValueError('Different game sets')
    deltas = []
    final = {name:{g['game_id']:g for g in run['game_runs']} for name,run in raw.items()}
    for game in sorted(checkpoints['control']):
        before, after = (checkpoints[name][game] for name in ('control',candidate_variant))
        deltas.append(dict(game=game,control=before,**{candidate_variant:after},
            common_elapsed_score_delta=after['score']-before['score'],
            final_score_delta=final[candidate_variant][game]['final_score']-final['control'][game]['final_score']))
    adoption = json.loads((candidate/'prediction-adoption.json').read_text())
    if adoption['source_origin'] != 'model' or adoption['audit_errors']:
        raise ValueError('Prediction event audit missing model origin or has inconsistencies')
    costs={}
    serving={}
    for name,run in raw.items():
        actions=sum(len(g['history']) for g in run['game_runs'])
        ceiling=mean(100*g['levels_completed']*(g['levels_completed']+1)/
            (g['number_of_levels']*(g['number_of_levels']+1)) for g in run['game_runs'])
        tail=0
        for g in run['game_runs']:
            if g['levels_completed']<g['number_of_levels']:
                last=sum(g['actions_per_level'][:g['levels_completed']])
                tail+=sum(a['generated_tokens'] for a in g['history'][last:])+g['final_generated_tokens']
        costs[name]=dict(actions=actions,completed_level_score_ceiling=ceiling,
            mean_action_efficiency_gap=ceiling-summaries[name]['mean_public_score'],
            generation_after_last_completion_on_unfinished_games=tail)
        path=directories[name]/'serving-analysis.json'
        serving[name]=json.loads(path.read_text()) if path.exists() else None
    return dict(checked_at=datetime.now(timezone.utc).isoformat(),candidate_variant=candidate_variant,benchmark_sha256=hashes,
        summaries=summaries,gameplay_seconds=durations,common_gameplay_seconds=common,
        common_elapsed_mean_score={name:mean(g['score'] for g in games.values()) for name,games in checkpoints.items()},
        final_mean_score_delta=summaries[candidate_variant]['mean_public_score']-summaries['control']['mean_public_score'],
        common_elapsed_mean_score_delta=mean(g['common_elapsed_score_delta'] for g in deltas),
        games_improved=sum(g['final_score_delta']>1e-8 for g in deltas),
        games_regressed=sum(g['final_score_delta']<-1e-8 for g in deltas),
        games_unchanged=sum(abs(g['final_score_delta'])<=1e-8 for g in deltas),
        per_game=sorted(deltas,key=lambda g:g['final_score_delta']),prediction_adoption=adoption,
        costs=costs,serving=serving,
        usage={name:usage(directory) for name,directory in directories.items()},
        boundary=('One stochastic public pair with frozen common components. '
            + ('ThinkingCap changes the target checkpoint bundle, quantization calibration and shard layout; this does not isolate training alone. '
               if candidate_variant == 'thinkingcap' else
               '27B changes target, draft and model-specific serving capacity/backends. This is a complete deployment comparison, not an isolated model-quality or training effect. '
               if candidate_variant == 'qwen27' else
               'The prediction variant adds an optional extension and guidance; installed tools do not establish adoption or causal benefit. ')
            + 'Final scores reflect the same total notebook cap, including startup. Common-gameplay truncation is descriptive and does not restore identical scheduling, inference budgets, random draws or interrupted turns. Unsuccessful tail generation can include useful exploration. No hidden score estimate, significance claim, automatic promotion or submission. Human baselines are used only by this offline researcher audit and never supplied to the agent.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control',type=Path,default=ROOT/'reports/kaggle/prediction-matched-control-v1')
    parser.add_argument('--prediction',type=Path,default=ROOT/'reports/kaggle/prediction-matched-prediction-v1')
    parser.add_argument('--candidate-variant',choices=('prediction','thinkingcap','qwen27'),default='prediction')
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    candidate=args.candidate or (ROOT/'reports/kaggle/thinkingcap-matched-v1' if args.candidate_variant=='thinkingcap' else ROOT/'reports/kaggle/qwen27-matched-baseline-v1' if args.candidate_variant=='qwen27' else args.prediction)
    report = compare(args.control,candidate,args.candidate_variant)
    output=args.output or ROOT/('reports/arc3/thinkingcap-comparison/comparison.json' if args.candidate_variant=='thinkingcap' else 'reports/arc3/qwen27-baseline/comparison.json' if args.candidate_variant=='qwen27' else 'reports/arc3/prediction-ablation/comparison.json')
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('per_game','usage','prediction_adoption','summaries','serving')},indent=2))
