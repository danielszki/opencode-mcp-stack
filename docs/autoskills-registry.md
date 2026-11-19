# autoskills registry (vendored)

Cópia local do **registry de skills do [autoskills](https://autoskills.sh)** —
[`midudev/autoskills`](https://github.com/midudev/autoskills), commit `46f50bab`
(2026-11-15), diretório `packages/autoskills/skills-registry/`.

- **O que foi copiado:** as **203 skills** referenciadas pelo `skills-map.ts`
  do upstream (204 ids menos `python-patterns`, que já existia neste repo e é
  byte-idêntico), incluindo `index.json` (manifesto com SHA-256 por arquivo e
  o parecer de revisão de cada skill). 4.387 arquivos, ~30 MB.
- **Não copiado:** `accessibility`, `frontend-design` e `seo` — estão no
  diretório do upstream mas **não são referenciadas pelo `skills-map.ts`**
  (nenhum stack as instala). Para incluí-las, copie à mão.
- **Licença do autoskills:** CC BY-NC 4.0 (**NonCommercial**, `LICENSE` do
  upstream, Copyright (c) 2025 midudev) — ver `skills/autoskills/LICENSE`.
- **Licença de cada skill:** as skills são de **75 projetos upstream distintos**
  e mantêm a licença de origem. O registro só empacota um `LICENSE`/`NOTICE`
  próprio em **3 casos** (`anthropics/skills`, `openai/skills` e
  `midudev/autoskills`); as outras 72 origens não trazem arquivo de licença no
  bundle. Antes de redistribuir qualquer uma delas fora deste repositório,
  confirme a licença no projeto de origem (coluna *Origem* abaixo).

## Como o upstream organiza

`skills-map.ts` mapeia **118 tecnologias** (detectadas por `package.json`,
arquivos de config, extensões e gems) para listas de skills, incluindo 30
combos (`nextjs-clerk`, `rails-rspec`, `react-shadcn`, ...). O CLI
`npx autoskills` baixa só as skills do stack do projeto, confere cada arquivo
contra o SHA-256 do `index.json` e grava `skills-lock.json`.

Como este repo é um stack portátil, mantemos o registry completo: qualquer
projeto pode receber o subconjunto certo sem depender da rede.

## Cobertura por tecnologia

.NET (3), ASP.NET Core (2), ASP.NET Minimal API (1), Android (8), Android+Clerk (3),
Angular (6), Astro (1), Astro+Clerk (1), Azure (3), Bash (1), Better Auth (4),
Blazor (1), Bun (1), C# (6), Celery (1), Chrome Extension (1), Chrome Extension+Clerk (3),
Clerk (7), Cloudflare (5), Cloudflare+Vite (1), Cloudflare AI (1), Cloudflare Agents (2),
Dart (1), Django (3), Drizzle ORM (1), Durable Objects (1), ElevenLabs (2), Elysia (1),
Expo (8), Expo+Clerk (1), FastAPI (3), FastMCP (1), Flask (1), Flutter (3), GSAP (7),
GSAP+React (1), Go (2), Hono (1), InstantDB (1), Java (2), Kotlin Multiplatform (2),
Laravel (2), Neon Postgres (1), NestJS (1), Next.js (1), Next.js+Clerk (1),
Next.js+Playwright (1), Next.js+Supabase (1), Next.js+Vercel AI SDK (1), Node.js (2),
Node.js+Express (1), NumPy (2), Nuxt (1), Nuxt+Clerk (1), PHP (1), Pandas (2), Pinia (1),
Playwright (1), Prisma (4), Pydantic (1), Pytest (1), Python (2), RSpec (2), React (2),
React+Clerk (1), React+React Three Fiber (1), React+shadcn/ui (2), React Hook Form (1),
React Hook Form+Zod (1), React Native (1), React Native+Expo (2), React Router+Clerk (3),
Redis Ruby (1), Remotion (1), Ruby (1), Ruby on Rails (6), Ruby on Rails+RSpec (2),
Rust (1), SQLAlchemy (2), Scikit-Learn (2), Sidekiq (1), Sorbet (2), Spring Boot (1),
Stripe (2), Supabase (1), Svelte (2), SwiftUI (5), SwiftUI+Clerk (3), Tailwind CSS (1),
Tailwind CSS+shadcn/ui (1), TanStack Start (1), TanStack Start+Clerk (3), Tauri (1),
Terraform (4), Three.js (10), Turborepo (1), TypeScript (1), Vercel (1), Vercel AI SDK (1),
Vite (1), Vitest (1), Vue (3), Vue+Clerk (1), WordPress (8), Zod (1), oxlint (1), shadcn/ui (1).

## Revisão de segurança do upstream

Cada skill no `index.json` traz `review.status` (`approved`/`flagged`), os
`flags` e um resumo. Nesta cópia: **196 approved, 7 flagged**. Todos os 7 são
`flagged` por padrões documentados pela própria documentação vendor (não por
injeção de prompt ou exfiltração):

| Skill | Motivo do flag |
|---|---|
| `clerk-chrome-extension-patterns` | exemplo headless envia URL de abas visitadas + token de sessão para a API; usa `<all_urls>`; sugere desligar bot protection |
| `eas-hosting` | CORS com `*`, `city` não escapado em URL, comando opcional `npx --yes submit-expo-feedback@latest` |
| `expo-dom`, `expo-dev-client`, `expo-upgrade` | mesmo comando opcional de feedback para a Expo |
| `remotion-best-practices` | `npx --yes create-video@latest`, Studio local, chaves de mapas em código de browser, chave pública do Algolia |
| `kotlin-tooling-cocoapods-spm-migration` | (ver `index.json` para o parecer completo) |

Nenhum script foi executado por esta importação: é só cópia de arquivos.

## Origem por skill

- **`clerk/skills`** (18): `clerk`, `clerk-android`, `clerk-astro-patterns`, `clerk-backend-api`, `clerk-chrome-extension-patterns`, `clerk-custom-ui`, `clerk-expo`, `clerk-nextjs-patterns`, `clerk-nuxt-patterns`, `clerk-orgs`, `clerk-react-patterns`, `clerk-react-router-patterns`, `clerk-setup`, `clerk-swift`, `clerk-tanstack-patterns`, `clerk-testing`, `clerk-vue-patterns`, `clerk-webhooks`
- **`github/awesome-copilot`** (14): `aspnet-minimal-api-openapi`, `containerize-aspnetcore`, `csharp-async`, `csharp-docs`, `csharp-mstest`, `csharp-nunit`, `csharp-tunit`, `csharp-xunit`, `dotnet-best-practices`, `dotnet-design-pattern-review`, `dotnet-upgrade`, `fluentui-blazor`, `java-docs`, `java-springboot`
- **`cloudai-x/threejs-skills`** (10): `threejs-animation`, `threejs-fundamentals`, `threejs-geometry`, `threejs-interaction`, `threejs-lighting`, `threejs-loaders`, `threejs-materials`, `threejs-postprocessing`, `threejs-shaders`, `threejs-textures`
- **`expo/skills`** (8): `eas-app-stores`, `eas-hosting`, `eas-workflows`, `expo-data-fetching`, `expo-dev-client`, `expo-dom`, `expo-native-ui`, `expo-upgrade`
- **`greensock/gsap-skills`** (8): `gsap-core`, `gsap-frameworks`, `gsap-performance`, `gsap-plugins`, `gsap-react`, `gsap-scrolltrigger`, `gsap-timeline`, `gsap-utils`
- **`krutikJain/android-agent-skills`** (8): `android-architecture-clean`, `android-compose-foundations`, `android-coroutines-flow`, `android-di-hilt`, `android-gradle-build-logic`, `android-kotlin-core`, `android-networking-retrofit-okhttp`, `android-testing-unit`
- **`wordpress/agent-skills`** (8): `wordpress-router`, `wp-block-development`, `wp-block-themes`, `wp-performance`, `wp-plugin-development`, `wp-project-triage`, `wp-rest-api`, `wp-wpcli-and-ops`
- **`cloudflare/skills`** (7): `agents-sdk`, `cloudflare`, `durable-objects`, `sandbox-stable`, `web-perf`, `workers-best-practices`, `wrangler`
- **`wshobson/agents`** (7): `bash-defensive-patterns`, `fastapi-templates`, `nodejs-backend-patterns`, `python-background-jobs`, `python-testing-patterns`, `terraform-module-library`, `typescript-advanced-types`
- **`affaan-m/everything-claude-code`** (6): `django-patterns`, `django-security`, `golang-patterns`, `golang-testing`, `java-coding-standards`, `laravel-patterns`
- **`igmarin/rails-agent-skills`** (6): `apply-stack-conventions`, `implement-background-job`, `plan-tests`, `review-migration`, `security-check`, `test-service`
- **`angular/angular`** (5): `adev-writing-guide`, `pr_review`, `reference-compiler-cli`, `reference-core`, `reference-signal-forms`
- **`antfu/skills`** (4): `nuxt`, `vite`, `vitest`, `vue`
- **`better-auth/skills`** (4): `best-practices`, `email-and-password-best-practices`, `organization-best-practices`, `two-factor-authentication-best-practices`
- **`jeffallan/claude-skills`** (4): `flutter-expert`, `laravel-specialist`, `pandas-pro`, `php-pro`
- **`prisma/skills`** (4): `prisma-cli`, `prisma-client-api`, `prisma-database-setup`, `prisma-postgres`
- **`bobmatnyc/claude-mpm-skills`** (3): `drizzle`, `pydantic`, `sqlalchemy`
- **`hashicorp/agent-skills`** (3): `refactor-module`, `terraform-stacks`, `terraform-style-guide`
- **`inferen-sh/skills`** (3): `elevenlabs-music`, `elevenlabs-tts`, `python-executor`
- **`lucianghinda/superpowers-ruby`** (3): `rails-guides`, `ruby`, `test-driven-development`
- **`microsoft/github-copilot-for-azure`** (3): `azure-ai`, `azure-deploy`, `azure-diagnostics`
- **`vercel-labs/agent-skills`** (3): `composition-patterns`, `deploy-to-vercel`, `react-best-practices`
- **`DmitryPogrebnoy/ruby-agent-skills`** (2): `generating-sorbet`, `generating-sorbet-inline`
- **`Kotlin/kotlin-agent-skills`** (2): `kotlin-tooling-agp9-migration`, `kotlin-tooling-cocoapods-spm-migration`
- **`aj-geddes/useful-ai-prompts`** (2): `flask-api-development`, `nodejs-express-server`
- **`davila7/claude-code-templates`** (2): `scikit-learn`, `senior-data-scientist`
- **`madteacher/mad-agents-skills`** (2): `flutter-animations`, `flutter-testing`
- **`mindrally/skills`** (2): `chrome-extension-development`, `fastapi-python`
- **`openai/skills`** (2): `aspnet-core`, `cloudflare-deploy`
- **`pluginagentmarketplace/custom-plugin-python`** (2): `machine-learning`, `pandas-data-analysis`
- **`pproenca/dot-skills`** (2): `react-hook-form`, `zod`
- **`stripe/ai`** (2): `stripe-best-practices`, `upgrade-stripe`
- **`vuejs-ai/skills`** (2): `vue-best-practices`, `vue-pinia-best-practices`
- **`angular/skills`** (1): `angular-developer`
- **`apollographql/skills`** (1): `rust-best-practices`
- **`astrolicious/agent-skills`** (1): `astro`
- **`avdlee/core-data-agent-skill`** (1): `core-data-expert`
- **`avdlee/swift-concurrency-agent-skill`** (1): `swift-concurrency`
- **`avdlee/swift-testing-agent-skill`** (1): `swift-testing-expert`
- **`avdlee/swiftui-agent-skill`** (1): `swiftui-expert-skill`
- **`avdlee/xcode-build-optimization-agent-skill`** (1): `xcode-build-orchestrator`
- **`cloudflare/vinext`** (1): `migrate-to-vinext`
- **`currents-dev/playwright-best-practices-skill`** (1): `playwright-best-practices`
- **`delexw/claude-code-misc`** (1): `oxlint`
- **`ejirocodes/agent-skills`** (1): `svelte5-best-practices`
- **`elysiajs/skills`** (1): `elysia`
- **`fastapi/fastapi`** (1): `fastapi`
- **`giuseppe-trisciuoglio/developer-kit`** (1): `tailwind-css-patterns`
- **`honojs/skills`** (1): `hono`
- **`hyf0/vue-skills`** (1): `vue-debug-guides`
- **`igmarin/ruby-core-skills`** (1): `triage-bug`
- **`instantdb/skills`** (1): `instantdb`
- **`kadajett/agent-nestjs-skills`** (1): `nestjs-best-practices`
- **`kevmoo/dash_skills`** (1): `dart-best-practices`
- **`midudev/autoskills`** (1): `bun`
- **`neondatabase/agent-skills`** (1): `neon-postgres`
- **`nodnarbnitram/claude-code-extensions`** (1): `tauri-v2`
- **`ombulabs/claude-code_rails-upgrade-skill`** (1): `rails-upgrade`
- **`redis/agent-skills`** (1): `redis-core`
- **`remotion-dev/skills`** (1): `remotion-best-practices`
- **`secondsky/claude-skills`** (1): `tailwind-v4-shadcn`
- **`sergiodxa/agent-skills`** (1): `ruby-on-rails-best-practices`
- **`shadcn/ui`** (1): `shadcn`
- **`sharanharsoor/skills`** (1): `fastmcp`
- **`sickn33/antigravity-awesome-skills`** (1): `nodejs-best-practices`
- **`sleekdotdesign/agent-skills`** (1): `design-mobile-apps`
- **`supabase/agent-skills`** (1): `supabase-postgres-best-practices`
- **`sveltejs/ai-tools`** (1): `svelte-code-writer`
- **`tanstack-skills/tanstack-skills`** (1): `tanstack-start`
- **`vercel-labs/json-render`** (1): `react-three-fiber`
- **`vercel/ai`** (1): `use-ai-sdk`
- **`vercel/next.js`** (1): `next-cache-components-adoption`
- **`vercel/turborepo`** (1): `turborepo`
- **`vintasoftware/django-ai-plugins`** (1): `django-expert`
- **`wispbit-ai/skills`** (1): `sqlalchemy-alembic-expert-best-practices-code-review`

## Instalação direta (upstream)

```bash
npx autoskills            # detecta o stack e instala o subconjunto
npx autoskills --dry-run  # só mostra o que instalaria
```
