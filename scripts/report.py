"""Generate a transparent Markdown report from benchmark JSONL files."""
import argparse
from collections import defaultdict, Counter
import json
from pathlib import Path
from statistics import mean, median


def render(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["policy"]].append(row)
    lines = ["# Measured local performance", "",
             "Scores are official local scorecard values on public games, on a 0–100 scale. They are not Kaggle leaderboard scores.",
             "Each row is one policy/game/policy-seed run. Game initialization seed is recorded separately (default 0).", "",
             "| Policy | Runs | Full wins | Levels completed | Mean local score | Median seconds | Exceptions |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for policy, items in grouped.items():
        scores = [r["official_score_if_available"] for r in items if r["official_score_if_available"] is not None]
        score = f"{mean(scores):.6f}" if scores else "unavailable"
        lines.append(f"| {policy} | {len(items)} | {sum(r['completion_status'] is True for r in items)} | "
                     f"{sum(r['levels_completed'] or 0 for r in items)} | {score} | "
                     f"{median(r['runtime_seconds'] for r in items):.3f} | {sum(len(r['exceptions']) for r in items)} |")
    lines += ["", "Means are descriptive: no statistical significance or hidden-set transfer is established.",
              "Count totals sum across seeds; they are not counts of distinct solved levels.",
              "Runtime measurements are exploratory local CPU timings; some experiments overlapped, so cross-policy latency differences are not controlled hardware comparisons.", "", "## Per-game results", "",
              "| Policy | Game | Runs | Levels | Mean score | Mean loop actions |", "|---|---|---:|---:|---:|---:|"]
    for policy, items in grouped.items():
        games = defaultdict(list)
        for r in items:
            games[r["game_id"]].append(r)
        for game, results in sorted(games.items()):
            scores = [r["official_score_if_available"] for r in results if r["official_score_if_available"] is not None]
            actions = [r["action_count"] for r in results if r["action_count"] is not None]
            lines.append(f"| {policy} | {game} | {len(results)} | {sum(r['levels_completed'] or 0 for r in results)} | "
                         f"{mean(scores) if scores else 'unavailable'} | {mean(actions) if actions else 'unavailable'} |")
    completions = []
    for r in rows:
        for environment in r.get("scorecard", {}).get("environments", []):
            for run in environment["runs"]:
                completions += (run.get("level_actions") or [])[:run["levels_completed"]]
    lines += ["", "## Action efficiency and limitations", "",
              f"Completed-level actions from official scorecards: mean {mean(completions) if completions else 'unavailable'}, median {median(completions) if completions else 'unavailable'}.",
              "Agent loop counts include commands; official scorecards may exclude initial full resets. Raw scorecards preserve reset and per-level accounting.",
              "Unfinished levels score zero. Missing human baselines make scores unavailable. No fabricated estimates are used.", ""]
    lines += ["| Policy | Completed / available level attempts | Completion rate | Runtime min / median / max (s) |",
              "|---|---:|---:|---|"]
    for policy, items in grouped.items():
        total = sum(r.get("total_levels", 0) or 0 for r in items)
        completed = sum(r["levels_completed"] or 0 for r in items)
        rate = f"{100*completed/total:.3f}%" if total else "unavailable"
        times = [r["runtime_seconds"] for r in items]
        lines.append(f"| {policy} | {completed} / {total} | {rate} | {min(times):.3f} / {median(times):.3f} / {max(times):.3f} |")
    lines.append("")
    failures = Counter()
    for r in rows:
        failures.update(r.get("diagnostics", {}))
    lines += ["## Diagnostics", "", "```json", json.dumps(dict(failures), indent=2), "```", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--output", default="reports/performance.md")
    args = parser.parse_args()
    rows = [json.loads(line) for name in args.inputs for line in Path(name).read_text(encoding="utf-8").splitlines() if line.strip()]
    Path(args.output).write_text(render(rows), encoding="utf-8")
    print(f"Wrote {args.output}: {len(rows)} runs")
