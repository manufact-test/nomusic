/* CELIKOM source-before-play: same Yandex HTMLMediaElement, never creates another player. */
(function(root) {
  "use strict";
  const GLOBAL = "__CELIKOM_WEB_SOURCE_V1__";
  if (root[GLOBAL]) return;
  const adapterFactory = root.__CELIKOM_YANDEX_ADAPTER_V1__;
  if (!adapterFactory || !root.HTMLMediaElement) return;
  const adapter = adapterFactory.createAdapter(root);
  const allowed = new Map();
  let enabled = false;
  let reported = "";
  const native = root.CelikomBridge;
  const origin = root.location && root.location.origin;
  if (origin !== "https://music.yandex.ru") return;
  const numeric = x => /^[1-9][0-9]{0,23}$/.test(String(x || ""));
  const post = message => {
    try { native && native.postMessage(JSON.stringify(message)); }
    catch (_) { /* Never break Yandex */ }
  };
  const identity = snapshot => {
    const t = snapshot && snapshot.track;
    if (!t || !numeric(t.id) || t.ambiguous || t.confidence < 100) return null;
    const entry = adapter.trackCatalog.get(t.id);
    if (!entry || !numeric(entry.albumId) || !Number.isFinite(entry.durationMs)) return null;
    if (Math.abs(entry.durationMs - (t.metadata && t.metadata.durationMs || 0)) > 1500) return null;
    return { id: t.id, albumId: entry.albumId, durationMs: entry.durationMs };
  };
  function observed(snapshot) {
    const t = identity(snapshot);
    if (!t) return;
    const key = t.id + ":" + t.albumId + ":" + t.durationMs;
    if (key === reported) return;
    reported = key;
    post({kind:"track", id:t.id, albumId:t.albumId, durationMs:t.durationMs});
  }
  const api = {
    enable(value) { enabled = value === true; if (enabled) observed(adapter.getSnapshot("enabled")); },
    ready(id, albumId, durationMs, uri) {
      if (!numeric(id) || !numeric(albumId) || !Number.isSafeInteger(durationMs)) return;
      try {
        const u = new URL(uri);
        if (u.origin !== "https://music.yandex.ru" ||
            !/^\/__celikom_audio\/[A-Za-z0-9-]{20,120}\/[1-9][0-9]{0,23}\/[1-9][0-9]{0,23}\.mp3$/.test(u.pathname)) return;
        if (!u.pathname.endsWith("/" + id + "/" + albumId + ".mp3")) return;
        allowed.set(id, {albumId, durationMs, uri:u.href});
        while (allowed.size > 40) allowed.delete(allowed.keys().next().value);
      } catch (_) {}
    },
    clear() { allowed.clear(); enabled = false; }
  };
  Object.defineProperty(root, GLOBAL, {value: Object.freeze(api), writable: false});
  const originalPlay = root.HTMLMediaElement.prototype.play;
  root.HTMLMediaElement.prototype.play = function celikomSourceFirstPlay(...args) {
    try {
      if (enabled && this.tagName === "AUDIO" && !this.srcObject &&
          this.currentTime <= 0.15 && this.paused) {
        const snapshot = adapter.getSnapshot("celikom-before-play");
        const t = identity(snapshot);
        const bound = snapshot?.player?.mediaId &&
              adapter.getMediaElement(snapshot.player.mediaId);
        const candidate = t && allowed.get(t.id);
        if (t && bound === this && candidate && candidate.albumId === t.albumId
            && Math.abs(candidate.durationMs - t.durationMs) <= 1500
            && !this.src.includes("/__celikom_audio/")) {
          // The host still owns this SAME player clock. No second audio element.
          const previousSource = this.currentSrc || this.src;
          const element = this;
          let alternateStarted = false;
          let startupFallbackUsed = false;
          if (typeof element.addEventListener === "function") {
            element.addEventListener("playing", () => {
              const playingAlternate=element.currentSrc === candidate.uri || element.src === candidate.uri;
              alternateStarted=playingAlternate;
              post({kind:"playback",id:t.id,phase:playingAlternate
                ? "alternate-playing":"host-overwrote-source"});
            },{once:true});
            element.addEventListener("error", () => {
              if (!startupFallbackUsed && !alternateStarted && previousSource &&
                  (element.src === candidate.uri || element.currentSrc === candidate.uri)) {
                startupFallbackUsed = true;
                element.src = previousSource;
                element.load();
                post({kind:"playback",id:t.id,phase:"original-startup-fallback"});
                try {
                  const playback=Reflect.apply(originalPlay,element,[]);
                  playback?.catch?.(() => {});
                } catch (_) { /* No extra audio decoder may be started */ }
              } else {
                post({kind:"playback",id:t.id,phase:"alternate-error"});
              }
            },{once:true});
          }
          // Source change happens before native host play(), never after playback starts.
          element.src = candidate.uri;
          element.load();
          post({kind:"selected", id:t.id});
        }
      }
    } catch (_) { /* Original stays playable */ }
    return Reflect.apply(originalPlay, this, args);
  };
  adapter.mount({
    onSnapshot(snapshot) { if (enabled) observed(snapshot); },
    onPlayerEvent(event) { if (enabled) observed(event && event.snapshot); }
  });
  post({kind:"injected"});
})(globalThis);
