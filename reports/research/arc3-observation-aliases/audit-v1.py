"""Measure observation aliasing on frozen public actions, without game-source access.

Every prediction is the last outcome for a previously observed key, frozen before
the next env.step. History suffixes are public observations/actions, not engine
state. This diagnostic cannot identify the cause of inconsistent outcomes or
establish that a new agent can exploit them.
"""
import argparse
from collections import Counter, deque
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
LENGTHS = (0,1,2,4,8)


def fingerprint(observation):
    grid = observation.frame[-1]
    shape = (len(grid),len(grid[0]))
    pixels = bytes(int(c) for row in grid for c in row)
    digest = sha256(pixels).hexdigest()
    # Include all exposed state metadata relevant to ordinary action dispatch.
    # Exclude GUID/action_input: these identify observations or echo the action,
    # rather than an independently observed board state.
    key = (shape,digest,tuple(sorted(observation.available_actions)),
           observation.state.name,int(observation.levels_completed))
    return key,pixels


def replay(arcade, game, deadline):
    from arcengine import GameAction
    env = arcade.make(game['game_id'],seed=0)
    os.environ['ONLY_RESET_LEVELS'] = 'true'
    raw = env.observation_space
    if raw.win_levels != game['number_of_levels']:
        raise ValueError('Environment level count differs from frozen recording')
    completed = 0
    counts = [0]*game['number_of_levels']
    digest = sha256()
    seen = {length:{} for length in LENGTHS}
    outcomes = {length:{} for length in LENGTHS}
    stats = {length:Counter() for length in LENGTHS}
    context = deque(maxlen=max(LENGTHS))
    examples = []
    for index,record in enumerate(game['history']):
        if time.monotonic() >= deadline:
            raise TimeoutError('CPU observation-alias audit budget exhausted')
        before,_ = fingerprint(raw)
        command = record['action']
        action = json.dumps(command,sort_keys=True,separators=(',',':'))
        reset = command['id'] == 'RESET'
        keys = {length:(before,action,tuple(context)[-length:] if length else ()) for length in LENGTHS}
        # Lookup is strictly before execution: no future outcome informs it.
        frozen = {length:seen[length].get(key) for length,key in keys.items()}
        old_completed = int(raw.levels_completed)
        counts[completed] += 1
        raw = env.step(GameAction[command['id']],data=command['data'])
        if raw is None or not raw.frame:
            raise ValueError('Recorded action returned no public observation')
        completed = max(completed,int(raw.levels_completed))
        after,pixels = fingerprint(raw)
        digest.update(pixels)
        boundary = reset or raw.state.name in ('WIN','GAME_OVER') or int(raw.levels_completed) != old_completed
        if boundary:
            # No collision across a reset/death/level boundary can establish a
            # within-level predictive inconsistency. Previous public cases are
            # retained, but history context is explicitly reset.
            for counter in stats.values():
                counter['excluded_boundary_actions'] += 1
            context.clear()
            continue
        for length,key in keys.items():
            counter = stats[length]
            counter['eligible_actions'] += 1
            known = outcomes[length].setdefault(key,set())
            if frozen[length] is not None:
                counter['predictions'] += 1
                if frozen[length] == after:
                    counter['last_outcome_matches'] += 1
                else:
                    counter['last_outcome_mismatches'] += 1
                    if length == 0 and len(examples) < 5:
                        examples.append(dict(step=index,action=command,before=before,
                            previously_observed_outcome=frozen[length],actual_outcome=after,
                            preceding_public_transitions=list(context)))
            else:
                counter['unknown'] += 1
            if known and after not in known:
                counter['new_distinct_outcome_for_seen_key'] += 1
            known.add(after)
            seen[length][key] = after
        context.append((before,action))
    parity = completed == game['levels_completed'] and counts == game['actions_per_level']
    for length in LENGTHS:
        stats[length]['unique_keys'] = len(outcomes[length])
        stats[length]['keys_with_multiple_outcomes'] = sum(len(v)>1 for v in outcomes[length].values())
    return dict(game_id=game['game_id'],actions_replayed=len(game['history']),parity=parity,
        completed_levels=completed,observation_sha256=digest.hexdigest(),
        history_suffixes={str(k):dict(v) for k,v in stats.items()},examples=examples)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'reports/kaggle/general-learner-v1/benchmark.json')
    parser.add_argument('--seconds',type=int,default=600)
    parser.add_argument('--output',type=Path,default=ROOT/'reports/research/arc3-observation-aliases/general-learner-v1.json')
    args = parser.parse_args()
    from arc_agi import Arcade,OperationMode
    logger = logging.getLogger('observation-alias-audit');logger.setLevel(logging.ERROR)
    arcade = Arcade(operation_mode=OperationMode.OFFLINE,logger=logger)
    raw = json.loads(args.source.read_text(encoding='utf-8'))
    output = args.output.resolve()
    if not output.is_relative_to(ROOT/'reports/research'):
        raise ValueError('CPU research reports must remain under reports/research')
    output.parent.mkdir(parents=True,exist_ok=True)
    deadline = time.monotonic()+args.seconds
    results = []
    reference = ROOT/'reports/research/prediction-real-replay-v2/diagnostic.json'
    reference_report = json.loads(reference.read_text(encoding='utf-8'))
    reference_hashes = {g['game_id']:g['observation_sha256'] for g in reference_report['per_game']}
    same_source = sha256(args.source.read_bytes()).hexdigest() == reference_report['source_sha256']
    for game in raw['game_runs']:
        result = replay(arcade,game,deadline)
        if same_source:
            result['matches_prior_replay_digest'] = result['observation_sha256'] == reference_hashes[game['game_id']]
        results.append(result)
        totals = {str(k):dict(sum((Counter(g['history_suffixes'][str(k)]) for g in results),Counter())) for k in LENGTHS}
        report = dict(checked_at=datetime.now(timezone.utc).isoformat(),
            source_sha256=sha256(args.source.read_bytes()).hexdigest(),
            script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),games_expected=len(raw['game_runs']),
            games_replayed=len(results),parity_games=sum(g['parity'] for g in results),
            actions_replayed=sum(g['actions_replayed'] for g in results),
            matching_prior_replay_digests=sum(g.get('matches_prior_replay_digest',False) for g in results) if same_source else None,
            history_suffixes=totals,per_game=results,
            boundary='Frozen actions from previously completed public model gameplay; no new policy evaluation. Full final-frame pixels, available actions, exposed state and completed-level count identify observations, not hidden state. Inconsistent next observations can reflect partial observability, randomness or reset-dependent effects; their cause is not identified. Longer histories change coverage and cannot be credited with improved prediction from raw error counts alone. No learned hidden-state model, goal discovery, score gain or official-performance estimate is established.')
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(game=result['game_id'],parity=result['parity'],stats=result['history_suffixes']['0'])),flush=True)


if __name__ == '__main__':
    main()
