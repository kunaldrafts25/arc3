import random
import numpy as np
from hydra.clicks import ClickReasoner, tile_groups, read_bits, expand_marked_tiles
from hydra.perception import components


def puzzle(state):
    grid = np.zeros((32, 48), dtype=np.int16)
    for offset, bits in ((2, 0b1010), (28, state)):
        for index, (x, y) in enumerate(((0, 0), (5, 0), (0, 5), (5, 5))):
            grid[8+y:11+y, offset+x:offset+x+3] = 9 if bits & (1 << index) else 8
    return grid


def parts(grid):
    objects = components(grid, describe=True)
    candidates = [(6, *obj["point"]) for obj in objects if obj["area"] == 9]
    return objects, candidates


def test_discovers_binary_click_effects_and_tests_reference_goal():
    reasoner = ClickReasoner()
    rng = random.Random(0)
    state = 0
    grid = puzzle(state)
    objects, candidates = parts(grid)
    reasoner.observe(grid, objects)
    groups = tile_groups(objects)
    assert len(groups) == 2
    active = next(g for g in groups if min(c["bbox"][0] for c in g) > 20)
    # One observed, successful intervention identifies which copy is interactive.
    reasoner.last_action = (6, *active[0]["point"])
    state ^= 1
    grid = puzzle(state)
    objects, candidates = parts(grid)
    reasoner.observe(grid, objects)
    assert reasoner.active is not None
    assert reasoner.palette == (8, 9)
    visited = {state}
    for _ in range(24):
        action = reasoner.choose(grid, objects, candidates, rng)
        assert action in candidates
        point = action[1:]
        index = next(i for i, cell in enumerate(active) if cell["point"] == point)
        reasoner.last_action = action
        state ^= 1 << index
        visited.add(state)
        grid = puzzle(state)
        objects, candidates = parts(grid)
        reasoner.observe(grid, objects)
        if 0b1010 in visited and reasoner.stats["binary_plan_actions"] >= 1:
            break
    assert 0b1010 in visited
    assert reasoner.stats["binary_plan_actions"] >= 1
    assert reasoner.stats["binary_matches"] >= 1


def test_nonbinary_or_nonuniform_patches_are_rejected():
    grid = puzzle(0)
    objects, _ = parts(grid)
    group = tile_groups(objects)[0]
    cell = group[0]
    x, y = cell["point"]
    grid[y, x] = 3
    assert read_bits(grid, group, (8, 9)) is None


def test_episode_memory_requires_identical_initial_board():
    reasoner = ClickReasoner()
    grid = puzzle(0)
    objects, _ = parts(grid)
    reasoner.observe(grid, objects)
    reasoner.rules[(29, 9)] = {1: 2}
    reasoner.visited = {0, 1, 3}
    reasoner.reset_episode()
    reasoner.observe(grid, objects)
    assert reasoner.rules[(29, 9)] == {1: 2}
    assert reasoner.visited == {0, 1, 3}
    reasoner.reset_episode()
    different = puzzle(4)
    objects, _ = parts(different)
    reasoner.observe(different, objects)
    assert not reasoner.rules
    assert not reasoner.visited
    assert reasoner.stats["reset_models_discarded"] == 1


def test_marked_cell_state_is_recovered_without_treating_glyphs_as_cells():
    grid = np.full((32,32),4,dtype=np.int16)
    cells = []
    for row in range(5):
        for col in range(3):
            x,y=2+5*col,2+5*row
            if (col,row) in ((1,1),(1,3)):
                grid[y:y+3,x:x+3]=0
                grid[y+1,x+1]=14
                grid[y,x]=2
            else:
                grid[y:y+3,x:x+3]=14
                cells.append(dict(color=14,area=9,point=(x+1,y+1),bbox=(x,y,x+2,y+2)))
    marked=cells.pop(5)
    x,y=marked["bbox"][:2]
    grid[y,x]=6
    expanded=expand_marked_tiles(grid,cells,(14,15),{0,2})
    assert len(expanded)==13
    assert any(c.get("marker_colors")== (6,) for c in expanded)
    assert read_bits(grid,expanded,(14,15))==0
    grid[y:y+3,x:x+3][grid[y:y+3,x:x+3]==14]=15
    assert read_bits(grid,expanded,(14,15))!=0


def test_fully_marked_lattice_is_discovered_and_every_cell_is_proposed():
    grid = np.full((32, 32), 4, dtype=np.int16)
    for y in (2, 10, 18):
        for x in (2, 10, 18):
            grid[y:y+6, x:x+6] = 11
            grid[y:y+2, x:x+2] = 6
    reasoner = ClickReasoner()
    reasoner.glyph_colors = {0, 2, 4}
    objects = components(grid, describe=True)
    reasoner.observe(grid, objects)
    assert len(reasoner.previous_groups) == 1
    group = reasoner.previous_groups[0]
    assert len(group) == 9
    assert len(reasoner.proposals()) == 9
    assert all(c['marker_colors'] == (6,) for c in group)
    reasoner.last_action = reasoner.proposals()[0]
    changed = grid.copy()
    x0, y0, x1, y1 = group[0]['bbox']
    patch = changed[y0:y1+1, x0:x1+1]
    patch[patch == 11] = 14
    reasoner.observe(changed, components(changed, describe=True))
    assert reasoner.palette == (11, 14)
    assert read_bits(changed, reasoner.active, reasoner.palette) == 1
