/* Additive owner-review interactions; source v10 JS remains unchanged. */
(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const revealTargets = [
    '.hero-copy', '.owner-visual', '.benefit', '.process .eyebrow',
    '.process h2', '.step', '.demo-copy', '.demo-board',
    '.familiar > div', '.community-header', '.community-card',
    '.trust-copy', '.trust-callout', '.faq-heading-row',
    '.faq-nav', '.faq-content', '.reward-copy', '.reward-illustration',
    '.install-text', '.install-card', '.closing'
  ];
  if (!reduced.matches && 'IntersectionObserver' in window) {
    const targets = document.querySelectorAll(revealTargets.join(','));
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add('owner-visible');
        observer.unobserve(entry.target);
      }
    }, {threshold:0.06, rootMargin:'0px 0px -36px 0px'});
    for (const [index, node] of [...targets].entries()) {
      node.classList.add('owner-reveal');
      node.style.setProperty('--owner-delay', String((index % 3) * 65) + 'ms');
      observer.observe(node);
    }
    document.documentElement.classList.add('owner-motion');
  }

  // Details/summary stays keyboard-accessible; native operation is used when
  // reduced motion is requested or WAAPI is unavailable.
  for (const details of document.querySelectorAll('#faq .faq-item')) {
    const summary = details.querySelector('summary');
    const answer = details.querySelector('.answer');
    if (!summary || !answer) continue;
    let animation = null;
    summary.addEventListener('click', event => {
      if (reduced.matches || typeof answer.animate !== 'function') return;
      event.preventDefault();
      if (animation) {
        animation.cancel();
        animation = null;
      }
      const wasOpen = details.open;
      if (!wasOpen) details.open = true;
      const fullHeight = answer.scrollHeight;
      const keyframes = wasOpen
        ? [{height:fullHeight + 'px',opacity:1}, {height:'0px',opacity:0}]
        : [{height:'0px',opacity:0}, {height:fullHeight + 'px',opacity:1}];
      animation = answer.animate(keyframes, {
        duration:wasOpen ? 260 : 330,
        easing:'cubic-bezier(.22,.72,.25,1)'
      });
      const current = animation;
      current.onfinish = () => {
        if (animation !== current) return;
        if (wasOpen) details.open = false;
        animation = null;
      };
      current.oncancel = () => {
        if (animation === current) animation = null;
      };
    });
  }
})();
