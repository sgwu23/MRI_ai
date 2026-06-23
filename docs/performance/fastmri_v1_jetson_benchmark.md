# fastMRI v1 Jetson Benchmark

## Model

- Checkpoint: `outputs/models/unet_fastmri_v1_best.pth`
- ONNX: `outputs/models/unet_fastmri_v1_best.onnx`
- TensorRT engine: `models/unet_fastmri_v1_best_fp16.engine`
- Input shape: `1x1x320x320`
- Output shape: `1x1x320x320`
- Precision: FP16 TensorRT engine with FP32 input/output tensors

## Training Result

- Dataset split: fastMRI knee singlecoil train/val directories
- Train slices: `10000`
- Validation slices: `1000`
- Acceleration: `4x`
- Completed epochs: `20`
- Validation L1: `0.035437`
- Best model PSNR: `26.49 dB`
- Zero-filled PSNR: `22.87 dB`
- PSNR gain: `+3.62 dB`

## TensorRT Build

- Device: NVIDIA Jetson Orin
- TensorRT version: `10.3.0`
- Engine build time: `83.0994 s`
- Engine size: `0.41238 MiB`
- trtexec throughput: `179.341 qps`
- trtexec host latency: mean `5.65208 ms`, p95 `5.6629 ms`, p99 `5.67871 ms`
- trtexec GPU compute: mean `5.56861 ms`

## C++ Inference Smoke

- Backend: `tensorrt-fp16`
- Accelerated: `1`
- Repeats: `50`
- Warmup: `5`
- Output bytes: `409600`
- Output elements: `102400`
- End-to-end latency: mean `8.30151 ms`, min `6.14912 ms`, max `11.6161 ms`

## Logs

- Training evaluation: `docs/performance/fastmri_v1_eval.md`
- TensorRT build and benchmark: `docs/performance/trtexec_fastmri_v1_fp16.log`
- C++ inference smoke: `docs/performance/cpp_fastmri_v1_tensorrt.log`
