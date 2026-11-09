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
          // Source change happens before native host play(), never after playback starts.
          this.src = candidate.uri;
          this.load();
          post({kind:"selected", id:t.id});
          if (typeof this.addEventListener === "function") {
            const id=t.id, url=candidate.uri;
            this.addEventListener("playing", () => {
              post({kind:"playback",id,phase:this.currentSrc === url || this.src === url
                ? "alternate-playing":"host-overwrote-source"});
            },{once:true});
            this.addEventListener("error", () => post({kind:"playback",id,phase:"alternate-error"}),{once:true});
          }
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
