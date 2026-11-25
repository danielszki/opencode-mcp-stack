#!/usr/bin/env node
/**
 * pexels.mjs: busca e baixa fotos do Pexels, com créditos. Não precisa de chave.
 *
 *   node scripts/pexels.mjs --busca "barber shop warm light" --quantos 6 --orientacao landscape --saida public/img
 *   node scripts/pexels.mjs --ids 6372911,8532753 --saida public/img        (quando já sabe as fotos)
 *
 * A busca abre pexels.com num Chromium de verdade (o mesmo da chicotada) e lê as fotos da página.
 * O download vem direto de images.pexels.com, em duas larguras (celular e desktop).
 * Com PEXELS_API_KEY no ambiente, usa a API oficial (traz o nome do fotógrafo).
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL, fileURLToPath } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt = (k, d) => {
  const i = argv.indexOf("--" + k);
  return i < 0 ? d : argv[i + 1];
};
const busca = opt("busca");
const idsArg = opt("ids");
const quantos = Math.min(30, Number(opt("quantos", 6)));
const orientacao = opt("orientacao", "landscape"); // landscape | portrait | square
const larguras = (opt("larguras", "800,1600")).split(",").map(Number);
const saida = path.resolve(opt("saida", "public/img"));

if (!busca && !idsArg) {
  console.log('uso: node scripts/pexels.mjs --busca "termos em inglês" [--quantos 6] [--orientacao landscape|portrait|square] [--larguras 800,1600] [--saida public/img]\n     node scripts/pexels.mjs --ids 6372911,8532753');
  process.exit(1);
}

async function viaApi() {
  const u = new URL("https://api.pexels.com/v1/search");
  u.searchParams.set("query", busca);
  u.searchParams.set("per_page", String(quantos));
  u.searchParams.set("orientation", orientacao);
  const r = await fetch(u, { headers: { Authorization: process.env.PEXELS_API_KEY } });
  if (!r.ok) throw new Error(`API ${r.status}`);
  const { photos = [] } = await r.json();
  return photos.map((f) => ({ id: String(f.id), alt: f.alt || busca, autor: f.photographer, perfil: f.photographer_url }));
}

async function viaNavegador() {
  let pw;
  for (const base of [path.join(AQUI, ".."), process.cwd()]) {
    try {
      const mod = await import(pathToFileURL(createRequire(path.join(base, "package.json")).resolve("playwright")).href);
      pw = mod.chromium ? mod : mod.default;
      break;
    } catch {}
  }
  if (!pw) throw new Error(`Playwright não encontrado: cd ${path.join(AQUI, "..")} && npm install && npx playwright install chromium`);
  const b = await pw.chromium.launch();
  try {
    const p = await b.newPage({ userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36", locale: "en-US", viewport: { width: 1280, height: 900 } });
    const u = `https://www.pexels.com/search/${encodeURIComponent(busca)}/${orientacao ? `?orientation=${orientacao}` : ""}`;
    await p.goto(u, { waitUntil: "domcontentloaded", timeout: 45000 });
    await p.waitForTimeout(3500);
    for (let i = 0; i < 3; i++) {
      const n = await p.$$eval("img[src*='images.pexels.com/photos/']", (x) => x.length);
      if (n >= quantos + 4) break;
      await p.mouse.wheel(0, 2500);
      await p.waitForTimeout(1200);
    }
    const fotos = await p.$$eval("img[src*='images.pexels.com/photos/']", (imgs) =>
      imgs.map((i) => ({ id: (i.src.match(/photos\/(\d+)/) || [])[1], alt: i.alt || "", w: i.naturalWidth })).filter((f) => f.id && f.w > 100),
    );
    const vistos = new Set();
    return fotos.filter((f) => !vistos.has(f.id) && vistos.add(f.id)).slice(0, quantos).map((f) => ({ id: f.id, alt: f.alt.replace(/^Free\s+/i, "").replace(/\s+Stock Photo$/i, "") || busca }));
  } finally {
    await b.close();
  }
}

let fotos;
if (idsArg) fotos = idsArg.split(",").map((id) => ({ id: id.trim(), alt: "" }));
else if (process.env.PEXELS_API_KEY) fotos = await viaApi().catch(() => viaNavegador());
else fotos = await viaNavegador();

if (!fotos.length) {
  console.error("Nada encontrado. Busque em inglês e com coisas concretas: objeto + luz + ângulo (\"barber chair warm light close up\").");
  process.exit(1);
}

fs.mkdirSync(saida, { recursive: true });
const slug = (busca ?? "pexels").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40);
const creditos = [];
for (const [i, f] of fotos.entries()) {
  const nome = `${slug}-${String(i + 1).padStart(2, "0")}`;
  const feitos = [];
  for (const w of larguras) {
    const url = `https://images.pexels.com/photos/${f.id}/pexels-photo-${f.id}.jpeg?auto=compress&cs=tinysrgb&w=${w}`;
    const r = await fetch(url);
    if (!r.ok) continue;
    const arq = `${nome}-${w}.jpg`;
    fs.writeFileSync(path.join(saida, arq), Buffer.from(await r.arrayBuffer()));
    feitos.push(arq);
  }
  if (!feitos.length) continue;
  const autor = f.autor ? `de [${f.autor}](${f.perfil}) ` : "";
  creditos.push(`- \`${feitos.join("`, `")}\` · foto ${autor}no [Pexels](https://www.pexels.com/photo/${f.id}/) · alt sugerido: "${f.alt}"`);
  console.log(`baixada ${nome} (${feitos.length} larguras) · ${f.alt.slice(0, 60)}`);
}
const credArq = path.join(saida, "CREDITOS.md");
const antes = fs.existsSync(credArq) ? fs.readFileSync(credArq, "utf8") : "# Créditos das imagens\n\nNo rodapé do site: \"Imagens ilustrativas: Pexels\".\n";
fs.writeFileSync(credArq, `${antes}\n## "${busca ?? idsArg}"\n${creditos.join("\n")}\n`);
console.log(`\n${creditos.length} fotos em ${saida}, larguras ${larguras.join(" e ")} para o srcset. Créditos em CREDITOS.md.`);
console.log('Use: <img src="X-800.jpg" srcset="X-800.jpg 800w, X-1600.jpg 1600w" sizes="(min-width: 900px) 50vw, 100vw" alt="..." width="..." height="..." loading="lazy">');
