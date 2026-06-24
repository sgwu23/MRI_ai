# STM32 Sequence Bridge Smoke Report

- Status: `PASS`
- Timestamp: `2026-06-24T17:34:31+08:00`
- Sequence: `firmware\sequences\spin_echo_demo.json`
- Port: `COM3`
- Baud: `57600`
- Load acknowledged: `True`
- Run completed: `True`

## Transcript

```text
opened COM3 baud=57600
>>> PING
cmd_port=usart1 cmd=PING
PONG controller=stm32_sequence state=idle
>>> LOAD BEGIN spin_echo_demo 6
cmd_port=usart1 cmd=LOAD BEGIN spin_echo_demo 6
load_begin name=spin_echo_demo expected=6
>>> LOAD EVENT 0 rf 1
cmd_port=usart1 cmd=LOAD EVENT 0 rf 1
load_event index=0 t_us=0 channel=rf value=1
>>> LOAD EVENT 90 rf 0
cmd_port=usart1 cmd=LOAD EVENT 90 rf 0
load_event index=1 t_us=90 channel=rf value=0
heartbeat state=idle uptime_ms=200042
>>> LOAD EVENT 120 gradient_x 1
cmd_port=usart1 cmd=LOAD EVENT 120 gradient_x 1
load_event index=2 t_us=120 channel=gradient_x value=1
>>> LOAD EVENT 220 gradient_x 0
cmd_port=usart1 cmd=LOAD EVENT 220 gradient_x 0
load_event index=3 t_us=220 channel=gradient_x value=0
>>> LOAD EVENT 400 adc_gate 1
cmd_port=usart1 cmd=LOAD EVENT 400 adc_gate 1
load_event index=4 t_us=400 channel=adc_gate value=1
>>> LOAD EVENT 800 adc_gate 0
cmd_port=usart1 cmd=LOAD EVENT 800 adc_gate 0
load_event index=5 t_us=800 channel=adc_gate value=0
>>> LOAD END
cmd_port=usart1 cmd=LOAD END
load_done name=spin_echo_demo events=6
>>> STATUS
cmd_port=usart1 cmd=STATUS
status state=idle sequence=spin_echo_demo events=6 runs=1 uptime_ms=202916
loaded name=spin_echo_demo ready=1 events=6 expected=6 loading=0
>>> RUN LOADED
cmd_port=usart1 cmd=RUN LOADED
seq_start name=spin_echo_demo events=6
seq_event index=0 t_us=0 channel=rf value=1
seq_event index=1 t_us=90 channel=rf value=0
seq_event index=2 t_us=120 channel=gradient_x value=1
seq_event index=3 t_us=220 channel=gradient_x value=0
seq_event index=4 t_us=400 channel=adc_gate value=1
seq_event index=5 t_us=800 channel=adc_gate value=0
seq_done name=spin_echo_demo total_us=800 runs=2
>>> STATUS
cmd_port=usart1 cmd=STATUS
status state=idle sequence=spin_echo_demo events=6 runs=2 uptime_ms=204510
loaded name=spin_echo_demo ready=1 events=6 expected=6 loading=0
```
