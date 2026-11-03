# First mechanically verified planner GPU pilot

Exact notebook: `kunalsinghh25/arc-hydra-verified-planner/1`.
Original model, draft checkpoint, v2.5.3 runtime and scheduler retained.
No Swift, rolling summaries, v3 runtime, new weights or game-specific policy.

The agent can take one unmodeled exploratory action per Python tool call.
Its checked-plan helper validates its proposed model against eligible recorded
current-level transitions, then compares predictions after every executed step.
Unknown predictions and contradictions stop the batch; no model does not block
single-action exploration. Encoding/prediction functions cannot call real actions
through the exposed API. Abstract checks do not establish full-grid correctness.

All 84 local tests passed. Exact-source CPU probe version 3 completed all seven
synthetic integration scenarios and prompt-contract consistency on Kaggle Linux.
The candidate helper/installer hashes were checked against that gate.

Pilot: FT09, LS20, R11L, VC33, BP35 — the same existing diagnostic set, one pass,
900 seconds after readiness. Competition-style minimal diagnostics are enabled
on these public environments, with explicit final benchmark serialization.
Startup health is mandatory, global competition finalization reserve is 600
seconds, and lifecycle counters persist separately from benchmark diagnostics.

Inspect before promotion:

1. Startup/health/termination artifacts and explicit model gameplay in all five
   games. An uploaded or completed notebook alone is insufficient.
2. Actual persisted `*.hydra-events.jsonl` files, analyzed with
   `scripts/analyze_verified_events.py`: whether the model invokes replay/plan
   helpers, responds to counterexamples and uses single probes appropriately.
3. Action/level progress and token/time overhead. A strict action policy may
   harm games that the model cannot represent; do not assume this architecture
   is beneficial merely because its mechanical tests pass.
4. A full matched 25-game comparison if the pilot justifies it. This five-game
   pilot is not an official score forecast or proof of >71.48.

The candidate adds lifecycle checks and action semantics together, so this first
run is an integration/adoption test, not a clean attribution study. It does not
yet simulate the real hidden gateway. Preserve the scored 24.87 baseline.
