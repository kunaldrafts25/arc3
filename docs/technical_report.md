# ARC-Hydra technical report

## v0.2 — 25 October 2026

The current candidate uses learned motion, click effects, color cycles, visual
glyph programs and verified linear plans, with a 300-action guard. All 38 local
tests pass. Private Kaggle notebook version 3 reproduced a complete six-level
FT09 win in 159 actions, plus two short public smoke checks without exceptions.
See [the v0.2 evidence and limitations](v02_development.md) for experiments and
the broad comparison. These public wins do not establish hidden performance.

The historical v0.1 report follows; its default and measurements describe the
previous agent rather than the current candidate.

## v0.1 historical report

Built on 2026-10-24 in D:/compi/ARC-AGI-3-Kaggle-Starter, branch feature/arc-hydra. This is an operational local baseline. Kaggle version 2 completed actual public-game smoke validation and was accepted as competition submission 57601062. Its hidden evaluation status is tracked in docs/kaggle_validation.md and reports/kaggle/submission-status.json.

Actual competition result: submission 57601062 is COMPLETE with public score 0.01 and no reported evaluation error. Hidden per-game diagnostics were not accessible. The result is far from competitive. A subsequent four-game budget trial increased commands fivefold with negligible mean-score gain and no full game wins; the next priority is mechanics and goal inference. The local timer-start correctness fix is not part of the scored version. See reports/kaggle/result-analysis.md.

## What exists and has run

The official starter and framework were cloned and their live interfaces inspected before replacing the agent. The implementation uses arc-agi 0.9.9 / arcengine 0.9.3 with Python 3.12.10. It has run through the real official Agent.main loop against cached public environments. The notebook embeds the complete Hydra source and imports it successfully in a separate interpreter outside the source tree.

The adapter preserves MyAgent(Agent), choose_action and is_done. It filters advertised actions, validates ACTION6 coordinates, resets level-local memory at lifecycle boundaries, bounds action/time/memory/search budgets, and isolates failures to the affected game. Per-agent payload snapshots go directly to the actual wrapper, preserving concurrent requests without reading mutable shared enum payloads.

Implemented components: lossless frame history retention, deterministic latest-image hashing with shape/level/legal-action metadata, vectorized frame differences, 4/8-neighbor color components, bounded outcome distributions, prediction falsification, count-based exploration, repeated-state diagnosis, empirical frontier BFS and one-step replanning, short action-run experiments, click-coverage experiments, and a JSONL/Markdown evaluation workflow.

The controller modes describe actual action selection, not inferred semantic understanding. Its frontier goal is an observed state with untested actions; it has no verified general game-goal recognizer. A repeated image does not prove that the hidden game state is identical. Contradictory transitions disable deterministic prediction.

## Final measured default

Default policy: novelty. It retains raw transition tuples and state/action counts, while predictive outcome modeling and frontier planning stay optional. Across all 25 public games and five policy seeds (0 through 4), with environment seed 0 and 200 commands per game:

| Policy | Runs | Level completions | Full game wins | Mean official local score (0–100) |
|---|---:|---:|---:|---:|
| Original starter | 125 | 4 | 0 | 0.0374618 |
| Legal random | 125 | 9 | 0 | 0.0584302 |
| Novelty (selected) | 125 | 9 | 0 | 0.1491665 |
| Transition memory | 125 | 9 | 0 | 0.1491665 |

The separate confirmation seeds 3 and 4 gave novelty/memory 0.148328, legal random 0.032521 and starter 0.001714. Predictive memory did not improve on the simpler policy, so it was not selected. Planning matched memory on the initial 75 runs and never selected a planned action. Persistence matched legal random; click coverage scored lower (0.008066 on 75 runs). These methods are retained as reproducible experimental variants, not claimed improvements.

The consolidated training report contains 525 validated rows (7 policies × 25 games × 3 seeds). Confirmation contains 200 validated rows (4 policies × 25 games × 2 seeds). No included row has a recorded exception. Raw source files and their SHA-256 manifest are preserved. Superseded novelty rows are excluded explicitly. Counts sum across repeated seeds; nine completions do not mean nine different levels. Scores remain extremely low, and the project has not solved a complete game.

## Earlier measurement and provenance

The first ablation used ls20 and vc33, 3 policy seeds, fixed environment seed 0 and equal 200-command caps. Across six runs per policy, the pristine starter completed zero levels, legal random completed three, and novelty, memory and planning each completed one. No full games were won. Legal random's mean local score was 0.028675 on the 0–100 scale. Full raw scorecards are in reports/ablation-v01.jsonl.

All 25 public environments were then downloaded through the official API and smoke-tested at 50 commands. Full comparisons use the stable cache, equal 200-command caps and policy seeds 0,1,2. See reports/public-ablation.md for the completed comparison. Scores come directly from the installed official scorer; missing information stays unavailable. These runs are development-set experiments, not hidden validation.

Twenty-one Hydra tests pass, including a real-engine integration test, a simulated reset-to-level-transition-to-WIN lifecycle test, a model-disabled novelty guard, a concurrent-request test and competition smoke-gating behavior. The independent upstream recorder tests pass 19/19. The full upstream suite fails collection on four files because this framework checkout's tests reference absent agents.structs or optional openai. Original Windows source-encoding and terminal-output bugs were fixed separately from policy changes.

The original novelty ablation accidentally consulted the model. Its raw results are retained with an erratum, and corrected reruns replace them in the final comparison. The full original run produced 450 rows with no per-run exceptions. Memory and planning produced zero confirmed model predictions and zero planned actions; BFS therefore has no demonstrated gameplay contribution in this experiment.

## Largest observed bottlenecks

| Rank | Evidence / implication | Next experiment | Expected cost |
|---|---|---|---|
| 1 | Very low completion; state/action novelty does not identify the game objective | Learn controllable-object motion and test several explicit reach/collect/transform hypotheses against actual feedback | Several focused development days; score benefit unknown |
| 2 | Full rendered states seldom repeat in initial games; empirical planning has little validated graph coverage | Compare robust visual abstractions with raw frames, retaining contradictory outcomes and checking action usefulness | 1–2 days; risk of merging mechanically distinct states |
| 3 | Click candidates include background/decorative components; extraction dominated one CPU profile | Compare candidate quality and cross-frame click coverage; optimize labeling only if target runtime requires it | Hours to days; coverage experiment already measured below baseline |

Rank is based on observed failure relevance, not a promised score gain. Short action persistence and cross-frame click coverage are the first cheap, measurable attempts to address ineffective exploration. More complex methods need evidence before becoming defaults.

## Limitations and deferred work

General goal inference, temporal object identities, transferable cross-level mechanics, A*, beam search, learned world simulators, hierarchical skills and local model assistance are not implemented. Empty modules or simulated success claims are not substituted for them. BFS is correct and tested, but useful game-solving planning has not been demonstrated. Recovery currently handles invalid predictions, resets and loops; it cannot diagnose arbitrary puzzle semantics.

Development action/time caps are engineering guards, not official competition budgets. Wall-clock profiling is local CPU evidence. Authenticated rules now confirm a nine-hour notebook limit, disabled internet and the November 2 23:59 UTC deadline; attached wheel versions and framework APIs have been inspected. Hardware RAM and hidden evaluation behavior remain unverified. No weights, hosted inference or runtime internet downloads are used by Hydra.

## Deployment boundary

The generated notebooks/submission.ipynb preserves offline competition-wheel installation and gateway-driven submission generation. The private notebook uses kunalsinghh25/arc-hydra-arc-agi-3. A configured project token authenticated; versions 1 and 2 completed on Kaggle. Version 2 also ran public-game smoke validation under the actual attached framework, taking 20 actions per game without exceptions. Submission 57601062 was accepted for competition evaluation. Commit-mode output is not a hidden score; see docs/kaggle_validation.md for scoring status.

This baseline does not justify a first-place performance claim. Its value is the verified adapter, reproducible measurements, and a clear record of which additions help or fail on the public games.
