(function startCelikomMainWorldBridge(root) {
  "use strict";

  const core = root.__CELIKOM_PLAYER_CORE_V1__;
  const adapterFactory = root.__CELIKOM_YANDEX_ADAPTER_V1__;
  const guardFactory = root.__CELIKOM_ORIGINAL_GUARD_V1__;
  if (!core || !adapterFactory || !guardFactory) return;

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
  let lastReleasedGeneration = 0;
  let lastGuardGeneration = 0;
  const adapter = adapterFactory.createAdapter(root);
  const guard = new guardFactory.OriginalAudioGuard(() => {
    post("PLAYER_SNAPSHOT", decorate(adapter.getSnapshot("volume-intent")));
  });

  function stopReplacement() {
    for (const element of root.document?.querySelectorAll('audio[data-celikom-replacement="true"]') || []) {
      try { element.muted = true; element.pause(); } catch (_error) { /* keep restoring */ }
    }
  }

  function release(reason, token = null) {
    const oldToken = guard.current?.token;
    const releasedGeneration = leaseGeneration(token || oldToken);
    if (releasedGeneration) lastReleasedGeneration = Math.max(lastReleasedGeneration, releasedGeneration);
    if (token && guard.current?.token !== token) return { released: false };
    stopReplacement();
    const result = guard.release(token);
    if (oldToken) post("GUARD_RELEASED", { reason, token: oldToken });
    if (oldToken && adapter.mounted) post("PLAYER_SNAPSHOT", decorate(adapter.getSnapshot("guard-released")));
    return result;
  }

  function leaseGeneration(token) {
    if (typeof token !== "string" || !controllerSession || !token.startsWith(`${controllerSession}:`)) return 0;
    const suffix = token.slice(controllerSession.length + 1);
    const generation = /^\d+$/.test(suffix) ? Number(suffix) : 0;
    return Number.isSafeInteger(generation) && generation > 0 ? generation : 0;
  }

  function decorate(snapshot) {
    const state = guard.state();
    if (snapshot.player) snapshot.player.guarded = state.active && state.mediaId === snapshot.player.mediaId;
    snapshot.guard = state;
    return snapshot;
  }

  function checkBinding(snapshot) {
    const lease = guard.current;
    if (!lease) return;
    const player = snapshot.player;
    if (snapshot.track?.id !== lease.trackId || snapshot.track?.ambiguous || player?.mediaId !== lease.mediaId
      || player?.ended
      || Math.abs(player.duration * 1000 - snapshot.track.metadata?.durationMs) > 1500) {
      release("master-binding-changed", lease.token);
    }
  }

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
      checkBinding(snapshot);
      post("PLAYER_SNAPSHOT", decorate(snapshot));
    },
    onPlayerEvent(event) {
      checkBinding(event.snapshot);
      if (["ENDED", "ERROR"].includes(event.type)) release(`master-${event.type.toLowerCase()}`);
      if (["PAUSE", "SEEK"].includes(event.type)) {
        for (const element of root.document?.querySelectorAll('audio[data-celikom-replacement="true"]') || []) {
          try { element.pause(); } catch (_error) { /* isolated controller also pauses */ }
        }
      }
      post("PLAYER_EVENT", { ...event, snapshot: decorate(event.snapshot) });
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
    if (controllerSession && controllerSession !== sessionId) { release("session-changed"); adapter.unmount(); }
    controllerSession = sessionId;
    lastReleasedGeneration = 0;
    lastGuardGeneration = 0;
    lastHeartbeatAt = now();
    sequence = 0;
    adapter.mount(sink);
    post("READY", {
      bridgeVersion: core.VERSION,
      protocolVersion: core.PROTOCOL_VERSION,
      service: adapter.service
    });
    post("PLAYER_SNAPSHOT", decorate(adapter.getSnapshot("bridge-init")));
  }

  function detach(reason) {
    if (!controllerSession) return;
    const previousSession = controllerSession;
    release(reason);
    adapter.unmount();
    controllerSession = null;
    lastHeartbeatAt = 0;
    sequence = 0;
    return { detached: true, reason, sessionId: previousSession };
  }

  function handleRequest(type, payload) {
    if (type === "GET_SNAPSHOT") return decorate(adapter.getSnapshot("request"));
    if (type === "GUARD_RELEASE") return release(payload?.reason || "release-request", payload?.token);
    if (type === "GUARD_ENGAGE") {
      const generation = leaseGeneration(payload?.token);
      if (!generation || generation <= lastReleasedGeneration || generation < lastGuardGeneration) throw new Error("Invalid or cancelled guard lease");
      const snapshot = adapter.getSnapshot("guard-request");
      const element = adapter.getMediaElement(payload.mediaId);
      const player = snapshot.player;
      if (!element || snapshot.track?.ambiguous || snapshot.track?.id !== payload.trackId || snapshot.track?.confidence < 100
        || player?.mediaId !== payload.mediaId || player?.ended || player?.readyState < 2
        || !Number.isFinite(player.duration) || !snapshot.track.metadata?.durationMs
        || Math.abs(player.duration * 1000 - snapshot.track.metadata.durationMs) > 1500) throw new Error("Master changed before guard");
      guard.engage(element, payload.mediaId, payload.token);
      lastGuardGeneration = generation;
      guard.current.trackId = payload.trackId;
      return { guard: guard.state(), snapshot: decorate(adapter.getSnapshot("guard-engaged")) };
    }
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

    if (message.type === "RELEASE_NOW") { release(message.payload?.reason || "emergency-signal", message.payload?.token); return; }

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
        const result = handleRequest(message.payload?.type, message.payload?.payload);
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
        lastHeartbeatAt,
        guard: guard.state()
      })
    }),
    configurable: false,
    enumerable: false,
    writable: false
  });

  announce();
})(globalThis);
