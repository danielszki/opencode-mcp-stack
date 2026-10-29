#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="${HOME:-$(eval echo ~)}"
mkdir -p "$HOME_DIR/.config/opencode"
sed "s#__HOME__#$HOME_DIR#g" "$ROOT/config/opencode.json.template" > "$HOME_DIR/.config/opencode/opencode.json"
echo "Gerado: $HOME_DIR/.config/opencode/opencode.json"
