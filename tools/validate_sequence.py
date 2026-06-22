from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if not data.get("name"):
        errors.append("missing sequence name")

    events = data.get("events")
    if not isinstance(events, list) or not events:
        errors.append("events must be a non-empty list")
        return errors

    previous_time = -1
    for index, event in enumerate(events):
        for key in ("t_us", "channel", "value"):
            if key not in event:
                errors.append(f"event {index} missing {key}")
        t_us = event.get("t_us")
        if not isinstance(t_us, int) or t_us < 0:
            errors.append(f"event {index} t_us must be a non-negative integer")
        elif t_us < previous_time:
            errors.append(f"event {index} timestamp is not monotonic")
        previous_time = t_us if isinstance(t_us, int) else previous_time
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sequence", type=Path)
    args = parser.parse_args()

    errors = validate(args.sequence)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"valid sequence: {args.sequence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
