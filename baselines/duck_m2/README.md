# Attributed public Duck M2 baseline

Original notebook downloaded through the official Kaggle API:
https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution

SHA-256: `88a379f17c3a4ba8c98715fc23155346ccd6eb289bdafebadfc61a3178f9d9bd`.
Original metadata is preserved in `upstream-metadata.json`.

Author: **Daniel Franzen**, building on **Jeroen Cottaar and Tufa Labs' Duck
harness**. The author repository is https://github.com/da-fr/arc-agi-3-solution,
inspected at commit `10882e332d883af3e61616df8c8a17d03a328a75`.
Its Apache-2.0 license is retained in `LICENSE`. This repository does not claim
authorship of the agent, serving code, prompts or harness patch.

The notebook mounts two public datasets, Intel's Qwen3.8-Flash-Next W4A16
AutoRound checkpoint, and Albucino's draft checkpoint. Weights and runtimes are
not copied into this repository. Model licenses are distinct from the harness
license; the Intel and original Qwen model cards identify Qwen Community 1.0.
Keep their notices/terms when redistributing any model-derived artifact.

Build the private evaluation notebook:

```powershell
.venv/Scripts/python.exe scripts/build_duck_notebook.py --mode preflight
```

Use `--mode benchmark` for all public games and a two-hour gameplay budget.
Both modes preserve the original full competition configuration. Only public
evaluation settings and result verification are changed. Generated metadata
retains all original offline inputs and the pinned container image, selects RTX
PRO 6000, uses our private notebook ID and disables internet.

The public evaluation waits for model readiness before starting the public
gameplay clock. It allows up to one hour from notebook initialization for model
startup, checks the server process and health, and fails explicitly if startup
cannot finish. This is public-only; competition startup behavior is unchanged.
Allow a 5,400-second notebook timeout for the preflight, or 12,000 seconds for
the two-hour public benchmark. Do not replace a running notebook version merely
because its model is still loading; inspect its terminal logs first.

An optional `--contest-reserve-seconds 600` build adds a competition-only
absolute deadline measured from notebook initialization, leaving ten minutes
for cancellation and final outputs. This is a separate lifecycle intervention,
not part of the original agent reproduction. Its prepared source is in
`notebooks/duck_m2_candidate` and has not been uploaded.

The author's write-up reports a 27.89 leaderboard score. Our reproduction is
currently unscored on hidden games. A completed five-game public preflight
verified model gameplay and seven level completions, with no full wins. The
25-game public benchmark is running. Do not treat local tests, an upload or a
running job as proof of model startup, game completion or score reproduction.

References:

- https://github.com/da-fr/arc-agi-3-solution/blob/main/WRITEUP.md
- https://github.com/Tufalabs/duck-harness
- https://huggingface.co/Intel/Qwen3.8-Flash-Next-W4A16-AutoRound
- https://huggingface.co/Qwen/Qwen3.8-Flash-Next
