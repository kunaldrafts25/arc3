from types import SimpleNamespace
import numpy as np
from hydra.perception import normalize, state_key, grid_diff, components
from hydra.model import TransitionMemory, bfs
from hydra.controller import Controller


def obs(grid, **kwargs):
    return SimpleNamespace(frame=[grid], levels_completed=0, state="active", available_actions=[1, 2], **kwargs)


def test_normalization_preserves_history_and_dimensions():
    observation = obs([[1, 2, 3], [4, 5, 6]])
    observation.frame.append([[7]])
    result = normalize(observation)
    assert [x.shape for x in result] == [(2, 3), (1, 1)]
    assert normalize(SimpleNamespace(frame=[])) == []
    assert normalize(SimpleNamespace(frame=[[[1], [1, 2]]])) == []


def test_hash_includes_shape_level_and_legal_actions():
    a, b = obs([[1, 2]]), obs([[1], [2]])
    assert state_key(a) != state_key(b)
    b = obs([[1, 2]])
    assert state_key(a) == state_key(b)
    b.levels_completed = 1
    assert state_key(a) != state_key(b)
    b.levels_completed, b.available_actions = 0, [3]
    assert state_key(a) != state_key(b)


def test_difference_and_connectivity():
    a = np.array([[1, 0], [0, 1]])
    assert grid_diff(a, a)["changed_cells"] == 0
    assert grid_diff(a, 1-a)["bbox"] == (0, 0, 1, 1)
    assert grid_diff(a, np.zeros((3, 3)))["shape_changed"]
    assert len(components(a, 4)) == 4
    assert len(components(a, 8)) == 2
    for obj in components(a):
        x, y = obj["point"]
        assert a[y, x] == obj["color"]


def test_transition_confidence_revoked_by_contradiction_and_bounded():
    m = TransitionMemory(capacity=2)
    m.record("a", (1,), "b")
    assert m.predict("a", (1,)) is None
    m.record("a", (1,), "b")
    assert m.predict("a", (1,)) == "b"
    m.record("a", (1,), "c")
    assert m.predict("a", (1,)) is None
    assert m.contradictions == 1
    m.record("x", (1,), "y")
    m.record("y", (1,), "z")
    assert len(m.edges) == 2


def test_bfs_shortest_path_cycles_and_budget():
    graph = {"a": [(1, "b"), (2, "d")], "b": [(3, "a"), (4, "c")], "d": [(5, "c")]}
    path = bfs("a", lambda s: graph.get(s, []), lambda s: s == "c")
    assert path == [1, 4]
    assert bfs("a", lambda s: graph.get(s, []), lambda s: s == "c", max_nodes=1) is None
    assert bfs("a", lambda s: graph.get(s, []), lambda s: s == "c", max_depth=1) is None
    assert bfs("a", lambda s: [], lambda s: s == "a") == []


def test_exploration_avoids_repeated_noop_and_reset_clears_pending():
    c = Controller(seed=7)
    candidates = [(1, None, None), (2, None, None)]
    c.observe("a")
    first = c.choose("a", candidates)
    c.observe("a")
    second = c.choose("a", candidates)
    assert second != first
    c.reset_level()
    c.observe("new")
    assert not c.memory.edges
    assert c.previous is None


def test_frontier_planner_routes_only_on_confirmed_edges():
    c = Controller(seed=0, policy="planning")
    a1, a2 = (1, None, None), (2, None, None)
    for _ in range(2):
        c.memory.record("a", a1, "b")
        c.memory.record("a", a2, "a")
    assert c.choose("a", [a1, a2]) == a1
    assert c.mode == "PLAN"
    c.observe("unexpected")
    assert c.stats["prediction_failures"] == 1
    assert c.memory.predict("a", a1) is None


def test_independent_rng_reproducibility():
    def trajectory(seed):
        c = Controller(seed)
        result = []
        for _ in range(10):
            c.observe("s")
            result.append(c.choose("s", [(1,), (2,), (3,)]))
        return result
    assert trajectory(42) == trajectory(42)


def test_click_coverage_survives_cosmetic_state_changes():
    c = Controller(seed=4, policy="coverage")
    candidates = [(6, 1, 1), (6, 20, 20), (6, 40, 40)]
    selected = []
    for state in ("frame1", "frame2", "frame3"):
        c.observe(state)
        selected.append(c.choose(state, candidates))
    assert len(set(selected)) == 3


def test_novelty_ablation_cannot_consult_or_train_transition_model():
    c = Controller(seed=0, policy="novelty")
    def forbidden(*args):
        raise AssertionError("novelty ablation accessed transition model")
    c.memory.predict = c.memory.record = forbidden
    for state in ("a", "a", "b", "a"):
        c.observe(state)
        c.choose(state, [(1,), (2,)])
    assert len(c.memory.history) == 3
