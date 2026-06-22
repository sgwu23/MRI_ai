# MRI-Style Real-Time Control & Edge AI Reconstruction Platform

基于 RTOS 与边缘 AI 的医学影像重建仿真平台。

This repository is a personal embedded medical-imaging prototype aligned with MRI-style software systems: deterministic RTOS control, medical image reconstruction, edge inference, DICOM I/O, and software-quality practices inspired by IEC 62304 and MISRA C++.

## Project Goals

- Build a Zephyr RTOS pulse-sequence controller prototype for STM32H7.
- Train and evaluate a lightweight U-Net for fastMRI-style undersampled MRI reconstruction.
- Export PyTorch models to ONNX, then deploy through TensorRT on Jetson Orin Nano.
- Wrap inference behind a C++ service interface and DICOM pipeline.
- Keep documentation, tests, static analysis, and CI visible from day one.

## Repository Layout

```text
mri-edge-rtos-ai/
  ai_recon/           Python training, dataset adapters, ONNX export
  cpp_inference/      C++17 inference service and DICOM/TensorRT integration
  firmware/           Zephyr RTOS firmware prototype for STM32H7
  docs/               Architecture notes, weekly logs, performance reports
  tests/              Host-side unit tests and smoke tests
  tools/              Developer scripts
```

## Milestones

| Week | Focus | Deliverable |
| --- | --- | --- |
| W1 | MRI basics and baseline | fastMRI data smoke test, zero-filled baseline report |
| W2 | U-Net training | MONAI/PyTorch training pipeline and metrics |
| W3 | ONNX/TensorRT | ONNX export, runtime parity check, Jetson latency table |
| W4 | DICOM and service | DICOM reader/writer and C++ inference API |
| W5 | Zephyr bring-up | STM32H7 hello world, GPIO timing smoke test |
| W6 | Pulse controller | JSON sequence parser and deterministic player |
| W7 | Integration and quality | UART data bridge, tests, static analysis |
| W8 | Packaging | Bilingual README, demo video, resume data |

## Quick Start

Create a Python environment for AI experiments:

```powershell
cd mri-edge-rtos-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ai_recon/requirements.txt
```

Run the current smoke test:

```powershell
python tools/smoke_check.py
```

Run all local checks that do not require Jetson:

```powershell
powershell -ExecutionPolicy Bypass -File tools/run_local_checks.ps1
```

The stopping point before real Jetson work is documented in `docs/jetson_handoff.md`.

Current Jetson milestone:

- TensorRT FP16 engine builds and runs on Jetson Orin.
- C++ TensorRT backend loads the engine and runs inference.
- Synthetic tensor input/output path is proven end-to-end.
- Residual synthetic v2 checkpoint slightly improves over zero-filled baseline on the local synthetic sample; see `docs/performance/synthetic_tensor_eval_v2.md`.

Next training milestone:

- Use fastMRI knee single-coil data for real reconstruction training.
- Follow `docs/cloud_training_fastmri.md` when renting cloud GPU.
- Start with `ai_recon/scripts/train_fastmri_unet.py` on a small HDF5 subset.

## Resume Target

中文简历目标表达：

> 基于 Zephyr RTOS + STM32H7 与 Jetson Orin Nano 构建 MRI 类医学影像系统原型，实现可编程脉冲序列控制、fastMRI 欠采样重建、ONNX/TensorRT 端侧部署、DICOM 数据链路与 C++17 工程化测试。

English resume target:

> Built an MRI-style embedded medical-imaging prototype with Zephyr RTOS on STM32H7 and Jetson Orin Nano, covering programmable pulse-sequence control, fastMRI reconstruction, ONNX/TensorRT edge deployment, DICOM I/O, and C++17 quality practices.
