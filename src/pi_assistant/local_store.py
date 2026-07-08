from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .audio import timestamp_for_filename
from .config import AppConfig, ensure_local_dirs


@dataclass(frozen=True)
class LocalRecordInput:
    audio_path: Path
    transcript_path: Optional[Path]
    transcript_text: str
    status: str
    error: Optional[str]
    supabase_status: str
    supabase_audio_path: Optional[str] = None
    supabase_transcript_path: Optional[str] = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_transcript(config: AppConfig, transcript_text: str) -> Path:
    ensure_local_dirs(config)
    transcript_path = (
        config.transcripts_dir / f"transcript_{timestamp_for_filename()}.txt"
    )
    transcript_path.write_text(transcript_text, encoding="utf-8")
    return transcript_path


def append_inbox_record(config: AppConfig, record_input: LocalRecordInput) -> dict[str, Any]:
    ensure_local_dirs(config)
    record = {
        "id": str(uuid.uuid4()),
        "created_at": utc_now_iso(),
        "source": config.source_device,
        "audio_path": str(record_input.audio_path),
        "transcript_path": str(record_input.transcript_path)
        if record_input.transcript_path
        else None,
        "transcript_text": record_input.transcript_text,
        "status": record_input.status,
        "error": record_input.error,
        "supabase_status": record_input.supabase_status,
        "supabase_audio_path": record_input.supabase_audio_path,
        "supabase_transcript_path": record_input.supabase_transcript_path,
    }

    with config.inbox_path.open("a", encoding="utf-8") as inbox_file:
        inbox_file.write(json.dumps(record, ensure_ascii=True) + "\n")

    return record


def read_latest_inbox(config: AppConfig, limit: int = 5) -> list[dict[str, Any]]:
    if not config.inbox_path.exists():
        return []

    records: list[dict[str, Any]] = []
    with config.inbox_path.open("r", encoding="utf-8") as inbox_file:
        for line in inbox_file:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return list(reversed(records[-limit:]))
