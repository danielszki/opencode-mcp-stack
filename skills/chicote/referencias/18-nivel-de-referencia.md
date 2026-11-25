# 18. O nível de referência: o mínimo aceitável

Este é o piso. Uma página do chicote precisa estar no nível das landing pages de produto mais bem feitas do mundo (o padrão de sites como os de Linear, Stripe, Apple, Mercury, Attio e dos templates premium de Framer). Se a página entregue parece um site de prefeitura, um documento do Word ou "um site que a IA fez", ela reprovou, mesmo com 100 nos números.

Nada aqui é para copiar marca ou texto de ninguém. É a **gramática** que esses sites dividem, e ela vale para qualquer nicho: barbearia, clínica, escritório, SaaS.

## A gramática

### 1. A moldura (canvas)
A página não encosta na borda da tela. O conteúdo principal mora em **painéis arredondados** (raio 24–32px) recuados 8–16px da janela, sobre um fundo de página levemente diferente (papel, cinza quente, a cor da marca). O hero é um painel; seções de virada também. Isso dá a sensação de objeto, de peça impressa.

```css
body { background: #e9e3d8; padding: 12px; }
.painel { border-radius: 28px; overflow: clip; }
```

### 2. Tipografia que tem voz
- **Fonte de título de verdade**, carregada (Google Fonts ou local). Nunca a fonte do sistema, nunca Georgia ou Arial no título. Pares que funcionam: Instrument Serif + Inter Tight; Fraunces (opsz, peso 300–400) + Inter; Newsreader + Geist; Bricolage Grotesque + Instrument Sans; DM Serif Display + DM Sans.
- **Título grande e apertado**: 56–96px no desktop, entrelinha 0,95–1,05, `letter-spacing` de −0,02em (serifa) a −0,045em (grotesca).
- **Peso leve na serifa** (400 ou menos): o tamanho já dá a força. Negrito em serifa grande vira jornal popular.
- **Duas cores no título ou na declaração**: a primeira parte em tinta cheia, a segunda em tinta apagada (40–55% de opacidade) ou em itálico. Isso cria leitura em dois tempos.
- Texto de apoio: 16–19px, cor apagada, no máximo 2 linhas no hero, medida de 38–46ch, centralizado com o título.
- Sobrelinha em **pílula**: "★ 4,9 · 212 avaliações", "Novo · Agenda online", com borda fina ou fundo levemente contrastado.

### 3. O hero padrão (escolha uma variação, nunca o hero de texto solto)
1. **Produto emergindo**: título e CTA centrados no alto; embaixo, a peça principal (tela, cartão, objeto, foto) subindo do fundo do painel, com 2 peças laterais menores e mais baixas (pódio), ligadas por linhas finas ao CTA.
2. **Produto na paisagem**: uma cena fotográfica ocupa o painel (montanha, céu, campo, ateliê); a peça principal fica sobre a cena e um **elemento da cena passa na frente dela** (grama, nuvem, folhagem, a mão), em PNG recortado. É o efeito "a interface mora no mundo".
3. **Objeto na mão / escultura**: um objeto real, segurado ou ladeado por figuras (estátuas, mãos), centralizado sob o título, com um padrão sutil no fundo (linhas de circuito, ASCII, grade).
4. **Colagem editorial**: o painel claro é recortado pela silhueta de uma foto vintage que invade a moldura (montanhas, pessoa, placa).

### 4. Prova logo abaixo do hero
Faixa de logos (clientes, parceiros, onde aparece) em tom apagado, ou, para negócio local, uma faixa de 3 números com divisória fina: "4,9 no Google", "30 min a barba", "Ter–sáb, 9h–20h".

### 5. Seções
- **Cabeçalho dividido**: título grande à esquerda (6 colunas) e parágrafo curto à direita (4 colunas), alinhados pela base. É o jeito de abrir seção desses sites.
- **Cards que mostram**: cada card tem uma **ilustração de verdade** em cima (pedaço da interface, foto tratada, gráfico, mini fluxo com cursor) e título + uma linha embaixo, centralizados. Ícone sozinho num círculo não é card.
- **Bento**: grade irregular (1 grande + 2 pequenos; 2/3 + 1/3), os cards com o mesmo raio e o mesmo material.
- **Declaração**: um parágrafo enorme (40–56px) centralizado, em duas cores, sobre um painel de cor forte. Uma vez por página.
- **Números**: 3 números grandes com rótulo, separados por linhas verticais finas.

### 6. Fotos com um só tratamento
Todas as fotos da página passam pelo **mesmo tratamento de cor** (a mesma temperatura, o mesmo contraste, a mesma granulação), como se fossem do mesmo ensaio. Em CSS:

```css
.foto { filter: saturate(.85) contrast(1.05) sepia(.12); }
.foto-wrap { position: relative; }
.foto-wrap::after { content: ""; position: absolute; inset: 0; background: #b0703c; mix-blend-mode: soft-light; opacity: .35; }
```

Foto de banco sem tratamento, cada uma de um jeito, é o sinal mais claro de página montada às pressas.

### 7. Detalhes que separam o amador do profissional
- Botões em **pílula** ou raio 12–14px, o principal cheio (escuro ou a cor da marca), o secundário fantasma ou claro. Altura 48–56px. Seta "›" discreta no principal.
- Avatares sobrepostos (pilha de 3–4 rostos) ao lado de uma prova ("Usado por 1.000+ times"). Só com rostos reais ou fotos de banco claramente ilustrativas.
- Linhas finas de 1px conectando elementos (CTA → cards do hero, nós de um fluxo).
- Fundo com padrão sutil: grade de pontos, linhas de circuito, ASCII, círculos concêntricos, sempre a 4–10% de opacidade.
- Cursor e etiquetas flutuantes ("nice flow!", "124 leads") dentro das ilustrações, dando vida.
- Espaço: seções com 96–160px de respiro vertical no desktop. Luxo é espaço.

## O teste do nível

Antes de entregar, ponha o print de 1440px ao lado de uma dessas referências e responda com sinceridade:
1. A tipografia do título tem a mesma classe? (fonte de verdade, tamanho, aperto)
2. O hero tem uma peça visual tão forte quanto? (produto emergindo, cena, objeto)
3. As fotos parecem do mesmo ensaio?
4. Os cards mostram alguma coisa ou só têm ícone?
5. Há moldura, respiro e detalhe (pílula, linha fina, padrão sutil)?

Um "não" = volta e refaz. Isso entra na rubrica (`nivel`).
