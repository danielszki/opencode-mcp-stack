# 17. Atmosfera e profundidade: a página não é uma folha de Word

A página que parece Word 2007 tem três sintomas: **fundo de uma cor só, tudo no mesmo plano e tudo encostado à esquerda**. A pintura clássica resolve isso com luz e plano: de onde vem a luz, o que está na frente, o que está atrás. Leonardo chamava isso de *chiaroscuro* e *sfumato*. Aqui vira CSS.

## 1. Atmosfera: de onde vem a luz deste lugar?

Antes de escolher a cor do fundo, responda: **onde esse negócio acontece e como é a luz lá?**

| Lugar | Luz | Fundo |
|---|---|---|
| Barbearia | luminária quente sobre couro e madeira | escuro de couro + radial âmbar vindo de cima + grão |
| Clínica | luz branca difusa de janela grande | branco quente + radial de janela no canto + sombra suave embaixo |
| Escritório de engenharia | luz fria de prancheta | papel milimetrado claro + holofote na malha |
| Restaurante à noite | velas, luz baixa | quase preto + radiais quentes pontuais + foto com véu |
| SaaS | tela acesa no escuro | escuro azulado + radial da cor da marca saindo do produto |
| Praia, turismo | sol forte | gradiente longo céu → areia, sombras duras |

### Receitas

```css
/* luz de luminária vindo de cima + respingo de cor embaixo + base */
.couro {
  background-color: #140e0a;                  /* sempre: cor base por baixo do gradiente */
  background-image:
    radial-gradient(70% 55% at 50% 0%, rgb(217 164 65 / .16), transparent 70%),
    radial-gradient(40% 40% at 85% 100%, rgb(179 38 30 / .10), transparent 70%),
    linear-gradient(180deg, #1f1611, #140e0a 60%);
}
/* grão: matéria sem imagem (efeitos/grao.css) */
.couro::before { content: ""; position: absolute; inset: 0; z-index: -1; background-image: var(--grao); opacity: .07; }

/* foto com véu: o texto fica legível e a foto continua dando o clima */
.capa { background: linear-gradient(180deg, rgb(20 14 10 / .2), rgb(20 14 10 / .85)), url(capa-1280.jpg) center / cover; }
```

### Ritmo claro/escuro
Alterne o clima entre capítulos para marcar as viradas da história: escuro (o lugar, a emoção) → claro (o preço, a decisão racional) → escuro (o ritual, a experiência) → claro (a placa, a ação). Nunca 5 seções seguidas com o mesmo fundo.

## 2. Profundidade: o que está na frente?

A escala hierárquica (03-composicao) diz o tamanho. A profundidade diz **a altura**: o que importa mais está mais perto do olho.

### Três níveis de elevação (use os três, nunca só um)

```css
--sombra-1: 0 1px 2px rgb(0 0 0 / .25), 0 2px 6px rgb(0 0 0 / .18);                                   /* chip, selo */
--sombra-2: 0 2px 4px rgb(0 0 0 / .2), 0 12px 24px -6px rgb(0 0 0 / .35), 0 24px 48px -16px rgb(0 0 0 / .35);  /* card */
--sombra-3: 0 4px 8px rgb(0 0 0 / .2), 0 24px 40px -12px rgb(0 0 0 / .45), 0 48px 80px -24px rgb(0 0 0 / .5);  /* destaque, foto */
```

Cada sombra tem **três camadas**: contato (curta e escura, encosta o objeto na superfície), média (dá o volume) e longa (a luz ambiente). Uma camada só parece adesivo.

### Material
- **Brilho no topo**: `inset 0 1px 0 rgb(255 255 255 / .12)`. A luz bate na borda de cima.
- **Filete interno**: `inset 0 0 0 1px rgb(cor-de-destaque / .2)` ou um `::before` com `inset: 8px` e borda fina (a moldura da placa).
- **Gradiente de 170°**, levemente mais claro em cima: o material recebe luz.

### O botão que pede para ser apertado

```css
.cta {
  background-color: #d9a441;
  background-image: linear-gradient(180deg, #f3d38a, #d9a441 55%, #c4892a);
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / .65),   /* brilho no topo */
    inset 0 -2px 0 rgb(138 90 18 / .45),    /* espessura embaixo */
    0 1px 0 #8a5a12,                        /* borda de contato */
    0 10px 24px -8px rgb(217 164 65 / .55), /* sombra da própria cor (luz atravessando) */
    0 3px 6px rgb(0 0 0 / .35);             /* sombra de contato */
}
```

Ao passar o mouse, ele sobe 2px; ao apertar, desce 1px. Isso é o "destaque" sem neon.

### O que não é profundidade
- Glow neon colorido em volta de tudo.
- Borda colorida grossa + sombra preta pesada.
- `backdrop-filter: blur` em toda superfície.
- A mesma sombra em todos os elementos (tudo no mesmo plano de novo).

## 3. Eixo: centralizar com intenção

- **Card**: conteúdo centralizado (título, número, texto curto, botão), card centrado no contêiner.
- **Grupo de cards**: o grupo fica centrado. Em pódio, o mais importante no meio e mais alto.
- **Botão**: centralizado no seu bloco. No celular, largura confortável (não necessariamente 100%), centrado.
- **A exceção**: texto à esquerda + card ou visual à direita. O botão que mora na coluna do texto segue o eixo do texto.
- **Texto de leitura longo** (mais de 3 linhas) dentro de um bloco centralizado: centralize o bloco e limite a medida (`max-width: 28–34ch`). Se passar de 4 linhas, o texto está grande demais para o card. Corte, não alinhe à esquerda.

## 4. Fotos: cheio, mas com critério

- Primeira tela: uma foto forte (ou um efeito), com sombra nível 3 e um leve giro (−1° a −2°) para sair do plano da página.
- Pelo menos mais duas peças visuais ao longo da página, cada uma provando algo (o lugar, o processo, o resultado).
- `width`/`height` sempre, `srcset` com as duas larguras do `pexels.mjs`, `loading="lazy"` fora da primeira tela, `fetchpriority="high"` na foto do topo.
- Pexels sem chave: `node scripts/pexels.mjs --busca "..." --orientacao portrait --larguras 640,1280`. Olhe as fotos antes de usar: o Pexels repete a mesma foto em buscas parecidas.
