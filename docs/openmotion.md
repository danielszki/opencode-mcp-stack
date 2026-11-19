# OpenMotion (vendored)

Cópia integral das skills públicas [`openmotion`](https://github.com/nexu-io/openmotion)
da **nexu-io**, redistribuídas sob licença **Apache 2.0**.

- **Commit de origem:** `f27124d5` (2026-11-20), `metadata.version` das skills: `1.5.5`
- **Licença:** Apache License 2.0 — `skills/openmotion/LICENSE`
- **Conteúdo:** 7 skills em `skills/openmotion*/` (64 arquivos, ~880 KB):
  Markdown, referências, `agents/*.yaml` (prompts de agente, alguns em zh-CN),
  scripts auxiliares Python/Node (medição de frames, playback, delivery) e
  `openmotion-production/fonts/catalog.json`. Sem binários.

## As skills

| Skill | Papel |
|---|---|
| `openmotion` | Entrada única: instala/conecta o Studio + MCP e roteia para a workflow certa |
| `openmotion-director` | Criação original de motion videos/graphics (narrativa, encenação, revisão) |
| `openmotion-media` | Biblioteca de mídia (fontes, assets, brand kit) |
| `openmotion-production` | Edição e exportação estabelecidas (MP4 para YouTube/Shorts/Reels/TikTok) |
| `openmotion-recreate` | Reconstrução editável a partir de um vídeo de referência |
| `openmotion-template-to-video` | Renderiza um vídeo a partir de um template editável |
| `openmotion-video-to-template` | Converte um vídeo em template editável reutilizável |

## Nota de integração

As skills assumem o **OpenMotion Studio local + servidor MCP** da própria
`nexu-io/openmotion` (repo full-stack Node 22.18+, Apache 2.0 — não incluído
aqui). A skill raiz `openmotion` detecta a conexão MCP e, se faltar, guia a
instalação. Sem o Studio, as skills de produção ficam sem backend.

## Instalação direta (upstream)

```bash
git clone https://github.com/nexu-io/openmotion.git
# skills em <repo>/skills/, formato <id>/SKILL.md
```
