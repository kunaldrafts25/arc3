# Measured local performance

Scores are official local scorecard values on public games, on a 0–100 scale. They are not Kaggle leaderboard scores.
Each row is one policy/game/policy-seed run. Game initialization seed is recorded separately (default 0).

| Policy | Runs | Full wins | Levels completed | Mean local score | Median seconds | Exceptions |
|---|---:|---:|---:|---:|---:|---:|
| starter | 6 | 0 | 0 | 0.000000 | 0.344 | 0 |
| random | 6 | 0 | 3 | 0.028675 | 1.758 | 0 |
| novelty | 6 | 0 | 1 | 0.003682 | 1.484 | 0 |
| memory | 6 | 0 | 1 | 0.003682 | 1.640 | 0 |
| planning | 6 | 0 | 1 | 0.003682 | 1.586 | 0 |

Means are descriptive: no statistical significance or hidden-set transfer is established.
Count totals sum across seeds; they are not counts of distinct solved levels.

## Per-game results

| Policy | Game | Runs | Levels | Mean score | Mean loop actions |
|---|---|---:|---:|---:|---:|
| starter | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| starter | vc33-5430563c | 3 | 0 | 0.0 | 200 |
| random | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| random | vc33-5430563c | 3 | 3 | 0.057350199334002205 | 200 |
| novelty | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| novelty | vc33-5430563c | 3 | 1 | 0.007364390018095358 | 200 |
| memory | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| memory | vc33-5430563c | 3 | 1 | 0.007364390018095358 | 200 |
| planning | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| planning | vc33-5430563c | 3 | 1 | 0.007364390018095358 | 200 |

## Action efficiency and limitations

Completed-level actions from official scorecards: mean 94.5, median 89.0.
Agent loop counts include commands; official scorecards may exclude initial full resets. Raw scorecards preserve reset and per-level accounting.
Unfinished levels score zero. Missing human baselines make scores unavailable. No fabricated estimates are used.

## Diagnostics

```json
{
  "explore_actions": 4752,
  "ineffective_actions": 1,
  "repeated_states": 1,
  "resets": 48
}
```
