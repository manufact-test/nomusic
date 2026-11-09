/*
 * W36 improvement to W33 disposable CI-only original Yandex boundary probe.
 * Appended to host.cjs only with CELIKOM_W33_RUNTIME_PROBE=1 in Windows CI.
 * Never distributed to the owner. No real signed tokens, accounts or audio.
 * The ONLY URL fetched has a deliberately invalid, hardcoded token.
 */
(() => {
  const fs = require("node:fs");
  const log = process.env.CELIKOM_W23_DEV_DIAG || "";
  function note(code) {
    if (!log || !/^[A-Z0-9_]{6,100}$/.test(code)) return;
    try { fs.appendFileSync(log, "W33_RT_" + code + "\n"); } catch {}
  }
  note(process.env.CELIKOM_W33_RUNTIME_PROBE === "1"
    ? "BOOTSTRAP_ON" : "BOOTSTRAP_OFF");
  if (process.env.CELIKOM_W33_RUNTIME_PROBE !== "1") return;

  const { app, webContents } = require("electron");
  if (!app || !webContents || typeof webContents.getAllWebContents !== "function") {
    note("ELECTRON_API_UNAVAILABLE");
    return;
  }
  const https = require("node:https");
  const invalid = "https://darkred-camel-588676.hostingersite.com" +
    "/api/v1/audio/7?token=" + "0".repeat(64) + "&expires=1800000180&sid=1";
  const allowed = new Set([
    "https://desktop.app.music.yandex.net",
    "https://music.yandex.ru", "https://next.music.yandex.ru",
    "https://music.yandex.com"
  ]);
  const started = new Map();
  const completed = new Set();
  const inFlight = new Set();
  const startedAt = Date.now();
  let discovered = false;
  const seenViewKinds = new Set();
  function noteViewKind(view) {
    let kind = "VIEW_URL_EMPTY";
    try {
      const raw = view.getURL();
      if (raw) {
        const u = new URL(raw);
        kind = u.protocol === "musicapplication:" ? "VIEW_SCHEME_NATIVE" :
          u.protocol === "https:" ? "VIEW_SCHEME_HTTPS" : "VIEW_SCHEME_OTHER";
        if (u.hostname.toLowerCase() === "desktop") kind = "VIEW_HOST_DESKTOP";
        else if (u.hostname.toLowerCase().endsWith(".yandex.ru") ||
          u.hostname.toLowerCase().endsWith(".yandex.net") ||
          u.hostname.toLowerCase() === "music.yandex.com") kind = "VIEW_HOST_YANDEX";
      }
    } catch { kind = "VIEW_URL_PARSE_ERROR"; }
    if (!seenViewKinds.has(kind)) { seenViewKinds.add(kind); note(kind); }
  }
  let finished = false;
  let pending = 0;

  // Compare with trusted Node/Electron main. This request has NO valid grant.
  const req = https.get(invalid, {
    headers: {
      Origin: "musicapplication://desktop",
      Range: "bytes=0-31"
    },
    timeout: 7000
  }, res => {
    const status = res.statusCode;
    note(status === 403 ? "MAIN_HTTP_403" :
      status >= 300 && status < 400 ? "MAIN_REDIRECT" :
      status >= 200 && status < 300 ? "MAIN_HTTP_2XX" : "MAIN_HTTP_OTHER");
    const acao = res.headers["access-control-allow-origin"];
    note(acao === "musicapplication://desktop" ? "MAIN_ACAO_NATIVE" :
      acao === "*" ? "MAIN_ACAO_WILDCARD" :
      acao === "null" ? "MAIN_ACAO_NULL" : "MAIN_ACAO_OTHER");
    res.resume();
  });
  req.on("timeout", () => { note("MAIN_TIMEOUT"); req.destroy(); });
  req.on("error", () => note("MAIN_NETWORK_ERROR"));

  // This function is serialized into the genuine Yandex renderer (not a
  // separate browser, local player, test HTML page, or isolated WebView).
  async function rendererProbe() {
    // Match the same native custom-scheme normalization as renderer-entry.mjs.
    const scheme = String(location.protocol || "").replace(/[^a-z]/gi, "").toLowerCase();
    const host = String(location.hostname || "").toLowerCase();
    const native = scheme === "musicapplication" && host === "desktop";
    const type = native ? "NATIVE" :
      location.origin === "https://music.yandex.ru" ? "MUSIC_WEB" :
      location.origin === "https://next.music.yandex.ru" ? "NEXT_WEB" :
      location.origin === "https://desktop.app.music.yandex.net" ? "DESKTOP_WEB" :
      location.origin === "https://music.yandex.com" ? "MUSIC_COM" : "OTHER";
    const realm = type !== "OTHER" ? "APPROVED" :
      scheme === "https" ? "UNEXPECTED_HTTPS" :
      scheme === "about" ? "ABOUT" :
      scheme === "file" ? "FILE" : "UNEXPECTED_SCHEME";
    const base = "https://darkred-camel-588676.hostingersite.com";
    const url = base + "/api/v1/audio/7?token=" + "0".repeat(64) +
      "&expires=1800000180&sid=1";
    let csp = "NONE";
    const mark = event => {
      if (!event || typeof event.blockedURI !== "string") return;
      try {
        if (new URL(event.blockedURI).origin !== base) return;
        const directive = String(event.effectiveDirective || "");
        csp = directive === "connect-src" ? "CONNECT_SRC" :
          directive === "media-src" ? "MEDIA_SRC" : "OTHER";
      } catch {}
    };
    document.addEventListener("securitypolicyviolation", mark, true);
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), 6000);
    let outcome = "UNKNOWN";
    try {
      const r = await fetch(url, {
        method: "GET", mode: "cors", credentials: "omit",
        redirect: "error", cache: "no-store",
        headers: { Range: "bytes=0-31" }, signal: abort.signal
      });
      outcome = r.status === 403 ? "HTTP_403_VISIBLE" :
        r.status === 200 ? "HTTP_200_VISIBLE" :
        r.status === 206 ? "HTTP_206_VISIBLE" : "HTTP_OTHER_VISIBLE";
      try { await r.body?.cancel(); } catch {}
    } catch (error) {
      outcome = error?.name === "AbortError" ? "TIMEOUT" :
        error instanceof TypeError ? "FETCH_BLOCKED_TYPEERROR" : "FETCH_OTHER_ERROR";
    } finally {
      clearTimeout(timer);
      await new Promise(resolve => setTimeout(resolve, 250));
      document.removeEventListener("securitypolicyviolation", mark, true);
    }
    return { type, outcome, csp, realm };
  }

  function approved(view) {
    try {
      if (typeof validView === "function") return validView(view);
      if (view.isDestroyed()) return false;
      const url = new URL(view.getURL());
      return allowed.has(url.origin) ||
        (url.protocol === "musicapplication:" && url.hostname === "desktop");
    } catch { return false; }
  }
  function classify(result) {
    const type = ["NATIVE", "MUSIC_WEB", "NEXT_WEB", "DESKTOP_WEB", "MUSIC_COM", "OTHER"]
      .includes(result?.type) ? result.type : "OTHER";
    const outcome = ["HTTP_403_VISIBLE", "HTTP_200_VISIBLE", "HTTP_206_VISIBLE",
      "HTTP_OTHER_VISIBLE", "TIMEOUT", "FETCH_BLOCKED_TYPEERROR",
      "FETCH_OTHER_ERROR"].includes(result?.outcome) ? result.outcome : "UNRECOGNIZED";
    const csp = ["NONE", "CONNECT_SRC", "MEDIA_SRC", "OTHER"]
      .includes(result?.csp) ? result.csp : "UNRECOGNIZED";
    return type + "_" + outcome + "_CSP_" + csp;
  }
  // W37: passive Chrome DevTools Protocol observer ONLY on the disposable CI
  // copy of genuine Yandex. It never intercepts or rewrites requests, reads
  // response bodies, disables protections, or exports URLs/headers/credentials.
  async function attachPassiveNetwork(view) {
    if (process.env.CELIKOM_W37_CDP_PROBE !== "1") return () => {};
    const debug = view?.debugger;
    if (!debug || typeof debug.attach !== "function" ||
        typeof debug.sendCommand !== "function") {
      note("CDP_UNAVAILABLE");
      return () => {};
    }
    try {
      if (debug.isAttached()) { note("CDP_ALREADY_ATTACHED"); return () => {}; }
      debug.attach("1.3");
    } catch { note("CDP_ATTACH_FAILED"); return () => {}; }

    const tracked = new Set();
    let seen = false, closed = false;
    const onMessage = (_event, method, data) => {
      try {
        if (method === "Network.requestWillBeSent" && data?.request?.url === invalid) {
          tracked.add(String(data.requestId));
          seen = true;
          note("CDP_REQUEST_SEEN");
        } else if (method === "Network.responseReceived" &&
            tracked.has(String(data?.requestId))) {
          const status = Number(data?.response?.status);
          note(status === 403 ? "CDP_HTTP_403" :
            status >= 200 && status < 300 ? "CDP_HTTP_2XX" : "CDP_HTTP_OTHER");
        } else if (method === "Network.loadingFailed" &&
            tracked.has(String(data?.requestId))) {
          if (data?.corsErrorStatus) note("CDP_LOAD_FAILED_CORS");
          else if (data?.blockedReason === "csp") note("CDP_LOAD_FAILED_CSP");
          else if (data?.blockedReason === "mixed-content") note("CDP_LOAD_FAILED_MIXED");
          else if (data?.blockedReason) note("CDP_LOAD_FAILED_BLOCKED_OTHER");
          else if (/ERR_(TIMED_OUT|CONNECTION_TIMED_OUT)/.test(String(data?.errorText)))
            note("CDP_LOAD_FAILED_TIMEOUT");
          else if (/ERR_(NAME_NOT_RESOLVED|CONNECTION_REFUSED|INTERNET_DISCONNECTED)/.test(
            String(data?.errorText))) note("CDP_LOAD_FAILED_NETWORK");
          else note("CDP_LOAD_FAILED_UNSPECIFIED");
        } else if (method === "Log.entryAdded") {
          const message = String(data?.entry?.text || "");
          if (message.includes("darkred-camel-588676.hostingersite.com") &&
              /Content Security Policy|Refused to connect|violates the following/i.test(message))
            note("CDP_CSP_CONSOLE");
        }
      } catch {}
    };
    debug.on("message", onMessage);
    try {
      await debug.sendCommand("Network.enable");
      await debug.sendCommand("Log.enable");
      note("CDP_NETWORK_ENABLED");
    } catch {
      note("CDP_ENABLE_FAILED");
      try { debug.removeListener("message", onMessage); debug.detach(); } catch {}
      return () => {};
    }
    function close() {
      if (closed) return;
      closed = true;
      if (!seen) note("CDP_REQUEST_NOT_SEEN");
      try { debug.removeListener("message", onMessage); } catch {}
      try { if (debug.isAttached()) debug.detach(); } catch {}
    }
    setTimeout(close, 14500);
    return close;
  }

  function attempt(view) {
    if (finished || !approved(view) || completed.has(view.id) || inFlight.has(view.id) || pending > 2) return;
    discovered = true;
    const attempts = started.get(view.id) || 0;
    if (attempts >= 3) return;
    let loading = true;
    try { loading = view.isLoadingMainFrame(); } catch {}
    if (loading) return;
    started.set(view.id, attempts + 1);
    inFlight.add(view.id);
    pending++;
    note("APPROVED_RENDERER_FOUND");
    const timeout = new Promise(resolve => {
      setTimeout(() => resolve({ timedOut: true }), 12500);
    });
    const task = Promise.resolve().then(async () => {
      const close = await attachPassiveNetwork(view);
      try {
        const result = await view.executeJavaScript("(" + rendererProbe.toString() + ")()");
        if (process.env.CELIKOM_W37_CDP_PROBE === "1")
          await new Promise(resolve => setTimeout(resolve, 750));
        return result;
      } finally { close(); }
    });
    void Promise.race([task.then(result => ({ result }), () => ({ failed: true })), timeout])
      .then(value => {
        if (value?.timedOut) {
          note("RENDERER_EXECUTION_TIMEOUT");
        } else if (value?.failed || !value?.result) {
          note("RENDERER_EXECUTION_FAILED");
        } else {
          note(classify(value.result));
          const realm = ["APPROVED","UNEXPECTED_HTTPS","ABOUT","FILE","UNEXPECTED_SCHEME"]
            .includes(value.result.realm) ? value.result.realm : "UNKNOWN";
          note("REALM_" + realm);
          completed.add(view.id);
        }
      }).finally(() => { pending--; inFlight.delete(view.id); });
  }
  function scan() {
    if (finished) return;
    let views;
    try { views = webContents.getAllWebContents(); }
    catch { note("WEB_CONTENTS_SCAN_ERROR"); return; }
    if (!Array.isArray(views)) return;
    if (views.length === 0) note("VIEW_LIST_EMPTY");
    for (const view of views) { noteViewKind(view); attempt(view); }
  }
  // The CI-compiled host calls this ONLY after its existing approved-view gate.
  // Avoid a second, potentially mistimed webContents discovery path.
  globalThis.__celikomW33OnApprovedView = attempt;
  app.on("web-contents-created", (_event, view) => {
    if (finished) return;
    view.on("dom-ready", () => attempt(view));
    view.on("did-finish-load", () => attempt(view));
    view.on("did-navigate", () => attempt(view));
  });
  const pulse = setInterval(scan, 500);
  scan();
  setTimeout(() => {
    finished = true;
    clearInterval(pulse);
    if (globalThis.__celikomW33OnApprovedView === attempt)
      delete globalThis.__celikomW33OnApprovedView;
    if (!discovered) note("NO_APPROVED_RENDERER_OBSERVED");
    if (pending > 0) note("EXECUTION_STILL_PENDING");
    if (!completed.size) note("NO_RENDERER_RESULT_OBSERVED");
  }, 70000);
})();