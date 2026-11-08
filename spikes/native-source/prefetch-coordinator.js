(function (root) {
  "use strict";
  if (root.__CELIKOM_NATIVE_PREFETCH__) return;
  class PrefetchCoordinator {
    constructor(options) {
      this.resolve = options.resolve;
      this.download = options.download;
      this.inspectDuration = options.inspectDuration;
      this.publish = options.publish;
      this.revoke = options.revoke;
      this.now = options.now || Date.now;
      this.ready = new Map(); this.pending = new Map(); this.negative = new Map();
      this.generation = 0; this.enabled = false; this.suspended = false;
      this.lastError = null;
      this.resetPending = Promise.resolve();
    }
    async configure(enabled, suspended = false) {
      const allow = enabled === true && suspended !== true;
      if (this.enabled === (enabled === true) && this.suspended === (suspended === true)) return;
      this.enabled = enabled === true; this.suspended = suspended === true;
      const previousGeneration = this.generation++;
      for (const task of this.pending.values()) task.abort.abort();
      this.pending.clear(); this.negative.clear(); this.ready.clear();
      this.resetPending = this.resetPending.then(() => this.revoke({ reason: allow ? "session-reset" : "authority-lost", generation: previousGeneration }));
      await this.resetPending;
    }
    allowed() { return this.enabled && !this.suspended; }
    async request(track) {
      const id = String(track?.id || "");
      if (!/^\d{1,24}$/.test(id) || !Number.isFinite(track?.durationMs) || track.durationMs <= 0 || !this.allowed()) return null;
      const cached = this.ready.get(id);
      if (cached && cached.expiresAt > this.now() + 1000) return cached;
      if (this.pending.has(id)) return this.pending.get(id).promise;
      if ((this.negative.get(id) || 0) > this.now() || this.pending.size >= 1 || this.ready.size >= 2) return null;
      const generation = this.generation, abort = new AbortController();
      const current = () => this.allowed() && this.generation === generation && !abort.signal.aborted;
      const task = { abort };
      task.promise = Promise.resolve().then(async () => {
        await this.resetPending;
        if (!current()) return null;
        /* resolve is the EXISTING isolated/background entitlement broker, never
           an unprivileged page URL or a new account/token implementation. */
        const asset = await this.resolve(id, { fresh: true });
        if (!current()) return null;
        if (!asset?.found) { this.negative.set(id, this.now() + 15000); return null; }
        if (asset.mimeType !== "audio/mpeg" || asset.gainDb !== 0 || !Number.isFinite(asset.durationMs)
          || Math.abs(asset.durationMs - track.durationMs) > 1500 || !Number.isFinite(asset.expiresAt)
          || asset.expiresAt <= this.now() + 1000) throw Error("native_asset_not_supported");
        const blob = await this.download(asset, abort.signal);
        if (!current()) return null;
        if (!blob || blob.type !== "audio/mpeg" || blob.size < 1024 || blob.size > 31457280) throw Error("native_asset_invalid");
        const decodedDuration = await this.inspectDuration(await blob.arrayBuffer());
        if (!current()) return null;
        if (!Number.isFinite(decodedDuration) || Math.abs(decodedDuration - asset.durationMs) > 1500) throw Error("native_duration_mismatch");
        const expiresAt = Math.min(asset.expiresAt, this.now() + 300000);
        if (expiresAt <= this.now() + 1000) throw Error("native_asset_expired");
        /* Only admitted bytes cross into MAIN: no Bearer or signed URL. */
        const message = { trackId: id, blob, durationMs: asset.durationMs, expiresAt, generation };
        await this.publish(message);
        if (!current()) { await this.revoke({ reason: "late-publish", generation, trackId: id }); return null; }
        const record = { trackId: id, expiresAt, durationMs: asset.durationMs, replacementId: asset.replacementId, version: asset.version };
        this.ready.set(id, record); this.lastError = null; return record;
      }).catch(error => {
        if (current()) { this.lastError = String(error?.message || "native_prefetch_failed"); this.negative.set(id, this.now() + 15000); }
        return null;
      }).finally(() => { if (this.pending.get(id) === task) this.pending.delete(id); });
      this.pending.set(id, task); return task.promise;
    }
    async admit(id) {
      id = String(id);
      const record = this.ready.get(id), generation = this.generation;
      if (!this.allowed() || !record) return null;
      try {
        const asset = await this.resolve(id, { fresh: true });
        if (!this.allowed() || generation !== this.generation) return null;
        if (!asset?.found || !Number.isFinite(asset.durationMs) || asset.replacementId !== record.replacementId || asset.version !== record.version
          || asset.expiresAt <= this.now() + 1000 || record.expiresAt <= this.now() + 1000 || asset.gainDb !== 0
          || asset.mimeType !== "audio/mpeg" || Math.abs(asset.durationMs - record.durationMs) > 1500) throw Error("native_admission_changed");
        return record;
      } catch (error) {
        if (generation === this.generation) { this.ready.delete(id); this.lastError = String(error?.message || "native_admission_denied"); }
        await this.revoke({ reason: "admission-denied", generation, trackId: id });
        return null;
      }
    }
    async stop() { return this.configure(false, this.suspended); }
    diagnostics() { return { enabled: this.enabled, suspended: this.suspended, generation: this.generation, ready: this.ready.size, pending: this.pending.size, lastError: this.lastError }; }
  }
  Object.defineProperty(root, "__CELIKOM_NATIVE_PREFETCH__", { value: { PrefetchCoordinator }, configurable: true });
})(globalThis);
