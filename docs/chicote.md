# chicote (vendored)

Cópia integral da skill **[chicote](https://github.com/matheusmongarde/chicote)**
de **Matheus Mongarde**, redistribuída sob licença **MIT**.

- **Commit de origem:** `ce3d39d9` (2026-11-25)
- **Licença:** MIT, Copyright (c) 2026 Matheus Mongarde — `skills/chicote/LICENSE`
- **Conteúdo:** `SKILL.md` (183 linhas), `referencias/` (19 arquivos),
  `modelos/`, `efeitos/` (6 receitas em CSS/JS), `scripts/` (instalar, medidas,
  chicotada e pexels) e `exemplos/` (a página reprovada, a página 100 e a
  vitrine de efeitos). Não copiamos `node_modules/` nem as saídas de medição
  (`exemplos/saida-*`, efêmeras e listadas no `.gitignore` do upstream).

## O que faz

Constrói sites, landing pages, sistemas e componentes **que vendem**, e mede a
página num Chromium de verdade até bater 100. Não confia no gosto do modelo:
dá ordens diretas e verifica cada uma com número.

O processo tem 9 passos, nesta ordem: interrogatório (história do nicho e de
quem compra) → roteiro (hero numa frase, capítulos com função) → metáfora (o
nicho vira forma, não três cards iguais) → medidas calculadas para o público
real (idoso, celular ruim, pressa) → composição justificada → imagem/efeito/3D
→ construção → chicotada (medir e corrigir, no máximo 5 rodadas) → entrega.

A nota são 70 pontos medidos pelo script em três aparelhos (360×640 com CPU 4×
mais lenta e 4G ruim, 390×844, 1440×900) mais 30 de rubrica com evidência. Os
16 portões cobrem CTA na dobra, contraste, alvo de toque, fonte, LCP, CLS,
peso, SEO, movimento, atmosfera, visual, tipografia, profundidade, eixo e
orçamento de texto.

## Instalação (precisa de Node 18+ e Chromium)

O `SKILL.md` só funciona inteiro com as dependências instaladas — a medição usa
Playwright:

```bash
cd skills/chicote
npm install
npm run instalar      # baixa o Chromium headless (~114 MB) e liga em ~/.claude/skills
```

Sem isso, a skill continua valendo como método (os 9 passos e as 19
referências), mas os passos 4 e 8 — medidas e chicotada — não rodam. O próprio
`SKILL.md` manda declarar quais medições ficaram sem fazer nesse caso.

Conferir que tudo mede certo (roda os 3 exemplos, ~1 min):

```bash
npm run teste
```

Ele usa os exemplos como régua: `exemplos/ruim.html` tem que reprovar (32,6),
`exemplos/barbearia.html` tem que dar 100 e `exemplos/efeitos.html` tem que
fechar os 70 portões.

## Scripts soltos

```bash
node scripts/medidas.mjs --publico idoso --aparelho fraco --titulo "Barba feita em 30 minutos, sem fila." --letra 0.6
node scripts/chicotada.mjs minha-pagina.html --publico geral
node scripts/chicotada.mjs https://meusite.com.br --rubrica chicote/chicotada/rubrica.json
node scripts/pexels.mjs --busca "barber chair warm light" --quantos 6 --larguras 640,1280
```

O `pexels.mjs` baixa fotos do Pexels sem chave de API.

## Relação com as outras skills deste repo

- `unslop-ui` corta os tells de IA de copy de interface; `chicote` os proíbe na
  origem (`referencias/12-anti-slop.md`) e ainda mede o resultado.
- `humanizer` limpa a prosa; o `chicote` mede o orçamento de palavras por seção.
- `web-perf` audita performance; a `chicotada` já traz LCP, CLS e peso como
  portões que reprovam a página.
- `modern-web-guidance`, `tailwind-css-patterns` e as skills de animation dão
  técnica. O `chicote` decide o que entra — é o que o
  `referencias/11-outras-skills.md` diz explicitamente.

## Instalação direta (upstream)

```bash
git clone https://github.com/matheusmongarde/chicote.git ~/chicote
cd ~/chicote && npm install && npm run instalar
```

Em agentes que não são Claude Code (Codex, Cursor, OpenCode), aponte para
`SKILL.md`; o instalador só cria o atalho em `~/.claude/skills/chicote`.

## Pedágio do upstream

O chicote é MIT e grátis, mas o autor pede (no README e na interface) seguir
[@mongarde_](https://x.com/mongarde_) no X, cadastrar o projeto no
[mamaevireidev.com.br](https://mamaevireidev.com.br) e entrar na comunidade do
WhatsApp. É pedido do autor, não condição da licença.
