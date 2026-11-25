# 8. Movimento: só com função

Movimento bom passa despercebido e deixa a página mais clara. Movimento ruim atrasa o conteúdo, rouba o foco e pesa no celular fraco.

## Para que serve (e só para isso)

| Função | Exemplo | Duração |
|---|---|---|
| Orientar | seção entrando de leve quando chega na tela | 300–500ms, uma vez |
| Confirmar | botão pressionado afunda; "Copiado ✓" | 100–200ms |
| Causa e efeito | card movido para a coluna "Fechado" | 200–350ms |
| Guiar até a ação | o CTA ganha um brilho único depois que o visitante lê a oferta | 1 vez, ≤ 800ms |
| Mostrar o produto | vídeo curto da tela real funcionando | em loop só se for curto, sem som, com pausa |

Se não cabe em nenhuma linha, corte.

## Regras de ouro

- **Nunca atrase o conteúdo.** O texto do hero aparece no primeiro quadro. Animação de entrada no hero, se houver, é só `opacity`/`transform` e começa visível o bastante para ser lida (não de 0).
- **Só `transform` e `opacity`** em animação contínua. `width`, `top`, `box-shadow` e `filter` grandes animados derrubam quadros no celular fraco.
- **Curvas**: entrada com `cubic-bezier(.2,.8,.2,1)` (sai rápido, chega suave); saída mais curta que a entrada.
- **`prefers-reduced-motion: reduce`** desliga entradas, parallax, vídeo automático e loop. Portão medido pela chicotada.
- **Nada que roda para sempre** (pulsar, girar, marquee) sem o visitante pedir.
- **Hover só em quem tem mouse**: `@media (hover: hover) and (pointer: fine)`.

## Por perfil

| Perfil | Movimento |
|---|---|
| idoso | mínimo: só confirmação e orientação curtas; nada de parallax ou carrossel |
| geral | orientação nas seções, confirmação nos botões |
| jovem | pode ter coreografia no hero e transições entre estados, sempre com reduce |
| aparelho fraco | sem parallax, sem blur animado, sem vídeo de fundo |

## Escada e linha do tempo animadas

Para passo a passo em escada: cada degrau entra com 80–120ms de diferença (stagger), na ordem da leitura, **uma vez**. A soma do stagger não passa de 500ms.
