# Step-verification guidance experiment

Exact run: `kunalsinghh25/arc-hydra-duck-verification/1`.

Hypothesis: the existing general instruction to check predicted effects in code
and revisit mechanics/goal/search assumptions can improve action efficiency and
completion under the current budget. The baseline does not enable
`ARC3_STEP_VERIFICATION_HINT`. This is a prompt experiment, not a new perception
tool or an automatic simulator validator.

Motivation: the baseline SK48 trace repeatedly reinterprets the wire/block
mechanics before attempting BFS. Its last five completed responses at action
counter 94 consumed 27,706 completion tokens. This may be useful reasoning;
the observation does not justify cutting it off or establish the cause of the
game's failure. The experiment asks whether the already-implemented general
verification guidance helps the model use evidence more effectively.

Only override: `ARC3_STEP_VERIFICATION_HINT=1`, exported before harness startup.
The original model, runtime, draft, tools, memory configuration and scheduler
remain unchanged. Rolling summaries and the v3 runtime overlay are excluded.
Distinct private notebook ID; 25 public games, one pass, 7,200 seconds after
model readiness. Startup allowance is 3,600 seconds. No competition entry made.

Thirteen packaging/runtime tests passed, including a check that this variant
changes only the configuration cell and preserves serving/data/model settings.
Source hashes are recorded in `upload.json`.

Before interpreting results:

1. Verify the step-verification addendum appears in a recorded model system
   prompt. An environment override alone does not prove execution.
2. Verify substantive model gameplay for all 25 games and analyze final metrics.
3. Compare mean score, levels, full wins and completion curves with original
   43.7621 / 102 levels / five wins under the matched public budget.
4. Keep the original official 24.87 agent until evidence supports promotion.
   A single public pass is not a causal estimate or a hidden-score forecast.
