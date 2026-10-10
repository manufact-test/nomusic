(function registerReplacementController(root) {
  "use strict";
  const KEY = "__CELIKOM_REPLACEMENT_CONTROLLER_V1__";
  if (root[KEY]) return;
  class ReplacementController {
    constructor(bridge, environment, options = {}) {
      // Registration can precede dependencies during recovery injection. Resolve
      // them at construction, never capture an absent value in an immutable registry.
      const core = root.__CELIKOM_PLAYER_CORE_V1__;
      const ReplacementPlayer = root.__CELIKOM_REPLACEMENT_PLAYER_V1__?.ReplacementPlayer;
      const SyncEngine = root.__CELIKOM_SYNC_ENGINE_V1__?.SyncEngine;
      const FailOpenController = root.__CELIKOM_FAIL_OPEN_V1__?.FailOpenController;
      if (typeof core?.normalizeTrackId !== "function" || !ReplacementPlayer || !SyncEngine || !FailOpenController) {
        throw new Error("Playback runtime dependencies are not ready");
      }
      this.core = core;
      this.SyncEngine = SyncEngine;
      this.bridge = bridge;
      this.environment = environment;
      this.log = options.log || (() => {});
      this.createPlayer = options.createPlayer || ((onFatal) => new ReplacementPlayer(environment, onFatal));
      this.resolveAsset = options.resolveAsset || null;
      this.onEvent = options.onEvent || (() => {});
      this.negativeResolution = null;
      this.failOpen = new FailOpenController(bridge, this.log);
      this.enabled = false;
      this.testTrackId = null;
      this.snapshot = null;
      this.operation = null;
      this.generation = 0;
      this.phase = "IDLE";
      this.manualBypass = null;
      this.blockedTrackId = null;
      this.restorePending = null;
      this.destroyed = false;
      this.driftMs = null;
      this.lastError = null;
      this.activationCount = 0;
      this.restoreCount = 0;
      this.lastRestore = null;
    }
    configure(enabled, testTrackId, explicitStart = false) {
      const id = this.core.normalizeTrackId(testTrackId);
      const changed = this.testTrackId !== id || this.enabled !== enabled;
      this.enabled = enabled;
      this.testTrackId = id;
      if (changed || explicitStart) { this.manualBypass = null; this.blockedTrackId = null; this.lastError = null; this.negativeResolution = null; }
      this.reconcile();
    }
    eligible(snapshot = this.snapshot, minimumReadyState = 2) {
      const track = snapshot?.track;
      const player = snapshot?.player;
      const exactRoute = this.testTrackId ? track?.id === this.testTrackId : Boolean(this.resolveAsset && this.core.normalizeTrackId(track?.id));
      return this.enabled && this.bridge.isHealthy() && exactRoute && !track?.ambiguous
        && track?.confidence >= 100 && player && !player.ended && player.readyState >= minimumReadyState
        && Number.isFinite(player.duration) && player.duration > 0
        && Math.abs(player.duration * 1000 - track.metadata?.durationMs) <= 1500
        && this.manualBypass?.trackId !== track.id && this.blockedTrackId !== track.id;
    }
    update(snapshot, eventType = "snapshot") {
      if (!snapshot || this.destroyed) return;
      if (this.snapshot && snapshot.observedAt < this.snapshot.observedAt) return;
      const previousId = this.snapshot?.track?.id;
      this.snapshot = snapshot;
      const id = snapshot.track?.id;
      if (id && ((previousId && id !== previousId) || (this.manualBypass && id !== this.manualBypass.trackId) || (this.blockedTrackId && id !== this.blockedTrackId))) { this.manualBypass = null; this.blockedTrackId = null; this.lastError = null; }
      if (["ERROR", "ENDED"].includes(eventType)) { this.abort(`master-${eventType.toLowerCase()}`, true); return; }
      this.reconcile(["SEEK", "PLAY", "RATE_CHANGED"].includes(eventType));
    }
    current(operation) { return !this.destroyed && this.operation === operation && this.generation === operation.generation; }
    event(name, properties) {
      try { Promise.resolve(this.onEvent(name, properties)).catch(() => undefined); }
      catch (_error) { /* best-effort telemetry is not a playback dependency */ }
    }
    reconcile(forceSync = false) {
      if (this.destroyed || this.restorePending) return;
      const operation = this.operation;
      const matching = operation && operation.trackId === this.snapshot?.track?.id && operation.mediaId === this.snapshot?.player?.mediaId;
      // A bound, already guarded master can temporarily have only metadata while
      // seeking/buffering. Keep the lease and pause replacement; admission still
      // requires current data, and emptied/changed/ambiguous masters fail open.
      const minimumReadyState = this.phase === "REPLACEMENT_ACTIVE" && matching ? 1 : 2;
      if (!this.eligible(this.snapshot, minimumReadyState) || (operation && !matching)) {
        if (operation) this.abort("state-changed");
        return;
      }
      if (!operation) {
        if (this.negativeResolution?.trackId === this.snapshot.track.id && this.negativeResolution.until > Date.now()) return;
        void this.prepare(); return;
      }
      if (this.phase === "REPLACEMENT_ACTIVE") {
        try { this.driftMs = operation.sync.sync(operation.player, this.snapshot, forceSync); }
        catch (error) { this.abort(error.message, true); }
      }
    }
    async prepare() {
      const snapshot = this.snapshot;
      const operation = { generation: ++this.generation, token: `${this.bridge.sessionId}:${this.generation}`, trackId: snapshot.track.id, mediaId: snapshot.player.mediaId, sync: new this.SyncEngine(), player: null };
      this.operation = operation;
      this.phase = "PREPARING";
      this.log(`PREPARING · ${operation.trackId}`);
      try {
        operation.asset = this.testTrackId
          ? { found: true, url: this.environment.chrome.runtime.getURL("assets/test-audio.mp3"), demoLoop: true }
          : await this.resolveAsset(operation.trackId);
        if (!this.current(operation)) return;
        if (!operation.asset?.found) {
          this.negativeResolution = { trackId: operation.trackId, until: Date.now() + Math.min(60000, Math.max(5000, operation.asset?.retryAfterMs || 15000)) };
          this.operation = null; this.phase = "IDLE"; return;
        }
        if (!operation.asset.demoLoop && (!Number.isFinite(operation.asset.durationMs)
          || Math.abs(operation.asset.durationMs - snapshot.track.metadata.durationMs) > 1500 || operation.asset.expiresAt <= Date.now())) {
          throw new Error("replacement_duration_or_token_invalid");
        }
        if (!operation.asset.demoLoop) this.event("replacement_available", { service: "yandex" });
        operation.player = this.createPlayer((reason) => { if (this.current(operation)) this.abort(reason, true); });
        await operation.player.prepare(operation.asset);
        if (!operation.asset.demoLoop && Math.abs(operation.player.audio.duration * 1000 - operation.asset.durationMs) > 1500) throw new Error("replacement_duration_mismatch");
        if (!this.current(operation)) return;
        this.update(await this.bridge.getSnapshot());
        if (!this.current(operation) || !this.eligible()) return;
        const guard = await this.bridge.request("GUARD_ENGAGE", { token: operation.token, trackId: operation.trackId, mediaId: operation.mediaId });
        if (!this.current(operation)) { this.bridge.post("RELEASE_NOW", { token: operation.token }); return; }
        this.update(guard.snapshot);
        if (!this.current(operation) || !this.eligible()) { this.abort("guard-state-changed"); return; }
        this.phase = "REPLACEMENT_ACTIVE";
        this.activationCount++;
        if (!operation.asset.demoLoop) this.event("replacement_started", { service: "yandex" });
        this.lastError = null;
        this.log(`REPLACEMENT_ACTIVE · ${operation.trackId}`);
        this.reconcile(true);
      } catch (error) { if (this.current(operation)) this.abort(error.message, true); }
    }
    abort(reason, blockTrack = false, detail = null) {
      const operation = this.operation;
      if (blockTrack) { this.blockedTrackId = operation?.trackId || this.snapshot?.track?.id; this.lastError = reason; }
      if (!operation) return;
      const completed = reason === "master-ended" || detail?.reason === "master-ended";
      if (operation.asset && !operation.asset.demoLoop && completed) this.event("replacement_completed", { service: "yandex" });
      else if (operation.asset && !operation.asset.demoLoop && !["manual-original", "state-changed", "controller-destroyed"].includes(reason)) this.event("fail_open", { service: "yandex", error_code: reason === "api_unavailable" ? "api_unavailable" : reason.startsWith("guard-lost:") ? "binding_changed" : "unknown" });
      this.restoreCount++;
      this.lastRestore = {
        reason, detail, requestedAt: Date.now(), trackId: operation.trackId, mediaId: operation.mediaId,
        detectedTrackId: this.snapshot?.track?.id || null, detectedMediaId: this.snapshot?.player?.mediaId || null,
        readyState: this.snapshot?.player?.readyState ?? null, seeking: Boolean(this.snapshot?.player?.seeking),
        snapshotReason: this.snapshot?.reason || null
      };
      ++this.generation;
      this.operation = null;
      this.phase = "RESTORING";
      this.driftMs = null;
      this.log(`RESTORING · ${reason}`);
      const pending = this.failOpen.restore(operation, reason);
      this.restorePending = pending;
      void pending.finally(() => {
        if (this.restorePending !== pending) return;
        this.restorePending = null;
        this.phase = "IDLE";
        this.log("IDLE · original restored/release requested");
        this.reconcile();
      });
    }
    manualRestore() {
      const trackId = this.snapshot?.track?.id || this.operation?.trackId;
      if (trackId) this.manualBypass = { trackId, requestedAt: Date.now() };
      this.abort("manual-original");
    }
    tick() {
      if (!this.bridge.isHealthy() && this.operation) { this.abort("bridge-unhealthy", true); return; }
      if (this.operation?.asset && !this.operation.asset.demoLoop && this.operation.asset.expiresAt <= Date.now()) { this.abort("audio-token-expired", true); return; }
      if (this.operation && this.snapshot.player.readyState >= 3 && !this.snapshot.player.paused && !this.snapshot.player.seeking
        && Date.now() - this.snapshot.observedAt > 3000 && !this.environment.document.hidden) {
        this.abort("snapshot-stale", true); return;
      }
      this.reconcile();
    }
    destroy() { this.destroyed = true; this.abort("controller-destroyed"); }
  }
  Object.defineProperty(root, KEY, { value: Object.freeze({ ReplacementController }), writable: false });
})(globalThis);
