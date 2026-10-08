(function startCelikomController(root) {
  "use strict";

  const bridgeFactory = root.__CELIKOM_PLAYER_BRIDGE_V1__;
  const engineFactory = root.__CELIKOM_REPLACEMENT_CONTROLLER_V1__;
  if (!bridgeFactory || !engineFactory) return;

  const CONTROLLER_KEY = "__CELIKOM_CONTENT_CONTROLLER_V2__";
  if (root[CONTROLLER_KEY]) {
    root[CONTROLLER_KEY].wake();
    return;
  }

  const COMMANDS = Object.freeze({
    getControllerStatus: "CELIKOM_CONTROLLER_STATUS_GET",
    restoreOriginal: "CELIKOM_RESTORE_ORIGINAL",
    controllerPing: "CELIKOM_CONTROLLER_PING"
  });

  class CelikomController {
    constructor() {
      this.bridge = bridgeFactory.createPlayerBridge(root);
      this.enabled = false;
      this.snapshot = null;
      this.lastEvent = "startup";
      this.logs = [];
      this.destroyed = false;
      this.startupError = null;
      this.mainVersion = null;
      this.testTrackId = "";
      this.apiConfigured = null;
      this.engine = new engineFactory.ReplacementController(this.bridge, root, {
        log: (message) => this.log(message),
        onEvent: (name, properties) => this.event(name, properties),
        resolveAsset: async (trackId) => {
          const response = await chrome.runtime.sendMessage({ type: "CELIKOM_API_RESOLVE", service: "yandex", trackId });
          this.apiConfigured = response?.configured ?? this.apiConfigured;
          if (!response?.ok) {
            const permitted = ["api_access_missing", "api_access_denied", "api_forbidden", "api_network_error",
              "api_server_error", "api_http_error", "invalid_api_response", "invalid_audio_url",
              "invalid_api_config", "extension_update_required", "invalid_api_sender"];
            throw new Error(permitted.includes(response?.error) ? response.error : "api_unavailable");
          }
          return response.asset;
        }
      });
      this.syncTimer = null;
      this.onRuntimeMessage = this.onRuntimeMessage.bind(this);
      this.onStorageChanged = this.onStorageChanged.bind(this);
    }

    log(message) {
      this.logs.push(`${new Date().toISOString()} ${String(message)}`);
      this.logs = this.logs.slice(-40);
    }

    event(name, properties = {}) {
      try { void chrome.runtime.sendMessage({ type: "CELIKOM_API_EVENT", name, properties }).catch(() => undefined); }
      catch (_error) { /* telemetry must never interfere with playback */ }
    }

    async start() {
      // Expose diagnostics even if storage or bridge initialization fails.
      chrome.runtime.onMessage.addListener(this.onRuntimeMessage);
      chrome.storage.onChanged.addListener(this.onStorageChanged);
      const stored = await chrome.storage.local.get(["enabled", "testTrackId"]);
      this.enabled = stored.enabled === true;
      this.testTrackId = stored.testTrackId || "";
      this.engine.configure(this.enabled, this.testTrackId);
      this.bridge.on("READY", (payload) => {
        this.mainVersion = payload?.bridgeVersion || null;
        this.log("MAIN-world bridge ready");
        this.bridge.getSnapshot()
          .then((snapshot) => this.handleSnapshot(snapshot, "request"))
          .catch((error) => this.log(error.message));
      });
      this.bridge.on("PLAYER_SNAPSHOT", (snapshot) => this.handleSnapshot(snapshot, "snapshot"));
      this.bridge.on("PLAYER_EVENT", (event) => {
        this.lastEvent = event?.type || "UNKNOWN";
        if (event?.snapshot && (!this.snapshot || event.snapshot.observedAt >= this.snapshot.observedAt)) { this.snapshot = event.snapshot; this.engine.update(event.snapshot, event.type); }
      });
      this.bridge.on("GUARD_RELEASED", (event) => {
        if (event.token === this.engine.operation?.token) this.engine.abort(`guard-lost:${event.reason}`, event.reason !== "master-binding-changed" || event.detail?.reason === "media-source-changed", event.detail);
      });
      this.bridge.on("BRIDGE_TIMEOUT", (payload) => {
        this.log(`bridge timeout · ${Math.round(payload?.elapsedMs || 0)} ms`);
        this.engine.abort("bridge-timeout", true);
      });
      this.bridge.start();
      this.syncTimer = root.setInterval(() => {
        try { this.engine.tick(); } catch (error) { this.engine.abort(`sync-error:${error.message}`, true); }
      }, 500);
      root.addEventListener("pagehide", () => this.destroy(), { once: true });
      this.markDocument();
      this.log("Stage 4 controller started");
    }

    markDocument() {
      if (document.documentElement) document.documentElement.dataset.celikomController = "player-integration-v1";
      else document.addEventListener("DOMContentLoaded", () => this.markDocument(), { once: true });
    }

    handleSnapshot(snapshot, source) {
      if (!snapshot || this.destroyed) return;
      if (this.snapshot && snapshot.observedAt < this.snapshot.observedAt) return;
      this.snapshot = snapshot;
      this.lastEvent = source;
      this.engine.update(snapshot);
    }

    onStorageChanged(changes, areaName) {
      if (areaName !== "local") return;
      if ("enabled" in changes) { this.enabled = changes.enabled.newValue === true; this.log(this.enabled ? "CELIKOM started" : "CELIKOM stopped"); this.event(this.enabled ? "celikom_started" : "celikom_stopped"); }
      if ("testTrackId" in changes) this.testTrackId = changes.testTrackId.newValue || "";
      if (this.startupError) return;
      this.engine.configure(this.enabled, this.testTrackId);
    }

    onRuntimeMessage(message, _sender, sendResponse) {
      const type = message && typeof message === "object" ? message.type : null;
      if (type === COMMANDS.getControllerStatus || type === COMMANDS.controllerPing) {
        sendResponse({ ok: true, status: this.getDiagnostics() });
        return false;
      }
      if (type === COMMANDS.restoreOriginal) {
        this.lastEvent = "ORIGINAL_RESTORED";
        this.engine.manualRestore();
        this.event("manual_original");
        sendResponse({ ok: true, stage: 3 });
        return false;
      }
      if (type === "CELIKOM_ADD_TRACK_OPENED") { this.event("add_track_opened"); sendResponse({ ok: true }); return false; }
      if (type === "CELIKOM_REPLACEMENT_RETRY") {
        if (this.startupError) { sendResponse({ ok: false, error: this.startupError }); return false; }
        this.engine.configure(this.enabled, this.testTrackId, true);
        sendResponse({ ok: true });
        return false;
      }
      return false;
    }

    getPhase() {
      if (!this.enabled) return "STOPPED";
      if (this.startupError) return "ERROR";
      if (!this.bridge.ready) return "CONNECTING";
      if (this.engine.phase !== "IDLE") return this.engine.phase;
      if (this.snapshot?.track?.id && this.snapshot?.player) return "READY";
      return "OBSERVING";
    }

    getDiagnostics() {
      return {
        celikomVersion: chrome.runtime.getManifest().version,
        buildVersion: root.__CELIKOM_PLAYER_CORE_V1__?.VERSION || null,
        stage: 4,
        enabled: this.enabled,
        phase: this.getPhase(),
        startupError: this.startupError,
        settings: { enabled: this.enabled, testTrackId: this.testTrackId, driftThresholdMs: 350 },
        active: this.engine.operation ? { generation: this.engine.operation.generation, trackId: this.engine.operation.trackId, mediaId: this.engine.operation.mediaId } : null,
        manualBypass: this.engine.manualBypass,
        replacementError: this.engine.lastError,
        guardActive: Boolean(this.snapshot?.guard?.active),
        driftMs: this.engine.driftMs,
        playback: { activationCount: this.engine.activationCount, restoreCount: this.engine.restoreCount, lastRestore: this.engine.lastRestore },
        api: { configured: this.apiConfigured, mode: this.testTrackId ? "synthetic-demo" : "remote", replacementId: this.engine.operation?.asset?.replacementId || null },
        track: this.snapshot?.track || null,
        player: this.snapshot?.player || null,
        mediaCandidates: this.snapshot?.mediaCandidates || [],
        bridge: {
          ready: this.bridge.ready,
          healthy: this.bridge.isHealthy(),
          lastSeenAt: this.bridge.lastSeenAt || null,
          protocolVersion: 1,
          bridgeVersion: this.mainVersion
        },
        lastEvent: this.lastEvent,
        page: `${location.origin}${location.pathname}`,
        recentLog: this.logs.slice(-20)
      };
    }

    wake() {
      if (!this.destroyed && !this.startupError) {
        this.bridge.connect();
        void chrome.storage.local.get(["enabled", "testTrackId"]).then((stored) => {
          this.enabled = stored.enabled === true;
          this.testTrackId = stored.testTrackId || "";
          this.engine.configure(this.enabled, this.testTrackId);
        }).catch((error) => this.log(`settings failed: ${error.message}`));
      }
    }

    destroy() {
      if (this.destroyed) return;
      this.destroyed = true;
      this.engine.destroy();
      root.clearInterval(this.syncTimer);
      chrome.runtime.onMessage.removeListener(this.onRuntimeMessage);
      chrome.storage.onChanged.removeListener(this.onStorageChanged);
      this.bridge.destroy();
    }
  }

  const controller = new CelikomController();
  Object.defineProperty(root, CONTROLLER_KEY, {
    value: controller,
    configurable: false,
    enumerable: false,
    writable: false
  });
  controller.start().catch((error) => {
    controller.startupError = String(error?.message || error);
    controller.log(`startup failed: ${controller.startupError}`);
  });
})(globalThis);
