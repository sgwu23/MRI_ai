from __future__ import annotations

import argparse
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the STM32 UART sequence controller.")
    parser.add_argument("--port", required=True, help="Serial port, for example COM6 on Windows.")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=0.2)
    parser.add_argument("--char-delay", type=float, default=0.0, help="Optional delay between transmitted characters.")
    args = parser.parse_args()

    try:
        import serial
    except ImportError:
        print("pyserial is required: pip install pyserial", file=sys.stderr)
        return 2

    with serial.Serial(args.port, args.baud, timeout=args.timeout) as connection:
        print(f"opened {args.port} baud={args.baud}")
        time.sleep(0.5)
        drain(connection, duration=0.5)
        for command in ("PING", "STATUS", "RUN DEMO", "STATUS"):
            print(f">>> {command}")
            write_command(connection, command, args.char_delay)
            drain(connection, duration=1.0 if command == "RUN DEMO" else 0.5)
    return 0


def write_command(connection, command: str, char_delay: float) -> None:
    payload = (command + "\r\n").encode("ascii")
    if char_delay <= 0.0:
        connection.write(payload)
        connection.flush()
        return

    for byte in payload:
        connection.write(bytes([byte]))
        connection.flush()
        time.sleep(char_delay)


def drain(connection, duration: float) -> None:
    deadline = time.time() + duration
    while time.time() < deadline:
        line = connection.readline()
        if line:
            print(line.decode("utf-8", errors="replace").rstrip())


if __name__ == "__main__":
    raise SystemExit(main())
