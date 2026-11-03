# Completed public baseline, 25 October 2026

Kaggle `kunalsinghh25/arc-hydra-duck-m2-baseline/2`: COMPLETE. Gameplay
15:18:01–17:19:19 UTC; configured two-hour deadline plus cancellation/output time.
The attributed Franzen/Duck M2 agent scored **43.7621** over 25 public games,
completed 102 levels and won five games. All 25 have substantive model gameplay;
no crashes or not-started games. Action-accounted generation: 4,331,218 tokens.
Cancelled means the configured public deadline ended an unfinished game.
This is not an official hidden competition score.

Completed levels at 30/60/90/120 minutes from benchmark start: **37/63/84/102**.
The final half hour still added 18 levels. More time may help, but extrapolating
these results to the larger hidden game set or nine-hour run is unverified.
Per-action wallclock fields are elapsed timestamps, not durations to sum.

Five full wins: FT09, LP85, M0R0, AR25, SB26. Only SK48 completed no level.
Five further games reached their last level: SC25, KA59, CN04, TR87, TU93.
Raw `benchmark.json` and `hydra_model_summary.json` retain per-game outcomes.

## Selected weak-game request audit

Six cached game logs were selected for diagnosis, not a representative estimate.
Across them: 395 completed responses, 808,231 completion tokens, 23 ordinary tool
errors, seven expected stale-state guard stops and one terminal-state guard stop.
The terminal-state stop was initially misclassified as an ordinary tool error.
Deduplicate tool messages by
call ID because every request retains earlier conversation history.

| Game | Responses | Ordinary errors | Cached prompt fraction | Largest token group at one action counter | Large prompt decreases |
|---|---:|---:|---:|---:|---:|
| BP35 | 69 | 3 | 0.930 | 58,236 / 16 responses | 3 |
| LF52 | 128 | 5 | 0.941 | 14,067 / 3 responses | 5 |
| SK48 | 29 | 1 | 0.879 | 27,706 / 5 responses | 1 |
| SP80 | 46 | 4 | 0.903 | 11,794 / 1 response | 2 |
| VC33 | 68 | 2 | 0.927 | 25,770 / 7 responses | 3 |
| WA30 | 55 | 8 | 0.936 | 25,576 / 18 responses | 1 |

BP35's retained late reasoning repeatedly reconstructs screen offsets and earlier
attempts. Its recorded prompt drops include 118,707→59,307 and 113,968→58,915
tokens at action counter 77. These observations motivate a memory experiment;
they do not prove forgetting caused the low score. Computation without game
actions can be useful search, so an automatic stall cutoff is not justified.

## Next controlled experiment

`kunalsinghh25/arc-hydra-duck-summary/1`: same 25 games, one pass, 7,200 seconds
after readiness, original model/runtime/scheduler/tools. Enable existing upstream
rolling summaries after 49,152 new context tokens, cap summaries at 4,096 tokens,
include current-turn state and use summary-aware history draining. Ordinary
reasoning, structured-memory settings and immediate history replacement remain
as in the baseline. Exact overrides are in its notebook provenance.

Verify actual summaries were produced and all games played; compare final score,
level completion and late-run progress. One stochastic run can suggest a useful
change but cannot establish a reliable causal gain. Preserve the original
baseline for official testing; no summary benefit is claimed before results.
