from __future__ import annotations

import argparse
import sys
import traceback
from typing import Optional

from . import audio
from . import gpio_button
from . import ui
from . import workflow
from .config import AppConfig, ensure_local_dirs, load_config, missing_optional_config
from .dashboard import print_dashboard


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


def _finish_recording_flow(
    config: AppConfig, result: audio.RecordingResult, debug: bool
) -> int:
    workflow.process_recording(config, result, debug=debug)
    print()
    print_dashboard(config)
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
    print("Recording stopped.")
    return _finish_recording_flow(config, result, args.debug)


def cmd_gpio_test(_args: argparse.Namespace) -> int:
    button = gpio_button.create_button()
    print("Waiting for button...")
    try:
        while True:
            gpio_button.wait_for_fresh_press(button)
            print("Button pressed", flush=True)
            button.wait_for_release()
    except KeyboardInterrupt:
        print("\nExiting gpio-test.")
        return 0
    finally:
        button.close()


def cmd_gpio_record(args: argparse.Namespace) -> int:
    config = load_config()
    ensure_local_dirs(config)

    button = gpio_button.create_button()
    active: Optional[audio.ActiveRecording] = None
    try:
        print("Waiting for button...")
        gpio_button.wait_for_fresh_press(button)
        active = audio.start_recording(config)
        print("Recording started. Press button again to stop.")
        button.wait_for_release()

        gpio_button.wait_for_fresh_press(button)
        print("Stopping recording...")
        result = audio.stop_recording(active)
        active = None
        print("Recording stopped.")
        return _finish_recording_flow(config, result, args.debug)
    except KeyboardInterrupt:
        if active is not None:
            print("\nStopping recording...")
            try:
                audio.stop_recording(active)
            except Exception:
                if args.debug:
                    traceback.print_exc()
        raise
    except Exception:
        if active is not None:
            try:
                audio.stop_recording(active)
            except Exception:
                if args.debug:
                    traceback.print_exc()
        raise
    finally:
        button.close()


def cmd_ui(args: argparse.Namespace) -> int:
    return ui.run(debug=args.debug)


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

    gpio_test = subparsers.add_parser("gpio-test")
    gpio_test.set_defaults(func=cmd_gpio_test)

    gpio_record = subparsers.add_parser("gpio-record")
    gpio_record.set_defaults(func=cmd_gpio_record)

    ui_parser = subparsers.add_parser("ui")
    ui_parser.set_defaults(func=cmd_ui)

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
