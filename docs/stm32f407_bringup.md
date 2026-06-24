# STM32F407VGT Bring-Up

## Hardware Status

- Board: STM32F407VGT development board.
- Host serial adapter: CH340 USB serial.
- Detected Windows port: `COM3`.
- Baud used for smoke test: `115200`.
- Some board pins are already connected to a camera and WiFi module, so the first firmware stage intentionally avoids GPIO outputs.

## Current Serial Observation

Before flashing the project firmware, the existing board firmware responded to the host smoke test:

```text
opened COM3 baud=115200
>>> PING
[D: 481.569] enter TX_Mode

[E: 481.571] unkown cmd
>>> STATUS
[E: 482.130] unkown cmd
>>> RUN DEMO
[E: 482.691] unkown cmd
>>> STATUS
[E: 483.791] unkown cmd
```

This confirms that the USB-serial link works, but the board is not yet running the Zephyr MRI sequence controller firmware.

## Firmware Stage 1

The current Zephyr app is UART-only:

- `HELP`
- `PING`
- `STATUS`
- `RUN DEMO`

It prints the built-in spin echo sequence events over UART and does not drive GPIO pins.

## Next Required Tooling

The local workstation currently does not expose these commands:

- `west`
- `pyocd`
- `STM32_Programmer_CLI`

To flash and test on the STM32F407VGT board, install one of the flashing paths:

1. Zephyr + west + Zephyr SDK, then build with an STM32F407-compatible board target.
2. STM32CubeProgrammer CLI, then flash a built `.elf` or `.hex`.
3. pyOCD or OpenOCD with a supported ST-Link/debug probe.

## Planned Bring-Up Steps

1. Confirm the exact board schematic and which UART is connected to CH340.
2. Select or create a Zephyr board definition for STM32F407VG.
3. Build `firmware/zephyr_app`.
4. Flash the board.
5. Run:

```powershell
python tools/stm32_uart_smoke.py --port COM3 --baud 115200
```

6. Confirm expected output includes:

```text
PONG controller=stm32_sequence state=idle
seq_start name=spin_echo_demo events=6
seq_done name=spin_echo_demo total_us=800 runs=1
```
