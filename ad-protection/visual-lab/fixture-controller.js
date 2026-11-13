/*
 * Isolated fixture-only demonstration of reversible visual banner suppression.
 * NEVER register this file in a production extension or on Yandex Music.
 */
(function () {
  'use strict';
  const PREFIXES = Object.freeze(['TopAdvertBanner_', 'SideAdvertBanner_']);
  const PROTECTED = 'audio, video, [data-test-protected], [role="dialog"]';

  function matchesBanner(node) {
    if (!node || node.nodeType !== 1 || typeof node.getAttribute !== 'function') return false;
    const value = node.getAttribute('class');
    if (typeof value !== 'string') return false;
    const tokens = value.split(/\s+/);
    return tokens.some(token => PREFIXES.some(prefix => token.startsWith(prefix)));
  }

  function createController(root, MutationObserverImpl = globalThis.MutationObserver) {
    if (!root || root.nodeType !== 1 || root.getAttribute('data-celikom-fixture') !== '1') {
      throw Error('Visual controller is restricted to explicit synthetic fixtures');
    }
    if (typeof MutationObserverImpl !== 'function') throw Error('MutationObserver required');
    let enabled = false;
    let disposed = false;
    const original = new Map();

    function safeCandidate(node) {
      if (!matchesBanner(node)) return false;
      if (typeof node.closest === 'function' && node.closest(PROTECTED)) return false;
      if (typeof node.querySelector === 'function' && node.querySelector(PROTECTED)) return false;
      return true;
    }

    function restore(node) {
      if (!original.has(node)) return;
      const prev = original.get(node);
      original.delete(node);
      // If the page changed display after our suppression, never overwrite it.
      if (node.style.getPropertyValue('display') !== 'none' ||
          node.style.getPropertyPriority('display') !== 'important') return;
      if (prev.value) node.style.setProperty('display', prev.value, prev.priority);
      else node.style.removeProperty('display');
    }

    function restoreSubtree(node) {
      if (!node || node.nodeType !== 1) return;
      restore(node);
      if (typeof node.querySelectorAll === 'function') {
        for (const child of node.querySelectorAll('*')) restore(child);
      }
    }

    function inspect(node) {
      if (!node || node.nodeType !== 1) return;
      const safe = safeCandidate(node);
      if (!enabled || !safe) {
        restore(node);
        return;
      }
      if (!original.has(node)) {
        original.set(node, {
          value: node.style.getPropertyValue('display'),
          priority: node.style.getPropertyPriority('display')
        });
      }
      node.style.setProperty('display', 'none', 'important');
    }

    function scan(node) {
      if (!node || node.nodeType !== 1) return;
      inspect(node);
      if (typeof node.querySelectorAll === 'function') {
        for (const element of node.querySelectorAll('[class*="AdvertBanner_"]')) inspect(element);
      }
    }

    const observer = new MutationObserverImpl(records => {
      if (!enabled || disposed) return;
      for (const record of records) {
        if (record.type === 'attributes') inspect(record.target);
        else if (record.type === 'childList') {
          // Removed nodes must not stay referenced for the entire listening session.
          for (const node of record.removedNodes || []) restoreSubtree(node);
          for (const node of record.addedNodes) scan(node);
        }
      }
    });
    observer.observe(root, {subtree: true, childList: true, attributes: true, attributeFilter: ['class']});

    return Object.freeze({
      enable() {
        if (disposed) throw Error('Controller disposed');
        if (enabled) return;
        enabled = true;
        scan(root);
      },
      disable() {
        enabled = false;
        for (const node of [...original.keys()]) restore(node);
      },
      dispose() {
        enabled = false;
        observer.disconnect();
        for (const node of [...original.keys()]) restore(node);
        disposed = true;
      },
      snapshot() {
        return {enabled, disposed, hiddenBannerCandidates: original.size, scope: 'synthetic-fixture-only'};
      }
    });
  }

  globalThis.CELIKOM_VISUAL_FIXTURE = Object.freeze({createController, matchesBanner});
})();
