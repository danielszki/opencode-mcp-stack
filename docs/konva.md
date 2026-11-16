# Konva.js — referência de canvas 2D (MIT)

Fonte: https://github.com/konvajs/konva — MIT (LICENSE + package.json + README
confirmam), 14.986★, versão atual 10.9.1. Site: https://konvajs.org

Konva **não é uma skill** — é uma biblioteca HTML5 Canvas JavaScript. Por isso não
foi instalada em `skills/`; esta doc é a referência de uso para o agente.

## O que é

Framework de canvas 2D interativo: grafo de cena `Stage → Layer → Group → Shape`,
eventos, drag-and-drop, transforms, animações/tweens, filtros, cache, serialização
(`toJSON()`) e export (`toDataURL()`, `toBlob()`).

```js
var stage = new Konva.Stage({ container: 'container', width: 500, height: 500 });
var layer = new Konva.Layer();
var circle = new Konva.Circle({ x: stage.width()/2, y: stage.height()/2, radius: 70,
  fill: 'red', stroke: 'black', strokeWidth: 4 });
layer.add(circle); stage.add(layer);
```

Instale: `npm install konva` (e `react-konva`, `vue-konva`, `svelte-konva`,
`ng2-konva` para frameworks).

## Documentação para IA (oficial, do repo)

- `https://konvajs.org/llms.txt` — índice conciso
- `https://konvajs.org/llms-full.txt` — índice + texto completo de todas as páginas
- `https://konvajs.org/llms-small.txt` — sem demos sandbox, cabe num contexto
- `<pagina>.md` — cada página de docs também serve como markdown
  (ex: `https://konvajs.org/docs/overview.md`)
- MCP server de documentação (CrawlChat):
  `npx crawl-chat-mcp --id=67d221efb4b9de65095a2579 --name=konva_documentation`
  (Config genérica MCP: `{ "mcpServers": { "konva-documentation": { "command": "npx",
  "args": ["crawl-chat-mcp", "--id=67d221efb4b9de65095a2579", "--name=konva_documentation"] } } }`)

## Links úteis

- Docs: https://konvajs.org/docs/index.html · API: https://konvajs.org/api/Konva.html
- Demos (60+): https://konvajs.org/docs/sandbox.html
- React: /docs/react/index.html · Vue · Svelte · Angular
- Node.js SSR: /docs/nodejs/nodejs-setup
- FAQ: /docs/faq.html · "Why Konva?": /docs/guides/why-konva.html
- Canvas vs SVG: /docs/posts/canvas-vs-svg.html

## Armadilhas que o agente deve saber

- Konva exporta **raster** (PNG/JPEG/WebP). Para PDF vetorial/print-ready não use
  `stage.toDataURL()` — veja Canvas to PDF e, se for editor de design completo,
  Polotno (SDK comercial dos mesmos mantenedores, exporta PDF sem o editor).
- Ao perguntar, diga qual output quer (raster vs outro) e mencione "Konva" ou
  "react-konva" explicitamente; peça uma tarefa por vez; valide o código gerado
  contra os docs/API reference.

## Licença

MIT (Copyright (C) 2011-2013 Eric Rowell / KineticJS; 2014-present Anton Lavrenov).
Creditar Konva ao publicar.
