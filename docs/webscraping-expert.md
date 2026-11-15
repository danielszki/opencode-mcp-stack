# Webscraping Expert (vendored)

Cópia integral e sem modificações da skill pública [`webscraping-expert`](https://github.com/gabrielgreco1/skills/tree/main/webscraping-expert)
de **Gabriel Greco** ([@greco_dev](https://x.com/greco_dev)), do repositório
[`gabrielgreco1/skills`](https://github.com/gabrielgreco1/skills).

- **Commit de origem:** `a3c2be7` (2026-11-02)
- **Licença do repo de origem:** "Use the skills, change them, ship videos with
  them. The vendored third-party code keeps its own license (Three.js is MIT)."
  (README.md, seção License). Sem arquivo LICENSE explícito no repo.
- **Conteúdo:** `SKILL.md` (986 linhas) + 67 arquivos de referência em
  `anti-bot/`, `approach/`, `browser-automation/`, `discovery/`, `networking/`,
  `reference/`, `reliability/`, `site-patterns/`. Somente Markdown — nenhum
  binário, script executável ou segredo.

## O que é / para que serve

Guia de extração de dados que sempre começa pelo caminho **mais barato e
confiável**, subindo um degrau por vez:

1. request HTTP simples
2. headers reais de Chrome (`User-Agent`, `Accept`, `Accept-Language`)
3. impersonação de fingerprint TLS/HTTP (`curl_cffi` com `impersonate="chrome"`;
   alternativas `primp`/`rnet`) — resolve os 403 baseados em JA3/JA4
4. ritmo humano (backoff exponencial, respeitar `Retry-After`, sleeps
   aleatórios) para 429
5. proxy / unblocker gerenciado (Zyte API) com IP do país certo
6. browser real (Playwright/patchright/camoufox/nodriver) quando o anti-bot
   valida cookie por JS (ex.: `_abck` do Akamai) — extrai **de dentro da
   página**, não copiando o cookie para um request

Cobre ainda a matriz de vendors (Cloudflare, DataDome, Kasada, Akamai),
CAPTCHA/Turnstile, HAR/DevTools, JSON-LD/microdata/OpenGraph, extração
adaptativa (scrapling/crawl4ai/firecrawl), playbooks por stack (Next.js RSC,
GraphQL, OData, PX-Web, SDMX, ASP.NET, Tableau, SPAs) e arquitetura limpa
OOP + execuções idempotentes.

Origem do conteúdo: a thread
<https://x.com/greco_dev/status/2121641166944846009> (9 sites brasileiros,
9/9 liberados com a escada acima).

## Como instalar no OpenCode (V2)

O OpenCode V2 descobre skills em `~/.config/opencode/skills/<id>/SKILL.md`:

```bash
cd ~/opencode/opencode-mcp-stack
mkdir -p ~/.config/opencode/skills
cp -a skills/webscraping-expert ~/.config/opencode/skills/
```

Carregue com `skill({id:"webscraping-expert"})` (ou `@webscraping-expert` no
prompt). Para dispensar confirmação, adicione em `~/.config/opencode/opencode.json`:

```jsonc
{
  "permissions": [
    { "action": "skill", "resource": "webscraping-expert", "effect": "allow" }
  ]
}
```

Adaptações locais usadas nesta máquina (no `~/.config/opencode/AGENTS.md`):
- "browser real" = MCP `browse` pareado com o Brave do usuário;
- `firecrawl` / `webfetch` / `beatapi` já são MCPs instalados;
- `AskUserQuestion` (Claude Code) → ferramenta `question` do OpenCode;
- respeitar termos dos sites, volume baixo, sem login com credenciais alheias
  nem bypass de CAPTCHA sem autorização explícita.

## Atualizar

```bash
cd /tmp && git clone --depth 1 https://github.com/gabrielgreco1/skills.git
diff -rq /tmp/skills/webscraping-expert \
  ~/.config/opencode/skills/webscraping-expert
```

> Nota: a pasta `skills/webscraping-expert/` neste repo é **cópia byte-a-byte**
> do upstream — verifique com `diff -rq`. Este arquivo (fora da pasta) documenta
> apenas a origem e a instalação, e não é carregado como skill.
