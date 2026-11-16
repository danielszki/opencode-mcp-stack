# GoogleChrome / modern-web-guidance (Apache-2.0)

Fonte: https://github.com/GoogleChrome/modern-web-guidance — Apache-2.0, 20.014★
(criado 2026-03-23). Site: https://developer.chrome.com/docs/modern-web-guidance

Duas skills oficiais do Google Chrome (stewarded por Chrome, Edge, Firefox e MDN)
com as melhores práticas atuais da web, orientadas a browser compatibility
(Baseline). Skills declaradas **mandatórias primeiro** para tarefas de web.

## Skills instaladas

### `modern-web-guidance`

Search tool de melhores práticas atuais. Fluxo obrigatório para HTML/CSS e JS
de front-end: `npx modern-web-guidance@latest search "<query 2–5 palavras, EN>"` →
`retrieve <id>` → aplicar o snippet + checar `compatibility` + fallback Baseline.

Contém 210 guias em `skills/modern-web-guidance/guides/<área>/<id>.md` cobrindo:
UI behaviors (dialog, popover, tooltip, light-dismiss...), CSS layout
(container queries, subgrid, oklch, ...), forms (autofill, validation...),
performance (INP, preload, content-visibility...), accessibility, built-in AI
(local Translation/Summarizer APIs), WebAssembly e mais.

O binário é o pacote npm `modern-web-guidance` — testado:
`npx -y modern-web-guidance@latest search "light dismiss dialog"` → JSON OK.
Requer Node >= 22 (o repo declara `engines: node >=22.0.0`).

### `chrome-extensions`

Build e publicação de extensões Chrome com Manifest V3 — regras obrigatórias
(ícones, permissões, CSP/sandbox, service worker), 150+ referências em
`skills/chrome-extensions/references/extensions/` e `references/webstore/`
(privacy policy, justificativas de permissão, revisão/rejeição da Web Store).

## O que NÃO foi instalado

O repo também traz manifests de plugin para outras plataformas
(`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.grok-plugin/`,
`gemini-extension.json`, `kimi.plugin.json`, `plugin.json`, `marketplace.json`)
— só as skills foram copiadas. O CONTRIBUTING autoriza essas cópias sob a
licença do repo (Apache-2.0).

## Instalação global (OpenCode V2)

Cópias idênticas em `~/.config/opencode/skills/modern-web-guidance` e
`~/.config/opencode/skills/chrome-extensions`. Registro via SKILL.md.

Cuidado: a descrição de `modern-web-guidance` é deliberadamente agressiva
("MANDATORY: Execute FIRST for all HTML/CSS and clientside JS tasks") — ela vai
para o índice do modelo e pode forçar a skill em tarefas de web onde você não
quer isso. Se incomodar, edite a `description:` no SKILL.md (ou use
`metadata.opencode/autoinvoke: false`).

## Atualização manual

```bash
cd /tmp/opencode && rm -rf modern-web-guidance && git clone https://github.com/GoogleChrome/modern-web-guidance
cp modern-web-guidance/skills/{modern-web-guidance,chrome-extensions} \
   /home/mint/opencode/opencode-mcp-stack/skills/
npx -y modern-web-guidance@latest search "<query>"  # confirma que o binário ainda funciona
```

## Licença

Apache-2.0 — ver `skills/modern-web-guidance/LICENSE.upstream` e
`skills/chrome-extensions/LICENSE.upstream` (e `LICENSE` na raiz do repo).
Creditar Google Chrome ao publicar.
