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
    modes = [(view,length) for view in ('final_pixels','animation_sequence') for length in LENGTHS]
    seen = {mode:{} for mode in modes}
    outcomes = {mode:{} for mode in modes}
    stats = {mode:Counter() for mode in modes}
    context = deque(maxlen=max(LENGTHS))
    examples = []
    for index,record in enumerate(game['history']):
        if time.monotonic() >= deadline:
            raise TimeoutError('CPU observation-alias audit budget exhausted')
        before,_ = fingerprint(raw)
        animation_digest = sha256()
        for frame in raw.frame:
            animation_digest.update(json.dumps((len(frame),len(frame[0]))).encode())
            animation_digest.update(bytes(int(c) for row in frame for c in row))
        views = dict(final_pixels=before,animation_sequence=(before,animation_digest.hexdigest()))
        command = record['action']
        action = json.dumps(command,sort_keys=True,separators=(',',':'))
        reset = command['id'] == 'RESET'
        keys = {mode:(views[mode[0]],action,tuple(context)[-mode[1]:] if mode[1] else ()) for mode in modes}
        # Lookup is strictly before execution: no future outcome informs it.
        frozen = {mode:seen[mode].get(key) for mode,key in keys.items()}
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
        base_prediction = frozen[('final_pixels',0)]
        for mode,key in keys.items():
            counter = stats[mode]
            counter['eligible_actions'] += 1
            known = outcomes[mode].setdefault(key,set())
            if frozen[mode] is not None:
                counter['predictions'] += 1
                if base_prediction is None:
                    raise ValueError('Extended observable key predicted without a state-only baseline')
                counter['state_only_mismatches_at_same_predicted_positions'] += int(base_prediction != after)
                counter['mismatches/'+command['id']] += int(frozen[mode] != after)
                if frozen[mode] == after:
                    counter['last_outcome_matches'] += 1
                else:
                    counter['last_outcome_mismatches'] += 1
                    if mode == ('final_pixels',0) and len(examples) < 5:
                        examples.append(dict(step=index,action=command,before=before,
                            previously_observed_outcome=frozen[mode],actual_outcome=after,
                            preceding_public_transitions=list(context)))
            else:
                counter['unknown'] += 1
            if known and after not in known:
                counter['new_distinct_outcome_for_seen_key'] += 1
            known.add(after)
            seen[mode][key] = after
        context.append((before,action))
    parity = completed == game['levels_completed'] and counts == game['actions_per_level']
    for mode in modes:
        stats[mode]['unique_keys'] = len(outcomes[mode])
        stats[mode]['keys_with_multiple_outcomes'] = sum(len(v)>1 for v in outcomes[mode].values())
    return dict(game_id=game['game_id'],actions_replayed=len(game['history']),parity=parity,
        completed_levels=completed,observation_sha256=digest.hexdigest(),
        observable_keys={view+'/'+str(length):dict(stats[(view,length)]) for view,length in modes},examples=examples)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'reports/kaggle/general-learner-v1/benchmark.json')
    parser.add_argument('--seconds',type=int,default=600)
    parser.add_argument('--output',type=Path,default=ROOT/'reports/research/arc3-observation-aliases/general-learner-v2.json')
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
        totals = {key:dict(sum((Counter(g['observable_keys'][key]) for g in results),Counter())) for key in result['observable_keys']}
        report = dict(checked_at=datetime.now(timezone.utc).isoformat(),
            source_sha256=sha256(args.source.read_bytes()).hexdigest(),
            script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),games_expected=len(raw['game_runs']),
            games_replayed=len(results),parity_games=sum(g['parity'] for g in results),
            actions_replayed=sum(g['actions_replayed'] for g in results),
            matching_prior_replay_digests=sum(g.get('matches_prior_replay_digest',False) for g in results) if same_source else None,
            observable_keys=totals,per_game=results,
            boundary='Frozen actions from previously completed public model gameplay; no new policy evaluation. Observable keys use full final-frame pixels, available actions, exposed state and completed-level count, optionally the current raw public animation sequence and preceding public final-frame/action pairs. Inconsistent next observations can reflect partial observability, randomness or reset-dependent effects; their cause is not identified. Longer keys change coverage; state-only errors are also reported at exactly the same predicted positions for each key. This matching does not establish off-policy benefit. No learned hidden-state model, goal discovery, score gain or official-performance estimate is established.')
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(game=result['game_id'],parity=result['parity'],stats=result['observable_keys']['final_pixels/0'])),flush=True)


if __name__ == '__main__':
    main()
