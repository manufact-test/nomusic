(function () {
  'use strict';
  // Hypothetical CSS class markers from research, NOT verified current Yandex ad detection.
  const RULES = Object.freeze({
    banner: ['TopAdvertBanner_', 'SideAdvertBanner_'],
    overlay: ['AdvertModal_', 'AdvertisingModal_', 'AdModal_'],
    video: ['VideoAd_'],
    audio: ['AudioAd_', 'AudioAdvert_', 'AdvertAudio_']
  });
  const KINDS = Object.freeze(Object.keys(RULES));
  const MEDIA_EVENTS = Object.freeze(['play', 'playing', 'pause', 'ended', 'waiting', 'stalled', 'error']);
  const MEDIA_KINDS = Object.freeze(['audio', 'video']);
  const MARKER_KINDS = Object.freeze(['ad-heard', 'normal-music', 'video-ad-seen', 'popup-ad-seen']);
  function classifyClassValue(value) {
    if (typeof value !== 'string' || value.length > 8192) return [];
    const tokens = value.trim().split(/\s+/).slice(0, 128);
    return KINDS.filter(kind => RULES[kind].some(prefix =>
      tokens.some(token => token.startsWith(prefix))));
  }
  function classifyElement(node) {
    if (!node || node.nodeType !== 1 || typeof node.getAttribute !== 'function') return [];
    return classifyClassValue(node.getAttribute('class'));
  }
  function createSession(clock = () => performance.now(), limit = 80) {
    const cap = Number.isInteger(limit) && limit >= 1 && limit <= 250 ? limit : 80;
    let start = clock(), droppedRoots = 0, events = [], markers = [];
    let candidates, media;
    function clearCounters() {
      candidates = Object.fromEntries(KINDS.map(kind => [kind, 0]));
      media = Object.fromEntries(MEDIA_KINDS.map(kind =>
        [kind, Object.fromEntries(MEDIA_EVENTS.map(name => [name, 0]))]));
    }
    clearCounters();
    function append(item) {
      events.push({s: Math.max(0, Math.floor((clock() - start) / 1000)), ...item});
      if (events.length > cap) events.shift();
    }
    function recordCandidate(kind) {
      if (!Object.hasOwn(candidates, kind)) return false;
      candidates[kind]++;
      append({category: 'candidate', kind});
      return true;
    }
    function recordMedia(kind, event) {
      if (!MEDIA_KINDS.includes(kind) || !MEDIA_EVENTS.includes(event)) return false;
      media[kind][event]++;
      append({category: 'media', kind, event});
      return true;
    }
    function recordMarker(kind) {
      if (!MARKER_KINDS.includes(kind)) return false;
      const s = Math.max(0, Math.floor((clock() - start) / 1000));
      markers.push({s, kind});
      if (markers.length > 20) markers.shift();
      append({category: 'marker', kind});
      return true;
    }
    function dropRoots(amount = 1) {
      if (Number.isSafeInteger(amount) && amount > 0) droppedRoots += amount;
    }
    function snapshot() {
      return {
        schema: 'celikom-ad-observer-v1',
        interpretation: 'candidates-only-not-confirmed-advertisements',
        ageSeconds: Math.max(0, Math.floor((clock() - start) / 1000)),
        candidates: {...candidates},
        media: Object.fromEntries(MEDIA_KINDS.map(kind => [kind, {...media[kind]}])),
        droppedRoots,
        markers: markers.map(item => ({...item})),
        recent: events.map(event => ({...event}))
      };
    }
    function reset() {
      start = clock();
      droppedRoots = 0;
      events = [];
      markers = [];
      clearCounters();
      return snapshot();
    }
    return Object.freeze({recordCandidate, recordMedia, recordMarker, dropRoots, snapshot, reset});
  }
  globalThis.CELIKOM_AD_OBSERVER_CORE = Object.freeze({
    classifyClassValue, classifyElement, createSession, KINDS, MEDIA_EVENTS, MEDIA_KINDS, MARKER_KINDS
  });
})();
