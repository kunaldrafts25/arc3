# Measured local performance

Scores are official local scorecard values on public games, on a 0–100 scale. They are not Kaggle leaderboard scores.
Each row is one policy/game/policy-seed run. Game initialization seed is recorded separately (default 0).

| Policy | Runs | Full wins | Levels completed | Mean local score | Median seconds | Exceptions |
|---|---:|---:|---:|---:|---:|---:|
| starter | 75 | 0 | 3 | 0.061294 | 0.328 | 0 |
| random | 75 | 0 | 6 | 0.075703 | 3.016 | 0 |
| memory | 75 | 0 | 4 | 0.149726 | 3.968 | 0 |
| planning | 75 | 0 | 4 | 0.149726 | 2.547 | 0 |
| persistent | 75 | 0 | 6 | 0.075703 | 2.187 | 0 |
| coverage | 75 | 0 | 3 | 0.008066 | 5.063 | 0 |
| novelty | 75 | 0 | 4 | 0.149726 | 1.890 | 0 |

Means are descriptive: no statistical significance or hidden-set transfer is established.
Count totals sum across seeds; they are not counts of distinct solved levels.
Runtime measurements are exploratory local CPU timings; some experiments overlapped, so cross-policy latency differences are not controlled hardware comparisons.

## Per-game results

| Policy | Game | Runs | Levels | Mean score | Mean loop actions |
|---|---|---:|---:|---:|---:|
| starter | ar25-0c556536 | 3 | 0 | 0.0 | 200 |
| starter | bp35-0a0ad940 | 3 | 0 | 0.0 | 200 |
| starter | cd82-fb555c5d | 3 | 1 | 0.38277959993521216 | 200 |
| starter | cn04-2fe56bfb | 3 | 0 | 0.0 | 200 |
| starter | dc22-fdcac232 | 3 | 0 | 0.0 | 200 |
| starter | ft09-0d8bbf25 | 3 | 0 | 0.0 | 200 |
| starter | g50t-5849a774 | 3 | 0 | 0.0 | 200 |
| starter | ka59-38d34dbb | 3 | 0 | 0.0 | 200 |
| starter | lf52-271a04aa | 3 | 0 | 0.0 | 200 |
| starter | lp85-305b61c3 | 3 | 0 | 0.0 | 200 |
| starter | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| starter | m0r0-492f87ba | 3 | 0 | 0.0 | 200 |
| starter | r11l-495a7899 | 3 | 0 | 0.0 | 200 |
| starter | re86-8af5384d | 3 | 0 | 0.0 | 200 |
| starter | s5i5-18d95033 | 3 | 0 | 0.0 | 200 |
| starter | sb26-7fbdac44 | 3 | 0 | 0.0 | 200 |
| starter | sc25-635fd71a | 3 | 0 | 0.0 | 200 |
| starter | sk48-d8078629 | 3 | 0 | 0.0 | 200 |
| starter | sp80-589a99af | 3 | 2 | 1.1495648381682901 | 200 |
| starter | su15-1944f8ab | 3 | 0 | 0.0 | 200 |
| starter | tn36-ef4dde99 | 3 | 0 | 0.0 | 200 |
| starter | tr87-cd924810 | 3 | 0 | 0.0 | 200 |
| starter | tu93-0768757b | 3 | 0 | 0.0 | 200 |
| starter | vc33-5430563c | 3 | 0 | 0.0 | 200 |
| starter | wa30-ee6fef47 | 3 | 0 | 0.0 | 200 |
| random | ar25-0c556536 | 3 | 0 | 0.0 | 200 |
| random | bp35-0a0ad940 | 3 | 0 | 0.0 | 200 |
| random | cd82-fb555c5d | 3 | 0 | 0.0 | 200 |
| random | cn04-2fe56bfb | 3 | 0 | 0.0 | 200 |
| random | dc22-fdcac232 | 3 | 0 | 0.0 | 200 |
| random | ft09-0d8bbf25 | 3 | 0 | 0.0 | 200 |
| random | g50t-5849a774 | 3 | 0 | 0.0 | 200 |
| random | ka59-38d34dbb | 3 | 0 | 0.0 | 200 |
| random | lf52-271a04aa | 3 | 0 | 0.0 | 200 |
| random | lp85-305b61c3 | 3 | 0 | 0.0 | 200 |
| random | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| random | m0r0-492f87ba | 3 | 0 | 0.0 | 200 |
| random | r11l-495a7899 | 3 | 3 | 1.8352206852046604 | 200 |
| random | re86-8af5384d | 3 | 0 | 0.0 | 200 |
| random | s5i5-18d95033 | 3 | 0 | 0.0 | 200 |
| random | sb26-7fbdac44 | 3 | 0 | 0.0 | 200 |
| random | sc25-635fd71a | 3 | 0 | 0.0 | 200 |
| random | sk48-d8078629 | 3 | 0 | 0.0 | 200 |
| random | sp80-589a99af | 3 | 0 | 0.0 | 200 |
| random | su15-1944f8ab | 3 | 0 | 0.0 | 200 |
| random | tn36-ef4dde99 | 3 | 0 | 0.0 | 200 |
| random | tr87-cd924810 | 3 | 0 | 0.0 | 200 |
| random | tu93-0768757b | 3 | 0 | 0.0 | 200 |
| random | vc33-5430563c | 3 | 3 | 0.057350199334002205 | 200 |
| random | wa30-ee6fef47 | 3 | 0 | 0.0 | 200 |
| memory | ar25-0c556536 | 3 | 0 | 0.0 | 200 |
| memory | bp35-0a0ad940 | 3 | 0 | 0.0 | 200 |
| memory | cd82-fb555c5d | 3 | 0 | 0.0 | 200 |
| memory | cn04-2fe56bfb | 3 | 0 | 0.0 | 200 |
| memory | dc22-fdcac232 | 3 | 0 | 0.0 | 200 |
| memory | ft09-0d8bbf25 | 3 | 0 | 0.0 | 200 |
| memory | g50t-5849a774 | 3 | 0 | 0.0 | 200 |
| memory | ka59-38d34dbb | 3 | 0 | 0.0 | 200 |
| memory | lf52-271a04aa | 3 | 0 | 0.0 | 200 |
| memory | lp85-305b61c3 | 3 | 0 | 0.0 | 200 |
| memory | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| memory | m0r0-492f87ba | 3 | 0 | 0.0 | 200 |
| memory | r11l-495a7899 | 3 | 3 | 3.7357821141604926 | 200 |
| memory | re86-8af5384d | 3 | 0 | 0.0 | 200 |
| memory | s5i5-18d95033 | 3 | 0 | 0.0 | 200 |
| memory | sb26-7fbdac44 | 3 | 0 | 0.0 | 200 |
| memory | sc25-635fd71a | 3 | 0 | 0.0 | 200 |
| memory | sk48-d8078629 | 3 | 0 | 0.0 | 200 |
| memory | sp80-589a99af | 3 | 0 | 0.0 | 200 |
| memory | su15-1944f8ab | 3 | 0 | 0.0 | 200 |
| memory | tn36-ef4dde99 | 3 | 0 | 0.0 | 200 |
| memory | tr87-cd924810 | 3 | 0 | 0.0 | 200 |
| memory | tu93-0768757b | 3 | 0 | 0.0 | 200 |
| memory | vc33-5430563c | 3 | 1 | 0.007364390018095358 | 200 |
| memory | wa30-ee6fef47 | 3 | 0 | 0.0 | 200 |
| planning | ar25-0c556536 | 3 | 0 | 0.0 | 200 |
| planning | bp35-0a0ad940 | 3 | 0 | 0.0 | 200 |
| planning | cd82-fb555c5d | 3 | 0 | 0.0 | 200 |
| planning | cn04-2fe56bfb | 3 | 0 | 0.0 | 200 |
| planning | dc22-fdcac232 | 3 | 0 | 0.0 | 200 |
| planning | ft09-0d8bbf25 | 3 | 0 | 0.0 | 200 |
| planning | g50t-5849a774 | 3 | 0 | 0.0 | 200 |
| planning | ka59-38d34dbb | 3 | 0 | 0.0 | 200 |
| planning | lf52-271a04aa | 3 | 0 | 0.0 | 200 |
| planning | lp85-305b61c3 | 3 | 0 | 0.0 | 200 |
| planning | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| planning | m0r0-492f87ba | 3 | 0 | 0.0 | 200 |
| planning | r11l-495a7899 | 3 | 3 | 3.7357821141604926 | 200 |
| planning | re86-8af5384d | 3 | 0 | 0.0 | 200 |
| planning | s5i5-18d95033 | 3 | 0 | 0.0 | 200 |
| planning | sb26-7fbdac44 | 3 | 0 | 0.0 | 200 |
| planning | sc25-635fd71a | 3 | 0 | 0.0 | 200 |
| planning | sk48-d8078629 | 3 | 0 | 0.0 | 200 |
| planning | sp80-589a99af | 3 | 0 | 0.0 | 200 |
| planning | su15-1944f8ab | 3 | 0 | 0.0 | 200 |
| planning | tn36-ef4dde99 | 3 | 0 | 0.0 | 200 |
| planning | tr87-cd924810 | 3 | 0 | 0.0 | 200 |
| planning | tu93-0768757b | 3 | 0 | 0.0 | 200 |
| planning | vc33-5430563c | 3 | 1 | 0.007364390018095358 | 200 |
| planning | wa30-ee6fef47 | 3 | 0 | 0.0 | 200 |
| persistent | ar25-0c556536 | 3 | 0 | 0.0 | 200 |
| persistent | bp35-0a0ad940 | 3 | 0 | 0.0 | 200 |
| persistent | cd82-fb555c5d | 3 | 0 | 0.0 | 200 |
| persistent | cn04-2fe56bfb | 3 | 0 | 0.0 | 200 |
| persistent | dc22-fdcac232 | 3 | 0 | 0.0 | 200 |
| persistent | ft09-0d8bbf25 | 3 | 0 | 0.0 | 200 |
| persistent | g50t-5849a774 | 3 | 0 | 0.0 | 200 |
| persistent | ka59-38d34dbb | 3 | 0 | 0.0 | 200 |
| persistent | lf52-271a04aa | 3 | 0 | 0.0 | 200 |
| persistent | lp85-305b61c3 | 3 | 0 | 0.0 | 200 |
| persistent | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| persistent | m0r0-492f87ba | 3 | 0 | 0.0 | 200 |
| persistent | r11l-495a7899 | 3 | 3 | 1.8352206852046604 | 200 |
| persistent | re86-8af5384d | 3 | 0 | 0.0 | 200 |
| persistent | s5i5-18d95033 | 3 | 0 | 0.0 | 200 |
| persistent | sb26-7fbdac44 | 3 | 0 | 0.0 | 200 |
| persistent | sc25-635fd71a | 3 | 0 | 0.0 | 200 |
| persistent | sk48-d8078629 | 3 | 0 | 0.0 | 200 |
| persistent | sp80-589a99af | 3 | 0 | 0.0 | 200 |
| persistent | su15-1944f8ab | 3 | 0 | 0.0 | 200 |
| persistent | tn36-ef4dde99 | 3 | 0 | 0.0 | 200 |
| persistent | tr87-cd924810 | 3 | 0 | 0.0 | 200 |
| persistent | tu93-0768757b | 3 | 0 | 0.0 | 200 |
| persistent | vc33-5430563c | 3 | 3 | 0.057350199334002205 | 200 |
| persistent | wa30-ee6fef47 | 3 | 0 | 0.0 | 200 |
| coverage | ar25-0c556536 | 3 | 0 | 0.0 | 200 |
| coverage | bp35-0a0ad940 | 3 | 0 | 0.0 | 200 |
| coverage | cd82-fb555c5d | 3 | 0 | 0.0 | 200 |
| coverage | cn04-2fe56bfb | 3 | 0 | 0.0 | 200 |
| coverage | dc22-fdcac232 | 3 | 0 | 0.0 | 200 |
| coverage | ft09-0d8bbf25 | 3 | 0 | 0.0 | 200 |
| coverage | g50t-5849a774 | 3 | 0 | 0.0 | 200 |
| coverage | ka59-38d34dbb | 3 | 0 | 0.0 | 200 |
| coverage | lf52-271a04aa | 3 | 0 | 0.0 | 200 |
| coverage | lp85-305b61c3 | 3 | 0 | 0.0 | 200 |
| coverage | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| coverage | m0r0-492f87ba | 3 | 0 | 0.0 | 200 |
| coverage | r11l-495a7899 | 3 | 3 | 0.20165824026452656 | 200 |
| coverage | re86-8af5384d | 3 | 0 | 0.0 | 200 |
| coverage | s5i5-18d95033 | 3 | 0 | 0.0 | 200 |
| coverage | sb26-7fbdac44 | 3 | 0 | 0.0 | 200 |
| coverage | sc25-635fd71a | 3 | 0 | 0.0 | 200 |
| coverage | sk48-d8078629 | 3 | 0 | 0.0 | 200 |
| coverage | sp80-589a99af | 3 | 0 | 0.0 | 200 |
| coverage | su15-1944f8ab | 3 | 0 | 0.0 | 200 |
| coverage | tn36-ef4dde99 | 3 | 0 | 0.0 | 200 |
| coverage | tr87-cd924810 | 3 | 0 | 0.0 | 200 |
| coverage | tu93-0768757b | 3 | 0 | 0.0 | 200 |
| coverage | vc33-5430563c | 3 | 0 | 0.0 | 200 |
| coverage | wa30-ee6fef47 | 3 | 0 | 0.0 | 200 |
| novelty | ar25-0c556536 | 3 | 0 | 0.0 | 200 |
| novelty | bp35-0a0ad940 | 3 | 0 | 0.0 | 200 |
| novelty | cd82-fb555c5d | 3 | 0 | 0.0 | 200 |
| novelty | cn04-2fe56bfb | 3 | 0 | 0.0 | 200 |
| novelty | dc22-fdcac232 | 3 | 0 | 0.0 | 200 |
| novelty | ft09-0d8bbf25 | 3 | 0 | 0.0 | 200 |
| novelty | g50t-5849a774 | 3 | 0 | 0.0 | 200 |
| novelty | ka59-38d34dbb | 3 | 0 | 0.0 | 200 |
| novelty | lf52-271a04aa | 3 | 0 | 0.0 | 200 |
| novelty | lp85-305b61c3 | 3 | 0 | 0.0 | 200 |
| novelty | ls20-9607627b | 3 | 0 | 0.0 | 200 |
| novelty | m0r0-492f87ba | 3 | 0 | 0.0 | 200 |
| novelty | r11l-495a7899 | 3 | 3 | 3.7357821141604926 | 200 |
| novelty | re86-8af5384d | 3 | 0 | 0.0 | 200 |
| novelty | s5i5-18d95033 | 3 | 0 | 0.0 | 200 |
| novelty | sb26-7fbdac44 | 3 | 0 | 0.0 | 200 |
| novelty | sc25-635fd71a | 3 | 0 | 0.0 | 200 |
| novelty | sk48-d8078629 | 3 | 0 | 0.0 | 200 |
| novelty | sp80-589a99af | 3 | 0 | 0.0 | 200 |
| novelty | su15-1944f8ab | 3 | 0 | 0.0 | 200 |
| novelty | tn36-ef4dde99 | 3 | 0 | 0.0 | 200 |
| novelty | tr87-cd924810 | 3 | 0 | 0.0 | 200 |
| novelty | tu93-0768757b | 3 | 0 | 0.0 | 200 |
| novelty | vc33-5430563c | 3 | 1 | 0.007364390018095358 | 200 |
| novelty | wa30-ee6fef47 | 3 | 0 | 0.0 | 200 |

## Action efficiency and limitations

Completed-level actions from official scorecards: mean 71.2, median 59.5.
Agent loop counts include commands; official scorecards may exclude initial full resets. Raw scorecards preserve reset and per-level accounting.
Unfinished levels score zero. Missing human baselines make scores unavailable. No fabricated estimates are used.

| Policy | Completed / available level attempts | Completion rate | Runtime min / median / max (s) |
|---|---:|---:|---|
| starter | 3 / 549 | 0.546% | 0.093 / 0.328 / 1.547 |
| random | 6 / 549 | 1.093% | 0.281 / 3.016 / 9.562 |
| memory | 4 / 549 | 0.729% | 0.359 / 3.968 / 8.406 |
| planning | 4 / 549 | 0.729% | 0.172 / 2.547 / 9.000 |
| persistent | 6 / 549 | 1.093% | 0.187 / 2.187 / 6.531 |
| coverage | 3 / 549 | 0.546% | 0.219 / 5.063 / 10.797 |
| novelty | 4 / 549 | 0.729% | 0.141 / 1.890 / 7.688 |

## Diagnostics

```json
{
  "explore_actions": 81137,
  "ineffective_actions": 26810,
  "repeated_states": 26972,
  "model_predictions": 137,
  "model_matches": 132,
  "resets": 821,
  "prediction_failures": 5,
  "recover_actions": 8042
}
```
