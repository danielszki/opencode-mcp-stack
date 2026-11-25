/** chicote · holofote.js: leva --x e --y de .holofote até o cursor (uma vez por quadro, só com mouse). */
(() => {
  if (!matchMedia("(hover: hover) and (pointer: fine)").matches || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  document.querySelectorAll(".holofote").forEach((el) => {
    let raf = 0, x = 0, y = 0;
    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      x = e.clientX - r.left; y = e.clientY - r.top;
      if (!raf) raf = requestAnimationFrame(() => { raf = 0; el.style.setProperty("--x", x + "px"); el.style.setProperty("--y", y + "px"); });
    }, { passive: true });
  });
})();
