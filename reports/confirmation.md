# Measured local performance

Scores are official local scorecard values on public games, on a 0–100 scale. They are not Kaggle leaderboard scores.
Each row is one policy/game/policy-seed run. Game initialization seed is recorded separately (default 0).

| Policy | Runs | Full wins | Levels completed | Mean local score | Median seconds | Exceptions |
|---|---:|---:|---:|---:|---:|---:|
| starter | 50 | 0 | 1 | 0.001714 | 0.484 | 0 |
| random | 50 | 0 | 3 | 0.032521 | 2.148 | 0 |
| memory | 50 | 0 | 5 | 0.148328 | 1.961 | 0 |
| novelty | 50 | 0 | 5 | 0.148328 | 1.571 | 0 |

Means are descriptive: no statistical significance or hidden-set transfer is established.
Count totals sum across seeds; they are not counts of distinct solved levels.
Runtime measurements are exploratory local CPU timings; some experiments overlapped, so cross-policy latency differences are not controlled hardware comparisons.

## Per-game results

| Policy | Game | Runs | Levels | Mean score | Mean loop actions |
|---|---|---:|---:|---:|---:|
| starter | ar25-0c556536 | 2 | 0 | 0.0 | 200 |
| starter | bp35-0a0ad940 | 2 | 0 | 0.0 | 200 |
| starter | cd82-fb555c5d | 2 | 0 | 0.0 | 200 |
| starter | cn04-2fe56bfb | 2 | 0 | 0.0 | 200 |
| starter | dc22-fdcac232 | 2 | 0 | 0.0 | 200 |
| starter | ft09-0d8bbf25 | 2 | 0 | 0.0 | 200 |
| starter | g50t-5849a774 | 2 | 0 | 0.0 | 200 |
| starter | ka59-38d34dbb | 2 | 0 | 0.0 | 200 |
| starter | lf52-271a04aa | 2 | 0 | 0.0 | 200 |
| starter | lp85-305b61c3 | 2 | 0 | 0.0 | 200 |
| starter | ls20-9607627b | 2 | 0 | 0.0 | 200 |
| starter | m0r0-492f87ba | 2 | 0 | 0.0 | 200 |
| starter | r11l-495a7899 | 2 | 1 | 0.04284581173337866 | 200 |
| starter | re86-8af5384d | 2 | 0 | 0.0 | 200 |
| starter | s5i5-18d95033 | 2 | 0 | 0.0 | 200 |
| starter | sb26-7fbdac44 | 2 | 0 | 0.0 | 200 |
| starter | sc25-635fd71a | 2 | 0 | 0.0 | 200 |
| starter | sk48-d8078629 | 2 | 0 | 0.0 | 200 |
| starter | sp80-589a99af | 2 | 0 | 0.0 | 200 |
| starter | su15-1944f8ab | 2 | 0 | 0.0 | 200 |
| starter | tn36-ef4dde99 | 2 | 0 | 0.0 | 200 |
| starter | tr87-cd924810 | 2 | 0 | 0.0 | 200 |
| starter | tu93-0768757b | 2 | 0 | 0.0 | 200 |
| starter | vc33-5430563c | 2 | 0 | 0.0 | 200 |
| starter | wa30-ee6fef47 | 2 | 0 | 0.0 | 200 |
| random | ar25-0c556536 | 2 | 0 | 0.0 | 200 |
| random | bp35-0a0ad940 | 2 | 0 | 0.0 | 200 |
| random | cd82-fb555c5d | 2 | 0 | 0.0 | 200 |
| random | cn04-2fe56bfb | 2 | 0 | 0.0 | 200 |
| random | dc22-fdcac232 | 2 | 0 | 0.0 | 200 |
| random | ft09-0d8bbf25 | 2 | 0 | 0.0 | 200 |
| random | g50t-5849a774 | 2 | 0 | 0.0 | 200 |
| random | ka59-38d34dbb | 2 | 0 | 0.0 | 200 |
| random | lf52-271a04aa | 2 | 0 | 0.0 | 200 |
| random | lp85-305b61c3 | 2 | 0 | 0.0 | 200 |
| random | ls20-9607627b | 2 | 0 | 0.0 | 200 |
| random | m0r0-492f87ba | 2 | 0 | 0.0 | 200 |
| random | r11l-495a7899 | 2 | 2 | 0.8055272766864895 | 200 |
| random | re86-8af5384d | 2 | 0 | 0.0 | 200 |
| random | s5i5-18d95033 | 2 | 0 | 0.0 | 200 |
| random | sb26-7fbdac44 | 2 | 0 | 0.0 | 200 |
| random | sc25-635fd71a | 2 | 0 | 0.0 | 200 |
| random | sk48-d8078629 | 2 | 0 | 0.0 | 200 |
| random | sp80-589a99af | 2 | 0 | 0.0 | 200 |
| random | su15-1944f8ab | 2 | 0 | 0.0 | 200 |
| random | tn36-ef4dde99 | 2 | 0 | 0.0 | 200 |
| random | tr87-cd924810 | 2 | 0 | 0.0 | 200 |
| random | tu93-0768757b | 2 | 0 | 0.0 | 200 |
| random | vc33-5430563c | 2 | 1 | 0.007501714677640603 | 200 |
| random | wa30-ee6fef47 | 2 | 0 | 0.0 | 200 |
| memory | ar25-0c556536 | 2 | 0 | 0.0 | 200 |
| memory | bp35-0a0ad940 | 2 | 0 | 0.0 | 200 |
| memory | cd82-fb555c5d | 2 | 0 | 0.0 | 200 |
| memory | cn04-2fe56bfb | 2 | 0 | 0.0 | 200 |
| memory | dc22-fdcac232 | 2 | 0 | 0.0 | 200 |
| memory | ft09-0d8bbf25 | 2 | 1 | 2.380952380952381 | 200 |
| memory | g50t-5849a774 | 2 | 0 | 0.0 | 200 |
| memory | ka59-38d34dbb | 2 | 0 | 0.0 | 200 |
| memory | lf52-271a04aa | 2 | 0 | 0.0 | 200 |
| memory | lp85-305b61c3 | 2 | 0 | 0.0 | 200 |
| memory | ls20-9607627b | 2 | 0 | 0.0 | 200 |
| memory | m0r0-492f87ba | 2 | 0 | 0.0 | 200 |
| memory | r11l-495a7899 | 2 | 2 | 0.11775728076360781 | 200 |
| memory | re86-8af5384d | 2 | 0 | 0.0 | 200 |
| memory | s5i5-18d95033 | 2 | 0 | 0.0 | 200 |
| memory | sb26-7fbdac44 | 2 | 0 | 0.0 | 200 |
| memory | sc25-635fd71a | 2 | 0 | 0.0 | 200 |
| memory | sk48-d8078629 | 2 | 0 | 0.0 | 200 |
| memory | sp80-589a99af | 2 | 1 | 1.154792274052478 | 200 |
| memory | su15-1944f8ab | 2 | 0 | 0.0 | 200 |
| memory | tn36-ef4dde99 | 2 | 0 | 0.0 | 200 |
| memory | tr87-cd924810 | 2 | 0 | 0.0 | 200 |
| memory | tu93-0768757b | 2 | 0 | 0.0 | 200 |
| memory | vc33-5430563c | 2 | 1 | 0.05468749999999999 | 200 |
| memory | wa30-ee6fef47 | 2 | 0 | 0.0 | 200 |
| novelty | ar25-0c556536 | 2 | 0 | 0.0 | 200 |
| novelty | bp35-0a0ad940 | 2 | 0 | 0.0 | 200 |
| novelty | cd82-fb555c5d | 2 | 0 | 0.0 | 200 |
| novelty | cn04-2fe56bfb | 2 | 0 | 0.0 | 200 |
| novelty | dc22-fdcac232 | 2 | 0 | 0.0 | 200 |
| novelty | ft09-0d8bbf25 | 2 | 1 | 2.380952380952381 | 200 |
| novelty | g50t-5849a774 | 2 | 0 | 0.0 | 200 |
| novelty | ka59-38d34dbb | 2 | 0 | 0.0 | 200 |
| novelty | lf52-271a04aa | 2 | 0 | 0.0 | 200 |
| novelty | lp85-305b61c3 | 2 | 0 | 0.0 | 200 |
| novelty | ls20-9607627b | 2 | 0 | 0.0 | 200 |
| novelty | m0r0-492f87ba | 2 | 0 | 0.0 | 200 |
| novelty | r11l-495a7899 | 2 | 2 | 0.11775728076360781 | 200 |
| novelty | re86-8af5384d | 2 | 0 | 0.0 | 200 |
| novelty | s5i5-18d95033 | 2 | 0 | 0.0 | 200 |
| novelty | sb26-7fbdac44 | 2 | 0 | 0.0 | 200 |
| novelty | sc25-635fd71a | 2 | 0 | 0.0 | 200 |
| novelty | sk48-d8078629 | 2 | 0 | 0.0 | 200 |
| novelty | sp80-589a99af | 2 | 1 | 1.154792274052478 | 200 |
| novelty | su15-1944f8ab | 2 | 0 | 0.0 | 200 |
| novelty | tn36-ef4dde99 | 2 | 0 | 0.0 | 200 |
| novelty | tr87-cd924810 | 2 | 0 | 0.0 | 200 |
| novelty | tu93-0768757b | 2 | 0 | 0.0 | 200 |
| novelty | vc33-5430563c | 2 | 1 | 0.05468749999999999 | 200 |
| novelty | wa30-ee6fef47 | 2 | 0 | 0.0 | 200 |

## Action efficiency and limitations

Completed-level actions from official scorecards: mean 85.07142857142857, median 71.5.
Agent loop counts include commands; official scorecards may exclude initial full resets. Raw scorecards preserve reset and per-level accounting.
Unfinished levels score zero. Missing human baselines make scores unavailable. No fabricated estimates are used.

| Policy | Completed / available level attempts | Completion rate | Runtime min / median / max (s) |
|---|---:|---:|---|
| starter | 1 / 366 | 0.273% | 0.172 / 0.484 / 2.813 |
| random | 3 / 366 | 0.820% | 0.140 / 2.148 / 8.094 |
| memory | 5 / 366 | 1.366% | 0.172 / 1.961 / 8.047 |
| novelty | 5 / 366 | 1.366% | 0.125 / 1.571 / 4.188 |

## Diagnostics

```json
{
  "explore_actions": 27052,
  "ineffective_actions": 8914,
  "repeated_states": 8962,
  "model_predictions": 65,
  "model_matches": 60,
  "resets": 254,
  "prediction_failures": 5,
  "recover_actions": 2694
}
```
