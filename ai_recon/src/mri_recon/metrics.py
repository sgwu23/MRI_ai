from __future__ import annotations

import numpy as np


def mse(reference: np.ndarray, prediction: np.ndarray) -> float:
    diff = np.asarray(reference, dtype=np.float32) - np.asarray(prediction, dtype=np.float32)
    return float(np.mean(diff * diff))


def psnr(reference: np.ndarray, prediction: np.ndarray, data_range: float | None = None) -> float:
    error = mse(reference, prediction)
    if error == 0.0:
        return float("inf")

    if data_range is None:
        ref = np.asarray(reference, dtype=np.float32)
        data_range = float(ref.max() - ref.min())
        if data_range == 0.0:
            data_range = 1.0

    return float(20.0 * np.log10(data_range) - 10.0 * np.log10(error))

