# Architecture

## System Story

The project simulates the software shape of an MRI embedded system without requiring real MRI hardware.

1. The RTOS controller runs a programmable pulse sequence and emits timing/status events.
2. The host bridge maps simulated acquisition output to k-space sample batches.
3. The reconstruction service converts k-space data to an image, runs AI reconstruction, and writes DICOM output.
4. Test and reporting tools record timing, latency, PSNR/SSIM, and static-analysis results.

## Modules

```mermaid
flowchart LR
    A["Zephyr RTOS Controller<br/>STM32F4 now / STM32H7 upgrade path"] --> B["UART/USB Bridge"]
    B --> C["K-space Adapter<br/>fastMRI HDF5"]
    C --> D["AI Reconstruction<br/>PyTorch / MONAI"]
    D --> E["ONNX / TensorRT<br/>Jetson Orin Nano"]
    E --> F["DICOM Output<br/>pydicom / DCMTK"]
```

## Design Principles

- Keep real-time control independent from AI reconstruction.
- Prefer C++17 RAII and explicit ownership in host services.
- Keep firmware sequence descriptions small and deterministic.
- Record performance numbers only when measured.
- Treat medical compliance as engineering discipline: traceability, tests, static checks, and clear risk notes.

## Initial Interfaces

Sequence description:

```json
{
  "name": "spin_echo_demo",
  "events": [
    { "t_us": 0, "channel": "rf", "value": 1 },
    { "t_us": 90, "channel": "rf", "value": 0 },
    { "t_us": 120, "channel": "gradient_x", "value": 1 }
  ]
}
```

STM32 UART bridge:

```text
PING
LOAD BEGIN spin_echo_demo 6
LOAD EVENT 0 rf 1
LOAD EVENT 90 rf 0
LOAD END
RUN LOADED
```

The host-side `tools/stm32_sequence_client.py` renders this line protocol from the JSON sequence file. The STM32F407 Zephyr firmware receives commands with interrupt-driven UART RX and reports each scheduled event back over UART.

Inference request:

```text
input: DICOM bytes or normalized k-space tensor
output: reconstructed DICOM bytes and metrics metadata
```
