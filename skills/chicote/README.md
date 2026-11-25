# chicote

> Site bonito é portfólio. Site que vende é site acessível.

**[Português](#português) · [English](#english)**

---

## Pedágio

O chicote é grátis para sempre. O pedágio é outro, e não custa nada:

1. Seguir o **[@mongarde_](https://x.com/mongarde_)** no X.
2. Cadastrar o seu projeto no ranking do **[mamaevireidev.com.br](https://mamaevireidev.com.br)**.
3. Dar uma força ao **[Clara Finance](https://github.com/cesaroeduardo/clara-finance?utm_source=mamaevireidev&utm_medium=ranking&utm_campaign=clara-finance&mvd_cid=zVTQdltE9CLQS7Yf)**, projeto de um amigo (uma estrela já ajuda).
4. Entrar na **[comunidade do X no WhatsApp](https://chat.whatsapp.com/GBKvnYBUEaaBqsJtzibh4r?s=cl&p=i&iam=2)**.

---

## Português

`/chicote` é uma skill para agentes de IA (Claude Code, Codex, Cursor e qualquer agente que lê arquivos) que constrói sites, landing pages, sistemas e componentes **que vendem**, e não para de chicotear até a página bater 100 pontos.

Ela não confia no gosto do modelo. Ela **manda e mede**. É por isso que funciona até em modelo pequeno.

### Instalar

Precisa do [Node.js 18+](https://nodejs.org).

```bash
git clone https://github.com/matheusmongarde/chicote.git ~/chicote
cd ~/chicote
npm install
npm run instalar      # baixa o Chromium que mede as páginas e liga a skill no Claude Code
npm run teste         # opcional: confere que tudo mede certo
```

O `npm run instalar` cria o atalho `~/.claude/skills/chicote` apontando para a pasta. Em outros agentes, aponte para o `SKILL.md`.

### Rodar

Abra uma conversa **nova** no Claude Code e conte a história:

```
/chicote Barbearia no Cambuí, Campinas. Cliente de 25 a 70 anos, chega pelo Google Maps no celular.
Quero que chamem no WhatsApp. Temos 4,9 no Google com 212 avaliações. HTML puro.
Referência: [link ou print de um site que você gosta]
```

Quanto mais da história você contar (o que é, pra quem, o que conta como venda, a prova que existe, o que você gosta e odeia), menos ela pergunta. Ela também pode chicotear uma página que já existe: `/chicote chicoteia o hero de https://meusite.com.br`.

O que volta:
- a página, na stack que você pediu;
- a nota (70 pontos medidos pelo script + 30 de rubrica com evidência);
- `chicote/prompts.md` com o prompt de cada imagem que falta, pronto para ChatGPT, Gemini ou Midjourney;
- `chicote/ficha.md`, `medidas/` e `composicao.md`: o porquê de cada decisão, para quem for mexer depois.

### O que ela faz

1. **Arranca a história.** Nicho, quem compra (idade, celular, pressa), a ação que conta como venda, a prova real. Sem história, não começa.
2. **Escreve o hero numa frase.** Se o produto não cabe numa frase, o problema não é o layout.
3. **Transforma o nicho em forma.** O card de um portal grego, a placa de preço da barbearia, o carimbo da engenharia. Nada de três cards iguais nem de passo 1-2-3 em fila.
4. **Calcula cada medida para o público real.** Para o idoso: 19px, alvo de 52px, contraste 7:1. O título sai de uma fórmula para caber em 3 linhas a 360px.
5. **Justifica a posição de cada elemento** com Fitts, Hick, escala modular, grade de 12 e peso visual.
6. **Costura uma seção na outra** e trata o cabeçalho e o rodapé como começo e fim da história.
7. **Não aceita página pobre.** O piso é o nível das melhores landing pages de produto: moldura em painéis, fonte de título de verdade, hero com peça visual forte, cards que mostram alguma coisa, fotos com um só tratamento, sombra em camadas, botão com relevo.
8. **Sem imagem, entrega o prompt**, em camadas quando a cena passa na frente do produto, e põe uma reserva bonita na página enquanto isso. Também baixa fotos do Pexels sem chave.
9. **Desenha quando a imagem não serve**: pontos que reagem ao dedo, holofote na malha, card que inclina em 3D, maquete em CSS, traço que se desenha, grão. Menos de 3 KB cada, sem travar o celular.
10. **Mede num navegador de verdade**, inclusive num celular de 360px com CPU 4× mais lenta e 4G ruim: CTA na primeira tela, contraste, toque, fonte, LCP, CLS, peso, SEO, movimento, texto e jargão, e o gosto (atmosfera, visual, profundidade, eixo, tipografia).
11. **Chicoteia até 100.** No máximo 5 rodadas. Se não chegar, diz o que falta, sem maquiar.

### Os scripts sozinhos

```bash
node scripts/medidas.mjs --publico idoso --aparelho fraco --titulo "Barba feita em 30 minutos, sem fila." --letra 0.6
node scripts/chicotada.mjs minha-pagina.html --publico geral
node scripts/chicotada.mjs https://meusite.com.br --rubrica chicote/chicotada/rubrica.json
node scripts/pexels.mjs --busca "barber chair warm light" --quantos 6 --larguras 640,1280
```

### Exemplos

| Página | Nota | O que mostra |
|---|---|---|
| `exemplos/ruim.html` | 32,6 de 70 nos portões | tudo o que a skill reprova: fundo chapado, sem imagem, fonte do sistema, texto ilegível, jargão |
| `exemplos/barbearia.html` | 100/100 | o nível mínimo: painéis, serifa grande, agenda, foto e recibo saindo do hero, bento com fotos tratadas, pódio de preços. Prompts em `barbearia-prompts.md` |
| `exemplos/efeitos.html` | 70/70 nos portões | os 6 efeitos funcionando |

Os exemplos mostram o método, não um visual para copiar. Cada projeto nasce da história dele.

### Estrutura

```
SKILL.md              as ordens diretas e o processo em 9 passos
referencias/          19 arquivos lidos sob demanda
efeitos/              pontos, holofote, inclinação 3D, maquete em CSS, traço e grão, prontos para colar
modelos/              ficha da história, mapa de composição, prompts de imagem
scripts/              instalar, medidas, chicotada (a auditoria) e pexels
exemplos/             a página ruim, a página 100 e a vitrine de efeitos
```

---

## English

`/chicote` (Portuguese for "whip") is a skill for AI coding agents that builds websites, landing pages, apps and components **that sell**, then keeps whipping the page until it scores 100. It doesn't trust the model's taste: it gives direct orders and measures them.

```bash
git clone https://github.com/matheusmongarde/chicote.git ~/chicote
cd ~/chicote && npm install && npm run instalar
```

Then, in a new Claude Code session: `/chicote <tell the story: what it is, who buys, what counts as a sale, references>`. Other agents: point them to `SKILL.md`.

- **Story first**, a one-sentence hero, and the niche turned into form (no three identical cards).
- **A quality floor**: framed panels, a real display typeface, a strong hero visual, cards that show something, one color treatment for every photo, layered shadows.
- **No image? It writes the prompt** (layered when the scene passes in front of the product) and downloads Pexels photos without an API key.
- **Measured in a real browser**, including a 360px phone with 4× CPU throttling and slow 4G: 70 points from the script (CTA, contrast, touch targets, LCP, SEO, word budget, atmosphere, visuals, depth, axis, typography) and 30 from an evidence-based rubric.

The instructions are in Portuguese; it answers in the user's language.

**The toll** (free, but please): follow [@mongarde_](https://x.com/mongarde_) on X, list your project on [mamaevireidev.com.br](https://mamaevireidev.com.br) and star a friend's project, [Clara Finance](https://github.com/cesaroeduardo/clara-finance?utm_source=mamaevireidev&utm_medium=ranking&utm_campaign=clara-finance&mvd_cid=zVTQdltE9CLQS7Yf).

---

MIT · feito por [@mongarde_](https://x.com/mongarde_)
