from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig


MAX_AUDIO_BYTES = int(24.5 * 1024 * 1024)


@dataclass(frozen=True)
class TranscriptionResult:
    transcript_text: str
    status: str
    error: str | None = None


def _response_to_text(response: object) -> str:
    if isinstance(response, str):
        return response.strip()
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text.strip()
    if isinstance(response, dict) and isinstance(response.get("text"), str):
        return response["text"].strip()
    return str(response).strip()


def transcribe_audio(audio_path: Path, config: AppConfig) -> TranscriptionResult:
    if not config.openai_api_key:
        return TranscriptionResult(
            transcript_text="",
            status="missing_openai_key",
            error="OPENAI_API_KEY is not configured, skipped transcription.",
        )

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")
    file_size = audio_path.stat().st_size
    if file_size <= 0:
        raise ValueError(f"Audio file is empty: {audio_path}")
    if file_size > MAX_AUDIO_BYTES:
        raise ValueError(
            "Audio file is larger than the V1 transcription limit of 24.5MB. "
            "Record a shorter clip and try again."
        )

    try:
        from openai import BadRequestError, OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The OpenAI Python package is not installed. Activate the venv and run "
            "`python -m pip install -r requirements.txt`."
        ) from exc

    client = OpenAI(api_key=config.openai_api_key)

    try:
        with audio_path.open("rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=config.transcription_model,
                file=audio_file,
                response_format="text",
            )
    except BadRequestError as exc:
        if "response_format" not in str(exc):
            raise
        with audio_path.open("rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=config.transcription_model,
                file=audio_file,
            )

    return TranscriptionResult(
        transcript_text=_response_to_text(response),
        status="new",
        error=None,
    )
