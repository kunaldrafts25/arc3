"""Replay frozen public actions to audit recovery notices, never choose new actions.

No model server, game-source inspection, hidden inputs, or network is used.
Future level completions are retrospective diagnostics only, not policy inputs.
"""
import argparse
from collections import deque
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hydra.recovery_monitor import RecoveryMonitor, render_notice


def replay(arcade, game, deadline):
    from arcengine import GameAction

    env = arcade.make(game['game_id'], seed=0)
    if env is None:
        raise ValueError('Recorded public game is unavailable')
    # Matches taaf.game_api: make-time full reset, subsequent level resets.
    os.environ['ONLY_RESET_LEVELS'] = 'true'
    state = env.observation_space
    n = game['number_of_levels']
    if state.win_levels != n:
        raise ValueError('Public environment level count differs from recording')
    counts = [0] * n
    completed = 0
    notices = []
    completions = []
    recent = deque(maxlen=257)
    monitor = RecoveryMonitor()
    frame_hash = sha256()

    def observe(step, action):
        rows = tuple(tuple(int(c) for c in row) for row in state.frame[-1])
        level = max(1, min(n, int(state.levels_completed) + 1))
        current = NS(step=step, level=level, grid=rows)
        recent.append(NS(action=action, frame=current))
        frame_hash.update(bytes(c for row in rows for c in row))
        return current

    current = observe(0, 'INITIAL')
    start = time.monotonic()
    for i, record in enumerate(game['history']):
        if time.monotonic() >= deadline:
            return dict(game_id=game['game_id'], complete=False, stop_reason='audit budget',
                        actions_replayed=i, notices=len(notices))
        # Positive token charges identify generation before an action. Decisions
        # with no environment action are absent from benchmark.json entirely.
        if record['generated_tokens'] > 0:
            evidence = monitor.observe(current, list(recent))
            if evidence:
                notices.append(dict(**evidence, rendered_characters=len(render_notice(evidence))))
        if completed < n:
            counts[completed] += 1
        action = record['action']
        state = env.step(GameAction[action['id']], data=action['data'])
        if state is None or not state.frame:
            raise ValueError('Recorded action no longer yields an observable frame')
        new_completed = max(completed, int(state.levels_completed))
        if new_completed > completed:
            completions.append(dict(step=i + 1, completed=new_completed))
        completed = new_completed
        # Coordinates are retained in the action key: different clicks must not
        # be counted as repetitions of the same transition.
        label = json.dumps(action, sort_keys=True, separators=(',', ':'))
        current = observe(i + 1, label)
    expected = list(game['actions_per_level'])
    parity = completed == game['levels_completed'] and counts == expected
    for notice in notices:
        next_completion = next((c['step'] for c in completions
                                if c['step'] > notice['step'] and c['completed'] >= notice['level']), None)
        notice['later_completed_same_level'] = next_completion is not None
        notice['actions_to_later_completion'] = None if next_completion is None else next_completion - notice['step']
    return dict(game_id=game['game_id'], complete=True, parity=parity,
                expected_levels=game['levels_completed'], replayed_levels=completed,
                expected_counts=expected, replayed_counts=counts,
                actions_replayed=len(game['history']), notices=notices,
                observation_sha256=frame_hash.hexdigest(), elapsed_seconds=time.monotonic() - start)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=600)
    args = parser.parse_args()
    from arc_agi import Arcade, OperationMode

    path = ROOT / 'reports/kaggle/general-learner-v1/benchmark.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    logger = logging.getLogger('recovery-replay')
    logger.setLevel(logging.WARNING)
    arcade = Arcade(operation_mode=OperationMode.OFFLINE, logger=logger)
    deadline = time.monotonic() + args.seconds
    results = []
    output = ROOT / 'reports/kaggle/general-learner-v1/recovery-replay.json'
    for game in data['game_runs']:
        if time.monotonic() >= deadline:
            break
        try:
            result = replay(arcade, game, deadline)
        except Exception as exc:
            result = dict(game_id=game['game_id'], complete=False, error_type=type(exc).__name__, error=str(exc))
        results.append(result)
        valid = [r for r in results if r.get('complete') and r['parity']]
        notices = [v for r in valid for v in r['notices']]
        report = dict(checked_at=datetime.now(timezone.utc).isoformat(),
                      source_sha256=sha256(path.read_bytes()).hexdigest(),
                      monitor_sha256=sha256((ROOT / 'hydra/recovery_monitor.py').read_bytes()).hexdigest(),
                      games_expected=len(data['game_runs']), games_attempted=len(results),
                      games_matching_level_and_action_counts=len(valid),
                      notices_on_parity_games=len(notices),
                      notices_before_later_level_success=sum(v['later_completed_same_level'] for v in notices),
                      notices_without_repeated_visible_transition=sum(not v['repeated_visible_transitions'] for v in notices),
                      per_game=results,
                      boundary='Frozen public actions replayed with seed 0. Matching aggregate level/action counts is necessary but does not prove every original pixel matched (original pixel hashes unavailable). Positive generation-token charges approximate decision boundaries and omit no-action decisions. Future completions used only for retrospective notice audit. No counterfactual policy, score gain or hidden generalization measured.')
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(game=result['game_id'], complete=result['complete'], parity=result.get('parity'),
                              notices=len(result['notices']) if isinstance(result.get('notices'), list) else result.get('notices'),
                              error=result.get('error'))), flush=True)


if __name__ == '__main__':
    main()
