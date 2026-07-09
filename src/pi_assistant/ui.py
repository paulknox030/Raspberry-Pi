from __future__ import annotations

import sys
import time
import traceback
from dataclasses import dataclass
from textwrap import shorten
from typing import Any, Optional

from . import audio
from . import gpio_button
from . import workflow
from .config import AppConfig, ensure_local_dirs, load_config


@dataclass
class UiState:
    status: str
    timer_seconds: int
    step: str
    latest_transcript: str
    latest_audio: str
    supabase_status: str
    error: Optional[str] = None


class TerminalDashboard:
    def start(self) -> None:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def stop(self) -> None:
        sys.stdout.write("\033[?25h\n")
        sys.stdout.flush()

    def render(self, state: UiState) -> None:
        lines = [
            "PAUL PI ASSISTANT V1",
            "=" * 20,
            "",
            f"Status: {state.status}",
            f"Timer: {_format_timer(state.timer_seconds)}",
            f"Step: {state.step or '-'}",
            "",
            "Latest transcript:",
            state.latest_transcript or "-",
            "",
            f"Latest audio: {state.latest_audio or '-'}",
            f"Supabase: {state.supabase_status}",
            "",
        ]
        if state.error:
            lines.extend(["Error:", state.error, ""])

        lines.extend(
            [
                "Controls:",
                "Press physical button once to start",
                "Press physical button again to stop",
                "Ctrl+C to exit",
            ]
        )

        sys.stdout.write("\033[2J\033[H")
        sys.stdout.write("\n".join(lines))
        sys.stdout.write("\n")
        sys.stdout.flush()


def _format_timer(seconds: int) -> str:
    minutes = max(0, seconds) // 60
    remaining_seconds = max(0, seconds) % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"


def _initial_supabase_status(config: AppConfig) -> str:
    if config.supabase_configured:
        return "ready"
    return "not configured"


def _supabase_status(config: AppConfig, result: workflow.WorkflowResult) -> str:
    if result.supabase_status == "uploaded":
        return "uploaded"
    if result.supabase_status == "error":
        return "error"
    if result.supabase_status == "skipped":
        if config.supabase_configured:
            return "upload skipped"
        return "upload skipped"
    return result.supabase_status or _initial_supabase_status(config)


def _transcript_preview(text: str) -> str:
    if not text.strip():
        return "-"
    return shorten(" ".join(text.split()), width=200, placeholder="...")


def _new_state(config: AppConfig) -> UiState:
    return UiState(
        status="WAITING",
        timer_seconds=0,
        step="",
        latest_transcript="-",
        latest_audio="-",
        supabase_status=_initial_supabase_status(config),
        error=None,
    )


def _pause_with_screen(render: TerminalDashboard, state: UiState, seconds: float) -> None:
    end_at = time.monotonic() + seconds
    while time.monotonic() < end_at:
        render.render(state)
        time.sleep(0.25)


def _wait_until_button_rearmed(
    button: Any,
    render: TerminalDashboard,
    state: UiState,
    stable_seconds: float = 0.8,
) -> None:
    released_since: Optional[float] = None
    state.step = "release button"

    while True:
        render.render(state)
        if getattr(button, "is_pressed", False):
            released_since = None
        else:
            if released_since is None:
                released_since = time.monotonic()
            if time.monotonic() - released_since >= stable_seconds:
                state.step = ""
                return
        time.sleep(0.1)


def _wait_for_button_release_with_timer(
    button: Any,
    recording: audio.ActiveRecording,
    render: TerminalDashboard,
    state: UiState,
) -> None:
    while getattr(button, "is_pressed", False):
        state.timer_seconds = int(time.monotonic() - recording.started_at)
        render.render(state)
        time.sleep(0.1)


def _wait_for_stop_press(
    button: Any,
    recording: audio.ActiveRecording,
    render: TerminalDashboard,
    state: UiState,
) -> None:
    while True:
        state.timer_seconds = int(time.monotonic() - recording.started_at)
        render.render(state)
        if getattr(button, "is_pressed", False):
            return
        time.sleep(0.2)


def _show_error(
    render: TerminalDashboard,
    state: UiState,
    message: str,
    debug: bool,
) -> None:
    if debug:
        traceback.print_exc()
    state.status = "ERROR"
    state.step = ""
    state.error = message
    render.render(state)
    time.sleep(3)


def run(debug: bool = False) -> int:
    config = load_config()
    ensure_local_dirs(config)
    button = gpio_button.create_button()
    render = TerminalDashboard()
    state = _new_state(config)
    active: Optional[audio.ActiveRecording] = None

    try:
        render.start()
        while True:
            state.status = "WAITING"
            state.timer_seconds = 0
            state.step = ""
            state.error = None
            if state.supabase_status == "upload skipped":
                state.supabase_status = _initial_supabase_status(config)
            render.render(state)

            gpio_button.wait_for_fresh_press(button)

            try:
                active = audio.start_recording(config)
                state.status = "RECORDING"
                state.step = ""
                state.latest_audio = str(active.audio_path)
                state.timer_seconds = 0
                render.render(state)

                _wait_for_button_release_with_timer(button, active, render, state)
                _wait_for_stop_press(button, active, render, state)

                state.status = "PROCESSING"
                state.step = "stopping"
                render.render(state)
                result = audio.stop_recording(active)
                active = None
                state.latest_audio = str(result.audio_path)
                state.timer_seconds = int(result.duration_seconds)

                def on_progress(step: str) -> None:
                    state.status = "PROCESSING"
                    state.step = step
                    render.render(state)

                workflow_result = workflow.process_recording(
                    config,
                    result,
                    debug=debug,
                    progress=on_progress,
                    printer=None,
                )
                state.latest_transcript = _transcript_preview(
                    workflow_result.transcript_text
                )
                state.latest_audio = str(workflow_result.audio_path)
                state.supabase_status = _supabase_status(config, workflow_result)
                state.step = ""
                state.error = workflow_result.error
                if workflow_result.status == "error":
                    state.status = "ERROR"
                else:
                    state.status = "DONE"
                render.render(state)
                _pause_with_screen(render, state, 2)
                _wait_until_button_rearmed(button, render, state)
            except Exception as exc:
                if active is not None:
                    try:
                        audio.stop_recording(active)
                    except Exception:
                        if debug:
                            traceback.print_exc()
                    active = None
                _show_error(render, state, str(exc), debug)
                _wait_until_button_rearmed(button, render, state)
    except KeyboardInterrupt:
        if active is not None:
            try:
                audio.stop_recording(active)
            except Exception:
                if debug:
                    traceback.print_exc()
        return 0
    finally:
        button.close()
        render.stop()
