# iart.ai Motion Skills — 55 skills de motion graphics / vídeo (MIT)

Origem: hub **[iart-ai/motion-skills](https://github.com/iart-ai/motion-skills)** (MIT, 1704★),
que indexa 19 packs de skills para agentes fazerem motion graphics, animação e vídeo.
Os 19 packs vivem em repositórios próprios `iart-ai/*-skills`; 18 deles são MIT.
O pack `generative-illustration-skills` **não tem licença** e foi excluído.

## O que está instalado

55 skills, achatadas em `skills/iart-motion/<skill-id>/` (cada uma com `SKILL.md`,
`references/` e, quando o pack oferece, `scripts/` embutido). O `LICENSE` (MIT,
Copyright (c) 2026 iart.ai) está em `skills/iart-motion/LICENSE`.

Duas skills se chamavam `lower-thirds` em packs diferentes: a do pack
`lower-thirds-skills` ficou como `lower-thirds` e a do pack `tiktok-video-skills`
foi renomeada para `lower-thirds-tiktok` (frontmatter `name:` também ajustado).

### Lista por pack (18 packs)

| Pack | Skills |
|---|---|
| ad-video-skills | ad-creative-video, launch-video, testimonial-video |
| b-roll-skills | talking-head-b-roll |
| data-animation-skills | animated-infographic, chart-animation, presentation-video |
| ecommerce-video-skills | photo-slideshow, product-demo-video, promo-video |
| explainer-video-skills | diagram-animation, explainer-video, isometric-animation, whiteboard-animation, wrapped-video |
| freelance-motion-skills | brand-motion-guidelines, client-revisions, creative-brief, motion-pricing, video-delivery-specs |
| javascript-animation-skills | javascript-animation, soundtrack |
| kinetic-typography-skills | kinetic-typography |
| lower-thirds-skills | lower-thirds |
| manim-skills | manim |
| map-animation-skills | map-animation |
| motion-design-skills | after-effects, animation-principles, beat-sync-editing, color-motion, logo-animation, motion-art-direction, motion-background, remotion-video, shot-composition |
| talking-head-skills | talking-head |
| text-message-video-skills | text-message-animation |
| tiktok-video-skills | caption-animation, countdown-video, lower-thirds-tiktok, short-form-video |
| web-animation-skills | 60fps-animation, accessible-animation, ascii-animation, glassmorphism, gsap-web, lottie-animation, micro-interaction, page-transition-animation, svg-animation |
| webgl-animation-skills | particle-system, shader-glsl, threejs-animation |
| youtube-video-skills | audiogram, youtube-intro-outro |

## Instalação global (OpenCode V2)

Cópias idênticas em `~/.config/opencode/skills/iart-motion/<skill-id>/`.
O OpenCode V2 descobre por `SKILL.md`; as skills são registradas por esse caminho.
O custo: 55 descrições longas entram no índice de skills do modelo. Se o contexto
ficar pesado, remova a pasta global ou sete `metadata.opencode/autoinvoke: false`
nos frontmatters que não quer invocação automática.

## Notas de uso

- As skills mencionam `scripts/contact-sheet.sh`, `scripts/probe-mp4.sh` e
  `scripts/seek-shot.sh` como "Packaged helper" — cada skill que precisa deles já
  traz sua cópia em `scripts/` (autocontida).
- Alguns packs pedem Remotion, Manim, After Effects, Chrome/Chromium ou ElevenLabs;
  instale o que for usar conforme o `SKILL.md` de cada skill.
- `talking-head` usa voz ElevenLabs: só com chave/conta própria e autorizada.
- O hub também oferece MCP server remoto pago (iArt) e `claude-plugin` marketplace —
  nada disso foi instalado; só as skills MIT.

## Atualização manual

```bash
cd /tmp/opencode && rm -rf iart-motion && mkdir iart-motion && cd iart-motion
PACKS="ad-video-skills b-roll-skills data-animation-skills ecommerce-video-skills \
explainer-video-skills freelance-motion-skills javascript-animation-skills \
kinetic-typography-skills lower-thirds-skills manim-skills map-animation-skills \
motion-design-skills talking-head-skills text-message-video-skills tiktok-video-skills \
web-animation-skills webgl-animation-skills youtube-video-skills"
for p in $PACKS; do git clone -q https://github.com/iart-ai/$p; done
# depois copie */skills/* para skills/iart-motion/<skill-id>/
# e */scripts para dentro de cada skill que mencionar "Packaged helper"
```

## Licença

MIT (iart.ai). O LICENSE completo está em `skills/iart-motion/LICENSE`.
Creditar iart.ai ao publicar trabalho feito com estas skills, como pede o README
do hub.
