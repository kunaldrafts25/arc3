import numpy as np
from hydra.clicks import tile_groups
from hydra.perception import components
from hydra.visual_goals import infer_visual_goals


def test_learns_glyph_color_relation_from_examples_with_different_palettes():
    grid = np.full((64, 64), 5, dtype=np.int16)
    patterns = [0b10110010, 0b01101001, 0b11000101]
    positions = [(x, y) for y in (-1, 0, 1) for x in (-1, 0, 1) if (x, y) != (0, 0)]
    for panel, (origin, bits) in enumerate(zip(((3, 3), (35, 3), (35, 35)), patterns)):
        bx, by = origin
        center_color = 10 if panel == 1 else 14
        for index, (dx, dy) in enumerate(positions):
            x, y = bx+(dx+1)*6, by+(dy+1)*6
            color = 14 if bits & (1 << index) else 10
            grid[y:y+4, x:x+4] = color if panel < 2 else 10
            glyph = 0 if color == center_color else 3
            grid[by+7+dy, bx+7+dx] = glyph
        grid[by+7, bx+7] = center_color
    groups = tile_groups(components(grid, describe=True))
    active = next(g for g in groups if min(c["bbox"][1] for c in g) > 30)
    references = [g for g in groups if g is not active]
    hypotheses = infer_visual_goals(grid, active, references, (10, 14))
    assert patterns[2] in hypotheses
    assert len(hypotheses) == 1


def test_no_goal_program_from_one_example():
    assert infer_visual_goals(np.zeros((16, 16)), [], [], (8, 9)) == {}
