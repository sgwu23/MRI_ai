# Local Development Plan

This file tracks work that can be completed before connecting Jetson.

## Done in Scaffold

- Repository layout.
- Synthetic MRI-like phantom.
- Cartesian undersampling mask.
- Centered FFT/IFFT zero-filled baseline.
- PSNR/MSE metrics.
- PyTorch U-Net training script.
- ONNX export script.
- ONNX Runtime parity check script.
- DICOM helper using pydicom.
- C++17 inference service host stub.
- Local test runner.

## Next Local Tasks

- Add fastMRI HDF5 smoke test after placing one `.h5` file under a local dataset folder.
- Replace synthetic report with a small real fastMRI report.
- Add GoogleTest or a lightweight C++ unit-test runner when CMake is available.

## Explicit Stop

Stop before claiming any of these:

- TensorRT latency.
- INT8 calibration accuracy.
- Jetson throughput.
- CUDA memory usage.
- STM32 to Jetson end-to-end transfer.

Those require real Jetson connection and measured logs.
