# Skills externas instaladas (créditos e licenças)

Estas skills foram copiadas de repositórios públicos de terceiros e redistribuídas
sob suas licenças originais. Os autores e as licenças constam abaixo.

## Instaladas (MIT)

| Skill | Autor | Repo | Licença |
|---|---|---|---|
| `motion-design` | LottieFiles | https://github.com/LottieFiles/motion-design-skill | MIT |
| `hairline-create` | Lucas Marques | https://github.com/lucasmarkes/hairline | MIT |
| `hairline-adopt` | Lucas Marques | https://github.com/lucasmarkes/hairline | MIT |
| `anatomy` | Ryan (@wheresryan22) | https://github.com/wheresryan22/anatomy | MIT |

### motion-design
Universal motion design principles for AI agents — timing, easing, choreography,
and Disney animation principles adapted for UI. Filosofia-first,
implementation-agnostic (CSS, Framer Motion, GSAP, Lottie, Spring, etc.).
Estrutura: `SKILL.md` + `director/` + `patterns/` + `reference/`.

### hairline-create / hairline-adopt
Isometric line figures that answer the pointer, no engine Hairline.
`hairline-create` desenha uma figura nova a partir de uma ideia;
`hairline-adopt` reconstrói um SVG que você já tem como figura Hairline.
Ambas entregam um HTML autocontido sem dependências.

### anatomy
Figuras isométricas interativas que explicam ideias técnicas como objetos
físicos reais (SVG, opcional WebGL shaders e 3D, PDF A4 imprimível).
Framework-free (TS/JS) e React/Next.js. Requer Node.js 20.10+ e Chrome/Chromium
para os checks.

## Skills iart.ai (motion graphics / vídeo)

Este repo também traz `skills/iart-motion/` — 55 skills de motion graphics,
animação e vídeo (iart.ai, MIT), ver `docs/iart-motion-skills.md`.

## Não instaladas

- `motiondivision/ai-kit` — **sem licença** no repo. Não redistribuível.
- `remotion-dev/skills` — **sem licença** no repo (package.json privado). Não redistribuível.
- `www.typingmind.com/skills` — não é uma skill, é um diretório de ~98k skills
  de terceiros, cada uma com sua própria licença.

## Atualização manual

```bash
cd /tmp/opencode
git clone https://github.com/LottieFiles/motion-design-skill.git
git clone https://github.com/lucasmarkes/hairline.git
git clone https://github.com/wheresryan22/anatomy.git
# compare com skills/<id>/ e replique o que mudou
```

## Instalação global no OpenCode V2

Além deste repo, as skills ficam disponíveis globalmente em
`~/.config/opencode/skills/<id>/` (cópia idêntica). O OpenCode V2 descobre
automaticamente por esse caminho. Para carregar sem confirmação, adicione ao
`opencode.json`:

```json
{
  "permissions": [
    { "action": "skill", "resource": "motion-design", "effect": "allow" },
    { "action": "skill", "resource": "hairline-create", "effect": "allow" },
    { "action": "skill", "resource": "hairline-adopt", "effect": "allow" },
    { "action": "skill", "resource": "anatomy", "effect": "allow" }
  ]
}
```

## Instalação direta (upstream)

Com o CLI `skills` (vercel-labs/skills) ou `npx skills add <user>/<repo>`:

```bash
npx skills add LottieFiles/motion-design-skill
npx skills add lucasmarkes/hairline
npx skills add wheresryan22/anatomy
```
