import random
import numpy as np
from hydra.cyclic import CyclicReasoner, modular_space


def test_prime_field_solution_and_unreachable_system():
    matrix = np.array([[1, 1, 0], [0, 1, 1]])
    rhs = np.array([2, 1])
    particular, basis = modular_space(matrix, rhs, 3)
    assert np.array_equal(matrix @ particular % 3, rhs)
    assert np.all(matrix @ basis.T % 3 == 0)
    assert modular_space(np.zeros((1, 2)), np.array([1]), 3) is None


def test_learns_three_color_cycle_and_validates_a_plan(monkeypatch):
    from hydra import cyclic
    monkeypatch.setattr(cyclic, "relational_constraints", lambda *a: [("test", [{0}, {1}, {2}])])
    group = [{"bbox":(2+5*i, 2, 4+5*i, 4), "point":(3+5*i, 3)} for i in range(3)]
    state = [9, 9, 9]
    def render():
        grid = np.zeros((12, 24), dtype=np.int16)
        for cell, color in zip(group, state):
            x0, y0, x1, y1 = cell["bbox"]
            grid[y0:y1+1, x0:x1+1] = color
        return grid
    next_color = {9:8, 8:12, 12:9}
    learner = CyclicReasoner({"test":1})
    candidates = [(6, *cell["point"]) for cell in group]
    def execute(action):
        before = render()
        index = candidates.index(action)
        state[index] = next_color[state[index]]
        learner.observe(before, render(), [group], action)
    for _ in range(3):
        execute(candidates[0])
    assert learner.cycle() == (8, 12, 9)
    rng = random.Random(0)
    for _ in range(16):
        action = learner.choose(render(), candidates, rng)
        if action is None:
            break
        execute(action)
        if state == [8, 12, 9]:
            break
    assert state == [8, 12, 9]
    assert learner.stats["cyclic_plan_actions"] >= 1
    assert learner.stats["cyclic_matches"] == learner.stats["cyclic_predictions"]
