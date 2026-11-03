"""Repeatable observation-only runs through the official Agent.main loop.

Use --bootstrap once to download public games; subsequent runs are offline.
Exceptions are recorded and make the command fail, never count as successes.
"""
from __future__ import annotations
import argparse
import json
import logging
import os
import random
import sys
import time
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor" / "ARC-AGI-3-Agents"))

from arc_agi import Arcade, OperationMode
from arcengine import GameState
from agent.my_agent import MyAgent


def starter_class():
    # Snapshot verified against the upstream commit; also works from source ZIP.
    source = (ROOT / "baselines/starter_agent.py").read_text(encoding="utf-8")
    namespace = {"__name__": "starter_baseline"}
    exec(compile(source, "starter_baseline.py", "exec"), namespace)
    return namespace["MyAgent"]


def run(args):
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.WARNING)
    if args.record:
        os.environ["RECORDINGS_DIR"] = str(ROOT / "recordings")
    rows = []
    sources = {p.relative_to(ROOT).as_posix():p.read_text(encoding="utf-8")
               for p in sorted((ROOT/"hydra").rglob("*.py"))}
    sources["agent/my_agent.py"] = (ROOT/"agent/my_agent.py").read_text(encoding="utf-8")
    encoded_sources = json.dumps(sources, sort_keys=True)
    source_digest = sha256(encoded_sources.encode()).hexdigest()
    output.with_suffix(".source.json").write_text(encoded_sources, encoding="utf-8")
    policies = args.policies.split(",")
    for policy in policies:
        for seed in map(int, args.seeds.split(",")):
            mode = OperationMode.NORMAL if args.bootstrap else OperationMode.OFFLINE
            arc = Arcade(operation_mode=mode)
            envs = arc.get_environments()
            wanted = set(args.games.split(",")) if args.games else None
            game_ids = sorted({e.game_id for e in envs if not wanted or e.game_id.split("-")[0] in wanted or e.game_id in wanted})
            if not game_ids:
                raise RuntimeError("No requested environments available; bootstrap the public games first")
            if wanted:
                missing = wanted - {g.split("-")[0] for g in game_ids} - set(game_ids)
                if missing:
                    raise ValueError(f"Requested games unavailable: {sorted(missing)}")
            for game_id in game_ids:
                started = time.monotonic()
                row = dict(agent_version="0.2.0-dev" if policy in ("abstract", "motion", "clicks", "reasoning") else "0.1.0",
                           source_sha256=source_digest, policy=policy, game_id=game_id, seed=seed,
                           completion_status=None, levels_completed=None, action_count=None,
                           human_reference_actions=None, official_score_if_available=None,
                           estimated_score=None, exceptions=[], level_completions=[])
                card = None
                agent = None
                try:
                    card = arc.open_scorecard(tags=["hydra", policy, str(seed)])
                    env = arc.make(game_id, scorecard_id=card, seed=args.env_seed)
                    if env is None:
                        raise RuntimeError("Official arcade could not create environment")
                    cls = starter_class() if policy == "starter" else MyAgent
                    # Equal strict action budget for all policies, including the
                    # upstream loop's off-by-one. Baseline action policy unchanged.
                    class Budgeted(cls):
                        def is_done(self, frames, latest_frame):
                            return self.action_counter >= args.steps or super().is_done(frames, latest_frame)
                    Budgeted.MAX_ACTIONS = args.steps
                    extra = {} if policy == "starter" else {"hydra_seed": seed, "hydra_policy": policy}
                    agent = Budgeted(card_id=card, game_id=game_id, agent_name=policy,
                                     ROOT_URL="http://localhost", record=args.record, arc_env=env, **extra)
                    random.seed(seed)  # pristine starter uses global RNG; runs sequentially
                    agent.main()
                    if args.record:
                        row["recording"] = agent.recorder.filename
                    final = agent.frames[-1]
                    row.update(completion_status=final.state == GameState.WIN,
                               levels_completed=final.levels_completed,
                               total_levels=final.win_levels,
                               final_state=final.state.name,
                               action_count=agent.action_counter)
                    previous_level, previous_count = 0, 0
                    for count, frame in enumerate(agent.frames[1:], 1):
                        if frame.levels_completed > previous_level:
                            row["level_completions"].append(dict(
                                level_id=frame.levels_completed, cumulative_action_count=count,
                                actions_since_previous_completion=count-previous_count))
                            previous_level, previous_count = frame.levels_completed, count
                    if hasattr(agent, "controller"):
                        row["diagnostics"] = dict(agent.controller.stats)
                        row["model_predictions"] = agent.controller.stats["model_predictions"]
                        row["model_exact_matches"] = agent.controller.stats["model_matches"]
                        row["exceptions"].extend(agent.errors)
                except Exception as error:
                    row["exceptions"].append(f"{type(error).__name__}: {error}")
                    if agent is not None:
                        row["action_count"] = agent.action_counter
                finally:
                    if card is not None:
                        try:
                            scorecard = arc.close_scorecard(card)
                            if scorecard is not None:
                                row["scorecard"] = scorecard.model_dump(mode="json")
                                row["scorecard"].pop("api_key", None)
                                row["official_score_if_available"] = getattr(scorecard, "score", None)
                                runs = [run for e in scorecard.environments for run in e.runs]
                                row["scorecard_action_count"] = sum(r.actions for r in runs)
                                row["human_reference_actions"] = [r.level_baseline_actions for r in runs]
                                if any(r.message for r in runs):
                                    row["official_score_if_available"] = None
                        except Exception as error:
                            row["exceptions"].append(f"scorecard: {type(error).__name__}: {error}")
                    row["runtime_seconds"] = round(time.monotonic()-started, 6)
                    row["environment_seed"] = args.env_seed
                    rows.append(row)
                    with output.open("w", encoding="utf-8") as stream:
                        for result in rows:
                            stream.write(json.dumps(result) + "\n")
                    print(json.dumps({k: row[k] for k in (
                        "policy", "seed", "game_id", "levels_completed", "action_count",
                        "official_score_if_available", "runtime_seconds", "exceptions")}), flush=True)
    return 1 if any(r["exceptions"] for r in rows) else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", default=None)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--env-seed", type=int, default=0)
    parser.add_argument("--policies", default="random,novelty,memory,planning", choices=None)
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--record", action="store_true", help="Save official frame/action recordings for diagnosis")
    parser.add_argument("--output", default="reports/benchmark.jsonl")
    args = parser.parse_args()
    allowed = {"starter", "random", "novelty", "memory", "planning", "persistent", "coverage", "abstract", "motion", "clicks", "reasoning"}
    if args.steps <= 0 or not set(args.policies.split(",")) <= allowed:
        parser.error("positive steps and supported policies required")
    raise SystemExit(run(args))
