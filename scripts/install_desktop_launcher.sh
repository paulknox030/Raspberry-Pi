#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

repo_dir="$(pwd)"
template_path="$repo_dir/desktop/paul-pi-assistant.desktop"

if command -v xdg-user-dir >/dev/null 2>&1; then
  desktop_dir="$(xdg-user-dir DESKTOP)"
else
  desktop_dir="$HOME/Desktop"
fi

mkdir -p "$desktop_dir"

launcher_path="$desktop_dir/paul-pi-assistant.desktop"

while IFS= read -r line; do
  printf '%s\n' "${line//__REPO_DIR__/$repo_dir}"
done < "$template_path" > "$launcher_path"

chmod +x "$repo_dir/scripts/start_ui.sh"
chmod +x "$launcher_path"

if command -v gio >/dev/null 2>&1; then
  gio set "$launcher_path" metadata::trusted true >/dev/null 2>&1 || true
fi

echo "Installed desktop launcher:"
echo "  $launcher_path"
echo
echo "Double-click 'Paul Pi Assistant' on the desktop to open the full-screen UI."
echo "If Raspberry Pi OS asks, choose 'Allow Launching'."
