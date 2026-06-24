# STM32F407VGT Bring-Up

## Hardware Status

- Board: STM32F407VGT development board.
- Host serial adapter: CH340 USB serial.
- Detected Windows port: `COM3`.
- Baud used for smoke test: `57600`.
- Some board pins are already connected to a camera and WiFi module, so the first firmware stage intentionally avoids GPIO outputs.

## Initial Serial Observation

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

This confirmed that the USB-serial link worked, but the board was not yet running the Zephyr MRI sequence controller firmware.

## Verified Zephyr Smoke Test

After flashing the Zephyr firmware and returning `BOOT0` to `0`, the board booted from user Flash and passed the normal, no-delay smoke test over USART1:

```text
mri_sequence_controller board=stm32f407vg mode=irq_uart
uart_irq active=usart1,usart2,usart3,usart6 baud=57600
cmd_port=usart1 cmd=PING
PONG controller=stm32_sequence state=idle
cmd_port=usart1 cmd=STATUS
status state=idle sequence=spin_echo_demo events=6 runs=0
cmd_port=usart1 cmd=RUN DEMO
seq_start name=spin_echo_demo events=6
seq_done name=spin_echo_demo total_us=800 runs=1
```

## Firmware Stage 1

The current Zephyr app is UART-only:

- `HELP`
- `PING`
- `STATUS`
- `RUN DEMO`

It prints the built-in spin echo sequence events over UART and does not drive GPIO pins.

## Zephyr Build Status

Local Zephyr tooling has been installed outside the repository:

- Conda environment: `D:\A_work\zephyr-env`
- Zephyr workspace: `D:\A_work\zephyrproject`
- Zephyr SDK: `D:\A_work\zephyr-sdk`

The project path contains a space (`project 4Autumn`), which can break Zephyr Kconfig path parsing on Windows. The helper script copies the Zephyr app into a temporary no-space path before building.

Build command:

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_zephyr_stm32f407.ps1
```

Current verified build target:

- Zephyr board: `olimex_stm32_h407`
- MCU qualifier: `stm32f407xx`
- Console UART: USART1, TX `PA9`, RX `PA10`, `57600`
- Clock overlay: internal HSI `16 MHz`, PLL `M=16`, `N=336`, `P=2`, target system clock `168 MHz`
- RX path: UART interrupt-driven receive with line buffering
- GPIO/timer outputs: disabled in the stable firmware image
- Firmware image for FlyMCU: `build\zephyr-stm32f407\zephyr\zephyr.hex`
- Last local build size: FLASH `23516 B`, RAM `8640 B`

Note: `stm32f4_disco` was not used because the installed Zephyr snapshot references a missing board pinctrl include. `olimex_stm32_h407` is still an STM32F407 target and is sufficient for the UART-only firmware stage.

Note: The `12.000` marking near the USB-serial area may belong to the USB-serial chip clock, not the STM32 HSE. The firmware intentionally uses HSI for this stage to avoid board-variant crystal assumptions.

## FlyMCU Flashing Steps

1. Connect the USB-serial adapter to the STM32 bootloader UART.
   - The current Zephyr console overlay uses USART1: board `PA9` to USB-serial RX, board `PA10` to USB-serial TX, and common GND.
   - This matches the common STM32F4 system bootloader UART used by FlyMCU.
2. Set `BOOT0 = 1`.
3. Press reset or power-cycle the board so it enters the STM32 system bootloader.
4. Open FlyMCU.
5. Select port `COM3`. `57600` was stable locally; the FlyMCU flashing baud does not need to match the firmware runtime baud.
6. Select `build\zephyr-stm32f407\zephyr\zephyr.hex`.
7. Start flashing.
8. After flashing succeeds, set `BOOT0 = 0`.
9. Press reset or power-cycle again to boot the project firmware.

## Smoke Test

Run:

```powershell
python tools/stm32_uart_smoke.py --port COM3 --baud 57600
```

Confirm expected output includes:

```text
PONG controller=stm32_sequence state=idle
seq_start name=spin_echo_demo events=6
seq_done name=spin_echo_demo total_us=800 runs=1
```

## Host Sequence Client

The next-stage host client loads a JSON sequence file and sends it through the STM32 line protocol:

```powershell
python tools/stm32_sequence_client.py firmware/sequences/spin_echo_demo.json --port COM3 --baud 57600
```

To save the transcript as a project report:

```powershell
python tools/stm32_sequence_client.py firmware/sequences/spin_echo_demo.json --port COM3 --baud 57600 --report docs/performance/stm32_sequence_bridge.md
```

Expected output includes:

```text
load_begin name=spin_echo_demo expected=6
load_event index=0 t_us=0 channel=rf value=1
load_done name=spin_echo_demo events=6
loaded name=spin_echo_demo ready=1 events=6 expected=6 loading=0
seq_start name=spin_echo_demo events=6
seq_done name=spin_echo_demo total_us=800 runs=1
```

This has been verified on the STM32F407VGT board through `COM3` at `57600` baud with the normal, no-delay host client.

## Logic Analyzer Follow-Up

The stable firmware image does not drive GPIO pins. This preserves SWD pins (`PA13/PA14`) and avoids interfering with existing camera/WiFi wiring.

For a future logic-analyzer stage, first identify three safe exposed pins that do not overlap with USART1 (`PA9/PA10`), USB, BOOT0, NRST, SWD, camera, or WiFi. Then map `rf`, `gradient_x`, and `adc_gate` to GPIO or timer outputs and capture the expected `spin_echo_demo` windows:

| Channel | High interval |
| --- | --- |
| `rf` | `0 us` to `90 us` |
| `gradient_x` | `120 us` to `220 us` |
| `adc_gate` | `400 us` to `800 us` |

If FlyMCU flashes successfully but this smoke test still shows the old `unkown cmd` firmware response, the board did not boot the new image. Recheck `BOOT0`, reset timing, selected hex file, and whether flash erase/program completed.

If the smoke test times out with no output after flashing, first check the runtime UART pins. The current image uses USART1 `PA9/PA10`. If there is still no output, recheck BOOT0 reset state, TX/RX crossing, and whether the CH340 is connected to another UART.

If command responses only work with `--char-delay`, rebuild and flash the interrupt-driven firmware. The polling prototype could drop bursty RX bytes, while the current firmware drains RX from the UART interrupt path.
