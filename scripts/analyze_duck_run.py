"""Audit actual model-gameplay evidence from a completed public notebook run."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from statistics import mean


def summarize(rows):
    if not rows:
        raise ValueError('No gameplay records')
    problems = []
    for row in rows:
        # A warmup RESET can happen before the model is ready. An action count
        # alone therefore cannot establish that inference/gameplay worked.
        if row['state'] in ('crashed','not_started'):
            problems.append(f"{row['game_id']}: {row['state']}")
        if row['actions'] <= 1 or row['generated_tokens'] <= 0:
            problems.append(f"{row['game_id']}: no substantive model-driven gameplay")
        if row['score'] is None:
            problems.append(f"{row['game_id']}: score unavailable")
    result = dict(model_gameplay_verified=not problems, problems=problems,
                  games=len(rows), levels=sum(r['levels_completed'] for r in rows),
                  full_wins=sum(r['total_levels']>0 and r['levels_completed']==r['total_levels'] for r in rows),
                  mean_public_score=mean(r['score'] for r in rows) if all(r['score'] is not None for r in rows) else None,
                  generated_tokens=sum(r['generated_tokens'] for r in rows),
                  notes={r['game_id']:r['note'] for r in rows if r.get('note')},
                  boundary='Public development gameplay only. Not a hidden score or proof of the 71-point goal.')
    return result


def reconcile_tokens(rows, runs):
    rows = [dict(row) for row in rows]
    corrections = []
    indexed = {r['game_id']:r for r in runs}
    if len(indexed) != len(runs):
        raise ValueError('Multiple passes require pass-aware matching')
    for row in rows:
        run = indexed[row['game_id']]
        total = sum(a['generated_tokens'] for a in run['history'])+run['final_generated_tokens']
        if total != row['generated_tokens']:
            corrections.append(dict(game_id=row['game_id'],reported_tokens=row['generated_tokens'],
                                    reconstructed_tokens=total))
            row['generated_tokens'] = total
    return rows, corrections


def analyze(directory):
    rows = json.loads((directory/'hydra_model_summary.json').read_text(encoding='utf-8'))
    # TAAF's final_generated_tokens means only the final no-action turn, not
    # total generation. Reconstruct v1 reporter totals from the raw benchmark.
    benchmark = directory/'benchmark.json'
    corrections = []
    if benchmark.exists():
        raw = json.loads(benchmark.read_text(encoding='utf-8'))
        runs = raw['game_runs']
        rows, corrections = reconcile_tokens(rows, runs)
    result = summarize(rows)
    result['token_accounting_corrections'] = corrections
    result['token_accounting_basis'] = 'Action-record generation plus terminal no-action generation; cancellation notes may include additional uncharged generation.'
    if benchmark.exists():
        completion_times=[]
        for run in runs:
            if sum(run['actions_per_level'])!=len(run['history']):
                raise ValueError('Action counts cannot locate level completions')
            offset=(datetime.fromisoformat(run['started_at'])-datetime.fromisoformat(raw['start_time'])).total_seconds()
            position=0
            for count in run['actions_per_level'][:run['levels_completed']]:
                if count<=0:
                    raise ValueError('Completed level has no recorded action')
                position+=count
                completion_times.append(offset+run['history'][position-1]['wallclock_seconds'])
        result['public_level_completions_by_elapsed_seconds']={str(t):sum(x<=t for x in completion_times) for t in (1800,3600,5400,7200)}
    (directory/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    args = parser.parse_args()
    result = analyze(args.directory)
    print(json.dumps(result,indent=2))
    if not result['model_gameplay_verified']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
