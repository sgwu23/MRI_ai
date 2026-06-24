# Firmware

Zephyr RTOS firmware prototype for an STM32 pulse-sequence controller. The current hardware target is an STM32F407VGT development board; STM32H7 remains a higher-performance upgrade path.

The first firmware target is a UART-only deterministic sequence controller:

1. Accept a small command set over USART1 at 57600 baud.
2. Receive commands with UART interrupt-driven RX and line buffering.
3. Load a JSON-defined sequence from a host-side client.
4. Play a built-in or loaded spin echo sequence by microsecond timestamp.
5. Report each event over UART without driving GPIO pins yet.
6. Keep GPIO outputs disabled until the camera and WiFi module pin usage is confirmed.

The current STM32F407VGT bring-up uses the `olimex_stm32_h407` Zephyr board target plus a local overlay for USART1, 57600 baud, and an HSI-based clock configuration.

## UART Command Set

The firmware currently supports:

```text
HELP
PING
STATUS
RUN DEMO
LOAD BEGIN <name> <count>
LOAD EVENT <t_us> <channel> <value>
LOAD END
RUN LOADED
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
python tools/stm32_uart_smoke.py --port COM3 --baud 57600
```

To load a sequence JSON and run it through the firmware protocol:

```powershell
python tools/stm32_sequence_client.py firmware/sequences/spin_echo_demo.json --port COM3 --baud 57600
```

If `pyserial` is missing:

```powershell
pip install pyserial
```

## Zephyr Build Example

The local Windows helper copies the app into a temporary no-space path before building because the repository path contains a space:

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_zephyr_stm32f407.ps1
```

The generated FlyMCU image is `build/zephyr-stm32f407/zephyr/zephyr.hex`.

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
