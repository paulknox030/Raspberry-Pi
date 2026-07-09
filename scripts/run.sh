#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo ".venv not found. Run: bash scripts/setup_pi.sh"
  exit 1
fi

. .venv/bin/activate

echo "Paul Pi Assistant V1"
echo
echo "Useful commands:"
echo "  python -m pi_assistant.main smoke-test"
echo "  python -m pi_assistant.main list-devices"
echo "  python -m pi_assistant.main test-mic --seconds 10"
echo "  python -m pi_assistant.main record"
echo "  python -m pi_assistant.main gpio-test"
echo "  python -m pi_assistant.main gpio-record"
echo "  python -m pi_assistant.main ui"
echo "  python -m pi_assistant.main dashboard"
echo
python -m pi_assistant.main dashboard
