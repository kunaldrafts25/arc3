"""Validate coverage and summarize the frozen public v0.2 comparison."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]


def metrics(rows):
    return dict(runs=len(rows), full_wins=sum(bool(r['completion_status']) for r in rows),
                completed_levels=sum(r['levels_completed'] for r in rows),
                mean_official_score=mean(r['official_score_if_available'] for r in rows),
                median_runtime_seconds=median(r['runtime_seconds'] for r in rows),
                exceptions=sum(bool(r['exceptions']) for r in rows))


def read(name):
    path = ROOT / 'reports/v02' / (name + '.jsonl')
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    digest = sha256(path.with_suffix('.source.json').read_bytes()).hexdigest()
    assert all(r['source_sha256'] == digest for r in rows), 'Source digest mismatch'
    assert not any(r['exceptions'] for r in rows), 'Agent/environment exceptions'
    assert all(r['official_score_if_available'] is not None for r in rows)
    assert len({(r['game_id'],r['seed']) for r in rows}) == len(rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    candidate, baseline = read('release-candidate'), read('baseline-300')
    games = {r['game_id'] for r in baseline}
    expected_base = {(g, s) for g in games for s in range(3)}
    expected_candidate = {(g, s) for g in games for s in range(5)}
    complete = (len(games)==25 and {(r['game_id'],r['seed']) for r in baseline} == expected_base
                and {(r['game_id'],r['seed']) for r in candidate} == expected_candidate)
    if args.require_complete and not complete:
        raise RuntimeError(f'Incomplete coverage: candidate {len(candidate)}/125, baseline {len(baseline)}/75')
    if not complete:
        print(json.dumps(dict(complete=False, candidate_runs=len(candidate), baseline_runs=len(baseline))))
        return
    paired = [r for r in candidate if r['seed'] < 3]
    heldout = [r for r in candidate if r['seed'] >= 3]
    assert {r['action_count'] for r in baseline} <= {300}
    assert all(r['action_count'] <= 300 for r in candidate)
    per_game = defaultdict(dict)
    for policy, rows in (('baseline',baseline),('candidate',paired)):
        for game in sorted(games):
            per_game[game][policy] = metrics([r for r in rows if r['game_id']==game])
    result = dict(complete=True, action_cap=300, environment_seed=0,
                  baseline=metrics(baseline), candidate_paired=metrics(paired),
                  candidate_additional_seeds=metrics(heldout), candidate_all=metrics(candidate),
                  per_game=per_game,
                  limitations=['Public development games only; no hidden score inference.',
                               'Additional seeds change policy randomness, not game layout.',
                               'Candidate was developed using public games; these are not unseen tasks.'])
    path = ROOT/'reports/v02/comparison.json'
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key!='per_game'},indent=2))


if __name__ == '__main__':
    main()
