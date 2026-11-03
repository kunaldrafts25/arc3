"""Bounded empirical outcomes; image equality is not latent-state equality."""
from collections import Counter, OrderedDict, deque


class TransitionMemory:
    def __init__(self, capacity=2048):
        self.capacity = capacity
        self.edges = OrderedDict()
        self.history = deque(maxlen=128)
        self.predictions = self.matches = self.contradictions = 0

    def record(self, source, action, target):
        key = (source, action)
        if key not in self.edges:
            self.edges[key] = Counter()
        counts = self.edges[key]
        if counts and target not in counts:
            self.contradictions += 1
        if target in counts or len(counts) < 16:
            counts[target] += 1
        else:
            counts[None] += 1  # bounded overflow remains contradictory
        self.edges.move_to_end(key)
        while len(self.edges) > self.capacity:
            self.edges.popitem(last=False)
        self.history.append((source, action, target))

    def predict(self, source, action):
        counts = self.edges.get((source, action), {})
        if len(counts) == 1 and sum(counts.values()) >= 2:
            return next(iter(counts))
        return None

    def attempts(self, source, action):
        return sum(self.edges.get((source, action), {}).values())

    def graph(self):
        graph = {}
        for source, action in self.edges:
            target = self.predict(source, action)
            if target is not None and target != source:
                graph.setdefault(source, []).append((action, target))
        return graph


def bfs(start, successors, goal, max_nodes=512, max_depth=16):
    """Shortest unit-cost path; bounded, no environment stepping or cloning."""
    queue = deque([(start, [])])
    seen = {start}
    expanded = 0
    while queue and expanded < max_nodes:
        state, path = queue.popleft()
        expanded += 1
        if goal(state):
            return path
        if len(path) >= max_depth:
            continue
        for action, target in successors(state):
            if target not in seen:
                seen.add(target)
                queue.append((target, path + [action]))
    return None
