(function (root) {
  "use strict";
  if (root.__CELIKOM_NATIVE_RUNTIME__) return;
  const channel = "CELIKOM_NATIVE_EXPERIMENT_V1", core = root.__CELIKOM_PLAYER_CORE_V1__;
  const session = new root.__CELIKOM_NATIVE_SESSION__.NativeSession({
    port: new root.__CELIKOM_NATIVE_ENGINE_PORT__.EnginePort(), resource: root.__CELIKOM_NATIVE_SOURCE_RESEARCH__
  });
  let controller = null, heartbeat = 0, resetting = false;
  const reset = () => {
    if (resetting) return;
    resetting = true;
    session.configure(false, Math.max(0, session.generation)).catch(() => {}).finally(() => { resetting = false; });
  };
  root.addEventListener("message", event => {
    if (event.source !== root) return;
    const m = event.data;
    if (m?.channel === core.CHANNEL && m.direction === "to-main" && m.protocolVersion === core.PROTOCOL_VERSION) {
      if (m.type === "INIT" && typeof m.sessionId === "string" && m.sessionId.length >= 8) {
        if (controller && controller !== m.sessionId) { reset(); return; }
        controller = m.sessionId; heartbeat = Date.now();
      }
      if (m.sessionId !== controller) return;
      if (m.type === "HEARTBEAT") heartbeat = Date.now();
      if (["SHUTDOWN", "RELEASE_NOW"].includes(m.type)) reset();
      return;
    }
    if (m?.channel !== channel || m.direction !== "request" || m.sessionId !== controller || !controller
      || typeof m.requestId !== "string" || m.requestId.length > 180) return;
    const run = async () => {
      if (resetting && m.type !== "inspect") throw Error("native_reset_pending");
      if (m.type === "inspect") return session.inspect();
      if (m.type === "configure") return session.configure(m.payload?.enabled, m.payload?.generation);
      if (m.type === "publish") return session.publish(m.payload);
      if (m.type === "activate") return session.activate(m.payload?.trackId, m.payload?.generation);
      if (m.type === "revoke") return session.revoke(m.payload);
      throw Error("native_unknown_command");
    };
    void run().then(result => ({ ok: true, result }), error => ({ ok: false, error: String(error?.message || "native_failed") }))
      .then(payload => root.postMessage({ channel, direction: "response", sessionId: m.sessionId, requestId: m.requestId, payload }, "*"));
  });
  root.setInterval(() => {
    const state = session.inspect();
    const expired = session.active && session.assets.get(session.active)?.expiresAt <= Date.now() + 1000;
    if (session.enabled && (expired || state.sourceMismatch || Date.now() - heartbeat > (root.document.hidden ? 120000 : 12000))) reset();
  }, 1000);
  root.addEventListener("pagehide", reset);
  Object.defineProperty(root, "__CELIKOM_NATIVE_RUNTIME__", { value: { inspect: () => session.inspect() }, configurable: false });
})(globalThis);
