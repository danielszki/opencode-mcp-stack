# 2. História: o roteiro que vende

## O hero em uma frase

A frase do hero carrega o site inteiro. Fórmula:

> **[Resultado desejado] para [quem], sem [a dor ou o esforço que ele teme].**

Variações aceitas:
- Resultado + prazo: "Seu site no ar hoje. Pague uma vez."
- Antes → depois: "Do Google Maps ao Pix, sem planilha no meio."
- Pergunta que o visitante já se faz, respondida: "Dor nas costas? Sem cirurgia, em 8 sessões."

Teste da frase (todos precisam passar):

| Teste | Como medir |
|---|---|
| Específica | Trocando o nome pelo do concorrente, deixa de ser verdade? |
| Curta | ≤ 12 palavras, ou ≤ 3 linhas a 360px no tamanho calculado pelo `medidas.mjs` |
| Concreta | Tem um substantivo que dá para ver (Pix, sessão, mesa, site) ou um número |
| Do cliente | Fala do resultado dele, não da empresa ("nós somos…" reprova) |
| Sem jargão | Uma pessoa de 70 anos entende de primeira |

A linha de apoio (subtítulo) faz o que a frase não faz: diz **como** ou **para quem**, em no máximo 2 linhas no celular.

## A equação de valor (Hormozi) aplicada à página

**Valor = (Resultado × Chance de dar certo) ÷ (Tempo até o resultado × Esforço)**

Cada capítulo deve mexer em pelo menos um termo. Escreva no roteiro qual:

| Termo | O que a página faz | Exemplo |
|---|---|---|
| Resultado ↑ | mostra o depois, concreto | "Agenda cheia na terça" |
| Chance ↑ | prova real, garantia, demonstração ao vivo | "4,9 no Google, 212 avaliações" |
| Tempo ↓ | prazo curto e visível | "No ar em 10 minutos" |
| Esforço ↓ | menos campos, menos telas, "fazer depois" | "Só o nome é obrigatório" |

## Os capítulos

Uma landing que vende quase sempre cabe nesta espinha. Corte o que não tiver material real.

| # | Capítulo | Função | Pergunta do visitante | Ação disponível |
|---|---|---|---|---|
| 1 | Hero | fisgar | "Isso é pra mim?" | CTA principal |
| 2 | Virada | mostrar o resultado / o produto funcionando | "Como fica na prática?" | CTA |
| 3 | Prova | aumentar a chance | "Funciona mesmo?" | — |
| 4 | Como funciona | reduzir esforço percebido | "É difícil?" | — |
| 5 | Objeção | desarmar o medo principal | "E se…?" | — |
| 6 | Oferta | pilha de valor, depois o preço | "Quanto custa e o que vem?" | CTA principal |
| 7 | Chamada final | decisão | "E agora?" | CTA principal |

Regras:
- **O CTA aparece pelo menos a cada ~1,5 tela de rolagem no celular** (ou fica fixo numa barra inferior em páginas de contato).
- **Nenhum capítulo repete a função de outro.** Duas seções de "benefícios" viram uma.
- **Preço só depois da pilha de valor**, nunca antes do visitante entender o resultado.
- Página de contato local (barbearia, clínica, oficina) pode ter 4 capítulos: hero com contato, serviços com preço ou faixa, prova, onde fica e horário.

## Copy

- Frase curta. Verbo concreto. Número quando existir.
- Título de seção é **frase**, nunca rótulo ("Por que escolher a gente" reprova; "Você sai com a dor no 2 de 10" passa).
- Botão diz o que acontece: "Chamar no WhatsApp", "Ver meu site pronto". Nunca "Saiba mais", "Clique aqui", "Enviar".
- Sem superlativo vazio ("melhor", "incrível", "revolucionário"). Troque pelo fato que o justificaria.
- Sem depoimento, número ou logo de cliente inventado. Se não há prova, use demonstração, garantia ou "veja funcionando".

## Orçamento de palavras

Texto demais esconde a frase que vende. O `chicotada.mjs` conta as palavras de cada capítulo (portão `enxuto`):

| Onde | geral / jovem | idoso | b2b / técnico |
|---|---|---|---|
| Hero inteiro (título + apoio + botões + prova) | ≤ 35 | ≤ 30 | ≤ 35 |
| Cada seção | ≤ 90 | ≤ 70 | ≤ 110 |
| Card | ≤ 20 | ≤ 15 | ≤ 30 |
| Parágrafo | ≤ 3 linhas a 360px | ≤ 3 linhas | ≤ 4 linhas |

Passou do orçamento? Troque parágrafo por número, lista de fatos por tabela, explicação por demonstração, instrução por botão.

## Jargão: proibido

O script procura e tira pontos: "solução completa/inovadora/integrada", "inovador", "revolucionário", "disruptivo", "alavancar", "potencializar", "sinergia", "de ponta", "excelência", "qualidade e compromisso", "eleve seu…", "outro nível", "agregar valor", "experiência única", "empoderar", "bem-vindo ao nosso site", "saiba mais", "clique aqui", "lorem ipsum", "nosso compromisso", "somos uma empresa", "transforme sua presença/negócio" (e os equivalentes em inglês: "next level", "game changer", "seamless", "cutting-edge", "unlock your", "elevate your").

Teste da tia: se a frase precisa de explicação para alguém de 70 anos que nunca trabalhou com aquilo, é jargão.

## Componente também é história

Antes de pôr qualquer elemento, responda: **que passo da jornada ele é?**

- Um botão é a decisão.
- Um card é uma escolha ou uma prova (não é enfeite para encher grade).
- Um número é a prova mais curta que existe.
- Um ícone só entra se fizer a leitura mais rápida que a palavra sozinha.
- Uma animação mostra causa e efeito ou guia o olhar até a ação.

Se a resposta for "deixa mais bonito", corte.
