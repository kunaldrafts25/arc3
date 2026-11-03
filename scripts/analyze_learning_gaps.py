"""Measure stalled inference and explicit belief revisions in saved public runs."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / 'reports/kaggle/general-learner-v1/benchmark.json'
    benchmark = json.loads(source.read_text(encoding='utf-8'))
    games = []
    for game in benchmark['game_runs']:
        total = sum(a['generated_tokens'] for a in game['history']) + game['final_generated_tokens']
        unfinished = game['levels_completed'] < game['number_of_levels']
        last_completion = sum(game['actions_per_level'][:game['levels_completed']])
        tail = (sum(a['generated_tokens'] for a in game['history'][last_completion:])
                + game['final_generated_tokens']) if unfinished else 0
        games.append(dict(game_id=game['game_id'], levels_completed=game['levels_completed'],
                          total_levels=game['number_of_levels'], generated_tokens=total,
                          unfinished_tail_tokens=tail))
    statuses = Counter()
    revisions = Counter()
    events = 0
    manifests = {}
    directory = ROOT / 'reference/kaggle/general-learner-v1/artifacts'
    paths = sorted(directory.glob('*.study.events.jsonl'))
    if {p.name.split('_p0_')[0] for p in paths} != {g['game_id'] for g in games}:
        raise ValueError('Memory evidence must cover every recorded game')
    for path in paths:
        manifests[path.name] = sha256(path.read_bytes()).hexdigest()
        previous = {}
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            events += 1
            for key, note in row['notes'].items():
                before = previous.get(key)
                if before != note:
                    statuses[note['status']] += 1
                    if before:
                        revisions[(before['status'], note['status'])] += 1
            previous = row['notes']
    total = sum(g['generated_tokens'] for g in games)
    tail = sum(g['unfinished_tail_tokens'] for g in games)
    report = dict(source_sha256=sha256(source.read_bytes()).hexdigest(),
                  generated_tokens=total, unfinished_tail_tokens=tail,
                  unfinished_tail_fraction=tail / total,
                  memory_files=len(manifests), memory_events=events,
                  changed_note_versions_by_status={s: statuses[s] for s in ('hypothesis', 'supported', 'contradicted')},
                  same_key_status_revisions=[dict(before=a, after=b, count=c)
                                             for (a, b), c in sorted(revisions.items())],
                  memory_file_hashes=manifests, per_game=games,
                  boundary='Retrospective public development measurements. Tail reasoning did not produce another recorded completion, but may contain useful exploration or near-solutions. Absence of explicitly contradicted notes does not prove absence of belief correction: deletion and implicit rewrites are possible. Memory status labels are model-authored; observed-step validity does not establish causality. No hidden diagnosis or score improvement established.')
    output = source.parent / 'learning-gaps.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('per_game', 'memory_file_hashes')}, indent=2))


if __name__ == '__main__':
    main()
