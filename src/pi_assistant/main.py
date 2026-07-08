from __future__ import annotations

import argparse
import sys
import traceback
from typing import Optional

from . import audio
from .config import ensure_local_dirs, load_config, missing_optional_config
from .dashboard import print_dashboard
from .local_store import LocalRecordInput, append_inbox_record, save_transcript
from .supabase_store import SupabaseUploadResult, upload_recording
from .transcribe import transcribe_audio


def _print_check(label: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "MISSING"
    suffix = f" - {detail}" if detail else ""
    print(f"{status}: {label}{suffix}")


def cmd_list_devices(_args: argparse.Namespace) -> int:
    print(audio.list_audio_devices())
    print()
    print("If needed, set MIC_DEVICE in .env.")
    return 0


def cmd_test_mic(args: argparse.Namespace) -> int:
    config = load_config()
    result = audio.record_for_seconds(config, args.seconds)
    print(f"Saved test recording: {result.audio_path}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    return 0


def cmd_dashboard(_args: argparse.Namespace) -> int:
    config = load_config()
    print_dashboard(config)
    return 0


def cmd_smoke_test(_args: argparse.Namespace) -> int:
    config = load_config()
    ensure_local_dirs(config)

    print("Paul Pi Assistant V1 smoke test")
    print()
    _print_check("local data directories", True, str(config.data_dir))
    _print_check("ffmpeg", audio.ffmpeg_available(), "needed for recording")
    _print_check("arecord", audio.arecord_available(), "needed for ALSA device listing")
    _print_check(".env loaded or defaults usable", True, str(config.project_root / ".env"))
    print()

    missing = missing_optional_config(config)
    if missing:
        print("Optional config missing:")
        for name in missing:
            print(f"- {name}")
    else:
        print("Optional config: OpenAI and Supabase values are present.")

    if not audio.ffmpeg_available() or not audio.arecord_available():
        print()
        print("Install ffmpeg and alsa-utils on the Raspberry Pi before recording.")
        return 1
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    config = load_config()
    ensure_local_dirs(config)

    print("Press ENTER to start recording.")
    input()

    active = audio.start_recording(config)
    print("Recording. Press ENTER to stop.")
    input()

    result = audio.stop_recording(active)
    print(f"Saved audio: {result.audio_path}")
    print(f"Duration: {result.duration_seconds:.1f}s")

    transcript_text = ""
    status = "new"
    error: Optional[str] = None

    try:
        transcription = transcribe_audio(result.audio_path, config)
        transcript_text = transcription.transcript_text
        status = transcription.status
        error = transcription.error
        if status == "missing_openai_key":
            print("OPENAI_API_KEY is not configured, skipped transcription.")
        else:
            print("Transcription complete.")
    except Exception as exc:
        status = "error"
        error = str(exc)
        if args.debug:
            traceback.print_exc()
        print(f"Transcription failed: {error}")
        print("Check OPENAI_API_KEY, the audio file, and the transcription model.")

    transcript_path = save_transcript(config, transcript_text)
    print(f"Saved transcript: {transcript_path}")

    supabase_result = SupabaseUploadResult(status="skipped")
    if config.supabase_configured:
        try:
            supabase_result = upload_recording(
                config,
                audio_path=result.audio_path,
                transcript_path=transcript_path,
                transcript_text=transcript_text,
                status=status,
                error=error,
            )
            print("Supabase upload complete.")
        except Exception as exc:
            supabase_result = SupabaseUploadResult(status="error", error=str(exc))
            status = "error"
            error = f"Supabase upload failed: {exc}"
            if args.debug:
                traceback.print_exc()
            print(error)
            print("Check SUPABASE_URL, service role key, bucket, and table.")
    else:
        print("Supabase not configured, skipped remote upload.")

    record = append_inbox_record(
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
    print(f"Saved local inbox row: {record['id']}")
    print()
    print_dashboard(config)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pi-assistant")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="show full traceback on errors",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_devices = subparsers.add_parser("list-devices")
    list_devices.set_defaults(func=cmd_list_devices)

    test_mic = subparsers.add_parser("test-mic")
    test_mic.add_argument("--seconds", type=int, default=10)
    test_mic.set_defaults(func=cmd_test_mic)

    record = subparsers.add_parser("record")
    record.set_defaults(func=cmd_record)

    dashboard = subparsers.add_parser("dashboard")
    dashboard.set_defaults(func=cmd_dashboard)

    smoke_test = subparsers.add_parser("smoke-test")
    smoke_test.set_defaults(func=cmd_smoke_test)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nCanceled.")
        return 130
    except Exception as exc:
        if args.debug:
            traceback.print_exc()
        else:
            print(f"Error: {exc}")
            print()
            print("Things to check:")
            print("- mic device and MIC_DEVICE in .env")
            print("- ffmpeg installed")
            print("- OpenAI key")
            print("- Supabase URL/key")
            print("- bucket exists")
            print("- table exists")
        return 1


def entrypoint() -> None:
    sys.exit(main())


if __name__ == "__main__":
    entrypoint()
