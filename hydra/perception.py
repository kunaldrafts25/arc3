"""Lossless frame normalization and compact visual measurements."""
from hashlib import blake2b
import numpy as np


def normalize(observation):
    """Return all valid 2D frames; missing/invalid images remain explicit."""
    frames = []
    for raw in getattr(observation, "frame", []) or []:
        try:
            grid = np.asarray(raw, dtype=np.int16)
            if grid.ndim == 2 and grid.size:
                frames.append(grid.copy())
        except (ValueError, TypeError, OverflowError):
            continue
    return frames


def state_key(observation, grid_override=None):
    # Latest rendered image is the decision state. Preserve complete animation
    # frames separately; including their count would split identical end states.
    frames = normalize(observation)
    h = blake2b(digest_size=16)
    h.update(str((getattr(observation, "levels_completed", 0),
                  str(getattr(observation, "state", "")),
                  tuple(getattr(observation, "available_actions", []) or []))).encode())
    grid = grid_override if grid_override is not None else (frames[-1] if frames else None)
    if grid is not None:
        h.update(str(grid.shape).encode())
        h.update(grid.tobytes())
    return h.hexdigest()


def grid_diff(previous, current):
    if previous.shape != current.shape:
        return {"changed_cells": None, "bbox": None, "shape_changed": True}
    ys, xs = np.nonzero(previous != current)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if xs.size else None
    return {"changed_cells": int(xs.size), "bbox": bbox, "shape_changed": False}


def components(grid, connectivity=4, limit=256, describe=False):
    """Color components including background; no semantic identity assumed.

    Iterative flood fill is bounded by grid size. Vectorized color segmentation
    would merge disconnected objects and lose useful click candidates.
    """
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    height, width = grid.shape
    seen = np.zeros(grid.shape, dtype=bool)
    offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if connectivity == 8:
        offsets += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    objects = []
    for y, x in np.ndindex(grid.shape):
        if seen[y, x]:
            continue
        color, stack, pixels = grid[y, x], [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop()
            pixels.append((cy, cx))
            for dy, dx in offsets:
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < height and 0 <= nx < width and not seen[ny, nx] and grid[ny, nx] == color:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        coords = np.asarray(pixels)
        # Pick a real component pixel nearest centroid, including concave shapes.
        center = coords.mean(axis=0)
        py, px = coords[np.argmin(((coords - center) ** 2).sum(axis=1))]
        obj = {"color": int(color), "area": len(pixels),
                        "point": (int(px), int(py)),
                        "bbox": (int(coords[:, 1].min()), int(coords[:, 0].min()),
                                 int(coords[:, 1].max()), int(coords[:, 0].max()))}
        if describe:
            x0, y0, x1, y1 = obj["bbox"]
            mask = np.zeros((y1-y0+1, x1-x0+1), dtype=np.uint8)
            mask[coords[:, 0]-y0, coords[:, 1]-x0] = 1
            obj["shape"] = (mask.shape, blake2b(mask.tobytes(), digest_size=8).hexdigest())
            obj["centroid"] = (float(center[1]), float(center[0]))
        objects.append(obj)
    return sorted(objects, key=lambda obj: obj["area"])[:limit]
