"""Retrospective oracle over fixed public trajectory prefixes, never a policy.

Costs and rewards use future recorded completions. This is deliberately NOT
deployable scheduling logic, an achievable counterfactual, or a hidden estimate.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts.audit_general_run import score


def solve(groups, budget, unit, rounding):
    """Multiple-choice prefix allocation with conservative rounding bounds."""
    if rounding not in ('ceil','floor') or budget < 0 or unit <= 0:
        raise ValueError('Use a nonnegative budget, positive unit and ceil/floor')
    capacity = budget//unit
    previous = np.full(capacity+1,-np.inf)
    previous[0] = 0
    choices = []
    bins = []
    for group in groups:
        costs = [(g['tokens']+unit-1)//unit if rounding == 'ceil' else g['tokens']//unit for g in group]
        bins.append(costs)
        current = np.full(capacity+1,-np.inf)
        selected = np.full(capacity+1,-1,dtype=np.int16)
        for index,(option,cost) in enumerate(zip(group,costs)):
            if cost > capacity:
                continue
            candidates = previous[:capacity-cost+1]+option['score']
            target = current[cost:]
            better = candidates > target
            target[better] = candidates[better]
            selected[cost:][better] = index
        choices.append(selected)
        previous = current
    remaining = int(np.argmax(previous))
    value = float(previous[remaining])
    allocation = []
    for index in range(len(groups)-1,-1,-1):
        choice = int(choices[index][remaining])
        if choice < 0:
            raise ValueError('No feasible prefix allocation')
        allocation.append(groups[index][choice])
        remaining -= bins[index][choice]
    allocation.reverse()
    return dict(score_sum=value,actual_tokens=sum(a['tokens'] for a in allocation),allocation=allocation)


def audit(path,unit=500):
    raw = json.loads(path.read_text(encoding='utf-8'))
    groups = []
    completion_cost = 0
    actual_score = 0.0
    for game in raw['game_runs']:
        if sum(game['actions_per_level']) != len(game['history']):
            raise ValueError('Action-count mismatch')
        options = [dict(game=game['game_id'],levels=0,tokens=0,score=0.0)]
        position = cost = 0
        for level,n in enumerate(game['actions_per_level'][:game['levels_completed']],1):
            cost += sum(a['generated_tokens'] for a in game['history'][position:position+n])
            position += n
            options.append(dict(game=game['game_id'],levels=level,tokens=cost,
                score=score(game['actions_per_level'],game['base_actions_per_level'],level)))
        if abs(options[-1]['score']-game['final_score'])>1e-8:
            raise ValueError('Prefix scoring does not reproduce final score')
        completion_cost += cost
        actual_score += game['final_score']
        groups.append(options)
    total = sum(sum(a['generated_tokens'] for a in g['history'])+g['final_generated_tokens'] for g in raw['game_runs'])
    start = datetime.fromisoformat(raw['start_time'])
    checkpoint = 7200
    checkpoint_tokens = checkpoint_score = 0
    for game in raw['game_runs']:
        offset = (datetime.fromisoformat(game['started_at'])-start).total_seconds()
        selected = [a for a in game['history'] if offset+a['wallclock_seconds'] <= checkpoint]
        checkpoint_tokens += sum(a['generated_tokens'] for a in selected)
        if offset+game['final_wallclock_seconds'] <= checkpoint:
            checkpoint_tokens += game['final_generated_tokens']
        position = levels = 0
        for n in game['actions_per_level'][:game['levels_completed']]:
            position += n
            levels += int(position <= len(selected))
        checkpoint_score += score(game['actions_per_level'],game['base_actions_per_level'],levels)
    budgets = sorted(set([1000000,2000000,checkpoint_tokens,8000000,completion_cost,total]))
    comparisons = []
    for budget in budgets:
        feasible = solve(groups,budget,unit,'ceil')
        optimistic = solve(groups,budget,unit,'floor')
        if feasible['actual_tokens'] > budget:
            raise ValueError('Conservative allocation exceeded actual token budget')
        comparisons.append(dict(token_budget=budget,
            fixed_trace_oracle_lower=feasible['score_sum']/len(groups),
            fixed_trace_oracle_upper=optimistic['score_sum']/len(groups),
            feasible_prefix_tokens=feasible['actual_tokens'],feasible_prefix_allocation=feasible['allocation']))
    return dict(checked_at=datetime.now(timezone.utc).isoformat(),source_sha256=sha256(path.read_bytes()).hexdigest(),
        cost_rounding_unit=unit,games=len(groups),recorded_generation_tokens=total,
        recorded_final_score=actual_score/len(groups),tokens_through_last_observed_completion=completion_cost,
        observed_two_hour_tokens=checkpoint_tokens,observed_two_hour_score=checkpoint_score/len(groups),
        comparisons=comparisons,
        boundary='Retrospective perfect-future-information oracle over each fixed recorded trajectory prefix. Exact multiple-choice prefix optimization is bracketed by conservative ceil and optimistic floor token rounding. No newly solved level or improved action sequence exists in the choices. Pausing/resuming is assumed free, and real policies may change trajectories, cache costs, tokens, learning and outcomes. Generation charges omit some unfinished computation. These bounds quantify fixed-trace opportunities only; they are neither achievable scheduling scores nor bounds/estimates of a new policy or official hidden performance. Human baseline values are used only in this offline researcher audit, never supplied to the agent.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('benchmark',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = audit(args.benchmark)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    summary = {k:v for k,v in report.items() if k!='comparisons'}
    summary['comparisons'] = [{k:v for k,v in row.items() if k!='feasible_prefix_allocation'} for row in report['comparisons']]
    print(json.dumps(summary,indent=2))
