# Completed full public comparison

Both exact jobs are COMPLETE: baseline/3 and verified-planner/2. Both played all
25 public games with substantive tokens/actions, without crashed/not-started
games. Same target/draft, runtime, scheduler and 7200-second post-readiness
window. Finalization added approximately 120 seconds to each benchmark duration.

| Metric | Original baseline/3 | Strict planner/2 |
| --- | ---: | ---: |
| Mean public score | 45.0150039777 | 33.1771134555 |
| Levels | 103 | 75 |
| Full wins | 5 | 4 |
| Accounted generated tokens | 4,353,017 | 4,001,021 |
| Levels by 30/60/90/120 minutes | 42/68/85/103 | 25/45/61/75 |

Planner score delta: **-11.8379 points**. Four games improved, 15 worsened, six
tied. Largest improvements: FT09 +52.38, TR87 +8.97. Largest regressions: CN04
-47.62, SP80 -42.86, VC33 -38.11, KA59 -37.52, AR25 -36.11. No game-specific
dispatch table is derived from these public identities.

Mechanical adoption was real: events in 25 games, 534 replay checks, 292 passing
checks, 131 retrospective counterexamples, 61 errors, 274 plan calls and 1427
reported planned actions. Fifty-three plans stopped on prospective mismatches;
80 reported unverified models. Of 534 checks, 528 used abstract representations.
Counts include repeated historical checks; event actions differ from benchmark
accounting and omit interrupted calls.

**Decision:** retain the original baseline; do not promote the strict run. This
single stochastic pair cannot isolate the action restriction from prompt
conflict, simulator overhead or sampling variability. Planner/2 still had the
older contradictory user guidance.

The next candidate preserves ordinary action batching/repeated calls, offers
checked planning optionally, and clarifies persistence/step limits. It tests a
complete configuration, not a causal ablation. Same model/runtime/scheduler,
no training and no hard-coded games. CPU v5 passed eight execution cases and
16 rendered prompt combinations before the new GPU run. These public results
do not change the best official 24.87 or establish the goal.
