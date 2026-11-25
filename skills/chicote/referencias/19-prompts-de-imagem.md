# 19. Prompt de imagem: sem imagem, entregue o prompt

A página de nível de referência quase sempre depende de uma imagem que **não existe no banco**: o produto emergindo da grama, a estátua segurando o cartão, a cadeira de barbeiro numa sala de mármore ao pôr do sol. A resposta nunca é "não tenho a imagem". A resposta é **o prompt pronto**, que a pessoa cola no ChatGPT, no Gemini ou no Midjourney e devolve.

## A ordem

Toda vaga de imagem da página recebe, nesta ordem:
1. **O lugar dela** na composição (qual painel, qual camada, proporção, o que fica por cima).
2. **O prompt**, em inglês (os geradores respondem melhor), no formato abaixo.
3. **A reserva** que já vai na página enquanto a imagem não chega: foto do Pexels tratada com o mesmo filtro, ou cena em CSS (gradiente de céu, padrão, forma da metáfora). A página nunca fica com buraco.

Grave tudo em `chicote/prompts.md` (modelo em `modelos/prompts.md`) e cite na entrega.

## Imagem em camadas (o efeito "a interface mora no mundo")

Para o hero de produto na paisagem, peça **duas imagens** do mesmo cenário:

| Camada | O que é | Como pedir |
|---|---|---|
| Fundo | a cena inteira, com espaço vazio no centro onde a peça vai | "...wide empty area in the lower center for a product to be placed..." |
| Frente | só o elemento que passa na frente (grama, nuvem, folhagem, mão), recortado | "...isolated foreground layer only, [grass tips] along the bottom edge, transparent background (PNG), no sky, no subject..." |

No código: fundo → peça (card, tela, objeto) → frente (`position: absolute; bottom: 0; pointer-events: none`). A frente cobre 10–25% da parte de baixo da peça.

## O formato do prompt

```
VAGA: hero, painel escuro, fundo (camada 1 de 2), 16:9 no desktop e 4:5 no celular
PROMPT:
[estilo], [assunto concreto], [ação ou estado], [lugar], [hora e luz: direção, cor, dureza],
[lente e enquadramento], [paleta: cores da página em palavras], [atmosfera],
[espaço livre: onde fica vazio e por quê], [tratamento: grão, contraste],
no text, no logos, no watermark, no people facing camera [se for nicho regulado ou banco]
PROPORÇÃO: --ar 16:9  (Midjourney) / "landscape 16:9" (ChatGPT, Gemini)
RESERVA NA PÁGINA: pexels "[busca]" com .foto-tratada, ou gradiente [cores]
```

## Estilos que funcionam no nível de referência

| Estilo | Palavras-chave | Bom para |
|---|---|---|
| Fotografia cinematográfica de paisagem | "cinematic landscape photography, golden hour, layered mountains, soft haze, 35mm" | SaaS, serviços, hero com produto |
| Escultura clássica | "classical white marble sculpture, museum lighting, soft shadows, plain light grey background" | finanças, jurídico, educação, autoridade |
| Colagem vintage | "1970s vintage photograph collage, cut-out paper edge, warm faded colors, film grain" | carreira, turismo, cultura, marca autoral |
| Objeto na mão | "close-up of a hand holding [object], studio light, soft warm beige background, product photography" | produto físico, app, cartão |
| Natureza estilizada | "stylized lush grass field with pink flowers, hyperreal 3D render, bright blue sky" | marcas jovens, tecnologia |
| Interior com luz | "interior photography, [lugar], warm practical lights, shallow depth of field, editorial" | negócio local, restaurante, clínica |

## Exemplo completo (barbearia)

```
VAGA: hero, painel escuro, fundo (camada 1 de 2), 16:9
PROMPT:
editorial interior photography of an empty vintage barber chair in dark oxblood leather,
in a quiet classic barbershop at dusk, warm brass wall lamps and a single soft window light from the left,
35mm lens, eye level, centered composition, deep walnut wood and cream marble tones,
calm and premium atmosphere, large empty dark area above the chair for a headline,
subtle film grain, no text, no logos, no people
PROPORÇÃO: --ar 16:9
RESERVA NA PÁGINA: pexels "vintage barber chair leather" com .foto-tratada (sépia .15, soft-light âmbar)
```

## Nunca

- Entregar a página com vaga vazia ou com cinza "imagem aqui".
- Pedir imagem com texto escrito dentro (os geradores erram letras; texto é HTML).
- Usar imagem gerada de pessoa como se fosse o profissional ou cliente real.
- Misturar estilos (uma foto cinematográfica + uma colagem + um 3D na mesma página). Um ensaio, um tratamento.
