#!/usr/bin/env bash
# sync-mcp-stack.sh
# Sincroniza o repositório opencode-mcp-stack com o GitHub (danielszki/opencode-mcp-stack)
# Rodar via systemd timer todo dia de manhã

set -euo pipefail

REPO_DIR="/home/mint/opencode/opencode-mcp-stack"
LOG_DIR="/home/mint/.local/state/sync-mcp-stack"
LOG_FILE="$LOG_DIR/sync-$(date +%F).log"

mkdir -p "$LOG_DIR"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== $(date '+%F %T') Iniciando sync ==="

cd "$REPO_DIR"

# 1. Verifica se há alterações locais não commitadas
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "⚠️  Há alterações locais não commitadas:"
    git status --short
    echo "→ Pulando pull/push para não perder trabalho local."
    echo "=== $(date '+%F %T') Fim (com alterações locais) ==="
    exit 0
fi

# 2. Atualiza o remote
git fetch origin

# 3. Verifica se está atrás do origin/main
BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
if [ "$BEHIND" -gt 0 ]; then
    echo "📥 Origin tem $BEHIND commits novos. Fazendo fast-forward..."
    git merge --ff-only origin/main
    echo "✓ Atualizado para $(git rev-parse --short HEAD)"
else
    echo "✓ Já está atualizado (HEAD = origin/main)"
fi

# 4. Verifica se está à frente do origin/main (commits locais não pushados)
AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
if [ "$AHEAD" -gt 0 ]; then
    echo "📤 Há $AHEAD commits locais não pushados. Enviando..."
    git push origin main
    echo "✓ Push concluído"
else
    echo "✓ Nada para pushar"
fi

echo "=== $(date '+%F %T') Sync concluído ==="