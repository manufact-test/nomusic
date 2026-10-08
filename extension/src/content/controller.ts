(function startCelikomController(root) {
  "use strict";

  const bridgeFactory = root.__CELIKOM_PLAYER_BRIDGE_V1__;
  if (!bridgeFactory) return;

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
      this.onRuntimeMessage = this.onRuntimeMessage.bind(this);
      this.onStorageChanged = this.onStorageChanged.bind(this);
    }

    log(message) {
      this.logs.push(`${new Date().toISOString()} ${String(message)}`);
      this.logs = this.logs.slice(-40);
    }

    async start() {
      // Expose diagnostics even if storage or bridge initialization fails.
      chrome.runtime.onMessage.addListener(this.onRuntimeMessage);
      chrome.storage.onChanged.addListener(this.onStorageChanged);
      const stored = await chrome.storage.local.get("enabled");
      this.enabled = stored.enabled === true;
      this.bridge.on("READY", () => {
        this.log("MAIN-world bridge ready");
        this.bridge.getSnapshot()
          .then((snapshot) => this.handleSnapshot(snapshot, "request"))
          .catch((error) => this.log(error.message));
      });
      this.bridge.on("PLAYER_SNAPSHOT", (snapshot) => this.handleSnapshot(snapshot, "snapshot"));
      this.bridge.on("PLAYER_EVENT", (event) => {
        this.lastEvent = event?.type || "UNKNOWN";
        if (event?.snapshot) this.snapshot = event.snapshot;
      });
      this.bridge.on("BRIDGE_TIMEOUT", (payload) => {
        this.log(`bridge timeout · ${Math.round(payload?.elapsedMs || 0)} ms`);
      });
      this.bridge.start();
      root.addEventListener("pagehide", () => this.destroy(), { once: true });
      this.markDocument();
      this.log("Stage 2 controller started");
    }

    markDocument() {
      if (document.documentElement) document.documentElement.dataset.celikomController = "player-integration-v1";
      else document.addEventListener("DOMContentLoaded", () => this.markDocument(), { once: true });
    }

    handleSnapshot(snapshot, source) {
      if (!snapshot || this.destroyed) return;
      this.snapshot = snapshot;
      this.lastEvent = source;
    }

    onStorageChanged(changes, areaName) {
      if (areaName !== "local" || !("enabled" in changes)) return;
      this.enabled = changes.enabled.newValue === true;
      this.log(this.enabled ? "CELIKOM started" : "CELIKOM stopped");
    }

    onRuntimeMessage(message, _sender, sendResponse) {
      const type = message && typeof message === "object" ? message.type : null;
      if (type === COMMANDS.getControllerStatus || type === COMMANDS.controllerPing) {
        sendResponse({ ok: true, status: this.getDiagnostics() });
        return false;
      }
      if (type === COMMANDS.restoreOriginal) {
        this.lastEvent = "ORIGINAL_CONFIRMED";
        this.log("original audio confirmed");
        sendResponse({ ok: true, stage: 2 });
        return false;
      }
      return false;
    }

    getPhase() {
      if (!this.enabled) return "STOPPED";
      if (this.startupError) return "ERROR";
      if (!this.bridge.ready) return "CONNECTING";
      if (this.snapshot?.track?.id && this.snapshot?.player) return "READY";
      return "OBSERVING";
    }

    getDiagnostics() {
      return {
        celikomVersion: chrome.runtime.getManifest().version,
        stage: 2,
        enabled: this.enabled,
        phase: this.getPhase(),
        startupError: this.startupError,
        track: this.snapshot?.track || null,
        player: this.snapshot?.player || null,
        mediaCandidates: this.snapshot?.mediaCandidates || [],
        bridge: {
          ready: this.bridge.ready,
          healthy: this.bridge.isHealthy(),
          lastSeenAt: this.bridge.lastSeenAt || null,
          protocolVersion: 1
        },
        lastEvent: this.lastEvent,
        page: `${location.origin}${location.pathname}`,
        recentLog: this.logs.slice(-20)
      };
    }

    wake() {
      if (!this.destroyed) {
        this.bridge.connect();
        void chrome.storage.local.get("enabled").then((stored) => {
          this.enabled = stored.enabled === true;
        }).catch((error) => this.log(`settings failed: ${error.message}`));
      }
    }

    destroy() {
      if (this.destroyed) return;
      this.destroyed = true;
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
