from itertools import product

from scripts.audit_arc3_allocation_bound import solve


def test_later_level_reward_requires_its_entire_observed_prefix_cost():
    groups = [[dict(tokens=0,score=0),dict(tokens=3,score=10),dict(tokens=5,score=100)],
              [dict(tokens=0,score=0),dict(tokens=3,score=50)]]
    result = solve(groups,6,1,'ceil')
    assert result['score_sum'] == 100 and result['actual_tokens'] == 5


def test_rounding_brackets_exact_prefix_oracle_and_lower_allocation_stays_feasible():
    groups = [[dict(tokens=0,score=0),dict(tokens=3,score=10),dict(tokens=5,score=100)],
              [dict(tokens=0,score=0),dict(tokens=3,score=50)]]
    for budget in range(9):
        exact = max(sum(a['score'] for a in allocation) for allocation in product(*groups)
                    if sum(a['tokens'] for a in allocation)<=budget)
        lower = solve(groups,budget,2,'ceil')
        upper = solve(groups,budget,2,'floor')
        assert lower['actual_tokens'] <= budget
        assert lower['score_sum'] <= exact <= upper['score_sum']
