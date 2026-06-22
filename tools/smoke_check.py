from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.metrics import psnr
from mri_recon.masks import cartesian_undersampling_mask
from mri_recon.phantom import synthetic_slice
from mri_recon.zero_filled import centered_fft2, zero_filled_magnitude


def main() -> int:
    target = synthetic_slice((64, 64))
    kspace = centered_fft2(target)
    mask = cartesian_undersampling_mask(target.shape, acceleration=4, center_fraction=0.08)
    recon = zero_filled_magnitude(kspace * mask)
    image = zero_filled_magnitude(kspace)
    score = psnr(target, recon)

    print("MRI edge platform smoke check")
    print(f"image_shape={image.shape}")
    print(f"zero_filled_psnr={score:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
