(function () {
  'use strict';
  if (globalThis.__CELIKOM_AD_OBSERVER_ACTIVE__) return;
  const core = globalThis.CELIKOM_AD_OBSERVER_CORE;
  if (!core || !document.documentElement || !chrome.runtime || !chrome.runtime.onMessage) return;
  globalThis.__CELIKOM_AD_OBSERVER_ACTIVE__ = true;
  // Observe classes and native media lifecycle only; do NOT alter DOM, player, network or storage.
  const MATCH = [
    '[class*="TopAdvertBanner_"]', '[class*="SideAdvertBanner_"]',
    '[class*="AdvertModal_"]', '[class*="AdvertisingModal_"]', '[class*="AdModal_"]',
    '[class*="VideoAd_"]', '[class*="AudioAd_"]',
    '[class*="AudioAdvert_"]', '[class*="AdvertAudio_"]'
  ].join(',');
  const session = core.createSession();
  let known = new WeakMap();
  const pending = new Set();
  let timer = null;
  const MAX_QUEUED = 160, MAX_PER_FLUSH = 40, DELAY = 180;

  function inspect(node) {
    const kinds = core.classifyElement(node);
    // Each candidate appearance is counted once per continuous class-state.
    // Reset the seen kinds when a SPA removes a marker, otherwise a later
    // reappearance on the same element would be silently missed.
    if (!kinds.length) {
      known.delete(node);
      return;
    }
    const before = known.get(node);
    const current = new Set(kinds);
    for (const kind of kinds) {
      if (!before || !before.has(kind)) session.recordCandidate(kind);
    }
    known.set(node, current);
  }
  function scan(node) {
    if (!node || node.nodeType !== 1) return;
    inspect(node);
    if (typeof node.querySelectorAll === 'function') {
      for (const match of node.querySelectorAll(MATCH)) inspect(match);
    }
  }
  function flush() {
    timer = null;
    let handled = 0;
    for (const node of pending) {
      pending.delete(node);
      if (node.isConnected !== false) scan(node);
      if (++handled >= MAX_PER_FLUSH) break;
    }
    if (pending.size) schedule();
  }
  function schedule() { if (timer === null) timer = setTimeout(flush, DELAY); }
  function enqueue(node) {
    if (!node || node.nodeType !== 1) return;
    if (pending.size >= MAX_QUEUED && !pending.has(node)) {
      session.dropRoots();
      return;
    }
    pending.add(node);
    schedule();
  }
  const mutationObserver = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'attributes') enqueue(record.target);
      else if (record.type === 'childList') {
        for (const node of record.addedNodes) enqueue(node);
      }
    }
  });
  const options = {childList: true, subtree: true, attributes: true, attributeFilter: ['class']};
  mutationObserver.observe(document.documentElement, options);
  for (const node of document.querySelectorAll(MATCH)) inspect(node);

  // No media URL, audio samples, title, source, account identifier or tokens are read.
  for (const eventName of core.MEDIA_EVENTS) {
    document.addEventListener(eventName, event => {
      const node = event.target;
      if (!(node instanceof HTMLMediaElement)) return;
      const tag = typeof node.tagName === 'string' ? node.tagName.toLowerCase() : '';
      if (tag === 'audio' || tag === 'video') session.recordMedia(tag, eventName);
    }, true);
  }
  function reset() {
    pending.clear();
    known = new WeakMap();
    for (const node of document.querySelectorAll(MATCH)) {
      const kinds = core.classifyElement(node);
      if (kinds.length) known.set(node, new Set(kinds));
    }
    return session.reset();
  }
  chrome.runtime.onMessage.addListener((message, sender, reply) => {
    if (sender?.id !== chrome.runtime.id || !message || typeof message !== 'object') return false;
    if (message.type === 'CELIKOM_OBSERVER_GET') reply(session.snapshot());
    else if (message.type === 'CELIKOM_OBSERVER_RESET') reply(reset());
    else if (message.type === 'CELIKOM_OBSERVER_MARK') {
      if (typeof message.kind !== 'string' || !core.MARKER_KINDS.includes(message.kind)) return false;
      session.recordMarker(message.kind);
      reply(session.snapshot());
    }
    return false;
  });
  window.addEventListener('pagehide', () => {
    mutationObserver.disconnect();
    if (timer !== null) clearTimeout(timer);
    timer = null;
    pending.clear();
  });
  window.addEventListener('pageshow', () => {
    mutationObserver.observe(document.documentElement, options);
    for (const node of document.querySelectorAll(MATCH)) inspect(node);
  });
})();
