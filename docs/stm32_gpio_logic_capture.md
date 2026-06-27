# STM32F407 GPIO Logic Capture

This note records the temporary GPIO auto-wave firmware used for logic-analyzer validation. The default Zephyr app remains the UART sequence bridge; this capture was a hardware validation experiment used to prove that the same spin-echo event schedule can be observed as MCU pin timing.

## Firmware Mode

The capture firmware was an auto-running GPIO waveform build:

| Sequence channel | STM32 pin | Expected high window |
| --- | --- | --- |
| `rf` | `PA9` | `0 us` to `90 us` |
| `gradient_x` | `PD5` | `120 us` to `220 us` |
| `adc_gate` | `PA11` | `400 us` to `800 us` |

The sequence repeats every about `20 ms`. Runtime USART1 was disabled in the capture build because `PA9` was used as a GPIO output. Serial flashing still uses the STM32 ROM bootloader before the application starts.

## Wiring

- Connect analyzer `GND` to STM32 board `GND`.
- Connect analyzer `CH0` to `PA9`.
- Connect analyzer `CH1` to `PD5`.
- Connect analyzer `CH2` to `PA11`.
- `PA10` is no longer used by the waveform build, so the USB-serial adapter TX line is less likely to interfere with capture.

## Kingst LA1010 Settings

Recommended first capture:

- Channels: enable only `CH0`, `CH1`, `CH2`.
- Threshold: `CMOS 3.3 V` or TTL-compatible threshold.
- Sample rate: `10 MHz` minimum; `20 MHz` is a good first setting.
- Capture depth/time: at least `50 ms` so multiple repeated frames are visible.
- Trigger: rising edge on `CH0` / `PA9`.
- Pre-trigger: `10%` to `20%`.

Expected pulse widths at `20 MHz`:

- `PA9`: about `90 us`, roughly `1800` samples.
- `PD5`: about `100 us`, roughly `2000` samples.
- `PA11`: about `400 us`, roughly `8000` samples.

If no waveform appears, first check common ground and whether the board actually booted from Flash with `BOOT0 = 0`.
If the `PA11` channel is noisy or unavailable, check whether USB hardware on the board is connected to the same pin.

## Captured Artifacts

- Screenshot: `docs/assets/stm32_gpio_logic_capture_pa9_pd5_pa11.png`
- Raw KingstVIS capture: `docs/assets/stm32_gpio_logic_capture_pa9_pd5_pa11.kvdat`
- Measurement report: `docs/performance/stm32_gpio_logic_capture.md`
