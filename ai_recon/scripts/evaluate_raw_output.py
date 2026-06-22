from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.metrics import mse, psnr


def normalize(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image, dtype=np.float32)
    image = image - float(image.min())
    peak = float(image.max())
    if peak > 0.0:
        image = image / peak
    return image.astype(np.float32)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-bin", type=Path, required=True)
    parser.add_argument("--target-npy", type=Path, required=True)
    parser.add_argument("--masked-npy", type=Path)
    parser.add_argument("--shape", type=int, nargs=2, default=(128, 128))
    parser.add_argument("--report", type=Path, default=ROOT / "docs" / "performance" / "synthetic_tensor_eval.md")
    args = parser.parse_args()

    target = np.load(args.target_npy).astype(np.float32)
    output = np.fromfile(args.output_bin, dtype=np.float32).reshape(tuple(args.shape))
    output_norm = normalize(output)

    lines = [
        "# Synthetic Tensor Reconstruction Eval",
        "",
        "This report evaluates a Jetson TensorRT C++ output tensor against the local synthetic target.",
        "",
        f"- Output file: `{args.output_bin}`",
        f"- Target file: `{args.target_npy}`",
        f"- Output shape: `{output.shape}`",
        f"- Output min/max: `{float(output.min()):.6f} / {float(output.max()):.6f}`",
        f"- Raw output MSE: `{mse(target, output):.6f}`",
        f"- Raw output PSNR: `{psnr(target, output):.2f} dB`",
        f"- Normalized output MSE: `{mse(target, output_norm):.6f}`",
        f"- Normalized output PSNR: `{psnr(target, output_norm):.2f} dB`",
    ]

    if args.masked_npy is not None:
        masked = np.load(args.masked_npy).astype(np.float32)
        lines.extend(
            [
                f"- Zero-filled masked MSE: `{mse(target, masked):.6f}`",
                f"- Zero-filled masked PSNR: `{psnr(target, masked):.2f} dB`",
            ]
        )

    lines.extend(
        [
            "",
            "Note: the current model is a tiny scaffold model trained only for pipeline validation.",
            "These quality numbers are not resume-grade yet; they prove the data path.",
            "",
        ]
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
