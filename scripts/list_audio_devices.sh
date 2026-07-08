#!/usr/bin/env bash
set -euo pipefail

echo "Audio capture devices from arecord:"
echo
arecord -l
echo
echo "If needed, set MIC_DEVICE in .env."
