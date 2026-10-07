(function startCelikomContentController() {
  "use strict";

  const core = globalThis.__CELIKOM_POC_CORE__;
  const overlayFactory = globalThis.__CELIKOM_POC_OVERLAY__;
  if (!core || !overlayFactory) {
    return;
  }

  const CONTROLLER_KEY = "__CELIKOM_POC_CONTENT_CONTROLLER_V4__";
  if (globalThis[CONTROLLER_KEY]) {
    globalThis[CONTROLLER_KEY].wake?.();
    return;
  }
  const runtime = { controller: null, wake: null };
  Object.defineProperty(globalThis, CONTROLLER_KEY, {
    value: runtime,
    configurable: true,
    enumerable: false,
    writable: false
  });

  const DEFAULT_SETTINGS = Object.freeze({
    enabled: true,
    automaticReplacement: true,
    testTrackId: "",
    driftThresholdMs: 350,
    showOverlay: true
  });

  const PHASE = Object.freeze({
    IDLE: "IDLE",
    PREPARING: "PREPARING",
    ACTIVE: "REPLACEMENT_ACTIVE",
    RESTORING: "RESTORING",
    ERROR: "ERROR_RECOVERY"
  });

  function delay(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
  }

  async function waitForDocumentElement() {
    for (let attempt = 0; attempt < 50; attempt += 1) {
      if (document.documentElement) return;
      await delay(20);
    }
    throw new Error("Document root is unavailable");
  }

  class MainBridgeClient {
    constructor() {
      this.sessionId = core.createSessionId();
      this.ready = false;
      this.lastSeenAt = 0;
      this.requestSequence = 0;
      this.pending = new Map();
      this.listeners = new Map();
      this.onMessage = this.onMessage.bind(this);
      window.addEventListener("message", this.onMessage);
    }

    on(type, listener) {
      const listeners = this.listeners.get(type) || new Set();
      listeners.add(listener);
      this.listeners.set(type, listeners);
      return () => listeners.delete(listener);
    }

    emit(type, payload) {
      for (const listener of this.listeners.get(type) || []) {
        try {
          listener(payload);
        } catch (_error) {
          // A diagnostic listener must never break the playback controller.
        }
      }
    }

    post(type, payload = {}, requestId = null) {
      window.postMessage({
        channel: core.CHANNEL,
        direction: "to-main",
        sessionId: this.sessionId,
        type,
        requestId,
        payload,
        sentAt: Date.now()
      }, "*");
    }

    connect() {
      this.post("INIT", { contentVersion: core.VERSION });
    }

    isHealthy() {
      const timeoutMs = document.hidden ? 150000 : 15000;
      return this.ready && Date.now() - this.lastSeenAt <= timeoutMs;
    }

    heartbeat() {
      if (!this.isHealthy()) {
        this.ready = false;
        this.connect();
        return;
      }
      this.post("HEARTBEAT");
    }

    async request(type, payload = {}, timeoutMs = 1800) {
      if (!this.isHealthy()) {
        this.ready = false;
        this.connect();
      }
      this.requestSequence += 1;
      const requestId = `${this.sessionId}:${this.requestSequence}`;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          this.pending.delete(requestId);
          reject(new Error(`Bridge request timed out: ${type}`));
        }, timeoutMs);
        this.pending.set(requestId, { resolve, reject, timer, type });
        this.post("REQUEST", { type, payload }, requestId);
      });
    }

    onMessage(event) {
      if (event.source !== window) return;
      const message = event.data;
      if (!message || message.channel !== core.CHANNEL || message.direction !== "from-main") return;

      if (message.type === "BRIDGE_PRESENT") {
        this.connect();
        return;
      }
      if (message.sessionId !== this.sessionId) return;
      this.lastSeenAt = Date.now();

      if (message.type === "READY" || message.type === "HEARTBEAT_ACK") {
        this.ready = true;
      }

      if (message.type === "BRIDGE_TIMEOUT") {
        this.ready = false;
        this.emit(message.type, message.payload);
        this.connect();
        return;
      }

      if (message.type === "RESPONSE" && typeof message.requestId === "string") {
        const pending = this.pending.get(message.requestId);
        if (!pending) return;
        clearTimeout(pending.timer);
        this.pending.delete(message.requestId);
        if (message.payload?.ok) {
          pending.resolve(message.payload.result);
        } else {
          pending.reject(new Error(message.payload?.error || `Bridge request failed: ${pending.type}`));
        }
        return;
      }

      this.emit(message.type, message.payload);
    }

    shutdown() {
      this.post("SHUTDOWN");
      this.ready = false;
      window.removeEventListener("message", this.onMessage);
      for (const pending of this.pending.values()) {
        clearTimeout(pending.timer);
        pending.reject(new Error("Bridge shut down"));
      }
      this.pending.clear();
    }
  }

  class ReplacementPlayer {
    constructor(sourceUrl, onFatalError) {
      this.sourceUrl = sourceUrl;
      this.blobUrl = null;
      this.sourcePromise = null;
      this.onFatalError = onFatalError;
      this.audio = document.createElement("audio");
      this.audio.dataset.celikomReplacement = "true";
      this.audio.setAttribute("aria-hidden", "true");
      this.audio.preload = "auto";
      this.audio.controls = false;
      this.audio.style.cssText = "position:fixed!important;width:1px!important;height:1px!important;opacity:0!important;pointer-events:none!important;left:-9999px!important;";
      this.audio.addEventListener("error", () => {
        this.onFatalError?.(new Error(`Replacement media error: ${this.audio.error?.code || "unknown"}`));
      });
      this.ensureAttached();
    }

    ensureAttached() {
      if (!this.audio.isConnected && document.documentElement) {
        document.documentElement.append(this.audio);
      }
    }

    waitUntilReady(timeoutMs = 6000) {
      if (this.audio.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA && Number.isFinite(this.audio.duration)) {
        return Promise.resolve();
      }

      return new Promise((resolve, reject) => {
        const cleanup = () => {
          clearTimeout(timer);
          this.audio.removeEventListener("loadedmetadata", onReady);
          this.audio.removeEventListener("canplay", onReady);
          this.audio.removeEventListener("error", onError);
        };
        const onReady = () => {
          cleanup();
          resolve();
        };
        const onError = () => {
          cleanup();
          reject(new Error("Replacement asset could not be loaded"));
        };
        const timer = setTimeout(() => {
          cleanup();
          reject(new Error("Replacement asset load timed out"));
        }, timeoutMs);
        this.audio.addEventListener("loadedmetadata", onReady, { once: true });
        this.audio.addEventListener("canplay", onReady, { once: true });
        this.audio.addEventListener("error", onError, { once: true });
      });
    }

    async ensureSource() {
      if (this.blobUrl) return this.blobUrl;
      if (!this.sourcePromise) {
        this.sourcePromise = fetch(this.sourceUrl, { cache: "force-cache" })
          .then((response) => {
            if (!response.ok) throw new Error(`Replacement asset returned HTTP ${response.status}`);
            return response.blob();
          })
          .then((blob) => {
            if (!blob.size) throw new Error("Replacement asset is empty");
            this.blobUrl = URL.createObjectURL(blob);
            return this.blobUrl;
          })
          .catch((error) => {
            this.sourcePromise = null;
            throw error;
          });
      }
      return this.sourcePromise;
    }

    async prepareAt(masterTime) {
      this.ensureAttached();
      const playableUrl = await this.ensureSource();
      if (this.audio.src !== playableUrl) {
        this.audio.src = playableUrl;
        this.audio.load();
      }
      await this.waitUntilReady();
      this.seekTo(masterTime);
    }

    seekTo(masterTime) {
      const target = core.safeReplacementTime(masterTime, this.audio.duration);
      if (Math.abs(this.audio.currentTime - target) > 0.02) {
        this.audio.currentTime = target;
      }
      return target;
    }

    applyMasterState(playerState) {
      if (!playerState) return;
      this.audio.volume = core.clamp(playerState.volume, 0, 1);
      this.audio.muted = Boolean(playerState.muted);
      const rate = core.clamp(playerState.playbackRate || 1, 0.25, 4);
      if (Math.abs(this.audio.playbackRate - rate) > 0.001) {
        this.audio.playbackRate = rate;
      }
    }

    async play() {
      this.ensureAttached();
      await this.audio.play();
    }

    pause() {
      this.audio.pause();
    }

    stop() {
      this.audio.pause();
      if (Number.isFinite(this.audio.duration)) {
        try {
          this.audio.currentTime = 0;
        } catch (_error) {
          // The emergency bridge still removes the element if this context dies.
        }
      }
    }

    destroy() {
      this.stop();
      this.audio.removeAttribute("src");
      this.audio.load();
      this.audio.remove();
      if (this.blobUrl) {
        URL.revokeObjectURL(this.blobUrl);
        this.blobUrl = null;
      }
    }
  }

  class CelikomPlaybackController {
    constructor() {
      this.bridge = new MainBridgeClient();
      this.settings = core.sanitizeSettings(DEFAULT_SETTINGS);
      this.phase = PHASE.IDLE;
      this.generation = 0;
      this.snapshot = null;
      this.active = null;
      this.manualBypass = null;
      this.lastEvent = "startup";
      this.driftMs = null;
      this.logs = [];
      this.overlay = null;
      this.heartbeatTimer = null;
      this.reconnectTimer = null;
      this.syncTimer = null;
      this.visibilityHandler = null;
      this.destroyed = false;
      this.replacement = new ReplacementPlayer(
        chrome.runtime.getURL("assets/test-audio.mp3"),
        (error) => this.failOpen(`replacement-error:${error.message}`, true)
      );
    }

    async start() {
      await waitForDocumentElement();
      await this.loadSettings();
      this.overlay = overlayFactory.createOverlay({
        onEmergency: () => this.manualRestore("overlay-emergency"),
        onCopy: () => this.log("diagnostics copied")
      });
      this.overlay.setVisible(this.settings.showOverlay);

      this.bridge.on("READY", () => {
        this.log("MAIN-world bridge ready");
        this.bridge.request("GET_SNAPSHOT").then((snapshot) => this.handleSnapshot(snapshot, "snapshot")).catch((error) => this.log(error.message));
      });
      this.bridge.on("PLAYER_STATE", (snapshot) => this.handleSnapshot(snapshot, "state"));
      this.bridge.on("PLAYER_EVENT", (payload) => this.handlePlayerEvent(payload));
      this.bridge.on("BRIDGE_TIMEOUT", (payload) => {
        this.log(`bridge timeout · ${payload?.hidden ? "hidden" : "visible"} · ${Math.round(payload?.elapsedMs || 0)} ms`);
      });
      this.bridge.on("VOLUME_INTENT", (payload) => {
        if (this.active) {
          this.replacement.applyMasterState({
            ...this.snapshot?.player,
            volume: payload?.volume,
            muted: payload?.muted
          });
        }
      });

      this.bridge.heartbeat();
      this.heartbeatTimer = setInterval(() => this.bridge.heartbeat(), 1000);
      this.reconnectTimer = setInterval(() => {
        if (!this.bridge.isHealthy()) {
          this.bridge.heartbeat();
        }
      }, 2500);
      this.visibilityHandler = () => {
        if (document.hidden) return;
        this.bridge.heartbeat();
      };
      document.addEventListener("visibilitychange", this.visibilityHandler);

      chrome.storage.onChanged.addListener((changes, areaName) => {
        if (areaName === "local" && Object.keys(changes).some((key) => key in DEFAULT_SETTINGS)) {
          this.reloadSettings();
        }
      });

      chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
        if (!message || typeof message.type !== "string") return false;
        if (message.type === "CELIKOM_GET_STATUS" || message.type === "CELIKOM_GET_STATUS_V4") {
          sendResponse({ ok: true, status: this.getDiagnostics() });
          return false;
        }
        if (message.type === "CELIKOM_EMERGENCY_RESTORE") {
          this.manualRestore("runtime-emergency").then(() => sendResponse({ ok: true }));
          return true;
        }
        if (message.type === "CELIKOM_RELOAD_SETTINGS") {
          this.reloadSettings().then(() => sendResponse({ ok: true, settings: this.settings }));
          return true;
        }
        return false;
      });

      window.addEventListener("pagehide", () => this.shutdown(), { once: true });
      this.log("controller started");
      this.render();
    }

    async loadSettings() {
      const stored = await chrome.storage.local.get(DEFAULT_SETTINGS);
      this.settings = core.sanitizeSettings(stored);
    }

    async reloadSettings() {
      const previous = this.settings;
      await this.loadSettings();
      this.overlay?.setVisible(this.settings.showOverlay);
      this.log("settings updated");
      const explicitlyReenabled = (!previous.enabled && this.settings.enabled) ||
        (!previous.automaticReplacement && this.settings.automaticReplacement);
      if (this.manualBypass && (previous.testTrackId !== this.settings.testTrackId || explicitlyReenabled)) {
        this.log(`manual bypass cleared · settings`);
        this.manualBypass = null;
      }
      if ((!this.settings.enabled || !this.settings.automaticReplacement || previous.testTrackId !== this.settings.testTrackId) && this.active) {
        await this.failOpen("settings-changed", false);
      }
      await this.reconcile("settings");
      this.render();
    }

    log(message) {
      const entry = `${new Date().toISOString()} ${String(message)}`;
      this.logs.push(entry);
      this.logs = this.logs.slice(-80);
      this.overlay?.log(message);
    }

    setPhase(nextPhase, reason) {
      if (this.phase !== nextPhase) {
        this.phase = nextPhase;
        this.log(`${nextPhase}${reason ? ` · ${reason}` : ""}`);
      }
      this.render();
    }

    handleSnapshot(snapshot, source) {
      if (!snapshot || this.destroyed) return;
      this.snapshot = snapshot;
      this.updateManualBypass(snapshot.track);
      this.lastEvent = source;
      this.reconcile(source).catch((error) => this.failOpen(`reconcile-error:${error.message}`, true));
      this.render();
    }

    handlePlayerEvent(payload) {
      if (!payload?.snapshot || this.destroyed) return;
      this.snapshot = payload.snapshot;
      this.updateManualBypass(payload.snapshot.track);
      this.lastEvent = payload.event || "unknown";

      if (payload.event === "error") {
        this.failOpen("original-player-error", true);
        return;
      }
      if (payload.event === "ended") {
        this.failOpen("master-ended", false);
        return;
      }
      this.reconcile(`event:${payload.event}`).catch((error) => this.failOpen(`event-error:${error.message}`, true));
      this.render();
    }

    isExactTarget() {
      const track = this.snapshot?.track;
      return Boolean(
        this.settings.testTrackId &&
        track?.id === this.settings.testTrackId &&
        track?.confidence >= 70 &&
        !track?.ambiguous &&
        !this.isManualBypass()
      );
    }

    isManualBypass() {
      return core.isTrackBypassed(this.manualBypass?.trackId, this.snapshot?.track?.id);
    }

    updateManualBypass(track) {
      if (!this.manualBypass || !track?.id || core.isTrackBypassed(this.manualBypass.trackId, track.id)) return;
      const previousTrackId = this.manualBypass.trackId;
      this.manualBypass = null;
      this.log(`manual bypass cleared · ${previousTrackId} → ${track.id}`);
    }

    projectedMasterTime(snapshot = this.snapshot) {
      return core.projectMediaTime(snapshot?.player, snapshot?.observedAt, Date.now());
    }

    async manualRestore(reason) {
      const trackId = this.active?.trackId || this.snapshot?.track?.id || null;
      if (trackId) {
        this.manualBypass = {
          trackId,
          mediaId: this.snapshot?.player?.mediaId || this.active?.mediaId || null,
          requestedAt: Date.now(),
          reason
        };
        this.log(`manual bypass · ${trackId}`);
      }
      await this.failOpen(reason, false);
    }

    async reconcile(reason) {
      if (this.destroyed || this.phase === PHASE.RESTORING || this.phase === PHASE.ERROR) return;
      const player = this.snapshot?.player;
      const track = this.snapshot?.track;

      if (!this.settings.enabled || !this.settings.automaticReplacement) {
        if (this.active || this.phase === PHASE.PREPARING) {
          await this.failOpen("disabled", false);
        }
        return;
      }

      if (this.isManualBypass()) {
        if (this.active || this.phase === PHASE.PREPARING) {
          await this.failOpen("manual-bypass", false);
        } else {
          this.setPhase(PHASE.IDLE, "manual bypass");
        }
        return;
      }

      if (this.active) {
        const staleTrack = track?.id !== this.active.trackId || track?.ambiguous;
        const stalePlayer = !player || player.mediaId !== this.active.mediaId;
        if (staleTrack || stalePlayer) {
          await this.failOpen(staleTrack ? "track-changed" : "master-changed", false);
          return;
        }
        await this.syncFromMaster(reason);
        return;
      }

      if (this.phase === PHASE.PREPARING) return;
      if (this.isExactTarget() && player && !player.paused && !player.ended) {
        await this.activate(player, track, reason);
      } else {
        this.setPhase(PHASE.IDLE, "original audio");
      }
    }

    async activate(player, track, reason) {
      const generation = ++this.generation;
      this.setPhase(PHASE.PREPARING, `${track.id} · ${reason}`);

      try {
        await this.replacement.prepareAt(this.projectedMasterTime());
        if (generation !== this.generation || !this.isExactTarget()) {
          throw new Error("Activation became stale before guard");
        }

        const guardState = await this.bridge.request("GUARD_ENGAGE", { mediaId: player.mediaId }, 2000);
        if (generation !== this.generation || !this.isExactTarget()) {
          throw new Error("Activation became stale after guard");
        }

        this.replacement.applyMasterState({
          ...player,
          volume: guardState?.volume ?? player.volume,
          muted: guardState?.muted ?? player.muted
        });
        this.replacement.seekTo(this.projectedMasterTime());
        await this.replacement.play();

        if (generation !== this.generation || !this.isExactTarget()) {
          throw new Error("Activation became stale after play");
        }

        this.active = {
          generation,
          trackId: track.id,
          mediaId: player.mediaId,
          startedAt: Date.now()
        };
        this.setPhase(PHASE.ACTIVE, track.id);
        this.startSyncLoop();
        await this.syncFromMaster("activation-complete");
      } catch (error) {
        this.log(`activation failed: ${error.message}`);
        await this.failOpen("activation-failed", true);
      }
    }

    startSyncLoop() {
      clearInterval(this.syncTimer);
      this.syncTimer = setInterval(() => {
        this.syncFromMaster("interval").catch((error) => this.failOpen(`sync-error:${error.message}`, true));
      }, 500);
    }

    async syncFromMaster(reason) {
      if (!this.active) return;
      const player = this.snapshot?.player;
      if (!player || player.mediaId !== this.active.mediaId) {
        await this.failOpen("sync-master-missing", true);
        return;
      }

      this.replacement.applyMasterState(player);
      const masterTime = this.projectedMasterTime();
      const drift = core.computeDrift(
        masterTime,
        this.replacement.audio.currentTime,
        this.settings.driftThresholdMs,
        this.replacement.audio.duration
      );
      this.driftMs = drift.driftMs;

      if (player.paused) {
        this.replacement.pause();
      } else {
        if (drift.shouldCorrect || player.seeking || /seek/.test(reason)) {
          this.replacement.seekTo(masterTime);
          this.log(`drift corrected ${drift.driftMs} ms`);
        }
        if (this.replacement.audio.paused) {
          await this.replacement.play();
        }
      }
      this.render();
    }

    async failOpen(reason, isError) {
      if (this.destroyed) return;
      this.generation += 1;
      clearInterval(this.syncTimer);
      this.syncTimer = null;
      this.setPhase(isError ? PHASE.ERROR : PHASE.RESTORING, reason);
      this.replacement.stop();
      this.active = null;
      this.driftMs = null;

      try {
        await this.bridge.request("EMERGENCY_RESTORE", { reason }, 2500);
      } catch (error) {
        this.log(`restore acknowledgement missing: ${error.message}`);
      }

      if (!this.destroyed) {
        this.setPhase(PHASE.IDLE, "original restored");
      }
    }

    getDiagnostics() {
      return {
        celikomVersion: core.VERSION,
        phase: this.phase,
        active: this.active,
        manualBypass: this.manualBypass,
        settings: this.settings,
        track: this.snapshot?.track || null,
        player: this.snapshot?.player || null,
        mediaCandidates: this.snapshot?.mediaCandidates || [],
        bridge: {
          ready: this.bridge.ready,
          healthy: this.bridge.isHealthy(),
          lastSeenAt: this.bridge.lastSeenAt || null
        },
        guardActive: Boolean(this.snapshot?.guardActive),
        driftMs: this.driftMs,
        lastEvent: this.lastEvent,
        page: `${location.origin}${location.pathname}`,
        recentLog: this.logs.slice(-25)
      };
    }

    render() {
      this.overlay?.update({
        phase: this.phase,
        track: this.snapshot?.track || null,
        player: this.snapshot?.player || null,
        driftMs: this.driftMs,
        lastEvent: this.lastEvent,
        diagnostics: this.getDiagnostics()
      });
    }

    shutdown() {
      if (this.destroyed) return;
      this.destroyed = true;
      this.generation += 1;
      clearInterval(this.heartbeatTimer);
      clearInterval(this.reconnectTimer);
      clearInterval(this.syncTimer);
      if (this.visibilityHandler) {
        document.removeEventListener("visibilitychange", this.visibilityHandler);
        this.visibilityHandler = null;
      }
      this.replacement.destroy();
      this.bridge.shutdown();
      this.overlay?.destroy();
    }
  }

  const controller = new CelikomPlaybackController();
  runtime.controller = controller;
  runtime.wake = () => {
    if (controller.destroyed) return;
    controller.bridge.connect();
    controller.render();
  };
  controller.start().catch((error) => {
    controller.failOpen(`startup-error:${error.message}`, true);
  });
})();
