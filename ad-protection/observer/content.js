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
  const MAX_RECORDS_PER_CALLBACK = 1000, MAX_ADDED_PER_RECORD = 160, MAX_MATCHES_PER_SCAN = 120;
  let paused = false;

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
  function visitDocumentCandidates(trackNew = true) {
    // DOM-wide scans have a fixed evidence cap, including startup and bfcache.
    const matches = document.querySelectorAll(MATCH);
    const limit = Math.min(matches.length, MAX_MATCHES_PER_SCAN);
    for (let i = 0; i < limit; i++) {
      const node = matches[i];
      if (trackNew) inspect(node);
      else {
        const kinds = core.classifyElement(node);
        if (kinds.length) known.set(node, new Set(kinds));
      }
    }
    if (matches.length > limit) session.dropRoots(matches.length - limit);
  }
  function scan(node) {
    if (!node || node.nodeType !== 1) return;
    inspect(node);
    if (typeof node.querySelectorAll === 'function') {
      const matches = node.querySelectorAll(MATCH);
      const limit = Math.min(matches.length, MAX_MATCHES_PER_SCAN);
      for (let i = 0; i < limit; i++) inspect(matches[i]);
      if (matches.length > limit) session.dropRoots(matches.length - limit);
    }
  }
  function flush() {
    timer = null;
    if (paused) { pending.clear(); return; }
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
    if (paused || !node || node.nodeType !== 1) return;
    if (pending.size >= MAX_QUEUED && !pending.has(node)) {
      session.dropRoots();
      return;
    }
    pending.add(node);
    schedule();
  }
  const mutationObserver = new MutationObserver(records => {
    if (paused) return;
    const count = Math.min(records.length, MAX_RECORDS_PER_CALLBACK);
    if (records.length > count) session.dropRoots(records.length - count);
    for (let i = 0; i < count; i++) {
      const record = records[i];
      if (record.type === 'attributes') enqueue(record.target);
      else if (record.type === 'childList') {
        const added = record.addedNodes || [];
        const limit = Math.min(added.length, MAX_ADDED_PER_RECORD);
        for (let j = 0; j < limit; j++) enqueue(added[j]);
        if (added.length > limit) session.dropRoots(added.length - limit);
      }
    }
  });
  const options = {childList: true, subtree: true, attributes: true, attributeFilter: ['class']};
  mutationObserver.observe(document.documentElement, options);
  visitDocumentCandidates();

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
    if (timer !== null) clearTimeout(timer);
    timer = null;
    known = new WeakMap();
    session.reset();
    // Existing matches form the baseline, not new candidate events.
    visitDocumentCandidates(false);
    return session.snapshot();
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
    paused = true;
    mutationObserver.disconnect();
    if (timer !== null) clearTimeout(timer);
    timer = null;
    pending.clear();
  });
  window.addEventListener('pageshow', () => {
    paused = false;
    mutationObserver.observe(document.documentElement, options);
    visitDocumentCandidates();
  });
})();
