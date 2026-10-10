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
      this.mediaSource = null;
      this.sourceBuffer = null;
      this.streamTask = null;
      this.audio = environment.document.createElement("audio");
      this.audio.dataset.celikomReplacement = "true";
      this.audio.hidden = true;
      this.audio.preload = "auto";
      this.audio.muted = true;
      this.audio.addEventListener("error", () => { if (!this.destroyed) onFatal("replacement-media-error"); });
      this.audio.addEventListener("ended", () => { if (!this.destroyed && !this.demoLoop) onFatal("replacement-ended"); });
    }
    async pumpRemote(asset) {
      // Page media-src permits blob: but rejects the private HTTPS origin.
      // Feed MSE with verified 512 KiB ranges; no whole-file JS buffer.
      const source = this.mediaSource;
      const abort = this.fetchAbort;
      const waitForSourceOpen = async () => {
        if (source.readyState === "open") return;
        await new Promise((resolve, reject) => {
          const cleanup = () => {
            this.environment.clearTimeout(timeout);
            source.removeEventListener("sourceopen", opened);
            abort.signal.removeEventListener("abort", cancelled);
          };
          const opened = () => { cleanup(); resolve(); };
          const cancelled = () => { cleanup(); reject(new Error("remote-stream-cancelled")); };
          const timeout = this.environment.setTimeout(() => { cleanup(); reject(new Error("remote-stream-timeout")); }, 10000);
          source.addEventListener("sourceopen", opened, { once: true });
          abort.signal.addEventListener("abort", cancelled, { once: true });
        });
      };
      await waitForSourceOpen();
      if (this.destroyed || abort.signal.aborted) return;
      const buffer = source.addSourceBuffer("audio/mpeg");
      this.sourceBuffer = buffer;
      source.duration = asset.durationMs / 1000;
      const append = async (bytes) => {
        if (this.destroyed || abort.signal.aborted) return;
        await new Promise((resolve, reject) => {
          const cleanup = () => {
            this.environment.clearTimeout(timeout);
            buffer.removeEventListener("updateend", done);
            buffer.removeEventListener("error", failed);
            abort.signal.removeEventListener("abort", cancelled);
          };
          const done = () => { cleanup(); resolve(); };
          const failed = () => { cleanup(); reject(new Error("remote-buffer-error")); };
          const cancelled = () => { cleanup(); reject(new Error("remote-stream-cancelled")); };
          const timeout = this.environment.setTimeout(() => { cleanup(); reject(new Error("remote-buffer-timeout")); }, 10000);
          buffer.addEventListener("updateend", done, { once: true });
          buffer.addEventListener("error", failed, { once: true });
          abort.signal.addEventListener("abort", cancelled, { once: true });
          try { buffer.appendBuffer(bytes); } catch (_error) { cleanup(); reject(new Error("remote-buffer-error")); }
        });
      };
      let total = null;
      let offset = 0;
      const chunkSize = 512 * 1024;
      const maxSize = 30 * 1024 * 1024;
      while (!this.destroyed && !abort.signal.aborted && (total === null || offset < total)) {
        if (buffer.buffered?.length
            && buffer.buffered.end(buffer.buffered.length - 1) - this.audio.currentTime > 120) {
          await new Promise((resolve) => {
            const timer = this.environment.setTimeout(resolve, 500);
            abort.signal.addEventListener("abort", () => { this.environment.clearTimeout(timer); resolve(); }, { once: true });
          });
          continue;
        }
        const lastRequested = total === null
          ? offset + chunkSize - 1 : Math.min(total - 1, offset + chunkSize - 1);
        let response;
        try {
          response = await this.environment.fetch(asset.url, {
            method: "GET",
            headers: { Range: "bytes=" + offset + "-" + lastRequested },
            credentials: "omit", cache: "no-store", redirect: "error", signal: abort.signal
          });
        } catch (_error) { throw new Error("remote-stream-network"); }
        if (response.status !== 206) throw new Error("remote-stream-http");
        if (!(response.headers.get("content-type") || "").toLowerCase().startsWith("audio/mpeg")) {
          throw new Error("remote-stream-format");
        }
        const match = /^bytes ([0-9]+)-([0-9]+)\/([0-9]+)$/.exec(response.headers.get("content-range") || "");
        if (!match) throw new Error("remote-stream-range");
        const from = Number(match[1]), last = Number(match[2]), length = Number(match[3]);
        if (!Number.isSafeInteger(length) || length < 1 || length > maxSize
            || from !== offset || last < from || last > lastRequested
            || (total !== null && length !== total)) throw new Error("remote-stream-range");
        total = length;
        const bytes = await response.arrayBuffer();
        if (bytes.byteLength !== last - from + 1 || bytes.byteLength > chunkSize) {
          throw new Error("remote-stream-range");
        }
        if (this.destroyed || abort.signal.aborted) return;
        await append(bytes);
        offset = last + 1;
      }
      if (!this.destroyed && !abort.signal.aborted && source.readyState === "open") {
        source.endOfStream();
      }
    }
    async prepare(asset) {
      this.demoLoop = asset.demoLoop === true;
      this.audio.loop = this.demoLoop;
      const parent = this.environment.document.documentElement;
      if (!parent) throw new Error("Document root is unavailable");
      parent.append(this.audio);
      let sourceUrl = asset.url;
      if (!this.demoLoop) {
        const MediaSource = this.environment.MediaSource;
        if (!MediaSource || !MediaSource.isTypeSupported("audio/mpeg")
            || !Number.isFinite(asset.durationMs) || asset.durationMs <= 0) {
          throw new Error("remote-mse-unsupported");
        }
        this.mediaSource = new MediaSource();
        this.fetchAbort = new this.environment.AbortController();
        this.blobUrl = this.environment.URL.createObjectURL(this.mediaSource);
        sourceUrl = this.blobUrl;
      } else {
        this.fetchAbort = new this.environment.AbortController();
        const fetchTimer = this.environment.setTimeout(() => this.fetchAbort?.abort(), 6000);
        try {
          const response = await this.environment.fetch(asset.url, { cache: "force-cache", signal: this.fetchAbort.signal });
          if (!response.ok) throw new Error("demo-asset-unavailable");
          const blob = await response.blob();
          if (this.destroyed) throw new Error("Replacement cancelled");
          if (!blob.size || blob.size > 5 * 1024 * 1024) throw new Error("demo-asset-size-invalid");
          this.blobUrl = this.environment.URL.createObjectURL(blob);
          sourceUrl = this.blobUrl;
        } finally { this.environment.clearTimeout(fetchTimer); this.fetchAbort = null; }
      }
      if (this.destroyed) throw new Error("Replacement cancelled");
      const ready = new Promise((resolve, reject) => {
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
        const onError = () => { cleanup(); reject(new Error("replacement-media-error")); };
        const timer = this.environment.setTimeout(() => { cleanup(); reject(new Error("replacement-load-timeout")); }, 10000);
        this.cancelLoad = () => { cleanup(); reject(new Error("Replacement cancelled")); };
        for (const event of ["loadedmetadata", "canplay"]) this.audio.addEventListener(event, onReady);
        this.audio.addEventListener("error", onError);
        this.audio.src = sourceUrl;
        this.audio.load();
        onReady();
      });
      if (this.mediaSource) {
        this.streamTask = this.pumpRemote(asset).catch((error) => {
          if (this.destroyed) return;
          const permitted = ["remote-stream-network", "remote-stream-http", "remote-stream-format",
            "remote-stream-range", "remote-stream-timeout", "remote-buffer-error", "remote-buffer-timeout"];
          const reason = permitted.includes(error?.message) ? error.message : "remote-stream-error";
          this.onFatal(reason);
        });
      }
      await ready;
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
      this.streamTask = null;
      this.sourceBuffer = null;
      this.mediaSource = null;
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
