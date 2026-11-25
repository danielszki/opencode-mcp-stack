# 13. Costuras: uma seção encaixa na outra

A página não é uma pilha de faixas separadas por uma linha. É **uma peça só**, como uma parede egípcia em registros: cada faixa tem função própria, mas a leitura passa de uma para a outra sem tropeçar. O lugar onde duas seções se encontram é a **costura**. Costura mal feita (linha cinza, troca seca de fundo, mesmo respiro em tudo) é o sintoma mais comum de página montada por partes.

## A regra

**Toda transição entre capítulos tem uma costura escolhida e justificada no `composicao.md`.** A pergunta é: *o que leva o olho da seção A para a B?*

Proibido como padrão:
- linha horizontal de 1px entre seções;
- troca seca de cor de fundo sem nada que atravesse;
- o mesmo `padding` em cima e embaixo de todas as seções (ritmo de metrônomo, sem respiração).

## Tipos de costura

| Costura | Como | Quando | Custo |
|---|---|---|---|
| **Elemento que atravessa** | um objeto da seção A invade a B (`margin-bottom` negativo, `translate`): a tela do produto, a placa de preço, o selo | hero → prova; virada → como funciona | zero |
| **Forma da metáfora** | a borda da seção tem a forma do nicho: rasgo de papel, recorte de planta, picote de bilhete, costura de couro, onda de água, degraus | qualquer troca de fundo | zero (SVG inline ou `clip-path`) |
| **Fio condutor** | uma linha, trilho ou caminho que continua de uma seção para a outra (a cota da engenharia, o trilho da linha do tempo, a rota no mapa) | passo a passo, processo, história | zero; desenhando com scroll: baixo |
| **Continuação de cor** | o fundo de A vira o de B num gradiente longo (≥ 40% da altura da tela), nunca num corte | mudar o clima (problema → solução, noite → dia) | zero |
| **Sobreposição de camadas** | a seção B sobe por cima de A com sombra e canto, como uma folha sobre outra | oferta, chamada final | zero |
| **Pergunta-ponte** | a última linha de A é a pergunta que o título de B responde ("E quanto custa?" → "O preço está na placa.") | entre qualquer par | zero |
| **Elemento fixo que muda** | algo fica parado (`position: sticky`) enquanto o conteúdo passa e muda de estado a cada seção (o número que sobe, a tela que troca) | demonstração em etapas | baixo com `IntersectionObserver`; não use evento de scroll |

## Ritmo vertical

O espaço entre capítulos não é igual em todo lugar. Ele diz a relação entre eles:

| Relação entre A e B | Espaço |
|---|---|
| B continua A (mesma ideia, próxima etapa) | 1× o espaço interno (ex.: 48px) |
| B muda de assunto | 2× (ex.: 96px) |
| B é a virada da história (problema → solução, prova → oferta) | 3× ou uma costura de forma, com troca de clima |

## Como escrever no `composicao.md`

```
Costura 1 → 2 (hero → preços): elemento que atravessa. A placa do combo sobe 48px por cima da borda do hero
(margin-top: -48px), porque o preço é a primeira pergunta de quem vem do Maps e o olho cai nele ao sair do CTA.
Costura 2 → 3 (preços → ritual): pergunta-ponte. Última linha "E como é a barba?" → título "O ritual, do jeito antigo."
Costura 3 → 4 (ritual → rodapé): forma da metáfora. A seção escura termina num recorte de toalha dobrada
(clip-path) e o rodapé começa nela.
```

## No celular

- Costura que depende de lado a lado (elemento que invade a coluna vizinha) vira costura vertical: o elemento sobe por cima da borda de cima.
- Forma de borda: altura de 16 a 32px. Mais que isso rouba tela.
- Nada de costura que precise de hover.
