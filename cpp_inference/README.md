# C++ Inference Service

This folder holds the C++17 host-side service boundary for medical image reconstruction.

Current status:

- `InferenceEngine` is a host stub that validates input and echoes DICOM bytes.
- The TensorRT implementation is intentionally not enabled yet because it requires Jetson libraries and hardware benchmarking.
- The same public interface should be kept when replacing the stub with ONNX Runtime or TensorRT.

Local GCC build without CMake:

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_cpp_gcc.ps1
```

Future Jetson backend:

Implemented first TensorRT backend target:

```bash
bash tools/build_cpp_jetson.sh
```

The current C++ smoke test:

1. Loads a serialized `.engine` file.
2. Allocates CUDA input/output buffers.
3. Runs one TensorRT inference through `enqueueV3`.
4. Returns output tensor bytes and latency metadata.

It is still a tensor smoke test, not a full DICOM reconstruction service.
