"use strict";
const CELIKOM_NATIVE_VERSION = "0.24.26";

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
const noisy = new Set(["TRACK_CHANGED", "RESOLVE_REQUEST", "GRANT_FOUND", "GRANT_MISS",
  "GRANT_DELIVERED", "GRANT_DELIVERY_FAILED", "LOCAL_RESOLVE_REPLY",
  "RESOLVE_BRIDGE_FAILURE", "RESOLVE_TRANSIENT", "NATIVE_FILEINFO_REQUEST", "NATIVE_FILEINFO_OK",
  "NATIVE_FILEINFO_ERROR", "SOURCE_ORIGINAL", "SOURCE_MAPPED",
  "SOURCE_SYNTHETIC_RESPONSE", "NATIVE_FILEINFO_SLOW", "NATIVE_FILEINFO_WAIT",
  "SOURCE_BATCH_ORIGINAL",
  "RESOLVE_TIMEOUT", "RESOLVE_START", "RESOLVE_ABORTED", "GRANT_RECEIVED",
  "NATIVE_TOGGLE_PLAYER_OBSERVER_READY", "NATIVE_TOGGLE_RELOAD_DEFERRED",
  "NATIVE_TOGGLE_RELOAD_REQUEST", "NATIVE_TOGGLE_RELOAD_OK",
  "NATIVE_TOGGLE_RELOAD_FAILED",
  "SOURCE_RECOVERY_SCHEDULED", "SOURCE_RECOVERY_RETRY",
  "SOURCE_RECOVERY_GRANTED", "SOURCE_RECOVERY_RELOAD_OK",
  "SOURCE_RECOVERY_RELOAD_FAILED", "SOURCE_RECOVERY_EXHAUSTED",
  "SOURCE_RECOVERY_NO_LONGER_CURRENT", "RESOLVE_BACKGROUND_TIMEOUT",
  "RESOLVE_BACKGROUND_TRANSIENT",
  "SOURCE_DEFERRED_WAITING", "SOURCE_DEFERRED_PROMOTED",
  "SOURCE_DEFERRED_EXPIRED", "SOURCE_DEFERRED_SKIPPED",
  "NATIVE_TOGGLE_RELOAD_DIFFERENT_TRACK",
  "SOURCE_EXPIRED_NATIVE_403",
  "SOURCE_UNFETCHED_CURRENT_REFRESH",
  "SOURCE_UNFETCHED_CURRENT_REFRESH_OK",
  "SOURCE_UNFETCHED_CURRENT_REFRESH_DEFERRED",
  "PLAYER_CURRENT_SOURCE_UNFETCHED_RECOVERY",
  "SOURCE_BATCH_REQUEST", "SOURCE_BATCH_MAPPED", "CACHE_HIT",
  "MEDIA_PLAY", "MEDIA_PAUSE", "MEDIA_PLAYING", "MEDIA_ERROR",
  "MEDIA_WAITING", "MEDIA_STALLED", "MEDIA_SEEKING", "MEDIA_SEEKED",
  "MEDIA_ENDED", "MEDIA_REQUEST_SEEN", "MEDIA_HTTP_OK",
  "MEDIA_HTTP_FAILED", "MEDIA_HTTP_UNVERIFIED", "STATE_ENABLED",
  "STATE_DISABLED", "STATE_UNREACHABLE", "RENDERER_STATE_ON",
  "RENDERER_STATE_OFF", "FILEINFO_SHAPE_FILE", "FILEINFO_SHAPE_DOWNLOAD",
  "FILEINFO_SHAPE_MISSING", "BATCH_FILEINFO_ERROR",
  "AUDIO_PROBE_STARTED", "AUDIO_PROBE_HTTP_PARTIAL", "AUDIO_PROBE_HTTP_FULL",
  "AUDIO_PROBE_HTTP_FORBIDDEN", "AUDIO_PROBE_HTTP_UNAUTHORIZED",
  "AUDIO_PROBE_HTTP_NOT_FOUND", "AUDIO_PROBE_HTTP_OTHER",
  "AUDIO_PROBE_MIME_MPEG", "AUDIO_PROBE_MIME_MPFOUR", "AUDIO_PROBE_MIME_OTHER",
  "AUDIO_PROBE_BYTES_MPTHREE", "AUDIO_PROBE_BYTES_MPFOUR",
  "AUDIO_PROBE_BYTES_OTHER", "AUDIO_PROBE_BODY_UNAVAILABLE",
  "AUDIO_PROBE_FETCH_BLOCKED", "AUDIO_PROBE_TIMEOUT",
  "AUDIO_PROBE_UNAVAILABLE", "AUDIO_CSP_BLOCKED",
  // These are Chromium/Electron player engine events, not the 32-byte probe.
  "PLAYER_ENGINE_STARTED", "PLAYER_ENGINE_PAUSED", "PLAYER_ENGINE_FAST_PAUSE",
  "PLAYER_AUDIO_AUDIBLE", "PLAYER_AUDIO_SILENT", "PLAYER_WITNESS_UNAVAILABLE",
  "AUDIO_URL_RESOURCE_UNATTRIBUTED",
  "FILEINFO_NATIVE_KEY_FIELD", "FILEINFO_NATIVE_IV_FIELD",
  "FILEINFO_NATIVE_URLS_ARRAY", "FILEINFO_NATIVE_URLS_OTHER",
  "FILEINFO_NATIVE_CODEC_MP3", "FILEINFO_NATIVE_CODEC_AAC",
  "FILEINFO_NATIVE_CODEC_OTHER", "FILEINFO_NATIVE_TRANSPORT_FIELD",
  "PLAYER_CDP_READY", "PLAYER_CDP_UNAVAILABLE", "PLAYER_CDP_DETACHED",
  "PLAYER_CDP_PIPELINE_ERROR", "PLAYER_CDP_ERROR_MESSAGE",
  "PLAYER_CDP_EVENT_START", "PLAYER_CDP_EVENT_PAUSE",
  "PLAYER_CDP_EVENT_PIPELINE_ERROR", "PLAYER_CDP_STATE_PLAYING",
  "PLAYER_CDP_STATE_NOT_PLAYING",
  // Passive current-player evidence: never logs URL/tokens.
  "PLAYER_DECODER_CELIKOM_SOURCE_MATCHED",
  "PLAYER_DECODER_CELIKOM_PIPELINE_ERROR",
  "PLAYER_CURRENT_SOURCE_LEFT_CELIKOM", "PLAYER_CURRENT_NATIVE_VOLUME_DROP",
  "NATIVE_ELECTRON_EVENT_LOOP_STALL", "NATIVE_ELECTRON_MEMORY_HIGH",
  "PLAYER_URL_MATCH", "PLAYER_URL_QUERY_MISSING", "PLAYER_URL_QUERY_CHANGED",
  "PLAYER_URL_EXPECTATION_MISSING", "PLAYER_URL_EXPIRED_AT_REQUEST",
  "PLAYER_URL_SIGNED_FIELDS_INTACT",
  "PLAYER_403_JSON", "PLAYER_403_HTML", "PLAYER_403_OTHER",
  "PLAYER_403_PHP_INVALID_AUDIO_TOKEN", "PLAYER_403_PHP_ACCESS_DENIED",
  "PLAYER_403_JSON_UNCLASSIFIED",
  "PLAYER_NET_READY", "PLAYER_NET_UNAVAILABLE", "PLAYER_NET_REQUEST",
  "PLAYER_NET_GET", "PLAYER_NET_HEAD", "PLAYER_NET_METHOD_OTHER",
  "PLAYER_NET_MEDIA", "PLAYER_NET_FETCH", "PLAYER_NET_XHR",
  "PLAYER_NET_TYPE_OTHER", "PLAYER_NET_HTTP_PARTIAL", "PLAYER_NET_HTTP_FULL",
  "PLAYER_NET_HTTP_FORBIDDEN", "PLAYER_NET_HTTP_UNAUTHORIZED",
  "PLAYER_NET_HTTP_OTHER", "PLAYER_NET_FINISHED",
  "PLAYER_NET_FAILED", "PLAYER_NET_CORS_BLOCKED",
  "PLAYER_NET_CORS_CREDENTIALS", "PLAYER_NET_CORS_PREFLIGHT",
  "PLAYER_NET_CSP_BLOCKED", "PLAYER_AUDIO_RESOURCE_TIMING_SEEN",
  // Correlation requires ALL native requests, not the first occurrence only.
  "PLAYER_URL_MATCH", "PLAYER_URL_QUERY_MISSING", "PLAYER_URL_QUERY_CHANGED",
  "PLAYER_URL_EXPECTATION_MISSING", "PLAYER_URL_EXPIRED_AT_REQUEST",
  "PLAYER_URL_SIGNED_FIELDS_INTACT",
  "PLAYER_403_JSON", "PLAYER_403_HTML", "PLAYER_403_OTHER",
  "PLAYER_403_PHP_INVALID_AUDIO_TOKEN", "PLAYER_403_PHP_ACCESS_DENIED",
  "PLAYER_403_JSON_UNCLASSIFIED"]);
function note(code, trackId = null, idKind = "track") {
  if (!/^[A-Z0-9_]{3,48}$/.test(code)) return;
  const id = typeof trackId === "string" && /^[1-9][0-9]{0,17}$/.test(trackId)
    ? trackId : null;
  if (!noisy.has(code) && logged.has(code)) return;
  if (!noisy.has(code)) logged.add(code);
  const line = new Date().toISOString() + "|" + code +
    (id ? "|" + (idKind === "resource_id" ? "resource_id" : "track") + "=" + id : "") + "\n";
  recent.push(line);
  if (recent.length > 256) recent.shift();
  if (process.env.LOCALAPPDATA) {
    try {
      fs.mkdirSync?.(nativeDirectory, { recursive: true });
      let existingSize = 0;
      try { existingSize = fs.statSync(nativeFile).size; } catch {}
      if (existingSize > 384 * 1024) {
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
function localRequest(token, route, method = "GET", payload = null, timeoutMs = 1000) {
  return new Promise(resolve => {
    const body = payload == null ? null : JSON.stringify(payload);
    if (!token || typeof route !== "string" || !route.startsWith("/v1/")) {
      resolve(null); return;
    }
    const request = http.request({
      host: "127.0.0.1", port: 21471, path: route, method, timeout: timeoutMs,
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
  // W61: short bounded local-only state poll to reduce time from UI click
  // to the native source refresh. Per-view tick is serialized (busy WeakSet)
  // and this never speeds up the actual Yandex media source download.
  if (now - (lastStateAt.get(view) || 0) < 260) return;
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
  const previousOrigin = nativeAudioOrigins.get(view);
  if (!safeState.enabled || !safeState.signedIn || previousOrigin !== safeState.apiOrigin) {
    nativeExpectedAudio.delete(view);
    verifiedDecoderSource.delete(view);
    nativeMediaHttpSuccess.delete(view);
  }
  nativeAudioOrigins.set(view, safeState.apiOrigin);
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
  // The original request remains fast so Next is not blocked. Background
  // current-track recovery is the ONLY call allowed a longer local deadline.
  const response = await localRequest(token,
    "/v1/resolve?track_id=" + encodeURIComponent(request.trackId),
    "GET", null, request.recovery === true ? 2700 : 1000);
  if (response != null) note("LOCAL_RESOLVE_REPLY", request.trackId);
  else note("RESOLVE_BRIDGE_FAILURE", request.trackId);
  const transient = response == null || response.retryable === true;
  // Marker is not a signed audio grant and never bypasses validation. The
  // renderer must not cache a transient miss as "track unavailable".
  const grant = transient ? {transient:true} :
    response?.found === true ? response.grant ?? null : null;
  note(!transient && grant ? "GRANT_FOUND" : "GRANT_MISS", request.trackId);
  // W52: keep the exact grant URL ONLY in process memory for comparison with
  // the native player request. Never log, hash, serialize, or persist it.
  rememberExpectedAudio(view, grant);
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
  observeNativePlayback(view);
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
      // A failed *prefetched* file-info may be played long afterwards.
      // Check the observed current Yandex queue entity before assuming the
      // old source is still good. Recovery may reload that entity only.
      await execute(view, ";window.__celikomBridgeNativeCheckDeferred?.()||false");
      const rendererStatus = await execute(view, ";window.__celikomBridgeNativeStatus?.()||'ORIGINAL'");
      const observed = await execute(view,
        ";window.__celikomBridgeNativeCurrentTrack?.()||null");
      const trackId = typeof observed?.id === "string" &&
        /^[1-9][0-9]{0,23}$/.test(observed.id) ? observed.id : null;
      const previous = lastStatus.get(view);
      const checkedAt = Date.now();
      const firstSeenAt = previous?.trackId === trackId && previous?.firstSeenAt
        ? previous.firstSeenAt : checkedAt;
      // Only matching current decoder kUrl + kIsPlaying is evidence of our
      // source reaching the actual player. HTTP 206 or a mapped file-info
      // is NOT enough for the green "Подмена активна" label.
      const decoder = verifiedDecoderSource.get(view);
      const decoderConfirmed = trackId && decoder?.trackId === trackId &&
        decoder.at >= firstSeenAt - 2000 &&
        checkedAt - decoder.at < 600000;
      const status = rendererStatus === "NATIVE_MAPPING_ACCEPTED" && decoderConfirmed
        ? "NATIVE_SOURCE_VERIFIED" : rendererStatus;
      if (rendererStatus === "NATIVE_MAPPING_ACCEPTED" && trackId &&
          nativeNetworkObserversReady.has(view) &&
          checkedAt - firstSeenAt >= 3500 &&
          checkedAt - firstSeenAt <= 16000) {
        const expected = [...(nativeExpectedAudio.get(view)?.values() || [])]
          .some(entry => entry.yandexTrackId === trackId &&
            entry.expiresAt > checkedAt && entry.recordedAt >= firstSeenAt - 5000);
        const mediaAt = nativeMediaHttpSuccess.get(view)?.get(trackId) || 0;
        const fetched = mediaAt >= firstSeenAt - 8000;
        let attempted = nativeUnfetchedReloadAttempt.get(view);
        if (!attempted) {
          attempted = new Map();
          nativeUnfetchedReloadAttempt.set(view, attempted);
        }
        const lastAttempt = attempted.get(trackId) || 0;
        if (expected && !fetched && !decoderConfirmed &&
            (!lastAttempt || checkedAt - lastAttempt >= 120000)) {
          if (attempted.size >= 32)
            attempted.delete(attempted.keys().next().value);
          attempted.set(trackId, checkedAt);
          // The renderer rechecks exact CURRENT track and its Start state
          // before requesting a single vendor reloadEntity. No other track,
          // seek, pause or media transport is controlled by this observer.
          void execute(view,
            ";window.__celikomBridgeNativeRefreshUnfetched?.(" +
            JSON.stringify(trackId) + ")").then(ok => {
              if (ok === true && validView(view))
                note("PLAYER_CURRENT_SOURCE_UNFETCHED_RECOVERY", trackId);
            });
        }
      }
      // Validate once more at the native boundary. None of the free-form
      // metadata ever enters the diagnostic event stream or public API.
      const cleanText = value => typeof value === "string" &&
        value.length <= 720 && !/[\u0000-\u001f\u007f]/.test(value)
          ? value.trim().slice(0, 180) : "";
      const title = trackId ? cleanText(observed.title) : "";
      const artist = trackId ? cleanText(observed.artist) : "";
      const durationMs = trackId &&
        Number.isSafeInteger(observed.durationMs) &&
        observed.durationMs >= 1000 && observed.durationMs <= 86400000
          ? observed.durationMs : null;
      lastStatus.set(view, { value: status, trackId, title, artist, durationMs,
        at: now, firstSeenAt });
      if ((status === "NATIVE_CONNECTED" || status === "NATIVE_MAPPING_ACCEPTED" ||
           status === "NATIVE_SOURCE_VERIFIED" ||
           status === "NATIVE_RECOVERING" || status === "NATIVE_SOURCE_FAILED" ||
           status === "ORIGINAL") &&
          (!previous || status !== previous.value || trackId !== previous.trackId ||
           title !== previous.title || artist !== previous.artist ||
           durationMs !== previous.durationMs)) {
        await localRequest(token, "/v1/heartbeat", "POST",
          {trackId, status, title, artist, durationMs});
      }
    }
  } finally {
    busy.delete(view);
  }
}
// W48: Observe the actual Electron media engine. The old AUDIO_PROBE 206
// only confirmed 32 bytes of MP3 were reachable; it never proved playback.
// No media commands, no WebAudio monkeypatches, no URLs/account data logged.
const playbackWitnesses = new WeakSet();
const nativeAudioOrigins = new WeakMap();
const nativeExpectedAudio = new WeakMap();
const nativeMediaHttpSuccess = new WeakMap();
const nativeNetworkObserversReady = new WeakSet();
const nativeUnfetchedReloadAttempt = new WeakMap();
const verifiedDecoderSource = new WeakMap();
const AUDIO_RESOURCE_PATH = /^\/api\/v1\/audio\/([1-9][0-9]{0,17})$/;
function rememberExpectedAudio(view, grant) {
  if (!validView(view) || grant?.approved !== true ||
      grant?.entitled !== true || typeof grant.audioUrl !== "string" ||
      typeof grant.trackId !== "string" ||
      !/^[1-9][0-9]{0,23}$/.test(grant.trackId)) return;
  try {
    const expectedOrigin = nativeAudioOrigins.get(view);
    const url = new URL(grant.audioUrl);
    const resourceId = AUDIO_RESOURCE_PATH.exec(url.pathname)?.[1];
    const expiresAt = grant.expiresAt;
    const now = Date.now();
    if (!expectedOrigin || url.protocol !== "https:" ||
        url.origin !== expectedOrigin || !resourceId ||
        url.username || url.password || url.hash ||
        !Number.isSafeInteger(expiresAt) || expiresAt <= now ||
        expiresAt > now + 1800000 ||
        !/^[a-f0-9]{64}$/.test(url.searchParams.get("token") || "") ||
        !/^[0-9]{9,12}$/.test(url.searchParams.get("expires") || "") ||
        Number(url.searchParams.get("expires")) * 1000 !== expiresAt ||
        (url.searchParams.has("sid") &&
          !/^[1-9][0-9]{0,17}$/.test(url.searchParams.get("sid") || "")) ||
        new Set(url.searchParams.keys()).size !== [...url.searchParams.keys()].length ||
        [...url.searchParams.keys()].some(k => !["token","expires","sid","variant"].includes(k)) ||
        url.searchParams.has("variant") !== (grant.gainApplied === true) ||
        (url.searchParams.has("variant") &&
          url.searchParams.get("variant") !== "windows_gain_v1"))
      return;
    let entries = nativeExpectedAudio.get(view);
    if (!entries) { entries = new Map(); nativeExpectedAudio.set(view, entries); }
    for (const [key, item] of entries) if (item.expiresAt <= now) entries.delete(key);
    if (entries.size >= 32) entries.delete(entries.keys().next().value);
    // Yandex track ID remains private metadata and is never used as an audio path ID.
    entries.set(resourceId, { href: url.origin + url.pathname + url.search,
      expiresAt, yandexTrackId: grant.trackId, recordedAt: now });
  } catch { /* Invalid grant is handled by the existing renderer validator. */ }
}
function classifyPlayerUrl(view, resourceId, actualUrl) {
  const entry = nativeExpectedAudio.get(view)?.get(resourceId);
  if (!entry) return "PLAYER_URL_EXPECTATION_MISSING";
  if (entry.expiresAt <= Date.now()) return "PLAYER_URL_EXPIRED_AT_REQUEST";
  const actual = actualUrl.origin + actualUrl.pathname + actualUrl.search;
  if (actual === entry.href) return "PLAYER_URL_MATCH";
  if (!actualUrl.search) return "PLAYER_URL_QUERY_MISSING";
  try {
    const expected = new URL(entry.href);
    const fields = ["token", "expires", "sid", "variant"];
    const parsed = actualUrl.searchParams;
    // PHP checks the signed fields, not their URL order. An unrelated extra
    // query field does not by itself break the HMAC. Be conservative about
    // duplicated signed fields (PHP and URLSearchParams can differ).
    const intact = fields.every(key => {
      const exp = expected.searchParams.getAll(key);
      const got = parsed.getAll(key);
      return exp.length === got.length && exp.length <= 1 &&
        (exp.length === 0 || exp[0] === got[0]);
    });
    if (intact) return "PLAYER_URL_SIGNED_FIELDS_INTACT";
  } catch {}
  return "PLAYER_URL_QUERY_CHANGED";
}
// Read only a real native GET's tiny JSON *403* on our exact audio route.
// Never request bodies of successful audio, other routes, or Yandex resources;
// never log body/error text, only two hardcoded PHP denial enums.
async function classifyAudioDenial(debug, requestId, id, eligible) {
  if (!eligible) return;
  try {
    const response = await debug.sendCommand("Network.getResponseBody", { requestId });
    if (response?.base64Encoded || typeof response?.body !== "string" ||
        response.body.length > 160) return;
    const body = JSON.parse(response.body);
    if (!body || typeof body !== "object" || Array.isArray(body) ||
        Object.keys(body).length !== 1) return;
    if (body.error === "invalid_audio_token")
      note("PLAYER_403_PHP_INVALID_AUDIO_TOKEN", id, "resource_id");
    else if (body.error === "access_denied")
      note("PLAYER_403_PHP_ACCESS_DENIED", id, "resource_id");
    else note("PLAYER_403_JSON_UNCLASSIFIED", id, "resource_id");
  } catch { /* Read-only CDP body access may be unavailable; do not interfere. */ }
}
function observeNativePlayback(view) {
  if (!validView(view) || playbackWitnesses.has(view)) return;
  playbackWitnesses.add(view);
  if (typeof view.on !== "function") {
    note("PLAYER_WITNESS_UNAVAILABLE");
    return;
  }
  // CDP Media domain is a passive native decoder witness. Never call
  // Network.getResponseBody, Runtime.evaluate, fetch, play, pause or seek.
  // When DevTools are already open or another client owns the debugger,
  // fail open and leave the original player entirely untouched.
  const debug = view.debugger;
  // Only matching *current* decoder URLs can corroborate a CELIKOM source.
  // Prefetch GETs, grant delivery, HTTP 206 and renderer status do not count.
  const decoderPlayers = new Map();
  const capturePlayerProperties = params => {
    const id = params?.playerId;
    if (typeof id !== "string" || id.length < 1 || id.length > 128 ||
        !/^[a-zA-Z0-9_-]+$/.test(id) || !Array.isArray(params?.properties)) return;
    if (!decoderPlayers.has(id) && decoderPlayers.size >= 32)
      decoderPlayers.delete(decoderPlayers.keys().next().value);
    const prev = decoderPlayers.get(id) || {
      playing:false, sourceTrackId:null, evidenceReportedFor:null,
      lastVolume:null, volumeTrackId:null
    };
    for (const prop of params.properties.slice(0, 30)) {
      if (prop?.name === "kUrl") {
        const wasCurrentCelikom = prev.playing && !!prev.sourceTrackId &&
          prev.sourceTrackId === lastStatus.get(view)?.trackId;
        prev.sourceTrackId = null;
        prev.evidenceReportedFor = null;
        verifiedDecoderSource.delete(view);
        if (typeof prop.value !== "string" || prop.value.length > 4096) continue;
        try {
          const actual = new URL(prop.value);
          const expectedOrigin = nativeAudioOrigins.get(view);
          const resourceId = expectedOrigin && actual.origin === expectedOrigin &&
            !actual.username && !actual.password &&
            AUDIO_RESOURCE_PATH.exec(actual.pathname)?.[1];
          const expected = resourceId && nativeExpectedAudio.get(view)?.get(resourceId);
          const classification = resourceId && expected ?
            classifyPlayerUrl(view, resourceId, actual) : "";
          if (expected?.expiresAt > Date.now() &&
              (classification === "PLAYER_URL_MATCH" ||
               classification === "PLAYER_URL_SIGNED_FIELDS_INTACT"))
            prev.sourceTrackId = expected.yandexTrackId;
        } catch { /* Unknown native URL: no source evidence. */ }
        if (wasCurrentCelikom && !prev.sourceTrackId)
          note("PLAYER_CURRENT_SOURCE_LEFT_CELIKOM", lastStatus.get(view)?.trackId);
      } else if (prop?.name === "kVolume") {
        // Optional CDP property, not all Electron builds expose it. Only
        // track a real signed-current decoder, never log values or URLs.
        const currentId = lastStatus.get(view)?.trackId;
        const value = prop.value;
        const volume = typeof value === "string" &&
          /^(?:0(?:\\.\\d{1,6})?|1(?:\\.0{1,6})?)$/.test(value)
          ? Number(value) : null;
        if (volume !== null && currentId && prev.playing &&
            prev.sourceTrackId === currentId) {
          if (prev.volumeTrackId === currentId &&
              Number.isFinite(prev.lastVolume) &&
              volume < prev.lastVolume - 0.15)
            note("PLAYER_CURRENT_NATIVE_VOLUME_DROP", currentId);
          prev.volumeTrackId = currentId;
          prev.lastVolume = volume;
        }
      } else if (prop?.name === "kIsPlaying") {
        prev.playing = prop.value === "true";
        if (!prev.playing) {
          prev.evidenceReportedFor = null;
          prev.lastVolume = null;
          prev.volumeTrackId = null;
          verifiedDecoderSource.delete(view);
        }
      }
    }
    decoderPlayers.set(id, prev);
    const current = lastStatus.get(view)?.trackId;
    if (prev.playing && prev.sourceTrackId && current === prev.sourceTrackId &&
        prev.evidenceReportedFor !== current) {
      prev.evidenceReportedFor = current;
      verifiedDecoderSource.set(view, {trackId: current, at: Date.now()});
      note("PLAYER_DECODER_CELIKOM_SOURCE_MATCHED", current);
    }
  };
  if (debug && typeof debug.attach === "function" &&
      typeof debug.sendCommand === "function" &&
      typeof debug.isAttached === "function" &&
      !(typeof view.isDevToolsOpened === "function" && view.isDevToolsOpened()) &&
      !debug.isAttached()) {
    try {
      debug.attach("1.3");
      const mediaRequests = new Map();
      // W50 native CDP Network observer: NO request/response bodies, URL,
      // headers, token, cookies, or personal data enter owner diagnostics.
      // The W48 independent probe has been disabled; matched GETs now
      // originate from Yandex itself (possibly its prefetcher, not sound).
      debug.on("message", (_event, method, params) => {
        if (!validView(view)) return;
        const requestId = typeof params?.requestId === "string" &&
          params.requestId.length < 160 ? params.requestId : null;
        if (method === "Network.requestWillBeSent" && requestId) {
          const origin = nativeAudioOrigins.get(view);
          let id = null, url = null;
          try {
            const u = new URL(params?.request?.url);
            if (origin && u.origin === origin && !u.username && !u.password) {
              id = AUDIO_RESOURCE_PATH.exec(u.pathname)?.[1] || null;
              if (id) url = u;
            }
          } catch {}
          if (!id) return;
          if (mediaRequests.size >= 64)
            mediaRequests.delete(mediaRequests.keys().next().value);
          const m = params?.request?.method;
          const classify = classifyPlayerUrl(view, id, url);
          const expected = nativeExpectedAudio.get(view)?.get(id);
          mediaRequests.set(requestId, { id, method: m, forbiddenJson: false,
            forbiddenJsonLength: null, expiredAtRequest:
              classify === "PLAYER_URL_EXPIRED_AT_REQUEST",
            trackId: expected?.yandexTrackId || null,
            requestType: params?.type || "" });
          note("PLAYER_NET_REQUEST", id, "resource_id");
          note(classify, id, "resource_id");
          note(m === "GET" ? "PLAYER_NET_GET" :
            m === "HEAD" ? "PLAYER_NET_HEAD" : "PLAYER_NET_METHOD_OTHER", id, "resource_id");
          note(params?.type === "Media" ? "PLAYER_NET_MEDIA" :
            params?.type === "Fetch" ? "PLAYER_NET_FETCH" :
            params?.type === "XHR" ? "PLAYER_NET_XHR" : "PLAYER_NET_TYPE_OTHER", id, "resource_id");
          return;
        }
        if (requestId && mediaRequests.has(requestId)) {
          const entry = mediaRequests.get(requestId), id = entry.id;
          if (method === "Network.responseReceived") {
            const status = Number(params?.response?.status);
            if ((status === 206 || status === 200) &&
                entry.method === "GET" && entry.requestType === "Media" &&
                typeof entry.trackId === "string") {
              let successes = nativeMediaHttpSuccess.get(view);
              if (!successes) {
                successes = new Map();
                nativeMediaHttpSuccess.set(view, successes);
              }
              if (successes.size >= 32)
                successes.delete(successes.keys().next().value);
              successes.set(entry.trackId, Date.now());
            }
            note(status === 206 ? "PLAYER_NET_HTTP_PARTIAL" :
              status === 200 ? "PLAYER_NET_HTTP_FULL" :
              status === 403 ? "PLAYER_NET_HTTP_FORBIDDEN" :
              status === 401 ? "PLAYER_NET_HTTP_UNAUTHORIZED" :
              "PLAYER_NET_HTTP_OTHER", id, "resource_id");
            if (status === 403) {
              // W76: a confirmed expired, previously signed media GET can
              // mean Yandex is playing its censored fallback. Recheck only
              // the current track: the renderer validates identity itself.
              if (entry.method === "GET" && entry.expiredAtRequest &&
                  /^[1-9][0-9]{0,23}$/.test(entry.trackId || "")) {
                void execute(view, ";window.__celikomBridgeNativeRecoverExpired?.(" +
                  JSON.stringify(entry.trackId) + ")");
              }
              const headers = params?.response?.headers || {};
              const contentType = Object.entries(headers).find(([k]) =>
                k.toLowerCase() === "content-type")?.[1];
              const ct = typeof contentType === "string" ? contentType.toLowerCase() : "";
              const json = /^application\/json(?:\s*;|\s*$)/.test(ct);
              const html = /^text\/html(?:\s*;|\s*$)/.test(ct);
              note(json ? "PLAYER_403_JSON" : html ? "PLAYER_403_HTML" :
                "PLAYER_403_OTHER", id, "resource_id");
              const rawLength = Object.entries(headers).find(([k]) =>
                k.toLowerCase() === "content-length")?.[1];
              const length = rawLength === undefined ? null : Number(rawLength);
              entry.forbiddenJson = entry.method === "GET" && json &&
                (length === null || (Number.isSafeInteger(length) && length <= 160));
              entry.forbiddenJsonLength = length;
            }
            return;
          }
          if (method === "Network.loadingFailed") {
            note("PLAYER_NET_FAILED", id, "resource_id");
            const cors = String(params?.corsErrorStatus?.corsError || "");
            if (cors) {
              note("PLAYER_NET_CORS_BLOCKED", id, "resource_id");
              if (/InvalidAllowCredentials|WildcardOriginNotAllowed/i.test(cors))
                note("PLAYER_NET_CORS_CREDENTIALS", id, "resource_id");
              else if (/Preflight/i.test(cors))
                note("PLAYER_NET_CORS_PREFLIGHT", id, "resource_id");
            } else if (params?.blockedReason === "csp")
              note("PLAYER_NET_CSP_BLOCKED", id, "resource_id");
            mediaRequests.delete(requestId);
            return;
          }
          if (method === "Network.loadingFinished") {
            note("PLAYER_NET_FINISHED", id, "resource_id");
            mediaRequests.delete(requestId);
            // Network.getResponseBody returns a full response; never ask for it
            // on an unknown or unbounded payload. A PHP error has tiny JSON.
            const encoded = params?.encodedDataLength;
            const knownLength = entry.forbiddenJsonLength;
            const bounded = Number.isSafeInteger(knownLength) ?
              knownLength >= 0 && knownLength <= 160 :
              Number.isFinite(encoded) && encoded >= 0 && encoded <= 4096;
            void classifyAudioDenial(debug, requestId, id, entry.forbiddenJson && bounded);
            return;
          }
        }

        if (method === "Media.playerDestroyed" &&
            typeof params?.playerId === "string") {
          const lost = decoderPlayers.get(params.playerId);
          if (lost?.sourceTrackId === verifiedDecoderSource.get(view)?.trackId)
            verifiedDecoderSource.delete(view);
          decoderPlayers.delete(params.playerId);
        }
        if (method === "Media.playerErrorsRaised" &&
            Array.isArray(params?.errors) && params.errors.length > 0) {
          note("PLAYER_CDP_PIPELINE_ERROR");
          // Only correlate an error to CELIKOM when the actual current signed
          // decoder source was observed; generic CDP errors remain unassigned.
          const player = typeof params?.playerId === "string" ?
            decoderPlayers.get(params.playerId) : null;
          const currentTrack = lastStatus.get(view)?.trackId;
          if (player?.sourceTrackId && player.sourceTrackId === currentTrack)
            note("PLAYER_DECODER_CELIKOM_PIPELINE_ERROR", currentTrack);
        }
        else if (method === "Media.playerMessagesLogged" &&
            Array.isArray(params?.messages) &&
            params.messages.some(x => x?.level === "error"))
          note("PLAYER_CDP_ERROR_MESSAGE");
        else if (method === "Media.playerEventsAdded" &&
            Array.isArray(params?.events)) {
          for (const item of params.events.slice(0, 30)) {
            const value = String(item?.value || "").slice(0, 256);
            // Fixed Chromium Media event enum names only, never log raw
            // potentially sensitive media error text or source URLs.
            if (/\bkPlay\b/.test(value)) note("PLAYER_CDP_EVENT_START");
            else if (/\bkPause\b/.test(value)) note("PLAYER_CDP_EVENT_PAUSE");
            else if (/\bkPipelineError\b/.test(value))
              note("PLAYER_CDP_EVENT_PIPELINE_ERROR");
          }
        } else if (method === "Media.playerPropertiesChanged" &&
            Array.isArray(params?.properties)) {
          capturePlayerProperties(params);
          for (const prop of params.properties.slice(0, 30)) {
            if (prop?.name !== "kIsPlaying") continue;
            if (prop.value === "true") note("PLAYER_CDP_STATE_PLAYING");
            if (prop.value === "false") note("PLAYER_CDP_STATE_NOT_PLAYING");
          }
        }
      });
      debug.on("detach", () => { if (validView(view)) note("PLAYER_CDP_DETACHED"); });
      Promise.resolve(debug.sendCommand("Media.enable")).then(
        () => { if (validView(view)) note("PLAYER_CDP_READY"); },
        () => {
          if (validView(view)) note("PLAYER_CDP_UNAVAILABLE");
          try { if (debug.isAttached()) debug.detach(); } catch {}
        });
      // Passive read-only recording of status and request destination class;
      // Network is NOT intercepted, requests are never modified or retried.
      Promise.resolve(debug.sendCommand("Network.enable")).then(
        () => {
          if (validView(view)) {
            nativeNetworkObserversReady.add(view);
            note("PLAYER_NET_READY");
          }
        },
        () => { if (validView(view)) note("PLAYER_NET_UNAVAILABLE"); });
    } catch {
      note("PLAYER_CDP_UNAVAILABLE");
    }
  } else note("PLAYER_CDP_UNAVAILABLE");
  let lastStarted = 0;
  view.on("media-started-playing", () => {
    if (!validView(view)) return;
    lastStarted = Date.now();
    note("PLAYER_ENGINE_STARTED");
  });
  view.on("media-paused", () => {
    if (!validView(view)) return;
    note("PLAYER_ENGINE_PAUSED");
    if (lastStarted && Date.now() - lastStarted < 1500)
      note("PLAYER_ENGINE_FAST_PAUSE");
    lastStarted = 0;
  });
  view.on("audio-state-changed", (_event, audible) => {
    if (!validView(view) || typeof audible !== "boolean") return;
    note(audible ? "PLAYER_AUDIO_AUDIBLE" : "PLAYER_AUDIO_SILENT");
  });
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
let lastHostPulseAt = Date.now();
let lastResourceSampleAt = Date.now();
const timer = setInterval(() => {
  const now = Date.now();
  const elapsed = now - lastHostPulseAt;
  // A small, read-only heartbeat for #53. No process names, stats,
  // account identifiers, privileged APIs or raw values enter diagnostics.
  // Ignore sleep/resume gaps; this is NOT proof of a whole-PC slowdown.
  if (elapsed > 4000 && elapsed < 60000)
    note("NATIVE_ELECTRON_EVENT_LOOP_STALL");
  lastHostPulseAt = now;
  if (now - lastResourceSampleAt >= 30000) {
    lastResourceSampleAt = now;
    try {
      const memory = typeof process.memoryUsage === "function"
        ? process.memoryUsage() : null;
      if (memory && Number.isFinite(memory.rss) &&
          memory.rss > 700 * 1024 * 1024)
        note("NATIVE_ELECTRON_MEMORY_HIGH");
    } catch {}
  }
  const views = webContents.getAllWebContents();
  if (views.length) note("WEB_CONTENTS_PRESENT");
  for (const view of views) void tick(view);
}, 180);
if (timer.unref) timer.unref();
