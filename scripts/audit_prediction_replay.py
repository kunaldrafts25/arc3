"""Prospective checks on frozen public actions, with online naive proposals.

This is real environment observation replay, not policy evaluation. No action is
selected, no game implementation is inspected, and future outcomes are unavailable
until env.step. Candidate programs need not include the real mechanics.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hydra.prediction_host import PredictionSession, measure

COLORS = 'WwgGcBMPRbSYOrNp'  # Original Duck public observation alphabet.
NAMES = dict(RESET='RESET', ACTION1='UP', ACTION2='DOWN', ACTION3='LEFT',
             ACTION4='RIGHT', ACTION5='SPACE', ACTION6='MOUSE', ACTION7='UNDO')


def replay(arcade, game, work, forecast_limit, deadline):
    from arcengine import GameAction
    env = arcade.make(game['game_id'], seed=0)
    os.environ['ONLY_RESET_LEVELS'] = 'true'
    raw = env.observation_space
    total_levels = game['number_of_levels']
    if raw.win_levels != total_levels:
        raise ValueError('Level count differs from recording')
    completed = 0
    counts = [0]*total_levels
    step = 0
    digest = sha256()
    def state():
        grid = raw.frame[-1]
        return dict(current_frame=dict(ascii='\n'.join(''.join(COLORS[int(c)] for c in row) for row in grid),
                    shape=[len(grid),len(grid[0])], step=step,
                    level=max(1,min(total_levels,completed+1))))
    session = PredictionSession(work/f"{game['game_id']}.prediction.json", state)
    learned_deltas = {}
    features = None
    scope_level = None
    stats = Counter()
    on_changed = Counter()
    wrong_examples = []
    for i, record in enumerate(game['history']):
        if time.monotonic() >= deadline:
            raise TimeoutError('Replay diagnostic budget exhausted')
        before = state()['current_frame']
        action = record['action']
        command = dict(action=NAMES[action['id']])
        if command['action'] == 'MOUSE':
            command.update(row=action['data']['y'],col=action['data']['x'])
        signature = json.dumps(command,sort_keys=True)
        if scope_level != before['level']:
            learned_deltas = {}
            color_counts = Counter(before['ascii'].replace('\n',''))
            # Quantitative measurement selection only: up to eight colors other
            # than the most common one. No actor/goal interpretation is supplied.
            colors = [c for c,_ in color_counts.most_common()[1:9]]
            features = {kind+'_'+color:[kind,color] for color in colors for kind in ('bbox','count')}
            scope_level = before['level']
        measured = measure(before, features) if features else {}
        proposals = {'unchanged':measured, 'last_same_action_effect':None}
        prior = learned_deltas.get(signature)
        if prior:
            predicted = {}
            for key, value in measured.items():
                old_before, old_after = prior
                a, b = old_before[key], old_after[key]
                if type(value) is int and type(a) is int and type(b) is int:
                    predicted[key] = value+b-a
                elif all(isinstance(v,list) and len(v)==4 for v in (value,a,b)):
                    predicted[key] = [v+y-x for v,x,y in zip(value,a,b)]
            proposals['last_same_action_effect'] = predicted or None
        checked = bool(features) and i < forecast_limit and command['action'] != 'RESET'
        if checked:
            session.rpc(dict(operation='start', models=list(proposals), features=features,
                             question='Online naive pixel-feature proposal diagnostic'))
            session.rpc(dict(operation='forecast',probes={'recorded':dict(action=command,predictions=proposals)}))
            stats['frozen_probes'] += 1
        def handler(actions, **kwargs):
            nonlocal raw, completed, step
            assert actions == [command], 'Replay must not alter recorded actions'
            if completed < total_levels:
                counts[completed] += 1
            old_completed = completed
            raw = env.step(GameAction[action['id']],data=action['data'])
            if raw is None or not raw.frame:
                raise ValueError('Action returned no observation')
            completed = max(completed,int(raw.levels_completed))
            step += 1
            return dict(state=state(),action_result=dict(executed=True,
                level_completed=completed>old_completed,game_over=raw.state.name=='GAME_OVER',
                done=raw.state.name=='WIN'))
        session.wrap_action(handler)([command])
        after = state()['current_frame']
        digest.update(bytes(int(c) for row in raw.frame[-1] for c in row))
        if before['level'] == after['level'] and command['action'] != 'RESET':
            actual = measure(after, features) if features else {}
            if checked:
                result = session.status()['last_outcome']
                if result['checked']:
                    stats['checked_probes'] += 1
                    changed = measured != actual
                    stats['changed_feature_probes'] += int(changed)
                    for name, verdict in result['verdicts'].items():
                        stats[name+'/'+verdict['verdict']] += 1
                        if changed:
                            on_changed[name+'/'+verdict['verdict']] += 1
                    if result['needs_new_hypotheses']:
                        stats['all_supplied_hypotheses_refuted'] += 1
                        if len(wrong_examples)<2:
                            wrong_examples.append(dict(before_step=i,action=command,outcome=result))
                else:
                    stats['boundary_or_unavailable_probes'] += 1
            learned_deltas[signature] = (measured,actual)
        elif checked:
            stats['boundary_or_unavailable_probes'] += 1
    parity = counts == game['actions_per_level'] and completed == game['levels_completed']
    return dict(game_id=game['game_id'],actions_replayed=step,parity=parity,
                completed_levels=completed,stats=dict(stats),changed_feature_stats=dict(on_changed),
                absent_true_rule_examples=wrong_examples,observation_sha256=digest.hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--forecast-actions',type=int,default=64)
    parser.add_argument('--seconds',type=int,default=600)
    parser.add_argument('--output-directory',type=Path,default=Path('reports/research/prediction-real-replay-v2'))
    args = parser.parse_args()
    from arc_agi import Arcade, OperationMode
    source = ROOT/'reports/kaggle/general-learner-v1/benchmark.json'
    benchmark = json.loads(source.read_text(encoding='utf-8'))
    output = (ROOT/args.output_directory).resolve()
    if not output.is_relative_to(ROOT/'reports/research'):
        raise ValueError('Replay evidence must remain in reports/research')
    output.mkdir(parents=True,exist_ok=True)
    work = ROOT/'.tmp'/('prediction-replay-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    work.mkdir(parents=True)
    logger = logging.getLogger('prediction-real-replay')
    logger.setLevel(logging.ERROR)
    arcade = Arcade(operation_mode=OperationMode.OFFLINE,logger=logger)
    deadline = time.monotonic()+args.seconds
    results = []
    stats = Counter()
    for game in benchmark['game_runs']:
        result = replay(arcade,game,work,args.forecast_actions,deadline)
        results.append(result)
        stats.update(result['stats'])
        report = dict(checked_at=datetime.now(timezone.utc).isoformat(),
            source_sha256=sha256(source.read_bytes()).hexdigest(),
            source_files={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in
                ('hydra/prediction_host.py','hydra/prediction_ledger.py','scripts/audit_prediction_replay.py')},
            forecast_actions_per_game=args.forecast_actions,
            games_expected=len(benchmark['game_runs']),games_replayed=len(results),
            parity_games=sum(r['parity'] for r in results),
            actions_replayed=sum(r['actions_replayed'] for r in results),stats=dict(stats),per_game=results,
            boundary='Frozen recorded actions; no new policy or model inference. Proposals use only past public observations and may all be wrong. Matching selected pixel features is not mechanics/goal correctness, action utility, gameplay improvement or an official score. Aggregate replay parity does not establish original pixel equality.')
        (output/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(game=result['game_id'],parity=result['parity'],stats=result['stats'])),flush=True)


if __name__ == '__main__':
    main()
