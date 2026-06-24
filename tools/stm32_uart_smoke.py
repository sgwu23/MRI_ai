from __future__ import annotations

import argparse
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the STM32 UART sequence controller.")
    parser.add_argument("--port", required=True, help="Serial port, for example COM6 on Windows.")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=0.2)
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
            connection.write((command + "\r\n").encode("ascii"))
            connection.flush()
            drain(connection, duration=1.0 if command == "RUN DEMO" else 0.5)
    return 0


def drain(connection, duration: float) -> None:
    deadline = time.time() + duration
    while time.time() < deadline:
        line = connection.readline()
        if line:
            print(line.decode("utf-8", errors="replace").rstrip())


if __name__ == "__main__":
    raise SystemExit(main())
