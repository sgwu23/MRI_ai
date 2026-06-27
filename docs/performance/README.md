# Performance Reports

This folder contains measured training, reconstruction, and deployment reports.

Recommended reading order:

1. `fastmri_v1_eval.md`: formal fastMRI v1 validation result.
2. `fastmri_v1_jetson_benchmark.md`: summary of ONNX/TensorRT deployment on Jetson.
3. `stm32_sequence_bridge.md`: raw STM32 UART sequence bridge smoke transcript.
4. `stm32_gpio_logic_capture.md`: STM32 GPIO timing capture measured with a Kingst LA1010.
5. `trtexec_fastmri_v1_fp16.log`: raw TensorRT benchmark log.
6. `cpp_fastmri_v1_tensorrt.log`: raw C++ inference smoke result.

Historical synthetic reports are kept for traceability and are labeled as synthetic. Use the fastMRI v1 reports for the current project result.

Measurement rules:

- Reports must identify whether the data is synthetic or real fastMRI.
- Jetson latency numbers must include model precision, input shape, command line, and tool path when available.
- STM32 reports must include the COM port, baud rate, loaded sequence, and raw UART transcript.
- Logic-analyzer reports must include pin mapping, sample rate, threshold, measured pulse widths, and the raw capture artifact when available.
- Public claims should only use measured numbers that are recorded in this folder.
