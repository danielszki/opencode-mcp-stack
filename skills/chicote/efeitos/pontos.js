/**
 * chicote · pontos.js: campo de pontos que acende e cresce perto do cursor ou do dedo.
 *
 *   <div data-pontos data-passo="28" data-raio="140" style="aspect-ratio: 1; color: #e9b43c"></div>
 *   <script src="efeitos/pontos.js" defer></script>
 *
 * Travas: desenha só enquanto há movimento (para sozinho), pausa fora da tela, DPR ≤ 2, número de pontos
 * proporcional à área, estático com prefers-reduced-motion, funciona com toque (pointerdown/move).
 * A cor vem de `color` (currentColor) ou de data-cor.
 */
(() => {
  const reduzir = matchMedia("(prefers-reduced-motion: reduce)");
  function iniciar(caixa) {
    if (caixa.__pontos) return;
    caixa.__pontos = true;
    const c = document.createElement("canvas");
    c.setAttribute("aria-hidden", "true");
    c.style.cssText = "position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none";
    if (getComputedStyle(caixa).position === "static") caixa.style.position = "relative";
    caixa.prepend(c);
    const ctx = c.getContext("2d");
    const passo = +caixa.dataset.passo || 28;
    const raio = +caixa.dataset.raio || 140;
    const cor = caixa.dataset.cor || getComputedStyle(caixa).color;
    let w = 0, h = 0, pts = [], alvo = { x: -1e4, y: -1e4 }, rodando = false, visivel = true;

    function medir() {
      const r = caixa.getBoundingClientRect();
      const dpr = Math.min(2, devicePixelRatio || 1);
      w = r.width; h = r.height;
      c.width = Math.round(w * dpr); c.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      pts = [];
      for (let y = passo / 2; y < h; y += passo) for (let x = passo / 2; x < w; x += passo) pts.push({ x, y, s: 0 });
      desenhar();
    }
    function desenhar() {
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = cor;
      let mexendo = false;
      for (const p of pts) {
        const d = Math.hypot(p.x - alvo.x, p.y - alvo.y);
        const t = reduzir.matches ? 0 : Math.max(0, 1 - d / raio);
        p.s += (t - p.s) * 0.18; // mola: chega rápido, assenta suave
        if (Math.abs(t - p.s) > 0.003) mexendo = true;
        ctx.globalAlpha = 0.22 + p.s * 0.78;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.2 + p.s * 3.2, 0, 6.2832);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      return mexendo;
    }
    function quadro() {
      if (desenhar() && visivel) requestAnimationFrame(quadro);
      else rodando = false;
    }
    function cutucar() {
      if (!rodando && visivel && !reduzir.matches) { rodando = true; requestAnimationFrame(quadro); }
    }
    const mover = (e) => {
      const r = caixa.getBoundingClientRect();
      alvo = { x: e.clientX - r.left, y: e.clientY - r.top };
      cutucar();
    };
    caixa.addEventListener("pointermove", mover, { passive: true });
    caixa.addEventListener("pointerdown", mover, { passive: true });
    caixa.addEventListener("pointerleave", () => { alvo = { x: -1e4, y: -1e4 }; cutucar(); });
    new IntersectionObserver(([e]) => { visivel = e.isIntersecting; }).observe(caixa);
    new ResizeObserver(medir).observe(caixa);
  }
  const ir = () => document.querySelectorAll("[data-pontos]").forEach(iniciar);
  document.readyState === "loading" ? addEventListener("DOMContentLoaded", ir) : ir();
})();
