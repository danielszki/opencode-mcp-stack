# 15. Efeitos: quando não é imagem, é efeito (sem travar)

Às vezes a imagem certa não existe, ou pesaria demais, ou não diz nada. A saída pode ser **desenhar com código**: um campo de pontos que reage ao mouse, um objeto em 3D feito só de CSS, uma malha que acende onde o dedo passa. Feito certo, pesa menos de 3 KB e prende o olho mais que uma foto de banco.

Feito errado, derruba a página no celular fraco. Por isso cada efeito aqui vem com o custo e as travas.

## Quando usar efeito no lugar de imagem

- O produto é abstrato (software, serviço, consultoria) e não há tela real ou foto boa.
- O nicho tem uma textura própria que dá para desenhar (pontos de uma planta, malha de engenharia, ondas, constelação, grão de papel).
- O aparelho do público é `medio` ou `forte` para efeitos com movimento. No `fraco`, só a versão estática.
- **Nunca** no lugar de uma prova (foto do resultado, tela real do produto).

## As travas (obrigatórias em todo efeito)

1. **Só `transform` e `opacity`** em CSS animado; em canvas, desenhar só quando algo muda.
2. **Para quando sai da tela** (`IntersectionObserver`) e quando a aba some (`visibilitychange`).
3. **`prefers-reduced-motion: reduce`** → versão estática, sem `requestAnimationFrame` rodando.
4. **Toque**: sem hover no celular. O efeito reage ao toque e arrasto ou fica estático, nunca depende de mouse para fazer sentido.
5. **Canvas com densidade de pixels limitada** (`devicePixelRatio` no máximo 2) e número de pontos proporcional à área (não fixo).
6. **Não bloqueia o LCP**: o efeito carrega depois (`defer`, `requestIdleCallback`) e o espaço dele já está reservado (`aspect-ratio`), para não pular o layout.
7. **Decorativo**: `aria-hidden="true"`, `pointer-events: none` se não for clicável.
8. **Orçamento**: ≤ 3 KB de JS por efeito, ≤ 2 efeitos com movimento por página, nunca dois na mesma dobra.

## As receitas (código em `efeitos/`, testado)

| Arquivo | O que é | Serve para | Custo |
|---|---|---|---|
| `efeitos/pontos.js` | campo de pontos em canvas; os pontos perto do cursor/dedo crescem e acendem, com mola de volta | hero de SaaS, tecnologia, engenharia, "dados" | ~2 KB, desenha só enquanto há movimento |
| `efeitos/holofote.css` | malha pontilhada em CSS puro (`radial-gradient`) com um holofote que segue o cursor (`--x`, `--y`) | fundo de seção, card em destaque | CSS + 6 linhas de JS; só `background-position` de uma máscara |
| `efeitos/inclinacao.js` | card inclina em 3D seguindo o cursor (`perspective` + `rotateX/Y`), com reflexo | card de oferta, produto, "placa", portal | ~1 KB, só `transform` |
| `efeitos/camadas.css` | objeto 3D só de CSS: camadas empilhadas com `translateZ` (prédio, pilha de documentos, maquete) | arquitetura, engenharia, "pilha de valor" | zero JS; gira devagar só com `no-preference` |
| `efeitos/revelar.js` | traço SVG que se desenha quando entra na tela (`stroke-dashoffset`): cota, rota, assinatura, trilho | fio condutor entre seções | ~0,6 KB, uma vez |
| `efeitos/grao.css` | grão de papel/filme em SVG inline (`feTurbulence`) estático | dar matéria ao fundo sem imagem | zero JS, estático |

Veja todos funcionando em `exemplos/efeitos.html`.

## Como escolher

| Nicho / clima | Efeito |
|---|---|
| Tecnologia, SaaS, dados | `pontos.js` no hero, `revelar.js` no fluxo |
| Engenharia | `holofote.css` com malha milimetrada, `revelar.js` nas cotas |
| Arquitetura | `camadas.css` (maquete), `revelar.js` (planta se desenhando) |
| Luxo, estética, joalheria | `inclinacao.js` com reflexo no card de oferta, `grao.css` |
| Serviço local para idoso | fotos reais tratadas + efeitos na versão estática (maquete parada, grão, traço já desenhado); nada se mexendo sozinho |

## Escreva no `composicao.md`

```
Efeito: pontos.js no hero (lado direito, 5/12, aspect-ratio 1/1).
Por quê: produto abstrato (API de dados), sem tela bonita para mostrar; os pontos são os "registros" que o
produto organiza, e acender perto do cursor mostra causa e efeito.
Travas: para fora da tela, estático com reduced-motion, DPR ≤ 2, 1 ponto a cada 28px, carregado com defer.
```
