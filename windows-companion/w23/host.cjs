"use strict";

/**
 * CELIKOM main-process relay for genuine Yandex Music desktop.
 * Bridges only fixed-shape state/grant data through Electron executeJavaScript.
 * Never weakens CSP or requires a browser-accessible localhost endpoint.
 * No access to Yandex account, player controls, queue or third-party secrets.
 */
const { app, webContents } = require("electron");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const allowedOrigins = new Set([
  "https://desktop.app.music.yandex.net",
  "https://music.yandex.ru",
  "https://next.music.yandex.ru",
  "https://music.yandex.com"
]);
const capabilityFile = path.join(process.env.LOCALAPPDATA || "",
  "CELIKOM", "Windows", "native-bridge.key");
const diagnostics = process.env.CELIKOM_W23_DEV_DIAG || "";
const nativeDirectory = path.join(process.env.LOCALAPPDATA || "", "CELIKOM", "Windows");
const nativeFile = path.join(nativeDirectory, "native-events.log");
const logged = new Set();
const recent = [];
const noisy = new Set(["RESOLVE_REQUEST", "GRANT_FOUND", "GRANT_MISS",
  "GRANT_DELIVERED", "GRANT_DELIVERY_FAILED", "LOCAL_RESOLVE_REPLY",
  "RESOLVE_BRIDGE_FAILURE", "NATIVE_FILEINFO_REQUEST", "NATIVE_FILEINFO_OK",
  "NATIVE_FILEINFO_ERROR", "SOURCE_ORIGINAL", "SOURCE_MAPPED",
  "SOURCE_SYNTHETIC_RESPONSE", "NATIVE_FILEINFO_SLOW",
  "RESOLVE_TIMEOUT", "RESOLVE_START", "RESOLVE_ABORTED", "GRANT_RECEIVED",
  "SOURCE_BATCH_REQUEST", "SOURCE_BATCH_MAPPED", "CACHE_HIT",
  "MEDIA_PLAY", "MEDIA_PAUSE", "MEDIA_PLAYING", "MEDIA_ERROR",
  "MEDIA_WAITING", "MEDIA_STALLED", "MEDIA_SEEKING", "MEDIA_SEEKED",
  "MEDIA_ENDED", "MEDIA_REQUEST_SEEN", "MEDIA_HTTP_OK",
  "MEDIA_HTTP_FAILED", "MEDIA_HTTP_UNVERIFIED", "STATE_ENABLED",
  "STATE_DISABLED", "STATE_UNREACHABLE", "RENDERER_STATE_ON",
  "RENDERER_STATE_OFF", "FILEINFO_SHAPE_FILE", "FILEINFO_SHAPE_DOWNLOAD",
  "FILEINFO_SHAPE_MISSING", "BATCH_FILEINFO_ERROR"]);
function note(code, trackId = null) {
  if (!/^[A-Z_]{3,48}$/.test(code)) return;
  const id = typeof trackId === "string" && /^[1-9][0-9]{0,17}$/.test(trackId)
    ? trackId : null;
  if (!noisy.has(code) && logged.has(code)) return;
  if (!noisy.has(code)) logged.add(code);
  const line = new Date().toISOString() + "|" + code +
    (id ? "|track=" + id : "") + "\n";
  recent.push(line);
  if (recent.length > 256) recent.shift();
  if (process.env.LOCALAPPDATA) {
    try {
      fs.mkdirSync?.(nativeDirectory, { recursive: true });
      if ((fs.statSync?.(nativeFile)?.size || 0) > 384 * 1024) {
        try { fs.unlinkSync?.(nativeFile + ".1"); } catch {}
        fs.renameSync?.(nativeFile, nativeFile + ".1");
      }
      fs.appendFileSync(nativeFile, line);
    } catch {}
  }
  // Preserve old disposable-runner proof output, never include source URLs.
  if (diagnostics && !logged.has("DEV_" + code)) {
    logged.add("DEV_" + code);
    try { fs.appendFileSync(diagnostics, code + "\n"); } catch {}
  }
}
let renderer = "";
try {
  renderer = fs.readFileSync(path.join(app.getAppPath(), "celikom", "renderer.js"), "utf8");
} catch {}
note("HOST_LOADED");
if (renderer) note("BUNDLE_PRESENT"); else note("BUNDLE_MISSING");
const injected = new WeakMap();
const busy = new WeakSet();
const lastStateAt = new WeakMap();
const lastStatus = new WeakMap();
const lastNativeState = new WeakMap();
const lastDiagPoll = new WeakMap();

function readToken() {
  try {
    const value = fs.readFileSync(capabilityFile, "utf8").trim();
    return /^[0-9a-f]{64}$/.test(value) ? value : "";
  } catch { return ""; }
}
function validView(view) {
  try {
    if (view.isDestroyed()) return false;
    const url = new URL(view.getURL());
    const proto = url.protocol.replace(/[^a-z]/gi, "").toLowerCase();
    if (allowedOrigins.has(url.origin) ||
        (proto === "musicapplication" && url.hostname.toLowerCase() === "desktop")) {
      note("APPROVED_VIEW");
      return true;
    }
  } catch {}
  return false;
}
function localRequest(token, route, method = "GET", payload = null) {
  return new Promise(resolve => {
    const body = payload == null ? null : JSON.stringify(payload);
    if (!token || typeof route !== "string" || !route.startsWith("/v1/")) {
      resolve(null); return;
    }
    const request = http.request({
      host: "127.0.0.1", port: 21471, path: route, method, timeout: 1000,
      headers: {
        "Origin": "musicapplication://desktop",
        "X-Celikom-Bridge-Token": token,
        "X-Celikom-Native-Host": "1",
        ...(body == null ? {} : {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body)
        })
      }
    }, response => {
      if (response.statusCode !== 200) {
        note("LOCAL_HTTP_NOT_OK");
        response.resume(); resolve(null); return;
      }
      const chunks = [];
      let length = 0;
      response.on("data", buffer => {
        length += buffer.length;
        if (length <= 64 * 1024) chunks.push(buffer);
        else request.destroy(new Error("RESPONSE_TOO_LARGE"));
      });
      response.on("end", () => {
        try {
          resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")));
        } catch { resolve(null); }
      });
      response.on("error", () => resolve(null));
    });
    request.on("timeout", () => { note("LOCAL_HTTP_TIMEOUT"); request.destroy(); });
    request.on("error", () => { note("LOCAL_HTTP_ERROR"); resolve(null); });
    if (body) request.write(body);
    request.end();
  });
}
async function execute(view, js) {
  try {
    if (!validView(view)) return null;
    return await view.executeJavaScript(js);
  } catch { return null; }
}
async function inject(view) {
  if (!renderer || !validView(view)) return false;
  if (injected.get(view) === true) return true;
  const result = await execute(view,
    ";(()=>{if(!window.__celikomBridgeNativeDrain){" + renderer +
    "\n}return !!window.__celikomBridgeNativeDrain;})()");
  if (result !== true) return false;
  injected.set(view, true);
  note("RENDERER_INJECTED");
  return true;
}
async function relayState(view, token, now) {
  if (now - (lastStateAt.get(view) || 0) < 2200) return;
  lastStateAt.set(view, now);
  const state = await localRequest(token, "/v1/state");
  if (state && typeof state === "object") note("LOCAL_STATE_OK");
  else note("STATE_UNREACHABLE");
  const active = state?.enabled === true;
  if (lastNativeState.get(view) !== active) {
    lastNativeState.set(view, active);
    note(active ? "STATE_ENABLED" : "STATE_DISABLED");
  }
  const safeState = {
    enabled: state?.enabled === true,
    signedIn: state?.signedIn === true,
    apiOrigin: typeof state?.apiOrigin === "string" ? state.apiOrigin.slice(0, 256) : ""
  };
  const ok = await execute(view,
    ";(()=>{if(!window.__celikomBridgeNativeSetState)return false;" +
    "window.__celikomBridgeNativeSetState(" + JSON.stringify(safeState) + ");return true})()");
  if (ok === true) note("RENDERER_STATE_DELIVERED");
}
async function relayGrant(view, token, request) {
  if (!request || typeof request !== "object" ||
      typeof request.requestId !== "string" ||
      !/^[1-9][0-9]{0,12}$/.test(request.requestId) ||
      typeof request.trackId !== "string" ||
      !/^[1-9][0-9]{0,23}$/.test(request.trackId)) return;
  note("RESOLVE_REQUEST", request.trackId);
  const response = await localRequest(token,
    "/v1/resolve?track_id=" + encodeURIComponent(request.trackId));
  if (response != null) note("LOCAL_RESOLVE_REPLY", request.trackId);
  else note("RESOLVE_BRIDGE_FAILURE", request.trackId);
  const grant = response?.found === true ? response.grant ?? null : null;
  note(grant ? "GRANT_FOUND" : "GRANT_MISS", request.trackId);
  // The result is application data only; no bridge capability or auth token
  // is transmitted into the renderer, only an approved signed audio grant.
  const sent = await execute(view,
    ";(()=>{if(typeof window.__celikomBridgeNativeReceive!=='function')return false;" +
    "window.__celikomBridgeNativeReceive(" + JSON.stringify(request.requestId) +
    "," + JSON.stringify(grant) + ");return true})()");
  note(sent === true ? "GRANT_DELIVERED" : "GRANT_DELIVERY_FAILED", request.trackId);
}
async function tick(view) {
  if (!validView(view) || busy.has(view)) return;
  busy.add(view);
  try {
    if (!await inject(view)) return;
    const token = readToken();
    if (!token) {
      await execute(view,
        ";window.__celikomBridgeNativeSetState?.({enabled:false,signedIn:false,apiOrigin:''})");
      return;
    }
    note("BOOTSTRAP_KEY_PRESENT");
    const now = Date.now();
    if (now - (lastDiagPoll.get(view) || 0) >= 700) {
      lastDiagPoll.set(view, now);
      const events = await execute(view, ";(window.__celikomBridgeNativeDrainDiagnostics?.()||[])");
      if (Array.isArray(events))
        for (const event of events.slice(0, 48))
          if (Array.isArray(event) && event.length === 2)
            note(event[0], event[1]);
    }
    await relayState(view, token, now);
    const queue = await execute(view,
      ";(window.__celikomBridgeNativeDrain?.()||[])");
    if (Array.isArray(queue)) {
      await Promise.all(queue.slice(0, 6).map(item => relayGrant(view, token, item)));
    }
    if (now - (lastStatus.get(view)?.at || 0) > 2200) {
      const status = await execute(view, ";window.__celikomBridgeNativeStatus?.()||'ORIGINAL'");
      const previous = lastStatus.get(view);
      lastStatus.set(view, { value: status, at: now });
      if ((status === "NATIVE_CONNECTED" || status === "NATIVE_MAPPING_ACCEPTED" ||
           status === "ORIGINAL") && (!previous || status !== previous.value)) {
        await localRequest(token, "/v1/heartbeat", "POST",
          {trackId:null,status});
      }
    }
  } finally {
    busy.delete(view);
  }
}
app.on("web-contents-created", (_event, view) => {
  view.on("dom-ready", () => { injected.delete(view); void tick(view); });
  view.on("did-finish-load", () => { injected.delete(view); void tick(view); });
  view.on("console-message", (event, _level, legacy) => {
    const msg = typeof event?.message === "string" ? event.message : legacy;
    if (msg === "[CELIKOM] Native file-info source connector attached") note("RESOURCE_ATTACHED");
    if (msg === "[CELIKOM] Native bridge state received") note("RENDERER_BRIDGE_STATE_SEEN");
  });
});
const timer = setInterval(() => {
  const views = webContents.getAllWebContents();
  if (views.length) note("WEB_CONTENTS_PRESENT");
  for (const view of views) void tick(view);
}, 180);
if (timer.unref) timer.unref();
