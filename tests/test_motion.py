import numpy as np
from hydra.motion import MotionReasoner
from hydra.perception import components


class RenderedMovement:
    """Test fixture exposes only rendered grids to the learner."""
    def __init__(self):
        self.position = (4, 4)
        self.vectors = {1: (2, 0), 2: (-2, 0), 3: (0, 2), 4: (0, -2)}
    def render(self):
        grid = np.ones((24, 24), dtype=np.int16)
        grid[[0, -1], :] = 4
        grid[:, [0, -1]] = 4
        grid[4:15, 10:12] = 4
        grid[16:18, 16:18] = 8
        x, y = self.position
        grid[y:y+2, x:x+2] = 9
        return grid
    def step(self, action):
        dx, dy = self.vectors[action]
        x, y = self.position
        grid = self.render()
        patch = grid[y+dy:y+dy+2, x+dx:x+dx+2]
        if patch.shape == (2, 2) and np.all(patch != 4):
            self.position = x+dx, y+dy


def observe(reasoner, env):
    grid = env.render()
    objects = components(grid, describe=True)
    reasoner.observe(grid, objects)
    return grid, objects


def test_infers_nonstandard_controls_and_navigates_to_contact_hypothesis():
    env = RenderedMovement()
    reasoner = MotionReasoner()
    observe(reasoner, env)
    for action in (1, 3, 2, 4, 1, 3, 2, 4):
        reasoner.last_action = (action, None, None)
        env.step(action)
        observe(reasoner, env)
    assert reasoner.selected is not None
    assert reasoner.vectors() == env.vectors
    for _ in range(60):
        grid, objects = observe(reasoner, env)
        action = reasoner.choose(grid, objects, [1, 2, 3, 4])
        if action is None:
            break
        reasoner.last_action = action
        env.step(action[0])
        observe(reasoner, env)
    assert env.position == (16, 16)
    assert reasoner.stats["contact_experiments"] >= 1
    assert reasoner.stats["motion_matches"] >= 5


def test_no_navigation_without_observed_control_and_terrain():
    reasoner = MotionReasoner()
    env = RenderedMovement()
    grid, objects = observe(reasoner, env)
    assert reasoner.choose(grid, objects, [1, 2, 3, 4]) is None
    reasoner.reset_level()
    assert reasoner.previous_grid is None
    assert not reasoner.blocked
