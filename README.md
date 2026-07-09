# paul-pi-assistant

Raspberry Pi 4 personal assistant foundation, V1.

This first milestone is intentionally small:

1. Record audio from a USB microphone.
2. Save the audio locally as MP3.
3. Transcribe the audio with OpenAI when configured.
4. Save the transcript locally.
5. Upload audio/transcript metadata to Supabase when configured.
6. Show recent local inbox entries in a terminal dashboard.

No Gmail, calendar, Apple Watch, grocery ordering, web app, LEDs, speaker code, or agent actions are included yet.

## Quick Start: Laptop Or Dev Machine

Python 3.9 or newer is supported.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
cp .env.example .env
python -m pi_assistant.main smoke-test
python -m pi_assistant.main dashboard
```

On Windows PowerShell, activate with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Audio recording uses ALSA through `ffmpeg`, so real microphone recording is intended for Raspberry Pi OS or Linux.

## Quick Start: Raspberry Pi

After pulling this repo onto the Pi:

```bash
bash scripts/setup_pi.sh
source .venv/bin/activate
cp .env.example .env
nano .env
python -m pi_assistant.main smoke-test
bash scripts/list_audio_devices.sh
bash scripts/test_mic.sh
python -m pi_assistant.main record
python -m pi_assistant.main gpio-test
python -m pi_assistant.main gpio-record
python -m pi_assistant.main dashboard
```

If `arecord -l` shows a specific USB device, set `MIC_DEVICE` in `.env`. The default is `default`.

## Commands

List audio devices:

```bash
python -m pi_assistant.main list-devices
```

Record a 10 second microphone test:

```bash
python -m pi_assistant.main test-mic --seconds 10
```

Start keyboard-controlled recording:

```bash
python -m pi_assistant.main record
```

Test the physical GPIO button:

```bash
python -m pi_assistant.main gpio-test
```

Start button-controlled recording:

```bash
python -m pi_assistant.main gpio-record
```

Show the latest local inbox rows:

```bash
python -m pi_assistant.main dashboard
```

Run local diagnostics:

```bash
python -m pi_assistant.main smoke-test
```

Add `--debug` before the command to show full tracebacks:

```bash
python -m pi_assistant.main --debug record
```

## Local Data

The app creates these folders and files when needed:

```text
data/audio/
data/transcripts/
data/inbox.jsonl
logs/
```

These generated files are ignored by git.

## Supabase

Supabase is optional for local testing. If `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are not set, recordings and transcripts are still saved locally, and remote upload is skipped.

To enable Supabase:

1. Create a Supabase project.
2. Run `supabase/schema.sql` in the SQL editor.
3. Create a Storage bucket named `assistant-audio`.
4. Put `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env` on the Pi.

The service role key is backend-only. Never commit it.

## GPIO Button

Button wiring:

- Physical pin 11 / GPIO17 -> button
- Physical pin 6 / GND -> other side of button

The app uses BCM numbering with `gpiozero.Button(17, pull_up=True, bounce_time=0.3)`.

Use this to test the button:

```bash
python -m pi_assistant.main gpio-test
```

Use this to record with the button:

```bash
python -m pi_assistant.main gpio-record
```

## Troubleshooting

If recording fails, check:

- `ffmpeg` is installed.
- `alsa-utils` is installed.
- `arecord -l` can see your USB microphone.
- `MIC_DEVICE` in `.env` matches the microphone device.

If transcription is skipped or fails, check:

- `OPENAI_API_KEY` is set in `.env`.
- The audio file exists and is under the V1 size limit.
- The OpenAI Python package is installed in the active venv.

If Supabase upload fails, check:

- `SUPABASE_URL` is set.
- `SUPABASE_SERVICE_ROLE_KEY` is set.
- The `assistant-audio` bucket exists.
- The `assistant_inbox` table exists.
- `supabase/schema.sql` was run in the project.
