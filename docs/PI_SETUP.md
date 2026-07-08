# Raspberry Pi Setup

Assumptions:

- Raspberry Pi 4 running Raspberry Pi OS.
- Python 3.9 or newer. Raspberry Pi OS with Python 3.9.2 is supported.
- USB microphone connected.
- This GitHub repo is cloned or can be cloned onto the Pi.
- You will use terminal keyboard start/stop recording for V1.

## Install And Clone

```bash
sudo apt update
sudo apt install -y git
git clone <your-repo-url>
cd Raspberry-Pi
```

If the repo already exists on the Pi:

```bash
cd Raspberry-Pi
git pull
```

## Run Setup

```bash
bash scripts/setup_pi.sh
source .venv/bin/activate
```

## Create Environment File

```bash
cp .env.example .env
nano .env
```

Set `OPENAI_API_KEY` if you want transcription. Set Supabase values if you want remote upload.

## Test Microphone

```bash
python -m pi_assistant.main smoke-test
bash scripts/list_audio_devices.sh
```

If needed, update `MIC_DEVICE` in `.env`.

Then record a test clip:

```bash
bash scripts/test_mic.sh
```

Listen to the MP3 in `data/audio/`.

## Run Recording Flow

```bash
python -m pi_assistant.main record
python -m pi_assistant.main dashboard
```
