/**
 * chicote · revelar.js: um traço SVG se desenha quando entra na tela (cota, rota, trilho, assinatura). Uma vez só.
 *
 *   <svg viewBox="0 0 400 40" aria-hidden="true"><path data-revelar d="M0 20 H400" stroke="currentColor" fill="none"/></svg>
 *   <script src="efeitos/revelar.js" defer></script>
 *
 * Com prefers-reduced-motion o traço já aparece pronto.
 */
(() => {
  const caminhos = document.querySelectorAll("[data-revelar]");
  if (!caminhos.length || matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;
  const io = new IntersectionObserver((es) => {
    for (const e of es) {
      if (!e.isIntersecting) continue;
      e.target.style.strokeDashoffset = "0";
      io.unobserve(e.target);
    }
  }, { rootMargin: "0px 0px -15% 0px" });
  caminhos.forEach((p) => {
    const L = p.getTotalLength();
    p.style.strokeDasharray = L;
    p.style.strokeDashoffset = L;
    p.style.transition = `stroke-dashoffset ${p.dataset.duracao || 900}ms cubic-bezier(.2,.8,.2,1)`;
    io.observe(p);
  });
})();
