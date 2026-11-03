# Swift 1.5 target-model experiment

Author: **UkisAI**. Public Kaggle AutoRound mirror: **phuongncn**.
Agent/harness attribution remains Daniel Franzen, Jeroen Cottaar and Tufa Labs.

Primary model card:
https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound

The author reports reasoning-token reductions on other benchmarks. Those
measurements compare BF16 checkpoints and do not establish quantized ARC-AGI-3
performance. This experiment tests the hypothesis under the existing budget.

`model.json` freezes public Kaggle variation versions and file sizes for the
two-part checkpoint (95 files, 177,291,201,631 bytes). No weights are stored in
this repository or downloaded to the Windows workspace. Kaggle mounts both
parts read-only. `scripts/swift_model_view.py` checks every file's presence/size,
AutoRound architecture and shard-index completeness before linking them into
one view. It never copies or rewrites the model tensors.

Metadata checks established `auto-round`, symmetric INT4, group size 128 and
the same tokenizer SHA-256 as the original FR-Spec map:
`06b9509352d2af50381ab2247e083b80d32d5c0aba91c272ca9ff729b6a0e523`.
The live GPU input check reports 82 indexed shards and mounted config SHA-256
`172763afc483a36814dcfcc34f02b2acc116b9b7d0fe2889e19d239934f565b6`,
matching the inspected upstream revision in `model.json`. File sizes are not
cryptographic verification of the weights; the original runtime still performs
its tokenizer-map compatibility check before serving.

```powershell
.venv/Scripts/python.exe scripts/build_duck_notebook.py --mode benchmark --model-variant swift-1.5
.venv/Scripts/python.exe scripts/kaggle_local.py kernels push -p notebooks/duck_swift --timeout 12000
```

Private run `kunalsinghh25/arc-hydra-duck-swift/1`: all 25 public games, one pass,
two hours after model readiness. Retains original runtime, draft checkpoint,
agent, prompts, tools and scheduling; no rolling summaries or v3 overlay. The
notebook uses a distinct ID and default output directory. Upload hashes are in
`reports/kaggle/duck-swift-v1/upload.json`.

The run is COMPLETE. All 25 games have verified model gameplay. Public mean
score was **11.3230**, with 50 levels and zero full wins, compared with the
original model's **43.7621**, 102 levels and five wins under the same public
budget. Swift is not promoted. These single-pass measurements do not establish
hidden competition scores or isolate the cause of the regression. Final metrics
and analysis are in `reports/kaggle/duck-swift-v1/`.

Swift's custom license and Qwen's base license apply separately from the
Apache-2.0 agent. Their texts and notice are retained from parent revision
`0bd4fe22431372cdad1979267d3ab45aa7e6150a` in `LICENSE.SWIFT`, `LICENSE.QWEN`
and `NOTICE.SWIFT`. These files do not assert competition prize eligibility.

An initial automatic-review rejection suspected `models get` would download
the full checkpoint. Inspection of installed CLI source proved the command
only writes model-card JSON; the verified metadata-only retry succeeded. No
large local transfer or unresolved approval request remains.
