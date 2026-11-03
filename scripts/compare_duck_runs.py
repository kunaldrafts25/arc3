"""Compare completed, single-pass public gameplay without inferring hidden scores."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_duck_run import summarize


def load_run(directory, expected_games):
    path = Path(directory) / 'benchmark.json'
    data = path.read_bytes()
    raw = json.loads(data)
    if raw['n_passes'] != 1 or not raw.get('end_time'):
        raise ValueError('Require a completed single-pass benchmark')
    duration = (datetime.fromisoformat(raw['end_time']) -
                datetime.fromisoformat(raw['start_time'])).total_seconds()
    if duration <= 0:
        raise ValueError('Invalid benchmark duration')
    rows = []
    for run in raw['game_runs']:
        if sum(run['actions_per_level']) != len(run['history']):
            raise ValueError('Action history does not match level accounting')
        rows.append(dict(game_id=run['game_id'], state=run['state'],
                         levels_completed=run['levels_completed'],
                         total_levels=run['number_of_levels'],
                         actions=len(run['history']), score=run['final_score'],
                         generated_tokens=sum(a['generated_tokens'] for a in run['history']) +
                         run['final_generated_tokens']))
    indexed = {row['game_id']: row for row in rows}
    if len(indexed) != len(rows) or len(rows) != expected_games:
        raise ValueError('Require the expected number of unique games')
    summary = summarize(rows)
    if not summary['model_gameplay_verified']:
        raise ValueError('Substantive gameplay missing: ' + '; '.join(summary['problems']))
    return dict(path=str(path), sha256=sha256(data).hexdigest(),
                elapsed_seconds=duration, summary=summary), indexed, raw.get('game_weights')


def compare(control, candidate, expected_games=25, duration_tolerance=120):
    if expected_games < 1 or duration_tolerance < 0:
        raise ValueError('Invalid comparison constraints')
    before, old, old_weights = load_run(control, expected_games)
    after, new, new_weights = load_run(candidate, expected_games)
    if old.keys() != new.keys():
        raise ValueError('Game sets differ')
    if old_weights != new_weights:
        raise ValueError('Game weights differ')
    if abs(before['elapsed_seconds'] - after['elapsed_seconds']) > duration_tolerance:
        raise ValueError('Benchmark durations differ beyond the comparison tolerance')
    per_game = []
    for game_id in sorted(old):
        a, b = old[game_id], new[game_id]
        if a['total_levels'] != b['total_levels']:
            raise ValueError('Level counts differ for ' + game_id)
        deltas = {key: b[key] - a[key] for key in
                  ('score', 'levels_completed', 'actions', 'generated_tokens')}
        per_game.append(dict(game_id=game_id, control=a, candidate=b, delta=deltas))
    keys = ('mean_public_score', 'levels', 'full_wins', 'generated_tokens')
    return dict(control=before, candidate=after,
                delta={key: after['summary'][key] - before['summary'][key] for key in keys},
                games_improved=sum(row['delta']['score'] > 0 for row in per_game),
                games_worsened=sum(row['delta']['score'] < 0 for row in per_game),
                games_tied=sum(row['delta']['score'] == 0 for row in per_game),
                per_game=per_game,
                boundary=('One stochastic public run per configuration. No causal significance, '
                          'hidden-score prediction or automatic promotion. Matching elapsed time '
                          'does not prove matched post-readiness budgets: inspect notebook sources '
                          'and startup logs separately. Mechanical helper adoption is separate evidence.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('control', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--expected-games', type=int, default=25)
    parser.add_argument('--duration-tolerance', type=float, default=120)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.control, args.candidate, args.expected_games, args.duration_tolerance)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'per_game'}, indent=2))


if __name__ == '__main__':
    main()
