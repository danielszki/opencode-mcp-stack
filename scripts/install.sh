#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="${HOME:-$(eval echo ~)}"

echo "==> Instalando dependencias de sistema (node, python, uv, postgres) — ajuste conforme sua distro"
# Exemplo Ubuntu/Mint:
# sudo apt update && sudo apt install -y nodejs npm python3 python3-venv python3-pip postgresql postgresql-contrib

echo "==> Node MCPs"
NODE_DIR="$HOME_DIR/.local/share/mcp-node"
mkdir -p "$NODE_DIR"
cp "$ROOT/node-mcp/package.json" "$NODE_DIR/package.json"
cp "$ROOT/node-mcp/package-lock.json" "$NODE_DIR/package-lock.json"
cd "$NODE_DIR"
npm ci

echo "==> Python venv (vision + fetch)"
VENV_DIR="$HOME_DIR/.local/share/venv-mcp"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$ROOT/python-mcp/requirements.txt"

echo "==> Copiando custom (guard, vision-bridge, vision-launcher)"
mkdir -p "$HOME_DIR/.config/opencode"
cp -r "$ROOT/custom/guard" "$HOME_DIR/opencode/opencode-mcp-stack/custom/guard" 2>/dev/null || true
cp "$ROOT/custom/vision-bridge.py" "$VENV_DIR/vision-bridge.py"
cp "$ROOT/custom/vision-launcher.py" "$HOME_DIR/.config/opencode/vision-launcher.py"

echo "==> Ajustando opencode.json"
"$ROOT/scripts/setup-config.sh"

echo "==> Pronto. Revise ~/.config/opencode/opencode.json e .env."
