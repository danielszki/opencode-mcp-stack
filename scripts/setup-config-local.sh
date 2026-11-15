#!/usr/bin/env bash
# Gera config/opencode.json com caminhos apontando para ESTA cópia do stack
# (instalação self-contained em /home/mint/Pasta Pessoal/deepai/opencode-mcp-stack).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="${HOME:-$(eval echo ~)}"
OUT="$ROOT/config/opencode.json"

sed \
  -e "s#__HOME__/opencode/opencode-mcp-stack#$ROOT#g" \
  -e "s#__HOME__/.local/share/mcp-node#$ROOT/node-mcp#g" \
  -e "s#__HOME__/.local/share/venv-mcp#$ROOT/.venv#g" \
  -e "s#__HOME__/opencode/bgts-context-engine#$ROOT/../bgts-context-engine#g" \
  -e "s#__HOME__/VoiceStudio#$ROOT/../VoiceStudio#g" \
  -e "s#__HOME__#$HOME_DIR#g" \
  "$ROOT/config/opencode.json.template" > "$OUT"

# vision-bridge usa caminhos fixos em ~/.local/share e ~/.config; aponta para o stack local.
python3 - "$OUT" "$ROOT" <<'PY'
import json, sys
out, root = sys.argv[1], sys.argv[2]
d = json.load(open(out))
d["mcp"]["vision"]["environment"] = {
    "VISION_PYTHON": f"{root}/.venv/bin/python",
    "VISION_LAUNCHER": f"{root}/custom/vision-launcher.py",
    "VISION_LOG": f"{root}/.vision-child.log",
    "GEMINI_MODEL": "{env:GEMINI_MODEL}",
    "GEMINI_API_KEY": "{env:GEMINI_API_KEY}",
}
json.dump(d, open(out, "w"), indent=2, ensure_ascii=False)
open(out, "a").write("\n")
PY

echo "Gerado: $OUT"
