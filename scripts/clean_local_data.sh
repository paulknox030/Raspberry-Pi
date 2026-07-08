#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "This will remove generated local audio, transcripts, inbox, and logs."
read -r -p "Type DELETE to continue: " confirmation

if [ "$confirmation" != "DELETE" ]; then
  echo "Canceled."
  exit 0
fi

rm -rf data/audio data/transcripts data/inbox.jsonl logs
echo "Local generated data removed."
