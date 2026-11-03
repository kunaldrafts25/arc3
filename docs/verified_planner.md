# Verified-planning candidate

This is a new experimental agent variant on the original attributed Duck/M2
model and runtime. Its score benefit is unverified. It does not replace the
official 24.87 baseline until actual gameplay and competition evidence support
promotion.

## Mechanics

`action(...)` permits one exploratory action per Python tool call. This permits
first-contact learning without a simulator. Unverified batches and a second
exploratory action in the same call are refused before they spend actions.

`verify_model(predict, encode=None, max_checks=512)` tests the proposed model
against eligible recorded transitions in the current level. Resets, automatic
transitions, missing prior frames and level boundaries are excluded and counted.
It returns coverage, errors and the first concrete counterexample. No checks,
abstentions, truncation, contradictions and constant abstractions cannot certify
a plan. A larger history can explicitly request up to 4,096 checks.

`execute_plan(actions, predict, encode=None, max_steps=12, max_checks=512)`
performs replay checks itself, then predicts and executes one real action at a
time. It stops on unknown predictions, a mismatch, refusal, no gameplay change,
or a level/game boundary. Its per-plan limit is at most 16 steps.

The default model state is a copied JSON-style grid. A supplied encoder can
extract a JSON-style object/state representation; a prediction must return the
next representation or `None` for unknown. Abstract-state checking is explicitly
reported and does not establish pixel-exact prediction. Prediction/encoding
callbacks cannot spend actions through the exposed API. Stored helper functions
continue to use the existing per-game retention mechanism.

Replay agreement is consistency with observed evidence, not proof that mechanics
or goals are correct. An abstraction can omit important variables despite varying
on historical examples. Prospective tests and goal hypotheses remain necessary.
These helpers are not a security boundary against adversarial introspection of
Python objects; the existing sandbox permissions are retained.

## Integration and diagnostics

The current optional variant is `planning-assist`. It preserves original ordinary
action batches/repeated calls and host results/guards; callbacks still cannot
spend actions, and checked plans retain replay and prospective validation.
Its guidance does not require a simulator to play. Ordinary action accounting
comes from the original benchmark, not helper events. This revision follows the
completed 25-game result of 45.0150 baseline versus 33.1771 strict planner;
causes are not isolated by that single stochastic pair. CPU probe v5 passed
eight sandbox cases and 16 user-prompt combinations for optional mode. The
Ultimate Candidate tests that revision with the same model/runtime/scheduler.

The installer patches the notebook-local writable source copy before unpickling
the solver. It validates expected source anchors and compiles both modified files
before writing. Source hashes are retained in `hydra_extension.json`. The old
instructions allowing arbitrary unchecked batches are rewritten to match the new
contract; the full contract is appended to the rendered system prompt.

Extension v2 also rewrites the per-turn user prompt. Actual pilot transcripts
revealed that extension v1 left repeated user instructions encouraging unchecked
batches and repeated exploratory actions. The model explicitly noticed the
conflict. CPU probe v3 checked the system prompt only, so its consistency result
was narrower than the full conversation. Probe v4 adds 16 rendered user-prompt
combinations covering memory, duplicate guidance, opener hints and initial versus
resumed turns, alongside the same seven mechanical sandbox cases. All pass on
the actual Kaggle bundle. The checker library/sandbox code is unchanged. Current
GPU notebook `verified-planner/2` remains the uploaded v1 extension; do not
attribute the v2 fix to that run or infer a measured score gain from CPU checks.

Mechanical events cross the sandbox RPC separately from model-written stdout
and are saved as `artifacts/*.hydra-events.jsonl`. The event analyzer measures
replay checks, refusals, completed planned actions and mismatches. Interrupted
tool calls can lack a final event payload, so counts are not complete accounting
of every action or token.

The candidate checks model readiness in public and competition runs. A shared
global deadline includes startup and reserves ten minutes for finalization.
`hydra_lifecycle.json` records startup, health, running counters and final state.
The run raises an explicit error if it finishes without substantive model-driven
gameplay; a legitimate zero-level run with real actions is kept distinct.

The five-game preflight uses competition-style minimal diagnostics on public
environments and explicitly saves benchmark metrics. It does not yet reproduce
the hidden gateway or establish full competition-path parity. A full 25-game
comparison and eventual official evaluation remain necessary.

## Validation sequence

1. Local semantic tests and real sandbox-protocol execution.
2. CPU/Linux integration against the actual original Kaggle bundle, including
   patch application, seven synthetic execution cases and prompt consistency.
3. A private GPU preflight on the existing five public diagnostic games for
   900 seconds after model readiness. Verify helper adoption, actual actions,
   lifecycle evidence and model/game failures.
4. If the agent uses the mechanism successfully without excessive overhead,
   compare with the original on all 25 games under matched budgets. Report
   per-game differences and sampling variability before selecting a submission.

No hard-coded game-specific solver, new model checkpoint or v3 runtime is added.
The original Franzen / Cottaar / Tufa attribution and third-party notices remain.
