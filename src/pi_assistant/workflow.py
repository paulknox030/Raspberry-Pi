from __future__ import annotations

import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from . import audio
from .config import AppConfig
from .local_store import LocalRecordInput, append_inbox_record, save_transcript
from .supabase_store import SupabaseUploadResult, upload_recording
from .transcribe import transcribe_audio


ProgressCallback = Callable[[str], None]
Printer = Callable[[str], None]


@dataclass(frozen=True)
class WorkflowResult:
    audio_path: Path
    duration_seconds: float
    transcript_path: Optional[Path]
    transcript_text: str
    status: str
    error: Optional[str]
    supabase_status: str
    supabase_audio_path: Optional[str]
    supabase_transcript_path: Optional[str]
    local_record: Dict[str, Any]


def _emit(printer: Optional[Printer], message: str) -> None:
    if printer is not None:
        printer(message)


def _progress(progress: Optional[ProgressCallback], step: str) -> None:
    if progress is not None:
        progress(step)


def process_recording(
    config: AppConfig,
    result: audio.RecordingResult,
    *,
    debug: bool = False,
    progress: Optional[ProgressCallback] = None,
    printer: Optional[Printer] = print,
) -> WorkflowResult:
    _emit(printer, f"Saved audio: {result.audio_path}")
    _emit(printer, f"Duration: {result.duration_seconds:.1f}s")

    transcript_text = ""
    status = "new"
    error: Optional[str] = None

    _progress(progress, "transcribing")
    _emit(printer, "Transcribing...")
    try:
        transcription = transcribe_audio(result.audio_path, config)
        transcript_text = transcription.transcript_text
        status = transcription.status
        error = transcription.error
        if status == "missing_openai_key":
            _emit(printer, "OPENAI_API_KEY is not configured, skipped transcription.")
        else:
            _emit(printer, "Transcription complete.")
    except Exception as exc:
        status = "error"
        error = str(exc)
        if debug:
            traceback.print_exc()
        _emit(printer, f"Transcription failed: {error}")
        _emit(printer, "Check OPENAI_API_KEY, the audio file, and the transcription model.")

    _progress(progress, "saving")
    _emit(printer, "Saving transcript locally...")
    transcript_path = save_transcript(config, transcript_text)
    _emit(printer, f"Saved transcript: {transcript_path}")

    supabase_result = SupabaseUploadResult(status="skipped")
    if config.supabase_configured:
        _progress(progress, "uploading")
        _emit(printer, "Uploading to Supabase...")
        try:
            supabase_result = upload_recording(
                config,
                audio_path=result.audio_path,
                transcript_path=transcript_path,
                transcript_text=transcript_text,
                status=status,
                error=error,
            )
            _emit(printer, "Supabase upload complete.")
        except Exception as exc:
            supabase_result = SupabaseUploadResult(status="error", error=str(exc))
            status = "error"
            error = f"Supabase upload failed: {exc}"
            if debug:
                traceback.print_exc()
            _emit(printer, error)
            _emit(printer, "Check SUPABASE_URL, service role key, bucket, and table.")
    else:
        _emit(printer, "Supabase not configured, skipped remote upload.")

    local_record = append_inbox_record(
        config,
        LocalRecordInput(
            audio_path=result.audio_path,
            transcript_path=transcript_path,
            transcript_text=transcript_text,
            status=status,
            error=error,
            supabase_status=supabase_result.status,
            supabase_audio_path=supabase_result.audio_path,
            supabase_transcript_path=supabase_result.transcript_path,
        ),
    )
    _emit(printer, f"Saved local inbox row: {local_record['id']}")
    _progress(progress, "done")
    _emit(printer, "Done.")

    return WorkflowResult(
        audio_path=result.audio_path,
        duration_seconds=result.duration_seconds,
        transcript_path=transcript_path,
        transcript_text=transcript_text,
        status=status,
        error=error,
        supabase_status=supabase_result.status,
        supabase_audio_path=supabase_result.audio_path,
        supabase_transcript_path=supabase_result.transcript_path,
        local_record=local_record,
    )
