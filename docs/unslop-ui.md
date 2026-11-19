# unslop-ui (vendored)

Cópia integral da skill pública [`unslop-ui`](https://github.com/felipebasurto/unslop-ui)
de **Felipe Basurto**, redistribuída sob licença **MIT**.

- **Commit de origem:** `cd89116` (2026-11-18), versão do plugin `0.5.1`
- **Licença:** MIT, Copyright (c) 2026 Felipe Basurto — `skills/unslop-ui/LICENSE`
- **Conteúdo:** `SKILL.md` (149 linhas), `references/` (`examples.md`,
  `tokens.md`, `unslop-fallback.md`), `scripts/` (`load_unslop.py`,
  `count_tells.py`) e `agents/openai.yaml`. Somente Markdown + Python padrão,
  sem binários (76 KB no total).

## O que faz

Remove os padrões que denunciam interface gerada por IA: eyebrow labels em caixa
alta sobre cada título, numeração `01 //`, subtítulo que repete o título, legenda
explicando o que já está visível, badges e status dots decorativos, notas de
design vazadas, e clutter de gráfico (legendas que um rótulo direto resolveria).

- **Subtrativa:** apaga primeiro, escreve pouco, nunca inventa números ou features.
- **Segura por padrão:** sem `--surface` mexe apenas em texto visível e decoração;
  preserva `aria-label`, `alt`, rótulos de formulário e o que reflete estado real.
- **Com `--surface`:** também corrige gradientes/glows, espaçamento fora de escala,
  pesos pesados e movimento decorativo (valores em `references/tokens.md`).
- **Relata:** cada execução termina com tabela de contagens, strings reescritas,
  o que foi mantido de propósito e as decisões que ficam para o humano.

Invoca com `/unslop-ui [arquivo|pasta|componente] [--surface]`.

## Nota de integração

O `SKILL.md` tem `disable-model-invocation: true` (só roda quando invocada
explicitamente) e usa `$CLAUDE_SKILL_DIR` para achar os scripts; em agentes que
não definem essa variável, o próprio arquivo instrui a rodar
`python3 scripts/load_unslop.py` a partir da pasta da skill — o fallback está em
`references/unslop-fallback.md`. `agents/openai.yaml` é específico do Codex.

## Instalação direta (upstream)

```bash
npx skills add felipebasurto/unslop-ui -g
```
