# Completed verification-guidance comparison

Exact notebook `kunalsinghh25/arc-hydra-duck-verification/1`: COMPLETE.
All 25 public games have verified model gameplay, no crashes or accounting
corrections. Public mean **46.2321**, 102 levels, eight full wins and 4,441,284
action-accounted generated tokens. Original baseline: **43.7621**, 102 levels,
five full wins and 4,331,218 tokens under the same two-hour gameplay budget.

Completed levels at 30/60/90/120 minutes: **36/77/94/102**, versus original
**37/63/84/102**. The mean-score difference is **+2.4700 points** in this single
pass. It does not prove a reliable causal gain or predict hidden performance.

The FT09 model request's actual system message contains the step-verification
addendum. `prompt-activation.json` records the trace and prompt hashes. This
closes the activation check required by `experiment.md`.

Official entry **57686595** was accepted from this exact completed version after
local source hashes matched `upload.json` and the allowance query returned one
remaining entry. Zero entries remain today. Initial official status is PENDING;
the highest official scored result remains original baseline **24.87**.
This public 46.23 is separate from the official competition score.

The per-game comparison has nine improved scores, seven worsened scores and
nine ties; four full wins are common to both runs. R11L, VC33 and CD82 gained
85.71, 78.57 and 64.10 points respectively, while M0R0, CN04 and DC22 lost
71.43, 66.67 and 47.62. Equal aggregate level counts therefore hide substantial
trajectory differences. These unpaired stochastic runs do not establish which
differences come from the prompt, scheduling or sampling. The complete rows
and input hashes are in `per-game-comparison.json`. No game-ID-specific choice
between these variants is deployed.
