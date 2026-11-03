# Kaggle validation — 2026-10-24

## Version 3 — 25 October 2026

Official result: submission **57630597 COMPLETE**, public score **0.02**, no
evaluation error. The aggregate improvement over v0.1's 0.01 is small; public
FT09 mastery did not establish generalization. Development now continues with a
separate model-agent reproduction; see `docs/goal_71.md`.

Private notebook COMPLETE. The v0.2 reasoning candidate completed all six FT09
levels in 159 actions, ending in official WIN, with no exceptions in the actual
offline Kaggle runtime. LS20 and VC33 each executed 20 smoke actions without
exceptions. Outputs and runtime log are in `reports/kaggle/commit-v3`.
The FT09 commit-mode regression now requires a full win. Competition reruns
skip the public smoke and retain the official gateway workflow.

The candidate uses reasoning with a 300-action guard. This is target runtime
validation on public data. After the matched 75-run public comparison improved
from 0.150198925 to 3.942818150 without exceptions, notebook version 3 was entered
as competition submission **57630597** on 25 October. Kaggle accepted it and
reported zero submissions remaining today. Acceptance does not establish its
hidden score; see the official status/history files for that result.

Account/notebook: https://www.kaggle.com/code/kunalsinghh25/arc-hydra-arc-agi-3

Authentication succeeded using the gitignored project-local token. Competition entry and file access are confirmed. No credentials are embedded in source, notebook, logs, or release packaging.

## Version 1

Command: `python scripts/kaggle_local.py kernels push -p notebooks --accelerator NvidiaTeslaT4 --timeout 32400`.

Kaggle reported COMPLETE. The output submission.parquet was downloaded and inspected: one commit-mode row, with row_id, game_id, end_of_game and score columns, matching the starter's dummy-output path. This verifies offline installation and basic notebook execution; it does not represent game completion or a competition score.

## Version 2

Adds an offline public-game smoke cell in commit mode only. It uses the actual attached framework, wheels and public environment files, takes up to 20 actions each on ls20 and vc33, and fails the notebook on agent exceptions. Results are written to hydra_public_smoke.json. Competition reruns skip this cell and use the original gateway-driven flow. Explicitly select submission.parquet for competition entry.

Before upload, 20 local tests passed, including a concurrency test. The per-agent action payload now goes directly to the actual wrapper, allowing concurrent HTTP calls without relying on mutable enum payloads. The per-game wall-clock guard is 600 seconds, under the verified nine-hour notebook limit; the action cap stays 200. These deployment changes do not claim any score improvement.

Version 2 reported COMPLETE. Its downloaded hydra_public_smoke.json records 20 actions on each public game, novelty policy, zero completed levels at that small cap, and no exceptions. The expected submission.parquet schema was also checked. Evidence is in reports/kaggle/commit-v2.

The runtime log confirms arc-agi 0.9.8 and arcengine 0.9.3 were installed from attached wheels. The Kaggle base environment used Python 3.13 package paths, NumPy 2.1.3, Pydantic 2.13.5 and Pillow 13.0.0. Thus attached wheel availability alone does not describe every installed dependency; the actual smoke run verifies this environment can run the adapter.

## Competition entry

Command: `python scripts/kaggle_local.py competitions submit arc-prize-2026-arc-agi-3 -k kunalsinghh25/arc-hydra-arc-agi-3 -v 2 -f submission.parquet -m 'ARC-Hydra v0.1 verified offline baseline'`.

Kaggle accepted submission **57601062** and reported zero submissions remaining today. At the first status checks it was PENDING, with empty public/private score fields and no error. Acceptance is not a scored result. reports/kaggle/submission-status.json and its history record subsequent checks.

Subsequently the official status API confirmed **COMPLETE**, public score **0.01**, no private score and no evaluation error. The submitted-artifact endpoint returned HTTP 403, so hidden per-game diagnostics are unavailable. See reports/kaggle/result-analysis.md for the result, controlled action-budget experiment and limitations. No further artifact-access route was attempted.

Local tests after the smoke-gating check: 21 passed. The gate test verifies public smoke is skipped during a competition rerun.

## Reproducible commands

```powershell
.venv/Scripts/python.exe scripts/kaggle_local.py kernels status kunalsinghh25/arc-hydra-arc-agi-3
.venv/Scripts/python.exe scripts/kaggle_local.py competitions submission-limits arc-prize-2026-arc-agi-3
.venv/Scripts/python.exe scripts/kaggle_submission_status.py 57601062
```

The wrapper reads the project token and sets CLI authentication internally, keeping the token out of shell command text. The CLI's competition-pages parser failed on its documented positional form; scripts/kaggle_inspect.py uses its verified SDK method instead. requirements-deploy-lock.txt records CLI/SDK dependencies separately from the original benchmark environment lock.
