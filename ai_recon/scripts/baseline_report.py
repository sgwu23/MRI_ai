from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.metrics import mse, psnr
from mri_recon.masks import cartesian_undersampling_mask
from mri_recon.phantom import synthetic_slice
from mri_recon.zero_filled import centered_fft2, zero_filled_magnitude


def build_report(acceleration: int) -> str:
    image = synthetic_slice((128, 128))
    kspace = centered_fft2(image)
    mask = cartesian_undersampling_mask(image.shape, acceleration=acceleration, center_fraction=0.08)
    undersampled = kspace * mask
    recon = zero_filled_magnitude(undersampled)

    score = psnr(image, recon)
    error = mse(image, recon)

    return "\n".join(
        [
            "# Local Zero-Filled Baseline",
            "",
            "This report uses a deterministic synthetic MRI-like slice. It verifies the",
            "reconstruction plumbing before fastMRI data and Jetson deployment are connected.",
            "",
            f"- Image shape: `{image.shape}`",
            f"- Acceleration: `{acceleration}x`",
            f"- MSE: `{error:.6f}`",
            f"- PSNR: `{score:.2f} dB`",
            "",
            "Next measured report should replace this synthetic source with fastMRI HDF5 files.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acceleration", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "performance" / "baseline_local.md")
    args = parser.parse_args()

    report = build_report(args.acceleration)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
