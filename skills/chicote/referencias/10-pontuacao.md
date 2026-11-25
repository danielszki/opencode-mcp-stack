# 10. Pontuação: 100 ou continua chicoteando

A nota tem duas partes. Os **70 pontos dos portões** são medidos pelo `chicotada.mjs`, sem conversa. Os **30 pontos da rubrica** são avaliados por você, e cada ponto exige evidência (texto exato, seletor, print). Sem evidência, o item vale zero.

**Meta: 100.** Máximo de 5 rodadas de correção. Se não chegar, pare e entregue o que falta. Nunca arredonde, nunca dê a nota "porque está quase".

## Portões medidos (70)

| id | Pontos | Passa quando |
|---|---|---|
| `cta-360` | 8 | o `[data-cta="principal"]` (ou o primeiro CTA detectado) está inteiro na primeira tela a 360×640 |
| `cta-desktop` | 2 | idem a 1440×900 |
| `sem-rolagem-lateral` | 3 | nenhuma das 3 larguras tem rolagem horizontal |
| `contraste` | 7 | ≥ 98% dos textos passam no mínimo do público e nenhum fica abaixo de 3:1 (parcial proporcional) |
| `alvos` | 4 | todo elemento clicável tem o lado menor ≥ alvo mínimo do público (links dentro de parágrafo são exceção) (parcial proporcional) |
| `fonte` | 4 | o texto de leitura está no corpo mínimo do público e nada fica abaixo do mínimo absoluto (parcial proporcional) |
| `lcp` | 5 | LCP ≤ 2,5 s no perfil lento (360px, CPU 4×, 4G ruim); 0 acima de 4 s, proporcional entre os dois |
| `cls` | 2 | CLS ≤ 0,1 |
| `peso` | 3 | bytes transferidos na primeira carga dentro do orçamento do aparelho |
| `seo` | 4 | 0,8 ponto para cada: `lang`, `title` 30–65, `description` 70–160, um único `h1`, `og:image` + `viewport` sem bloquear zoom |
| `movimento` | 2 | com `prefers-reduced-motion: reduce`, nenhuma animação infinita rodando |
| `enxuto` | 3 | metade: cada capítulo dentro do orçamento de palavras (proporcional); metade: nenhum jargão |
| `tipografia` | 3 | o `h1` usa uma fonte própria carregada (não a do sistema nem Georgia/Arial), com ≥ 56px a 1440, `letter-spacing` ≤ −0,01em e entrelinha ≤ 1,12 |
| `atmosfera` | 6 | ≥ 75% dos capítulos (e o rodapé) têm camada visual: gradiente, luz radial, textura ou foto; fundo chapado perde |
| `visual` | 5 | ≥ 3 peças visuais (foto real ou do Pexels, canvas, 3D em CSS, SVG grande), uma na primeira tela; `--tipo sistema` dispensa |
| `profundidade` | 5 | ≥ 3 elementos com sombra em camadas (3 pontos) e o CTA com relevo (2 pontos) |
| `eixo` | 4 | cards e botões centralizados no contêiner, ou à direita com texto à esquerda (3 pontos, proporcional); conteúdo dos cards centralizado (1 ponto) |

O script imprime a nota de cada portão, o que falhou e onde (seletor, texto, medida).

## Rubrica com evidência (30)

Preencha `chicote/chicotada/rubrica.json`:

```json
{
  "itens": [
    { "id": "hero-frase", "pontos": 4, "evidencia": "h1: 'Barba feita em 30 minutos, sem fila.' — 7 palavras, 3 linhas a 360px (print 360-dobra.png), concreta (30 min), do cliente (sem fila)" }
  ]
}
```

| id | Máx. | Nota máxima só se |
|---|---|---|
| `nivel` | 6 | o teste do nível de `18-nivel-de-referencia.md`: as 5 perguntas com "sim", cada uma com o print que prova; 0 se a página parece documento ou "site de IA" |
| `hero-frase` | 4 | a frase passa nos 5 testes de `02-historia.md` (−2 por teste reprovado) |
| `roteiro` | 3 | cada seção tem função única e responde a uma pergunta do visitante; CTA a cada ~1,5 tela no celular; nenhuma seção repetida |
| `metafora` | 4 | a metáfora do nicho está escrita e os componentes principais derivam dela; a composição dos itens mostra a importância (`16-composicoes.md`); nenhum passo 1-2-3 em fila de ícones |
| `composicao` | 3 | `composicao.md` completo: eixo, colunas, peso e porquê com número em cada capítulo; um único peso 1 por dobra; medidas vindas do `tokens.css` |
| `costuras` | 3 | toda transição entre capítulos tem costura escolhida (`13-costuras.md`), nenhuma linha de 1px nem troca seca de fundo; cabeçalho com comportamento justificado; rodapé como último capítulo com a forma da metáfora (`14-cabecalho-rodape.md`) |
| `copy` | 2 | nada da lista de `12-anti-slop.md`; botões dizem o que acontece; nenhuma prova inventada |
| `publico` | 2 | o checklist do perfil (`05-publico.md`) está cumprido, item por item |
| `imagem` | 3 | cada imagem ou efeito prova algo ou cria a atmosfera certa; `alt` com significado; regras do nicho regulado respeitadas; prompts entregues quando falta imagem; efeitos com as travas de `15-efeitos.md`; **prompt entregue em `prompts.md` para toda imagem que falta** |

Rode de novo com a rubrica para ter o total:

```bash
node scripts/chicotada.mjs <url> --publico idoso --rubrica chicote/chicotada/rubrica.json
```

## Ordem de correção

Corrija pelo que mais pesa e mais rápido resolve: `cta-360` → `contraste` → `atmosfera` → `visual` → `profundidade` → `alvos` → `lcp` → o resto. Na rubrica, a frase do hero vem primeiro: se ela muda, muita coisa muda junto.

## Hero 100

Para avaliar só o hero (pedido comum: "chicoteia meu hero"), use `--so-hero`: o script mede só a primeira tela (CTA, contraste, fonte, alvos e LCP) e a rubrica considera `hero-frase`, `metafora` e `composicao` daquela dobra. A regra é a mesma: 100 ou continua.
