#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo ".venv not found. Run: bash scripts/setup_pi.sh"
  exit 1
fi

. .venv/bin/activate
python -m pi_assistant.main test-mic --seconds 10
