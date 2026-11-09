import { createNativeResourceAdapter } from "../w22/native-resource-adapter.mjs";

// Runs inside Yandex's already running renderer. The Electron main process
// handles the localhost connection; this view never fetches localhost itself.
(() => {
  "use strict";
  if (window.__celikomBridgeNativeDrain) return;
  const approved = new Set([
    "https://desktop.app.music.yandex.net",
    "https://music.yandex.ru",
    "https://next.music.yandex.ru",
    "https://music.yandex.com"
  ]);
  const nativeScheme = window.location.protocol.replace(/[^a-z]/gi, "").toLowerCase();
  if (!approved.has(window.location.origin) &&
      !(nativeScheme === "musicapplication" &&
        window.location.hostname.toLowerCase() === "desktop")) return;

  let apiOrigin = "", stopped = false, attached = false;
  let pendingCount = 0, sequence = 0, lastReported = "";
  const queued = [], pending = new Map();
  const MAX_QUEUE = 24;
  const diagnosticQueue = [];
  function report(code, trackId = null) {
    if (!/^[A-Z_]{3,48}$/.test(code)) return;
    const id = typeof trackId === "string" && /^[1-9][0-9]{0,17}$/.test(trackId)
      ? trackId : null;
    diagnosticQueue.push([code, id]);
    if (diagnosticQueue.length > 256) diagnosticQueue.shift();
  }
  window.__celikomBridgeNativeDrainDiagnostics = () => diagnosticQueue.splice(0, 48);

  // Only report observable media DOM events. WebAudio-only playback is explicitly
  // marked as unobserved in the exported diagnostics.
  if (typeof document !== "undefined" && document?.addEventListener) {
    for (const name of ["play", "pause", "playing", "error", "waiting",
                        "stalled", "seeking", "seeked", "ended"]) {
      document.addEventListener(name, event => {
        if (event?.target?.tagName === "AUDIO")
          report("MEDIA_" + name.toUpperCase());
      }, true);
    }
  }
  // Resource Timing may not disclose HTTP status on cross-origin media.
  // Never record the name, full URL, query string, response headers or tokens.
  if (typeof PerformanceObserver !== "undefined") {
    try {
      const observer = new PerformanceObserver(list => {
        for (const entry of list.getEntries()) {
          if (!apiOrigin || typeof entry.name !== "string") continue;
          try {
            const url = new URL(entry.name);
            if (url.origin !== apiOrigin ||
                !/^\\/api\\/v1\\/audio\\/[A-Za-z0-9_-]{1,128}$/.test(url.pathname)) continue;
            report("MEDIA_REQUEST_SEEN");
            const status = Number(entry.responseStatus);
            report(status >= 200 && status < 300 ? "MEDIA_HTTP_OK" :
              status >= 400 ? "MEDIA_HTTP_FAILED" : "MEDIA_HTTP_UNVERIFIED");
          } catch {}
        }
      });
      observer.observe({ type: "resource", buffered: false });
      window.addEventListener("beforeunload", () => observer.disconnect(), { once: true });
    } catch {}
  }

  const adapter = createNativeResourceAdapter({
    onEvent: report,
    allowedOrigin: () => apiOrigin,
    resolve: (trackId, signal) => new Promise(resolve => {
      if (stopped || signal.aborted || pending.size >= MAX_QUEUE) {
        resolve(null); return;
      }
      const requestId = String(++sequence);
      const finish = result => {
        if (!pending.has(requestId)) return;
        pending.delete(requestId);
        signal.removeEventListener("abort", abort);
        resolve(result);
      };
      const abort = () => { report("RESOLVE_ABORTED", trackId); finish(null); };
      pending.set(requestId, { finish });
      signal.addEventListener("abort", abort, { once: true });
      queued.push({ requestId, trackId });
    })
  });

  window.__celikomBridgeNativeDrain = () => {
    if (stopped) return [];
    const items = [];
    while (queued.length > 0 && items.length < 6) {
      const candidate = queued.shift();
      if (pending.has(candidate.requestId)) items.push(candidate);
    }
    return items;
  };
  window.__celikomBridgeNativeReceive = (requestId, grant) => {
    if (stopped || typeof requestId !== "string") return;
    pending.get(requestId)?.finish(grant ?? null);
  };
  window.__celikomBridgeNativeSetState = next => {
    if (stopped) return;
    let origin = "";
    try {
      const uri = new URL(next?.apiOrigin);
      if (uri.protocol === "https:" && uri.pathname === "/" &&
          !uri.username && !uri.password && !uri.search && !uri.hash &&
          uri.origin === next.apiOrigin) origin = uri.origin;
    } catch {}
    if (origin !== apiOrigin) { apiOrigin = origin; adapter.disable(); }
    if (next?.enabled === true && next?.signedIn === true && !!origin && attached)
      adapter.enable();
    else adapter.disable();
    const status = adapter.enabled ? "NATIVE_CONNECTED" : "ORIGINAL";
    if (status !== lastReported) {
      lastReported = status;
      report(adapter.enabled ? "RENDERER_STATE_ON" : "RENDERER_STATE_OFF");
      console.info("[CELIKOM] Native bridge state received");
    }
  };
  window.__celikomBridgeNativeStatus = () => {
    if (stopped || !attached || !adapter.enabled) return "ORIGINAL";
    return adapter.status === "SOURCE_MAPPING_RETURNED_NOT_AUDIO_VERIFIED"
      ? "NATIVE_MAPPING_ACCEPTED" : "NATIVE_CONNECTED";
  };

  function findResource() {
    if (attached || stopped) return attached;
    const chunks = window.webpackChunk_N_E;
    if (!Array.isArray(chunks)) return false;
    let webpackRequire;
    try {
      const tag = Symbol("celikom");
      chunks.push([[tag], {}, r => { webpackRequire = r; }]);
      chunks.pop();
    } catch { return false; }
    if (!webpackRequire?.m || typeof webpackRequire !== "function") return false;
    for (const id in webpackRequire.m) {
      let source;
      try { source = webpackRequire.m[id].toString(); } catch { continue; }
      if (!source.includes('"get-file-info"') &&
          !source.includes('"resources/v2/file-info"')) continue;
      let module;
      try { module = webpackRequire(id); } catch { continue; }
      for (const name in module) {
        const klass = module[name];
        if (typeof klass !== "function" || !klass.prototype ||
            typeof klass.prototype.getFileInfo !== "function") continue;
        try {
          adapter.attach(klass.prototype);
          attached = true;
          report("RESOURCE_HOOK_ATTACHED");
          console.info("[CELIKOM] Native file-info source connector attached");
          return true;
        } catch {}
      }
    }
    return false;
  }

  const finder = setInterval(() => {
    if (findResource()) clearInterval(finder);
  }, 300);
  let attempts = 0;
  const deadline = setInterval(() => {
    if (attached || ++attempts >= 35) {
      clearInterval(deadline);
      if (!attached) { report("RESOURCE_HOOK_MISSING"); clearInterval(finder); }
    }
  }, 1000);
  findResource();
  window.addEventListener("beforeunload", () => {
    stopped = true;
    clearInterval(finder);
    clearInterval(deadline);
    for (const job of pending.values()) job.finish(null);
    queued.length = 0;
    adapter.dispose();
    delete window.__celikomBridgeNativeDrain;
    delete window.__celikomBridgeNativeReceive;
    delete window.__celikomBridgeNativeSetState;
    delete window.__celikomBridgeNativeStatus;
    delete window.__celikomBridgeNativeDrainDiagnostics;
  }, { once: true });
})();
