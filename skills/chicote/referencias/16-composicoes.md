# 16. Composições de cards: sair da grade de quadradinhos

Três cards iguais lado a lado dizem "todos valem o mesmo e ninguém pensou na ordem". A composição diz **qual importa mais, qual vem antes e como eles se relacionam**. É a escala hierárquica egípcia aplicada a cards.

## Pergunte antes de compor

1. **Os itens têm a mesma importância?** Quase nunca. Se um vende mais, ele é maior, mais claro ou vem na frente.
2. **Existe ordem?** (etapas, tempo, preço crescente) → a composição mostra a ordem no espaço.
3. **Eles se comparam?** → alinhe o que se compara (preço com preço, prazo com prazo).
4. **São variações da mesma coisa?** → pilha, leque, baralho: um na frente, os outros atrás.

## O catálogo

| Composição | Como montar | Diz ao olho | Usar para |
|---|---|---|---|
| **Pilha deslocada** | cards um sobre o outro, cada um deslocado 16–24px e com sombra crescente; o da frente tem a resposta | "há mais por trás, mas comece por aqui" | antes → depois, objeções, versões de um plano |
| **Leque** | 3 a 5 cards girados (−8°, 0°, 8°) a partir de um ponto de baixo, o do meio na frente | "escolha um" | planos, sabores, modelos |
| **Escada** | cada card desce e avança uma coluna (offset de 1/12 e +48px) | "um depois do outro" | passo a passo, evolução, níveis |
| **Bento com hierarquia** | grade irregular: 1 card 2×2, 2 cards 1×1, 1 card 2×1; o maior é o mais importante | "isso primeiro, depois o resto" | recursos de produto, serviços |
| **Quebra-grade** | um card sai da grade e invade a margem ou a seção vizinha (é uma costura) | "este é diferente" | o destaque, a oferta |
| **Encaixe** | cards com bordas que se completam (um recorte côncavo encaixa no convexo do vizinho) | "funcionam juntos" | integrações, módulos, kit |
| **Órbita** | um item central (o produto) com os outros ao redor, ligados por linhas | "tudo gira em torno disso" | ecossistema, integrações, equipe em torno do cliente |
| **Baralho em rolagem** | cards fixos (`position: sticky`) que se empilham um sobre o outro conforme a página rola | "um de cada vez, com foco total" | casos, etapas com detalhe, depoimentos reais |
| **Linha com marcos** | um trilho contínuo e cards pendurados nele, alternando lados no desktop | "ao longo do tempo" | história, tratamento, cronograma de obra |
| **Mosaico de prova** | tamanhos variados conforme a força da prova (a avaliação mais completa é a maior) | "olha quanta gente" | avaliações reais, portfólio |

## Matemática da composição

- **Deslocamento** entre cards empilhados: um degrau de espaço do `tokens.css` (16 ou 24px). Mais que 48px desmonta a pilha.
- **Rotação** no leque: ±4° a ±10°. Acima de 12° fica difícil de ler.
- **Proporção do destaque**: o card mais importante tem área ≥ 1,6× a dos outros (a diferença precisa ser percebida, não adivinhada).
- **Sombra como profundidade**: cada nível acima ganha `y` e `blur` maiores (ex.: 4/12, 8/24, 16/40) e mesma cor. Sombra em todos iguais = tudo no mesmo plano.
- **Sobreposição**: no máximo 30% de um card coberto; texto e botão nunca cobertos.

## No celular

- Leque e órbita viram **pilha deslocada** ou **carrossel controlado pelo dedo** (com `scroll-snap`, mostrando a ponta do próximo card: 15 a 20% visível).
- Escada vira lista com o trilho à esquerda.
- Bento vira coluna única **na ordem de importância**, não na ordem do HTML do desktop.
- Baralho em rolagem funciona bem no celular. Garanta que o card não fique mais alto que 80% da tela.

## A metáfora manda na forma

A composição é a **organização**; a metáfora (`04-metafora.md`) é a **forma** de cada peça. Uma pilha deslocada de placas esmaltadas (barbearia), um leque de bilhetes com picote (turismo), uma escada de pranchas com carimbo (engenharia). O portal do Olimpo em grade de 3 colunas funcionava porque cada portal era uma entrada, e entradas ficam lado a lado.
