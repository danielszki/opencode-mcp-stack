# 4. Metáfora: o nicho vira forma

Card genérico é o que sobra quando ninguém pensou no nicho. A saída não é enfeitar o card: é **descobrir que forma esse conteúdo teria no mundo real daquele negócio** e desenhar o componente a partir dela.

## O caso que originou a regra: o Olimpo

No painel Olimpo (mamãe virei dev), o tema é o Olimpo grego. O card pequeno deixou de ser retângulo e virou **um portal**: topo em arco (meio círculo), uma linha interna fina formando arco e colunas, um fecho dourado em losango no alto e uma placa com o nome na base. O material é vidro fosco sobre o céu. Tudo em CSS, sem imagem:

```css
.card-portal {
  aspect-ratio: 3 / 4;
  border-radius: 50% 50% 20px 20px / 37.5% 37.5% 20px 20px; /* arco = meia largura = 37,5% da altura em 3:4 */
  container-type: inline-size;   /* o conteúdo escala com o portal (cqw) */
  backdrop-filter: blur(24px) saturate(1.7);
}
.card-portal::before { inset: 6px; border: 1px solid rgb(31 43 69 / .12); border-radius: inherit; } /* arco e colunas */
```

Repare no porquê matemático: o raio é **50% da largura**, que em 3:4 dá **37,5% da altura**. Com `9999px` o navegador encolheria todos os raios e a base ficaria reta. A forma veio do nicho, o número veio da geometria.

## O procedimento

1. **Liste 10 coisas reais do nicho**: objetos, materiais, ferramentas, documentos, gestos, lugares, sons. Barbearia: navalha, cadeira, espelho, toalha quente, poste listrado, tabela de preço em placa, pente, ficha de cliente, couro, azulejo.
2. **Escolha uma metáfora central** que tenha forma clara e não pareça fantasia. Critério: um cliente do nicho reconhece em 1 segundo.
3. **Derive os 5 componentes que mais aparecem** a partir dela:
   - o card (forma do contorno, material, textura);
   - o divisor de seção (linha, corte, costura, cota);
   - o número de destaque (como ele apareceria naquele mundo);
   - o passo a passo (que estrutura do catálogo combina com a metáfora);
   - o botão (o botão continua botão, mas o material ou o detalhe conversa com a metáfora).
4. **Teste de função**: alguém de 70 anos ainda sabe onde clicar? O preço está legível? Se a metáfora atrapalhar, ela sai daquele componente.
5. **Escreva no `composicao.md`**: a metáfora, os componentes derivados e o porquê de cada um.

## Banco de metáforas por nicho

Ponto de partida, não receita. Prefira sempre o que a ficha revelar sobre aquele negócio específico.

| Nicho | Metáfora | Card | Divisor | Número | Passo a passo |
|---|---|---|---|---|---|
| Engenharia | prancha técnica | folha com carimbo no canto inferior direito (título, escala, data) | linha de cota com setas e medida | cota: valor entre traços | escada como etapas de obra, com cotas de prazo |
| Arquitetura | planta e corte, luz entrando | recorte de planta com hachura e norte | linha de corte (A–A') | área em m² com rótulo de ambiente | sequência de cortes: terreno → estrutura → luz |
| Barbearia | balcão de navalha | placa de preço esmaltada, cantos chanfrados | listra do poste, fina | preço em placa, serifa condensada | ritual: toalha → navalha → acabamento em linha do tempo |
| Odontologia / saúde | prontuário limpo | ficha com aba lateral e campo preenchido | régua milimetrada discreta | "8 sessões" como dose em receita | linha do tempo do tratamento por sessão |
| Advocacia | autos e carimbos | folha de processo com numeração lateral | linha dupla clássica | artigo e parágrafo como numeração | tramitação: petição → audiência → decisão (sem prometer resultado) |
| Pet shop | coleira e plaquinha | tag de coleira com furo e nome | pegadas espaçadas pela grade | peso/idade como plaquinha | banho → tosa → entrega em escada |
| Nutrição | prato e mercado | etiqueta de feira / rótulo nutricional | linha de mesa | tabela nutricional como prova | semana como cardápio, dia a dia |
| Confeitaria | caixa de confeitaria | caixa com laço/selo, tampa | renda de papel | peso em gramas, como balança | camadas do bolo como pilha sobreposta |
| Academia | quadro de treino | ficha de treino com séries × repetições | fita de marcação no chão | carga em kg como placa de anilha | periodização em linha do tempo |
| Imobiliária | planta e chave | chaveiro com etiqueta | linha de lote | m², quartos, vagas como placa de obra | visita → proposta → chave |
| SaaS / ferramenta | o próprio produto | tela real do sistema, recortada | trilha de dados (pipeline) | métrica com variação ▲▼ | o fluxo do sistema funcionando (vídeo/tela) |
| Educação / curso | caderno e lousa | página de caderno com margem | linha de pauta | nota / aula nº | módulos como sumário de livro |
| Restaurante | cardápio impresso | prato fotografado de cima + ficha | linha pontilhada de cardápio (preço alinhado) | preço com pontilhado | reserva → mesa → prato |
| Turismo | passaporte e bilhete | bilhete destacável com picote | linha de rota | distância/tempo como carimbo | roteiro dia a dia em mapa |

## O que a metáfora nunca faz

- Esconder o CTA, o preço ou o contato.
- Virar fantasia infantil (exceto se o público for infantil).
- Usar imagem pesada onde CSS resolve (o portal do Olimpo é só CSS).
- Mudar de metáfora no meio da página. Uma por site; os componentes variam dentro dela.
- Copiar a metáfora de outro projeto da pessoa (cada projeto tem identidade própria).
