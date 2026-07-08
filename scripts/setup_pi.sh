#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg alsa-utils git

echo "Creating Python virtual environment..."
python3 -m venv .venv

echo "Installing Python dependencies..."
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .

echo
echo "Setup complete."
echo
echo "Next steps:"
echo "1. source .venv/bin/activate"
echo "2. cp .env.example .env"
echo "3. nano .env"
echo "4. bash scripts/list_audio_devices.sh"
echo "5. bash scripts/test_mic.sh"
echo "6. python -m pi_assistant.main record"
