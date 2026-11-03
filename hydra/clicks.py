"""Learn click affordances and test goals in observed binary tile systems."""
from collections import Counter, deque
from itertools import combinations
import numpy as np
from .model import bfs
from .visual_goals import infer_visual_goals, visual_key, transfer_goals, relational_constraints
from .linear import xor_plan
from .cyclic import CyclicReasoner


def tile_groups(objects, grid=None, glyph_colors=()):
    """Connected regular-layout hypotheses from equal rectangular components."""
    families = {}
    for obj in objects:
        x0, y0, x1, y1 = obj["bbox"]
        width, height = x1-x0+1, y1-y0+1
        if not (3 <= width <= 12 and 3 <= height <= 12):
            continue
        cell = obj
        if obj["area"] != width*height:
            if grid is None or obj["area"] < width*height*0.75:
                continue
            patch = grid[y0:y1+1, x0:x1+1]
            extra = set(map(int, np.unique(patch)))-{obj["color"]}
            if (len(extra) != 1 or extra & set(glyph_colors)
                    or int(patch[height//2, width//2]) != obj["color"]):
                continue
            cell = dict(obj, marker_colors=tuple(extra))
        families.setdefault((width, height), []).append(cell)
    groups = []
    for (width, height), cells in families.items():
        remaining = set(range(len(cells)))
        while remaining:
            root = remaining.pop()
            queue, indices = [root], [root]
            while queue:
                index = queue.pop()
                ax, ay = cells[index]["bbox"][:2]
                neighbors = []
                for other in remaining:
                    bx, by = cells[other]["bbox"][:2]
                    if ((ay == by and 0 < abs(ax-bx) <= width*2+2)
                            or (ax == bx and 0 < abs(ay-by) <= height*2+2)):
                        neighbors.append(other)
                for other in neighbors:
                    remaining.remove(other)
                    queue.append(other)
                    indices.append(other)
            if 3 <= len(indices) <= 48:
                groups.append(sorted((cells[i] for i in indices), key=lambda c: (c["bbox"][1], c["bbox"][0])))
    return groups


def group_key(group):
    return tuple(cell["bbox"] for cell in group)


def read_bits(grid, group, palette):
    bits = 0
    for index, cell in enumerate(group):
        x0, y0, x1, y1 = cell["bbox"]
        patch = grid[y0:y1+1, x0:x1+1]
        if not patch.size:
            return None
        value = int(patch[patch.shape[0]//2, patch.shape[1]//2])
        markers = cell.get("marker_colors", ())
        if value not in palette or np.any(~np.isin(patch, (value,)+tuple(markers))):
            return None
        bits |= (value == palette[1]) << index
    return bits


def expand_marked_tiles(grid, group, palette, glyph_colors):
    """Complete a regular cell lattice using observed state-plus-marker patches."""
    if not group or not glyph_colors:
        return group
    cells = {(c["bbox"][0], c["bbox"][1]):c for c in group}
    xs = sorted({x for x, _ in cells})
    ys = sorted({y for _, y in cells})
    width = group[0]["bbox"][2]-group[0]["bbox"][0]+1
    height = group[0]["bbox"][3]-group[0]["bbox"][1]+1
    for x in xs:
        for y in ys:
            if (x, y) in cells:
                continue
            patch = grid[y:y+height, x:x+width]
            color = int(patch[height//2, width//2])
            extra = set(map(int, np.unique(patch)))-set(palette)
            if color in palette and len(extra) == 1 and not (extra & glyph_colors) and np.all(np.isin(patch, (color,)+tuple(extra))):
                cells[x, y] = dict(color=color, area=width*height, point=(x+width//2,y+height//2),
                                  bbox=(x,y,x+width-1,y+height-1), marker_colors=tuple(extra))
    return sorted(cells.values(), key=lambda c:(c["bbox"][1],c["bbox"][0]))


class ClickReasoner:
    def __init__(self):
        self.success_labels = Counter()
        self.glyph_colors = set()
        self.stats = Counter()
        self.cyclic = CyclicReasoner(self.success_labels,
                                    lambda grid,group,palette: expand_marked_tiles(grid,group,palette,self.glyph_colors))
        self.reset_level()

    def reset_level(self):
        self.previous = None
        self.previous_groups = []
        self.last_action = None
        self.active = None
        self.palette = None
        self.rules = {}
        self.visited = set()
        self.goal_labels = {}
        self.predicted = None
        self.failures = Counter()
        self.effects = {}
        self.steps = 0
        self.initial_board = None
        self.last_mask = None
        self.awaiting_reset_check = False
        self.last_visual_key = None
        self.visual_goals = {}
        self.cached_visual = {}
        self.visual_masks = {}
        self.panel_cache = {}
        self.selected_mode = "EXPLORE"
        self.cyclic.reset_level()

    def reset_episode(self):
        self.previous = None
        self.last_action = self.predicted = None
        self.awaiting_reset_check = self.initial_board is not None
        self.cyclic.clear_plan()

    def completed_level(self):
        # Completion supports proposed labels; it does not prove a formula from
        # one example. Preserve only these weak priors within this game.
        self.cyclic.completed_level()
        if self.predicted is not None:
            if self.active is not None and self.previous is not None:
                xs = sorted({c["bbox"][0] for c in self.active})
                ys = sorted({c["bbox"][1] for c in self.active})
                occupied = {(c["bbox"][0],c["bbox"][1]) for c in self.active}
                width = self.active[0]["bbox"][2]-self.active[0]["bbox"][0]+1
                height = self.active[0]["bbox"][3]-self.active[0]["bbox"][1]+1
                for x in xs:
                    for y in ys:
                        if (x,y) not in occupied:
                            self.glyph_colors.update(set(map(int,np.unique(self.previous[y:y+height,x:x+width])))-set(self.palette))
            full=(1 << len(self.active))-1 if self.active else 0
            for goal, theories in self.goal_labels.items():
                mask=self.visual_masks.get(goal,full)
                if (self.predicted ^ goal) & mask == 0:
                    for label in theories:
                        if mask==full or label.startswith("glyph:"):
                            self.success_labels[label] += 1
            self.stats["binary_level_completions"] += 1

    def _goals(self, groups):
        count = len(self.active)
        full = (1 << count)-1
        references = [g for g in groups if len(g) == count and group_key(g) != group_key(self.active)]
        values = [read_bits(self.previous, g, self.palette) for g in references]
        values = [v for v in values if v is not None]
        labels = {}
        def add(value, label):
            labels.setdefault(int(value), []).append(label)
        for index, value in enumerate(values[:6]):
            add(value, f"reference:{index}")
            add(value ^ full, f"complement:{index}")
        for i, j in combinations(range(min(len(values), 6)), 2):
            for name, value in (("xor", values[i]^values[j]), ("and", values[i]&values[j]), ("or", values[i]|values[j])):
                add(value, f"{name}:{i}:{j}")
                add(value ^ full, f"not-{name}:{i}:{j}")
        add(0, "uniform:first-color")
        add(full, "uniform:second-color")
        key = visual_key(self.previous, self.active, references, self.palette)
        if key != self.last_visual_key:
            self.cached_visual = infer_visual_goals(self.previous, self.active, references, self.palette)
            self.last_visual_key = key
        self.visual_goals={g:list(theories) for g,theories in self.cached_visual.items()}
        self.visual_goals.update(transfer_goals(self.previous, self.active, self.palette, self.success_labels))
        self.visual_masks={g:full for g in self.visual_goals}
        for label, allowed in relational_constraints(self.previous,self.active,self.palette,self.success_labels):
            mask=sum((1 << i) for i,values in enumerate(allowed) if len(values)==1)
            goal=sum((next(iter(values)) << i) for i,values in enumerate(allowed) if len(values)==1)
            if goal not in self.visual_masks:
                self.visual_masks[goal]=mask
            self.visual_goals.setdefault(goal,[]).append(label)
        for bits, theories in self.visual_goals.items():
            for theory in theories:
                add(bits, theory)
        self.stats["visual_goal_hypotheses"] = len(self.visual_goals)
        self.goal_labels = labels
        self.stats["binary_goal_hypotheses"] = len(labels)

    def observe(self, grid, objects, canonical_previous=None, canonical_current=None, mask=None):
        groups = tile_groups(objects, grid, self.glyph_colors)
        if self.awaiting_reset_check:
            ignored = self.last_mask if self.last_mask is not None else np.zeros(grid.shape, dtype=bool)
            if self.initial_board.shape != grid.shape or np.any((self.initial_board != grid) & ~ignored):
                self.stats["reset_models_discarded"] += 1
                self.reset_level()
            else:
                self.stats["reset_models_revalidated"] += 1
            self.awaiting_reset_check = False
        if self.initial_board is None:
            self.initial_board = grid.copy()
        if mask is not None:
            self.last_mask = mask.copy()
        self.steps += 1
        if self.previous is not None and self.last_action is not None and self.last_action[0] == 6:
            self.cyclic.observe(self.previous, grid, self.previous_groups, self.last_action)
            point = self.last_action[1:]
            before = canonical_previous if canonical_previous is not None else self.previous
            after = canonical_current if canonical_current is not None else grid
            changed = not np.array_equal(before, after)
            successful, total = self.effects.get(point, (0, 0))
            self.effects[point] = successful+int(changed), total+1
            if len(self.effects) > 2048:
                self.effects.pop(next(iter(self.effects)))
            if self.active is None and changed:
                for group in self.previous_groups:
                    clicked = next((c for c in group if c["bbox"][0] <= point[0] <= c["bbox"][2] and c["bbox"][1] <= point[1] <= c["bbox"][3]), None)
                    if clicked is None:
                        continue
                    colors = set(c["color"] for c in group)
                    for cell in group:
                        x0, y0, x1, y1 = cell["bbox"]
                        colors.update(set(map(int, np.unique(grid[y0:y1+1, x0:x1+1])))-set(cell.get("marker_colors", ())))
                    if len(colors) != 2:
                        continue
                    palette = tuple(sorted(colors))
                    group = expand_marked_tiles(self.previous, group, palette, self.glyph_colors)
                    old, new = read_bits(self.previous, group, palette), read_bits(grid, group, palette)
                    if old is not None and new is not None and old != new:
                        self.active, self.palette = group, palette
                        self.stats["binary_model_hypotheses"] += 1
                        self.stats["inferred_binary_cells"] = len(group)
                        self.visited.add(old)
                        break
            if self.active is not None:
                old = read_bits(self.previous, self.active, self.palette)
                new = read_bits(grid, self.active, self.palette)
                if self.predicted is not None:
                    self.stats["binary_predictions"] += 1
                    if new == self.predicted:
                        self.stats["binary_matches"] += 1
                    else:
                        self.stats["binary_mismatches"] += 1
                self.predicted = None
                if old is not None and new is not None:
                    cell = next((c for c in self.active if c["bbox"][0] <= point[0] <= c["bbox"][2] and c["bbox"][1] <= point[1] <= c["bbox"][3]), None)
                    if cell is not None:
                        self.rules.setdefault(cell["point"], Counter())[old ^ new] += 1
                    self.visited.add(new)
                    if new in self.goal_labels:
                        for label in self.goal_labels[new]:
                            self.failures[label] += 1
                        self.stats["binary_goal_tests"] += 1
                else:
                    self.stats["binary_representation_failures"] += 1
                    self.active = None
                    self.rules.clear()
        self.previous = grid.copy()
        self.previous_groups = groups
        if self.active is not None:
            self._goals(groups)
        for name, value in self.cyclic.stats.items():
            self.stats[name] = value

    def proposals(self):
        # Small glyph fragments can exhaust the adapter's component sample.
        # Retain every cell of each bounded lattice hypothesis for discovery.
        groups = self.previous_groups + [self.active, self.cyclic.active]
        return list(dict.fromkeys((6, *cell["point"]) for group in groups if group for cell in group))

    def choose(self, grid, objects, candidates, rng, mask=None):
        clicks = [a for a in candidates if a[0] == 6]
        if not clicks:
            return None
        self.selected_mode = "EXPLORE"
        cyclic_action = self.cyclic.choose(grid, candidates, rng)
        for name, value in self.cyclic.stats.items():
            self.stats[name] = value
        if cyclic_action is not None:
            self.selected_mode = "PLAN" if self.cyclic.expected is not None else "MODEL"
            return cyclic_action
        if self.active is not None:
            current = read_bits(grid, self.active, self.palette)
            if current is not None:
                if any((current ^ goal) & self.visual_masks.get(goal,(1 << len(self.active))-1)==0 for goal in self.visual_goals):
                    self.stats["panel_subgoals_satisfied"] += 1
                    self.active = None
                    self.rules.clear()
                    self.visited.clear()
                    self.predicted = None
                    return self.choose(grid, objects, candidates, rng, mask)
                available = {a[1:]: a for a in clicks}
                unknown = [c["point"] for c in self.active if c["point"] in available and c["point"] not in self.rules]
                if unknown:
                    self.stats["binary_probe_actions"] += 1
                    self.selected_mode = "MODEL"
                    return available[unknown[0]]
                transitions = {}
                for point, counts in self.rules.items():
                    delta, count = counts.most_common(1)[0]
                    if point in available and delta and len(counts) == 1:
                        transitions[available[point]] = delta
                if transitions:
                    goals = (set(self.goal_labels)-self.visited) | set(self.visual_goals)
                    supported = {g for g in goals if any(self.success_labels[label] for label in self.goal_labels[g])}
                    if supported:
                        goals = supported
                    else:
                        visual = goals & set(self.visual_goals)
                        if visual:
                            goals = visual
                    paths = [xor_plan({a:d & self.visual_masks.get(goal,(1 << len(self.active))-1) for a,d in transitions.items()},
                                      (current^goal) & self.visual_masks.get(goal,(1 << len(self.active))-1),len(self.active)) for goal in goals]
                    paths = [p for p in paths if p]
                    path = min(paths, key=len) if paths else None
                    if path:
                        self.stats["linear_plan_actions"] += 1
                    if path is None:
                        path = bfs(current, lambda s: [(a, s^delta) for a, delta in transitions.items()],
                                   lambda s: s not in self.visited, max_nodes=4096, max_depth=32)
                    if path:
                        action = path[0]
                        self.predicted = current ^ transitions[action]
                        self.stats["binary_plan_actions"] += 1
                        self.selected_mode = "PLAN"
                        return action
        # Candidate goal decomposition: panels consistent with the learned
        # example relation are left intact while unmatched panels are probed.
        groups = self.previous_groups
        colors = {c["color"] for group in groups for c in group}
        satisfied, unmatched = [], []
        if len(colors) == 2:
            palette = tuple(sorted(colors))
            for group in groups:
                references = [g for g in groups if group_key(g) != group_key(group)]
                key = group_key(group), visual_key(grid, group, references, palette)
                if key not in self.panel_cache:
                    self.panel_cache[key] = infer_visual_goals(grid, group, references, palette)
                goals = self.panel_cache[key]
                current = read_bits(grid, group, palette)
                if len(goals) == 1 and current is not None:
                    if current in goals:
                        satisfied.append(group)
                    else:
                        unmatched.append(group)
            if len(self.panel_cache) > 64:
                self.panel_cache.clear()
        if unmatched:
            available = {a[1:]: a for a in clicks}
            targets = [c["point"] for group in unmatched for c in group if c["point"] in available]
            if targets:
                target = min(targets, key=lambda p: self.effects.get(p, (0, 0))[1]+rng.random()*0.1)
                self.stats["visual_panel_probe_actions"] += 1
                self.selected_mode = "MODEL"
                return available[target]
        # Before a validated representation exists, isolate clicks on small
        # visible components and downweight repeatedly ineffective locations.
        useful = {}
        tile_points = {cell["point"] for group in groups for cell in group}
        counts = Counter(map(int, grid.ravel()))
        for obj in objects:
            x, y = obj["point"]
            if mask is not None and mask[y, x]:
                continue
            if 2 <= obj["area"] <= 128 and counts[obj["color"]] < grid.size*0.2:
                useful[obj["point"]] = 0.5
        def score(action):
            point = action[1:]
            successes, total = self.effects.get(point, (0, 0))
            exploration = 1/(1+total)
            effect = successes/(1+total)
            protected = any(min(c["bbox"][0] for c in g) <= point[0] <= max(c["bbox"][2] for c in g)
                            and min(c["bbox"][1] for c in g) <= point[1] <= max(c["bbox"][3] for c in g) for g in satisfied)
            return exploration+useful.get(point, 0)+0.65*(point in tile_points)+0.4*effect-1.0*protected+rng.random()*0.05
        self.stats["click_probe_actions"] += 1
        return max(clicks, key=score)
