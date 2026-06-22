from __future__ import annotations

import numpy as np


def cartesian_undersampling_mask(
    shape: tuple[int, int],
    acceleration: int,
    center_fraction: float,
    seed: int = 7,
) -> np.ndarray:
    if acceleration <= 1:
        return np.ones(shape, dtype=np.float32)

    rows, cols = shape
    mask = np.zeros((rows, cols), dtype=np.float32)
    center_cols = max(1, int(round(cols * center_fraction)))
    start = (cols - center_cols) // 2
    mask[:, start : start + center_cols] = 1.0

    rng = np.random.default_rng(seed)
    target_cols = max(center_cols, cols // acceleration)
    candidates = np.setdiff1d(np.arange(cols), np.arange(start, start + center_cols))
    extra = max(0, target_cols - center_cols)
    if extra > 0 and len(candidates) > 0:
        chosen = rng.choice(candidates, size=min(extra, len(candidates)), replace=False)
        mask[:, chosen] = 1.0
    return mask
