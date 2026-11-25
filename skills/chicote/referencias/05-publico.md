# 5. Público: quem olha vira número

Uma obra também acontece em quem a vê. O visitante real tem olho, dedo, aparelho, rede e paciência. Cada um desses vira um número.

## Os perfis

O `medidas.mjs` usa estes valores. Os números da coluna "por quê" são o que você escreve no `medidas.md`.

| Medida | geral | idoso | jovem | b2b | tecnico | Por quê |
|---|---|---|---|---|---|---|
| Corpo (texto de leitura) | 16–17px | 19px | 16px | 16px | 15px | acuidade visual cai com a idade; 16px é o mínimo sem zoom no iOS |
| Mínimo absoluto (rótulo) | 13px | 15px | 12px | 13px | 12px | metadado ainda precisa ser lido |
| Razão da escala | 1,25 | 1,2 | 1,333 | 1,25 | 1,2 | idoso e técnico: saltos menores, nada some; jovem: mais drama |
| Entrelinha do corpo | 1,5 | 1,6 | 1,5 | 1,5 | 1,45 | WCAG 1.4.12 pede tolerar 1,5 |
| Alvo de toque | 44px | 52px | 44px | 44px | 40px* | tremor e precisão menor; *técnico em desktop |
| Contraste mínimo | 4,5:1 | 7:1 | 4,5:1 | 4,5:1 | 4,5:1 | AAA para quem enxerga menos |
| Opções por tela | ≤ 5 | ≤ 3 | ≤ 5 | ≤ 7 | ≤ 9 | Hick: mais opção, mais demora |
| Movimento | médio | mínimo | rico | discreto | discreto | movimento confunde e enjoa quem tem vestibular sensível |
| Menu escondido (hambúrguer) | aceitável | **evitar**: ações à vista | ok | ok | ok | idoso não procura ícone de 3 riscos |
| Contato visível | sempre | telefone **e** WhatsApp, grandes, fixos | WhatsApp/Instagram | formulário curto + agenda | documentação | quem tem dificuldade digital liga |

## O aparelho

| Medida | fraco | medio | forte |
|---|---|---|---|
| Exemplo | Android de entrada, 2 GB, 4G ruim | Android intermediário / iPhone antigo | iPhone recente, desktop |
| Peso da página (primeira carga) | ≤ 700 KB | ≤ 1,2 MB | ≤ 2 MB |
| JavaScript | ≤ 120 KB | ≤ 250 KB | ≤ 450 KB |
| LCP alvo (no perfil lento da chicotada) | ≤ 2,5 s | ≤ 2,5 s | ≤ 2,5 s |
| 3D / WebGL | versão estática (CSS 3D parado ou imagem), nunca WebGL | só com imagem de reserva e carregamento sob demanda | permitido com reserva |
| Vídeo de fundo | proibido | proibido no celular | só com `poster` e sem autoplay com som |
| Efeitos (blur, backdrop-filter grande, sombra animada) | evitar | com moderação | ok |

Aparelho fraco **não** é desculpa para página sem foto, sem atmosfera ou sem profundidade: gradiente e sombra custam zero bytes, foto de 640px custa ~60 KB, e efeito com movimento vira a versão estática. O mesmo site atende os três. Projete para o **fraco** e melhore progressivamente para o forte (`@media (min-width)`, `prefers-reduced-motion: no-preference`, `navigator.connection` quando houver).

## O polegar

No celular, a metade de baixo da tela é a área confortável do polegar (Fitts). Consequências:
- Página de contato: barra fixa embaixo com o CTA principal (WhatsApp/ligar), 56px de altura, sem tampar conteúdo (`padding-bottom` no body).
- Menu de navegação essencial também pode morar embaixo em sistemas (abas inferiores).
- Nada importante só no canto superior direito.

## Pessoa idosa: o checklist extra

- Texto de leitura ≥ 19px, botões com texto ≥ 18px.
- Botões com **palavra**, não só ícone. "Ligar agora (11) 99999-9999" ganha de um ícone de telefone.
- Nada de texto sobre foto sem uma camada que garanta 7:1.
- Nada de carrossel automático, pop-up, contagem regressiva ou elemento que muda sozinho.
- Formulário com rótulo visível em cima do campo (não só placeholder) e teclado certo (`type="tel"`, `inputmode="numeric"`).
- Links sublinhados no texto corrido.
- Foco visível e grosso (3px).
