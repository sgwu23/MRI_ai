# Jetson And Hardware Handoff

This document records which parts can run on a local workstation and which parts require Jetson or STM32 hardware.

## Completed Jetson Work

- Exported the fastMRI v1 PyTorch checkpoint to ONNX.
- Built a TensorRT FP16 engine on Jetson Orin with fixed input shape `1x1x320x320`.
- Benchmarked the ONNX/TensorRT path with `trtexec`.
- Verified the project C++ TensorRT backend can deserialize the engine and run inference.

Current benchmark summary:

- `docs/performance/fastmri_v1_jetson_benchmark.md`
- `docs/performance/trtexec_fastmri_v1_fp16.log`
- `docs/performance/cpp_fastmri_v1_tensorrt.log`

## Local Workstation Can Run

- Unit tests and smoke tests.
- fastMRI HDF5 parsing if `h5py` is installed correctly.
- PyTorch checkpoint loading on CPU.
- ONNX export.
- Reconstruction visualization from a checkpoint and a sample `.h5` file.
- C++ host stub build where TensorRT is not available.

## Requires Jetson

- TensorRT engine build from ONNX.
- Real GPU latency, throughput, and memory measurements.
- C++ TensorRT backend linking against Jetson TensorRT and CUDA libraries.
- Future optimization work such as dynamic shape profiles, CUDA graph, or INT8 calibration.

## Requires STM32 Hardware

- Zephyr board bring-up.
- GPIO/timer pulse-sequence playback.
- UART/USB bridge tests between STM32 and Jetson or host PC.
- Timing jitter measurement with a logic analyzer or oscilloscope.

The next hardware target is the available STM32F4 board. STM32H7 can remain an upgrade target after the F4 prototype is working.

## Current Jetson Commands

Build the engine:

```bash
/usr/src/tensorrt/bin/trtexec \
  --onnx=models/unet_fastmri_v1_best.onnx \
  --saveEngine=models/unet_fastmri_v1_best_fp16.engine \
  --fp16 \
  --shapes=masked_image:1x1x320x320 \
  --duration=10
```

Run the C++ smoke test:

```bash
./build/jetson-cpp/mri_inference_demo models/unet_fastmri_v1_best_fp16.engine 50 5
```
