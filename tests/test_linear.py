from hydra.linear import xor_plan


def apply(actions, plan):
    result = 0
    for action in plan:
        result ^= actions[action]
    return result


def test_solves_multicell_xor_effects_and_rejects_unreachable_goals():
    actions = {"a": 0b011, "b": 0b110, "c": 0b001}
    plan = xor_plan(actions, 0b101, 3)
    assert apply(actions, plan) == 0b101
    assert len(plan) == 2
    assert xor_plan({"a": 0b11}, 0b01, 2) is None


def test_nullspace_search_removes_redundant_actions():
    actions = {"a": 0b01, "b": 0b10, "c": 0b11}
    plan = xor_plan(actions, 0b11, 2)
    assert plan == ["c"]
    assert xor_plan(actions, 0, 2) == []
