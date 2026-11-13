/**
 * W7 - fail closed, fixture-only DevTools target gate.
 * Do not use this module to attach to real or authenticated applications.
 */
const idPattern = /^[a-f0-9]{32}$/;

export function classifyDebugTarget({ target, debuggerPort, fixtureOrigin, nonce }) {
  const no = reason => Object.freeze({ accepted: false, reason, mayTouchOfficialYandex: false });
  if (!idPattern.test(nonce || "")) return no("INVALID_NONCE");
  if (!Number.isInteger(debuggerPort) || debuggerPort < 1024 || debuggerPort > 65535)
    return no("INVALID_DEBUG_PORT");
  let expected, page, ws;
  try {
    expected = new URL(fixtureOrigin);
    page = new URL(target?.url);
    ws = new URL(target?.webSocketDebuggerUrl);
  } catch { return no("INVALID_TARGET_URL"); }
  if (expected.protocol !== "http:" || expected.hostname !== "127.0.0.1" ||
      !expected.port || expected.pathname !== "/" || expected.search || expected.hash)
    return no("NONLOCAL_FIXTURE_ORIGIN");
  if (page.origin !== expected.origin || page.pathname !== "/" ||
      page.search !== "?nonce=" + nonce || page.hash)
    return no("TARGET_NOT_EXACT_FIXTURE");
  if (target?.type !== "page" || target?.title !== "CELIKOM W7 isolated attach")
    return no("TARGET_NOT_W7_PAGE");
  if (ws.protocol !== "ws:" || ws.hostname !== "127.0.0.1" ||
      Number(ws.port) !== debuggerPort || !/^\/devtools\/page\/[a-zA-Z0-9_-]+$/.test(ws.pathname) ||
      ws.username || ws.password || ws.search || ws.hash)
    return no("DEBUG_ENDPOINT_UNSAFE");
  return Object.freeze({
    accepted: true, reason: "EXACT_W7_SYNTHETIC_TARGET",
    mayTouchOfficialYandex: false,
    noInstalledYandexProcess: true,
    noYandexAccountAccess: true
  });
}

export function productionDecision() {
  return Object.freeze({
    supportedLiveAttachment: false,
    officialPlayerIntegrationTested: false,
    allowDebugPortOnUserYandex: false,
    allowYandexFileChanges: false,
    why: "Remote debugging grants broad access to the live renderer; W7 is fixture-only."
  });
}
