import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from stm32_sequence_client import render_load_commands


def test_render_load_commands_for_spin_echo_sequence():
    sequence = {
        "name": "spin_echo_demo",
        "events": [
            {"t_us": 0, "channel": "rf", "value": 1},
            {"t_us": 90, "channel": "rf", "value": 0},
        ],
    }

    assert render_load_commands(sequence) == [
        "LOAD BEGIN spin_echo_demo 2",
        "LOAD EVENT 0 rf 1",
        "LOAD EVENT 90 rf 0",
        "LOAD END",
    ]


def test_render_load_commands_rejects_whitespace_tokens():
    sequence = {
        "name": "bad name",
        "events": [{"t_us": 0, "channel": "rf", "value": 1}],
    }

    try:
        render_load_commands(sequence)
    except ValueError as exc:
        assert "UART-token safe" in str(exc)
    else:
        raise AssertionError("expected invalid sequence name to be rejected")
