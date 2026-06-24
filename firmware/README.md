# Firmware

Zephyr RTOS firmware prototype for an STM32 pulse-sequence controller. The next hardware target is the available STM32F407VGT board; STM32H7 remains a higher-performance upgrade path.

The first firmware target is a UART-only deterministic sequence controller:

1. Accept a small command set over the Zephyr console UART.
2. Play a built-in spin echo demo sequence by microsecond timestamp.
3. Report each event over UART without driving GPIO pins yet.
4. Keep GPIO outputs disabled until the camera and WiFi module pin usage is confirmed.

The code in this folder starts as a portable host-readable scaffold. Board-specific overlays should be added after confirming the exact STM32F4 board model.

## UART Command Set

The firmware currently supports:

```text
HELP
PING
STATUS
RUN DEMO
```

Expected `RUN DEMO` output:

```text
seq_start name=spin_echo_demo events=6
seq_event index=0 t_us=0 channel=rf value=1
seq_event index=1 t_us=90 channel=rf value=0
seq_event index=2 t_us=120 channel=gradient_x value=1
seq_event index=3 t_us=220 channel=gradient_x value=0
seq_event index=4 t_us=400 channel=adc_gate value=1
seq_event index=5 t_us=800 channel=adc_gate value=0
seq_done name=spin_echo_demo total_us=800 runs=1
```

## Host Smoke Test

After flashing the Zephyr app and identifying the COM port:

```powershell
python tools/stm32_uart_smoke.py --port COM6 --baud 115200
```

If `pyserial` is missing:

```powershell
pip install pyserial
```

## Zephyr Build Example

For an STM32F407VG-class board, start with a close Zephyr board target such as `stm32f4_disco` when the custom board does not yet have a dedicated board definition:

```bash
west build -b stm32f4_disco firmware/zephyr_app
```

Use the exact board target or a custom board definition once the development board schematic and pin map are confirmed.

## Host-First Sequence Contract

The first firmware contract is intentionally simple:

```json
{
  "name": "spin_echo_demo",
  "events": [
    { "t_us": 0, "channel": "rf", "value": 1 },
    { "t_us": 90, "channel": "rf", "value": 0 }
  ]
}
```

Before hardware timing tests, validate sequences on the host side and keep all event timestamps monotonic. Real jitter measurements require an STM32 board plus a logic analyzer or oscilloscope; without external measurement hardware, UART logs can still validate the software flow.
