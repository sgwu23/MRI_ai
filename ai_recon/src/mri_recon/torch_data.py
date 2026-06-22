from __future__ import annotations

import numpy as np

from .masks import cartesian_undersampling_mask
from .phantom import synthetic_slice
from .zero_filled import centered_fft2, zero_filled_magnitude


class SyntheticReconDataset:
    def __init__(self, samples: int, shape: tuple[int, int], acceleration: int) -> None:
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("PyTorch is required for SyntheticReconDataset") from exc

        self._torch = torch
        self.samples = samples
        self.shape = shape
        self.acceleration = acceleration
        self._items = [self._build_item(index) for index in range(samples)]

    def __len__(self) -> int:
        return self.samples

    def __getitem__(self, index: int):
        return self._items[index]

    def _build_item(self, index: int):
        image = np.roll(synthetic_slice(self.shape), shift=index % 9, axis=1)
        if (index // 9) % 2 == 1:
            image = np.flip(image, axis=0).copy()
        scale = 0.85 + 0.03 * (index % 7)
        image = np.clip(image * scale, 0.0, 1.0).astype(np.float32)
        kspace = centered_fft2(image)
        mask = cartesian_undersampling_mask(self.shape, self.acceleration, center_fraction=0.08, seed=index)
        masked = zero_filled_magnitude(kspace * mask)

        return {
            "masked_image": self._torch.from_numpy(masked[None, :, :]).float(),
            "target": self._torch.from_numpy(image[None, :, :]).float(),
        }
