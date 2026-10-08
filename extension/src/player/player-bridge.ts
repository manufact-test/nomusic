(function initCelikomPlayerBridge(root) {
  "use strict";

  const core = root.__CELIKOM_PLAYER_CORE_V1__;
  if (!core) return;

  const GLOBAL_KEY = "__CELIKOM_PLAYER_BRIDGE_V1__";
  if (root[GLOBAL_KEY]) return;
  const DIRECTION_IN = "to-main";
  const DIRECTION_OUT = "from-main";

  class PlayerBridge {
    constructor(targetWindow = root, options = {}) {
      this.targetWindow = targetWindow;
      this.sessionId = options.sessionId || core.createSessionId();
      this.requestTimeoutMs = options.requestTimeoutMs || 2000;
      this.heartbeatIntervalMs = options.heartbeatIntervalMs || 1000;
      this.ready = false;
      this.started = false;
      this.destroyed = false;
      this.lastSeenAt = 0;
      this.lastSequence = 0;
      this.requestSequence = 0;
      this.lastInitAt = 0;
      this.pending = new Map();
      this.listeners = new Map();
      this.heartbeatTimer = null;
      this.onMessage = this.onMessage.bind(this);
    }

    on(type, listener) {
      if (!this.listeners.has(type)) this.listeners.set(type, new Set());
      this.listeners.get(type).add(listener);
      return () => this.off(type, listener);
    }

    off(type, listener) {
      this.listeners.get(type)?.delete(listener);
    }

    emit(type, payload) {
      for (const listener of this.listeners.get(type) || []) {
        try {
          listener(payload);
        } catch (_error) {
          // A diagnostic listener must not break the bridge lifecycle.
        }
      }
    }

    post(type, payload = {}, requestId = null) {
      if (this.destroyed) return;
      this.targetWindow.postMessage({
        channel: core.CHANNEL,
        protocolVersion: core.PROTOCOL_VERSION,
        direction: DIRECTION_IN,
        sessionId: this.sessionId,
        type,
        requestId,
        payload,
        sentAt: Date.now()
      }, "*");
    }

    start() {
      if (this.destroyed) throw new Error("PlayerBridge is destroyed");
      if (this.started) return this;
      this.started = true;
      this.targetWindow.addEventListener("message", this.onMessage);
      this.connect();
      this.heartbeatTimer = this.targetWindow.setInterval(() => this.heartbeat(), this.heartbeatIntervalMs);
      return this;
    }

    connect() {
      if (this.destroyed || !this.started) return;
      this.lastInitAt = Date.now();
      this.post("INIT", { controllerVersion: core.VERSION });
    }

    heartbeat() {
      if (this.destroyed || !this.started) return;
      if (!this.isHealthy() && Date.now() - this.lastInitAt >= this.heartbeatIntervalMs * 2) {
        this.ready = false;
        this.lastSequence = 0;
        this.connect();
        return;
      }
      this.post("HEARTBEAT");
    }

    isHealthy(now = Date.now()) {
      return this.ready && this.lastSeenAt > 0 && now - this.lastSeenAt <= this.heartbeatIntervalMs * 4;
    }

    request(type, payload = {}, timeoutMs = this.requestTimeoutMs) {
      if (this.destroyed) return Promise.reject(new Error("PlayerBridge is destroyed"));
      const requestId = `${this.sessionId}:${++this.requestSequence}`;
      return new Promise((resolve, reject) => {
        const timer = this.targetWindow.setTimeout(() => {
          this.pending.delete(requestId);
          reject(new Error(`Bridge request timed out: ${type}`));
        }, timeoutMs);
        this.pending.set(requestId, { resolve, reject, timer, type });
        this.post("REQUEST", { type, payload }, requestId);
      });
    }

    getSnapshot() {
      return this.request("GET_SNAPSHOT");
    }

    acceptSequence(message) {
      if (!Number.isSafeInteger(message.sequence) || message.sequence <= 0) return false;
      if (message.sequence <= this.lastSequence) return false;
      this.lastSequence = message.sequence;
      return true;
    }

    onMessage(event) {
      if (event.source !== this.targetWindow) return;
      const message = event.data;
      if (!message || message.channel !== core.CHANNEL || message.protocolVersion !== core.PROTOCOL_VERSION) return;
      if (message.direction !== DIRECTION_OUT) return;

      if (message.type === "BRIDGE_PRESENT") {
        if (!this.isHealthy()) {
          this.ready = false;
          this.lastSequence = 0;
        }
        if (this.started && !this.destroyed) this.connect();
        return;
      }
      if (message.sessionId !== this.sessionId) return;
      this.lastSeenAt = Date.now();

      if (message.type === "RESPONSE" && typeof message.requestId === "string") {
        const pending = this.pending.get(message.requestId);
        if (!pending) return;
        this.targetWindow.clearTimeout(pending.timer);
        this.pending.delete(message.requestId);
        if (message.payload?.ok) pending.resolve(message.payload.result);
        else pending.reject(new Error(message.payload?.error || `Bridge request failed: ${pending.type}`));
        return;
      }

      if (!this.acceptSequence(message)) return;
      if (message.type === "READY" || message.type === "HEARTBEAT_ACK") this.ready = true;
      if (message.type === "BRIDGE_TIMEOUT") {
        this.ready = false;
        this.lastSequence = 0;
      }
      this.emit(message.type, message.payload);
      if (message.type === "BRIDGE_TIMEOUT") this.connect();
    }

    destroy() {
      if (this.destroyed) return;
      if (this.started) this.post("SHUTDOWN");
      this.destroyed = true;
      this.ready = false;
      this.started = false;
      this.targetWindow.removeEventListener("message", this.onMessage);
      this.targetWindow.clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
      for (const pending of this.pending.values()) {
        this.targetWindow.clearTimeout(pending.timer);
        pending.reject(new Error("PlayerBridge shut down"));
      }
      this.pending.clear();
      this.listeners.clear();
    }
  }

  Object.defineProperty(root, GLOBAL_KEY, {
    value: Object.freeze({
      PlayerBridge,
      createPlayerBridge: (targetWindow, options) => new PlayerBridge(targetWindow, options)
    }),
    configurable: false,
    enumerable: false,
    writable: false
  });
})(globalThis);
