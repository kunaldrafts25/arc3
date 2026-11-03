"""Count-based exploration with optional empirical frontier routing."""
from collections import Counter, deque
import random
from .model import TransitionMemory, bfs


class Controller:
    def __init__(self, seed=0, policy="memory"):
        self.rng = random.Random(seed)
        self.policy = policy
        self.memory = TransitionMemory()
        self.visits = Counter()
        self.action_counts = Counter()
        self.location_counts = Counter()
        self.recent = deque(maxlen=12)
        self.previous = None
        self.expected = None
        self.mode = "OBSERVE"
        self.stats = Counter()
        self.held_action = None
        self.hold_remaining = 0
        self.last_was_noop = False

    def reset_level(self):
        # Do not infer transferable mechanics from a bare state hash.
        self.memory = TransitionMemory()
        self.visits.clear()
        self.action_counts.clear()
        self.location_counts.clear()
        self.recent.clear()
        self.previous = self.expected = None
        self.held_action = None
        self.hold_remaining = 0
        self.last_was_noop = False

    def observe(self, state):
        self.last_was_noop = self.previous is not None and self.previous[0] == state
        if self.previous:
            if self.policy != "novelty":
                self.memory.record(*self.previous, state)
            else:
                # Keep bounded raw transition evidence for debugging without
                # training or consulting the predictive model in this ablation.
                self.memory.history.append((*self.previous, state))
            if self.previous[0] == state:
                self.stats["ineffective_actions"] += 1
        if self.expected is not None:
            self.memory.predictions += 1
            self.stats["model_predictions"] += 1
            if self.expected == state:
                self.memory.matches += 1
                self.stats["model_matches"] += 1
            else:
                self.stats["prediction_failures"] += 1
                self.mode = "RECOVER"
        if state in self.recent:
            self.stats["repeated_states"] += 1
        self.visits[state] += 1
        if len(self.visits) > 4096:
            self.visits.pop(next(iter(self.visits)))
        self.recent.append(state)
        self.previous = self.expected = None

    def choose(self, state, candidates):
        if not candidates:
            raise ValueError("no candidate actions")
        self.mode = "EXPLORE"
        if self.policy == "coverage" and all(a[0] == 6 for a in candidates):
            action = max(candidates, key=lambda a: 1 / (1 + self.location_counts[a]) + self.rng.random() * 0.05)
        elif self.policy == "persistent":
            # Test short open-loop runs only for simple inputs, ending a run
            # on an exact no-op. Coordinates are never blindly repeated.
            blocked = self.last_was_noop
            if self.hold_remaining and self.held_action in candidates and not blocked:
                action = self.held_action
                self.hold_remaining -= 1
            else:
                action = self.rng.choice(candidates)
                self.held_action = action
                self.hold_remaining = self.rng.choice([1, 3, 7]) if action[0] in (1, 2, 3, 4) else 0
        elif self.policy == "random":
            action = self.rng.choice(candidates)
        else:
            def utility(action):
                n = self.memory.attempts(state, action) if self.policy != "novelty" else self.action_counts[state, action]
                target = self.memory.predict(state, action) if self.policy != "novelty" else None
                no_effect = 1 if target == state else 0
                risk = self.visits[target] if target is not None else 0
                return 1 / (1 + n) - 0.4 * no_effect - 0.15 * min(risk, 5) + self.rng.random() * 0.05
            action = max(candidates, key=utility)
            if self.policy == "planning" and all(self.memory.attempts(state, a) >= 2 for a in candidates):
                graph = self.memory.graph()
                # Route to an observed state with a still-untested simple action.
                # This is a frontier goal, not a claim about the game's objective.
                simple = [a for a in candidates if a[0] != 6]
                path = bfs(state, lambda s: graph.get(s, []),
                           lambda s: s != state and any(self.memory.attempts(s, a) == 0 for a in simple))
                if path and path[0] in candidates:
                    action = path[0]
                    self.mode = "PLAN"
            if self.recent.count(state) >= 4:
                self.mode = "RECOVER"
        self.stats[self.mode.lower() + "_actions"] += 1
        self.action_counts[state, action] += 1
        self.location_counts[action] += 1
        if len(self.location_counts) > 4096:
            self.location_counts.pop(next(iter(self.location_counts)))
        if len(self.action_counts) > 8192:
            self.action_counts.pop(next(iter(self.action_counts)))
        self.previous = (state, action)
        self.expected = self.memory.predict(state, action) if self.policy != "novelty" else None
        return action
