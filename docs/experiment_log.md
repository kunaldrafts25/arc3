# Experiment log

Erratum: the initial policy named novelty still consulted transition predictions, so its original rows are not a clean model-disabled ablation. They remain preserved in the raw logs. The corrected policy forbids model training and prediction while retaining raw transition evidence. Final comparisons replace the affected novelty rows with reports/novelty-corrected-v01.jsonl. A regression test enforces the boundary. The original six-policy run produced 450 rows with no per-run exceptions; memory and planning had zero model predictions and zero planned actions.

Date for all initial experiments: 2026-10-24 (Asia/Calcutta). Local public development results only. No leaderboard results or hidden evaluation claims.

## SETUP-01 — official baseline and Windows portability

- Agent version: unmodified starter at eeb1535.
- Hypothesis: the official local loop runs on this Windows Python 3.12 machine.
- Commands: `py -3.12 -m venv .venv`; pip install official dependencies; `python scripts/slim_framework.py`; `python -m pytest vendor/ARC-AGI-3-Agents/tests -q -p no:cacheprovider`; `python scripts/play_local.py --game ls20,vc33 --max-steps 50`.
- Failures: sandboxed ensurepip could not write temporary wheel files; approved environment setup succeeded. Original slim_framework wrote cp1252 Python source that could not import as UTF-8. First real ls20 run completed 51 commands and 0 levels, then terminal output failed on a Unicode arrow. Both Windows issues were corrected explicitly.
- Upstream suite after encoding fix: 4 collection errors (missing agents.structs and openai). Independent recorder suite: 19 passed.
- Decision: KEEP UTF-8 source writing and ASCII terminal status; preserve framework interfaces.

## BASE-01 — reproducible official starter smoke

- Commands: `python scripts/benchmark.py --bootstrap --policies starter --seeds 0 --steps 50 --games ls20,vc33 --output reports/starter-smoke.jsonl`; then all public games into reports/public-starter-smoke.jsonl.
- Baseline policy: pristine source loaded by git show; RNG reseeded deterministically after construction. Budget wrapper enforces equal exact caps, correcting the base loop's extra command.
- Evaluation: 25 advertised public games, policy seed 0, environment seed 0, 50 commands per game.
- Results: all 25 runs completed without exceptions. Detailed completions, action counts and scorecards in JSONL. This is a smoke check, not evidence of competitive play.
- Decision: KEEP as reproducible comparison.

## HYDRA-01 — legal actions, novelty, memory, empirical frontier planning

- Agent version: 0.1.0.
- Hypothesis: advertised action filtering and count-based exploration outperform the starter.
- Components: observation encoding, transition outcome counts, conservative repeated-edge predictions, bounded BFS, cycle recovery, per-instance RNG, validated click coordinates.
- Evaluation: ls20 and vc33; policy seeds 0,1,2; environment seed 0; 200 commands per game.
- Command: `python scripts/benchmark.py --policies starter,random,novelty,memory,planning --seeds 0,1,2 --steps 200 --output reports/ablation-v01.jsonl`.
- Baseline: 0 levels over 6 runs, mean local score 0.
- Legal random: 3 completed levels over 6 runs, mean local score 0.028675099667001106 on the 0–100 scale. All completions were vc33 level 1, once per seed; no full game wins.
- Novelty / memory / planning: each 1 completed level over 6 runs, mean local score 0.003682195009047679. These policies produced identical scores, so the extra model did not show a gain.
- Median runtime: starter 0.344 s; legal random 1.758 s; novelty 1.484 s; memory 1.640 s; planning 1.586 s. Component click candidate extraction adds CPU work.
- Exceptions: 0. ls20 remained unsolved. Very few repeated rendered states; no meaningful planning advantage demonstrated. Timers/animation/hidden state are candidate explanations, not a verified causal diagnosis.
- Decision: INVESTIGATE on the full public set; do not promote planning based on architecture alone.

## HYDRA-02 — full public ablation and temporally coherent experiments

- Hypothesis: holding simple actions for short sampled runs improves spatial exploration compared to changing action every step.
- Changed components: persistent policy holds IDs 1–4 for runs of length 2,4,8, stops after exact no-op, rechecks legality each step; never repeats coordinate clicks as an open-loop option.
- Evaluation: all 25 public games, policy seeds 0,1,2, environment seed 0, 200 commands. Six policies: starter, random, novelty, memory, planning, persistent.
- Command: `python scripts/benchmark.py --policies starter,random,novelty,memory,planning,persistent --seeds 0,1,2 --steps 200 --output reports/public-ablation-v01.jsonl`.
- Results: 75 runs per policy. Starter mean 0.061294 (3 level completions); random/persistent each 0.075703 (6); memory/planning each 0.149726 (4), on the 0–100 scale. No full wins. Legacy novelty rows are superseded as described in the erratum.
- Decision: no measured benefit from persistence or planning. Do not promote them to the production default. Preserve optional variants for reproducibility.

## HYDRA-03 — click coverage under changing rendered states

- Hypothesis: tracking tested click locations across frames reduces repeated uninformative probes when full-frame state keys change continually.
- Components: bounded level-local click counts, least-tested candidate bonus; active only in click-only states. Other states use memory exploration.
- Evaluation: all 25 public games, policy seeds 0,1,2, environment seed 0, 200 commands.
- Command: `python scripts/benchmark.py --policies coverage --seeds 0,1,2 --steps 200 --output reports/coverage-v01.jsonl`.
- Results: 75 runs, 3 level completions, 0 full wins, mean local score 0.008066. All completions were r11l level 1. Zero recorded exceptions.
- Decision: REVERT as a default candidate; cross-frame click suppression did not improve the measured objective. Retain only as an experimental policy.

## HYDRA-04 — ablation correction and seed confirmation

- Hypothesis: separating the novelty action-count policy from the transition model gives an interpretable ablation; additional policy seeds test whether the apparent gain repeats.
- Correction: novelty neither trains outcome distributions nor consults their predictions. Bounded raw transition tuples are still retained for debugging.
- Commands: `python scripts/benchmark.py --policies novelty --seeds 0,1,2,3,4 --steps 200 --output reports/novelty-corrected-v01.jsonl`; `python scripts/benchmark.py --policies memory --seeds 3,4 --steps 200 --output reports/memory-confirmation-v01.jsonl`.
- Baseline/random confirmation: seeds 3,4 in reports/confirmation-v01.jsonl; its legacy novelty rows are superseded and excluded from the final report.
- Evaluation: the same 25 public games, fixed environment seed 0. These are additional policy seeds, not held-out games and not evidence of hidden-set generalization.
- Results: corrected novelty and memory each averaged 0.1491665471 over 125 runs (25 games × 5 seeds), with 9 level completions and 0 full wins. Starter averaged 0.0374617995 with 4 completions; legal random averaged 0.0584301651 with 9. On separate seeds 3,4, novelty/memory averaged 0.148328; starter 0.001714; random 0.032521. All scores are on the 0–100 scale.
- Decision: KEEP corrected novelty as the simpler default. Transition prediction/planning remain experimental because neither improved its result. Final consolidated reports contain 525 training rows and 200 confirmation rows, all complete and without recorded exceptions. Additional policy seeds are not held-out games.

## FINAL-01 — production default and notebook verification

- Selected policy: corrected novelty with bounded raw transition tracking and legal action validation.
- Command: `python scripts/play_local.py --offline --game ls20,vc33 --max-steps 50`.
- Result: ls20 0 completed levels / 50 commands; vc33 1 completed level / 50 commands; aggregate local scorecard 0.08034894398530763. This short-ID smoke run uses the helper's normal game identifiers and is separate from full-ID seeded benchmark comparisons.
- Tests: `python -m pytest -q` → 19 passed. An earlier final check exposed that the model-reset test implicitly relied on the old default; it now explicitly selects the memory policy it tests.
- Packaging: `python scripts/build_notebook.py` and `python scripts/verify_notebook.py` succeeded. Bundled source imported and emitted a validated ACTION6 in a fresh isolated interpreter. `pip check` found no broken dependencies.
- Boundary: no Kaggle token was present. No remote notebook execution, hidden competition rerun or successful competition submission has been asserted.

## KAGGLE-01 — authenticated deployment

- The user configured a new project-local token. Authentication and prior competition entry were confirmed without displaying credentials.
- Verified official pages: nine-hour runtime, disabled internet, one submission/day, 110 private games, final deadline November 2 at 23:59 UTC. Attached arc-agi 0.9.8 / arcengine 0.9.3 interfaces and scorer were inspected.
- Deployment fix: send per-agent payload copies directly to the verified wrapper so concurrent games are not serialized by a shared HTTP lock. Extend the per-game wall guard to 600 seconds; action cap stays 200. No policy-score gain is claimed from these changes.
- Kaggle notebook v1: COMPLETE with expected commit-mode parquet.
- Kaggle notebook v2: COMPLETE; actual offline public smoke ran 20 actions each on ls20/vc33, no exceptions. The smoke cell is skipped during competition rerun. Full local suite: 21 passed.
- Submitted notebook v2 as competition submission 57601062. Kaggle accepted it, leaving zero daily submissions. Initial scoring status PENDING, with no score yet. Live status is recorded in reports/kaggle/submission-status.json.
- Decision: KEEP as the first validated deployment baseline; evaluate the actual competition result before claiming hidden-set performance.

## KAGGLE-RESULT-01 — first scored submission

- Submission: 57601062, notebook version 2.
- Official API result: COMPLETE; public score 0.01; private score unavailable; evaluation error empty.
- Own-submission download: HTTP 403. Per-game metrics remain unavailable; no alternative access path was attempted.
- Interpretation: valid scored baseline with weak performance; do not infer hidden completion/action counts or assign a specific failure cause from this aggregate alone.

## BUDGET-01 — test the 200-action guard

- Hypothesis: the small development cap substantially limits completion.
- Components changed: benchmark cap only, 200 versus 1,000 commands; same novelty policy and official loop.
- Games: cd82, ls20, r11l, vc33; policy seeds 0,1,2; environment seed 0.
- Baseline: 12 runs, 2,400 commands, 4 completed levels, 0 full wins, mean local score 0.9357866260, median runtime 1.812 s.
- Candidate: 12 runs, 12,000 commands, 6 completed levels, 0 full wins, mean local score 0.9359760621, median runtime 7.1015 s.
- Exceptions: 0. Failures: cd82 and ls20 remain unsolved; r11l stops at one completed level; two additional vc33 first-level completions are highly inefficient.
- Decision: INVESTIGATE mechanics/goal inference next; do not promote the fivefold cap globally from this small gain on four games.
- Independent guard fix: start the per-game timer when main begins, excluding Swarm construction waits. Local behavioral test verifies play still occurs after a simulated long setup wait. 22 tests pass. No hidden-score benefit is claimed; this source change has not been submitted.

An early persistence run started while the game cache was still populating, was interrupted, and is excluded from comparisons (reports/persistence-v01.jsonl). Complete comparisons use the stable 25-game cache. Tests, bookkeeping, portability and failure isolation are retained for correctness independently of policy score.

## PROFILE-01 — identify CPU cost before optimizing

- Command: `python -m cProfile -o reports/profile-v01.prof scripts/benchmark.py --games vc33 --policies memory --seeds 0 --steps 200 --output reports/profile-run.jsonl`.
- Measured under profiling with other experiments running: agent loop 4.448 s; choose_action 4.076 s; connected-component extraction 3.858 s (197 calls).
- Interpretation: component extraction dominates policy CPU time in this click game. This is a measured runtime hotspot, not the main demonstrated scoring failure: total time is still below the local guard, while goal-directed completion is weak.
- Decision: INVESTIGATE vectorized/run-length labeling later if actual Kaggle runtime is binding. Do not add an unverified binary dependency merely to optimize local speed. Profile timings are not target GPU/runtime estimates.

## MECHANICS-02 — learned mechanics and visual goals, 25 October 2026

- Hypothesis: intervention-based motion/tile models and example-based visual
  goals will outperform state novelty when action effects are regular.
- Changes: meter abstraction, inferred displacement controls, binary XOR and
  prime-cycle models, observed glyph equality/inequality programs, partial-panel
  constraints, marked-tile recognition and prediction checks. No game-ID policy.
- Evidence: `reports/v02` raw local scorecards and source snapshots. Intermediate
  experiments and failure diagnoses are described in `docs/v02_development.md`.
- Matched comparison: all 25 public games, environment seed 0, policy seeds
  0–2, strict 300-action cap, 75 runs each. Novelty mean 0.150198925, six level
  completions, no full wins. Candidate mean 3.942818150, 27 level completions,
  three full wins. Neither recorded exceptions.
- Concentration: all full wins are FT09. The candidate regresses on some games;
  gains do not establish a generally capable solver or unseen-task accuracy.
- Additional policy seeds 3 and 4 are evaluated separately. They change policy
  randomness, not game layout, and do not constitute unseen tasks.
- Additional-seed result: 50 runs, mean 3.953284272, 17 completed levels, two
  full wins, no exceptions. All 125 candidate runs: mean 3.947004599,
  44 completed levels, five full wins, no exceptions. Coverage/source digests
  validated by `scripts/report_v02.py --require-complete`; per-game summary in
  `reports/v02/comparison.json`.
- Local validation: 38 tests pass; extracted notebook source imports and chooses
  a legal complex action in an isolated interpreter.
- Target validation: private Kaggle version 3 COMPLETE; six FT09 levels and WIN
  in 159 actions, plus LS20/VC33 smoke actions, no exceptions.
- Decision: PROMOTE v0.2 reasoning/300 as the measured candidate; retain novelty
  for comparisons. Submitted as 57630597, initially PENDING, no evaluation error.
  This used the available daily attempt. Hidden results must come from the
  official status API, independently of these public measurements.

## TRANSFER-02 — official result and model-agent pivot

- Official v0.2 submission 57630597: COMPLETE, score **0.02**, no evaluation
  error. Its strong public FT09 gain barely transferred to hidden games.
- Decision: reproduce a publicly released model-driven coding agent rather
  than continuing to optimize only the public puzzle-specific mechanisms.
- Source: Daniel Franzen's Apache-2.0 Milestone 2 release, crediting Jeroen
  Cottaar and Tufa Labs. Source notebook SHA and original mounts are preserved
  in `baselines/duck_m2`. Author reports 27.89; our hidden score is unmeasured.

## MODEL-01 — completed real Kaggle preflight, 25 October 2026

- Private notebook `kunalsinghh25/arc-hydra-duck-m2-baseline/1`: COMPLETE.
  RTX PRO 6000, pinned model/drafter and offline Pennyroyal runtime verified.
- Scope: five public games, one pass, 900-second rollout deadline. Server
  readiness occurred about 20 minutes after launch, leaving only about six
  minutes of model-ready gameplay in that rollout.
- Results: seven completed levels, no full wins, 119 actions, subset mean
  11.397576782. FT09 four levels; LS20/R11L/VC33 one each; BP35 zero.
- Per-action plus terminal generation: 135,986 tokens. The first summary
  incorrectly used terminal-turn tokens as totals. The auditor reconstructs
  totals from raw `benchmark.json` and records corrections without modifying
  the downloaded summary. Cancellation notes may include additional uncharged
  generation. Regression test added.
- Decision: runtime/gameplay preflight passed; proceed to all 25 games. This
  subset mean is not comparable to the 25-game v0.2 mean or the hidden score.

## MODEL-02 — full public model baseline, running

- Notebook version 2: uploaded and official status RUNNING.
- Agent/model/prompts/serving unchanged. One pass on all 25 public games, two
  hours of gameplay after model readiness, one-hour startup allowance,
  12,000-second notebook timeout. Upload hashes are in
  `reports/kaggle/duck-m2-benchmark-v2/upload.json`.
- Public wait now checks model health/process state before assigning gameplay
  deadline. Competition behavior remains original for this reproduction.
- Separate, unuploaded contest candidate adds an absolute notebook deadline
  with a 600-second finalization reserve. It counts setup time and uses the
  existing cancellation mechanism. It changes lifecycle budget only.
- Local checks: 46 pass. Model-02 performance remains unmeasured until actual
  run artifacts arrive; do not promote it from tests or RUNNING status alone.

## REQUEST-AUDIT-01 — identify the next bottleneck

- Completed Model-01 request logs contain 107 completed responses and 143,977
  response-usage tokens. This includes completed analysis with no associated
  action, unlike the 135,986 action-plus-terminal accounted tokens. In-flight
  generation is excluded from both totals.
- Deduplicating retained conversation tool results by call ID gives 102 visible
  results, three ordinary errors (syntax, type and empty-iterable errors), and
  one expected stale-action guard stop. Repeated history is not counted as
  repeated failures. Per-game weighted cached-prompt fractions are 89.26–93.91%.
- Source-file digests and per-game metrics are in `request-audit.json`;
  `scripts/profile_duck_requests.py` reproduces the audit from the cached logs.
- Decision: no blanket tool/parsing rewrite from these data. Inspect the longer
  run for context-loss and scheduling failures. The public D-prime author also
  reports baseline resubmission variance (27.62–31.47) overlapping the single
  31.54 D-prime result, so that comparison alone is insufficient to select it.

## SERVING-V3-BUILD-01 — independent CPU runtime experiment

- Private CPU notebook `kunalsinghh25/arc-hydra-pennyroyal-v3-build/1`: RUNNING.
  Online build only, no competition attachment, no model weights, four-hour cap.
- Source pinned to upstream v3 commit 560edbdca18aedae13f71ae20b3984efa4d22633.
  Compiler package versions and micromamba artifact hash are frozen. Existing
  INT4 scale-dtype compatibility fix is retained and attributed to Franzen.
- Actual live log verifies CUDA SM120f compiler probe success and ongoing native
  Rust compilation. Final kernel build/offline reinstall are still unverified.
- Required outputs: frozen delta wheels, compiler assets, license notices,
  manifest, and `BUILD_COMPLETE` only after fresh offline-install checks.
- Decision: prepare a possible throughput/context improvement without changing
  the running v2.5.3 model baseline. GPU inference and score comparisons remain
  mandatory before using this runtime in a scored candidate.
- Local checks now total 48 passes; CPU build syntax and embedded source also
  validated. Accelerator quota snapshot shows 4.1103 of 30 GPU hours used and
  pay-to-scale disabled. No quota or billing setting was changed.
## 2026-10-25: runtime dependency repair and prepared GPU integration

CPU build `arc-hydra-pennyroyal-v3-build/1` failed after successfully building the
native SGLang wheel. The final log identifies missing architecture requirements
of the cache umbrella at `pip check`; sitecustomize also lacked wrapt. Resolve
the umbrella dependencies, pin wrapt, and retain all fresh offline checks.
Hash-verified native wheel reuse avoids repeating Rust compilation. Private
dataset `kunalsinghh25/arc-hydra-retained-v3-native-wheel` is ready. Repair v1
failed because Kaggle rejected the failed build's kernel input. Repair v2 uses
that dataset but failed early because Kaggle stripped `+` from its wheel name.
The official dataset file listing verified that transformation. Version 3 handles
the sanitized name, verifies its content hash and restores the wheel filename;
it is the current CPU-only experiment, with a 14,400-second cap.
Its live log confirms wheel hash verification and the SM120f compiler probe
passed; official version-3 status is RUNNING at 16:35 UTC. Latest unfinished
GPU baseline public mean observed: 30.21. Both jobs remain live.

Prepared `install_overlay.py` plus separate offline notebook hooks require a
verified completed artifact and its manifest SHA. Not yet GPU tested or uploaded.
50 local tests and Bash syntax checks passed. The running baseline is unchanged;
latest unfinished public snapshot mean 28.19, two full wins. No new official
competition score and no evidence yet of a score above 71.48.

## 2026-10-25: completed baseline and rolling-summary experiment

GPU baseline version 2 COMPLETE: public mean 43.7621, 102 levels, five full wins,
all 25 games with model gameplay. No accounting correction was needed. Level
completion curve at 30/60/90/120 minutes: 37/63/84/102. Per-action wallclock is an
elapsed timestamp; summing those fields would overcount runtime. Final metrics
and six weak-game request audits are retained in `reports/kaggle/duck-m2-benchmark-v2`.

BP35 spent 58,236 completion tokens over 16 responses at one action counter and
had three large prompt reductions. This suggests testing memory retention;
neither causality nor waste is established. Matched all-25-game rolling-summary
experiment `kunalsinghh25/arc-hydra-duck-summary/1` is RUNNING, same model/runtime
and two-hour gameplay budget. Enable upstream periodic summaries (49,152 new
tokens, 4,096 output cap), current-turn context and summary-aware drains. No
summary result yet; require actual summary production before comparison.

CPU repair v3 ERROR after passing dependencies: missing cuBLAS development header
during FlashInfer build. Repair v4 uses Torch's installed library files to extend
the compiler overlay and is RUNNING. No GPU runtime improvement established.
GPU quota checked before the memory experiment: 24.42 of 30 hours remaining.
51 local tests passed. Official hidden score remains 0.02 and the >71.48 goal is
still active. Exact version hashes and observer handles are in `docs/goal_71.md`.

Follow-up: official submission-limits read still reports zero remaining today.
CPU repair v4 and summary GPU v1 were re-polled RUNNING, so both are preserved.
Corrected diagnostic classification of `TerminalStateActionError`: an expected
terminal-state guard stop, not an ordinary Python error. Regenerated six-game
audit now has 23 ordinary errors, seven stale-state stops and one terminal-state
stop; two targeted tests pass. Raw traces and final scores are unchanged.

## 2026-10-25: reasoning-efficient Swift model comparison

Public primary-source research found UkisAI Swift 1.5 and a compatible AutoRound
INT4 Kaggle mirror (`phuongncn/arc3-qwen38-swift-w4a16-autoround`). The author
reports shorter reasoning on other benchmarks, not ARC. Metadata-only queries
verified both version-1 model parts, inventory, quantization settings and matching
FR-Spec tokenizer hash. No tensors were downloaded locally. An automatic review
initially rejected a model-card command as a possible huge download; installed
source inspection proved it only fetches JSON metadata and the retry succeeded.

Prepared and launched `kunalsinghh25/arc-hydra-duck-swift/1`: original agent,
runtime, draft, tools and scheduler; all 25 public games, one pass, two-hour
gameplay after readiness. Independent of rolling-summary and runtime changes.
Live input checks passed for 95 files/82 indexed shards; mounted config SHA
matches inspected upstream. Offline runtime installation started. GPU loading,
inference and performance remain unverified. Summary v1 and CPU repair v4 were
also re-polled RUNNING. 53 local tests pass. See `baselines/swift_15/README.md`.

## 2026-10-26 IST: both GPU comparisons passed readiness

Swift public readiness passed, configured deadline 25 October 20:32:58 UTC;
summary passed shortly afterwards, deadline 20:34:08 UTC. Both retain the full
7,200-second post-readiness gameplay budget. Structured readiness snapshots
record these settings and distinguish health from substantive model gameplay.
No final score, verified summary execution or hidden-score improvement yet.
The CPU build remains separate. No notebook version was restarted or replaced.

Subsequent live snapshots verify substantive model gameplay: Swift two levels,
224 actions and 130,680 tokens; summary variant three levels, 142 actions and
145,223 tokens. These unfinished snapshots are not synchronized and cannot rank
the interventions. Actual summary requests still need verification.

CPU v4 subsequently ended ERROR on missing `nvrtc.h`. The CUDA library filter
was excluding NVRTC along with compiler packages. V5 narrows that exclusion and
adds a cuBLAS/NVRTC/CCCL compile probe before native compilation. Launched only
after authoritative v4 ERROR; Python/Bash syntax checked. GPU versions unchanged.

V5 later passed dependency checking and the cuBLAS/NVRTC/CCCL SM120f compile
probe, clearing the two observed header omissions. Native module completion and
fresh offline reinstall remain unverified. Structured stage evidence is in its
`header-probe.json`; observer 39736 replaced a disconnected observer without
restarting the cloud job. Both GPU comparisons remain running.

Inspected the existing sandbox/perception API before adding tools: connected
components, color/shape/rotation hashes, adjacency and movement are already
available. A duplicate component detector is not justified. Retain failure-trace
analysis as the basis for any additional perception intervention.

Operational follow-up: installed Kaggle CLI source confirmed that five quiet
stream failures end the observer without establishing cloud completion. Added
`scripts/kaggle_watch.py`, a read-only exact-version observer with longer retry
tolerance and an authoritative status read when it exits. Syntax and help
checks passed. CPU v5 was re-polled RUNNING and observer session 17923 attached;
`watcher.log` is now preferred. Both GPU versions and the CPU cloud job remain
unchanged. No performance improvement or final build result is claimed.

## 2026-10-26: completed comparisons and best-version official submission

Both GPU experiments COMPLETE, all 25 games with verified model gameplay.
Rolling summaries: mean 37.0547, 89 levels, six full wins, 3,545,214 accounted
tokens. Swift: mean 11.3230, 50 levels, zero wins, 4,593,943 accounted tokens;
its last half hour added no completed level. Original baseline remains the
highest measured public mean at 43.7621, 102 levels and five wins. Keep original;
neither variant demonstrated a better public score in this single-pass comparison.
Summary execution and detailed failure mechanisms still need trace inspection.

CPU v5 ERROR: headers passed and native objects compiled, but final linking
could not find `-lcudart`. No successful runtime bundle or GPU result exists.
Next repair should add the unversioned runtime-library alias and an actual host
link probe. Preserve the terminal log; do not rerun the same defective build.

User explicitly requested upload of the current best and result checking.
Official allowance showed one entry remaining. Verified all three local source
hashes against the original version-2 upload and its COMPLETE status. Submitted
`kunalsinghh25/arc-hydra-duck-m2-baseline/2`: accepted as **57657435**, zero entries
remaining today. Initial official check: PENDING, empty scores, no error, at
12:23:53 IST. Public 43.76 is not the official competition score. Goal >71.48
remains active. Selection record: `reports/kaggle/best-candidate-submission.json`.


26 October continuation: official submission 57657435 remains PENDING at 18:47 IST, with no score/error. CPU repair v5 confirmed ERROR at final native link (-lcudart). Uploaded CPU-only repair v6 with CUDA runtime development alias and an early host-link probe; local Python/Bash checks and two runtime-overlay tests passed. Cloud build and offline installation remain unverified. Exact-source hashes: reports/kaggle/pennyroyal-v3-repair-v6/upload.json. Observer session 70362 follows that exact version. No second competition entry or GPU run was launched.


26 October 23:37 IST: official entry 57657435 COMPLETE, public score 24.87, no error; improves best scored result from 0.02 but remains below 71.48. CPU runtime repair v6 COMPLETE, including host link, all native objects, accepted kernel checks, fresh offline reinstall and imports. Bundle manifest: 36 files, 1,978,944,573 bytes. Prepared and uploaded separate GPU runtime preflight v1 using the exact completed CPU notebook output, hash pinned; no local bundle transfer or altered wheel filenames. Twelve packaging/runtime tests passed. Original model/agent/memory settings retained. Five public games, 900 seconds after readiness; GPU inference remains unverified. Numeric quota read: 70,361.28 free GPU seconds remaining, paid scaling disabled. Observer 35416 follows exact GPU version 1.


26 October 23:50 IST: both exact GPU runtime-preflight/1 and verification/1 jobs officially RUNNING. Existing runtime observer returned without events while cloud status remained RUNNING; no restart. Launched separate quality experiment with only ARC3_STEP_VERIFICATION_HINT=1, original model/runtime/memory/tools/scheduling and matched all-25-game two-hour public budget. Motivated by SK48 mechanics reconstruction, not by assuming action-free thinking is waste. Thirteen packaging tests passed; source/diagnostic hashes retained. Actual prompt activation and final gameplay results still require verification. Observer 57352 follows verification/1.


27 October 00:04 IST: both exact GPU jobs remain RUNNING. Verification model startup exposed its initial 720-second wait and the separate 3600-second readiness allowance; checkpoint precaching read 62 files / 185.40 GB in 690.91 seconds. Readiness and gameplay remain unverified. Runtime stream still returns server errors. Launched CPU-only offline runtime-input-probe/1 with only completed CPU builder version 6 as input, no model/competition/GPU. It checks the same supported mount paths, exact manifest and every bundle file hash; actual result pending. This independently tests input integration without restarting either GPU run. Source compiled locally; upload hashes and observer 87895 recorded.


27 October 08:18 IST: verification/1 COMPLETE, public mean 46.2321, 102 levels/eight wins; all 25 games verified and FT09 model system prompt contains the guidance (hashed evidence). Exact uploaded source hashes matched, official allowance read one remaining; submitted exact version as 57686595, accepted/PENDING, allowance now zero. Official best scored remains 24.87. CPU input probe COMPLETE, all 36 files/1,978,944,573 bytes hash-verified at the supported mount path. Runtime/1 ERROR: Triton host C compilation failed on missing Python multiarch pyconfig.h through Conda GCC, followed by process-tree kill (not evidence of OOM). Launched repaired runtime/2 with system host C compiler, retained GCC15 C++/CUDA host, and an early real Triton driver-helper probe. Thirteen packaging tests passed; GPU validation pending. Free GPU quota 59,646.734 seconds, paid scaling disabled. Observer 97875 follows exact runtime/2.


27 October research reset: official verification entry 57686595 completed at 0.00, metadata has no error description; cause remains unverified, original 24.87 is best scored. Runtime/2 ERROR after its Triton host probe passed: FlashInfer XQA JIT cannot link -lcuda. No further runtime repair launched. User requested deep internet/paper/model research. Completed reports/research/2026-10-27/strategy.md (3,168 words, 27 primary URLs including 13 papers), source/evidence register, and fresh official constraints/quota snapshot. Recommendation: competition lifecycle parity, optional mechanically checked world-model/goal layer on frozen original stack, controlled full comparisons, then one model pilot. No GPU jobs, submissions or model weights downloaded during this research pass. Goal >71.48 remains active and unachieved.


27 October verified-planner implementation: built hydra/verified_planning.py and exact-source installer. One exploratory action per tool call; planned batches replay current-level evidence and check predictions action by action. Unknown, truncated, contradicted or constant abstractions cannot certify plans. Mechanical events are propagated separately from model stdout and persisted. Added shared readiness, global finalization reserve and lifecycle counters. 84 local tests passed including real sandbox-protocol execution and prompt consistency. CPU probe v1 caught missing patch EOF newline; fixed and regression-tested. CPU v2 passed seven mechanical cases; final CPU v3 also passed prompt contract and seven integration cases on the exact Kaggle source bundle. Candidate library/installer hashes matched. Uploaded private GPU preflight kunalsinghh25/arc-hydra-verified-planner/1: existing five public diagnostic games, 900 seconds after readiness, competition-style minimal diagnostics, explicit benchmark output. Original model/runtime retained. Observer 79691 follows exact GPU version. No official submission made; score benefit and >71.48 goal remain unverified.


27 October 21:16 IST: verified-planner/1 COMPLETE; all five games played, public mean 15.9206, 10 levels/zero wins, 343,178 accounted tokens. Actual events: 29 passing abstract-state replays, 158 planned actions, three prospective mismatch stops. No full-grid check claimed. Old five-game control timer began roughly 8.5 minutes before model readiness; historical 11.40 versus 15.92 cannot establish quality improvement. Launched fresh exact-source baseline/3 and frozen verified-planner/2 on all 25 games, one pass/7,200 seconds after readiness, both with full public diagnostics and original model/runtime. Observers 64036/24665. Pre-launch free GPU quota 57,133.787 seconds, paid scaling disabled. No official entry or model-weight training. Goal above 71.48 remains unverified.
