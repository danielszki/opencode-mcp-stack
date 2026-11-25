#!/usr/bin/env node
/**
 * chicotada.mjs: mede a página num Chromium de verdade e dá a nota dos portões (70 pontos).
 *
 *   node scripts/chicotada.mjs <url | arquivo.html> [--publico idoso] [--aparelho fraco] [--saida chicote/chicotada]
 *                              [--rubrica chicote/chicotada/rubrica.json] [--so-hero]
 *
 * Aparelhos: 360×640 (CPU 4× mais lenta, 4G ruim), 390×844, 1440×900.
 * Saída: relatorio.md, relatorio.json e prints (dobra e página inteira) na pasta --saida.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL, fileURLToPath } from "node:url";

import { APARELHOS, PERFIS } from "./perfis.mjs";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const alvoArg = argv.find((a, i) => !a.startsWith("--") && !(argv[i - 1] ?? "").startsWith("--"));
const opt = (k, d) => {
  const i = argv.indexOf("--" + k);
  if (i < 0) return d;
  const v = argv[i + 1];
  return v === undefined || v.startsWith("--") ? true : v;
};
if (!alvoArg || opt("ajuda")) {
  console.log("uso: node scripts/chicotada.mjs <url | arquivo.html> [--publico geral|idoso|jovem|b2b|tecnico] [--aparelho fraco|medio|forte] [--saida pasta] [--rubrica rubrica.json] [--so-hero] [--tipo venda-direta|contato|cadastro|sistema]");
  process.exit(alvoArg ? 0 : 1);
}

const publico = opt("publico", "geral");
const aparelho = opt("aparelho", publico === "idoso" ? "fraco" : "medio");
const P = PERFIS[publico];
const A = APARELHOS[aparelho];
if (!P || !A) {
  console.error("perfil ou aparelho desconhecido");
  process.exit(1);
}
const soHero = !!opt("so-hero", false);
const tipo = opt("tipo", "contato"); // venda-direta | contato | cadastro | sistema
const saida = path.resolve(opt("saida", "chicote/chicotada"));
fs.mkdirSync(saida, { recursive: true });
const url = /^https?:|^file:/.test(alvoArg) ? alvoArg : pathToFileURL(path.resolve(alvoArg)).href;

// Playwright: da pasta da skill, depois do projeto atual.
async function carregarPlaywright() {
  for (const base of [path.join(AQUI, ".."), process.cwd()]) {
    try {
      const req = createRequire(path.join(base, "package.json"));
      const mod = await import(pathToFileURL(req.resolve("playwright")).href);
      return mod.chromium ? mod : mod.default;
    } catch {}
  }
  console.error(`\nPlaywright não encontrado. Rode uma vez:\n  cd ${path.join(AQUI, "..")} && npm install && npx playwright install chromium\n`);
  process.exit(2);
}
const { chromium } = await carregarPlaywright();

// orçamento de palavras (ver referencias/02-historia.md)
const LIMITE_HERO = publico === "idoso" ? 30 : 35;
const LIMITE_SECAO = publico === "idoso" ? 70 : publico === "b2b" || publico === "tecnico" ? 110 : 90;

const APARELHOS_TESTE = [
  { id: "360", largura: 360, altura: 640, lento: true, movel: true },
  { id: "390", largura: 390, altura: 844, lento: false, movel: true },
  { id: "1440", largura: 1440, altura: 900, lento: false, movel: false },
];

// Coletores de LCP e CLS antes de qualquer script da página.
const OBSERVADORES = `
  window.__chicote = { lcp: 0, lcpEl: "", cls: 0 };
  try {
    new PerformanceObserver((l) => { for (const e of l.getEntries()) { window.__chicote.lcp = e.startTime; const el = e.element; window.__chicote.lcpEl = el ? (el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") + (el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\\s+/).slice(0,2).join(".") : "")) : ""; } }).observe({ type: "largest-contentful-paint", buffered: true });
    new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__chicote.cls += e.value; }).observe({ type: "layout-shift", buffered: true });
  } catch (e) {}
`;

// Tudo que roda dentro da página para medir.
function medirNaPagina({ alvoMin, corpoMin, minimo, contrasteMin, limiteHero, limiteSecao }) {
  const vw = innerWidth, vh = innerHeight;
  const visivel = (el) => {
    const s = getComputedStyle(el);
    if (s.display === "none" || s.visibility === "hidden" || +s.opacity === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const sel = (el) => {
    if (el.id) return `#${el.id}`;
    let s = el.tagName.toLowerCase();
    if (typeof el.className === "string" && el.className.trim()) s += "." + el.className.trim().split(/\s+/).slice(0, 2).join(".");
    const t = (el.innerText || el.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ").slice(0, 40);
    return t ? `${s} "${t}"` : s;
  };
  // cor
  const parse = (c) => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p[3] === undefined ? 1 : p[3] };
  };
  const lum = ({ r, g, b }) => {
    const f = (v) => ((v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const misturar = (cima, baixo) => ({ r: cima.r * cima.a + baixo.r * (1 - cima.a), g: cima.g * cima.a + baixo.g * (1 - cima.a), b: cima.b * cima.a + baixo.b * (1 - cima.a), a: 1 });
  const fundoDe = (el) => {
    const camadas = [];
    let imagem = false;
    for (let n = el; n; n = n.parentElement) {
      const s = getComputedStyle(n);
      if (s.backgroundImage && s.backgroundImage !== "none") imagem = true;
      const c = parse(s.backgroundColor);
      if (c && c.a > 0) {
        camadas.push(c);
        if (c.a >= 1) break;
      }
    }
    let cor = { r: 255, g: 255, b: 255, a: 1 };
    for (let i = camadas.length - 1; i >= 0; i--) cor = misturar(camadas[i], cor);
    return { cor, imagem };
  };
  const razao = (a, b) => {
    const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x);
    return (l1 + 0.05) / (l2 + 0.05);
  };

  // elementos de texto: folhas com texto próprio
  const textos = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const vistos = new Set();
  while (walker.nextNode()) {
    const t = walker.currentNode;
    if (!t.textContent.trim()) continue;
    const el = t.parentElement;
    if (!el || vistos.has(el) || !visivel(el) || el.closest("script,style,noscript,svg")) continue;
    vistos.add(el);
    textos.push(el);
  }
  let contrasteOk = 0, contrasteTotal = 0, abaixoDe3 = 0;
  const contrasteFalhas = [], sobreImagem = [];
  let fonteCorpoOk = 0, fonteCorpoTotal = 0;
  const fonteFalhas = [];
  for (const el of textos) {
    const s = getComputedStyle(el);
    const px = parseFloat(s.fontSize);
    const peso = parseInt(s.fontWeight) || 400;
    const fg = parse(s.color);
    const { cor: bg, imagem } = fundoDe(el);
    const grande = px >= 24 || (px >= 18.66 && peso >= 700);
    const min = Math.max(grande ? 3 : 4.5, grande ? Math.min(contrasteMin, 4.5) : contrasteMin);
    if (fg) {
      const cr = razao(fg.a < 1 ? misturar(fg, bg) : fg, bg);
      contrasteTotal++;
      if (imagem) sobreImagem.push(sel(el));
      if (cr >= min - 0.01) contrasteOk++;
      else contrasteFalhas.push({ el: sel(el), razao: +cr.toFixed(2), minimo: min });
      if (cr < 3) abaixoDe3++;
    }
    // fonte: texto de leitura = parágrafo/li/td com mais de 40 caracteres
    const txt = el.innerText.trim();
    // <small> é metadado (legal, crédito): só precisa do mínimo absoluto
    const leitura = /^(P|LI|TD|DD|BLOCKQUOTE|LABEL|SPAN|A|DIV)$/.test(el.tagName) && txt.length > 40 && !el.closest("small");
    if (px < minimo - 0.1) fonteFalhas.push({ el: sel(el), px, regra: `abaixo do mínimo absoluto ${minimo}px` });
    if (leitura) {
      fonteCorpoTotal++;
      if (px >= corpoMin - 0.1) fonteCorpoOk++;
      else fonteFalhas.push({ el: sel(el), px, regra: `texto de leitura abaixo de ${corpoMin}px` });
    }
  }

  // alvos de toque
  const clicaveis = [...document.querySelectorAll("a[href], button, input:not([type=hidden]), select, textarea, [role=button], [role=link], summary, label[for]")].filter(visivel);
  let alvosOk = 0;
  const alvosFalhas = [];
  for (const el of clicaveis) {
    const r = el.getBoundingClientRect();
    const dentroDeTexto = el.tagName === "A" && getComputedStyle(el).display === "inline" && el.parentElement && /^(P|LI|SPAN|SMALL|TD|DD)$/.test(el.parentElement.tagName) && el.parentElement.innerText.trim().length > el.innerText.trim().length + 10;
    if (dentroDeTexto) { alvosOk++; continue; }
    if (Math.min(r.width, r.height) >= alvoMin - 0.5) alvosOk++;
    else alvosFalhas.push({ el: sel(el), tamanho: `${Math.round(r.width)}×${Math.round(r.height)}` });
  }

  // CTA
  const palavrasCta = /(comprar|assinar|agendar|chamar|whatsapp|ligar|quero|come[cç]ar|cadastr|contratar|pedir|or[cç]amento|reservar|garantir|baixar|testar|experimentar|falar|entrar em contato|buy|start|get|book|call|sign up|try)/i;
  let cta = document.querySelector('[data-cta="principal"]');
  let ctaOrigem = "data-cta=principal";
  if (!cta || !visivel(cta)) {
    cta = [...document.querySelectorAll("[data-cta]")].find(visivel);
    ctaOrigem = "data-cta";
  }
  if (!cta) {
    cta = clicaveis.filter((el) => /^(A|BUTTON)$/.test(el.tagName) && palavrasCta.test(el.innerText || el.getAttribute("aria-label") || "")).sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)[0];
    ctaOrigem = "detectado pelo texto (marque com data-cta=\"principal\")";
  }
  if (!cta) {
    cta = clicaveis.filter((el) => /^(A|BUTTON)$/.test(el.tagName) && !el.closest("nav,header,footer")).sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)[0];
    ctaOrigem = "primeiro botão/link da página: o texto não diz a ação (marque com data-cta=\"principal\")";
  }
  let ctaInfo = null;
  if (cta) {
    const r = cta.getBoundingClientRect();
    ctaInfo = { el: sel(cta), origem: ctaOrigem, topo: Math.round(r.top + scrollY), base: Math.round(r.bottom + scrollY), altura: Math.round(r.height), naDobra: r.top >= 0 && r.bottom <= vh && r.left >= 0 && r.right <= vw };
  }
  const todosCta = [...document.querySelectorAll("[data-cta]")].filter(visivel).map((e) => Math.round(e.getBoundingClientRect().top + scrollY));
  const fixo = cta ? (() => { for (let n = cta; n; n = n.parentElement) { const p = getComputedStyle(n).position; if (p === "fixed" || p === "sticky") return true; } return false; })() : false;

  // SEO
  const meta = (n) => document.querySelector(`meta[name="${n}"],meta[property="${n}"]`)?.getAttribute("content") ?? "";
  const vp = meta("viewport");
  const h1s = [...document.querySelectorAll("h1")].filter(visivel);
  const seo = {
    lang: document.documentElement.lang || "",
    titulo: document.title || "",
    descricao: meta("description"),
    h1: h1s.map((h) => h.innerText.trim().replace(/\s+/g, " ")),
    ogImage: meta("og:image"),
    viewport: vp,
    zoomBloqueado: /user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b/i.test(vp),
    canonical: document.querySelector('link[rel="canonical"]')?.href ?? "",
    jsonld: document.querySelectorAll('script[type="application/ld+json"]').length,
  };

  // imagens
  const imgs = [...document.images].filter(visivel);
  const semAlt = imgs.filter((i) => !i.hasAttribute("alt")).map(sel);
  const grandesDemais = imgs.filter((i) => i.naturalWidth > i.getBoundingClientRect().width * devicePixelRatio * 2.2 && i.naturalWidth > 600).map((i) => `${sel(i)} ${i.naturalWidth}px exibida a ${Math.round(i.getBoundingClientRect().width)}px`);

  // medida de linha
  const linhasLongas = [...document.querySelectorAll("p")].filter(visivel).filter((p) => p.innerText.trim().length > 120).map((p) => {
    const s = getComputedStyle(p);
    const chars = p.getBoundingClientRect().width / (parseFloat(s.fontSize) * 0.5);
    return { el: sel(p), chars: Math.round(chars), alinhamento: s.textAlign, hifen: s.hyphens };
  }).filter((x) => x.chars > 85 || (x.alinhamento === "justify" && (x.chars < 45 || x.hifen !== "auto")));

  // texto: palavras por capítulo e jargão
  const contar = (t) => (t.match(/[\p{L}\p{N}]+/gu) || []).length;
  let capitulos = [...document.querySelectorAll("main > section, main > article, body > section")].filter(visivel);
  if (capitulos.length < 2) capitulos = [...(document.querySelector("main") || document.body).children].filter((e) => visivel(e) && !/^(NAV|HEADER|FOOTER|SCRIPT|STYLE)$/.test(e.tagName));
  const texto = capitulos.map((c, i) => {
    const t = c.innerText || "";
    const palavras = contar(t);
    const limite = i === 0 ? limiteHero : limiteSecao;
    return { el: sel(c).slice(0, 70), palavras, limite, passou: palavras <= limite };
  });
  const corpoTexto = (document.querySelector("main") || document.body).innerText || "";
  const JARGAO = [/solu[çc](ão|ões) (completa|inovadora|integrada|personalizada)s?/i, /inovador[ae]?s?\b/i, /revolucion[áa]ri[oa]s?/i, /disruptiv[oa]s?/i, /alavanc(ar|e|ando)/i, /potencializ(ar|e|ando)/i, /sinergia/i, /\bde ponta\b/i, /excel[êe]ncia/i, /qualidade e (compromisso|excel)/i, /elev(e|ar) (o |a )?(seu|sua)/i, /outro n[íi]vel/i, /agregar valor/i, /experi[êe]ncia [úu]nica/i, /empoder/i, /bem-vind[oa] ao (nosso )?site/i, /saiba mais/i, /clique aqui/i, /lorem ipsum/i, /nosso compromisso/i, /somos uma empresa/i, /transform(e|ar) (a |o )?(sua|seu) (presen[çc]a|neg[óo]cio)/i, /next level/i, /game[- ]changer/i, /seamless/i, /cutting[- ]edge/i, /unlock (your|the)/i, /elevate your/i];
  const jargao = [...new Set(JARGAO.flatMap((re) => { const m = corpoTexto.match(re); return m ? [m[0]] : []; }))];

  // cabeçalho: altura e comportamento no celular
  const cab = document.querySelector("header") || [...document.body.children].find((e) => { const p = getComputedStyle(e).position; return (p === "fixed" || p === "sticky") && e.getBoundingClientRect().top <= 1; });
  let cabecalho = null;
  if (cab && visivel(cab)) {
    const r = cab.getBoundingClientRect(), p = getComputedStyle(cab).position;
    cabecalho = { altura: Math.round(r.height), fixo: p === "fixed" || p === "sticky", temCta: !!cab.querySelector("[data-cta], a[href^='tel:'], a[href*='wa.me']"), menuEscondido: !!cab.querySelector("[aria-expanded], .hamburguer, .menu-toggle, button[aria-controls]") };
  }


  // ── atmosfera: o capítulo tem camada visual (gradiente, imagem, textura) ou é chapado?
  const ricoFundo = (el) => {
    for (const pseudo of [null, "::before", "::after"]) {
      const st = getComputedStyle(el, pseudo);
      if (pseudo && (st.content === "none" || st.content === "normal")) continue;
      if (st.backgroundImage && st.backgroundImage !== "none") return true;
    }
    const r = el.getBoundingClientRect();
    const area = r.width * r.height || 1;
    return [...el.querySelectorAll("img, canvas, video, svg, picture")].some((m) => { const q = m.getBoundingClientRect(); return visivel(m) && (q.width * q.height) / area >= 0.25; });
  };
  const ricoComPais = (el) => { for (let n = el; n && n !== document.documentElement; n = n.parentElement) if (ricoFundo(n)) return true; return ricoFundo(document.documentElement); };
  const blocosAtm = [...capitulos, ...document.querySelectorAll("footer")].filter(visivel);
  const atmosfera = { total: blocosAtm.length, ricos: blocosAtm.filter(ricoComPais).length, chapados: blocosAtm.filter((b) => !ricoComPais(b)).map((b) => sel(b).slice(0, 60)) };

  // ── visual: fotos reais, canvas, 3D em CSS ou SVG grande
  const midias = [];
  for (const m of document.querySelectorAll("img, canvas, svg, video, [data-pontos], *")) {
    if (!visivel(m)) continue;
    const r = m.getBoundingClientRect();
    const st = getComputedStyle(m);
    let tipo = null;
    if (m.tagName === "IMG" && (m.naturalWidth >= 600 || r.width >= 240)) tipo = "foto";
    else if (m.tagName === "VIDEO" && r.width >= 240) tipo = "vídeo";
    else if (m.tagName === "CANVAS" && r.width >= 200 && r.height >= 150) tipo = "canvas";
    else if (m.tagName === "svg" && r.width >= 200 && r.height >= 150) tipo = "svg";
    else if (st.transformStyle === "preserve-3d" || (st.perspective !== "none" && m.children.length)) tipo = "3d";
    else if (/repeating-linear-gradient|radial-gradient/.test(st.backgroundImage) && r.width >= 40 && r.height >= 160 && m.children.length === 0 && !m.closest("[data-chicote-3d-visto]")) tipo = "3d";
    if (tipo) { midias.push({ tipo, el: sel(m).slice(0, 50), naDobra: r.top < vh && r.bottom > 0 && r.top + scrollY < vh }); if (tipo === "3d") m.dataset.chicote3dVisto = 1; }
    if (midias.length > 40) break;
  }

  // ── profundidade: sombras em camadas e CTA com relevo
  const camadas = (bs) => (bs && bs !== "none" ? bs.split(/,(?![^(]*\))/).length : 0);
  const comProfundidade = [...document.querySelectorAll("body *")].filter((e) => visivel(e) && camadas(getComputedStyle(e).boxShadow) >= 2);
  const ctaEl = document.querySelector('[data-cta="principal"]') || document.querySelector("[data-cta]");
  const ctaRelevo = !!ctaEl && (camadas(getComputedStyle(ctaEl).boxShadow) >= 1 || /gradient/.test(getComputedStyle(ctaEl).backgroundImage));
  const profundidade = { elementos: comProfundidade.length, ctaRelevo };

  // ── eixo: card e botão centralizados no seu contêiner, ou à direita com texto à esquerda (exceção)
  const fundoProprio = (e) => { const c = parse(getComputedStyle(e).backgroundColor); return (c && c.a > 0.05) || getComputedStyle(e).backgroundImage !== "none"; };
  const ehCard = (e) => {
    if (/^(IMG|FIGURE|PICTURE|svg|CANVAS|A|BUTTON|HEADER|FOOTER|MAIN|SECTION|NAV|BODY|HTML)$/.test(e.tagName)) return false;
    const r = e.getBoundingClientRect(), pai = e.parentElement?.getBoundingClientRect();
    if (!pai || r.height < 90 || r.width < 160) return false;
    const st = getComputedStyle(e);
    const raio = parseFloat(st.borderTopLeftRadius) || 0;
    return raio >= 8 && (fundoProprio(e) || camadas(st.boxShadow) >= 1) && r.width <= pai.width * 0.88 && (e.innerText || "").trim().length > 8 && !e.querySelector("img") ;
  };
  const centradoNoPai = (e) => {
    let pai = e.parentElement;
    while (pai && pai.getBoundingClientRect().width <= e.getBoundingClientRect().width + 2) pai = pai.parentElement;
    if (!pai) return true;
    const r = e.getBoundingClientRect(), p = pai.getBoundingClientRect();
    const desvio = Math.abs((r.left + r.width / 2) - (p.left + p.width / 2)) / p.width;
    if (desvio <= 0.08) return true;
    // exceção espelhada: botão na coluna de texto (com título) e um visual/card na coluna da direita
    for (let n = e.parentElement, i = 0; n && i < 5; n = n.parentElement, i++) {
      if (!n.querySelector("h1,h2")) continue;
      const nr = n.getBoundingClientRect();
      const vizinho = [...(n.parentElement?.children || [])].some((x) => x !== n && visivel(x) && x.getBoundingClientRect().left >= nr.right - 4 && x.getBoundingClientRect().width > 120);
      if (vizinho) return true;
      break;
    }
    // exceção: está na metade direita e há texto relevante à esquerda dele
    if (r.left + r.width / 2 > p.left + p.width / 2) {
      const irmaoTexto = [...pai.querySelectorAll("h1,h2,h3,p")].some((t) => { const q = t.getBoundingClientRect(); return visivel(t) && q.right <= r.left + 4 && q.bottom > r.top - 200 && q.top < r.bottom + 200; });
      if (irmaoTexto) return true;
    }
    // em grade de vários itens lado a lado (pódio, bento), o grupo é que precisa estar centrado
    const irmaos = [...e.parentElement.children].filter((x) => x !== e && visivel(x) && Math.abs(x.getBoundingClientRect().top - r.top) < r.height);
    if (irmaos.length) {
      const todos = [e, ...irmaos].map((x) => x.getBoundingClientRect());
      const esq = Math.min(...todos.map((q) => q.left)), dir = Math.max(...todos.map((q) => q.right));
      const pp = e.parentElement.getBoundingClientRect();
      return Math.abs((esq + dir) / 2 - (pp.left + pp.width / 2)) / pp.width <= 0.08;
    }
    return false;
  };
  const cards = [...document.querySelectorAll("body *")].filter((e) => visivel(e) && ehCard(e)).filter((e, _, arr) => !arr.some((o) => o !== e && o.contains(e)));
  const ctas = [...document.querySelectorAll("[data-cta]")].filter((e) => visivel(e) && !e.closest("nav") && getComputedStyle(e).position !== "fixed" && !e.closest('[style*="position: fixed"]'));
  const alvosEixo = [...new Set([...cards, ...ctas])].filter((e) => { for (let n = e; n; n = n.parentElement) if (getComputedStyle(n).position === "fixed") return false; return true; });
  const fora = alvosEixo.filter((e) => !centradoNoPai(e));
  const cardsEsquerda = cards.filter((c) => { const ps = [...c.querySelectorAll("h2,h3,h4,p")].filter(visivel); return ps.length && ps.every((t) => getComputedStyle(t).textAlign === "left" || getComputedStyle(t).textAlign === "start"); });
  const eixo = { total: alvosEixo.length, centrados: alvosEixo.length - fora.length, fora: fora.map((e) => sel(e).slice(0, 60)), cardsTextoEsquerda: cardsEsquerda.map((e) => sel(e).slice(0, 60)), cards: cards.length };


  // ── tipografia: fonte de título de verdade, grande e apertada
  const genericas = /^(system-ui|-apple-system|blinkmacsystemfont|segoe ui|roboto|arial|helvetica|helvetica neue|georgia|times|times new roman|serif|sans-serif|ui-sans-serif|ui-serif|verdana|tahoma)$/i;
  const tit = document.querySelector("h1");
  let tipografia = null;
  if (tit && visivel(tit)) {
    const st = getComputedStyle(tit);
    const primeira = st.fontFamily.split(",")[0].replace(/["']/g, "").trim();
    const carregada = [...document.fonts].some((f) => f.status === "loaded" && f.family.replace(/["']/g, "").trim().toLowerCase() === primeira.toLowerCase());
    const px = parseFloat(st.fontSize);
    const ls = st.letterSpacing === "normal" ? 0 : parseFloat(st.letterSpacing) / px;
    const lh = st.lineHeight === "normal" ? 1.2 : parseFloat(st.lineHeight) / px;
    tipografia = { fonte: primeira, propria: !genericas.test(primeira) && carregada, px: Math.round(px), aperto: +ls.toFixed(3), entrelinha: +lh.toFixed(2) };
  }
  return {
    tipografia, atmosfera, midias, profundidade, eixo,
    texto, jargao, cabecalho,
    rolagemLateral: document.documentElement.scrollWidth > vw + 1,
    larguraDoc: document.documentElement.scrollWidth,
    alturaDoc: document.documentElement.scrollHeight,
    contraste: { ok: contrasteOk, total: contrasteTotal, abaixoDe3, falhas: contrasteFalhas.slice(0, 15), sobreImagem: sobreImagem.slice(0, 8) },
    fonte: { corpoOk: fonteCorpoOk, corpoTotal: fonteCorpoTotal, falhas: fonteFalhas.slice(0, 15) },
    alvos: { ok: alvosOk, total: clicaveis.length, falhas: alvosFalhas.slice(0, 15) },
    cta: ctaInfo, todosCta, ctaFixo: fixo,
    seo, semAlt, grandesDemais: grandesDemais.slice(0, 8), linhasLongas: linhasLongas.slice(0, 8),
    lcp: window.__chicote?.lcp ?? 0, lcpEl: window.__chicote?.lcpEl ?? "", cls: window.__chicote?.cls ?? 0,
  };
}

async function medirAparelho(browser, ap, reduzir = false) {
  const ctx = await browser.newContext({
    viewport: { width: ap.largura, height: ap.altura },
    deviceScaleFactor: ap.movel ? 2 : 1,
    isMobile: ap.movel,
    hasTouch: ap.movel,
    reducedMotion: reduzir ? "reduce" : "no-preference",
    locale: "pt-BR",
  });
  await ctx.addInitScript(OBSERVADORES);
  const page = await ctx.newPage();
  let bytes = 0, js = 0;
  if (ap.lento) {
    const cdp = await ctx.newCDPSession(page);
    await cdp.send("Network.enable");
    await cdp.send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: (1.6 * 1024 * 1024) / 8, uploadThroughput: (750 * 1024) / 8 });
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
    cdp.on("Network.loadingFinished", (e) => (bytes += e.encodedDataLength || 0));
    const tipos = new Map();
    cdp.on("Network.responseReceived", (e) => tipos.set(e.requestId, e.type));
    cdp.on("Network.loadingFinished", (e) => { if (tipos.get(e.requestId) === "Script") js += e.encodedDataLength || 0; });
  }
  const t0 = Date.now();
  try {
    await page.goto(url, { waitUntil: "load", timeout: 60000 });
  } catch (e) {
    await ctx.close();
    throw new Error(`não abriu ${url}: ${e.message}`);
  }
  await page.waitForTimeout(ap.lento ? 2500 : 1200);
  const carga = Date.now() - t0;

  let animacoesInfinitas = null;
  if (reduzir) {
    animacoesInfinitas = await page.evaluate(() => document.getAnimations().filter((a) => a.playState === "running" && a.effect?.getTiming?.().iterations === Infinity).map((a) => (a.effect.target ? a.effect.target.tagName.toLowerCase() + (a.effect.target.className && typeof a.effect.target.className === "string" ? "." + a.effect.target.className.split(" ")[0] : "") : "?") + " " + (a.animationName || a.constructor.name)));
    await ctx.close();
    return { animacoesInfinitas };
  }
  const prefixo = path.join(saida, ap.id);
  await page.screenshot({ path: `${prefixo}-dobra.png` });
  const m = await page.evaluate(medirNaPagina, { alvoMin: ap.movel ? P.alvo : Math.min(P.alvo, 32), corpoMin: P.corpo - (publico === "geral" ? 1 : 0), minimo: P.minimo, contrasteMin: P.contraste, limiteHero: LIMITE_HERO, limiteSecao: LIMITE_SECAO });
  if (!soHero) {
    // elementos fixos (barra de contato, cabeçalho fixo) apareceriam no meio do print da página inteira
    // imagens com loading="lazy" só carregam perto da tela: carregue todas antes do print inteiro
    await page.evaluate(async () => {
      document.querySelectorAll('img[loading="lazy"]').forEach((i) => (i.loading = "eager"));
      await Promise.all([...document.images].filter((i) => !i.complete).map((i) => new Promise((r) => { i.onload = i.onerror = r; setTimeout(r, 4000); })));
    });
    const ocultos = await page.evaluate(() => [...document.querySelectorAll("body *")].filter((e) => getComputedStyle(e).position === "fixed").map((e, i) => { e.dataset.chicoteFixo = i; e.style.setProperty("visibility", "hidden", "important"); return i; }).length);
    await page.screenshot({ path: `${prefixo}-inteira.png`, fullPage: true }).catch(() => {});
    if (ocultos) await page.evaluate(() => document.querySelectorAll("[data-chicote-fixo]").forEach((e) => e.style.removeProperty("visibility")));
  }
  // CTA presente ao longo da rolagem (celular)
  if (ap.movel && !soHero) {
    const passos = Math.max(1, Math.ceil(m.alturaDoc / ap.altura));
    let telasComCta = 0;
    for (let i = 0; i < passos; i++) {
      await page.evaluate((y) => scrollTo(0, y), i * ap.altura);
      await page.waitForTimeout(80);
      const tem = await page.evaluate(() => [...document.querySelectorAll("[data-cta], a[href^='tel:'], a[href*='wa.me'], a[href*='whatsapp']")].some((el) => { const r = el.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight && r.height > 0; }));
      if (tem) telasComCta++;
    }
    m.cadenciaCta = { telas: passos, comCta: telasComCta };
  }
  await ctx.close();
  return { ...m, bytes, js, carga };
}

// ─────────────────────────────── roda
const browser = await chromium.launch();
const res = {};
try {
  for (const ap of APARELHOS_TESTE) {
    process.stdout.write(`medindo ${ap.largura}×${ap.altura}${ap.lento ? " (lento)" : ""}… `);
    res[ap.id] = await medirAparelho(browser, ap);
    console.log("ok");
  }
  res.reduzido = await medirAparelho(browser, APARELHOS_TESTE[1], true);
} finally {
  await browser.close();
}

// ─────────────────────────────── nota
const portoes = [];
const add = (id, max, pontos, detalhe, falhas = []) => portoes.push({ id, max, pontos: Math.max(0, Math.min(max, +pontos.toFixed(1))), detalhe, falhas });
const m360 = res["360"], m390 = res["390"], m1440 = res["1440"];

add("cta-360", 8, m360.cta?.naDobra ? 8 : 0, m360.cta ? `${m360.cta.el} (${m360.cta.origem}) · topo ${m360.cta.topo}px, base ${m360.cta.base}px, dobra 640px${m360.cta.naDobra ? "" : " → FORA DA PRIMEIRA TELA"}` : "nenhum CTA encontrado: marque com data-cta=\"principal\"");
add("cta-desktop", 2, m1440.cta?.naDobra ? 2 : 0, m1440.cta ? `${m1440.cta.el} · base ${m1440.cta.base}px, dobra 900px` : "nenhum CTA encontrado");
const lateral = ["360", "390", "1440"].filter((k) => res[k].rolagemLateral);
add("sem-rolagem-lateral", 3, lateral.length ? 0 : 3, lateral.length ? `rolagem lateral em ${lateral.map((k) => `${k}px (documento com ${res[k].larguraDoc}px)`).join(", ")}` : "nenhuma");

const somar = (f) => ["360", "390", "1440"].reduce((acc, k) => { const v = f(res[k]); return { ok: acc.ok + v.ok, total: acc.total + v.total }; }, { ok: 0, total: 0 });
const c = somar((r) => ({ ok: r.contraste.ok, total: r.contraste.total }));
const pc = c.total ? c.ok / c.total : 1;
const abaixo3 = ["360", "390", "1440"].reduce((a, k) => a + res[k].contraste.abaixoDe3, 0);
add("contraste", 7, abaixo3 ? Math.min(3.5, 7 * pc) : pc >= 0.98 ? 7 : 7 * pc, `${c.ok}/${c.total} textos passam em ${P.contraste}:1 (texto grande: ${Math.min(P.contraste, 4.5) === 4.5 && P.contraste > 4.5 ? 4.5 : 3}:1)${abaixo3 ? ` · ${abaixo3} abaixo de 3:1` : ""}${m390.contraste.sobreImagem.length ? ` · sobre imagem (conferir no print): ${m390.contraste.sobreImagem.length}` : ""}`, [...m360.contraste.falhas, ...m1440.contraste.falhas].slice(0, 12).map((f) => `${f.el}: ${f.razao}:1 (mín. ${f.minimo})`));

const al = { ok: m360.alvos.ok + m390.alvos.ok, total: m360.alvos.total + m390.alvos.total };
add("alvos", 4, al.total ? 4 * (al.ok / al.total) : 4, `${al.ok}/${al.total} alvos no celular com ≥ ${P.alvo}px`, [...m360.alvos.falhas].slice(0, 12).map((f) => `${f.el}: ${f.tamanho}`));

const fo = somar((r) => ({ ok: r.fonte.corpoOk, total: r.fonte.corpoTotal }));
const fonteMin = ["360", "390", "1440"].flatMap((k) => res[k].fonte.falhas.filter((f) => f.regra.includes("absoluto")));
add("fonte", 4, (fo.total ? 4 * (fo.ok / fo.total) : 4) - (fonteMin.length ? 2 : 0), `${fo.ok}/${fo.total} blocos de leitura com ≥ ${P.corpo - (publico === "geral" ? 1 : 0)}px · ${fonteMin.length} textos abaixo de ${P.minimo}px`, [...m360.fonte.falhas].slice(0, 12).map((f) => `${f.el}: ${f.px}px (${f.regra})`));

const lcp = m360.lcp;
add("lcp", 5, lcp <= 2500 ? 5 : lcp >= 4000 ? 0 : 5 * (1 - (lcp - 2500) / 1500), `LCP ${(lcp / 1000).toFixed(2)} s no perfil lento (360px, CPU 4×, 4G ruim)${m360.lcpEl ? ` · elemento: ${m360.lcpEl}` : ""}`);

if (!soHero) {
  const cls = Math.max(m360.cls, m1440.cls);
  add("cls", 2, cls <= 0.1 ? 2 : cls >= 0.25 ? 0 : 2 * (1 - (cls - 0.1) / 0.15), `CLS ${cls.toFixed(3)}`);
  const kb = m360.bytes / 1024, jsKb = m360.js / 1024;
  add("peso", 3, kb <= A.pesoKB ? (jsKb <= A.jsKB ? 3 : 2) : kb >= A.pesoKB * 2 ? 0 : 3 * (1 - (kb - A.pesoKB) / A.pesoKB), `${Math.round(kb)} KB transferidos (orçamento ${A.pesoKB} KB) · JS ${Math.round(jsKb)} KB (orçamento ${A.jsKB} KB)`);
  const s = m390.seo;
  const seoItens = [
    [!!s.lang, `lang="${s.lang}"`],
    [s.titulo.length >= 30 && s.titulo.length <= 65, `title com ${s.titulo.length} caracteres`],
    [s.descricao.length >= 70 && s.descricao.length <= 160, `description com ${s.descricao.length} caracteres`],
    [s.h1.length === 1, `${s.h1.length} h1`],
    [!!s.ogImage && !!s.viewport && !s.zoomBloqueado, `og:image ${s.ogImage ? "ok" : "faltando"}, viewport ${s.viewport ? (s.zoomBloqueado ? "BLOQUEIA ZOOM" : "ok") : "faltando"}`],
  ];
  add("seo", 4, seoItens.filter(([ok]) => ok).length * 0.8, seoItens.map(([ok, t]) => `${ok ? "✓" : "✗"} ${t}`).join(" · "));
  const inf = res.reduzido.animacoesInfinitas ?? [];
  add("movimento", 2, inf.length ? 0 : 2, inf.length ? `com reduced-motion ainda rodam: ${inf.slice(0, 5).join(", ")}` : "nada infinito com prefers-reduced-motion");
}


// ── portões de gosto: atmosfera, visual, profundidade, eixo (as ordens diretas do SKILL.md)
{
  const at = m1440.atmosfera;
  const fr = at.total ? at.ricos / at.total : 0;
  add("atmosfera", 6, fr >= 0.75 ? 6 : 6 * (fr / 0.75), `${at.ricos}/${at.total} capítulos com camada visual (gradiente, luz, textura, foto)${at.chapados.length ? " · chapados: " + at.chapados.slice(0, 4).join("; ") : ""}`, at.chapados.map((c) => `${c}: fundo chapado. Dê luz (radial), textura (grão), gradiente longo ou foto com véu`));
  const vis = m1440.midias;
  const fotos = vis.filter((v) => v.tipo === "foto" || v.tipo === "vídeo").length;
  const outros = vis.length - fotos;
  const dobra = m1440.midias.some((v) => v.naDobra) || m360.midias.some((v) => v.naDobra);
  const semFotoOk = tipo === "sistema";
  const n = Math.min(3, vis.length);
  add("visual", 5, semFotoOk ? 5 : (n / 3) * 4 + (dobra ? 1 : 0), semFotoOk ? "tipo sistema: fotos não exigidas" : `${fotos} fotos/vídeos + ${outros} efeitos (canvas, 3D, SVG) · ${dobra ? "tem visual na primeira tela" : "NADA visual na primeira tela"} · mínimo: 3 peças visuais, 1 na dobra`, vis.length < 3 ? ["faltam peças visuais: baixe fotos (node scripts/pexels.mjs) ou desenhe com efeitos/ (pontos, maquete, holofote)"] : []);

  const tp = m1440.tipografia;
  if (tp) {
    const ptsFonte = tp.propria ? 1.5 : 0;
    const ptsTam = tp.px >= 56 ? 0.75 : tp.px >= 44 ? 0.4 : 0;
    const ptsAperto = tp.aperto <= -0.01 && tp.entrelinha <= 1.12 ? 0.75 : tp.entrelinha <= 1.12 ? 0.35 : 0;
    add("tipografia", 3, ptsFonte + ptsTam + ptsAperto, `h1 em "${tp.fonte}" ${tp.propria ? "(carregada)" : "(GENÉRICA: carregue uma fonte de título de verdade)"} · ${tp.px}px a 1440 (mín. 56) · letter-spacing ${tp.aperto}em (≤ −0,01) · entrelinha ${tp.entrelinha} (≤ 1,12)`);
  } else add("tipografia", 3, 0, "sem h1 visível");
  const pr = m1440.profundidade;
  add("profundidade", 5, Math.min(3, pr.elementos) + (pr.ctaRelevo ? 2 : 0), `${pr.elementos} elementos com sombra em camadas (mín. 3) · CTA ${pr.ctaRelevo ? "com relevo" : "CHAPADO: dê brilho interno, borda inferior e sombra"}`);
  const ex = m1440.eixo;
  const pe = ex.total ? ex.centrados / ex.total : 1;
  const ptsEixo = 3 * pe + (ex.cardsTextoEsquerda.length ? 0 : 1);
  add("eixo", 4, ptsEixo, `${ex.centrados}/${ex.total} cards e botões centralizados (ou à direita com texto à esquerda) · ${ex.cards} cards · ${ex.cardsTextoEsquerda.length ? ex.cardsTextoEsquerda.length + " com texto encostado à esquerda" : "conteúdo dos cards centralizado"}`, [...ex.fora.map((f) => `${f}: fora do eixo (encostado à esquerda)`), ...ex.cardsTextoEsquerda.map((f) => `${f}: texto do card alinhado à esquerda`)]);
}
{
  const tx = m390.texto;
  const dentro = tx.filter((t) => t.passou).length;
  const jg = m390.jargao;
  const ptsTexto = tx.length ? 2 * (dentro / tx.length) : 2;
  const ptsJargao = jg.length === 0 ? 2 : jg.length <= 2 ? 1 : 0;
  add("enxuto", 3, (ptsTexto + ptsJargao) * 0.75, `${dentro}/${tx.length} capítulos dentro do orçamento (hero ≤ ${LIMITE_HERO}, seção ≤ ${LIMITE_SECAO} palavras) · jargão: ${jg.length ? jg.map((j) => `"${j}"`).join(", ") : "nenhum"}`, tx.filter((t) => !t.passou).map((t) => `${t.el}: ${t.palavras} palavras (limite ${t.limite})`));
}
const maxPortoes = portoes.reduce((a, p) => a + p.max, 0);
const notaPortoes = +portoes.reduce((a, p) => a + p.pontos, 0).toFixed(1);
const escala = soHero ? 70 / maxPortoes : 1;

// rubrica
let rubrica = null;
const rubArq = opt("rubrica", null);
const MAX_RUB = { nivel: 6, "hero-frase": 4, roteiro: 3, metafora: 4, composicao: 3, costuras: 3, copy: 2, publico: 2, imagem: 3 };
if (rubArq) {
  const r = JSON.parse(fs.readFileSync(rubArq, "utf8"));
  const itens = Object.entries(MAX_RUB).map(([id, max]) => {
    const it = (r.itens ?? []).find((x) => x.id === id);
    const evid = (it?.evidencia ?? "").trim();
    const pontos = it && evid.length >= 15 ? Math.min(max, Number(it.pontos) || 0) : 0;
    return { id, max, pontos, evidencia: evid || "(sem evidência: vale zero)" };
  });
  rubrica = { itens, total: itens.reduce((a, i) => a + i.pontos, 0) };
}

const total = +(notaPortoes * escala + (rubrica?.total ?? 0)).toFixed(1);

// avisos (não pontuam, mas aparecem)
const avisos = [];
if (m360.cadenciaCta && m360.cadenciaCta.telas > 2 && !m360.ctaFixo && m360.cadenciaCta.comCta / m360.cadenciaCta.telas < 0.5) avisos.push(`CTA visível em só ${m360.cadenciaCta.comCta} de ${m360.cadenciaCta.telas} telas de rolagem a 360px: repita o CTA a cada ~1,5 tela ou use barra fixa`);
if (m390.semAlt.length) avisos.push(`imagens sem alt: ${m390.semAlt.slice(0, 5).join(", ")}`);
if (m1440.grandesDemais.length) avisos.push(`imagens maiores que o necessário: ${m1440.grandesDemais.join("; ")}`);
if (m1440.linhasLongas.length) avisos.push(`medida de linha ou justificado problemático: ${m1440.linhasLongas.map((l) => `${l.el} ~${l.chars} car./linha${l.alinhamento === "justify" ? " justificado" + (l.hifen !== "auto" ? " sem hyphens:auto" : "") : ""}`).join("; ")}`);
const cab = m360.cabecalho;
if (cab && cab.fixo && cab.altura > 640 * 0.12) avisos.push(`cabeçalho fixo com ${cab.altura}px a 360×640 (${Math.round((cab.altura / 640) * 100)}% da tela): o limite é 12% (77px)`);
if (cab && cab.menuEscondido && !cab.temCta && !(m360.cta && m360.cta.naDobra)) avisos.push("no celular, o CTA principal parece estar escondido dentro do menu");
if (publico === "idoso" && cab && cab.menuEscondido) avisos.push("público idoso: troque o menu escondido (hambúrguer) por palavras visíveis ou barra inferior");
if (!soHero && m390.texto.length >= 2) {
  const total = m390.texto.reduce((a, t) => a + t.palavras, 0);
  if (total > LIMITE_SECAO * 7) avisos.push(`a página tem ${total} palavras nos capítulos: corte até caber em ~${LIMITE_SECAO * 7}`);
}
if (!m390.seo.jsonld) avisos.push("sem dados estruturados JSON-LD (LocalBusiness, Product, FAQPage)");
if (!m390.seo.canonical) avisos.push("sem link canonical");
if (m360.cta && m360.cta.altura < Math.max(P.alvo, publico === "idoso" ? 56 : 48)) avisos.push(`CTA principal com ${m360.cta.altura}px de altura no celular; o perfil pede ${Math.max(P.alvo, publico === "idoso" ? 56 : 48)}px`);
if (m360.cta && !m360.cta.origem.startsWith("data-cta")) avisos.push("CTA detectado pelo texto: marque o principal com data-cta=\"principal\" para a medida ser exata");

const relatorio = { url, publico, aparelho, soHero, total, notaPortoes: +(notaPortoes * escala).toFixed(1), maxPortoes: 70, portoes, rubrica, avisos, medidas: res };
fs.writeFileSync(path.join(saida, "relatorio.json"), JSON.stringify(relatorio, null, 2));

const linhas = [];
linhas.push(`# Chicotada · ${total}/100${rubrica ? "" : " (só portões; preencha a rubrica)"}`);
linhas.push("");
linhas.push(`\`${url}\` · público \`${publico}\` · aparelho \`${aparelho}\`${soHero ? " · só hero" : ""}`);
linhas.push("");
linhas.push(`## Portões medidos: ${(notaPortoes * escala).toFixed(1)}/70`);
linhas.push("");
linhas.push("| Portão | Nota | Medida |");
linhas.push("|---|---|---|");
for (const p of portoes) linhas.push(`| ${p.pontos >= p.max ? "✓" : "✗"} \`${p.id}\` | ${p.pontos}/${p.max} | ${p.detalhe.replace(/\|/g, "/")} |`);
const comFalha = portoes.filter((p) => p.falhas.length);
if (comFalha.length) {
  linhas.push("", "### Onde corrigir");
  for (const p of comFalha) {
    linhas.push("", `**${p.id}**`);
    for (const f of p.falhas) linhas.push(`- ${f}`);
  }
}
if (rubrica) {
  linhas.push("", `## Rubrica: ${rubrica.total}/30`, "", "| Item | Nota | Evidência |", "|---|---|---|");
  for (const i of rubrica.itens) linhas.push(`| \`${i.id}\` | ${i.pontos}/${i.max} | ${i.evidencia.replace(/\|/g, "/").replace(/\n/g, " ")} |`);
} else {
  linhas.push("", "## Rubrica: pendente", "", "Preencha `rubrica.json` (ver `referencias/10-pontuacao.md`) e rode de novo com `--rubrica`.");
}
if (avisos.length) {
  linhas.push("", "## Avisos (não pontuam, mas pesam na rubrica)");
  for (const a of avisos) linhas.push(`- ${a}`);
}
linhas.push("", "## Prints", "");
for (const ap of APARELHOS_TESTE) linhas.push(`- ${ap.id}px: \`${ap.id}-dobra.png\`${soHero ? "" : `, \`${ap.id}-inteira.png\``}`);
linhas.push("", total >= 100 ? "**100. Pode entregar.**" : `**${total}/100. Continua chicoteando:** corrija primeiro o portão de maior peso que falhou.`);
fs.writeFileSync(path.join(saida, "relatorio.md"), linhas.join("\n") + "\n");

console.log("\n" + linhas.slice(0, 6 + portoes.length + 3).join("\n"));
if (avisos.length) console.log("\nAvisos:\n- " + avisos.join("\n- "));
console.log(`\nRelatório completo: ${path.join(saida, "relatorio.md")}`);
console.log(total >= 100 ? "\n100. Pode entregar." : `\n${total}/100. Continua chicoteando.`);
process.exitCode = total >= 100 ? 0 : 3;
