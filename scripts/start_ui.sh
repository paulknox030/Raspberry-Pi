#!/usr/bin/env bash
set -u

cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo ".venv not found. Run this first:"
  echo "  bash scripts/setup_pi.sh"
  echo
  read -r -p "Press ENTER to close this window..." _
  exit 1
fi

. .venv/bin/activate

if [ ! -f ".env" ]; then
  echo "Warning: .env not found."
  echo "Create one with: cp .env.example .env"
  echo
fi

python -m pi_assistant.main ui
status=$?

if [ "$status" -ne 0 ]; then
  echo
  echo "Paul Pi Assistant exited with status $status."
  echo "Things to check:"
  echo "- .env exists"
  echo "- microphone is connected"
  echo "- GPIO button wiring"
  echo "- OPENAI_API_KEY if transcription should run"
  echo "- Supabase URL/key if upload should run"
  echo
  read -r -p "Press ENTER to close this window..." _
fi

exit "$status"
