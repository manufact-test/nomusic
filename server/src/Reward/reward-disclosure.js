// Native disclosures keep focus and scroll position; history is loaded only
// for the selected account. Responses never replace the page or reopen a card.
// This script is authorized by its exact CSP hash on the owner rewards page.
(() => {
  // At the bottom of a long history, collapsing shortens the document below
  // the viewport. Reserve only the missing space so Chrome cannot clamp scroll.
  const tail = document.createElement('div');
  tail.setAttribute('aria-hidden', 'true');
  tail.style.height = '0px';
  tail.style.overflowAnchor = 'none';
  document.body.appendChild(tail);
  window.addEventListener('scroll', () => {
    const reserved = parseFloat(tail.style.height) || 0;
    const naturalHeight = document.documentElement.scrollHeight - reserved;
    if (reserved && window.scrollY + window.innerHeight <= naturalHeight) tail.style.height = '0px';
  }, { passive: true });
  for (const card of document.querySelectorAll('[data-reward-account]')) {
    const content = card.querySelector('[data-reward-content]');
    const summary = card.querySelector('summary');
    let loading = false;
    summary.addEventListener('click', event => {
      if (!card.open) return;
      event.preventDefault();
      const y = window.scrollY;
      const height = content.getBoundingClientRect().height;
      const remaining = document.documentElement.scrollHeight - height;
      const missing = Math.max(0, y + window.innerHeight - remaining);
      tail.style.height = ((parseFloat(tail.style.height) || 0) + missing) + 'px';
      card.open = false;
      window.scrollTo({ top: y, behavior: 'instant' });
    });
    async function load(raw) {
      if (loading) return;
      const url = new URL(raw, location.href);
      if (url.origin !== location.origin || url.pathname !== '/admin' ||
          url.searchParams.get('tab') !== 'rewards' ||
          url.searchParams.get('account') !== card.dataset.rewardAccount) return;
      loading = true;
      content.setAttribute('aria-busy', 'true');
      try {
        const response = await fetch(url.href, { credentials: 'same-origin',
          cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(15000) });
        if (!response.ok || !response.headers.get('Content-Type')?.startsWith('text/html')) throw new Error('history_unavailable');
        const parsed = new DOMParser().parseFromString(await response.text(), 'text/html');
        const detail = parsed.querySelector('[data-reward-account="' + card.dataset.rewardAccount + '"][data-reward-loaded="1"] [data-reward-content]');
        if (!detail) throw new Error('history_unavailable');
        content.replaceChildren(...Array.from(detail.childNodes, node => document.importNode(node, true)));
        card.dataset.rewardLoaded = '1';
      } catch (_) {
        const note = document.createElement('p');
        note.textContent = 'Не удалось загрузить историю. Закройте и откройте аккаунт, чтобы повторить.';
        content.replaceChildren(note);
        delete card.dataset.rewardLoaded;
      } finally {
        loading = false;
        content.removeAttribute('aria-busy');
      }
    }
    card.addEventListener('toggle', () => {
      summary.textContent = card.open ? 'Свернуть' : 'Песни и бонусы';
      if (card.open && card.dataset.rewardLoaded !== '1') void load(card.dataset.rewardUrl);
    });
    content.addEventListener('click', event => {
      const link = event.target.closest?.('a[data-reward-page]');
      if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      void load(link.href);
    });
  }
})();
