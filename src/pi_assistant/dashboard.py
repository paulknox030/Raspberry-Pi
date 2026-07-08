from __future__ import annotations

from textwrap import shorten
from typing import Optional

from .config import APP_NAME, AppConfig, ensure_local_dirs
from .local_store import read_latest_inbox


def _preview(text: Optional[str]) -> str:
    if not text:
        return "(no transcript)"
    return shorten(" ".join(text.split()), width=200, placeholder="...")


def render_dashboard(config: AppConfig, limit: int = 5) -> str:
    ensure_local_dirs(config)
    records = read_latest_inbox(config, limit=limit)

    lines = [
        APP_NAME,
        "=" * len(APP_NAME),
        "",
        f"Local inbox: {config.inbox_path}",
        "",
        f"Latest {limit} entries",
        "-" * 16,
    ]

    if not records:
        lines.append("No local inbox entries yet. Run `python -m pi_assistant.main record`.")
        return "\n".join(lines)

    for record in records:
        lines.extend(
            [
                f"Timestamp: {record.get('created_at', '(missing)')}",
                f"Status: {record.get('status', '(missing)')}",
                f"Supabase: {record.get('supabase_status', 'unknown')}",
                f"Transcript: {_preview(record.get('transcript_text'))}",
                f"Audio: {record.get('audio_path', '(missing)')}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def print_dashboard(config: AppConfig, limit: int = 5) -> None:
    print(render_dashboard(config, limit=limit))
