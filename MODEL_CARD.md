---
license: apache-2.0
base_model: Qwen/Qwen3.8-27B
tags: [arc-agi-3, lora, research-artifact, negative-result]
---

# Qwen3.8-27B ARC3 research adapters (rejected in gameplay)

These are the actual native and serving-converted adapters from the completed
ARC3 LoRA pilot. **They regressed in real gameplay and were rejected.** They
are released for reproducibility, not as the strongest agent or a winning model.
The project's strongest verified agent uses a different FlashNext checkpoint.

## Base, format and license

- Exact training base: `dangkhoa2016/qwen-qwen3-8-27b/Transformers/default/1` on Kaggle.
- Base family: [Qwen/Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B).
- Base license: Apache-2.0. The pinned license text is preserved in `artifacts/licenses/Qwen3.8-27B-LICENSE.txt`.
- Native PEFT adapter: 435,280,528 bytes, SHA-256 `45c87044ffc3c133e4dfb637ed769e13fb78b040c7aefba59672183783760c4d`.
- Serving adapter: 466,767,600 bytes, SHA-256 `d43af1abea2c99c6fe527546c72bcb6acdb4cdb972a6dc9181a7b42e007e7b30`.

Only adapter weights are released here; the 27B base is a separate public model.
The serving adapter contains the projection conversion required by the tested
SGLang runtime. Use the native adapter for the native training layout. Neither
adapter is a drop-in modification of the larger FlashNext target.

## Actual training and evaluation

One epoch: 158 examples, 40 optimizer updates, 1,626,879 input tokens and
103,939 supervised tokens. Rank 16, alpha 32, learning rate 1e-5, accumulation 4.
400 supported language projections, 108,789,760 trainable parameters; vision
and base weights frozen. Whole-game gradient splits were retained.

Sampled validation loss on eight examples from four games improved
0.76633628 to 0.72365186, with an exact independent adapter reload. This did
not predict better gameplay. On five gradient-held-out public games, the
base scored 15.7143 with 12 levels; adapted scored 5.3301 with 7 levels.
All five adapted game scores regressed; neither arm completed a full game.
These public experiments are not unseen official evaluation.

Training, conversion, routing and the repaired reporting race are documented in
`reports/kaggle/qwen27-lora-pilot-v1/sft-pilot/training-report.json` and
`reports/arc3/qwen27-lora-gameplay/completed-reconciliation.json`. Paths are
relative to the project directory; in the combined repository it is
`ARC-AGI-3-Kaggle-Starter/`.

## Restore and inspect

```bash
python scripts/restore_artifacts.py --kind adapters
python scripts/restore_artifacts.py --kind adapters --verify-only
```

`ARTIFACTS.json` maps downloads to the original adapter directories, including
the native and serving `adapter_config.json` already in Git. Use the pinned
base/runtime and the included training/export implementation to reproduce the
experiment. No inference is launched by downloading or restoring these files.

## Data provenance

Training used outcome-filtered model replies from our public-game development
trajectories. The raw records, exact processed examples, split records, masks,
tokenizer/dependency artifacts and reproducibility input bundle are preserved
in the companion raw-data release archive. These development games had already
been studied; the gradient holdout is not a blind competition holdout.
Third-party datasets, models, wheels and code retain their upstream licenses
and attribution, with source manifests and license files preserved.
