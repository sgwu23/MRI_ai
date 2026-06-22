#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT/build/jetson-cpp"

cmake -S "$ROOT/cpp_inference" -B "$BUILD_DIR" -DMRI_ENABLE_TENSORRT=ON
cmake --build "$BUILD_DIR" -j"$(nproc)"

"$BUILD_DIR/mri_inference_demo" "$ROOT/models/unet_demo_fp16.engine" 50 5
