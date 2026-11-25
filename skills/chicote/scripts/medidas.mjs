#!/usr/bin/env node
/**
 * medidas.mjs: transforma o público e o aparelho em números, com o porquê de cada um.
 *
 *   node scripts/medidas.mjs --publico idoso --aparelho fraco --titulo "Barba feita em 30 min, sem fila" --saida chicote/medidas
 *
 * Gera tokens.css (variáveis CSS) e medidas.md (a justificativa). Sem dependências.
 */
import fs from "node:fs";
import path from "node:path";

import { APARELHOS, PERFIS } from "./perfis.mjs";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => (a.startsWith("--") ? [...acc, [a.slice(2), arr[i + 1]?.startsWith("--") || arr[i + 1] === undefined ? "1" : arr[i + 1]]] : acc), []),
);
if (args.ajuda || args.help) {
  console.log("uso: node scripts/medidas.mjs --publico geral|idoso|jovem|b2b|tecnico --aparelho fraco|medio|forte [--titulo \"frase do hero\"] [--razao 1.25] [--base 16] [--letra 0.52 (0.6 para serifada negrito)] [--saida pasta]");
  process.exit(0);
}

const publico = args.publico ?? "geral";
const aparelho = args.aparelho ?? "medio";
const P = PERFIS[publico];
const A = APARELHOS[aparelho];
if (!P || !A) {
  console.error(`perfil desconhecido: --publico ${publico} --aparelho ${aparelho}`);
  process.exit(1);
}
const base = Number(args.base ?? P.corpo);
const razao = Number(args.razao ?? P.razao);
const r = (n) => Math.round(n);

// escala: t(n) = base × razão^n
const degraus = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7].map((n) => ({ n, px: r(base * razao ** n) }));
const tam = (n) => degraus.find((d) => d.n === n).px;
const entrelinha = (px) => Math.max(1.05, +(1.1 + 0.4 * (base / px) + (publico === "idoso" && px <= base * 1.3 ? 0.1 : 0)).toFixed(2));

// título que cabe: tamanho ≤ (W × N) ÷ (L × 0,52)
const titulo = args.titulo ?? "";
const L = titulo.length;
const W360 = 360 - 2 * 16;
// largura média do caractere em em: grotesca ≈ 0,52; serifada ou negrito largo ≈ 0,58–0,62 (meça no print)
const letra = Number(args.letra ?? 0.52);
// a linha quebra em palavras inteiras e desperdiça ~15% da largura: fator de quebra 1,15
const QUEBRA = 1.15;
const fitTitulo = (W, N) => (L ? Math.floor((W * N) / (L * letra * QUEBRA)) : null);
const tituloCel = L ? Math.min(fitTitulo(W360, 3), tam(5)) : tam(4);
const tituloDesk = L ? Math.min(fitTitulo(Math.min(1440 * (7 / 12), 760), 2), tam(7)) : tam(6);
const palavras = titulo.trim() ? titulo.trim().split(/\s+/).length : 0;

const espacos = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16].map((k) => k * 8);
const medida = publico === "idoso" ? 60 : 66;

const css = `/* chicote · medidas para público "${publico}" em aparelho "${aparelho}" (gerado por scripts/medidas.mjs) */
:root {
  /* escala tipográfica: base ${base}px × ${razao}^n */
${degraus.map((d) => `  --t${d.n < 0 ? "m" + -d.n : d.n}: ${d.px}px; /* ${d.n} */`).join("\n")}
  --t-corpo: ${base}px;
  --t-minimo: ${P.minimo}px;
  --t-titulo-cel: ${tituloCel}px;
  --t-titulo-desk: ${tituloDesk}px;
  --t-titulo: clamp(${tituloCel}px, ${(((tituloDesk - tituloCel) / (1440 - 360)) * 100).toFixed(3)}vw + ${(tituloCel - ((tituloDesk - tituloCel) / (1440 - 360)) * 360).toFixed(1)}px, ${tituloDesk}px);

  /* entrelinha ≈ 1,1 + 0,4 × (corpo ÷ tamanho) */
  --lh-corpo: ${entrelinha(base)};
  --lh-titulo: ${entrelinha(tituloDesk)};
  --lh-sub: ${entrelinha(tam(2))};

  /* medida da linha */
  --medida: ${medida}ch;

  /* espaço: base 8px */
${espacos.map((v, i) => `  --e${[1, 2, 3, 4, 5, 6, 8, 10, 12, 16][i]}: ${v}px;`).join("\n")}
  --e-meio: 4px;
  --secao: clamp(${espacos[6]}px, 8vw, ${espacos[9]}px);

  /* grade */
  --colunas: 12;
  --goteira: clamp(16px, 2vw, 24px);
  --margem: clamp(16px, 5vw, 40px);
  --conteudo: 1200px;

  /* toque e acessibilidade */
  --alvo: ${P.alvo}px;
  --alvo-cta: ${Math.max(P.alvo, publico === "idoso" ? 56 : 48)}px;
  --foco: ${publico === "idoso" ? 3 : 2}px solid currentColor;

  /* movimento */
  --curva-entrada: cubic-bezier(.2, .8, .2, 1);
  --dur-curta: ${publico === "idoso" ? 120 : 160}ms;
  --dur-media: ${publico === "idoso" ? 200 : 320}ms;
}
@media (prefers-reduced-motion: reduce) {
  :root { --dur-curta: 0ms; --dur-media: 0ms; }
}
`;

const md = `# Medidas · público \`${publico}\` · aparelho \`${aparelho}\`

Gerado por \`scripts/medidas.mjs\`. Use os tokens de \`tokens.css\`; número fora deles precisa de porquê escrito.

## Por que este perfil
- Público: ${P.porque}.
- Aparelho: ${A.porque}.

## Tipografia
| Token | Valor | Porquê |
|---|---|---|
| corpo | ${base}px | mínimo de leitura do perfil \`${publico}\` |
| mínimo absoluto | ${P.minimo}px | rótulos e metadados; nada abaixo disso |
| razão | ${razao} | t(n) = ${base} × ${razao}^n |
| escala | ${degraus.map((d) => d.px).join(" · ")} | degraus −2 a 7 |
| entrelinha do corpo | ${entrelinha(base)} | 1,1 + 0,4 × (corpo ÷ tamanho)${publico === "idoso" ? " + 0,1 (idoso)" : ""} |
| entrelinha do título | ${entrelinha(tituloDesk)} | letra grande pede entrelinha relativa menor |
| medida | ${medida}ch | conforto de leitura entre 45 e 75 caracteres |
${titulo ? `
## Frase do hero
"${titulo}": ${L} caracteres, ${palavras} palavras${palavras > 12 ? " (**acima de 12 palavras: encurte**)" : ""}.

| Onde | Cálculo | Tamanho |
|---|---|---|
| celular 360px, até 3 linhas | (${W360} × 3) ÷ (${L} × ${letra} × 1,15) = ${fitTitulo(W360, 3)}px, limitado ao degrau 5 (${tam(5)}px) | **${tituloCel}px** |
| desktop, coluna de 7/12, até 2 linhas | (${Math.min(1440 * (7 / 12), 760)} × 2) ÷ (${L} × ${letra} × 1,15) = ${fitTitulo(Math.min(1440 * (7 / 12), 760), 2)}px, limitado ao degrau 7 (${tam(7)}px) | **${tituloDesk}px** |
${tituloCel < base * 1.6 ? `\n**Atenção:** a frase é longa demais para ter peso de título a 360px (${tituloCel}px < ${r(base * 1.6)}px). Encurte a frase antes de diminuir a letra.\n` : ""}` : ""}
## Espaço e grade
| Token | Valor | Porquê |
|---|---|---|
| base | 8px | todo espaçamento é múltiplo de 8 (cânone: tudo deriva de uma unidade) |
| degraus | ${espacos.join(" · ")} | 4px só dentro de componente pequeno |
| entre seções | 64 a 128px | 2 a 3× o espaço interno: capítulos lidos como faixas |
| grade | 12 colunas, goteira 16–24px | 12 divide em 2, 3, 4 e 6; arranjos com tensão: 7/5, 8/4 |

## Toque, contraste e escolhas
| Medida | Valor | Porquê |
|---|---|---|
| alvo de toque | ${P.alvo}px | Fitts: alvo maior = acerto mais rápido; folga de 8px entre alvos |
| altura do CTA | ${Math.max(P.alvo, publico === "idoso" ? 56 : 48)}px | o maior alvo da tela é a ação principal |
| contraste mínimo | ${P.contraste}:1 | ${P.contraste === 7 ? "WCAG AAA" : "WCAG AA"} para texto de leitura |
| opções por tela | ≤ ${P.opcoes} | Hick: T = b × log₂(n + 1) |
| movimento | ${P.movimento} | ver \`08-movimento.md\` |

## Orçamento do aparelho \`${aparelho}\`
| Medida | Limite |
|---|---|
| peso da primeira carga | ${A.pesoKB} KB |
| JavaScript | ${A.jsKB} KB |
| 3D | ${A.tresD} |
| vídeo de fundo | ${A.video} |
| LCP | ≤ 2,5 s no perfil lento da chicotada |
`;

const saida = args.saida;
if (saida) {
  fs.mkdirSync(saida, { recursive: true });
  fs.writeFileSync(path.join(saida, "tokens.css"), css);
  fs.writeFileSync(path.join(saida, "medidas.md"), md);
  fs.writeFileSync(path.join(saida, "medidas.json"), JSON.stringify({ publico, aparelho, base, razao, minimo: P.minimo, alvo: P.alvo, contraste: P.contraste, pesoKB: A.pesoKB, jsKB: A.jsKB, tituloCel, tituloDesk }, null, 2));
  console.log(`ok: ${path.join(saida, "tokens.css")} e medidas.md`);
} else {
  console.log(md);
  console.log("\n```css\n" + css + "```");
}
