"""Learn monotone edge-meter candidates without discarding raw observations.

This abstraction is for exploration counts only, never a latent-state model.
"""
import numpy as np


class MeterDetector:
    def __init__(self, confirmations=4):
        self.confirmations = confirmations
        self.anchor = None
        self.probes = {}
        self.confirmed = {}
        self.mask = None
        self.revocations = 0

    def reset(self):
        self.anchor = self.mask = None
        self.probes.clear()
        self.confirmed.clear()

    @staticmethod
    def _line(grid, axis, index):
        return grid[index, :] if axis == 0 else grid[:, index]

    def observe(self, previous, current):
        if self.anchor is None or self.anchor.shape != current.shape:
            self.anchor = current.copy() if previous is None or previous.shape != current.shape else previous.copy()
            self.mask = np.zeros(current.shape, dtype=bool)
        if previous is None or previous.shape != current.shape:
            return
        height, width = current.shape
        for key in list(self.confirmed):
            axis, index, start, end, old, new = key
            before = self._line(previous, axis, index)[start:end]
            after = self._line(current, axis, index)[start:end]
            changed = before != after
            # Restore information if the region stops behaving like a small,
            # monotone, two-color meter. Raw grids have always remained intact.
            if changed.sum() > 4 or np.any(changed & ((before != old) | (after != new))):
                del self.confirmed[key]
                self.probes.pop(key, None)
                self.revocations += 1
        for axis, length in ((0, height), (1, width)):
            margin = min(4, max(1, length//16))
            for index in sorted(set(range(margin)) | set(range(length-margin, length))):
                before = self._line(previous, axis, index)
                after = self._line(current, axis, index)
                changed = np.flatnonzero(before != after)
                if not 1 <= len(changed) <= 4:
                    continue
                old_values, new_values = np.unique(before[changed]), np.unique(after[changed])
                if len(old_values) != 1 or len(new_values) != 1:
                    continue
                old, new = int(old_values[0]), int(new_values[0])
                anchor = self._line(self.anchor, axis, index)
                if np.any(anchor[changed] != old):
                    continue
                start, end = int(changed[0]), int(changed[-1])+1
                while start > 0 and anchor[start-1] == old:
                    start -= 1
                while end < len(anchor) and anchor[end] == old:
                    end += 1
                if end-start < max(12, len(anchor)//4) or np.any(anchor[start:end] != old):
                    continue
                key = axis, index, start, end, old, new
                probe = self.probes.setdefault(key, {"hits": 0, "positions": set(), "last": None, "direction": None})
                center = float(changed.mean())
                direction = np.sign(center-probe["last"]) if probe["last"] is not None else 0
                if set(changed) & probe["positions"] or (probe["direction"] not in (None, 0) and direction != probe["direction"]):
                    self.probes.pop(key, None)
                    self.confirmed.pop(key, None)
                    continue
                probe["hits"] += 1
                probe["positions"].update(map(int, changed))
                probe["last"] = center
                if direction:
                    probe["direction"] = direction
                if probe["hits"] >= self.confirmations and len(probe["positions"]) >= self.confirmations:
                    self.confirmed[key] = True
        self.mask[:] = False
        for axis, index, start, end, _, _ in self.confirmed:
            if axis == 0:
                self.mask[index, start:end] = True
            else:
                self.mask[start:end, index] = True

    def canonical(self, grid):
        result = grid.copy()
        if self.mask is not None and grid.shape == self.mask.shape:
            result[self.mask] = self.anchor[self.mask]
        return result
