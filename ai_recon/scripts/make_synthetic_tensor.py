from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.masks import cartesian_undersampling_mask
from mri_recon.phantom import synthetic_slice
from mri_recon.zero_filled import centered_fft2, zero_filled_magnitude


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-bin", type=Path, default=ROOT / "outputs" / "samples" / "synthetic_masked_image.bin")
    parser.add_argument("--target-npy", type=Path, default=ROOT / "outputs" / "samples" / "synthetic_target.npy")
    parser.add_argument("--masked-npy", type=Path, default=ROOT / "outputs" / "samples" / "synthetic_masked_image.npy")
    parser.add_argument("--acceleration", type=int, default=4)
    args = parser.parse_args()

    target = synthetic_slice((128, 128)).astype(np.float32)
    kspace = centered_fft2(target)
    mask = cartesian_undersampling_mask(target.shape, acceleration=args.acceleration, center_fraction=0.08)
    masked = zero_filled_magnitude(kspace * mask).astype(np.float32)

    for path in (args.input_bin, args.target_npy, args.masked_npy):
        path.parent.mkdir(parents=True, exist_ok=True)

    masked.tofile(args.input_bin)
    np.save(args.target_npy, target)
    np.save(args.masked_npy, masked)

    print(f"input_bin={args.input_bin}")
    print(f"target_npy={args.target_npy}")
    print(f"masked_npy={args.masked_npy}")
    print(f"input_shape={masked.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
