# Performance Reports

This folder contains measured training, reconstruction, and deployment reports.

Recommended reading order:

1. `fastmri_v1_eval.md`: formal fastMRI v1 validation result.
2. `fastmri_v1_jetson_benchmark.md`: summary of ONNX/TensorRT deployment on Jetson.
3. `trtexec_fastmri_v1_fp16.log`: raw TensorRT benchmark log.
4. `cpp_fastmri_v1_tensorrt.log`: raw C++ inference smoke result.

Historical synthetic reports are kept for traceability and are labeled as synthetic. Use the fastMRI v1 reports for the current project result.

Measurement rules:

- Reports must identify whether the data is synthetic or real fastMRI.
- Jetson latency numbers must include model precision, input shape, command line, and tool path when available.
- Public claims should only use measured numbers that are recorded in this folder.
