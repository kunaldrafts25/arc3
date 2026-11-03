# ARC-Hydra v0.2 development — 25 October 2026

The scored v0.1 Kaggle baseline is 0.01 (submission 57601062). All results below
are from the public development environments and do not predict hidden scores.

## Implemented behavior

- Learn monotonic edge meters and exclude only their verified pixels from state
  identity; keep raw observations for mechanics and goal inference.
- Match moving components, infer action displacements, and test navigation goals.
- Discover repeated tile lattices, including tiles containing visible markers.
- Learn binary XOR or prime-length color-cycle effects through interventions.
- Infer small glyph-to-neighbor equality programs from observed example panels;
  retain hypotheses supported by level completions within the same game.
- Solve bounded linear systems and verify each predicted transition. Support
  partial panels and unconstrained cells without inventing a complete target.
- Preserve learned click effects after death only when the reset observation
  matches the original board, excluding the learned meter.

No runtime branch selects behavior by game ID. Public source was inspected to
diagnose observation failures, but the runtime receives only frames and actions.
No hidden game source or private per-game diagnostics were accessed.

## Experiments

The JSONL files under `reports/v02` contain official local scorecard results,
exceptions and action counts. Companion `.source.json` files preserve the full
agent/module sources used by later experiments; their digest is in each row.
The early abstraction and motion pilots predate source snapshots.

| Stage | Scope | Observed result |
|---|---|---|
| Meter abstraction alone | Four games, three seeds, 200 actions | No overall improvement; retained as supporting representation only |
| Motion pilot | Five games, three seeds, 200 actions | LS20 first level in two of three runs |
| Validated reset memory | Four games, three seeds, 200 actions | FT09 first level in all three runs |
| Glyph transfer | FT09, three seeds, 300 actions | Three levels in each run |
| Color-cycle reasoning | FT09, three seeds, 300 actions | Four levels in each run |
| Partial edge constraints | FT09, three seeds, 300 actions | Four, four, five levels |
| Broad intermediate candidate | 25 games, three seeds, 300 actions | Mean score 1.347467538; 25 completed levels; no full wins or exceptions |
| Lattice discovery candidates | FT09, three seeds, 300 actions | Five levels in each run |
| Fully marked lattice recognition | FT09, three seeds, 300 actions | Six levels and full WIN in each run; score 97.377961361 |

The old novelty baseline at 200 actions averaged 0.149725860 over the same
25 games and seeds 0–2, with four completed levels and no full wins. This is
an unequal-budget comparison. `baseline-300.jsonl` and
`release-candidate.jsonl` provide the subsequent equal-budget comparison;
the latter also includes seeds 3 and 4 as additional validation.

## Limits and next decisions

The largest gain currently comes from one public game's puzzle family. Most
public games remain unsolved. The color planner supports prime cycle lengths;
large null spaces use bounded sampling. Navigation still tests uncertain goals
and can waste actions. A matched visual hypothesis is not proof of game victory:
only the official environment's WIN counts as a full completion.

The matched comparison finished: 75 runs per policy at 300 actions, public
environment seed 0, policy seeds 0–2. Baseline mean score was 0.150198925,
with six completed levels and no full wins. Candidate mean was 3.942818150,
with 27 completed levels and three full wins. Both recorded zero exceptions.
All full wins are FT09; this is not broad task mastery. Additional policy seeds
3 and 4 completed all 50 runs: mean score 3.953284272, 17 level completions,
two full wins and no exceptions. Across all 125 candidate runs: mean
3.947004599, 44 completed levels, five full wins and no exceptions.
`reports/v02/comparison.json` contains the coverage-checked, source-digest-checked
summary and per-game comparisons. Reproduce with
`python scripts/report_v02.py --require-complete`.

Kaggle notebook version 3 completed its offline regression: FT09 WIN in 159
actions, two short smoke checks, no exceptions. Competition submission
57630597 was accepted on 25 October, using the one available attempt. Its
official status is recorded in `reports/kaggle/submission-status.json`.
