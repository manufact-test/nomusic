(function (root) {
  "use strict";
  const channel = "CELIKOM_NATIVE_EXPERIMENT_V1";
  class NativeController {
    constructor(bridge, environment, options = {}) {
      this.bridge = bridge; this.environment = environment; this.resolveAsset = options.resolveAsset;
      this.log = options.log || (() => {}); this.enabled = false; this.suspended = false; this.destroyed = false;
      this.phase = "IDLE"; this.operation = null; this.manualBypass = null; this.negativeResolution = null;
      this.lastError = null; this.retryBlock = null; this.driftMs = null; this.activationCount = 0;
      this.restoreCount = 0; this.lastRestore = null; this.startupHistory = []; this.policyRevision = 0;
      this.pending = new Map(); this.sequence = 0; this.control = Promise.resolve(); this.busy = false;
      this.snapshot = null; this.latest = null; this.revision = 0; this.readyRevision = -1;
      this.onMessage = event => {
        const message = event.data;
        if (event.source !== root || message?.channel !== channel || message.direction !== "response" || message.sessionId !== bridge.sessionId) return;
        const pending = this.pending.get(message.requestId); if (!pending) return;
        this.pending.delete(message.requestId); root.clearTimeout(pending.timer);
        if (message.payload?.ok) pending.resolve(message.payload.result); else pending.reject(Error(message.payload?.error || "native_failed"));
      };
      root.addEventListener("message", this.onMessage);
      this.coordinator = root.__CELIKOM_NATIVE_DESKTOP_ADAPTER__.createDesktopPrefetch({
        engine: this, environment, mp3DurationMs: root.__CELIKOM_NATIVE_MP3_DURATION__,
        publish: message => this.rpc("publish", message), revoke: message => this.rpc("revoke", message)
      });
    }
    rpc(type, payload = {}) {
      if (this.destroyed && type !== "configure") return Promise.reject(Error("native_controller_destroyed"));
      const requestId = `${this.bridge.sessionId}:native:${++this.sequence}`;
      return new Promise((resolve, reject) => {
        const timer = root.setTimeout(() => { this.pending.delete(requestId); reject(Error("native_command_timeout")); }, 20000);
        this.pending.set(requestId, { resolve, reject, timer });
        root.postMessage({ channel, direction: "request", sessionId: this.bridge.sessionId, requestId, type, payload }, "*");
      });
    }
    publishPolicy() {
      /* Disable ALL legacy muting/intro admission. No second playback owner. */
      this.bridge.post("POLICY_UPDATE", { revision: ++this.policyRevision, enabled: false, holdIntro: false, reset: true });
    }
    configure(enabled, testTrackId, explicit = false) {
      const changed = this.enabled !== (enabled === true) || this.testTrackId !== (testTrackId || "");
      this.enabled = enabled === true; this.testTrackId = testTrackId || ""; this.publishPolicy();
      if (!changed && !explicit) return;
      this.manualBypass = null; this.lastError = null; this.reset();
    }
    reset() {
      const revision = ++this.revision; this.readyRevision = -1; this.operation = null;
      this.phase = "IDLE";
      this.control = this.control.catch(() => {}).then(async () => {
        await this.coordinator.stop();
        if (revision !== this.revision || this.destroyed) return;
        const allow = this.enabled && !this.suspended && !this.testTrackId;
        if (allow) await this.coordinator.configure(true);
        await this.rpc("configure", { enabled: allow, generation: this.coordinator.generation });
        if (revision === this.revision) this.readyRevision = revision;
      }).catch(error => { if (revision === this.revision) this.lastError = String(error.message); });
    }
    suspendAccess(value, reason) {
      if (this.suspended === value) return;
      this.suspended = value; this.publishPolicy(); this.reset();
      if (value) this.lastError = reason;
    }
    update(snapshot, event) {
      this.snapshot = snapshot;
      if (event === "ERROR") this.abort("native_media_error");
      else if (this.operation && snapshot?.track?.confidence >= 100 && !snapshot.track.ambiguous
        && snapshot.track.id && snapshot.track.id !== this.operation.trackId) this.reset();
    }
    tick() {
      if (this.busy || this.destroyed || !this.bridge.isHealthy()) return;
      this.busy = true;
      void this.poll().catch(error => {
        this.lastError = String(error.message || "native_failed"); this.abort(this.lastError);
      }).finally(() => { this.busy = false; });
    }
    async poll() {
      const revision = this.revision;
      if (this.readyRevision !== revision || !this.enabled || this.suspended || this.testTrackId) return;
      const state = await this.rpc("inspect"); this.latest = state;
      if (revision !== this.revision || !state.found || state.pending) return;
      const id = state.trackId;
      if (this.operation && this.operation.trackId !== id) { this.reset(); return; }
      if (this.manualBypass && this.manualBypass.trackId !== id) this.manualBypass = null;
      if (this.manualBypass?.trackId === id) return;
      if (this.negativeResolution?.trackId === id && this.negativeResolution.until > Date.now()) return;
      if (state.sourceMismatch) throw Error("native_source_identity_mismatch");
      if (state.activeTrackId === id) {
        this.phase = "REPLACEMENT_ACTIVE";
        return;
      }
      if (this.operation?.trackId === id && this.phase === "REPLACEMENT_ACTIVE") throw Error("native_source_lost");
      this.operation = { trackId: id, generation: revision, stage: "resolving", startedAt: Date.now() };
      this.operation.player = { diagnostics: () => ({ backend: "native-experiment-001", engine: this.latest, prefetch: this.coordinator.diagnostics() }) };
      this.phase = "PREPARING";
      const record = await this.coordinator.request({ id, durationMs: state.durationMs });
      if (revision !== this.revision) return;
      if (!record) {
        this.operation = null; this.phase = "IDLE";
        this.negativeResolution = { trackId: id, until: Date.now() + 15000 };
        this.lastError = this.coordinator.lastError; return;
      }
      this.operation.stage = "admitting";
      const admitted = await this.coordinator.admit(id);
      if (revision !== this.revision) return;
      if (!admitted) throw Error("native_admission_denied");
      const current = await this.rpc("inspect");
      if (revision !== this.revision || current.trackId !== id) { this.operation = null; this.phase = "IDLE"; return; }
      this.operation.stage = "switching";
      await this.rpc("activate", { trackId: id, generation: this.coordinator.generation });
      if (revision !== this.revision) return;
      this.operation.asset = { found: true, ...record }; this.phase = "REPLACEMENT_ACTIVE"; this.lastError = null;
      this.activationCount++; this.negativeResolution = null;
      this.startupHistory.push({ trackId: id, native: true, elapsedMs: Date.now() - this.operation.startedAt });
      this.startupHistory = this.startupHistory.slice(-12); this.log(`Native source active · ${id}`);
    }
    abort(reason) {
      this.lastError = reason; this.manualBypass = { trackId: this.latest?.trackId || this.snapshot?.track?.id };
      this.restoreCount++; this.lastRestore = { reason, at: Date.now() }; this.reset();
    }
    manualRestore() { this.abort("manual-original"); }
    releaseIntroWait() { return false; }
    canRecoverConnection() { return false; }
    recoverConnection() { this.manualBypass = null; this.lastError = null; this.reset(); }
    destroy() {
      if (this.destroyed) return;
      this.enabled = false; this.revision++; this.publishPolicy();
      void this.coordinator.stop().catch(() => {});
      void this.rpc("configure", { enabled: false, generation: this.coordinator.generation }).catch(() => {});
      this.destroyed = true;
      root.removeEventListener("message", this.onMessage);
      for (const item of this.pending.values()) { root.clearTimeout(item.timer); item.reject(Error("native_controller_destroyed")); }
      this.pending.clear();
    }
  }
  Object.defineProperty(root, "__CELIKOM_REPLACEMENT_CONTROLLER_V1__", { value: { ReplacementController: NativeController }, configurable: false });
})(globalThis);
