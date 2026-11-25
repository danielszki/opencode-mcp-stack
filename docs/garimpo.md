# garimpo / skill-prospeccao (vendored)

Nove skills de prospecção e vendas do **[garimpo](https://github.com/matheusmongarde/garimpo)**
de **Matheus Mongarde**, redistribuídas sob licença **MIT**.

- **Commit de origem:** `ac28cde3` (2026-11-24)
- **Licença:** MIT, Copyright (c) 2026 Matheus Mongarde — `skills/<id>/LICENSE`
- **Origem das skills 01–08:** as mesmas da skill pública
  [`skill-prospeccao`](https://github.com/matheusmongarde/skill-prospeccao)
  (commit `696943c8`); o garimpo já as embarca dentro do sistema, em `skills/`.
  A `00-operador-garimpo` só existe no garimpo — ela liga as outras à API `/api/v1`.
- **Conteúdo:** apenas `SKILL.md` por skill (~124 KB no total). Não copiamos o
  sistema Next.js, `servicos/` (Rastro e WhatsApp), `prisma/`, `marca/` nem os
  modelos de prévia HTML — nada disso é skill.

## O que faz

Manual de operação comercial completa, canal-agnóstico (WhatsApp, LinkedIn,
e-mail frio, Direct). Funciona para qualquer oferta: SaaS, software sob medida,
agência, consultoria, profissional liberal, comércio local.

| Skill | Função |
|---|---|
| `00-operador-garimpo` | Rotina do dia via API `/api/v1`: ordem das chamadas, erros 409 do envio e o que nunca fazer. Ler primeiro quando o alvo é o sistema garimpo |
| `01-prospeccao-fria` | Lacuna real por tipo de negócio, fila Tier A/B/C, regras e templates por canal, primeira mensagem sem pitch |
| `02-pesquisa-de-lead` | Dossiê público em 5 minutos, sinais de momento (triggers), mapa de decisor, regra anti-achismo |
| `03-negociacao-whatsapp` | Condução consultiva em 5 etapas: valor, diagnóstico NEPQ, visualização, empilhamento, fechamento com reversão de risco |
| `04-quebra-de-objecoes` | Filtro dúvida real vs. "não" definitivo, fórmula C.D.D. (Chris Voss), matriz de 14 objeções |
| `05-follow-up-e-reconquista` | Cadência de até 3 toques, trava de 30 dias, parada no primeiro "não", win-back de 60–90+ dias |
| `06-lista-negra-e-governanca` | Lei da operação: 35+ termos banidos com substituição, opt-out definitivo, filtro de bots, autópsia pós-perda |
| `07-psicologia-por-perfil` | Ajuste por perfil do decisor (engenheiro, arquiteto, saúde, jurídico, gestor) e por usuário final leigo/idoso |
| `08-arquitetura-operacao-24-7` | CRM/banco, API em 5 endpoints, os 3 workers, aquecimento de chip, limites anti-banimento, logs |

## Ordem de leitura

`00` (se for operar pelo garimpo) → `06` (governança, é lei) → `01` → `02` →
`03` → `04` → `05`. A `07` e a `08` entram conforme o perfil do lead e a
necessidade de escalar a infraestrutura.

## Relação com as outras skills deste repo

- `06-lista-negra-e-governanca` é prosa comercial: combina com `humanizer`
  (tira tells de IA do texto) e `unslop-ui` (copy de interface).
- Para achar os negócios que alimentam a fila, `webscraping-expert` cobre
  extração de dados públicos; o garimpo faz isso com o Rastro (navegador real).

## Instalação direta (upstream)

```bash
git clone https://github.com/matheusmongarde/garimpo.git
# skills em garimpo/skills/, sistema completo em Next.js na raiz
```

As skills sozinhas, sem o sistema:

```bash
git clone https://github.com/matheusmongarde/skill-prospeccao.git
# skills 01–08 em skills/
```

## Pedágio do upstream

O garimpo é MIT e grátis, mas o autor pede (dentro do README e da interface)
seguir [@mongarde_](https://x.com/mongarde_) no X, cadastrar o projeto no
[mamaevireidev.com.br](https://mamaevireidev.com.br) e entrar na comunidade do
WhatsApp. É pedido do autor, não condição da licença.
