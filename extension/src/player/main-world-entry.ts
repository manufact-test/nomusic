(function startCelikomMainWorldBridge(root) {
  "use strict";

  const core = root.__CELIKOM_PLAYER_CORE_V1__;
  const adapterFactory = root.__CELIKOM_YANDEX_ADAPTER_V1__;
  if (!core || !adapterFactory) return;

  const BRIDGE_KEY = "__CELIKOM_MAIN_BRIDGE_V1__";
  if (root[BRIDGE_KEY]) {
    root[BRIDGE_KEY].announce();
    return;
  }

  const DIRECTION_IN = "to-main";
  const DIRECTION_OUT = "from-main";
  const VISIBLE_TIMEOUT_MS = 12000;
  const HIDDEN_TIMEOUT_MS = 120000;
  let controllerSession = null;
  let lastHeartbeatAt = 0;
  let sequence = 0;
  let destroyed = false;
  const adapter = adapterFactory.createAdapter(root);

  function now() {
    return Date.now();
  }

  function post(type, payload = {}, requestId = null) {
    if (!controllerSession && type !== "BRIDGE_PRESENT") return null;
    const messageSequence = type === "BRIDGE_PRESENT" ? 0 : ++sequence;
    const normalizedPayload = type === "PLAYER_EVENT"
      ? { ...payload, sequence: messageSequence }
      : payload;
    root.postMessage({
      channel: core.CHANNEL,
      protocolVersion: core.PROTOCOL_VERSION,
      direction: DIRECTION_OUT,
      sessionId: controllerSession,
      sequence: messageSequence,
      type,
      requestId,
      payload: normalizedPayload,
      sentAt: now()
    }, "*");
    return messageSequence;
  }

  const sink = Object.freeze({
    onSnapshot(snapshot) {
      post("PLAYER_SNAPSHOT", snapshot);
    },
    onPlayerEvent(event) {
      post("PLAYER_EVENT", event);
    }
  });

  function attach(sessionId) {
    if (controllerSession === sessionId && adapter.mounted) {
      lastHeartbeatAt = now();
      post("READY", {
        bridgeVersion: core.VERSION,
        protocolVersion: core.PROTOCOL_VERSION,
        service: adapter.service
      });
      return;
    }
    if (controllerSession && controllerSession !== sessionId) adapter.unmount();
    controllerSession = sessionId;
    lastHeartbeatAt = now();
    sequence = 0;
    adapter.mount(sink);
    post("READY", {
      bridgeVersion: core.VERSION,
      protocolVersion: core.PROTOCOL_VERSION,
      service: adapter.service
    });
    post("PLAYER_SNAPSHOT", adapter.getSnapshot("bridge-init"));
  }

  function detach(reason) {
    if (!controllerSession) return;
    const previousSession = controllerSession;
    adapter.unmount();
    controllerSession = null;
    lastHeartbeatAt = 0;
    sequence = 0;
    return { detached: true, reason, sessionId: previousSession };
  }

  function handleRequest(type) {
    if (type === "GET_SNAPSHOT") return adapter.getSnapshot("request");
    throw new Error(`Unknown bridge request: ${type}`);
  }

  function validSessionId(value) {
    return typeof value === "string" && value.length >= 8 && value.length <= 128;
  }

  function onWindowMessage(event) {
    if (destroyed || event.source !== root) return;
    const message = event.data;
    if (!message || message.channel !== core.CHANNEL || message.protocolVersion !== core.PROTOCOL_VERSION) return;
    if (message.direction !== DIRECTION_IN || !validSessionId(message.sessionId)) return;

    if (message.type === "INIT") {
      attach(message.sessionId);
      return;
    }
    if (message.sessionId !== controllerSession) return;
    lastHeartbeatAt = now();

    if (message.type === "HEARTBEAT") {
      post("HEARTBEAT_ACK", {
        bridgeVersion: core.VERSION,
        hidden: Boolean(root.document?.hidden)
      });
      return;
    }
    if (message.type === "SHUTDOWN") {
      detach("content-shutdown");
      return;
    }
    if (message.type === "REQUEST" && typeof message.requestId === "string") {
      try {
        const result = handleRequest(message.payload?.type);
        if (controllerSession) post("RESPONSE", { ok: true, result }, message.requestId);
      } catch (error) {
        post("RESPONSE", { ok: false, error: String(error?.message || error) }, message.requestId);
      }
    }
  }

  function announce() {
    if (destroyed) return;
    root.postMessage({
      channel: core.CHANNEL,
      protocolVersion: core.PROTOCOL_VERSION,
      direction: DIRECTION_OUT,
      sessionId: controllerSession,
      sequence: 0,
      type: "BRIDGE_PRESENT",
      payload: { bridgeVersion: core.VERSION, service: adapter.service },
      sentAt: now()
    }, "*");
  }

  function checkHeartbeat() {
    if (!controllerSession) return;
    const timeoutMs = root.document?.hidden ? HIDDEN_TIMEOUT_MS : VISIBLE_TIMEOUT_MS;
    const elapsedMs = now() - lastHeartbeatAt;
    if (elapsedMs <= timeoutMs) return;
    post("BRIDGE_TIMEOUT", { elapsedMs, hidden: Boolean(root.document?.hidden) });
    detach("heartbeat-timeout");
  }

  function onVisibilityChange() {
    if (root.document?.hidden) return;
    checkHeartbeat();
    announce();
  }

  function destroy(reason = "page-unload") {
    if (destroyed) return;
    detach(reason);
    destroyed = true;
    root.removeEventListener("message", onWindowMessage);
    root.document?.removeEventListener("visibilitychange", onVisibilityChange);
    root.clearInterval(watchdogTimer);
  }

  root.addEventListener("message", onWindowMessage);
  root.document?.addEventListener("visibilitychange", onVisibilityChange);
  root.addEventListener("pagehide", () => destroy("pagehide"), { once: true, capture: true });
  const watchdogTimer = root.setInterval(checkHeartbeat, 500);

  Object.defineProperty(root, BRIDGE_KEY, {
    value: Object.freeze({
      announce,
      destroy,
      getDiagnostics: () => ({
        attached: Boolean(controllerSession),
        mounted: adapter.mounted,
        service: adapter.service,
        lastHeartbeatAt
      })
    }),
    configurable: false,
    enumerable: false,
    writable: false
  });

  announce();
})(globalThis);
