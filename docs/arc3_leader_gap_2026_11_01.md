# Investigating the leader gap, 1 November 2026

The authenticated refresh at 07:52 UTC confirms Yi-Chia Chen @ Fields Model at
75.56, our best completed official result at 28.45, submission 57751759 COMPLETE
at 25.96, one submission available, and the deadline 2 November 23:59 UTC. The
official gap is 47.11 points. Our optional-tool experiments do not yet establish
a capability change large enough to close it.

## What the leader actually disclosed

[Chen's ARC3 milestone comment](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742935)
states that she chose not to release her second-milestone solution. The reviewed
public sources do not disclose the current 75.56 recipe. We must not present
another competition's model, training procedure or hardware as her ARC3 method.

The authenticated public-account inspection found seven notebooks, four models
and two datasets. The model IDs initially looked relevant: an OPD 32B checkpoint
and separate DFlash drafts. However, the
[FM-Pochi card](https://huggingface.co/fieldsmodelorg/FM-Pochi-32B-ProofPilot)
explicitly links these exact Kaggle artifacts to AIMO Proof Pilot. They are math
assets, not evidence of the ARC3 checkpoint. Their existence does not justify an
ARC3 model switch.

Her [Proof Pilot write-up](https://www.kaggle.com/competitions/ai-mathematical-olympiad-proof-pilot/discussion/715176)
reports a trained/distilled 32B system with candidate generation, verification,
refinement and selection, deployed with quantization and a draft model. It also
describes substantial training compute and missing clean component ablations.
This supports investigating trained agent behavior and candidate correction as
directions; it does not establish that ARC3 uses them or that untrained role
prompts reproduce the result.

[Agent Factory 3](https://github.com/ycchen-tw/agent-factory-3) publicly implements
agentic training and asynchronous rollouts for GPT-OSS, including Wordle and
Minesweeper examples. It documents multi-GPU training. This is real relevant
engineering experience, but neither an ARC3 release nor a single-RTX/two-hour
training recipe. The [Fields Model team page](https://fieldsmodel.org/about)
identifies Chen's focus as LLM training; affiliation does not reveal the method
or compute behind a particular ARC3 submission.

Her public startup notebook was downloaded read-only to
`reference/kaggle/leader-launch-20261101/`. It uses pre-reading and saved compile
caches for GPT-OSS on an AIMO H100 setup. Its six-minute title is not a measured
startup estimate for our different Flash-Next/RTX configuration. We already use
checkpoint prefetching, prefix retention and speculative decoding.

## Testable differences, with evidence strength

| Direction | Evidence | Implication |
| --- | --- | --- |
| Specialized weights / learned tool behavior | Direct evidence in Chen's other competition; ARC3 method unknown | Test an existing trained checkpoint before assuming more prompting closes the gap. |
| Generate, challenge, revise, select | Direct evidence in the proof system; ARC transfer unmeasured | Investigate selective independent review of stuck interpretations. A second copy sharing the actor's assumptions can fail too. |
| Efficient reasoning and serving | Public deployment evidence; our server already has strong prefix reuse and a draft | Measure completed useful decisions, action efficiency and score under equal total time. Higher token throughput alone is insufficient. |
| Better allocation across games | Plausible, no leader-specific method disclosed | Our fixed-trace allocation oracle cannot solve missing trajectories. This cannot be the entire intervention. |

## New public checkpoint search changed the next experiment

The search was extended to current public Kaggle models, not just notebooks.
Metadata/cards and exact variation/file snapshots are preserved under
`reference/models/*-20261101/` and
`reports/research/arc3-model-candidates-20261101/`.

1. [Ravi's agentic LoRA](https://www.kaggle.com/models/ravinderonkaggle/flashnext-arc3-recipe-v3)
   is based on our exact checkpoint. Its card reports lower held-out next-reply
   loss but worse downstream puzzle scores: 43.43 versus 52.98 in a weights-only
   comparison. It identifies action-inefficient successful traces as a likely
   problem. Reject it as a proposed improvement. Completion-filtered self-training
   alone is not sufficient evidence for spending our quota on fine-tuning.
2. [Swift Flash-Next](https://huggingface.co/ukisai/Swift1.5-Qwen3.8-Flash-Next)
   is an efficiency/agentic post-trained derivative. Its card's headline reduction
   differs from mean reductions and from total-output cost: Terminal-Bench output
   tokens increase. Published results do not include ARC3. The Kaggle mirror is
   split into two PyTorch variations and uses a custom license. Keep as an
   historical alternative only: an existing completed deployment,
   arc-hydra-duck-swift/1, scored11.3230 with50levels and0wins. Earlier research
   missed that result. Reject as a replacement; retain existing license notices
   and do not duplicate its evaluation.
3. [ThinkingCap Flash-Next](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-Flash-Next)
   reports 38.5% macro-average thinking-token reduction with approximately one
   point lower macro accuracy on its benchmarks. These are author-reported BF16
   multi-GPU results, not ARC3 or our quantized runtime. Unlike the 27B ThinkingCap
   release, the Flash-Next card uses the Qwen Community License. A
   [public AutoRound quant](https://www.kaggle.com/models/lamdang/thinkingcap-qwen3-8-flash-next-w4a16-autoround)
   is designed for the same layout/tokenizer map as ours. This is the best current
   concrete checkpoint-bundle ablation, not a known winning checkpoint.

## Work completed toward that comparison

CPU notebook `kunalsinghh25/arc-hydra-model-compatibility-cpu-probe/1` is COMPLETE.
It read checkpoint metadata and safetensors headers, not weight payloads, in
5.63 seconds of inspection. Authoritative evidence:
`reports/kaggle/model-compatibility-cpu-probe-v1/`.

Both versions contain 224,280 tensor names with identical shapes and dtypes.
Architecture configuration outside quantization is identical. Tokenizer,
chat-template, image-processor and processor-config hashes match. There are 100
quantization-metadata differences, chiefly removed BF16 router exclusions; the
actual stored tensor schema still matches. Weight contents, draft acceptance,
real kernel loading and runtime quality remain unverified. File layouts differ:
our base has 50 files and ThinkingCap 83; each bundle is about 181 GB. A worse
startup is possible despite equal overall size.

`scripts/build_arc3_model_probe.py` built that CPU-only, offline, no-game probe,
with an external 1,800-second cap and exclusive launch journal. ARC2 development
was checked COMPLETE and paid scaling disabled before launch. Subsequent audit
found its inherited GPU machine type overrode the CPU flag, with a 24.697-second
quota increment consistent with that short run. The no-GPU-quota claim is
retracted; metadata/header measurements remain valid. See the resource correction
below and the preserved executed package/report.

`scripts/build_thinkingcap_candidate.py` has staged
`notebooks/thinkingcap_matched_candidate/`, not uploaded or launched. It verifies
the exact CPU report and frozen control hashes, pins the model version, and adds
exact checkpoint-metadata validation. Only the notebook introduction and the
target-path/metadata-preflight cell differ from the completed inspection control.
Serving, agent, scheduler, gameplay and budget cells are byte-identical. The
candidate remains a 7,200-second total development package and is explicitly
ineligible for official submission. Any future launch must also pass timeout
7200 externally and freshly verify shared jobs/quota.

The practical experiment compares checkpoint bundles, including their calibration
and sharding; it cannot isolate post-training alone. Compare against the completed
control at 31.5812675 using all 25 games, actual model lifecycle verification,
score/action efficiency, startup-adjusted gameplay time, completed response costs
and draft acceptance. Both existing packages remain frozen. The initial
sequential-only policy was subsequently revised as described below. No automatic
promotion or official submission is armed.

The larger strategic conclusion is conditional: stronger learning behavior and
better decisions under the compute budget are more credible routes to a large
gain than another optional API. A trained checkpoint may help, regress, or fail
to serve. If it helps, assess retaining the validated memory components; if it
does not, preserve the best official agent and test targeted hypothesis revision.
The official target remains unmet; no public or CPU result substitutes for it.

## Launch and resource correction, 08:43 UTC

After the prediction candidate spent more than an hour queued without gameplay,
the independent ThinkingCap evaluation was accepted as
`kunalsinghh25/arc-hydra-thinkingcap-matched-candidate/1`. Journal:
`reports/kaggle/thinkingcap-matched-v1/`; live observer:
`reports/arc3/thinkingcap-comparison/`. The two remaining ARC3 jobs are each
externally capped at 7,200 seconds, at most four GPU hours combined, and may be
scheduled simultaneously. This queue-policy revision was explicitly communicated.

The new launcher permits an existing job only when it is the acknowledged capped
prediction version and still QUEUED at launch check. Any other active shared
notebook, running prediction job, reserved quota, paid scaling, insufficient free
time or changed package blocks launch. Fresh checks found only that queued
prediction job, 101,286.643 free seconds, paid off and ARC2 COMPLETE. Both full
ARC3 budgets plus the three-hour ARC2 floor were required. No third GPU launch
or automatic official submission is armed.

Two resource defects were corrected before this checkpoint launch. First, the
model-header probe had inherited a GPU type despite its CPU flag. Kaggle's request
precedence makes that a GPU request. Quota increased by 24.697 seconds, consistent
with the run, though no device census was saved. Its CPU computation did not load
model payloads or invoke CUDA. Executed original files remain unchanged, with an
erratum in `accelerator-correction.json`. The fixed builder creates a separate
V2 package without a machine type; the CPU launcher rejects overriding types.

Second, notebook list summaries report enable_gpu=False even for known RTX runs.
The old scanner could therefore miss active shared jobs. The corrected scanner
checks all recent notebooks and labels accelerator identity unclassified. The
new fresh scan found the queued prediction notebook. Twenty-seven tests cover
resource/recovery behavior, the false-CPU ARC2 case and explicit queue budgets.
