# 3. Composição: nada fica onde está por acaso

Os egípcios não desenhavam o que o olho via: desenhavam **o que precisava ser entendido**, com proporção fixa, tamanho pela importância e faixas de leitura. Leonardo **observava** antes de compor: anatomia, luz, perspectiva, quem olha. Uma página que vende junta as duas coisas: um sistema de proporção rígido e o teste com o observador real.

## Os cinco princípios, traduzidos em regra

| Fonte | Princípio | Regra na página |
|---|---|---|
| Cânone egípcio | toda figura deriva de uma unidade (a grade de 18 quadrados) | **Unidade base**: todo espaçamento é múltiplo de 8px (4px só dentro de componente pequeno). Toda largura ocupa um número inteiro de colunas. Nada "mais ou menos". |
| Escala hierárquica | o faraó é maior porque importa mais | **Tamanho = importância.** O peso visual segue o roteiro: o CTA principal e a frase do hero são os maiores pesos da primeira tela. Só um peso 1 por dobra. |
| Registros | a parede é lida em faixas horizontais | **Capítulos são faixas.** Cada seção tem começo e fim claros (respiro de 2 a 3× o espaço interno entre seções) e uma função só. |
| Perspectiva de Leonardo | o olho segue linhas, contraste e luz | **Rota do olhar desenhada**: o maior contraste da tela fica onde a ação está. Linhas e direções apontam para o CTA, nunca para fora. |
| Observação de Leonardo | estudar o corpo antes de pintar | **Teste com o observador real**: celular de 360px, tela suja, sol, olho cansado. A chicotada faz isso. |

## A matemática que manda

### Escala tipográfica
Tamanho do degrau `n`: **`t(n) = base × razão^n`**, arredondado para inteiro.

| Razão | Nome | Quando usar |
|---|---|---|
| 1,2 | terça menor | sistema, painel, público idoso (saltos pequenos, tudo legível) |
| 1,25 | terça maior | padrão para landing e site institucional |
| 1,333 | quarta | landing de impacto, pouco texto |
| 1,5 a 1,618 | quinta / áurea | só para o título do hero contra o corpo, nunca para a escala inteira |

A proporção áurea (1,618) é uma razão possível, não mágica. A evidência de que ela "vende" é fraca. Use quando o contraste de tamanho precisa ser dramático.

### Entrelinha
Quanto maior a letra, menor a entrelinha relativa: **`entrelinha ≈ 1,1 + 0,4 × (corpo ÷ tamanho)`**. Corpo de 16px → 1,5. Título de 64px → 1,2. Público idoso: some 0,1 no texto de leitura.

### Medida da linha
Leitura confortável entre **45 e 75 caracteres** por linha (66 ideal). Em CSS: `max-width: 66ch` no parágrafo. Linha longa cansa e o olho se perde na volta; linha curta demais quebra o ritmo.

### Título que cabe
Largura média de um caractere ≈ 0,52 × tamanho da fonte em grotescas; serifadas em negrito e fontes largas chegam a 0,58–0,62 (passe `--letra 0.6` ao `medidas.mjs`). Depois confira no print de 360px: o número é estimativa, o print é a verdade. Para a frase de `L` caracteres caber em `N` linhas numa largura `W`:
**`tamanho máximo = (W × N) ÷ (L × 0,52 × 1,15)`**, onde 1,15 é a perda média por quebrar a linha em palavras inteiras. O `medidas.mjs` calcula isso para 360px.

### Lei de Fitts (alvos)
Tempo para acertar um alvo: **`T = a + b × log₂(1 + D/L)`** (D = distância, L = largura do alvo). Conclusões práticas:
- CTA grande e perto de onde o polegar já está (metade de baixo da tela no celular).
- Barra fixa de contato no rodapé do celular ganha de botão no topo.
- Alvo de toque mínimo: 44px (geral), 48px (idoso, aparelho fraco), com 8px de folga entre alvos.

### Lei de Hick (escolhas)
Tempo de decisão: **`T = b × log₂(n + 1)`** (n = opções iguais). Cada opção a mais na mesma tela atrasa a decisão.
- Um CTA principal por dobra. O secundário tem metade do peso visual (contorno, não preenchido).
- Menu com no máximo 5 itens no topo. Formulário com o mínimo de campos.
- Planos de preço: 3 no máximo, com um destacado.

### Contraste
Razão WCAG: **`(L1 + 0,05) ÷ (L2 + 0,05)`**, com luminância relativa de cada cor. Mínimos: 4,5:1 texto normal, 3:1 texto grande (≥ 24px, ou ≥ 18,66px negrito) e elementos de interface. Público idoso: 7:1. O `chicotada.mjs` mede.

### Grade
12 colunas no desktop (divisível por 2, 3, 4 e 6), 4 ou 6 no celular. Goteira de 16px (celular) a 24px (desktop). Arranjos com tensão: 7/5, 8/4, 5/7. O 6/6 simétrico é calmo demais para hero de venda: use quando a página pede confiança e ordem (advocacia, contabilidade).

## Alinhamento e eixo

Não deixe tudo encostado à esquerda por inércia. Escolha o **eixo** de cada capítulo e escreva o porquê:

| Eixo | Quando | Por quê |
|---|---|---|
| Centro (**padrão para cards e botões**) | hero de uma frase só, chamada final, preço, todo card e todo botão | simetria = decisão, foco total. Card e botão encostados à esquerda reprovam no portão `eixo` |
| Esquerda | coluna de texto ao lado de um visual (a exceção: texto à esquerda + card/visual à direita), formulários | o olho volta ao mesmo ponto de partida; o visual à direita equilibra o peso |
| Direita | números, preços, datas em tabela | alinha as casas decimais |
| Diagonal / escada | passo a passo, evolução, antes → depois | o olho desce em Z e "sente" o avanço |
| Assimétrico (7/5, texto de um lado, imagem sangrando do outro) | hero com produto ou foto forte | tensão visual, a imagem prova e o texto vende |

**Texto justificado:** só com `hyphens: auto`, `lang` correto no HTML e medida entre 55 e 75 caracteres. Em coluna estreita (celular) ele abre "rios" de espaço que atrapalham a leitura de quem tem dislexia ou enxerga mal. Por isso: no celular, alinhe à esquerda; no desktop, justifique só blocos editoriais largos, se a direção pedir. Justificar é uma decisão da composição, não um padrão.

## Catálogo de estruturas dominantes

Toda seção tem **uma** estrutura dominante, nomeada antes de construir. Escolha pela função, não pelo hábito. Proibido repetir a mesma estrutura em seções vizinhas.

| Estrutura | Serve para | Em vez de |
|---|---|---|
| **Frase-pôster**: uma frase gigante, um botão, muito ar | hero, chamada final | hero com 3 parágrafos |
| **Produto sangrando**: tela real ou foto saindo da borda, texto 5/12 do outro lado | virada, demonstração | mockup centralizado com sombra |
| **Escada**: passos descendo em diagonal, cada um deslocado uma coluna | como funciona (3 a 4 passos) | três ícones lado a lado com "1, 2, 3" |
| **Linha do tempo vertical** com um trilho e marcos | processo longo, história da empresa, tratamento em sessões | lista de cards |
| **Pilha sobreposta**: cartas deslocadas, a da frente com a resposta | antes → depois, objeções, planos | cards em grade |
| **Recibo / nota**: lista com valores alinhados à direita e total | pilha de valor da oferta | lista de bullets com check verde |
| **Número gigante** com rótulo pequeno e uma frase de contexto | prova (avaliações, clientes, anos) | faixa de 4 números iguais |
| **Mosaico assimétrico** (1 grande + 2 pequenos) | portfólio, galeria, serviços com foto | grade de fotos iguais |
| **Mapa / planta** com pontos clicáveis | negócio local, imóvel, arquitetura | endereço em parágrafo |
| **Conversa**: perguntas e respostas como mensagens | FAQ, objeções | sanfona genérica |
| **Prontuário / ficha**: coluna fixa de identidade + capítulos ao lado | perfil profissional, página de serviço técnico | biografia em parágrafos |
| **Tabela de verdade** | comparação com concorrente ou com "fazer sozinho" | dois cards "nós vs eles" |

Escada, pilha e linha do tempo já resolvem quase todo "passo a passo" sem cair no 1-2-3 lado a lado.

## Peso visual

Peso = tamanho × contraste × cor saturada × isolamento (ar em volta). Na tabela `chicote/composicao.md`, ordene os elementos de cada dobra por peso (1, 2, 3…). Regras:
- **Um** peso 1 por dobra.
- No hero, o peso 1 é a frase ou o CTA. Nunca o logo, nunca uma imagem decorativa.
- Um único bloco preenchido na cor de destaque por tela: o que mais importa.
- Se dois elementos disputam o peso 1, um deles está errado. Reduza o outro.

## Rota do olhar

Desenhe a rota no `composicao.md`: de onde o olho entra (o maior contraste), por onde passa e onde termina (o CTA). No celular, a leitura é vertical e o polegar mora embaixo: a ação mais importante deve estar ao alcance dele sem esticar.
