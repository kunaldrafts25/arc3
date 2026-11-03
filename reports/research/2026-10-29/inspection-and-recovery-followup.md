# Follow-up: precise observation access, flexible reasoning and official comparison

## Decision

Keep the earlier flexible agent as the primary control. Test an optional exact
inspection interface separately from study memory and recovery advisories.
The inspection branch addresses a reproduced coordinate-parser error in our own
trace, while retaining the model's freedom to use qualitative representations.
No new model weights are required. No improvement is established before actual
gameplay and official evaluation.

## Primary-source updates

[VISTA](https://arxiv.org/html/2610.02200v1), especially sections 3, 4.3 and A.4:
retrievable observations and exact inspection are useful mechanisms to test.
The paper reports public-set 100 with a proprietary backend and 66.93 with
GLM-5.3 Flash 320B. Neither result reproduces our offline Qwen setup. Its
inspection ablations motivate a controlled interface experiment, not a promised
score. Our existing host already supplies lossless historical frames; another
archive would duplicate that capability. A nominal four-bit 320B model needs
about 160 GB for weights alone, so a GPU-resident swap is not a straightforward
fit for the current 96 GB GPU. Offloading would need separate validation.

[NVIDIA AVO](https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/):
the authors describe supervision for stalled trajectories and persistent memory,
reporting 100 on the 25 public environments using Claude Opus 5 and text grids.
They explicitly caution that comparison with VISTA is not a controlled ablation.
This supports investigating trajectory-level recovery, but does not isolate
memory, establish private-game performance or supply a drop-in offline model.
Our lightweight advisory is not an implementation or reproduction of AVO.

[Human think-aloud study](https://arxiv.org/html/2610.34523v1), especially sections
4.2–4.4: the descriptive analysis distinguishes belief errors, planning failures
and execution errors. Humans frequently use qualitative explanations and also
explore without a fully specified hypothesis. These findings caution against
requiring a complete simulator or quantified causal account before every action.
The supplied public-game trajectories are not unseen validation data. We have
not downloaded the dataset, trained on it, or injected its game solutions.

Review scope: relevant HTML methods/results sections and the NVIDIA technical
article, not an exhaustive audit of the repositories or independent replication.
The top competitor's undisclosed method remains unknown.

## Concrete implementation

`hydra/grid_inspection.py` exposes three bounded observation-only functions:

- `read_cells` returns exact letter-coded pixels at explicit raw row/column
  positions, rejecting negative and out-of-range coordinates.
- `read_region` returns a sampled region with explicit raw coordinate axes.
  Sampling does not certify a logical tile size, origin or object identity.
- `row_runs` returns same-color segments with absolute start columns and
  exclusive stop columns. This removes the need to rewrite elementary endpoint
  arithmetic whenever the model wants run lengths.

Default selection follows the refreshed current observation. Historical step
lookup uses supplied history, rejects unavailable or ambiguous steps, and cannot
cross game contexts. Calls do not advance the game. Usage telemetry records
actual calls independently of model-authored assertions, with explicit overflow
counts after the per-call event bound. Outputs stay bounded.

This is deliberately a separate flexible-agent branch: no added study-memory or
recovery protocol, no scheduler/runtime/model changes. Tools remain optional.
They cannot resolve goals or physics by themselves, and additional tool choices
or prompt text can hurt performance. Those costs require measured gameplay.

## Validation and evaluation

124 local tests passed before adding the submission waiter. New tests include
exhaustive binary row reconstruction through length eight, coordinate/crop
invariants, history refresh, invalid indices and a real composed child-RPC test.
Kaggle CPU gate `kunalsinghh25/arc-hydra-inspection-cpu-probe/1` completed with
seven inspection cases, eight original mechanical cases and 16 prompt
combinations, including actual host event persistence and game isolation.
This establishes interface behavior, not language-model problem solving.

The packaged full-budget inspection candidate has not been launched. The
previous flexible agent is already available as completed exact version
`kunalsinghh25/arc-hydra-ultimate-candidate/3`: 48.2861 on its two-hour public
development run. Its official path automatically uses the full competition
runtime with startup and a 600-second finalization reserve included.

A one-attempt submission waiter is armed for that exact completed version.
It checks authoritative allowance, source hashes and terminal status; it stops
if credentials change or another entry appears. Mutation intent is persisted
before the API call, and ambiguous outcomes are never retried automatically.
The waiter does not start another public GPU notebook. Acceptance and official
score must still be observed; the current best remains submission 57726784,
28.45. Eight separate waiter tests cover allowance, version choice, ambiguity,
journal failures, source validation and competing submissions.
