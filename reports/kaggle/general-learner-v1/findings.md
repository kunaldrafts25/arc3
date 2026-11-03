# General learner extended public evaluation

Launched 2026-10-27 UTC / 2026-10-28 IST as exact version
`kunalsinghh25/arc-hydra-general-learner/1`. Authoritative status was RUNNING
after upload; no score or model readiness had been established at that check.

Research translated into the agent:

- A game-independent learning protocol separates controls, modes, mechanics,
  goals and resources, asks for discriminating experiments and diagnoses failed
  predictions before abandoning useful mechanics.
- Mathematical methods are conditional: geometry and actor footprints,
  permutations and abstractions, toggle algebra with assumption checks,
  search/constraints, and adversarial reasoning only where justified.
- Up to ten concise model-authored hypotheses survive Python calls and context
  drains in a per-game sidecar. Evidence references must name observed steps;
  this does not certify a causal or goal claim. Prior-level transferable notes
  are marked for rechecking. Ordinary action batches remain available.
- CPU-tested source hashes are checked again during GPU installation. Mutation
  events and runtime provenance support later adoption and failure audits.

No weight training, new model, paid scaling, extra account or game-specific
solution was added. Original target/draft checkpoints, serving v2.5.3, scheduler
and optional planning tools remain in use. The source incorporates the previous
manual and primary-source research; it is not a claim of universal solving.

Budget: 32,400 seconds for the whole notebook, with 600 seconds reserved for
finalization. Startup reduces the gameplay window. Public mode runs all 25 games
concurrently for the remaining time; there is no two-hour cap. Official reruns
also obey the smaller of the configured wall budget and competition runtime.
The fresh prelaunch quota was 33,063.913 GPU seconds, zero reserved, paid scaling
disabled. One run fits; other accounts are not used to bypass quota restrictions.

Validation: 109 local tests passed, including real composed child-RPC memory
carryover and executed deadline logic. Kaggle CPU gate version 2 passed eight
mechanical cases, 16 prompt combinations and nine memory/host cases. The
exact accepted notebook hashes and budget are in `launch.json`.

Previous best public result remains 48.2861 (109 levels, six full wins); best
official remains 24.87. This run changes both strategy and available compute,
so comparison against the previous two-hour run cannot isolate strategy gain.
Keep the previous candidate intact until the new artifacts support promotion.

## Completed-run audit, 29 October IST

Authoritative cloud status COMPLETE. Actual lifecycle: run_finished, no error,
25/25 games with model gameplay, 147 completed levels, 11 full wins, 15,203,434
reconstructed generated tokens. Exact development score 62.09472223548143.
The game runs ended won=11, gave_up=9, cancelled=5; these states alone do not
identify whether termination was model choice or orchestration at the deadline.

Official submission 57726784 is COMPLETE at 28.45, versus previous best 24.87
(+3.58). The user reports submitting this candidate. Submission metadata does
not expose a notebook-version link, our own submitted-file endpoint returned
403, and the own-submission episode listing was empty. Consequently no hidden
game failure diagnosis or exact artifact hash linkage has been established.
The downloaded development parquet is a dummy trigger file, not the evaluation
result; the competition reruns the notebook. Its development score is not an
estimate of the separate official game set.

Observed time curve, relative to gameplay benchmark start:

| Elapsed | Score | Levels |
| --- | ---: | ---: |
| 2 hours | 42.99 | 100 |
| 4 hours | 53.43 | 126 |
| 6 hours | 61.06 | 143 |
| 8 hours | 62.09 | 147 |
| Final (about 8h22m) | 62.09 | 147 |

The previous two-hour candidate scored 48.29. This run was weaker at the
two-hour checkpoint and gained most of its final advantage with more compute.
This is a single stochastic comparison, not evidence that guidance/memory
caused either the early regression or late gains.

Memory changed 244 times across all 25 games; adoption is now established,
benefit is not. The 14 unfinished games spent 5,436 actions on their terminal
unsolved levels. These actions may include useful experiments; the count alone
does not prove they were wasted. With current completed levels but ideal action
efficiency, the mean score ceiling is 73.44. Thus the public deficit separates
into 11.35 points below the completion ceiling plus 26.56 points from incomplete
later levels. This is an opportunity bound, not an achievable score prediction.

Exact action-count scoring reproduced every recorded final game score. See
`diagnosis.json` for per-game gaps, time curve, tokens and memory evidence hashes.
