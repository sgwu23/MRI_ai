from __future__ import annotations

import numpy as np


def centered_fft2(image: np.ndarray) -> np.ndarray:
    shifted = np.fft.ifftshift(image, axes=(-2, -1))
    kspace = np.fft.fft2(shifted, axes=(-2, -1))
    return np.fft.fftshift(kspace, axes=(-2, -1))


def centered_ifft2(kspace: np.ndarray) -> np.ndarray:
    shifted = np.fft.ifftshift(kspace, axes=(-2, -1))
    image = np.fft.ifft2(shifted, axes=(-2, -1))
    return np.fft.fftshift(image, axes=(-2, -1))


def zero_filled_magnitude(kspace: np.ndarray) -> np.ndarray:
    return np.abs(centered_ifft2(kspace)).astype(np.float32)
