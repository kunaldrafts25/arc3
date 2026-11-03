# ARC-Hydra Ultimate Candidate

An experimental candidate informed by a completed 25-game comparison: original
agent **45.0150 / 103 levels / 5 wins**, strict planner **33.1771 / 75 levels /
4 wins**. All games had substantive model gameplay. One stochastic pair does
not isolate causes or predict hidden performance. Do not promote the strict run.

The current candidate preserves ordinary batches and repeated calls, with optional
`verify_model` and checked `execute_plan`. It retains the original model/draft,
v2.5.3 runtime and scheduler. Shared readiness, lifecycle records, ten-minute
competition finalization reserve and exact-name input resolution are included.
Model weights are frozen. There is no game-ID-based routing or public solver.

The builder checks source hashes against completed offline CPU probe **v5**,
which passed eight sandbox cases and 16 rendered user-prompt combinations.
This validates integration, not GPU inference, gameplay gains or hidden scores.
Original attribution and license notices remain in the notebook.

Build and run the full public benchmark:

```powershell
.venv/Scripts/python.exe scripts/build_ultimate_notebook.py --mode benchmark
.venv/Scripts/python.exe scripts/kaggle_local.py kernels push -p notebooks/ultimate_candidate --timeout 12000
```

The benchmark uses all 25 games for 7200 seconds after readiness. An optional
`--mode preflight` uses five games for 900 seconds. Private, internet-disabled,
RTX PRO 6000, no official submission or paid scaling.

Versions 1 and 2 failed before model loading because dataset/competition inputs
used short mount names. Version 3 resolves all required inputs, including the
competition wheels/public environment path, and is the active benchmark.
Preserve exact uploaded-version provenance. Official competition reruns use the
competition budget and global finalization reserve. Require final gameplay,
coverage, helper adoption and error analysis before promotion/submission.

Retain the official best submission until stronger evidence justifies promotion.
Goal: official 100, or beat the latest verified competing leader; public scores
cannot establish completion.
