"use strict";
const CELIKOM_NATIVE_VERSION = "0.24.32";

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
let tokenCache = "", tokenCacheAt = 0;
let tokenCacheMtime = -1, tokenCacheCtime = -1, tokenCacheSize = -1;
let tokenFileRevision = 0;
const noisy = new Set(["TRACK_CHANGED", "RESOLVE_REQUEST", "GRANT_FOUND", "GRANT_MISS",
  "GRANT_DELIVERED", "GRANT_DELIVERY_FAILED", "LOCAL_RESOLVE_REPLY",
  "RESOLVE_BRIDGE_FAILURE", "RESOLVE_TRANSIENT", "NATIVE_FILEINFO_REQUEST", "NATIVE_FILEINFO_OK",
  "NATIVE_FILEINFO_ERROR", "SOURCE_ORIGINAL", "SOURCE_MAPPED",
  "SOURCE_SYNTHETIC_RESPONSE", "NATIVE_FILEINFO_SLOW", "NATIVE_FILEINFO_WAIT",
  "SOURCE_BATCH_ORIGINAL", "SOURCE_ACTIVE_REPLACEMENT", "SOURCE_UNKNOWN",
  "RESOLVE_TIMEOUT", "RESOLVE_START", "RESOLVE_ABORTED", "GRANT_RECEIVED",
  "NATIVE_ORIGINAL_SOURCE_NO_RELOAD", "NATIVE_UNKNOWN_SOURCE_NO_RELOAD",
  "NATIVE_STATE_CURRENT_SOURCE_UNKNOWN", "NATIVE_CURRENT_SOURCE_REVALIDATE",
  "NATIVE_CURRENT_SOURCE_REVALIDATE_STALE", "NATIVE_ORIGINAL_SOURCE_RESTORE",
  "NATIVE_ORIGINAL_SOURCE_RESTORED", "NATIVE_ORIGINAL_SOURCE_RESTORE_DEFERRED",
  "NATIVE_ROUTE_RECOVERY_PAUSED", "NATIVE_ROUTE_RECOVERY_RESUMED",
  "NATIVE_ROUTE_RECOVERY_SOURCE_HELD", "NATIVE_ROUTE_RECOVERY_SOURCE_KEPT",
  "NATIVE_ROUTE_HOLD_NO_WITNESS", "NATIVE_ROUTE_HOLD_NOT_MAPPED",
  "NATIVE_ROUTE_HOLD_TRACK_CHANGED", "NATIVE_ROUTE_HOLD_NOT_PLAYING",
  "NATIVE_ROUTE_HOLD_EARLY_CLEAR", "NATIVE_ROUTE_HOLD_NO_PRIOR_MAP",
  "NATIVE_ROUTE_HOLD_TRACK_CHANGED_RECAPTURED", "NATIVE_ROUTE_RECOVERY_TRACK_DEFERRED",
  "NATIVE_CURRENT_TRACK_APPROVAL_REVALIDATE", "NATIVE_CURRENT_TRACK_APPROVAL_REVALIDATE_MISS",
  "NATIVE_CURRENT_TRACK_APPROVAL_REVALIDATE_STALE", "NATIVE_CURRENT_TRACK_APPROVAL_RELOAD",
  "NATIVE_CURRENT_TRACK_APPROVAL_RELOAD_OK", "NATIVE_CURRENT_TRACK_APPROVAL_RELOAD_DEFERRED",
  "NATIVE_REPLACEMENT_SOURCE_RELOAD", "NATIVE_REPLACEMENT_SOURCE_RELOAD_OK",
  "NATIVE_REPLACEMENT_SOURCE_RELOAD_DEFERRED",
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
  "PLAYER_CURRENT_GAIN_VARIANT_URL_SELECTED", "PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING",
  "SOURCE_RECOVERY_DECODER_ALREADY_PLAYING",
  "NATIVE_ELECTRON_EVENT_LOOP_STALL", "NATIVE_ELECTRON_MEMORY_HIGH",
  "NATIVE_ELECTRON_CPU_HIGH",
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
const lastTokenRevision = new WeakMap();
const lastDeliveredState = new WeakMap();
// Only an actual renderer delivery may acknowledge a resumed route.
const deliveredRecoveryEpoch = new WeakMap();
const lastDiagPoll = new WeakMap();
// W141: one actual audible Yandex window owns playback identity; a hidden
// renderer or a stale window cannot overwrite the owner-facing heartbeat.
const viewActivity = new WeakMap();
let selectedPlaybackView = null;
let selectionGeneration = 0;
const heartbeatInstanceId = "w23-" + Date.now().toString(36) + "-" +
  Math.random().toString(36).slice(2, 10);
let heartbeatSequence = 0;
const HEARTBEAT_INTERVAL_MS = 4000;
// Current-song metadata is local UI state, not the heartbeat cadence. Sample it
// quickly while keeping unchanged server heartbeats at the existing 4-second rate.
const PLAYBACK_STATE_SAMPLE_INTERVAL_MS = 500;
function activity(view) {
  let state = viewActivity.get(view);
  if (!state) {
    state = { audible: false, startedAt: 0, audibleAt: 0 };
    viewActivity.set(view, state);
  }
  return state;
}
// The Electron property is sometimes available before its event is delivered.
// Selection and playback-state reporting must use the same native evidence.
function nativeAudible(view) {
  try {
    if (typeof view.isCurrentlyAudible === "function") {
      const current = view.isCurrentlyAudible();
      // Both true AND false are fresher than a retained historic event.
      if (typeof current === "boolean") return current;
    }
  } catch {}
  return activity(view).audible === true;
}
function choosePlaybackView() {
  const eligible = webContents.getAllWebContents().filter(validView);
  const audible = eligible.filter(nativeAudible);
  let choice = null;
  if (audible.length === 1) choice = audible[0];
  else if (audible.length > 1) {
    const ranked = audible.map(view => ({view,at:activity(view).audibleAt}))
      .sort((a,b)=>b.at-a.at);
    if (ranked[0].at > 0 && ranked[0].at-ranked[1].at >= 350)
      choice = ranked[0].view;
  } else if (eligible.length === 1) choice = eligible[0];
  else if (eligible.length > 1) {
    // A newly started silent/paused session outranks an old retained view.
    // This resolves My Wave / Next switching before audio-state-changed fires.
    const recent = eligible.map(view => ({view,at:activity(view).startedAt}))
      .filter(x=>x.at>0 && Date.now()-x.at<15000)
      .sort((a,b)=>b.at-a.at);
    if (recent.length && (recent.length === 1 || recent[0].at-recent[1].at>=500))
      choice = recent[0].view;
    else if (selectedPlaybackView && eligible.includes(selectedPlaybackView))
      choice = selectedPlaybackView;
  }
  if (selectedPlaybackView !== choice) {
    selectedPlaybackView = choice;
    ++selectionGeneration;
  }
  return choice;
}
function heartbeatPayload(state) {
  return {...state, instanceId:heartbeatInstanceId, sequence:++heartbeatSequence};
}

function readToken() {
  const now = Date.now();
  if (now - tokenCacheAt < 1000) return tokenCache;
  tokenCacheAt = now;
  try {
    const stat = fs.statSync(capabilityFile);
    const mtime = Number(stat.mtimeMs) || 0;
    const ctime = Number(stat.ctimeMs) || 0;
    const size = Number(stat.size) || 0;
    if (mtime === tokenCacheMtime && ctime === tokenCacheCtime &&
        size === tokenCacheSize) return tokenCache;
    const value = fs.readFileSync(capabilityFile, "utf8").trim();
    tokenCache = /^[0-9a-f]{64}$/.test(value) ? value : "";
    tokenCacheMtime = mtime;
    tokenCacheCtime = ctime;
    tokenCacheSize = size;
    tokenFileRevision++;
    return tokenCache;
  } catch {
    if (tokenCache || tokenCacheMtime !== -1 || tokenCacheCtime !== -1 ||
        tokenCacheSize !== -1) tokenFileRevision++;
    tokenCache = "";
    tokenCacheMtime = -1;
    tokenCacheCtime = -1;
    tokenCacheSize = -1;
    return "";
  }
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
  // A fresh renderer document must receive state even if the previous one
  // had the same value cached for this webContents.
  lastDeliveredState.delete(view);
  deliveredRecoveryEpoch.delete(view);
  note("RENDERER_INJECTED");
  return true;
}
async function deliverState(view, safeState) {
  // Avoid repeated Electron IPC/renderer execution when the authoritative
  // bridge state has not changed. A newly injected document clears this cache.
  const stateKey = JSON.stringify(safeState);
  if (lastDeliveredState.get(view) === stateKey) return true;
  const ok = await execute(view,
    ";(()=>{if(!window.__celikomBridgeNativeSetState)return false;" +
    "window.__celikomBridgeNativeSetState(" + stateKey + ");return true})()");
  if (ok === true) {
    lastDeliveredState.set(view, stateKey);
    note("RENDERER_STATE_DELIVERED");
  }
  return ok === true;
}
function validNativeApiOrigin(value) {
  if (typeof value !== "string" || value.length > 256) return false;
  try {
    const uri = new URL(value);
    return uri.protocol === "https:" && uri.pathname === "/" &&
      !uri.username && !uri.password && !uri.search && !uri.hash &&
      uri.origin === value;
  } catch { return false; }
}
async function relayState(view, token, now) {
  // W61: short bounded local-only state poll to reduce time from UI click
  // to the native source refresh. Per-view tick is serialized (busy WeakSet)
  // and this never speeds up the actual Yandex media source download.
  if (now - (lastStateAt.get(view) || 0) < 300) return false;
  lastStateAt.set(view, now);
  let justEnabled = false;
  const state = await localRequest(token, "/v1/state");
  const stateAvailable = !!state && typeof state === "object" && !Array.isArray(state);
  if (stateAvailable) {
    note("LOCAL_STATE_OK");
    const active = state.enabled === true && state.signedIn === true;
    const previousActive = lastNativeState.get(view);
    if (previousActive !== active) {
      lastNativeState.set(view, active);
      note(active ? "STATE_ENABLED" : "STATE_DISABLED");
      justEnabled = active;
    }
  } else {
    // A failed poll invalidates the cached disabled state too. Keep the next
    // host pulse fast until the companion explicitly confirms OFF again.
    lastNativeState.delete(view);
    note("STATE_UNREACHABLE");
  }
  const previous = lastStatus.get(view);
  const apiOrigin = stateAvailable && validNativeApiOrigin(state.apiOrigin)
    ? state.apiOrigin : "";
  const rawRecoveryPending = stateAvailable &&
    state.networkRecoveryPending === true;
  const networkRecoveryPending = rawRecoveryPending &&
    state.signedIn === true && !!apiOrigin;
  const previousOrigin = nativeAudioOrigins.get(view);
  const originChanged = previousOrigin !== undefined &&
    previousOrigin !== apiOrigin;
  let recoveryHold = nativeRecoveryHolds.get(view);
  const recoveryHoldExpired = recoveryHold &&
    (!Number.isSafeInteger(recoveryHold.capturedAt) ||
     now < recoveryHold.capturedAt ||
     now - recoveryHold.capturedAt >= 600000);
  if (!networkRecoveryPending) {
    nativeRecoveryHolds.delete(view);
    recoveryHold = null;
    if (stateAvailable && state.enabled === true && state.signedIn === true &&
        !!apiOrigin && !originChanged) {
      nativeRecoveryHoldBlocked.delete(view);
    } else {
      // Stop, logout, denial, invalid state and origin changes must not reuse
      // a stale mapped-track hint on the next transient route transition.
      nativeRecoveryHoldBlocked.add(view);
    }
  } else if (originChanged || recoveryHoldExpired) {
    nativeRecoveryHolds.delete(view);
    recoveryHold = null;
    nativeRecoveryHoldBlocked.add(view);
  } else if (recoveryHold && justEnabled) {
    // Validate the actual Yandex player again immediately before allowing the
    // renderer to keep a mapped source. If Next happened during the handoff,
    // recapture only when the NEW exact current entity has its own mapping witness.
    const heldTrackId = recoveryHold.trackId;
    const observed = await execute(view,
      ";window.__celikomBridgeNativeCurrentTrack?.()||null");
    const observedId = typeof observed?.id === "string" &&
      /^[1-9][0-9]{0,23}$/.test(observed.id) ? observed.id : null;
    const canContinue = observed?.playbackState === "PLAYING" ||
      observed?.playbackState === "PAUSED";
    if (observedId !== heldTrackId || !canContinue) {
      const mappedId = observedId && canContinue
        ? await execute(view, ";window.__celikomBridgeNativeMappedCurrentTrackId?.()||''")
        : "";
      if (observedId && observedId !== heldTrackId && canContinue &&
          mappedId === observedId) {
        recoveryHold = {trackId:observedId, firstSeenAt:now, capturedAt:now};
        nativeRecoveryHolds.set(view, recoveryHold);
        nativeRecoveryHoldBlocked.delete(view);
        note("NATIVE_ROUTE_HOLD_TRACK_CHANGED_RECAPTURED", observedId);
      } else {
        nativeRecoveryHolds.delete(view);
        recoveryHold = null;
        nativeRecoveryHoldBlocked.add(view);
        note(observedId !== heldTrackId ? "NATIVE_ROUTE_HOLD_TRACK_CHANGED" :
          !canContinue ? "NATIVE_ROUTE_HOLD_NOT_PLAYING" :
            "NATIVE_ROUTE_HOLD_NO_WITNESS", observedId || heldTrackId);
      }
    }
  } else if (!recoveryHold && !nativeRecoveryHoldBlocked.has(view) &&
      previous && typeof previous.trackId === "string") {
    // A read-only current-mapping witness covers a lagging native status
    // pulse on Yandex builds without kUrl. It is never decoder proof.
    const observed = await execute(view,
      ";window.__celikomBridgeNativeCurrentTrack?.()||null");
    const observedId = typeof observed?.id === "string" &&
      /^[1-9][0-9]{0,23}$/.test(observed.id) ? observed.id : null;
    const mappedId = await execute(view,
      ";window.__celikomBridgeNativeMappedCurrentTrackId?.()||''");
    const previouslyMapped = previous.value === "NATIVE_MAPPING_ACCEPTED" ||
      previous.value === "NATIVE_SOURCE_VERIFIED";
    const canContinue = observed?.playbackState === "PLAYING" ||
      observed?.playbackState === "PAUSED";
    const samePreviouslyMappedTrack = observedId === previous.trackId && previouslyMapped;
    const currentTrackHasOwnMapping = !!observedId && mappedId === observedId;
    if (canContinue && (samePreviouslyMappedTrack || currentTrackHasOwnMapping)) {
      recoveryHold = {
        trackId: observedId,
        firstSeenAt: observedId === previous.trackId ? previous.firstSeenAt || now : now,
        capturedAt: now
      };
      nativeRecoveryHolds.set(view, recoveryHold);
    } else {
      nativeRecoveryHoldBlocked.add(view);
      note(observedId !== previous.trackId ? "NATIVE_ROUTE_HOLD_TRACK_CHANGED" :
        !canContinue ? "NATIVE_ROUTE_HOLD_NOT_PLAYING" :
        "NATIVE_ROUTE_HOLD_NO_PRIOR_MAP", previous.trackId);
    }
  }
  const preserveCurrentSource = networkRecoveryPending &&
    state.enabled === true && state.signedIn === true && !!apiOrigin &&
    previousOrigin === apiOrigin &&
    typeof recoveryHold?.trackId === "string" &&
    !nativeRecoveryHoldBlocked.has(view);
  const currentTrackRevalidationId =
    typeof state?.currentTrackRevalidationId === "string" &&
    /^[1-9][0-9]{0,23}$/.test(state.currentTrackRevalidationId)
      ? state.currentTrackRevalidationId : "";
  const currentTrackRevalidationEpoch =
    Number.isSafeInteger(state?.currentTrackRevalidationEpoch) &&
    state.currentTrackRevalidationEpoch > 0
      ? state.currentTrackRevalidationEpoch : 0;
  let isSelectedPlaybackView = view === selectedPlaybackView;
  if (!isSelectedPlaybackView && !selectedPlaybackView && currentTrackRevalidationId) {
    const observed = await execute(view,
      ";window.__celikomBridgeNativeCurrentTrack?.()||null");
    const observedId = typeof observed?.id === "string" &&
      /^[1-9][0-9]{0,23}$/.test(observed.id) ? observed.id : "";
    const canContinue = observed?.playbackState === "PLAYING" ||
      observed?.playbackState === "PAUSED";
    isSelectedPlaybackView = observedId === currentTrackRevalidationId &&
      canContinue && nativeAudible(view);
  }
  const safeState = {
    enabled: stateAvailable && state.enabled === true &&
      state.signedIn === true && !!apiOrigin,
    signedIn: stateAvailable && state.signedIn === true,
    apiOrigin,
    networkRecoveryPending,
    preserveCurrentSource,
    preserveCurrentTrackId: preserveCurrentSource ? recoveryHold.trackId : "",
    currentTrackRevalidationId: isSelectedPlaybackView ? currentTrackRevalidationId : "",
    currentTrackRevalidationEpoch: isSelectedPlaybackView ? currentTrackRevalidationEpoch : 0
  };
  const preserveDecoderWitness = safeState.networkRecoveryPending &&
    safeState.signedIn && !!safeState.apiOrigin &&
    previousOrigin === safeState.apiOrigin;
  if ((!safeState.enabled || !safeState.signedIn || originChanged) &&
      !preserveDecoderWitness) {
    // A same-origin transient VPN suspension is not a source loss. Keep the
    // exact signed-grant and current-decoder evidence so a kUrl refresh during
    // the outage can still be attributed to the already-playing CELIKOM track.
    // Manual Stop, logout, denial and origin changes still clear every witness.
    nativeExpectedAudio.delete(view);
    verifiedDecoderSource.delete(view);
    nativeMediaHttpSuccess.delete(view);
    nativeDecoderPlayers.delete(view);
  }
  nativeAudioOrigins.set(view, safeState.apiOrigin);
  const delivered = await deliverState(view, safeState);
  if (delivered && safeState.enabled && safeState.networkRecoveryPending &&
      Number.isSafeInteger(state?.recoveryEpoch) &&
      state.recoveryEpoch > 0)
    deliveredRecoveryEpoch.set(view, state.recoveryEpoch);
  else deliveredRecoveryEpoch.delete(view);
  return justEnabled;
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
      lastTokenRevision.delete(view);
      lastStateAt.delete(view);
      lastStatus.delete(view);
      lastNativeState.delete(view);
      lastDeliveredState.delete(view);
      deliveredRecoveryEpoch.delete(view);
      nativeAudioOrigins.set(view, "");
      nativeExpectedAudio.delete(view);
      verifiedDecoderSource.delete(view);
      nativeMediaHttpSuccess.delete(view);
      nativeDecoderPlayers.delete(view);
      nativeRecoveryHolds.delete(view);
      nativeRecoveryHoldBlocked.add(view);
      deliveredRecoveryEpoch.delete(view);
      await deliverState(view, {enabled:false,signedIn:false,apiOrigin:""});
      return;
    }
    const tokenRevision = tokenFileRevision;
    const previousTokenRevision = lastTokenRevision.get(view);
    const companionSessionChanged = previousTokenRevision !== undefined &&
      previousTokenRevision !== tokenRevision;
    lastTokenRevision.set(view, tokenRevision);
    if (companionSessionChanged) {
      lastStateAt.delete(view);
      lastStatus.delete(view);
      lastNativeState.delete(view);
      lastDeliveredState.delete(view);
      deliveredRecoveryEpoch.delete(view);
      nativeAudioOrigins.set(view, "");
      nativeExpectedAudio.delete(view);
      verifiedDecoderSource.delete(view);
      nativeMediaHttpSuccess.delete(view);
      nativeDecoderPlayers.delete(view);
    }
    note("BOOTSTRAP_KEY_PRESENT");
    const now = Date.now();
    if (now - (lastDiagPoll.get(view) || 0) >= 700) {
      lastDiagPoll.set(view, now);
      const events = await execute(view, ";(window.__celikomBridgeNativeDrainDiagnostics?.()||[])");
      if (Array.isArray(events)) {
        for (const event of events.slice(0, 48)) {
          if (!Array.isArray(event) || event.length !== 2) continue;
          if (event[0] === "SOURCE_MAPPED" && typeof event[1] === "string") {
            const currentId = await execute(view,
              ";window.__celikomBridgeNativeCurrentTrackId?.()||''");
            if (currentId === event[1]) nativeRecoveryHoldBlocked.delete(view);
          }
          note(event[0], event[1]);
        }
      }
    }
    const bridgeJustEnabled = await relayState(view, token, now);
    const queue = await execute(view,
      ";(window.__celikomBridgeNativeDrain?.()||[])");
    if (Array.isArray(queue)) {
      await Promise.all(queue.slice(0, 6).map(item => relayGrant(view, token, item)));
    }
    if (bridgeJustEnabled ||
        now - (lastStatus.get(view)?.at || 0) > PLAYBACK_STATE_SAMPLE_INTERVAL_MS) {
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
      // Only the exact current Media player's signed kUrl or direct src
      // attribute, paired with that same player's PLAYING state, is evidence
      // of CELIKOM reaching the player. Network 206 and file-info mapping are
      // not enough. Queue identity and CDP events may arrive in either order.
      const decoderPlayer = currentDecoderPlayer(view, trackId, firstSeenAt, checkedAt);
      const decoderConfirmed = !!decoderPlayer;
      if (decoderConfirmed) {
        verifiedDecoderSource.set(view, {trackId, at:decoderPlayer.sourceAt});
        if (decoderPlayer.evidenceReportedFor !== trackId) {
          decoderPlayer.evidenceReportedFor = trackId;
          note("PLAYER_DECODER_CELIKOM_SOURCE_MATCHED", trackId);
          if (decoderPlayer.gainApplied === true)
            note("PLAYER_CURRENT_GAIN_VARIANT_URL_SELECTED", trackId);
          else if (Number.isFinite(decoderPlayer.gainDb) && decoderPlayer.gainDb !== 0)
            note("PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING", trackId);
          void execute(view,
            ";window.__celikomBridgeNativeConfirmedCurrentSource?.(" +
            JSON.stringify(trackId) + ")").catch(() => null);
        }
      } else {
        verifiedDecoderSource.delete(view);
      }
      const status = decoderConfirmed &&
        (rendererStatus === "NATIVE_MAPPING_ACCEPTED" ||
         rendererStatus === "NATIVE_CONNECTED" ||
         rendererStatus === "NATIVE_SOURCE_VERIFIED")
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
      // Decoder proof applies only to the exact current queue identity.
      // A mapping or a successful HTTP 206 alone is NOT replacement proof.
      const source = decoderConfirmed ? "ACTIVE_REPLACEMENT" : "UNKNOWN";
      const reportedState = ["PLAYING","PAUSED","STOPPED"].includes(
        observed?.playbackState) ? observed.playbackState : "UNKNOWN";
      const audibleNow = nativeAudible(view);
      const playbackState = reportedState === "PLAYING" &&
        (decoderConfirmed || audibleNow)
          ? "PLAYING" : reportedState === "PAUSED" && !audibleNow
          ? "PAUSED" : reportedState === "STOPPED" && !audibleNow
          ? "STOPPED" : "UNKNOWN";
      const current = {
        value:status, trackId, title, artist, durationMs,
        source, playbackState, at:checkedAt, firstSeenAt,
        heartbeatAt:previous?.heartbeatAt || 0,
        selectionGeneration:previous?.selectionGeneration || 0
      };
      lastStatus.set(view,current);
      const chosen = choosePlaybackView();
      const selectedGeneration = selectionGeneration;
      if (chosen === view && (!previous || bridgeJustEnabled ||
          status !== previous.value || trackId !== previous.trackId ||
          title !== previous.title || artist !== previous.artist ||
          durationMs !== previous.durationMs || source !== previous.source ||
          playbackState !== previous.playbackState ||
          previous.selectionGeneration !== selectedGeneration ||
          !previous.heartbeatAt ||
          checkedAt - previous.heartbeatAt >= HEARTBEAT_INTERVAL_MS)) {
        // Recheck after sampling; an older window never publishes its track.
        if (choosePlaybackView() === view &&
            selectionGeneration === selectedGeneration) {
          current.heartbeatAt = checkedAt;
          current.selectionGeneration = selectedGeneration;
          await localRequest(token, "/v1/heartbeat", "POST", heartbeatPayload({
            trackId, status, title, artist, durationMs,
            source, playbackState,
            recoveryEpoch:deliveredRecoveryEpoch.get(view)
          }));
        }
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
// Holds only the last mapped current-track identity across a same-origin
// transient VPN suspension. This is a no-reload continuity hint, NOT proof
// that the native decoder is still playing the CELIKOM URL.
const nativeRecoveryHolds = new WeakMap();
const nativeRecoveryHoldBlocked = new WeakSet();
const nativeExpectedAudio = new WeakMap();
const nativeMediaHttpSuccess = new WeakMap();
const nativeNetworkObserversReady = new WeakSet();
const nativeUnfetchedReloadAttempt = new WeakMap();
const nativeDecoderPlayers = new WeakMap();
const nativeDecoderDomRefreshers = new WeakMap();
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
      expiresAt, yandexTrackId: grant.trackId, gainApplied: grant.gainApplied === true,
      gainDb: Number.isFinite(grant.gainDb) ? grant.gainDb : null, recordedAt: now });
    // If the Media player already exposed its own direct src before this
    // approved grant arrived, re-read only that same player's src attribute.
    nativeDecoderDomRefreshers.get(view)?.(grant.trackId);
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
function currentDecoderPlayer(view, trackId, firstSeenAt, checkedAt) {
  if (!trackId) return null;
  const players = nativeDecoderPlayers.get(view);
  if (!players) return null;
  for (const player of players.values()) {
    if (player?.playing === true && player.pipelineFailed !== true &&
        player.sourceTrackId === trackId && Number.isSafeInteger(player.sourceAt) &&
        player.sourceAt >= firstSeenAt - 3000 &&
        checkedAt >= player.sourceAt && checkedAt - player.sourceAt < 600000)
      return player;
  }
  return null;
}
function downgradeVerifiedPlaybackHeartbeat(view, trackId) {
  const previous = lastStatus.get(view);
  if (!previous || previous.trackId !== trackId ||
      previous.value !== "NATIVE_SOURCE_VERIFIED") return false;
  const token = readToken();
  if (!token || choosePlaybackView() !== view) return false;
  // A CDP source/playing invalidation outranks the prior green label.
  // Only invalidate UI evidence: never touch Yandex audio or its queue.
  const downgraded = {...previous, value:"NATIVE_MAPPING_ACCEPTED",
    source:"UNKNOWN", heartbeatAt:Date.now()};
  lastStatus.set(view, downgraded);
  void localRequest(token, "/v1/heartbeat", "POST", heartbeatPayload({
    trackId, status:downgraded.value,
    title:previous.title, artist:previous.artist, durationMs:previous.durationMs,
    source:"UNKNOWN", playbackState:previous.playbackState || "UNKNOWN"
  })).then(result => {
    if (!result && lastStatus.get(view) === downgraded)
      lastStatus.set(view, previous);
  });
  return true;
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
  nativeDecoderPlayers.set(view, decoderPlayers);
  const decoderPlayerNodes = new Map();
  const decoderNodePlayers = new Map();
  const pendingDecoderNodes = new Map();
  let domReady = false;
  const createDecoderPlayer = () => ({
    playing:false, playingPropertySeen:false, sourceTrackId:null, sourceAt:null,
    gainApplied:null, gainDb:null, pipelineFailed:false, evidenceReportedFor:null,
    lastVolume:null, volumeTrackId:null, urlPropertySeen:false, sourceKind:null
  });
  const getDecoderPlayer = id => {
    let player = decoderPlayers.get(id);
    if (player) return player;
    if (decoderPlayers.size >= 32) {
      const oldest = decoderPlayers.keys().next().value;
      decoderPlayers.delete(oldest);
      const node = decoderPlayerNodes.get(oldest);
      if (node) decoderNodePlayers.delete(node.nodeId);
      decoderPlayerNodes.delete(oldest);
      pendingDecoderNodes.delete(oldest);
    }
    player = createDecoderPlayer();
    decoderPlayers.set(id, player);
    return player;
  };
  const verifyDecoderPlayer = player => {
    const current = lastStatus.get(view)?.trackId;
    if (!player || player.playing !== true || player.pipelineFailed === true ||
        !current || player.sourceTrackId !== current ||
        !Number.isSafeInteger(player.sourceAt) ||
        player.evidenceReportedFor === current) return;
    player.evidenceReportedFor = current;
    verifiedDecoderSource.set(view, {trackId:current, at:Date.now()});
    note("PLAYER_DECODER_CELIKOM_SOURCE_MATCHED", current);
    if (player.sourceKind === "dom")
      note("PLAYER_DOM_SOURCE_CELIKOM_MATCHED", current);
    if (player.gainApplied === true)
      note("PLAYER_CURRENT_GAIN_VARIANT_URL_SELECTED", current);
    else if (Number.isFinite(player.gainDb) && player.gainDb !== 0)
      note("PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING", current);
    void execute(view,
      ";window.__celikomBridgeNativeConfirmedCurrentSource?.(" +
      JSON.stringify(current) + ")").catch(() => null);
  };
  const applyDecoderUrl = (player, rawUrl, sourceKind) => {
    const previousTrackId = player.sourceTrackId;
    const currentTrackId = lastStatus.get(view)?.trackId;
    const wasCurrentCelikom = player.playing && !!previousTrackId &&
      previousTrackId === currentTrackId;
    player.sourceTrackId = null;
    player.sourceAt = null;
    player.gainApplied = null;
    player.gainDb = null;
    player.sourceKind = null;
    player.evidenceReportedFor = null;
    verifiedDecoderSource.delete(view);
    if (typeof rawUrl === "string" && rawUrl.length <= 4096) {
      try {
        const actual = new URL(rawUrl);
        const expectedOrigin = nativeAudioOrigins.get(view);
        const resourceId = expectedOrigin && actual.origin === expectedOrigin &&
          !actual.username && !actual.password &&
          AUDIO_RESOURCE_PATH.exec(actual.pathname)?.[1];
        const expected = resourceId && nativeExpectedAudio.get(view)?.get(resourceId);
        const classification = resourceId && expected ?
          classifyPlayerUrl(view, resourceId, actual) : "";
        if (expected?.expiresAt > Date.now() &&
            (classification === "PLAYER_URL_MATCH" ||
             classification === "PLAYER_URL_SIGNED_FIELDS_INTACT")) {
          player.sourceTrackId = expected.yandexTrackId;
          player.sourceAt = Date.now();
          player.pipelineFailed = false;
          player.gainApplied = expected.gainApplied === true;
          player.gainDb = expected.gainDb;
          player.sourceKind = sourceKind;
        }
      } catch { /* Unknown native URL: no source evidence. */ }
    }
    if (wasCurrentCelikom && player.sourceTrackId !== previousTrackId) {
      downgradeVerifiedPlaybackHeartbeat(view, currentTrackId);
      if (!player.sourceTrackId) {
        nativeRecoveryHolds.delete(view);
        nativeRecoveryHoldBlocked.add(view);
        note("PLAYER_CURRENT_SOURCE_LEFT_CELIKOM", currentTrackId);
        return !!currentTrackId;
      }
    }
    return false;
  };
  const requestSourceRecovery = () => {
    const currentTrackId = lastStatus.get(view)?.trackId;
    if (currentTrackId)
      void execute(view,
        ";window.__celikomBridgeNativeRecoverSourceLeft?.(" +
        JSON.stringify(currentTrackId) + ")").catch(() => null);
  };
  const captureDomSource = (playerId, rawUrl) => {
    const player = decoderPlayers.get(playerId);
    if (!player || player.urlPropertySeen) return;
    if (typeof rawUrl === "string") {
      note(rawUrl.startsWith("blob:") ?
        "PLAYER_DOM_SOURCE_BLOB_SEEN" : "PLAYER_DOM_SOURCE_ATTRIBUTE_SEEN");
    }
    const sourceLeftCurrent = applyDecoderUrl(player,
      typeof rawUrl === "string" ? rawUrl : null, "dom");
    decoderPlayers.set(playerId, player);
    if (sourceLeftCurrent && player.playing) requestSourceRecovery();
    if (player.sourceKind !== "dom" && typeof rawUrl === "string" &&
        !rawUrl.startsWith("blob:"))
      note("PLAYER_DOM_SOURCE_OTHER");
    verifyDecoderPlayer(player);
  };
  const readMediaPlayerNode = async (playerId, backendNodeId) => {
    if (!Number.isSafeInteger(backendNodeId) || backendNodeId <= 0) return;
    if (!domReady) {
      pendingDecoderNodes.set(playerId, backendNodeId);
      return;
    }
    try {
      const pushed = await debug.sendCommand(
        "DOM.pushNodesByBackendIdsToFrontend", {backendNodeIds:[backendNodeId]});
      const nodeId = pushed?.nodeIds?.[0];
      if (!Number.isSafeInteger(nodeId) || nodeId <= 0) {
        note("PLAYER_DOM_NODE_UNAVAILABLE");
        return;
      }
      const oldNode = decoderPlayerNodes.get(playerId);
      if (oldNode) decoderNodePlayers.delete(oldNode.nodeId);
      decoderPlayerNodes.set(playerId, {backendNodeId, nodeId});
      decoderNodePlayers.set(nodeId, playerId);
      pendingDecoderNodes.delete(playerId);
      note("PLAYER_DOM_MEDIA_NODE_SEEN");
      const result = await debug.sendCommand("DOM.getAttributes", {nodeId});
      const attributes = result?.attributes;
      if (!Array.isArray(attributes) || attributes.length > 256) {
        note("PLAYER_DOM_SOURCE_ATTRIBUTE_MISSING");
        return;
      }
      let found = false;
      for (let i = 0; i + 1 < attributes.length; i += 2) {
        if (attributes[i] !== "src") continue;
        found = true;
        captureDomSource(playerId, attributes[i + 1]);
        break;
      }
      if (!found) note("PLAYER_DOM_SOURCE_ATTRIBUTE_MISSING");
    } catch { note("PLAYER_DOM_UNAVAILABLE"); }
  };
  nativeDecoderDomRefreshers.set(view, trackId => {
    for (const [playerId, player] of decoderPlayers) {
      if (!player.playing || player.urlPropertySeen ||
          (player.sourceKind === "dom" && player.sourceTrackId === trackId)) continue;
      const node = decoderPlayerNodes.get(playerId);
      if (node) void readMediaPlayerNode(playerId, node.backendNodeId);
      else if (pendingDecoderNodes.has(playerId))
        void readMediaPlayerNode(playerId, pendingDecoderNodes.get(playerId));
    }
  });
  const initializeDomObserver = () => {
    Promise.resolve(debug.sendCommand("DOM.getDocument", {depth:1, pierce:true})).then(
      () => {
        if (!validView(view)) return;
        domReady = true;
        note("PLAYER_DOM_READY");
        for (const [playerId, backendNodeId] of pendingDecoderNodes)
          void readMediaPlayerNode(playerId, backendNodeId);
      },
      () => { if (validView(view)) note("PLAYER_DOM_UNAVAILABLE"); });
  };
  const capturePlayerProperties = params => {
    const id = params?.playerId;
    if (typeof id !== "string" || id.length < 1 || id.length > 128 ||
        !/^[a-zA-Z0-9_-]+$/.test(id) || !Array.isArray(params?.properties)) return;
    const prev = getDecoderPlayer(id);
    const properties = params.properties.slice(0, 30);
    // Never record property values or media URLs. This Yandex build may omit
    // kUrl; the fallback below reads only the src attribute of this exact
    // Media player's own DOM node and still requires the same player to play.
    if (properties.length) note("PLAYER_CDP_PROPERTIES_SEEN");
    if (properties.some(prop => prop?.name === "kUrl")) {
      note("PLAYER_CDP_URL_PROPERTY_SEEN");
      prev.urlPropertySeen = true;
    }
    let sourceLeftCurrent = false;
    for (const prop of properties) {
      if (prop?.name === "kUrl") {
        if (applyDecoderUrl(prev, prop.value, "cdp"))
          sourceLeftCurrent = true;
      } else if (prop?.name === "kIsPlaying" &&
          (prop.value === "true" || prop.value === "false")) {
        const currentTrackId = lastStatus.get(view)?.trackId;
        const wasCurrentVerified = prev.playing && !!currentTrackId &&
          prev.sourceTrackId === currentTrackId;
        prev.playingPropertySeen = true;
        prev.playing = prop.value === "true";
        if (prev.playing) prev.pipelineFailed = false;
        if (!prev.playing) {
          if (wasCurrentVerified) {
            downgradeVerifiedPlaybackHeartbeat(view, currentTrackId);
            verifiedDecoderSource.delete(view);
          }
          prev.evidenceReportedFor = null;
          prev.lastVolume = null;
          prev.volumeTrackId = null;
        }
      }
    }
    if (sourceLeftCurrent && prev.playing) requestSourceRecovery();
    for (const prop of properties) {
      if (prop?.name !== "kVolume") continue;
      const currentId = lastStatus.get(view)?.trackId;
      const value = prop.value;
      const volume = typeof value === "string" &&
        /^(?:0(?:\.\d{1,6})?|1(?:\.0{1,6})?)$/.test(value)
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
    }
    decoderPlayers.set(id, prev);
    verifyDecoderPlayer(prev);
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
        try {
        if (!validView(view)) return;
        if (method === "Media.playerCreated") {
          const mediaPlayer = params?.player;
          const id = mediaPlayer?.playerId;
          const backendNodeId = mediaPlayer?.domNodeId;
          if (typeof id === "string" && id.length >= 1 && id.length <= 128 &&
              /^[a-zA-Z0-9_-]+$/.test(id)) {
            getDecoderPlayer(id);
            if (Number.isSafeInteger(backendNodeId) && backendNodeId > 0)
              void readMediaPlayerNode(id, backendNodeId);
            else note("PLAYER_DOM_MEDIA_NODE_UNAVAILABLE");
          }
          return;
        }
        if (method === "DOM.documentUpdated") {
          decoderNodePlayers.clear();
          decoderPlayerNodes.clear();
          pendingDecoderNodes.clear();
          domReady = false;
          initializeDomObserver();
          return;
        }
        if (method === "DOM.attributeModified" && params?.name === "src" &&
            Number.isSafeInteger(params?.nodeId)) {
          const playerId = decoderNodePlayers.get(params.nodeId);
          if (playerId) captureDomSource(playerId, params.value);
          return;
        }
        if (method === "DOM.attributeRemoved" && params?.name === "src" &&
            Number.isSafeInteger(params?.nodeId)) {
          const playerId = decoderNodePlayers.get(params.nodeId);
          if (playerId) captureDomSource(playerId, null);
          return;
        }
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
          const verified = verifiedDecoderSource.get(view);
          if (lost?.sourceTrackId === verified?.trackId) {
            downgradeVerifiedPlaybackHeartbeat(view, verified.trackId);
            verifiedDecoderSource.delete(view);
          }
          if (lost?.playing === true) {
            nativeRecoveryHolds.delete(view);
            nativeRecoveryHoldBlocked.add(view);
          }
          const node = decoderPlayerNodes.get(params.playerId);
          if (node) decoderNodePlayers.delete(node.nodeId);
          decoderPlayerNodes.delete(params.playerId);
          pendingDecoderNodes.delete(params.playerId);
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
          if (player?.playing === true && nativeAudible(view)) {
            nativeRecoveryHolds.delete(view);
            nativeRecoveryHoldBlocked.add(view);
          }
          if (player?.sourceTrackId && player.sourceTrackId === currentTrack) {
            player.pipelineFailed = true;
            verifiedDecoderSource.delete(view);
            note("PLAYER_DECODER_CELIKOM_PIPELINE_ERROR", currentTrack);
            downgradeVerifiedPlaybackHeartbeat(view, currentTrack);
          }
        }
        else if (method === "Media.playerMessagesLogged" &&
            Array.isArray(params?.messages) &&
            params.messages.some(x => x?.level === "error"))
          note("PLAYER_CDP_ERROR_MESSAGE");
        else if (method === "Media.playerEventsAdded" &&
            Array.isArray(params?.events)) {
          const id = params?.playerId;
          const player = typeof id === "string" &&
            /^[a-zA-Z0-9_-]{1,128}$/.test(id) ? getDecoderPlayer(id) : null;
          for (const item of params.events.slice(0, 30)) {
            const value = String(item?.value || "").slice(0, 256);
            if (/\bkPlay\b/.test(value)) {
              note("PLAYER_CDP_EVENT_START");
              if (player && !player.playingPropertySeen) {
                player.playing = true;
                player.pipelineFailed = false;
                const node = decoderPlayerNodes.get(id);
                if (node) void readMediaPlayerNode(id, node.backendNodeId);
                else if (pendingDecoderNodes.has(id))
                  void readMediaPlayerNode(id, pendingDecoderNodes.get(id));
              }
            } else if (/\bkPause\b/.test(value)) {
              note("PLAYER_CDP_EVENT_PAUSE");
              if (player && !player.playingPropertySeen) {
                const currentTrackId = lastStatus.get(view)?.trackId;
                const wasCurrentVerified = player.playing && !!currentTrackId &&
                  player.sourceTrackId === currentTrackId;
                player.playing = false;
                if (wasCurrentVerified) {
                  downgradeVerifiedPlaybackHeartbeat(view, currentTrackId);
                  verifiedDecoderSource.delete(view);
                }
                player.evidenceReportedFor = null;
                player.lastVolume = null;
                player.volumeTrackId = null;
              }
            } else if (/\bkPipelineError\b/.test(value)) {
              note("PLAYER_CDP_EVENT_PIPELINE_ERROR");
            }
          }
          if (player) {
            decoderPlayers.set(id, player);
            verifyDecoderPlayer(player);
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
        } catch {
          // A malformed vendor CDP event must not escape Electron's main
          // process event handler or restart Yandex. Fail closed for this
          // passive decoder witness; do not touch player/audio controls.
          verifiedDecoderSource.delete(view);
          decoderPlayers.clear();
          nativeDecoderPlayers.delete(view);
          note("NATIVE_CDP_EVENT_EXCEPTION");
        }
      });
      debug.on("detach", () => {
        if (!validView(view)) return;
        // A detached CDP observer can no longer prove which source is
        // currently playing. Downgrade any green heartbeat immediately and
        // invalidate both Media and DOM source witnesses.
        const verified = verifiedDecoderSource.get(view);
        if (verified?.trackId)
          downgradeVerifiedPlaybackHeartbeat(view, verified.trackId);
        verifiedDecoderSource.delete(view);
        nativeExpectedAudio.delete(view);
        nativeMediaHttpSuccess.delete(view);
        nativeNetworkObserversReady.delete(view);
        nativeUnfetchedReloadAttempt.delete(view);
        nativeDecoderDomRefreshers.delete(view);
        decoderPlayers.clear();
        decoderPlayerNodes.clear();
        decoderNodePlayers.clear();
        pendingDecoderNodes.clear();
        domReady = false;
        nativeDecoderPlayers.delete(view);
        note("PLAYER_CDP_DETACHED");
      });
      Promise.resolve(debug.sendCommand("Media.enable")).then(
        () => { if (validView(view)) note("PLAYER_CDP_READY"); },
        () => {
          if (validView(view)) note("PLAYER_CDP_UNAVAILABLE");
          try { if (debug.isAttached()) debug.detach(); } catch {}
        });
      // DOM is read-only and restricted to the src attribute on the exact
      // node associated by Media.playerCreated. Never inspect page scripts,
      // text, account data, successful response bodies or arbitrary elements.
      initializeDomObserver();
      // Passive read-only recording of status and request destination class;
      // Network is NOT intercepted, requests are never modified or retried.
      // Bound Chromium's retained Network payload buffers. We only need
      // small denial metadata for the 403 guard; request/response bodies,
      // post data and signed URLs are never exported.
      Promise.resolve(debug.sendCommand("Network.enable", {
        maxTotalBufferSize: 2 * 1024 * 1024,
        maxResourceBufferSize: 128 * 1024,
        maxPostDataSize: 0
      })).then(
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
    activity(view).startedAt = lastStarted;
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
    activity(view).audible = audible;
    if (audible) activity(view).audibleAt = Date.now();
    note(audible ? "PLAYER_AUDIO_AUDIBLE" : "PLAYER_AUDIO_SILENT");
  });
  view.on("destroyed", () => {
    viewActivity.delete(view);
    const wasSelected = selectedPlaybackView === view;
    if (wasSelected) {
      selectedPlaybackView = null;
      ++selectionGeneration;
    }
    lastStatus.delete(view);
    deliveredRecoveryEpoch.delete(view);
    nativeRecoveryHolds.delete(view);
    nativeDecoderDomRefreshers.delete(view);
    if (wasSelected && choosePlaybackView() === null) {
      const token = readToken();
      if (token) void localRequest(token, "/v1/heartbeat", "POST", heartbeatPayload({
        trackId:null, status:"UNAVAILABLE", title:"", artist:"",
        durationMs:null, source:"UNKNOWN", playbackState:"UNKNOWN"
      }));
    }
  });
}

// Fire-and-forget pulses must never leak rejected promises into Electron's
// main process. A passive relay failure is diagnostic, not a Yandex restart.
function scheduleTick(view) {
  void tick(view).catch(() => note("NATIVE_RELAY_TICK_EXCEPTION"));
}
app.on("web-contents-created", (_event, view) => {
  view.on("dom-ready", () => { injected.delete(view); scheduleTick(view); });
  view.on("did-finish-load", () => { injected.delete(view); scheduleTick(view); });
  view.on("console-message", (event, _level, legacy) => {
    const msg = typeof event?.message === "string" ? event.message : legacy;
    if (msg === "[CELIKOM] Native file-info source connector attached") note("RESOURCE_ATTACHED");
    if (msg === "[CELIKOM] Native bridge state received") note("RENDERER_BRIDGE_STATE_SEEN");
  });
});
let lastHostPulseAt = Date.now();
let lastResourceSampleAt = lastHostPulseAt;
let lastCpuUsage = null;
try {
  if (typeof process.cpuUsage === "function") lastCpuUsage = process.cpuUsage();
} catch {}
// Keep the established 300ms relay cadence until issue #53 has objective
// runtime evidence. CDP playback observation and recovery are not disabled.
const timer = setInterval(() => {
  const now = Date.now();
  const elapsed = now - lastHostPulseAt;
  // A small, read-only heartbeat for #53. Ignore sleep/resume gaps; this is
  // not proof of a whole-PC slowdown or a measurement of other applications.
  if (elapsed > 4000 && elapsed < 60000)
    note("NATIVE_ELECTRON_EVENT_LOOP_STALL");
  lastHostPulseAt = now;
  const sampleElapsed = now - lastResourceSampleAt;
  if (sampleElapsed >= 30000) {
    lastResourceSampleAt = now;
    try {
      const memory = typeof process.memoryUsage === "function"
        ? process.memoryUsage() : null;
      if (memory && Number.isFinite(memory.rss) &&
          memory.rss > 700 * 1024 * 1024)
        note("NATIVE_ELECTRON_MEMORY_HIGH");
    } catch {}
    // Measure only this Electron main process. Record a fixed threshold event,
    // never raw CPU values, PIDs, process names or account/audio information.
    try {
      const currentCpu = typeof process.cpuUsage === "function"
        ? process.cpuUsage() : null;
      if (currentCpu && lastCpuUsage &&
          sampleElapsed >= 10000 && sampleElapsed <= 60000) {
        const cpuMicros = (currentCpu.user - lastCpuUsage.user) +
          (currentCpu.system - lastCpuUsage.system);
        const cpuPercent = cpuMicros / (sampleElapsed * 1000) * 100;
        if (Number.isFinite(cpuPercent) && cpuPercent >= 80)
          note("NATIVE_ELECTRON_CPU_HIGH");
      }
      if (currentCpu) lastCpuUsage = currentCpu;
    } catch {}
  }
  const views = webContents.getAllWebContents();
  if (views.length) note("WEB_CONTENTS_PRESENT");
  for (const view of views) scheduleTick(view);
}, 300);
if (timer.unref) timer.unref();
