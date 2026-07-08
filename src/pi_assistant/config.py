from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "Paul Pi Assistant V1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    data_dir: Path
    audio_dir: Path
    transcripts_dir: Path
    inbox_path: Path
    logs_dir: Path
    openai_api_key: str | None
    supabase_url: str | None
    supabase_service_role_key: str | None
    supabase_bucket: str
    supabase_table: str
    mic_device: str
    audio_bitrate: str
    sample_rate: int
    channels: int
    transcription_model: str
    source_device: str

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)


def _load_dotenv(project_root: Path) -> bool:
    env_path = project_root / ".env"
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    return load_dotenv(env_path)


def _optional_env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer. Current value: {raw_value!r}") from exc


def load_config() -> AppConfig:
    project_root = PROJECT_ROOT
    _load_dotenv(project_root)

    data_dir = project_root / "data"
    audio_dir = data_dir / "audio"
    transcripts_dir = data_dir / "transcripts"
    inbox_path = data_dir / "inbox.jsonl"
    logs_dir = project_root / "logs"

    return AppConfig(
        project_root=project_root,
        data_dir=data_dir,
        audio_dir=audio_dir,
        transcripts_dir=transcripts_dir,
        inbox_path=inbox_path,
        logs_dir=logs_dir,
        openai_api_key=_optional_env("OPENAI_API_KEY"),
        supabase_url=_optional_env("SUPABASE_URL"),
        supabase_service_role_key=_optional_env("SUPABASE_SERVICE_ROLE_KEY"),
        supabase_bucket=os.getenv("SUPABASE_BUCKET", "assistant-audio").strip()
        or "assistant-audio",
        supabase_table=os.getenv("SUPABASE_TABLE", "assistant_inbox").strip()
        or "assistant_inbox",
        mic_device=os.getenv("MIC_DEVICE", "default").strip() or "default",
        audio_bitrate=os.getenv("AUDIO_BITRATE", "48k").strip() or "48k",
        sample_rate=_env_int("SAMPLE_RATE", 16000),
        channels=_env_int("CHANNELS", 1),
        transcription_model=os.getenv(
            "TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"
        ).strip()
        or "gpt-4o-mini-transcribe",
        source_device=os.getenv("SOURCE_DEVICE", "raspberry-pi-v1").strip()
        or "raspberry-pi-v1",
    )


def ensure_local_dirs(config: AppConfig) -> None:
    config.audio_dir.mkdir(parents=True, exist_ok=True)
    config.transcripts_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    config.data_dir.mkdir(parents=True, exist_ok=True)


def missing_optional_config(config: AppConfig) -> list[str]:
    missing: list[str] = []
    if not config.openai_api_key:
        missing.append("OPENAI_API_KEY")
    if not config.supabase_url:
        missing.append("SUPABASE_URL")
    if not config.supabase_service_role_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    return missing
