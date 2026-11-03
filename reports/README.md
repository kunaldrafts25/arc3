# Result index

- [Final public ablation](public-ablation.md): 525 validated rows, seven policies, seeds 0/1/2, all 25 games.
- [Confirmation](confirmation.md): 200 validated rows, four policies, seeds 3/4, all 25 games.
- [Technical interpretation](../docs/technical_report.md): selected default, limitations and target validation boundary.
- evidence-sha256.json hashes the raw files used in the final comparisons.

All scored comparisons use environment seed 0 and a strict 200-command cap. No full game wins were observed. Final corrected novelty mean over 125 runs: 0.1491665471 on the 0–100 scale. Original starter: 0.0374617995. Completion totals include repeated runs of the same levels.

Historical evidence is retained. Original novelty rows in ablation-v01.jsonl, public-ablation-v01.jsonl and confirmation-v01.jsonl had predictive-model access and are superseded as clean novelty ablations. Final consolidated files exclude them and use novelty-corrected-v01.jsonl. two-game-ablation.md and public-ablation-progress.md are historical summaries and must not be used to choose the production default. persistence-v01.jsonl is an interrupted run during cache population and is excluded entirely.

final-official-smoke.txt records the selected policy in the official local helper at 50 commands per game: ls20 0 levels, vc33 1 level. Logs also preserve upstream test collection errors and the 19 passing upstream recorder tests. Binary-looking text logs are Windows UTF-16 redirected console output. profile-v01.prof is a local cProfile artifact.

Rebuild final summaries with `python scripts/consolidate_experiments.py`. Its assertions enforce complete game/seed coverage, unique rows, action caps and absence of recorded per-run exceptions. Notebook generation/import checks do not certify a Kaggle submission.

Kaggle follow-up: reports/kaggle/commit-v2 contains actual cloud public-smoke evidence and the runtime log. Both games ran 20 actions without exceptions. Notebook version 2 was accepted as competition submission 57601062; reports/kaggle/submission-status.json records its latest scoring status. The cloud commit parquet is a dummy artifact and is not presented as an evaluated competition score.
