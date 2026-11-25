# 9. Desempenho e SEO

Página lenta não vende: o visitante vai embora antes de ler a frase. SEO ruim não vende: ninguém chega.

## Orçamento (Core Web Vitals)

| Métrica | Alvo | Como chegar lá |
|---|---|---|
| LCP (maior elemento visível) | ≤ 2,5 s no perfil lento da chicotada | o elemento do LCP (frase do hero ou imagem principal) sem lazy, com `fetchpriority="high"`; fonte com `font-display: swap` e pré-carregada |
| CLS (layout pulando) | ≤ 0,1 | `width`/`height` ou `aspect-ratio` em toda imagem e vídeo; fonte com métricas de reserva (`size-adjust`); nada injetado acima do conteúdo |
| INP (resposta ao toque) | ≤ 200ms | pouco JS, nada pesado no clique, sem hidratação desnecessária |
| Peso e JS | ver tabela do aparelho em `05-publico.md` | imagens AVIF/WebP com `srcset`, fontes subconjunto (latin), uma família ou duas no máximo |

## Imagens

- `srcset` + `sizes` com 2 ou 3 larguras. A imagem nunca é baixada com mais que 2× a largura em que aparece.
- `loading="lazy"` em tudo abaixo da dobra; **nunca** na imagem do LCP.
- `alt` descrevendo o que a imagem prova ("Cadeira de barbeiro de couro na Navalha de Ouro"), vazio (`alt=""`) só em decoração pura.

## Fontes

- No máximo 2 famílias (uma de título, uma de texto). Variável quando possível.
- `woff2`, subconjunto latin, `preload` só da usada acima da dobra.
- Pilha de reserva parecida (`Arial`, `system-ui`) para o texto aparecer na hora.

## SEO na construção

- `<html lang="pt-BR">` (ou o idioma certo).
- `<title>` de 30 a 65 caracteres: o que é + cidade/nicho + marca. Ex.: "Barbearia em Campinas no Cambuí | Navalha de Ouro".
- `<meta name="description">` de 70 a 160 caracteres, com a promessa e a ação.
- **Um único `<h1>`** = a frase do hero (ou próxima dela). Títulos de seção em `<h2>`, em ordem.
- `<meta name="viewport" content="width=device-width, initial-scale=1">`. Nunca bloquear zoom.
- Open Graph: `og:title`, `og:description`, `og:image` (1200×630, com a frase e a marca).
- `<link rel="canonical">`.
- Dados estruturados JSON-LD: `LocalBusiness` (com `address`, `geo`, `openingHours`, `telephone`, `aggregateRating` só se for real), `Product`/`Offer` para venda, `FAQPage` se houver perguntas.
- `robots.txt` e `sitemap.xml` se houver mais de uma página.
- HTML semântico: `header`, `main`, `section` com título, `footer`, `nav`, botões são `<button>`, links são `<a>`.

## Acessibilidade que também é SEO

- Texto real, nunca texto dentro de imagem.
- Links com texto que faz sentido fora de contexto.
- Foco visível em tudo que é clicável.
