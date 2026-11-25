/**
 * chicote · inclinacao.js: o card inclina em 3D seguindo o cursor, com reflexo de luz.
 *
 *   <article data-inclinar data-max="8" class="inclinavel">…</article>
 *   <script src="efeitos/inclinacao.js" defer></script>
 *
 * CSS do reflexo (opcional):
 *   .inclinavel { position: relative; overflow: hidden; }
 *   .inclinavel::after { content: ""; position: absolute; inset: 0; pointer-events: none; opacity: var(--brilho, 0);
 *     background: radial-gradient(circle at var(--bx, 50%) var(--by, 0%), rgb(255 255 255 / .35), transparent 55%);
 *     transition: opacity 300ms; }
 *
 * Só com mouse (no toque o card fica parado), só transform, desliga com prefers-reduced-motion.
 */
(() => {
  if (!matchMedia("(hover: hover) and (pointer: fine)").matches || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  document.querySelectorAll("[data-inclinar]").forEach((el) => {
    const max = +el.dataset.max || 8;
    let raf = 0, px = 0, py = 0;
    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      px = (e.clientX - r.left) / r.width - 0.5;
      py = (e.clientY - r.top) / r.height - 0.5;
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        el.style.transition = "transform 80ms linear";
        el.style.transform = `perspective(900px) rotateX(${(-py * max).toFixed(2)}deg) rotateY(${(px * max).toFixed(2)}deg)`;
        el.style.setProperty("--bx", `${((px + 0.5) * 100).toFixed(1)}%`);
        el.style.setProperty("--by", `${((py + 0.5) * 100).toFixed(1)}%`);
        el.style.setProperty("--brilho", "1");
      });
    }, { passive: true });
    el.addEventListener("pointerleave", () => {
      el.style.transition = "transform 450ms cubic-bezier(.2,.8,.2,1)";
      el.style.transform = "";
      el.style.setProperty("--brilho", "0");
    });
  });
})();
