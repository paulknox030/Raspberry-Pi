from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import AppConfig, ensure_local_dirs


@dataclass
class ActiveRecording:
    process: subprocess.Popen[bytes]
    audio_path: Path
    started_at: float
    log_file: object


@dataclass(frozen=True)
class RecordingResult:
    audio_path: Path
    duration_seconds: float


def timestamp_for_filename() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def arecord_available() -> bool:
    return shutil.which("arecord") is not None


def list_audio_devices() -> str:
    if not arecord_available():
        return (
            "arecord was not found. Install alsa-utils on the Raspberry Pi, then run "
            "`arecord -l` again."
        )

    result = subprocess.run(
        ["arecord", "-l"],
        check=False,
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "").strip()
    error = (result.stderr or "").strip()
    if result.returncode != 0:
        return f"arecord -l failed.\n{error or output}"
    return output or "No audio capture devices were listed by arecord."


def _new_audio_path(config: AppConfig, prefix: str = "recording") -> Path:
    return config.audio_dir / f"{prefix}_{timestamp_for_filename()}.mp3"


def _new_log_path(config: AppConfig, prefix: str) -> Path:
    return config.logs_dir / f"{prefix}_{timestamp_for_filename()}.log"


def _ffmpeg_command(config: AppConfig, output_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-f",
        "alsa",
        "-i",
        config.mic_device,
        "-ac",
        str(config.channels),
        "-ar",
        str(config.sample_rate),
        "-b:a",
        config.audio_bitrate,
        str(output_path),
    ]


def start_recording(
    config: AppConfig, output_path: Optional[Path] = None
) -> ActiveRecording:
    ensure_local_dirs(config)
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg was not found. Install ffmpeg and try again.")

    audio_path = output_path or _new_audio_path(config)
    log_path = _new_log_path(config, "ffmpeg_record")
    log_file = log_path.open("ab")
    command = _ffmpeg_command(config, audio_path)

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=log_file,
            stderr=log_file,
        )
    except Exception:
        log_file.close()
        raise

    time.sleep(0.5)
    if process.poll() is not None:
        log_file.close()
        raise RuntimeError(
            "ffmpeg stopped immediately. Check MIC_DEVICE, microphone connection, "
            f"and the ffmpeg log at {log_path}."
        )

    return ActiveRecording(
        process=process,
        audio_path=audio_path,
        started_at=time.monotonic(),
        log_file=log_file,
    )


def stop_recording(recording: ActiveRecording) -> RecordingResult:
    process = recording.process

    try:
        if process.stdin:
            process.stdin.write(b"q")
            process.stdin.flush()
            process.stdin.close()
        process.wait(timeout=8)
    except Exception:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    finally:
        try:
            recording.log_file.close()
        except Exception:
            pass

    duration = max(0.0, time.monotonic() - recording.started_at)
    if not recording.audio_path.exists() or recording.audio_path.stat().st_size == 0:
        raise RuntimeError(
            "Recording did not create a usable audio file. Check the mic device, "
            "ffmpeg installation, and ALSA device name."
        )
    return RecordingResult(audio_path=recording.audio_path, duration_seconds=duration)


def record_for_seconds(config: AppConfig, seconds: int) -> RecordingResult:
    ensure_local_dirs(config)
    if seconds <= 0:
        raise ValueError("--seconds must be greater than 0.")
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg was not found. Install ffmpeg and try again.")

    audio_path = _new_audio_path(config, prefix="test")
    log_path = _new_log_path(config, "ffmpeg_test")
    base_command = _ffmpeg_command(config, audio_path)
    command = base_command[:-1] + ["-t", str(seconds), str(audio_path)]

    started_at = time.monotonic()
    with log_path.open("ab") as log_file:
        result = subprocess.run(
            command,
            check=False,
            stdout=log_file,
            stderr=log_file,
            timeout=seconds + 20,
        )

    if result.returncode != 0:
        raise RuntimeError(
            "ffmpeg test recording failed. Check MIC_DEVICE, microphone connection, "
            f"and the ffmpeg log at {log_path}."
        )
    if not audio_path.exists() or audio_path.stat().st_size == 0:
        raise RuntimeError(
            "Test recording did not create a usable audio file. Check the mic device."
        )

    return RecordingResult(
        audio_path=audio_path,
        duration_seconds=max(0.0, time.monotonic() - started_at),
    )
