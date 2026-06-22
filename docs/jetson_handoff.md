# Jetson Handoff Point

Everything before this point can be developed on the local workstation.

## Local Workstation Can Finish

- Synthetic reconstruction baseline.
- fastMRI HDF5 dataset adapter.
- PyTorch U-Net training on CPU/GPU if available.
- ONNX export and ONNX Runtime parity check.
- DICOM read/write with `pydicom`.
- C++17 service interface and host stub.
- Documentation, tests, CI, and resume narrative.

## Requires Jetson Connection

- TensorRT engine build with `trtexec`. First FP16 build completed on 2026-06-01.
- FP16/INT8 calibration and accuracy comparison on Jetson Orin Nano.
- Real latency, memory, and throughput measurements. First FP16 random-input benchmark is in `docs/performance/jetson_benchmark.md`.
- Jetson-side C++ linking against TensorRT, CUDA, and optionally DCMTK.
- End-to-end UART/USB bridge test with STM32H7 hardware.

## Expected Jetson Commands Later

```bash
trtexec --onnx=outputs/models/unet_demo.onnx --saveEngine=outputs/models/unet_demo_fp16.engine --fp16
trtexec --loadEngine=outputs/models/unet_demo_fp16.engine --shapes=masked_image:1x1x128x128
```

Record real results in `docs/performance/jetson_benchmark.md`.
