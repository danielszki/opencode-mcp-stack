# OpenCode MCP Stack (portável)

Conjunto de MCP servers + plugins usados no OpenCode, organizado para ser
clonado em outra máquina e reinstalado de forma reproduzível.

## O que tem aqui

- `node-mcp/` — manifestos npm dos MCPs em Node (playwright, chrome-devtools, css, filesystem, firecrawl).
- `python-mcp/` — `requirements.txt` do venv (vision, fetch, mcp).
- `custom/` — código próprio: plugin `guard`, `vision-bridge.py`, `vision-launcher.py`.
- `config/opencode.json.template` — config do OpenCode com placeholders `__HOME__`.
- `scripts/install.sh` — instala tudo.
- `scripts/setup-config.sh` — gera `~/.config/opencode/opencode.json`.
- `env.example` — variáveis de ambiente necessárias.

## O que NÃO está aqui (dependências externas)

- **bgts-context-engine** — repo separado: https://github.com/bgts-ai-org/bgts-context-engine (precisa de Postgres com AGE + pgvector). Clone em `$HOME/opencode/bgts-context-engine` e crie o `.venv`.
- **VoiceStudio / omnivoice** — repo separado: https://github.com/debpalash/VoiceStudio. Clone em `$HOME/VoiceStudio`.
- Runtimes: Node.js, Python 3.13, `uv`, PostgreSQL.

## Instalação em outra máquina

```bash
git clone https://github.com/SEU_USUARIO/opencode-mcp-stack.git ~/opencode/opencode-mcp-stack
cd ~/opencode/opencode-mcp-stack
cp env.example ~/.config/opencode/.env   # edite e preencha as chaves
./scripts/install.sh
```

Depois:
1. Clone `bgts-context-engine` e `VoiceStudio` nos caminhos esperados.
2. Configure o Postgres e rode `install-postgres-host.sh` do bgts.
3. Exporte as variáveis do `.env` (ou use o mecanismo do OpenCode).
4. Abra o OpenCode — os MCPs locais devem subir.

## Publicar no GitHub (nesta máquina)

```bash
cd ~/opencode/opencode-mcp-stack
git init
git add .
git commit -m "feat: stack MCP portável para OpenCode"
# crie o repo vazio no GitHub (web) e então:
git remote add origin https://github.com/SEU_USUARIO/opencode-mcp-stack.git
git branch -M main
git push -u origin main
```

> Sem `gh` CLI instalado; crie o repositório vazio pelo site do GitHub antes do push.
