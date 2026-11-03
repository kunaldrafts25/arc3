"""Learn color cycles and plan through validated modular action effects."""
from collections import Counter, deque
import numpy as np
from .visual_goals import relational_constraints


def colors_at(grid, group):
    values = []
    for cell in group:
        x0, y0, x1, y1 = cell["bbox"]
        patch = grid[y0:y1+1, x0:x1+1]
        if not patch.size:
            return None
        value=int(patch[patch.shape[0]//2,patch.shape[1]//2])
        if np.any(~np.isin(patch,(value,)+tuple(cell.get("marker_colors",())))):
            return None
        values.append(value)
    return tuple(values)


def modular_space(matrix, rhs, modulus):
    """Particular solution and null-space basis over a prime field."""
    matrix = np.asarray(matrix, dtype=np.int16).copy() % modulus
    rhs = np.asarray(rhs, dtype=np.int16).copy() % modulus
    rows, columns = matrix.shape
    pivots, rank = [], 0
    for column in range(columns):
        possible = np.flatnonzero(matrix[rank:, column])
        if not len(possible):
            continue
        pivot = rank+int(possible[0])
        matrix[[rank, pivot]] = matrix[[pivot, rank]]
        rhs[[rank, pivot]] = rhs[[pivot, rank]]
        inverse = pow(int(matrix[rank, column]), -1, modulus)
        matrix[rank] = matrix[rank]*inverse % modulus
        rhs[rank] = rhs[rank]*inverse % modulus
        factors = matrix[:, column].copy()
        factors[rank] = 0
        matrix = (matrix-factors[:, None]*matrix[rank]) % modulus
        rhs = (rhs-factors*rhs[rank]) % modulus
        pivots.append(column)
        rank += 1
        if rank == rows:
            break
    if np.any((~matrix.any(axis=1)) & (rhs != 0)):
        return None
    particular = np.zeros(columns, dtype=np.int16)
    for row, column in enumerate(pivots):
        particular[column] = rhs[row]
    free = [c for c in range(columns) if c not in pivots]
    basis = np.zeros((len(free), columns), dtype=np.int16)
    for i, column in enumerate(free):
        basis[i, column] = 1
        for row, pivot in enumerate(pivots):
            basis[i, pivot] = -matrix[row, column] % modulus
    return particular, basis


class CyclicReasoner:
    def __init__(self, successful_labels, group_expander=None):
        self.successful_labels = successful_labels
        self.stats = Counter()
        self.group_expander=group_expander
        self.reset_level()

    def reset_level(self):
        self.active = None
        self.edges = {}
        self.history = {}
        self.plan = deque()
        self.expected = None
        self.last_point = None
        self.label = None
        self.discovery_trials = 0

    def clear_plan(self):
        self.plan.clear()
        self.expected = None

    def cycle(self):
        colors = set(self.edges)
        colors.update(v for counts in self.edges.values() for v in counts)
        if len(colors) < 3:
            return None
        successors = {c:next(iter(counts)) for c, counts in self.edges.items() if len(counts) == 1}
        result = [min(colors)]
        while result[-1] in successors and successors[result[-1]] not in result and len(result) <= 16:
            result.append(successors[result[-1]])
        if len(result) == len(colors) and successors.get(result[-1]) == result[0]:
            return tuple(result)
        return None

    def observe(self, previous, current, groups, action):
        if previous is None or action is None or action[0] != 6:
            return
        point = action[1:]
        if self.active is None:
            for group in groups:
                if any(c["bbox"][0] <= point[0] <= c["bbox"][2] and c["bbox"][1] <= point[1] <= c["bbox"][3] for c in group):
                    before, after = colors_at(previous, group), colors_at(current, group)
                    if before is not None and after is not None and before != after:
                        self.active = self.group_expander(previous,group,tuple(set(before+after))) if self.group_expander else group
                        break
        if self.active is None:
            return
        before, after = colors_at(previous, self.active), colors_at(current, self.active)
        if before is None or after is None:
            self.clear_plan()
            return
        if self.expected is not None:
            self.stats["cyclic_predictions"] += 1
            if after == self.expected:
                self.stats["cyclic_matches"] += 1
            else:
                self.stats["cyclic_mismatches"] += 1
                self.plan.clear()
            self.expected = None
        cell = next((c for c in self.active if c["bbox"][0] <= point[0] <= c["bbox"][2] and c["bbox"][1] <= point[1] <= c["bbox"][3]), None)
        if cell is None:
            return
        self.history.setdefault(cell["point"], deque(maxlen=4)).append((before, after))
        for old, new in zip(before, after):
            if old != new:
                self.edges.setdefault(old, Counter())[new] += 1
        if before != after:
            self.last_point = cell["point"]

    def completed_level(self):
        if self.label is not None and self.expected is not None:
            self.successful_labels[self.label] += 1
            self.stats["cyclic_level_completions"] += 1

    def choose(self, grid, candidates, rng):
        if self.active is None:
            return None
        available = {a[1:]:a for a in candidates if a[0] == 6}
        seen_colors = set(self.edges) | {v for counts in self.edges.values() for v in counts}
        if len(seen_colors) < 3:
            return None
        palette = self.cycle()
        if palette is None:
            if self.last_point in available and self.discovery_trials < 8:
                self.discovery_trials += 1
                self.stats["cycle_discovery_actions"] += 1
                return available[self.last_point]
            return None
        modulus = len(palette)
        self.stats["inferred_cycle_size"] = modulus
        if modulus not in (3, 5, 7, 11, 13):
            return None
        current_colors = colors_at(grid, self.active)
        if current_colors is None or any(c not in palette for c in current_colors):
            return None
        if self.plan:
            action, expected = self.plan.popleft()
            if action[1:] in available:
                self.expected = expected
                self.stats["cyclic_plan_actions"] += 1
                return action
            self.clear_plan()
        unknown = [c["point"] for c in self.active if c["point"] in available and c["point"] not in self.history]
        if unknown:
            self.stats["cyclic_probe_actions"] += 1
            return available[unknown[0]]
        actions, deltas = [], []
        for point, transitions in self.history.items():
            vectors = set()
            for before, after in transitions:
                if all(c in palette for c in before+after):
                    vectors.add(tuple((palette.index(new)-palette.index(old)) % modulus for old, new in zip(before, after)))
            if len(vectors) == 1 and point in available:
                vector = next(iter(vectors))
                if any(vector):
                    actions.append(available[point])
                    deltas.append(vector)
        if not actions:
            return None
        constraints = relational_constraints(grid, self.active, palette, self.successful_labels)
        current = np.array([palette.index(c) for c in current_colors], dtype=np.int16)
        effects = np.array(deltas, dtype=np.int16).T
        best = None
        for label, allowed in constraints:
            fixed = [i for i, values in enumerate(allowed) if len(values) == 1]
            rhs = np.array([(next(iter(allowed[i]))-current[i]) % modulus for i in fixed], dtype=np.int16)
            space = modular_space(effects[fixed], rhs, modulus)
            if space is None:
                continue
            particular, basis = space
            dimension = len(basis)
            total = modulus**dimension
            if total <= 4096:
                powers = np.array([modulus**i for i in range(dimension)], dtype=np.int64)
                coefficients = (np.arange(total)[:, None]//powers[None, :]) % modulus if dimension else np.zeros((1,0), dtype=np.int16)
            else:
                generator = np.random.default_rng(rng.getrandbits(64))
                coefficients = generator.integers(0, modulus, size=(4096, dimension), dtype=np.int16)
                coefficients[0] = 0
            presses = (particular[None, :]+coefficients @ basis) % modulus
            states = (current[None, :]+presses @ effects.T) % modulus
            allowed_table = np.array([[value in values for value in range(modulus)] for values in allowed])
            valid = allowed_table[np.arange(len(self.active))[None, :], states].all(axis=1)
            if not np.any(valid):
                continue
            choices = np.flatnonzero(valid)
            counts = presses[choices]
            index = int(np.argmin(counts.sum(axis=1)))
            solution = counts[index]
            cost = int(solution.sum())
            if cost and (best is None or cost < best[0]):
                best = cost, label, solution
        if best is None:
            return None
        _, self.label, solution = best
        state = current.copy()
        for column, presses in enumerate(solution):
            for _ in range(int(presses)):
                state = (state+effects[:, column]) % modulus
                expected = tuple(palette[int(c)] for c in state)
                self.plan.append((actions[column], expected))
        if self.plan:
            action, self.expected = self.plan.popleft()
            self.stats["cyclic_plan_actions"] += 1
            return action
        return None
