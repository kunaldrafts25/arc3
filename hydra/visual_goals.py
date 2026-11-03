"""Infer small visual programs from repeated, observed example panels.

Programs map a small central glyph to surrounding tile colors. No palette
meaning, game identifier, target pattern or action sequence is supplied.
"""
import numpy as np
import re
from math import gcd
from functools import reduce


def observed_panels(group, grid_shape):
    """Missing cell positions with visible neighbors, including edge panels."""
    cells = {(c["bbox"][0],c["bbox"][1]):i for i,c in enumerate(group)}
    xs=sorted({x for x,_ in cells})
    ys=sorted({y for _,y in cells})
    if len(xs)<2 or len(ys)<2:
        return []
    width=group[0]["bbox"][2]-group[0]["bbox"][0]+1
    height=group[0]["bbox"][3]-group[0]["bbox"][1]+1
    sx=reduce(gcd,[b-a for a,b in zip(xs,xs[1:])])
    sy=reduce(gcd,[b-a for a,b in zip(ys,ys[1:])])
    if sx<width or sy<height:
        return []
    result=[]
    for y in range(ys[0]-sy,ys[-1]+sy+1,sy):
        for x in range(xs[0]-sx,xs[-1]+sx+1,sx):
            if (x,y) in cells or x<0 or y<0 or x+width>grid_shape[1] or y+height>grid_shape[0]:
                continue
            pairs=[((dx,dy),cells[(x+dx*sx,y+dy*sy)]) for dy in (-1,0,1) for dx in (-1,0,1)
                   if (dx,dy)!=(0,0) and (x+dx*sx,y+dy*sy) in cells]
            if len(pairs)>=2:
                result.append((x,y,[p for p,_ in pairs],[i for _,i in pairs]))
    return result


def lattice(group):
    xs = sorted({c["bbox"][0] for c in group})
    ys = sorted({c["bbox"][1] for c in group})
    if len(group) != 8 or len(xs) != 3 or len(ys) != 3:
        return None
    coordinates = [(xs.index(c["bbox"][0])-1, ys.index(c["bbox"][1])-1) for c in group]
    if set(coordinates) != {(x, y) for y in (-1, 0, 1) for x in (-1, 0, 1) if (x, y) != (0, 0)}:
        return None
    x0, y0, x1, y1 = group[0]["bbox"]
    return xs[1], ys[1], x1-x0+1, y1-y0+1, coordinates


def visual_key(grid, active, references, palette):
    result = [palette]
    for group in [active]+references:
        layout = lattice(group)
        if layout is None:
            return None
        x, y, width, height, _ = layout
        result.append(grid[y:y+height, x:x+width].tobytes())
        if group is not active:
            result.append(tuple(int(grid[c["bbox"][1], c["bbox"][0]]) for c in group))
    return tuple(result)


def infer_visual_goals(grid, active, references, palette):
    target_layout = lattice(active)
    examples = [(group, lattice(group)) for group in references]
    examples = [(g, layout) for g, layout in examples if layout is not None]
    if target_layout is None or len(examples) < 2:
        return {}
    _, _, width, height, _ = target_layout
    if any(layout[2:4] != (width, height) for _, layout in examples):
        return {}
    outputs = {tuple(c["color"] for c in group) for group, _ in examples}
    if len(outputs) < 2:
        return {}
    goals = {}
    best_support = 0
    offsets_x = sorted({(width-1)//2, width//2})
    offsets_y = sorted({(height-1)//2, height//2})
    for step in range(1, max(1, min(width, height)//2)+1):
        for ox in offsets_x:
            for oy in offsets_y:
                examples_samples = []
                for group, layout in examples:
                    x, y, w, h, positions = layout
                    cx, cy = x+ox, y+oy
                    if any(not (x <= cx+dx*step < x+w and y <= cy+dy*step < y+h) for dx, dy in positions):
                        continue
                    center = int(grid[cy, cx])
                    if center not in palette:
                        continue
                    examples_samples.append([(int(grid[cy+dy*step, cx+dx*step]), center, cell["color"])
                                             for cell, (dx, dy) in zip(group, positions)])
                if len(examples_samples) < 2:
                    continue
                for special in {pixel for samples in examples_samples for pixel, _, _ in samples}:
                    for polarity in (False, True):
                        def predict(pixel, center):
                            same = (pixel == special) != polarity
                            return center if same else palette[1-palette.index(center)]
                        supporting = [samples for samples in examples_samples if all(predict(p, q) == t for p, q, t in samples)]
                        if len(supporting) < 2 or len({tuple(t for _, _, t in s) for s in supporting}) < 2:
                            continue
                        if len(supporting) < best_support:
                            continue
                        x, y, w, h, positions = target_layout
                        cx, cy = x+ox, y+oy
                        center = int(grid[cy, cx])
                        if center not in palette:
                            continue
                        if any(not (x <= cx+dx*step < x+w and y <= cy+dy*step < y+h) for dx, dy in positions):
                            continue
                        predicted = [predict(int(grid[cy+dy*step, cx+dx*step]), center) for dx, dy in positions]
                        bits = sum((color == palette[1]) << i for i, color in enumerate(predicted))
                        label = f"glyph:size={width},{height}:step={step}:offset={ox},{oy}:special={special}:invert={int(polarity)}"
                        if len(supporting) > best_support:
                            goals.clear()
                            best_support = len(supporting)
                        goals.setdefault(bits, []).append(label)
    return goals


def transfer_goals(grid, group, palette, successful_labels):
    """Apply within-game visual programs to overlapping observed panels."""
    cells = {(cell["bbox"][0], cell["bbox"][1]):(i, cell) for i, cell in enumerate(group)}
    xs = sorted({p[0] for p in cells})
    ys = sorted({p[1] for p in cells})
    if len(xs) < 3 or len(ys) < 3:
        return {}
    panels = []
    for xi in range(1, len(xs)-1):
        for yi in range(1, len(ys)-1):
            if (xs[xi], ys[yi]) in cells:
                continue
            if xs[xi]-xs[xi-1] != xs[xi+1]-xs[xi] or ys[yi]-ys[yi-1] != ys[yi+1]-ys[yi]:
                continue
            positions = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx, dy) != (0, 0)]
            if all((xs[xi+dx], ys[yi+dy]) in cells for dx, dy in positions):
                panels.append((xs[xi], ys[yi], positions, [(cells[(xs[xi+dx], ys[yi+dy])][0]) for dx, dy in positions]))
    panels = observed_panels(group, grid.shape)
    if not panels:
        return {}
    width = group[0]["bbox"][2]-group[0]["bbox"][0]+1
    height = group[0]["bbox"][3]-group[0]["bbox"][1]+1
    goals = {}
    pattern = r"glyph:size=(\d+),(\d+):step=(\d+):offset=(\d+),(\d+):special=(\d+):invert=(\d+)"
    for label, support in successful_labels.items():
        match = re.fullmatch(pattern, label)
        if not support or match is None:
            continue
        ow, oh, step, ox, oy, special, polarity = map(int, match.groups())
        sx, sy = max(1, round(step*width/ow)), max(1, round(step*height/oh))
        nx, ny = round((ox+0.5)*width/ow-0.5), round((oy+0.5)*height/oh-0.5)
        assignments = {}
        consistent = True
        for x, y, positions, indices in panels:
            cx, cy = x+nx, y+ny
            if not (x <= cx < x+width and y <= cy < y+height):
                consistent = False
                break
            center = int(grid[cy, cx])
            if center not in palette or np.unique(grid[y:y+height,x:x+width]).size<2:
                continue
            for (dx, dy), index in zip(positions, indices):
                px, py = cx+dx*sx, cy+dy*sy
                if not (x <= px < x+width and y <= py < y+height):
                    consistent = False
                    break
                same = (int(grid[py, px]) == special) != bool(polarity)
                color = center if same else palette[1-palette.index(center)]
                if index in assignments and assignments[index] != color:
                    consistent = False
                    break
                assignments[index] = color
            if not consistent:
                break
        if consistent and len(assignments) == len(group):
            bits = sum((color == palette[1]) << index for index, color in assignments.items())
            goals.setdefault(bits, []).append(label)
    return goals


def relational_constraints(grid, group, palette, labels, require_coverage=False):
    """Transfer equality/inequality glyph programs to a larger color alphabet."""
    if len(palette) < 2:
        return []
    cells = {(c["bbox"][0], c["bbox"][1]):i for i, c in enumerate(group)}
    xs = sorted({x for x, _ in cells})
    ys = sorted({y for _, y in cells})
    width = group[0]["bbox"][2]-group[0]["bbox"][0]+1
    height = group[0]["bbox"][3]-group[0]["bbox"][1]+1
    panels = []
    positions = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx, dy) != (0, 0)]
    for xi in range(1, len(xs)-1):
        for yi in range(1, len(ys)-1):
            if (xs[xi], ys[yi]) in cells or xs[xi]-xs[xi-1] != xs[xi+1]-xs[xi] or ys[yi]-ys[yi-1] != ys[yi+1]-ys[yi]:
                continue
            if all((xs[xi+dx], ys[yi+dy]) in cells for dx, dy in positions):
                panels.append((xs[xi], ys[yi], [cells[(xs[xi+dx], ys[yi+dy])] for dx, dy in positions]))
    panels = observed_panels(group, grid.shape)
    result, seen = [], set()
    for label, support in labels.items():
        match = re.fullmatch(r"glyph:size=(\d+),(\d+):step=(\d+):offset=(\d+),(\d+):special=(\d+):invert=(\d+)", label)
        if not support or match is None:
            continue
        ow, oh, step, ox, oy, special, polarity = map(int, match.groups())
        sx, sy = max(1, round(step*width/ow)), max(1, round(step*height/oh))
        nx, ny = round((ox+0.5)*width/ow-0.5), round((oy+0.5)*height/oh-0.5)
        allowed = [set(range(len(palette))) for _ in group]
        covered = set()
        valid = True
        for x, y, panel_positions, indices in panels:
            cx, cy = x+nx, y+ny
            if not (x <= cx < x+width and y <= cy < y+height):
                valid = False
                break
            if int(grid[cy,cx]) not in palette or np.unique(grid[y:y+height,x:x+width]).size<2:
                continue
            center = palette.index(int(grid[cy, cx]))
            for (dx, dy), index in zip(panel_positions, indices):
                px, py = cx+dx*sx, cy+dy*sy
                if not (x <= px < x+width and y <= py < y+height):
                    valid = False
                    break
                same = (int(grid[py, px]) == special) != bool(polarity)
                allowed[index] &= {center} if same else set(range(len(palette)))-{center}
                covered.add(index)
        key = tuple(tuple(sorted(values)) for values in allowed)
        if valid and len(covered)>=2 and (not require_coverage or len(covered)==len(group)) and all(allowed) and key not in seen:
            result.append((label, allowed))
            seen.add(key)
    return result
