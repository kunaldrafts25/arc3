# ARC3 evidence update, 1 November 2026

The matched control completed. Authoritative outputs are under
`reports/kaggle/prediction-matched-control-v1/`, including benchmark, lifecycle,
25 actual model transcripts, serving audit and diagnosis. Public mean score is
31.5812675, 81 completed levels, four full wins and 2,911,914 charged generation
tokens. The whole-notebook cap includes startup: actual gameplay was 4,819.35
seconds. Do not compare this number directly to older two-hour gameplay scores.

Exact inspection was used in 19 games, with 704 queries: 239 read_cells, 216
read_region and 249 row_runs. Of these, 182 have identical logged event metadata
at the same observation/level. **read_cells events omit the requested points**,
so these collisions do not establish repeated identical queries. Measurements
may also be cheap repeated computations inside one snippet; they do not establish
wasted model turns. The transcripts contain
1,675 response metadata records, 7,855,418 reasoning characters and 309 prompts
following no-action snippets. Search and inspection can make no-action turns
useful; these counts alone justify no inference cap or forced exploration.

At the same 4,819.35 seconds of recorded gameplay, historical ultimate/3 scores
29.0047471 with 80 levels and 2,925,742 tokens; historical general-learner/1
scores 38.5342392 with 87 levels and 2,886,132 tokens. The control scores 31.5812675
with 81 levels and 2,911,914 tokens. These are retrospective trajectory prefixes,
with different scheduling horizons, extensions and random draws. They isolate
neither an inspection benefit nor a memory benefit. They reinforce the need to
retain the best memory candidate when considering promotion from this pair.

One inspected no-completion transcript, bp35, still contains uncertainty about
the goal and motion mechanism near its end. Predictions could make specific
incorrect expected changes explicit, but fixed pixel features do not identify a
goal, causal object or hidden state automatically. Read the candidate's actual
forecasts and subsequent decisions before deciding whether the host helps.

Current public implementations were refreshed through the authenticated Kaggle
kernel listing sorted by scoreDescending. This listing's order is not a verified
official score field. Sources were downloaded for reading only, never executed:

* [The AGI Boys | I AM BETTER](https://www.kaggle.com/code/romantamrazov/the-agi-boys-i-am-better)
  is preserved under `reference/kaggle/agi-boys-20261101/`.
* [arc-agi-3-lalalia-final](https://www.kaggle.com/code/vickyfym/arc-agi-3-lalalia-final)
  is preserved under `reference/kaggle/lalalia-20261101/`.
* [CheckedPlan](https://www.kaggle.com/code/evgendvorkin/arc-3-checkedplan-sc25-47-6-tu93-22-2)
  is preserved under `reference/kaggle/checkedplan-20261101/`.
* [Try merging it](https://www.kaggle.com/code/heliosli/try-merging-it-you-might-get-lucky-and-win-gold)
  is preserved under `reference/kaggle/merge-20261101/`.

All four attach the same Intel Qwen3.8 Flash Next W4A16 target and Albucino draft
as ours. All four contain the same base harness patch, SHA256
6fdcd1ae7445c0cfc26eec1047363aa0c196c867d289a35b6f64403b5a43dce2.
In particular the merging notebook's title is not evidence of different weights:
its attached model versions remain the same. No inspected source establishes a
new compatible checkpoint or a path to the leading 75.56 score.

Lalalia's introduction reports 31.46 official for solved-level memory and says
compact prompts / 12 streams instead of 10 looked neutral publicly but regressed
by approximately 7–8 points in hidden scoring. These are the author's claims;
the claimed Paper Track ablation artifact was not retrieved or independently
reproduced. Do not treat them as our controlled evidence. Its implementation
captures the winning attempt's last 30 actions, last 900 reasoning characters,
and a model-supplied rule; it retains full details for the latest three solved
levels and refreshes a system-prompt suffix only at existing history trims.
Attribution cites rellik13/sirikilohit's M85 idea, CC-BY 4.0, plus Franzen/Tufa.
No code from this source has been integrated into our agent in this update.

The useful distinction from our study-memory API is automatic retention of
completion witnesses even if the model never writes a note. A completion witness
is stronger evidence that a particular trajectory worked than self-labeled
"supported" notes, but the last reasoning text and extracted rule remain model
claims. A level-number jump must not fabricate witnesses for missing intermediate
levels; actions before a reset must not contaminate the successful attempt;
cross-level transfer still requires checks. Any later implementation should
preserve these distinctions and the ordinary action/accounting guarantees.

CheckedPlan adds local motion extrapolation and interrupts snippets on contract
mismatch or boundaries. This overlaps our already-tested verification direction,
with stronger action interception. Its public title covers selected public games,
not all-game or official evidence. We have already measured a regression from
mandatory planning in our own experiments. Do not adopt interception merely
because its synthetic contracts pass.

The broader mount/cache incident was rechecked through the public news index,
but direct Kaggle discussion pages 752147 and 751756 returned no readable body
through web extraction. The secondary report is not evidence of our submission's
hidden execution path. The completed control actually initialized and played all
25 games. Our nonzero official/public gap has no demonstrated cache explanation.

Next decision remains empirical: complete the accepted prediction run, inspect
adoption/counterexamples and actual trajectories, compare matched capped results,
then decide whether to reject it or combine validated useful behavior with the
stronger retained memory candidate. Neither passing tools nor a public gain meets
the objective; an official evaluation against a freshly checked leader is required.

## Observation-history audit and tested memory composition, 07:52 UTC

The next CPU diagnostic replayed the same 15,476 actions twice, with all 25 game
action/level counts and all 25 prior replay pixel digests matching. Source and
script hashes are in `reports/research/arc3-observation-aliases/`. V1's exact
script is preserved as `audit-v1.py`; the current V2 script adds animation and
matched-coverage diagnostics. Neither script selects new actions or inspects game
implementations. Its lookup is frozen before each environment step.

Across 15,130 non-boundary actions, full final-frame pixels plus available actions,
exposed state, completed-level count and the next action produced 501 previously
seen keys. Predicting the last observed outcome was wrong 100 times; 98 distinct
keys had multiple observed outcomes. Mismatches were five UNDO, 70 MOUSE, eight
LEFT, four RIGHT, nine SPACE, one DOWN and three UP. Thus this is not solely the
expected history dependence of UNDO. These counts establish inconsistent next
observations under this visible key, not the cause: latent modes, stochasticity,
reset-dependent conditions and unmodeled history remain possible.

Including the latest public animation sequence leaves 456 predictions and 95
errors. One preceding final-frame/action pair leaves 369 predictions and one
error; two pairs leave 348 predictions and zero errors. This is mostly an
abstention effect. At exactly the 369 positions predicted by the one-pair key,
the state-only predictor makes three errors versus one. At the 348 two-pair
positions it makes two errors versus zero. Without these matched counts, claiming
that history solves the problem would overstate the result. Even the state-only
lookup abstains on 14,629/15,130 actions (96.69%). Exact transition memorization
cannot serve as the main unfamiliar-state model in this evidence.

This supports retaining history-conditioned hypotheses and rejecting claims that
pixel identity certifies complete state. It does not establish that enabling a new
warning, changing existing guards, or adding another lookup API improves gameplay.
No such action-policy change was made from the audit alone. Current prediction
tools already allow forecasts conditioned on the model's history interpretation;
the ongoing model run must establish whether it uses that capability well.

In parallel, the existing study-memory/guidance extension was composed onto the
unchanged optional prediction/inspection base. CPU gate
`kunalsinghh25/arc-hydra-prediction-study-cpu-probe/1` is COMPLETE, with downloaded
evidence in `reports/kaggle/prediction-study-cpu-probe-v1/`. It passed all 12
prediction cases, nine study cases, eight base mechanical cases and 16 rendered
prompt combinations. Four new actual host/child composition checks establish:
one call persists both kinds of evidence; a new ToolAgent/empty context restores
both panels and exact inspection; one ordinary action can update a note and a
measured counterexample; and separate game paths isolate both stores.

New files: `scripts/build_prediction_study_probe.py`,
`scripts/prediction_study_agent_probe.py` and
`scripts/build_prediction_study_notebook.py`. The existing CPU launcher now has
an explicitly restricted `--study-combination` path with a 1,800-second CPU
timeout, private/offline/no-model/no-competition metadata, exact source validation
and an exclusive mutation journal. It checked ARC2 development COMPLETE and paid
scaling disabled before launching. This gate consumed no GPU quota.

`notebooks/prediction_study_candidate/` is staged with the completed exact CPU
gate hashes and source checks. Its builder rejects budgets above 7,200 seconds,
including startup and the 600-second finalization reserve, and marks it ineligible
for official submission. It has NOT been uploaded or GPU evaluated. It is an
option if measured prediction use is worth carrying into a memory candidate;
CPU compatibility is not promotion evidence. The accepted frozen GPU prediction
pair and its package hashes were not changed, and no extra GPU job was launched.
