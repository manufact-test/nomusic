(function () {
  'use strict';
  // Strict export schema: never forward unknown content, identifiers, URLs or page text.
  const KINDS = ['banner','overlay','video','audio'];
  const MEDIA = ['audio','video'];
  const EVENTS = ['play','playing','pause','ended','waiting','stalled','error'];
  const MARKERS = ['ad-heard','normal-music','video-ad-seen','popup-ad-seen'];
  function count(n) {
    if (!Number.isSafeInteger(n) || n < 0 || n > 1000000000) throw Error('Invalid count');
    return n;
  }
  function seconds(n) {
    if (!Number.isSafeInteger(n) || n < 0 || n > 604800) throw Error('Invalid time');
    return n;
  }
  function normalize(input) {
    if (!input || input.schema !== 'celikom-ad-observer-v1' ||
        !input.candidates || !input.media ||
        !Array.isArray(input.markers) || !Array.isArray(input.recent)) throw Error('Invalid observer report');
    const ageSeconds = seconds(input.ageSeconds);
    const candidates = Object.fromEntries(KINDS.map(k=>[k,count(input.candidates[k])]));
    const media = Object.fromEntries(MEDIA.map(k=>[k,
      Object.fromEntries(EVENTS.map(e=>[e,count(input.media[k]?.[e])]))]));
    if (input.markers.length > 20 || input.recent.length > 80) throw Error('Oversized report');
    const markers = input.markers.map(x=>{
      if (!x || !MARKERS.includes(x.kind)) throw Error('Unknown marker');
      const s = seconds(x.s);
      if (s > ageSeconds + 2) throw Error('Marker outside session');
      return {s,kind:x.kind};
    });
    const recent = input.recent.map(x=>{
      if (!x) throw Error('Missing event');
      const s = seconds(x.s);
      if (s > ageSeconds + 2) throw Error('Event outside session');
      if (x.category === 'candidate' && KINDS.includes(x.kind))
        return {s,category:'candidate',kind:x.kind};
      if (x.category === 'media' && MEDIA.includes(x.kind) && EVENTS.includes(x.event))
        return {s,category:'media',kind:x.kind,event:x.event};
      if (x.category === 'marker' && MARKERS.includes(x.kind))
        return {s,category:'marker',kind:x.kind};
      throw Error('Unknown event');
    });
    return {schema:'celikom-ad-observer-v1',ageSeconds,candidates,media,
      droppedRoots:count(input.droppedRoots),markers,recent};
  }
  globalThis.CELIKOM_OBSERVER_EXPORT = Object.freeze({normalize});
})();