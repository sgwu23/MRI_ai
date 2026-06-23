# Firmware

Zephyr RTOS firmware prototype for an STM32 pulse-sequence controller. The next hardware target is an available STM32F4 board; STM32H7 remains a higher-performance upgrade path.

The first firmware target is a deterministic GPIO pulse player:

1. Parse a small sequence table.
2. Schedule events by microsecond timestamp.
3. Drive GPIO or timer output compare.
4. Report timing statistics over UART.

The code in this folder starts as a portable host-readable scaffold. Board-specific overlays should be added after confirming the exact STM32F4 board model.

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

Before hardware timing tests, validate sequences on the host side and keep all event timestamps monotonic. Real jitter measurements require an STM32 board plus a logic analyzer or oscilloscope; without external measurement hardware, UART logs and GPIO toggling can still validate the software flow.
