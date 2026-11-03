# Qwen Max feasibility assessment

Reviewed 28 October 2026. User suggested adding Qwen Max. Assume the current
Qwen3.8-Max family; do not conflate the older `qwen-max` endpoint with it.

The [official model card](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B)
provides the open Max-class relative Qwen3.8-2.4T-A95B: 2.4 trillion total
parameters, 95 billion active. It is text-only with required thinking; the
managed Max service has additional features. It is not a drop-in replacement
for the current checkpoint/template/runtime. The repository has a
[custom license](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE),
not an Apache-2.0 label.

Weight-only arithmetic from the nominal parameter count: BF16 about 4.8 TB,
8-bit about 2.4 TB, 4-bit about **1.2 TB**, before quantization metadata, cache,
activations and serving overhead. Active parameter count does not describe
total weight storage. Our observed single GPU has about 96 GB and the host
about 177 GB RAM. Heavy disk/expert offload would be required even at four bits;
useful nine-hour performance has not been established. Do not spend a GPU pilot
or download terabytes merely to test an obviously poor memory fit.

Fresh authenticated competition-page reads at 20:15 UTC on 27 October confirm
offline notebooks and at most nine hours. A hosted Max API cannot be called by
the evaluated offline agent. Official [code requirements](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/code-requirements).

Decision: retain a deployable model for Kaggle. Consider Max as a development
teacher only: evaluate it on permitted public/synthetic learning episodes,
verify predictions/actions against actual transitions, then assess whether
teacher data or general procedures improve a smaller offline student. Separate
mechanics families before producing training examples. No ARC gain is assumed.

No paid API evaluation, model download, distillation or notebook change was made
in this assessment. A teacher branch still needs an explicit spending budget,
credentials through a private channel, and review of the selected API service's
output-reuse terms; the weight license is not a substitute for API terms.
