from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from validate_sequence import validate


TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+$")


def render_load_commands(sequence: dict[str, Any]) -> list[str]:
    name = str(sequence["name"])
    events = sequence["events"]
    if not TOKEN_PATTERN.match(name):
        raise ValueError(f"sequence name is not UART-token safe: {name!r}")

    commands = [f"LOAD BEGIN {name} {len(events)}"]
    for event in events:
        channel = str(event["channel"])
        if not TOKEN_PATTERN.match(channel):
            raise ValueError(f"channel name is not UART-token safe: {channel!r}")
        commands.append(f"LOAD EVENT {int(event['t_us'])} {channel} {int(event['value'])}")
    commands.append("LOAD END")
    return commands


def load_sequence(path: Path) -> dict[str, Any]:
    errors = validate(path)
    if errors:
        raise ValueError("; ".join(errors))
    return json.loads(path.read_text(encoding="utf-8"))


def write_line(connection: Any, line: str, char_delay: float) -> None:
    payload = (line + "\r\n").encode("ascii")
    if char_delay <= 0.0:
        connection.write(payload)
        connection.flush()
        return

    for byte in payload:
        connection.write(bytes([byte]))
        connection.flush()
        time.sleep(char_delay)


def drain(connection: Any, duration: float) -> list[str]:
    lines: list[str] = []
    deadline = time.time() + duration
    while time.time() < deadline:
        line = connection.readline()
        if not line:
            continue
        decoded = line.decode("utf-8", errors="replace").rstrip()
        lines.append(decoded)
        print(decoded)
    return lines


def run_client(port: str, baud: int, sequence_path: Path, timeout: float, char_delay: float) -> int:
    try:
        import serial
    except ImportError:
        print("pyserial is required: pip install pyserial", file=sys.stderr)
        return 2

    sequence = load_sequence(sequence_path)
    commands = ["PING", *render_load_commands(sequence), "STATUS", "RUN LOADED", "STATUS"]

    with serial.Serial(port, baud, timeout=timeout) as connection:
        print(f"opened {port} baud={baud}")
        time.sleep(0.5)
        drain(connection, duration=0.5)
        for command in commands:
            print(f">>> {command}")
            write_line(connection, command, char_delay)
            wait = 1.0 if command == "RUN LOADED" else 0.35
            drain(connection, duration=wait)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Load and run a JSON pulse sequence on the STM32 controller.")
    parser.add_argument("sequence", type=Path, help="Sequence JSON, for example firmware/sequences/spin_echo_demo.json.")
    parser.add_argument("--port", required=True, help="Serial port, for example COM3 on Windows.")
    parser.add_argument("--baud", type=int, default=57600)
    parser.add_argument("--timeout", type=float, default=0.2)
    parser.add_argument("--char-delay", type=float, default=0.0)
    args = parser.parse_args()

    try:
        return run_client(args.port, args.baud, args.sequence, args.timeout, args.char_delay)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
