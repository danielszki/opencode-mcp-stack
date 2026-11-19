# humanizer (vendored)

Cópia integral da skill pública [`humanizer`](https://github.com/blader/humanizer)
de **Siqi Chen**, redistribuída sob licença **MIT**.

- **Commit de origem:** `a32f2440` (2026-11-19)
- **Licença:** MIT, Copyright (c) 2025 Siqi Chen — `skills/humanizer/LICENSE`
- **Conteúdo:** `SKILL.md` (504 linhas), `agents/openai.yaml` (prompt de agente
  Codex). Não incluímos `scripts/validate-package.py` (validador de CI do
  upstream, irrelevante para quem só usa a skill).

## O que faz

Remove os padrões de escrita que denunciam texto gerado por IA sem alterar o
que está sendo dito. A skill descreve **os padrões** e os reescreve:

- **A. Staging em vez de afirmação** — "não X, mas Y"; fechos de linha única e
  fragmentos dramáticos; ditos com ar de profundidade; arranque ensaiado antes
  do ponto; discutir com ninguém.
- **B. Ritmo por regra** — tríades forçadas; aberturas de frase repetidas;
  travessão como conector universal; qualificadores empilhados; pares com hífen
  em tudo; voz passiva e sujeito faltando.
- **C. Inflação e autoridade emprestada** — palavras gastas ("robusto",
  "aprofundar"), reivindicações infladas, linguagem de vendas, rótulos em
  negrito, adjetivos default, fillers.

A parte prática começa em *How to work*: preserva a voz do autor, não
reescreve o conteúdo, devolve o texto limpo com nota do que mudou.

## Relação com `unslop-ui`

Skill complementar à `skills/unslop-ui` (Felipe Basurto): `humanizer` trata
**prosa**; `unslop-ui` trata **copy de interface, gráficos e dashboards**.

## Instalação direta (upstream)

```bash
git clone https://github.com/blader/humanizer.git
```

Formato Agent Skills: `SKILL.md` na raiz, compatível com Claude Code, Cursor,
Codex (`agents/openai.yaml`) e agentes que leem `~/.agents/skills/`.