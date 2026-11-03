---
configs:
- config_name: stateful
  data_files:
  - split: train
    path: data/train-*.parquet
  - split: validation
    path: data/validation-*.parquet
  - split: test
    path: data/test-*.parquet
  default: true
- config_name: search
  data_files:
  - split: train
    path: reasoning/data/train-*.parquet
  - split: validation
    path: reasoning/data/validation-*.parquet
  - split: test
    path: reasoning/data/test-*.parquet
- config_name: physics
  data_files:
  - split: train
    path: physics/data/train-*.parquet
  - split: validation
    path: physics/data/validation-*.parquet
  - split: test
    path: physics/data/test-*.parquet
- config_name: composition
  data_files:
  - split: train
    path: composition/data/train-*.parquet
  - split: validation
    path: composition/data/validation-*.parquet
  - split: test
    path: composition/data/test-*.parquet
- config_name: ambiguity
  data_files:
  - split: train
    path: ambiguity/data/train-*.parquet
  - split: validation
    path: ambiguity/data/validation-*.parquet
  - split: test
    path: ambiguity/data/test-*.parquet
license: apache-2.0
task_categories:
- image-text-to-text
tags:
- arc-agi-3
- synthetic-data
- vision-language
- causal-reasoning
pretty_name: ARC-AGI-3 Full Transformation Curriculum
size_categories:
- 100K<n<1M
---

# ARC-AGI-3 full transformation curriculum

This release contains **444,000 deterministic multimodal episodes** across
five curriculum configs:

- **stateful:** 168,000 episodes over 12 stateful causal families;
- **search:** 76,000 episodes over 6 graph, search, and objective families;
- **physics:** 96,000 episodes over 8 object-physics families.
- **composition:** 64,000 episodes over 8 pairwise mechanic templates, with
  complete validation and test pairings absent from training.
- **ambiguity:** 40,000 episodes where all supplied hypotheses fit the visible
  history and the target is a maximally discriminating real action.

Every row contains two visible before/action/after supports, one query-before
image, and the exact registered transition call. Query results and hidden
counterfactual transitions are reconstructed only by the verifier.

## Visual inspection

The [visual QA gallery](./preview/README.md) contains ordinary PNG files for
all 39 families: 780 model-visible source frames, 312 highlighted delta maps,
and 156 labeled contact sheets. It exists independently of Parquet and Dataset
Viewer so every generator family can be reviewed directly in the file browser.

The independent atomic foundation is published in
[`ritwika96/arc-agi-3-transformation-induction`](https://huggingface.co/datasets/ritwika96/arc-agi-3-transformation-induction).
