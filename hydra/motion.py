"""Observed object motion, tentative contact goals, and bounded navigation.

No action-direction mapping, terrain color, avatar color or target location is
provided. These are hypotheses inferred from public observation transitions.
"""
from collections import Counter
from hashlib import blake2b
import numpy as np
from .model import bfs


def signature(obj):
    return obj["color"], obj["area"], obj["shape"]


def overlaps(a, b, margin=0):
    return a[0] <= b[2]+margin and b[0] <= a[2]+margin and a[1] <= b[3]+margin and b[1] <= a[3]+margin


class MotionReasoner:
    def __init__(self):
        self.rules = {}
        self.floor = Counter()
        self.selected = None
        self.previous_objects = None
        self.previous_grid = None
        self.last_action = None
        self.expected = None
        self.blocked = set()
        self.tested_goals = set()
        self.goals = {}
        self.stats = Counter()
        self.failed_predictions = 0
        self.cooldown = 0
        self.pending_contact = None
        self.unreachable = set()
        self.context = None
        self.missing = 0

    def reset_level(self):
        # Mechanics remain hypotheses within a game; geometry and trials reset.
        self.floor.clear()
        self.selected = self.previous_objects = self.previous_grid = self.last_action = self.expected = None
        self.blocked.clear()
        self.tested_goals.clear()
        self.goals.clear()
        self.failed_predictions = self.cooldown = 0
        self.pending_contact = self.context = None
        self.unreachable.clear()
        self.missing = 0

    def observe(self, grid, objects):
        if self.previous_objects is not None and self.last_action is not None and self.last_action[0] in range(1, 6):
            action = self.last_action[0]
            previous_by_signature = {}
            current_by_signature = {}
            for group, items in ((previous_by_signature, self.previous_objects), (current_by_signature, objects)):
                for obj in items:
                    if 3 <= obj["area"] <= 256:
                        group.setdefault(signature(obj), []).append(obj)
            for spec, old_objects in previous_by_signature.items():
                new_objects = current_by_signature.get(spec, [])
                # Strong identification gate: defer repeated/ambiguous shapes.
                if len(old_objects) != 1 or len(new_objects) != 1:
                    continue
                old, new = old_objects[0], new_objects[0]
                dx, dy = new["bbox"][0]-old["bbox"][0], new["bbox"][1]-old["bbox"][1]
                if not (0 < abs(dx)+abs(dy) <= 16 and (dx == 0 or dy == 0)):
                    continue
                counts = self.rules.setdefault(spec, {}).setdefault(action, Counter())
                counts[(dx, dy)] += 1
                if len(self.rules) > 512:
                    self.rules.pop(next(key for key in self.rules if key != self.selected))
            if self.selected is not None:
                old_matches = previous_by_signature.get(self.selected, [])
                new_matches = current_by_signature.get(self.selected, [])
                if len(old_matches) == len(new_matches) == 1:
                    old, new = old_matches[0], new_matches[0]
                    if old["bbox"] != new["bbox"]:
                        x0, y0, x1, y1 = old["bbox"]
                        exposed = self.previous_grid[y0:y1+1, x0:x1+1] == old["color"]
                        nx0, ny0, nx1, ny1 = new["bbox"]
                        yy, xx = np.indices(exposed.shape)
                        exposed &= ~((xx+x0 >= nx0) & (xx+x0 <= nx1) & (yy+y0 >= ny0) & (yy+y0 <= ny1))
                        colors = grid[y0:y1+1, x0:x1+1][exposed]
                        self.floor.update(map(int, colors))
        if self.expected is not None:
            source, action, predicted = self.expected
            matches = [o for o in objects if signature(o) == self.selected]
            self.stats["motion_predictions"] += 1
            if len(matches) == 1 and matches[0]["bbox"][:2] == predicted:
                self.stats["motion_matches"] += 1
                self.failed_predictions = 0
                if self.pending_contact is not None:
                    self.tested_goals.add(self.pending_contact)
                    self.stats["contact_experiments"] += 1
            else:
                self.stats["motion_mismatches"] += 1
                self.blocked.add((source, action))
                self.failed_predictions += 1
                if self.failed_predictions >= 3:
                    self.cooldown = 12
            self.expected = None
            self.pending_contact = None
        if self.selected is not None:
            self.missing = 0 if sum(signature(o) == self.selected for o in objects) == 1 else self.missing+1
            if self.missing >= 2:
                self.selected = None
                self.floor.clear()
                self.blocked.clear()
                self.stats["control_losses"] += 1
        # Require consistent action-conditioned displacement in multiple
        # directions, not merely an object that animates whenever time advances.
        choices = []
        for spec, actions in self.rules.items():
            vectors = self.vectors(spec)
            if len(vectors) >= 2 and len(set(vectors.values())) >= 2:
                evidence = sum(sum(c.values()) for c in actions.values())
                if evidence >= 3 and sum(signature(o) == spec for o in objects) == 1:
                    choices.append((evidence, spec))
        if choices and self.selected is None:
            self.selected = max(choices, key=lambda item: item[0])[1]
            self.stats["control_hypotheses"] += 1
        self.previous_objects = objects
        self.previous_grid = grid.copy()
        if self.cooldown:
            self.cooldown -= 1

    def vectors(self, spec=None):
        result = {}
        for action, counts in self.rules.get(spec or self.selected, {}).items():
            vector, count = counts.most_common(1)[0]
            if count/sum(counts.values()) >= 0.8:
                result[action] = vector
        return result

    def choose(self, grid, objects, available):
        if self.selected is None or not self.floor or self.cooldown:
            return None
        matches = [o for o in objects if signature(o) == self.selected]
        if len(matches) != 1:
            return None
        player = matches[0]
        x0, y0, x1, y1 = player["bbox"]
        vectors = {a: d for a, d in self.vectors().items() if a in available}
        if len(vectors) < 2:
            return None
        floor_color, count = self.floor.most_common(1)[0]
        if count/sum(self.floor.values()) < 0.7:
            return None
        # Erase only nearby co-moving pieces to retain multi-color avatars.
        pieces = [player]
        for obj in objects:
            if signature(obj) in self.rules and overlaps(obj["bbox"], player["bbox"], margin=1):
                if self.vectors(signature(obj)) == self.vectors():
                    pieces.append(obj)
        footprint = (min(o["bbox"][0] for o in pieces)-x0, min(o["bbox"][1] for o in pieces)-y0,
                     max(o["bbox"][2] for o in pieces)-x0, max(o["bbox"][3] for o in pieces)-y0)
        clean = grid.copy()
        for obj in pieces:
            bx0, by0, bx1, by1 = obj["bbox"]
            clean[by0:by1+1, bx0:bx1+1] = floor_color
        context = blake2b(clean.tobytes(), digest_size=8).hexdigest()
        if context != self.context:
            self.blocked.clear()
            self.context = context
        color_counts = Counter(map(int, grid.ravel()))
        for obj in objects:
            if obj in pieces or obj["color"] == floor_color or not 2 <= obj["area"] <= 128:
                continue
            if color_counts[obj["color"]] > grid.size*0.15:
                continue
            bx0, by0, bx1, by1 = obj["bbox"]
            if max(bx1-bx0, by1-by0) > 16:
                continue
            key = (obj["color"], obj["shape"], obj["bbox"])
            self.goals[key] = obj
        if len(self.goals) > 128:
            self.goals.pop(next(iter(self.goals)))
        origin = (x0, y0)
        width, height = grid.shape[1], grid.shape[0]
        targets = sorted(self.goals.items(), key=lambda item: abs(item[1]["point"][0]-player["point"][0])+abs(item[1]["point"][1]-player["point"][1]))
        for key, goal in targets[:24]:
            trial = context, key
            if trial in self.tested_goals or (trial, origin) in self.unreachable:
                continue
            gx0, gy0, gx1, gy1 = goal["bbox"]
            def reached(position):
                px, py = position
                return overlaps((px+footprint[0], py+footprint[1], px+footprint[2], py+footprint[3]), goal["bbox"])
            if reached(origin):
                self.tested_goals.add(trial)
                self.stats["contact_experiments"] += 1
                continue
            def successors(position):
                px, py = position
                for action, (dx, dy) in vectors.items():
                    if (position, action) in self.blocked:
                        continue
                    nx, ny = px+dx, py+dy
                    bx0, by0, bx1, by1 = nx+footprint[0], ny+footprint[1], nx+footprint[2], ny+footprint[3]
                    if bx0 < 0 or by0 < 0 or bx1 >= width or by1 >= height:
                        continue
                    patch = clean[by0:by1+1, bx0:bx1+1]
                    yy, xx = np.indices(patch.shape)
                    contact = (xx+bx0 >= gx0) & (xx+bx0 <= gx1) & (yy+by0 >= gy0) & (yy+by0 <= gy1)
                    if np.all((patch == floor_color) | contact):
                        yield action, (nx, ny)
            path = bfs(origin, successors, reached, max_nodes=512, max_depth=32)
            if path:
                action = path[0]
                dx, dy = vectors[action]
                self.expected = origin, action, (x0+dx, y0+dy)
                if reached((x0+dx, y0+dy)):
                    self.pending_contact = trial
                self.stats["navigation_actions"] += 1
                return action, None, None
            self.unreachable.add((trial, origin))
        if len(self.tested_goals) > 2048:
            self.tested_goals.clear()
        if len(self.unreachable) > 4096:
            self.unreachable.clear()
        return None
