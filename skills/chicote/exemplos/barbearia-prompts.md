# Prompts de imagem: Navalha de Ouro (exemplo)

Estilo do ensaio: fotografia editorial de interior, luz quente de luminária de latão, couro e madeira escura.
Tratamento de cor (já no CSS `.foto`): saturação 0,82 · contraste 1,06 · sépia 0,14 · véu âmbar em soft-light a 38%.
Hoje a página usa fotos do Pexels como reserva (créditos em `barbearia-img/CREDITOS.md`). Estas são as imagens próprias que as substituem.

## Vaga 1: hero, peça central (foto entre os dois cards)
- **Onde:** palco do hero, card central 4:3,4, sombra nível 3; etiqueta "Lâmina nova a cada cliente" por cima, embaixo e no centro
- **Prompt:** editorial close-up photograph of a barber's hand holding a straight razor against a client's lathered beard, the client reclining with eyes closed, warm brass lamp light from the upper left, deep oxblood leather and walnut wood in the soft background, 50mm lens, shallow depth of field, calm and precise mood, empty lower center area for a small caption, subtle film grain, no text, no logos
- **Proporção:** 4:5 (ChatGPT/Gemini: "portrait 4:5"; Midjourney: --ar 4:5)
- **Reserva na página:** `barber-shaving-beard-straight-razor-01` (Pexels) com `.foto`

## Vaga 2: ritual, primeiro tempo (bloco grande do bento)
- **Onde:** bloco 1 do bento, 1,4/2,4 da largura, duas linhas de altura; texto centralizado na parte de baixo sobre véu escuro
- **Prompt:** editorial photograph of a barber gently placing a steaming hot white towel over a client's face in a classic barbershop, visible soft steam, warm practical lights, dark walnut background, 35mm lens, eye level, the lower third darker and empty for text, film grain, no text, no logos
- **Proporção:** 3:4
- **Reserva na página:** `barber-hot-towel-shave-01`

## Vaga 3: cena final (fundo do painel "Sua cadeira, no seu horário")
- **Onde:** painel inteiro, foto atrás de um véu radial escuro; título, horário e botões centralizados por cima
- **Prompt:** wide editorial interior photograph of an empty vintage barber chair in dark oxblood leather, centered, in a quiet classic barbershop at dusk, two warm brass wall lamps, a single soft window light from the left, deep walnut and cream marble tones, large dark empty area around the chair for a centered headline, 35mm lens, eye level, calm premium atmosphere, subtle film grain, no text, no logos, no people
- **Proporção:** 16:9 no desktop e 4:5 no celular (pedir as duas)
- **Reserva na página:** `vintage-barber-chair-leather-01`

## Vaga 4 (opcional): hero em camadas, se quiser a cena passando na frente
- **Fundo:** cinematic photograph of a classic barbershop interior at night seen from a low angle, warm brass lamps glowing, blurred bottles on wooden shelves, large empty dark center for a floating product card, 24mm lens, film grain, no text, no people, --ar 16:9
- **Frente (recorte):** isolated foreground layer only: the top edge of a dark oxblood leather barber chair back and a folded white towel along the bottom edge of the frame, transparent background (PNG), nothing else in the image, --ar 16:9
- **No código:** fundo → cards do palco → frente com `position: absolute; bottom: 0; pointer-events: none`, cobrindo 15% da base dos cards
