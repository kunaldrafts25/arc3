# ARC-Hydra research and competition strategy

Research date: **27 October 2026**. Objective: an **official competition score above 71.48**. This report records evidence and an implementation plan; it does not claim that the proposed system has achieved that score.

## Decision

Keep the original 24.87-scoring notebook as the reproducible control. Prioritize competition-path reliability and a small, mechanically checked world-model layer using that model and runtime. Test alternative weights as separate experiments. Stop treating runtime upgrades, shorter reasoning, prompt hints, or a single public score as sufficient evidence of progress toward 71.48.

The proposed improvement is substantive: the agent must distinguish observed facts, uncertain mechanics, and uncertain goals; execute its proposed transition models on recorded evidence; and compare predicted outcomes with actual actions. It can explore when it lacks a model. Long planned batches require stronger evidence than a confident explanation.

This recommendation is an engineering inference from the literature and our traces. Its benefit with our local Qwen checkpoint remains untested.

## 1. What our own results establish

| Candidate | Public development mean | Levels / full wins | Official competition result |
|---|---:|---:|---|
| Original attributed Duck/M2 baseline | 43.7621 | 102 / 5 | **24.87**, entry 57657435 |
| Rolling summaries | 37.0547 | 89 / 6 | Not submitted |
| Swift 1.5 target replacement | 11.3230 | 50 / 0 | Not submitted |
| Step-verification prompt guidance | 46.2321 | 102 / 8 | **0.00**, entry 57686595 |
| Pennyroyal v3 runtime | No gameplay established | — | Not submitted; GPU preflights failed |

Sources: the completed runs' `analysis.json`, `hydra_model_summary.json`, hashed upload manifests, and official submission history under `reports/kaggle/`.

The verification option reached the actual model system prompt. Nevertheless, nine public games improved, seven worsened, and nine tied. The official zero has no error description in the available submission metadata. We do **not** have evidence proving whether it arose from startup, gateway interaction, termination, agent behavior, or another condition. It must not be explained away as variance, or blamed on the prompt, without execution evidence.

The baseline SK48 trace repeatedly reconstructs uncertain mechanics and considers a simulator/search before solving a level. That motivates checking hypotheses against transitions. It does not prove that the intervening reasoning was wasted. BP35's summary run retained five summaries and improved locally while the aggregate regressed. These observations argue for precise interventions and measurements.

Runtime v1 failed compiling Triton's host-C helper because Conda GCC could not find Python's multiarch header. V2 passed the early host-extension probe but later failed a FlashInfer XQA JIT link with `cannot find -lcuda`. The completed CPU bundle and independent mount probe validate their respective scopes; they do not validate every GPU JIT path. There is no measured v3 speed benefit to weigh against these integration costs.

## 2. Constraints that determine which research transfers

Fresh official competition pages and quota responses are retained in [constraints.json](constraints.json). Kaggle requires offline notebooks within a nine-hour CPU/GPU runtime and permits publicly accessible external models/data subject to its rules. The final submission deadline is **2 November 2026, 23:59 UTC**, or **3 November, 05:29 IST**. The current hardware pool uses `g4-standard-48`; our observed runs expose approximately 95.6 GiB GPU memory and 176.9 GiB host memory. [Official competition](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview), [rules](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules).

The quota service currently reports **58,754.402 free GPU seconds, approximately 16.32 hours**, with paid scaling disabled. It reports a reset at 31 October 00:00 UTC, or 05:30 IST. Recheck before spending that future allocation.

Three distinctions are essential:

1. Public development games, the public competition leaderboard's hidden games, and the final private score are different evaluations.
2. A frontier API model's public-set success is evidence about a method under that model/budget, not an offline single-GPU reproduction.
3. Publicly downloadable weights and a model-card license label do not by themselves establish competition prize eligibility. Review the actual terms before adopting a new checkpoint.

ARC Prize explicitly labels community results as self-reported public-set results except where otherwise stated. Its community board is useful for locating methods and artifacts, not for treating every score as an independently verified Kaggle result. [Community evaluation policy](https://arcprize.org/leaderboard/community).

## 3. Directly relevant research

The table separates author-reported results from what we can reasonably transfer. Full-text sections were inspected for Kepler, Memento 3 and the component ablation; other entries were checked through their primary abstracts, original repositories or author write-ups. Full-text retrieval of two additional HTML papers stalled, so no claim here depends on unseen sections.

| Work | Evidence and limitation | Transfer to ARC-Hydra |
|---|---|---|
| [ARC-AGI-3 benchmark report](https://arxiv.org/abs/2603.24621) | Interactive inference of rules/goals; evaluation rewards completion and action efficiency. Historical launch-model scores are not today's rankings. | Measure discoveries and real actions, not just output-token speed. |
| [Executable World Models, Rodionov](https://arxiv.org/abs/2605.05138) | Reports 58.12 mean public RHAE and 15 fully solved games with GPT-5.5 high. Uses executable hypotheses, replay checks and planning; private validation untested. | Prototype a compact transition-model interface on our existing local model. |
| [Component ablation, Rodionov](https://arxiv.org/abs/2607.15439) | Model capability/effort often matter more than scaffold changes. Executable-only does not always beat textual reasoning. Complete verification ranks first in the main comparisons but costs more. Strong-model public saturation does not establish held-out generalization. | Compare an enforced checker with a textual control; allow abstention and inexpensive exploration. Do not force every easy action through costly simulator construction. |
| [TWIN](https://arxiv.org/abs/2608.14490) | Authors report 93.3 public score and 179/183 levels using a frontier coding agent. Replay consistency is enforced; goal inference remains a major difficulty. No equivalent single-Kaggle-GPU result is established by that claim. | Validate mechanics and goals separately; return concrete counterexamples when model predictions fail. |
| [Kepler](https://arxiv.org/html/2610.00834v1) | Reports perfect final public replay scores with Claude Opus 5, while explicitly distinguishing replay from first exposure. It reports large token use and audits leakage, tool replacement and observation failures. Conditional prediction failures/zero coverage are logged rather than universally blocking actions. | Use append-only evidence, explicit prediction coverage, tool-integrity checks, and first-attempt reporting. Do not copy its score as a target forecast. |
| [Memento 3](https://arxiv.org/abs/2610.11794) | Maintains a revisable rulebook, compiles it to code and checks recorded transitions. Reports 100 public RHAE with Claude Opus 5 extra-high; a population extension explores multiple hypotheses. This is external-memory adaptation with frozen weights. | Keep rule claims linked to evidence and counterexamples. Start with one model plus a bounded alternative, not a large population of expensive agents. |
| [OPINE-World](https://arxiv.org/abs/2607.01531) | Reports public improvement from 1.5 to 78.40 with Claude Opus 4.8 high. Revises the object/state abstraction as well as mechanics and goals. | A failed prediction may indicate bad object identity or an omitted state variable, not just a wrong movement rule. |
| [NOOA](https://arxiv.org/abs/2607.20709), [original code](https://github.com/NVIDIA-NeMo/labs-OO-Agents) | Typed Python objects unite agent state, callable actions and deterministic methods. ARC Prize lists a separate 85.1 public-demo result. Neither framework packaging nor that result proves an offline Qwen gain. | Prefer a few explicit, testable state/method contracts within our harness. A wholesale framework migration is unnecessary for testing this idea. |

The common useful mechanism is **counterexample-driven learning**. An explanation becomes a testable prediction; an observed contradiction becomes a small repair task. This is stronger than asking the model to be careful. However, the ablation evidence prevents concluding that more scaffolding always improves a weaker local model.

## 4. What open competition write-ups add

[Daniel Franzen's original M2 write-up](https://github.com/da-fr/arc-agi-3-solution/blob/main/WRITEUP.md) reports 27.89 on the competition leaderboard. It combines a capable Qwen model, animation access, undo, persistent helpers, larger context, prefix caching and compute scheduling. Much of this is already present in our attributed baseline. Reimplementing segmentation, animation access or generic persistent functions would duplicate existing capabilities.

[Lohit Siriki's M2 write-up](https://github.com/LohitSiriki/arc-agi-3-milestone2-solution/blob/main/WRITEUP.md) reports 22.53 and documents public-practice/leaderboard inversions and repeated-run variability. It recommends reading trajectories and comparing token budgets as well as wall time. This independently supports treating our single public improvement cautiously; it does not explain our official zero.

The original [RPS repository](https://github.com/iamjasonfeng/rps-arc-agi-3) says the author removed the report after discovering a serious flaw in one solution. Search engines still surface the older abstract. **Exclude it as positive evidence for a training recipe.**

Searches for the leading Fields Model entry did not establish a public recipe or downloadable competition-winning checkpoint. A team name or leaderboard score is not evidence of a particular architecture. No recommendation here depends on access to undisclosed competitor methods.

## 5. Foundations worth adapting, and methods to defer

| Research | Useful principle | Scope limit for this competition |
|---|---|---|
| [BAMCP](https://arxiv.org/abs/1205.3109) | Plan while accounting for uncertainty about dynamics. | Use disagreement among a small number of consistent hypotheses as an exploration proxy. Do not claim calibrated Bayesian probabilities from LLM confidence. |
| [DreamCoder](https://arxiv.org/abs/2006.08381) | Reusable symbolic abstractions make later synthesis easier. | Build a small library of tested, general transition/search primitives; importing its entire learning system is a separate research project. |
| [Voyager](https://arxiv.org/abs/2305.16291) | Store executable skills and improve them using execution feedback. | Minecraft/API results do not predict ARC-AGI-3 scores. Keep helper code only with preconditions and tests. |
| [DreamerV3](https://www.nature.com/articles/s41586-025-08744-2) | Learn dynamics and improve decisions through imagined trajectories. | Its trained control results do not establish efficient first-contact learning of unfamiliar ARC games. A fresh pixel-world-model/RL training project is a poor deadline choice here. |
| [Tiny recursive model adaptation](https://arxiv.org/abs/2511.02886) | Small specialized models can benefit from task-time learning. | The cited work concerns static ARC-AGI-II. It is not a demonstrated replacement for an interactive ARC-AGI-3 agent. |

## 6. Model shortlist

These are candidates to evaluate, not claims of superior ARC performance. Weight-memory arithmetic excludes KV cache, activations, vision components and runtime overhead.

| Candidate | Why consider it | Feasibility and decision |
|---|---|---|
| Current Intel AutoRound Qwen3.8-Flash-Next | Only our original stack has a verified useful official score. | **Control and first implementation target.** Preserve exact weights, template, tokenizer and runtime. |
| [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | Official dense vision-language model; Apache-2.0 card. Smaller operational footprint makes it a useful reliability/cost comparator. | Estimated raw BF16 parameter storage: 27B × 2 bytes ≈54 GB. Actual fit/context must be tested. It needs its own template/config; Flash-Next's draft/token map must not be reused blindly. The original author found Flash-Next stronger, so this is a comparator, not an assumed quality upgrade. |
| [ThinkingCap Flash-Next](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-Flash-Next), [NVFP4 release](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-Flash-Next-NVFP4) | Author reports 38.5% average reasoning-token reduction across other benchmarks, with aggregate accuracy 88.8 versus base 89.8. Quantized weights exist. | **Conditional model pilot.** No ARC score is established. NVFP4 requires a working compatible engine and offload; offline mirror, tokenizer/draft alignment and license terms need checking. Our Swift regression makes efficiency-only claims insufficient. |
| [NVIDIA Flash-Next NVFP4](https://huggingface.co/nvidia/Qwen3.8-Flash-Next-NVFP4) | Public quantization of the same model family, with a documented model card and evaluation. | Treat as a precision/runtime experiment. GPU-resident and host-offloaded portions, temporary buffers and actual startup matter more than total download size. No proven advantage over our INT4 checkpoint. |
| [Swift 1.5 AutoRound](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound) | Public efficient-thinking alternative already integrated in our tests. | **Deprioritize:** our matched public run scored 11.32. Retest only after identifying a concrete compatibility or evaluation issue that changes that evidence. |
| A targeted 27B adapter or small rule/proposal model | Could train transition prediction, valid tool use and counterexample repair directly. | Research branch after the verifier exists. No measured gain or training-memory fit is established. |

The [official Flash-Next card](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) describes a sparse architecture with large n-gram tables; nominal active parameter count is not the memory footprint. The [official serving recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next) is useful compatibility evidence, but a multi-GPU throughput recipe is not a single-RTX performance measurement.

Closed frontier-model results guide architecture research. Our final agent must operate without internet and use eligible artifacts; it cannot depend on those API calls at submission time.

## 7. Proposed implementation

This section is our proposed design, not an implemented or evaluated paper reproduction.

### Evidence and state

Retain an immutable per-game record of observation, legal action, next observation, actual status, animation information and action-budget change. Keep hypotheses and verified facts in separate fields. Each rule records supporting and contradicting transition IDs, scope, model version and unresolved conditions. Existing frame-diff and connected-component APIs remain available.

Object identity is provisional. Touching same-color components can merge; animation frames can expose events absent from the settled board. HUD masking may help novelty search, but must not silently remove energy, phase or task-relevant state from prediction evaluation. Record explicit coverage when a model predicts only part of an observation.

### Small executable hypotheses

Start with one proposed transition model and an optional alternative for an unresolved interaction. A minimal interface is `encode(observation, history)`, `predict(state, action)`, `render(state)` and `goal_candidates(state)`. Predictions can explicitly abstain. A model's supported domain and goal assumptions are part of its interface.

After a revision, replay the relevant recorded history in a separate runner. Return the first counterexample and a concise mismatch description. Cache successful checks by model version and history-prefix hash, not by a free-text assurance. Passing recorded examples establishes consistency on that evidence, not correctness on unobserved states.

The evaluation target must remain outside the predictor call. A model that memorizes history or returns no predictions must not receive a perfect generalization score. Use prospective checks and reserved synthetic transitions to detect those shortcuts.

### Planning and exploration

Use bounded BFS/A* or another appropriate search when a consistent model and plausible goal exist. Initially cap search by both elapsed CPU time and expanded states; log actual cost. Prefer a short executable prefix over a long unverified action batch. Compare predicted and observed effects after each real step and stop the batch on contradiction.

When no model or credible goal exists, allow a low-cost exploratory action. Universal blocking would deadlock the agent at first contact. Require stronger consistency for **claimed model-based plans**, not for all exploration. If two plausible models disagree, choose a safe action that distinguishes them when possible. This is an information-gathering heuristic, not a claim of exact Bayesian optimality.

Track goal uncertainty separately from transition uncertainty. Correct mechanics plus the wrong win condition still loses. A failed search can indicate a wrong goal, omitted state, insufficient search budget or an incorrect rule; it should not automatically trigger more actions under the same explanation.

### Memory and compute allocation

Store concise rule changes and tested helper functions rather than repeatedly summarizing the entire conversation. Keep counterexamples after compression. Reuse helpers only when their preconditions match the new level. Existing scheduling already redistributes work; change it only after measuring whether the new verification costs stall other games.

Measure action efficiency, completion, elapsed time, emitted tokens, prediction coverage/accuracy, model-repair count, invalid tools and recovery after a contradiction. Tokens per second is a supporting metric, not the competition objective.

## 8. What a custom trained model should learn

Start with external-memory and executable-model learning while keeping LM weights frozen. This directly tests the architectural hypothesis without a new quantization/training variable.

If that works, construct a dataset from permitted public interactions and synthetic mechanics: state abstraction; competing rule hypotheses; predicted outcomes; a counterexample; a corrected rule; a valid short tool call. Train for verified next-state accuracy and repair, not just imitation of long successful-looking reasoning. Include negative examples of plausible but contradicted models and invalid tool formats.

A small adapter on a 27B model, or a smaller proposal/ranking network, is a bounded experiment. Its memory use, training time and quantized deployment need separate tests. Training a new foundation model is outside the available budget.

Split synthetic mechanics families before generating training examples. Use game-level separation for public diagnostic comparisons, while acknowledging that we have already inspected the public set: it is not a clean unseen holdout. Validate first-contact behavior on newly generated mechanics families, then the official evaluation. Do not train or dispatch on hidden game identities, and do not use hidden implementation access.

## 9. Ranked experiments and stopping rules

GPU allocations are initial caps, not promises. CPU-only unit tests, trace analysis and synthetic replay checks should precede GPU runs. Total below leaves approximately 5.8 GPU hours of contingency from the current balance.

| Order | Experiment | Initial GPU cap | Evidence required to continue |
|---|---|---:|---|
| 1 | Reproduce competition lifecycle using public environments and a local/mock gateway, including startup, high concurrency, cancellation and output finalization | 1.5 h | Readiness, actual model calls/actions, valid generated output and a global deadline covering startup. Zero-score cause remains unknown until evidence distinguishes failure classes. |
| 2 | Counterexample/replay layer on frozen original stack; compare textual guidance with mechanically checked plans on a predetermined small diagnostic set | 2 h | Prospective predictions, counterexample-driven repairs, no deadlocks and no hidden game logic. Useful action/level gains must exceed verification overhead. |
| 3 | Matched full 25-game comparison: control and strongest architectural candidate, same budget and recorded sampling settings | 5.5 h | Full gameplay for every game; report per-game gains/losses and variability. A higher single mean is a screening signal, not proof. |
| 4 | One alternative model pilot after CPU metadata/template checks | 1.5 h | Fits, parses tools, sees frames correctly, and improves useful progress per time. Stop on quality regression. |
| 5 | Reserve remaining compute for a targeted replication or full pre-submission validation | ≈5.8 h | Spend according to the strongest remaining uncertainty, not to keep every branch alive. |

Treat runtime v3 as a separate, time-boxed branch. The next concrete linker repair would need compile-time access to the CUDA driver library and a GPU-side JIT/warmup test. Successful CPU builds or a fixed host-C probe are insufficient. Stop this branch if it does not improve measured useful throughput under our actual INT4 workload.

For every submitted candidate, retain exact source hashes, model and data revisions, licenses, readiness evidence, action traces, finalization evidence and the official reference. Never promote solely on a dummy public submission file or a completed notebook status.

A reasonable calendar is: establish parity and the first verifier pilot on 27–28 October; compare complete runs and use official slots only for candidates that pass those gates on 28–30 October; recheck the scheduled quota reset on 31 October; reserve the final days for a frozen candidate's full-duration validation and submission before the UTC deadline. This calendar is conditional on results, not a guarantee of 71.48.

## 10. Research limitations and conclusion

This was a targeted primary-source search across ARC Prize documentation, arXiv, original repositories, author write-ups and model cards, with citation following into related methods. It is not a claim to have exhaustively read the internet or every paper. Third-party summaries were used to discover sources, not to establish technical recommendations. The unpublished leading team's method remains unknown; its score is not reverse-engineerable from a team name.

The evidence supports investing in **reliable evaluation plus falsifiable online learning and planning**, with a small, controlled model comparison. It does not support a claim that another engine version, another efficient-thinking checkpoint, or training a model from scratch will take this submission from 24.87 to above 71.48. That objective remains open and must be demonstrated by an official result.
