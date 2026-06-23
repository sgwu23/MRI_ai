from __future__ import annotations

import argparse
import os
import pathlib
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.models import build_unet
from mri_recon.phantom import synthetic_slice
from mri_recon.zero_filled import centered_fft2, zero_filled_magnitude


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs" / "assets" / "fastmri_v1")
    parser.add_argument("--sample-h5", type=Path, default=None)
    parser.add_argument("--slice-index", type=int, default=0)
    parser.add_argument("--crop-size", type=int, default=None)
    parser.add_argument("--acceleration", type=int, default=4)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args()

    try:
        import torch
    except ImportError as exc:
        raise SystemExit("PyTorch is required for visualization. Install ai_recon/requirements.txt.") from exc

    if os.name == "nt":
        pathlib.PosixPath = pathlib.WindowsPath

    state = torch.load(args.checkpoint, map_location="cpu")
    config = state.get("config", {}) if isinstance(state, dict) else {}
    crop_size = args.crop_size if args.crop_size is not None else int(config.get("crop_size", 320))

    if args.sample_h5 is not None:
        target, kspace, source = load_h5_slice(args.sample_h5, args.slice_index, crop_size)
    else:
        target = synthetic_slice((crop_size, crop_size))
        kspace = centered_fft2(target)
        source = "synthetic phantom smoke sample"

    masked_kspace = undersample(kspace, acceleration=args.acceleration, seed=args.seed)
    zero_filled = normalize(zero_filled_magnitude(masked_kspace))
    target = normalize(target)
    input_kspace = normalize(np.log1p(np.abs(masked_kspace)))

    model = build_unet()
    model.load_state_dict(state["model"] if isinstance(state, dict) and "model" in state else state)
    model.eval()
    with torch.no_grad():
        model_input = torch.from_numpy(zero_filled[None, None, :, :]).float()
        prediction = model(model_input)[0, 0].cpu().numpy()
    prediction = normalize(prediction)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    panels = [
        ("01_input_kspace.png", input_kspace),
        ("02_zero_filled.png", zero_filled),
        ("03_model_reconstruction.png", prediction),
        ("04_target.png", target),
    ]
    for filename, image in panels:
        write_png(args.output_dir / filename, image)

    contact = make_contact_sheet([image for _, image in panels])
    write_png(args.output_dir / "fastmri_v1_reconstruction_contact_sheet.png", contact)
    write_report(args.output_dir / "README.md", source, args, crop_size)

    print(f"wrote {args.output_dir}")
    print(f"source={source}")
    print(f"contact_sheet={args.output_dir / 'fastmri_v1_reconstruction_contact_sheet.png'}")
    return 0


def load_h5_slice(path: Path, slice_index: int, crop_size: int) -> tuple[np.ndarray, np.ndarray, str]:
    try:
        import h5py
    except ImportError as exc:
        raise SystemExit("h5py is required when --sample-h5 is used.") from exc

    with h5py.File(path, "r") as h5_file:
        kspace = np.asarray(h5_file["kspace"][slice_index])
        if "reconstruction_rss" in h5_file:
            target = np.asarray(h5_file["reconstruction_rss"][slice_index], dtype=np.float32)
        elif "reconstruction_esc" in h5_file:
            target = np.asarray(h5_file["reconstruction_esc"][slice_index], dtype=np.float32)
        else:
            target = zero_filled_magnitude(kspace)
    return center_crop(target, crop_size), center_crop(kspace, crop_size), f"{path.name} slice {slice_index}"


def undersample(kspace: np.ndarray, acceleration: int, seed: int) -> np.ndarray:
    cols = kspace.shape[-1]
    rng = np.random.default_rng(seed)
    mask = np.zeros(cols, dtype=np.float32)
    center_cols = max(1, int(round(cols * 0.08)))
    start = (cols - center_cols) // 2
    mask[start : start + center_cols] = 1.0
    target_cols = max(center_cols, cols // acceleration)
    candidates = np.setdiff1d(np.arange(cols), np.arange(start, start + center_cols))
    extra = max(0, target_cols - center_cols)
    if extra > 0 and len(candidates) > 0:
        chosen = rng.choice(candidates, size=min(extra, len(candidates)), replace=False)
        mask[chosen] = 1.0
    return kspace * mask


def center_crop(image: np.ndarray, crop_size: int) -> np.ndarray:
    height, width = image.shape[-2:]
    top = (height - crop_size) // 2
    left = (width - crop_size) // 2
    if top < 0 or left < 0:
        raise ValueError(f"Cannot crop image shape {image.shape[-2:]} to {crop_size}x{crop_size}")
    return np.asarray(image[..., top : top + crop_size, left : left + crop_size], dtype=image.dtype)


def normalize(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image, dtype=np.float32)
    image = image - float(image.min())
    peak = float(image.max())
    if peak > 0.0:
        image = image / peak
    return image.astype(np.float32)


def make_contact_sheet(images: list[np.ndarray], gap: int = 12) -> np.ndarray:
    height, width = images[0].shape
    canvas = np.ones((height, width * len(images) + gap * (len(images) - 1)), dtype=np.float32)
    cursor = 0
    for image in images:
        canvas[:, cursor : cursor + width] = image
        cursor += width + gap
    return canvas


def write_png(path: Path, image: np.ndarray) -> None:
    image_u8 = np.clip(normalize(image) * 255.0, 0, 255).astype(np.uint8)
    rgb = np.repeat(image_u8[:, :, None], 3, axis=2)
    height, width, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[row].tobytes() for row in range(height))
    payload = png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    payload += png_chunk(b"IDAT", zlib.compress(raw, level=9))
    payload += png_chunk(b"IEND", b"")
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + payload)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_report(path: Path, source: str, args, crop_size: int) -> None:
    path.write_text(
        "\n".join(
            [
                "# fastMRI v1 Reconstruction Visualization",
                "",
                f"- Source: `{source}`",
                f"- Checkpoint: `{args.checkpoint}`",
                f"- Crop size: `{crop_size}x{crop_size}`",
                f"- Acceleration: `{args.acceleration}x`",
                f"- Seed: `{args.seed}`",
                "",
                "Panels:",
                "",
                "1. `01_input_kspace.png`: undersampled k-space log magnitude",
                "2. `02_zero_filled.png`: zero-filled image sent to the model",
                "3. `03_model_reconstruction.png`: U-Net reconstruction",
                "4. `04_target.png`: target image",
                "",
                "The contact sheet is `fastmri_v1_reconstruction_contact_sheet.png`.",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
