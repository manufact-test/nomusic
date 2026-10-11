// Native disclosures keep focus and scroll position; history is loaded only
// for the selected account. Responses never replace the page or reopen a card.
// This script is authorized by its exact CSP hash on the owner rewards page.
(() => {
  for (const card of document.querySelectorAll('[data-reward-account]')) {
    const content = card.querySelector('[data-reward-content]');
    const summary = card.querySelector('summary');
    let loading = false;
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
