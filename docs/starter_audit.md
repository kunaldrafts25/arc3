# Official starter audit

Inspected 2026-10-24. Starter commit `eeb1535404f321d280a8f9194bbc1d7aca5f05fc`; framework commit `4743e7d0aaae0ded0d98a89a7e282e63564cd58b`.

## Structure and dependencies

The starter has one agent file, three Python scripts (local play, notebook generation, import slimming), a Makefile and Kaggle metadata. No starter test suite or dependency lock is supplied. Setup requests Python 3.12, arc-agi >=0.9.6, kaggle >=2.2, python-dotenv, pandas and pyarrow. Framework metadata additionally lists numerous hosted-LLM dependencies; the starter deliberately slims its registry to avoid loading them. No hosted model is required for the baseline.

Source: https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter and https://github.com/arcprize/ARC-AGI-3-Agents

## Actual framework interface

`Agent.__init__(self, card_id: str, game_id: str, agent_name: str, ROOT_URL: str, record: bool, arc_env: EnvironmentWrapper, tags: Optional[list[str]] = None)`.

Required methods:

```python
is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool
choose_action(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction
```

`frames` is the agent's accumulated history, initially `[FrameData(levels_completed=0)]`. The `latest_frame` passed to choose_action is converted from the environment's current `FrameDataRaw`. These are not necessarily the same object on the first call. Conversion preserves game_id, frame arrays as lists, state, levels_completed, win_levels, guid, full_reset and available_actions.

The main loop calls is_done on stored history, chooses one action, submits it via `arc_env.step(action, data=action.action_data.model_dump(), reasoning=...)`, appends a validated response, then increments action_counter. There is no multi-action batching in this path. WIN is the sample's successful termination; NOT_PLAYED and GAME_OVER cause RESET. The framework loop uses `action_counter <= MAX_ACTIONS`, so its nominal cap permits one extra action. Hydra needs its own `>=` stop condition. Errors from the environment can escape the base main loop.

`Swarm` creates one agent per game, executes them in threads, opens/closes an arcade scorecard, and records final results. Agent memory is per instance. GameAction enum instances carry mutable action_data and reasoning: parameters must be rehydrated under a shared lock when submitting concurrently.

## Baseline and debugging

The starter seeds global random from current time and Python's game-id hash, samples every non-RESET enum, and biases ACTION4 on ls20. It does not filter against available_actions. ACTION6 receives random 0..63 coordinates. This is a plumbing baseline, not a performance standard. It must be preserved for comparison.

`scripts/play_local.py` hosts real environments with `Arcade(operation_mode=OperationMode.NORMAL)`, caches downloaded games, invokes `Agent.main()`, prints levels/actions and fetches a scorecard. Its max-steps flag uses min(existing cap, requested cap), so it cannot raise the default 80. Reports must disclose this when interpreting its counts. Terminal rendering and frame recordings are available; raw game internals must never be passed to the policy.

Original commands: `make setup`, `make verify-local` (ls20 and vc33, 50-step setting), `make play-local`, `make notebook`, `make submit`, `make status`. The Makefile assumes POSIX shell and `.venv/bin`, so Windows uses `.venv/Scripts/python.exe scripts/...` and the added setup_windows.ps1.

Framework tests use `python -m pytest tests` from its root. Some tests import `agents.structs`, which is absent in this checkout, and legacy agent constructors omit required arc_env. Results must be recorded rather than treating these as Hydra regressions or rewriting upstream tests.

## Notebook / submission

The official builder installs from the attached offline competition wheel directory, writes the agent to /tmp, copies the framework to /kaggle/working, replaces its registry, configures the gateway and invokes `python main.py --agent myagent` only on competition rerun. Save/run creates a dummy parquet. The gateway owns real submission output. We preserve this flow and extend source packaging for hydra/*.py.

`make submit` pushes a notebook; the human must separately select Submit to Competition and submission.parquet. Credentials and a real username are not supplied by the repository. No remote upload has been performed by this audit.
