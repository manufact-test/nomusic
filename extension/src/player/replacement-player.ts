(function registerReplacementPlayer(root) {
  "use strict";
  const KEY = "__CELIKOM_REPLACEMENT_PLAYER_V1__";
  if (root[KEY]) return;
  class ReplacementPlayer {
    constructor(environment, onFatal) {
      this.environment = environment;
      this.onFatal = onFatal;
      this.destroyed = false;
      this.cancelLoad = null;
      this.playPending = false;
      this.wantPlay = false;
      this.blobUrl = null;
      this.fetchAbort = null;
      this.audio = environment.document.createElement("audio");
      this.audio.dataset.celikomReplacement = "true";
      this.audio.hidden = true;
      this.audio.preload = "auto";
      this.audio.muted = true;
      this.audio.addEventListener("error", () => { if (!this.destroyed) onFatal("replacement-media-error"); });
      this.audio.addEventListener("ended", () => { if (!this.destroyed && !this.demoLoop) onFatal("replacement-ended"); });
    }
    async prepare(asset) {
      this.demoLoop = asset.demoLoop === true;
      this.audio.loop = this.demoLoop;
      if (!this.demoLoop) this.audio.crossOrigin = "anonymous";
      const parent = this.environment.document.documentElement;
      if (!parent) throw new Error("Document root is unavailable");
      parent.append(this.audio);
      let sourceUrl = asset.url;
      if (asset.demoLoop === true) {
        // Preserve the accepted PoC's packaged-asset → blob playback path.
        // This is only a bounded synthetic fixture; future real files stream
        // directly through the Range-capable API, never through a full-file blob.
        this.fetchAbort = new this.environment.AbortController();
        const fetchTimer = this.environment.setTimeout(() => this.fetchAbort?.abort(), 6000);
        try {
          const response = await this.environment.fetch(asset.url, { cache: "force-cache", signal: this.fetchAbort.signal });
          if (!response.ok) throw new Error(`Demo asset HTTP ${response.status}`);
          const blob = await response.blob();
          if (this.destroyed) throw new Error("Replacement cancelled");
          if (!blob.size || blob.size > 5 * 1024 * 1024) throw new Error("Demo asset size is invalid");
          this.blobUrl = this.environment.URL.createObjectURL(blob);
          sourceUrl = this.blobUrl;
        } finally { this.environment.clearTimeout(fetchTimer); this.fetchAbort = null; }
      }
      if (this.destroyed) throw new Error("Replacement cancelled");
      await new Promise((resolve, reject) => {
        const cleanup = () => {
          this.environment.clearTimeout(timer);
          for (const event of ["loadedmetadata", "canplay"]) this.audio.removeEventListener(event, onReady);
          this.audio.removeEventListener("error", onError);
          this.cancelLoad = null;
        };
        const onReady = () => {
          if (this.audio.readyState < 2 || !Number.isFinite(this.audio.duration) || this.audio.duration <= 0) return;
          cleanup(); resolve();
        };
        const onError = () => { cleanup(); reject(new Error("Replacement load failed")); };
        const timer = this.environment.setTimeout(() => { cleanup(); reject(new Error("Replacement load timeout")); }, 6000);
        this.cancelLoad = () => { cleanup(); reject(new Error("Replacement cancelled")); };
        for (const event of ["loadedmetadata", "canplay"]) this.audio.addEventListener(event, onReady);
        this.audio.addEventListener("error", onError);
        this.audio.src = sourceUrl;
        this.audio.load();
        onReady();
      });
      if (this.destroyed) throw new Error("Replacement cancelled");
    }
    applyState(player) {
      this.audio.volume = Math.min(1, Math.max(0, player.volume));
      this.audio.muted = Boolean(player.muted);
      this.audio.playbackRate = player.playbackRate > 0 ? player.playbackRate : 1;
    }
    play() {
      this.wantPlay = true;
      if (this.destroyed || this.playPending || !this.audio.paused) return;
      this.playPending = true;
      Promise.resolve(this.audio.play()).then(() => {
        if (this.destroyed || !this.wantPlay) this.audio.pause();
      }).catch(() => {
        // pause() can legitimately reject an in-flight play() with AbortError.
        if (!this.destroyed && this.wantPlay) this.onFatal("replacement-play-blocked");
      }).finally(() => { this.playPending = false; });
    }
    pause() { this.wantPlay = false; this.audio.pause(); }
    destroy() {
      if (this.destroyed) return;
      this.destroyed = true;
      this.fetchAbort?.abort();
      this.cancelLoad?.();
      this.audio.muted = true;
      this.pause();
      this.audio.removeAttribute("src");
      this.audio.load();
      this.audio.remove();
      if (this.blobUrl) { this.environment.URL.revokeObjectURL(this.blobUrl); this.blobUrl = null; }
    }
  }
  Object.defineProperty(root, KEY, { value: Object.freeze({ ReplacementPlayer }), writable: false });
})(globalThis);
