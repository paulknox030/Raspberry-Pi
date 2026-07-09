#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-gpiozero ffmpeg alsa-utils git

if apt-cache show python3-lgpio >/dev/null 2>&1; then
  sudo apt install -y python3-lgpio
else
  echo "python3-lgpio is not available from apt on this OS; continuing with available gpiozero pin factories."
fi

echo "Checking Python version..."
python3 --version
if ! python3 - <<'PY'
import sys

if sys.version_info < (3, 9):
    print("Python 3.9 or newer is required.")
    print("Current Python:", sys.version.split()[0])
    raise SystemExit(1)
PY
then
  exit 1
fi

echo "Creating Python virtual environment..."
python3 -m venv --system-site-packages .venv

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
echo "4. python -m pi_assistant.main smoke-test"
echo "5. bash scripts/list_audio_devices.sh"
echo "6. bash scripts/test_mic.sh"
echo "7. python -m pi_assistant.main record"
echo "8. python -m pi_assistant.main gpio-test"
echo "9. python -m pi_assistant.main gpio-record"
