from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import AppConfig


@dataclass(frozen=True)
class SupabaseUploadResult:
    status: str
    audio_path: str | None = None
    transcript_path: str | None = None
    error: str | None = None


def upload_recording(
    config: AppConfig,
    *,
    audio_path: Path,
    transcript_path: Path | None,
    transcript_text: str,
    status: str,
    error: str | None,
) -> SupabaseUploadResult:
    if not config.supabase_configured:
        return SupabaseUploadResult(status="skipped")

    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError(
            "The Supabase Python package is not installed. Activate the venv and run "
            "`python -m pip install -r requirements.txt`."
        ) from exc

    today = datetime.now().strftime("%Y-%m-%d")
    remote_audio_path = f"audio/{today}/{audio_path.name}"
    remote_transcript_path = (
        f"transcripts/{today}/{transcript_path.name}" if transcript_path else None
    )

    client = create_client(
        config.supabase_url or "",
        config.supabase_service_role_key or "",
    )

    bucket = client.storage.from_(config.supabase_bucket)

    with audio_path.open("rb") as audio_file:
        bucket.upload(
            remote_audio_path,
            audio_file.read(),
            file_options={"content-type": "audio/mpeg", "upsert": "true"},
        )

    if transcript_path and transcript_path.exists() and remote_transcript_path:
        with transcript_path.open("rb") as transcript_file:
            bucket.upload(
                remote_transcript_path,
                transcript_file.read(),
                file_options={"content-type": "text/plain; charset=utf-8", "upsert": "true"},
            )

    client.table(config.supabase_table).insert(
        {
            "source": config.source_device,
            "audio_path": remote_audio_path,
            "transcript_path": remote_transcript_path,
            "transcript_text": transcript_text,
            "status": status,
            "error": error,
        }
    ).execute()

    return SupabaseUploadResult(
        status="uploaded",
        audio_path=remote_audio_path,
        transcript_path=remote_transcript_path,
    )
