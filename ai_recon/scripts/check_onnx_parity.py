from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx", type=Path, required=True)
    args = parser.parse_args()

    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise SystemExit("onnxruntime is required for local ONNX parity checks.") from exc

    session = ort.InferenceSession(str(args.onnx), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    sample = np.zeros((1, 1, 128, 128), dtype=np.float32)
    output = session.run([output_name], {input_name: sample})[0]

    print(f"onnx={args.onnx}")
    print(f"input={input_name} shape={sample.shape}")
    print(f"output={output_name} shape={output.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
