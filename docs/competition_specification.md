# Competition specification — verified 2026-10-24

This is a development audit, not certification of eligibility or submission validity.

| Requirement | Finding | Source / status |
|---|---|---|
| Rules, external data, pretrained models | Authenticated SDK pages retrieved: public external data/models permitted subject to the rules' accessibility requirements; no external model used | https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules |
| Runtime, RAM, action budgets | CPU/GPU notebooks each limited to 9 hours; hardware RAM and per-game action cap remain unverified | Authenticated Code Requirements page |
| Deadline | 2026-11-02 23:59 UTC, which is November 3 at 05:29 IST; retain November 2 as our development cutoff | Authenticated Timeline page and competition-list API |
| Python | Starter requests 3.12; package minimum is 3.12; actual Kaggle run used Python 3.13 paths and passed public smoke | Starter + attached package metadata + Kaggle v2 runtime log |
| GPU | Starter supports CPU, T4, P100, RTX6000; defaults T4 | README and scripts/build_notebook.py; actual allocation UNVERIFIED |
| Internet | Generated notebook disables internet; installs from attached wheels | scripts/build_notebook.py, notebooks/kernel-metadata.json |
| Submission | Starter builds a notebook; gateway produces submission.parquet during competition rerun | scripts/build_notebook.py |
| Save/run versus evaluation | Save/run emits dummy parquet; hidden competition rerun executes agent | scripts/build_notebook.py; passing save/run alone does not validate gameplay |
| Upload | make submit builds and pushes; competition entry is a separate Kaggle UI step | README / Makefile |
| Public versus hidden | 25 public development games; 110 private evaluation games split equally between public/private leaderboard evaluation | Authenticated data-description page |
| Memory boundaries | Agent object per game; no cross-game memory planned | vendor framework agents/swarm.py |
| Optional models | No weights or hosted inference used in v0.1 | Implementation decision; authenticated external-data rules inspected |

Official starter: https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter

Scoring documentation: https://docs.arcprize.org/methodology

RHAE combines completion and squared human/agent action ratios. Documentation specifies a per-level 1.15 cap, level-index weights, a completion-dependent game cap, and averaging across games. Local engine implementation must be checked before implementing an independent estimate. Missing human baselines must remain unavailable. Counts from the agent loop may differ from scorecard counts, particularly for resets. There is no evidence here authorizing action batching or establishing reset cost. Read the installed wrapper and scorecard before relying on either.

Before any final submission: read the authenticated competition rules, confirm exact hardware/runtime/data restrictions and deadline, attach the competition data, configure the Kaggle handle, and execute the notebook in Kaggle. None of those checks is implied by a locally generated notebook.

## Installed implementation verification

Installed arc-agi 0.9.9 / arcengine 0.9.3, under Python 3.12.10. Exact transitive versions are in requirements-lock.txt; these are local versions, not verified Kaggle wheel versions.

- `arcengine/enums.py`: FrameData.frame is list[list[list[int]]], with state, levels_completed, win_levels, action_input, guid, full_reset and available_actions. FrameDataRaw.frame is a runtime list of NumPy arrays. Policy input is observed images and advertised actions only.
- GameAction IDs: RESET 0; ACTION1 through ACTION7 are 1 through 7. Only ACTION6 is ComplexAction, with x/y integers in 0..63. SimpleAction has optional game_id. The adapter does not assume game-specific action semantics.
- `arc_agi/wrapper.py`: reading observation_space returns the last response, without submitting an action. action_space converts advertised IDs. No action batching exists in the inspected interface.
- `arcengine/base_game.py`: RESET restarts the current level after play; it performs a full reset at action count 0 or after WIN, subject to ONLY_RESET_LEVELS. GAME_OVER is recovered through RESET.
- `arc_agi/scorecard.py`: initial full reset opens a play without charging a reset action; level reset increments reset and action counts. IDs 1 through 7 increment scorecard actions. The harness preserves raw official scorecards alongside agent command counts.
- EnvironmentScoreCalculator uses min(115, 100*(human/actions)**2) for completed levels with positive action counts, otherwise zero. It weights by 1-indexed level and caps the result by completed positive-score weights / all level weights times 100. The scorecard averages games. Missing baselines produce zero plus a diagnostic message in the package; our harness instead reports those scores as unavailable.

Metric calculation delegates to the installed official scorer. Tests cover weighting, completion cap, efficiency and unavailable baselines. Hidden gateway compatibility still requires a Kaggle run.

## Authenticated follow-up — 2026-10-24

The user's new project-local token successfully authenticated through official Kaggle CLI 2.2.5 / SDK 0.1.38. The competition-list API reports userHasEntered=True; competition files are accessible. Token values are never recorded in the repository.

- Authenticated rules specify one submission per day and up to two final selections. The starter README's five-per-day statement was incorrect and has been corrected. At inspection, zero submissions had been made and one remained available that day.
- Code Requirements specify a nine-hour CPU or GPU notebook limit, disabled internet, public external data/models permitted, and automatic submission-file generation.
- The entry/team-merger deadline is October 26 at 23:59 UTC (October 27, 05:29 IST). Final submission deadline is November 2 at 23:59 UTC (November 3, 05:29 IST).
- Rules include open-system/model/parameter requirements and winner source-delivery/license obligations. Hydra uses no proprietary inference service or pretrained weights; a future model needs a fresh eligibility/license check.
- Attached wheels include arc-agi 0.9.8, arcengine 0.9.3, NumPy 2.4.4 and Pydantic 2.13.2. The attached agent source was downloaded and inspected: constructor/frame/action contracts match, while its reasoning forwarding predates the upstream fix. Hydra passes its per-agent payload/reasoning directly through the verified wrapper interface.
- The attached 0.9.8 scorer implements the 115 per-level efficiency cap and completion-dependent game cap, matching the local 0.9.9 scorer. The data-description page still describes a 100 per-level cap. Actual attached code takes precedence for our local metric; remote scores will be recorded as returned rather than inferred from prose.

Sources: authenticated `competition_list_pages` and `competition_list_files` via the official SDK, for this competition's Rules, Code Requirements, Timeline and data-description pages. The raw retrieved pages and third-party sources remain in gitignored reference/kaggle; normalized findings are recorded here. Deployment progress is in docs/kaggle_validation.md.
