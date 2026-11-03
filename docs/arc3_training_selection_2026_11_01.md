# ARC3 training decision, 1 November 2026

## Superseding outcome, 22:25 UTC: reject the trained27B candidate

The paired real-game screen completed: untrained base15.7143/12levels versus
trained adapter5.3301/7levels; all five adapted game scores regressed, both0wins.
Both arms ran substantive games and the saved adapter changed serving outputs.
The observer's routing JSON was corrupted by a concurrent writer, reconciled
from all ten actual transcripts without rerunning the GPU. See
reports/arc3/qwen27-lora-gameplay/completed-reconciliation.json. The writer is
fixed for future runs; preserve the original evidence. Reject this adapter and
do not expand this SFT merely because its held-out token loss improved.

The8-slot/FCFS27B capacity experiment also completed at8.3627, below9.5417 for
the4-slot baseline. Lower queue tails and greater token throughput did not
establish better gameplay. FlashNext remains the strongest verified system.

A new CPU-only native FlashNext/GGUF training feasibility probe/1 is accepted.
The reviewed40GiB training recipe is AMD-specific, but its pinned Transformers
fork exposes a generic Torch quantized-activation-gradient path. An existing
Kaggle IQ3_S mirror avoids a large local download. The probe checks architecture,
tiny CPU math and native multimodal data; CUDA, split-file/vision integration,
learning objective and serving remain open. This is research toward training
our stronger base, not proof that the rejected data/objective will work there.
See the top handoff for exact sources, job identity, hashes and resource floors.

## Actual training result and gameplay test, 17:13 UTC

Status17:17UTC: the paired saved-adapter gameplay/1 is now RUNNING. Its API
still exposes no live output/log files; model readiness and substantive games
are not yet verified. The exact observer remains live; no duplicate launch.

The BF16-LoRA pilot/1 is COMPLETE:40optimizer updates,158examples/oneepoch,
108,789,760trainable parameters. Fixed validation-token loss0.766336→0.723652;
saved native adapter reload error0.0. Actual CUDA peak allocated70.26GiB;
trained16:30–16:54UTC and finalized16:55:43, well within the total7200-second
cap. Full native and serving adapters are downloaded and hash-checked. This
is actual training evidence, not actual-game improvement.

The exact saved-output CPU mount/header check also completed (992FP32tensors,
48GDN groups, all file/report hashes). A two-hour paired real-game screen/1
is now accepted/QUEUED: untrained base and trained adapter each play the same
five frozen whole-game gradient holdouts simultaneously on one8-slot FCFS
server with LoRA enabled. Correct adapter routing and output probability changes
are checked before games. Same-runtime contention and one draw limit conclusions.
No official submission or model promotion. Full identities/hashes in the handoff.

### Additional primary-source check during evaluation

[Agnes3.0Qwen's card](https://huggingface.co/Agnes-AI/Agnes-3.0-Qwen) describes
a Flash-Next derivative with self-reported general coding/tool benchmarks,
not ARC3 results. Its documented BF16 checkpoint is about360GB with an8GPU
example. That does not prove quantized single-GPU use impossible; no compatible
AutoRound/Kaggle deployment was established here. Do not expand GPU jobs on the
strength of those benchmarks while our actual saved-adapter test is running.

[StateSet's own verification section](https://github.com/stateset/stateset-agents)
explicitly distinguishes Flash-Next integration/smoke tests from retained live
training/serving certification. Its named-model support is not a verified
single96GB training path for our AutoRound checkpoint. No paid providers or
additional accounts were used. Existing native27B training now has actual CUDA
evidence; Flash-Next training remains an implementation/reproduction problem.

## Execution update, 16:17 UTC

Native CPU data gate passed231/231 actual examples with no errors and FLA
import. The bounded actual BF16-LoRA pilot/1 is now RUNNING; native GPU optimizer
progress is not yet verified. The finalized package includes a checked GDN
adapter-format export plus the exact deployed normalizer preflight. Full
7200-second cap and fresh shared-resource checks passed; ARC2 reserve preserved.
See the latest handoff for immutable package hashes and exact accepted job.

## Superseding evidence, 16:06 UTC

The untrained27B completed at9.5417 public,36levels and0wins, versus31.5813
for our inspection control. At equal4,819seconds it scores5.8819. It is a
trainable experimental student, not our best model. A capped8request/FCFS
serving counterfactual is running; do not assume training repairs runtime stalls.

Swift was already evaluated at11.3230/50levels/0wins; earlier notes treating it
as untested were incorrect. ThinkingCap also regressed. Keep Flash-Next as
the incumbent. Our official28.45 remains far below the freshly verified75.56.

The selected pilot implementation now uses frozen native BF16 rather than
QLoRA, avoiding an additional unverified training quantization stack on96GB.
Rank16 adapts400 language projections supported by the actual serving runtime,
108,789,760parameters, with conservative LR1e-5 and one epoch maximum of158
real16K examples. This offers recurrent/MLP as well as full-attention adaptation;
it does not establish enough data or capacity to overcome the measured deficit.
Base/vision remain frozen. CPU inventory is actual; full400-module placement,
CUDA memory/backward throughput, serialization and serving remain GPU gates.
CPU data probe/2 is running. No trained weights exist yet. See the latest
handoff for exact journals, immutable assets and7200-second total caps.

## Execution update, 13:35 UTC / 19:05 IST

The CPU-gated untrained27B baseline is now running as
`kunalsinghh25/arc-hydra-qwen27-matched-baseline/1`, with a persistent observer
and external/internal7200-second total caps. See the superseding top of
`docs/arc3_new_chat_handoff.md` for exact state, process and artifact locations.
Model readiness and gameplay remain unconfirmed. One separate CPU-only training
dependency/meta-model check is running; no additional GPU run or training was
launched. The older proposal/status statements below describe the research pass.

The data proposal was revised from synthetic-only training to an explicit pilot
using our own actual completed agent traces. This avoids teaching unavailable
synthetic tools and permits a real training feasibility test now. A whole-game
hash split was fixed before the27B evaluation result:16train,4validation,5test.
All public games were previously studied; the test games are held out from
gradients, not a claim of blindness or hidden-game generalization.

Outcome/efficiency/causal/context filters produced255train/69validation examples
at32K and158train/57validation at16K, covering every allocated training and
validation game. We retained useful inspection replies as well as real actions.
All inputs are the recorded preceding request; later tool results and eventual
completion are used for selection only. Generator parameters and future outcome
metadata stay outside model input. A real completion-boundary indexing defect
was caught and corrected before training; all selected levels now match the
last recorded user observation. Four alignment tests pass.

The deployed27B tokenizer differs from Flash-Next. We pinned files matching the
actual mounted hashes and inspected the exact Transformers5.12.1 template JSON
filter rather than approximating it with Jinja defaults. Native multimodal
tensor masks still require actual-processor verification. The staged collator
refuses different rendering or image-expanded input prefixes.

Data/report: `reports/arc3/qwen27-training-pilot/`, `context-32768/`.
Scripts: `fetch_arc3_teacher_prefixes.py`, `prepare_arc3_teacher_pilot.py`;
collator: `hydra/arc3_training_collator.py`. Data is not yet cleared for training.
Before choosing QLoRA versus BF16-LoRA on96GB, measure real activation memory,
backward speed and adapter export/serving; the dependency check itself does not
establish these. The incumbent still must be beaten in deployed actual gameplay.

User direction: research the strongest practical model, then train a contender;
potential model release comes later. No paid resources or account bypass. Keep
every development session at a hard 7,200 seconds including setup and saving.

## Decision

**Qwen3.8-27B is the provisional first training candidate, using QLoRA.**
This selects a practical training experiment, not a proven best ARC3 model.
Keep the existing Intel Flash-Next agent and its best official result as the
incumbent. A new checkpoint must beat that system in actual gameplay with the
deployment runtime, not merely reduce training loss.

The choice is based on a documented single-GPU training path, native vision,
Apache-2.0 release and straightforward adapter export. Unsloth documents 24-GB
QLoRA support; that is not a measurement of our image/context/batch workload.
See the [primary training guide](https://unsloth.ai/docs/models/qwen3.8/train)
and [official model card](https://huggingface.co/Qwen/Qwen3.8-27B).

Other choices considered:

| Candidate | Evidence | Decision |
| --- | --- | --- |
| Current Qwen3.8-Flash-Next W4A16 | Proven in our serving stack; best completed official 28.45. A public author trained frozen-int4/BF16-linear LoRA on one 96-GB RTX, but their model regressed. | Retain incumbent. Prefer it for final training if an executable, auditable small-adapter trainer is established quickly. Do not treat inference fit as backward-pass support. |
| Qwen3.8-27B | Completed public9.5417,36levels,0wins; severe regression. Native BF16 training dependencies pass CPU checks. | Experimental student only; serving counterfactual and actual saved-adapter gameplay must justify further use. |
| Qwen3.6-35B-A3B | Official 35B/3B-active vision MoE, Apache-2.0. Older model with a different training/serving tradeoff. | Backup, not an extra immediate GPU experiment. Its lower active parameter count does not prove better ARC3 performance. |
| ThinkingCap Flash-Next | Our completed actual comparison regresses strongly. | Reject as replacement. |
| Ravi ARC3 LoRA | Author reports held-out loss improving but actual interactive score declining, with inefficient training episodes a suspected cause. | Learn from the failure; do not adopt its weights or copy its unfiltered recipe. |
| Swift | Existing completed deployment11.3230,50levels,0wins; primary licenses retained. | Reject as replacement. Do not duplicate the completed comparison. |
| Large models requiring remote APIs or multiple accelerators | Cannot use remote inference in the required offline competition run; training/deployment not established within our resources. | Outside this pilot. |

References: [Qwen3.6 card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B),
[Ravi's primary release](https://www.kaggle.com/models/ravinderonkaggle/flashnext-arc3-recipe-v3),
[NVIDIA's Flash-Next training coverage](https://docs.nvidia.com/nemo/automodel/latest/model-coverage/large-language-models/qwen/Qwen3.8-Flash-Next).
NVIDIA's multi-node full-training validation is not evidence that a small frozen
adapter requires those resources, nor that a single-GPU adapter is ready here.

## Fresh evidence, 12:35 UTC / 18:05 IST

Official leader: Yi-Chia Chen @ Fields Model **75.56**; Tufa **70.24**.
Own best: **57726784 COMPLETE 28.45**; **57751759 COMPLETE 25.96**.
One submission currently available. Deadline remains **2 November 23:59 UTC /
3 November 05:29 IST**. See `reports/arc3/current-state/state.json`.

Free GPU time: **87,869.277 seconds**, reserved zero, paid scaling disabled.
Fresh shared-job scan found no active recent notebooks, including ARC2.
Preserving the existing 10,800-second ARC2 floor leaves **77,069.277 seconds /
21.41 hours** available to ARC3 at that check. These figures expire when other
work uses the account; refresh immediately before every launch.

Both previously launched development versions have finished. Prediction's local
observer stopped at its observation deadline while the exact remote version was
still running. We reconciled that SAME version and downloaded its completed
artifacts; no rerun or new GPU launch occurred.

| Actual run | Final public score | Levels / full wins | Gameplay seconds | Score at common 4,819.35 seconds |
| --- | --- | --- | --- | --- |
| Inspection control/1 | 31.5813 | 81 / 4 | 4,819.35 | 31.5813 |
| Prediction candidate/1 | 45.1843 | 99 / 8 | 6,069.52 | 34.7601 |
| ThinkingCap candidate/1 | 22.3583 | 70 / 1 | 6,057.05 | 19.2567 |

These are single stochastic public runs, with different startup duration and
scheduling. Prediction's audit contains zero store/event files: no adoption is
established. Do not attribute its score gain to counterexample learning.
ThinkingCap took 7,014 actions versus the control's 3,606; the prediction run took
4,711. These results do not estimate hidden performance or replace the stronger
historical memory candidate. Comparison JSONs are in the respective ARC3 report
directories. ThinkingCap's observed regression warrants rejecting it, without
claiming a statistically measured population effect.

## Training data: inspected, not accepted blindly

The public [full transformation curriculum](https://huggingface.co/datasets/ritwika96/arc-agi-3-full-curriculum)
has an Apache-2.0 card advertising 444,000 episodes. We pinned revision
`cfae5144a91072b05039a3d6c32bea17aa8404fb`, downloaded three small shards, and
executed `scripts.audit_arc3_training_curriculum` on **15,000 records**.

Observed: 40 visual skins per structural identity. In the sampled stateful
train/validation shards, identity and exact visible-prompt overlaps are zero.
All sampled images decode at 256x256; checked click coordinates are valid.
No sampled identical visible prompt has conflicting exact targets. These are
limited sample checks, not a full split or label-correctness audit.

Important limitations: outputs call a synthetic transition library absent from
our deployed agent; the public repository file listing contains no Python
registry/verifier. We have not re-executed its labels. The first stateful train
shard contains only lattice permutations, and the ambiguity shard only palette
ordering. Taking the first N rows would create a narrow curriculum. Selecting
between supplied candidate rules is easier than discovering those rules unaided.
The card omits an additional deep-composition directory visible in the current
file listing: use pinned files and schemas, not headline counts alone.

**Do not directly train on raw rows.** Exclude family, hidden parameters, seeds,
identities and targets from model inputs. Split and sample by structural identity
and mechanic composition. Translate labels into operations that actually exist
in the deployed agent, or implement and verify the shared library first. Keep
all 25 real games out of this initial synthetic training set.

The new [human think-aloud corpus](https://huggingface.co/datasets/hellohawaii/ARC3-human-think-aloud)
is CC BY 4.0 and explicitly covers the same 25 public games. It can inform error
taxonomy and hypothesis-revision examples, but is not an independent unseen-game
test. AI-assisted retrospective annotations and future observations must not be
inserted into earlier model inputs. Third-party agent material has its own
licenses. We fetched the card/metadata, not the complete trajectory corpus.

## Pilot that would justify training

1. Freeze a deployable 27B baseline, exact chat/vision/tool protocol and runtime.
   Prove offline availability, CUDA support, real gameplay and saved-adapter
   reload. Use the actual intended precision and context length. Bound startup
   and finalization inside the two-hour session.
2. Build a small, family-balanced, executable curriculum for observing changes,
   discriminating hypotheses, discovering goals and repairing contradicted
   beliefs. Use the same action and Python-tool interface as evaluation. Prefer
   independently verified efficient trajectories; do not imitate an entire
   failed search simply because its final step succeeds. Count useful
   information-gathering actions, not only direct goal progress.
3. First adapter: rank 16, frozen base/vision backbone, conservative learning
   rate selected after loss/gradient inspection, assistant-only loss, bounded
   context and gradient checkpointing. Exact settings must be frozen after the
   measured memory/throughput preflight; documentation examples are not our
   validated hyperparameters. Save resumable checkpoints before wall timeout.
4. Compare untrained versus adapted 27B with identical runtime, game set,
   wall-time, scheduler and sampling policy, then compare the winner against
   the incumbent Flash-Next. Track completions, actions, startup, token costs,
   invalid tools, recovery and revised hypotheses. Public score is a screening
   result; final selection still requires official evaluation.

Initial resource envelope: at most two hours each for compatibility/baseline,
training pilot, and each of two evaluation sessions (eight hours total maximum),
subject to fresh shared usage. This is a proposal, not four armed queue entries.
No GPU launch or official submission was made in this research pass. Package,
data conversion, offline training dependencies and deployment baseline are still
required. A larger RL run on Flash-Next is not justified by the remaining time.

Release later: preserve upstream notices, data provenance, precise base revision,
adapter configuration and evaluation results. Do not publish unsupported claims
about beating the leader. The competition objective is still unmet.

## Reproducible artifacts

Primary metadata, source URLs/hashes, sampled shard manifest and audit:
`reports/research/arc3-training-selection-20261101/`.
Official model revisions inspected: 27B
`1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`; Unsloth BNB
`8aa5f05d26b7205477066e1449e0af13f762a299`.
The public Kaggle listing for Ravi returned no notebooks; no executable trainer
was recovered. No downloaded external code was executed.
