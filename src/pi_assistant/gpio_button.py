from __future__ import annotations

from time import sleep
from typing import Any


def create_button() -> Any:
    try:
        from gpiozero import Button
    except ImportError as exc:
        raise RuntimeError(
            "gpiozero is not installed. On the Raspberry Pi, run "
            "`bash scripts/setup_pi.sh`, then activate `.venv` again."
        ) from exc

    return Button(17, pull_up=True, bounce_time=0.3)


def wait_for_fresh_press(button: Any) -> None:
    if getattr(button, "is_pressed", False):
        button.wait_for_release()
        sleep(0.05)
    button.wait_for_press()
