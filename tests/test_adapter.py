import random
import time
from types import SimpleNamespace
import numpy as np
import pytest
from arcengine import FrameData, FrameDataRaw, GameAction, GameState
from agent.my_agent import MyAgent, legal_candidates, validate_action


def frame(state=GameState.NOT_FINISHED, level=0, actions=None):
    return FrameData(game_id="test", state=state, levels_completed=level,
                     available_actions=[1, 2, 3, 4, 5, 6, 7] if actions is None else actions,
                     frame=[[[0, 1], [1, 0]]])


def agent(**kwargs):
    return MyAgent(card_id="test", game_id="test", agent_name="hydra-test",
                   ROOT_URL="http://localhost", record=False, arc_env=kwargs.pop("env", None), **kwargs)


def test_all_advertised_action_types_and_invalid_coordinates():
    observation = frame()
    candidates = legal_candidates(observation, random.Random(0))
    assert {c[0] for c in candidates} == set(range(1, 8))
    for choice in candidates:
        action, payload = validate_action(choice, observation)
        assert isinstance(action, GameAction)
        assert action.validate_data(payload)
    with pytest.raises(ValueError):
        validate_action((2, None, None), frame(actions=[1]))
    with pytest.raises(ValueError):
        validate_action((6, -1, 64), observation)
    with pytest.raises(ValueError):
        validate_action((6, None, 0), observation)


def test_lifecycle_memory_resets_and_caps():
    a = agent(hydra_policy="memory")
    f = frame(GameState.NOT_PLAYED)
    assert a.choose_action([f], f) is GameAction.RESET
    f = frame(actions=[1])
    a.choose_action([f], f)
    a.choose_action([f], f)
    assert a.controller.memory.edges
    f = frame(level=1, actions=[1])
    a.choose_action([f], f)
    assert not a.controller.memory.edges
    f = frame(GameState.GAME_OVER, level=1)
    assert a.choose_action([f], f) is GameAction.RESET
    assert a.controller.previous is None
    assert a.is_done([], frame(GameState.WIN))
    a.action_counter = a.MAX_ACTIONS
    assert a.is_done([], frame())
    a.action_counter = 0
    a.started = time.monotonic() - a.MAX_SECONDS - 1
    assert a.is_done([], frame())


def test_full_reset_empty_frames_and_unknown_actions():
    a = agent()
    f = frame(actions=[1, 999])
    f.frame = []
    assert a.choose_action([f], f) is GameAction.ACTION1
    f.full_reset = True
    a.choose_action([f], f)
    assert not a.controller.memory.edges
    f.available_actions = []
    assert a.choose_action([f], f) is GameAction.RESET
    assert not a.errors


def test_per_agent_payload_ignores_mutated_shared_enum():
    class Capture:
        def step(self, action, data, reasoning):
            self.data = data.copy()
            raw = FrameDataRaw(game_id="test", available_actions=[6])
            raw.frame = [np.zeros((64, 64), dtype=np.int16)]
            return raw
    first_env, second_env = Capture(), Capture()
    first, second = agent(env=first_env), agent(env=second_env)
    first._payload, second._payload = {"x": 2, "y": 3}, {"x": 61, "y": 60}
    GameAction.ACTION6.set_data(second._payload)
    first.do_action_request(GameAction.ACTION6)
    second.do_action_request(GameAction.ACTION6)
    assert first_env.data["x"] == 2
    assert second_env.data["x"] == 61


def test_separate_games_can_submit_concurrently():
    from concurrent.futures import ThreadPoolExecutor
    import threading
    barrier = threading.Barrier(2)
    class ParallelEnvironment:
        def step(self, action, data, reasoning):
            barrier.wait(timeout=3)
            self.x = data["x"]
            return FrameDataRaw(game_id="test", available_actions=[6])
    envs = [ParallelEnvironment(), ParallelEnvironment()]
    agents = [agent(env=env) for env in envs]
    for index, a in enumerate(agents):
        a._payload = {"x": index, "y": 0}
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda a: a.do_action_request(GameAction.ACTION6), agents))
    assert [env.x for env in envs] == [0, 1]


def test_environment_failure_is_recorded_without_crashing_other_games():
    a = agent(env=SimpleNamespace(observation_space=None))
    a.main()
    assert a.errors == ["ValueError: Received None frame data from environment"]
    assert a.action_counter == 0


def test_waiting_for_other_agents_does_not_exhaust_play_budget():
    class Environment:
        def __init__(self):
            self.observation_space = FrameDataRaw(game_id="test", state=GameState.NOT_FINISHED,
                                                 available_actions=[1])
            self.observation_space.frame = [np.zeros((64, 64), dtype=np.int16)]
        def step(self, action, data, reasoning):
            return self.observation_space
    a = agent(env=Environment())
    a.started = time.monotonic() - a.MAX_SECONDS - 1
    a.MAX_ACTIONS = 2
    a.main()
    assert a.action_counter == 2
    assert not a.errors


def test_official_loop_through_simulated_reset_level_transition_and_win():
    class Lifecycle:
        def __init__(self):
            self.count = 0
            self.observation_space = FrameDataRaw(game_id="test", state=GameState.NOT_PLAYED)

        def step(self, action, data, reasoning):
            self.count += 1
            if self.count == 1:
                assert action is GameAction.RESET
            else:
                assert action is GameAction.ACTION1
            self.observation_space = FrameDataRaw(
                game_id="test", available_actions=[1], levels_completed=self.count-1,
                win_levels=2, full_reset=self.count == 1,
                state=GameState.WIN if self.count == 3 else GameState.NOT_FINISHED)
            self.observation_space.frame = [np.zeros((64, 64), dtype=np.int16)]
            return self.observation_space
    env = Lifecycle()
    a = agent(env=env)
    a.main()
    assert a.action_counter == 3
    assert a.frames[-1].state is GameState.WIN
    assert a.frames[-1].levels_completed == 2
    assert a.controller.stats["resets"] == 1


def test_official_loop_with_real_cached_public_engine():
    from arc_agi import Arcade, OperationMode
    arcade = Arcade(operation_mode=OperationMode.OFFLINE)
    games = arcade.get_environments()
    if not games:
        pytest.skip("Public environment cache absent; bootstrap using scripts/benchmark.py")
    game = games[0].game_id
    env = arcade.make(game, seed=0)
    assert env is not None
    a = MyAgent(card_id="test", game_id=game, agent_name="integration", ROOT_URL="http://localhost",
                record=False, arc_env=env)
    a.MAX_ACTIONS = 12
    a.main()
    assert a.action_counter <= 12
    assert len(a.frames) > 1
    assert not a.errors
    for observed in a.frames[1:]:
        assert isinstance(observed, FrameData)
