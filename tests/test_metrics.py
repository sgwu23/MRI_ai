import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.metrics import mse, psnr


def test_mse_zero_for_identical_arrays():
    image = np.ones((4, 4), dtype=np.float32)
    assert mse(image, image) == 0.0


def test_psnr_inf_for_identical_arrays():
    image = np.ones((4, 4), dtype=np.float32)
    assert psnr(image, image) == float("inf")

