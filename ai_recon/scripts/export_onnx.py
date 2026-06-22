from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.models import build_unet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()

    try:
        import torch
    except ImportError as exc:
        raise SystemExit("PyTorch is required for ONNX export. Install ai_recon/requirements.txt.") from exc

    model = build_unet()
    state = torch.load(args.checkpoint, map_location="cpu")
    model.load_state_dict(state["model"] if "model" in state else state)
    model.eval()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    example = torch.zeros((1, 1, 128, 128), dtype=torch.float32)
    torch.onnx.export(
        model,
        example,
        args.output,
        input_names=["masked_image"],
        output_names=["reconstruction"],
        dynamic_axes={"masked_image": {0: "batch"}, "reconstruction": {0: "batch"}},
        opset_version=args.opset,
    )

    print(f"exported {args.output}")
    print("Jetson step later: convert this ONNX file to TensorRT engine and benchmark latency.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
