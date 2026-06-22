from __future__ import annotations

import numpy as np


def synthetic_slice(shape: tuple[int, int] = (128, 128)) -> np.ndarray:
    rows, cols = shape
    y_axis = np.linspace(-1.0, 1.0, rows, dtype=np.float32)
    x_axis = np.linspace(-1.0, 1.0, cols, dtype=np.float32)
    y_grid, x_grid = np.meshgrid(y_axis, x_axis, indexing="ij")

    image = np.zeros(shape, dtype=np.float32)
    image += ellipse(x_grid, y_grid, 0.0, 0.0, 0.75, 0.55, 1.0)
    image += ellipse(x_grid, y_grid, -0.25, 0.15, 0.18, 0.12, 0.45)
    image += ellipse(x_grid, y_grid, 0.28, -0.18, 0.22, 0.10, 0.35)
    image -= ellipse(x_grid, y_grid, 0.10, 0.22, 0.12, 0.08, 0.25)
    return np.clip(image, 0.0, 1.0)


def ellipse(
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    x0: float,
    y0: float,
    rx: float,
    ry: float,
    value: float,
) -> np.ndarray:
    inside = (((x_grid - x0) / rx) ** 2 + ((y_grid - y0) / ry) ** 2) <= 1.0
    return inside.astype(np.float32) * value
