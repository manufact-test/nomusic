import { createNativeResourceAdapter } from "../w22/native-resource-adapter.mjs";
import { createCurrentSourceRefresh } from "../w60/current-source-refresh.mjs";
import { createTransientSourceRecovery } from "./transient-source-recovery.mjs";
import { createDeferredTrackRecovery } from "./deferred-track-recovery.mjs";

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

  let apiOrigin = "", stopped = false, attached = false, stateSeen = false;
  let stateTransitionGeneration = 0;
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
  // W50: stop the diagnostic 32-byte GET. W45 CORS is already proven live.
  // All future signed-audio network requests can now be attributed by a
  // passive Network observer to Yandex's own media pipeline or preloading.
  // Do not copy blockedURIs (which can contain signed audio URLs) to logs.
  if (typeof document !== "undefined" && document?.addEventListener) {
    document.addEventListener("securitypolicyviolation", event => {
      if (!apiOrigin || typeof event?.blockedURI !== "string") return;
      try {
        if (new URL(event.blockedURI).origin === apiOrigin)
          report("AUDIO_CSP_BLOCKED");
      } catch {}
    }, true);
  }

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
                (!url.pathname.startsWith("/api/v1/audio/") ||
                 !/^[A-Za-z0-9_-]{1,128}$/.test(url.pathname.slice(14)))) continue;
            // A PerformanceObserver entry may be OUR own independent 32-byte
            // probe, not a request made by Yandex's audio decoder. It must
            // never be counted as evidence the real player fetched or played.
            // No CELIKOM diagnostic fetch exists in W50. Still not proof
            // of audible playback: it can be native preloading.
            report("PLAYER_AUDIO_RESOURCE_TIMING_SEEN");
          } catch {}
        }
      });
      observer.observe({ type: "resource", buffered: false });
      window.addEventListener("beforeunload", () => observer.disconnect(), { once: true });
    } catch {}
  }

  let sourceRecovery = null, deferredRecovery = null;
  const adapter = createNativeResourceAdapter({
    onEvent: (code, id) => {
      report(code, id);
      if (code === "RESOLVE_TRANSIENT" || code === "RESOLVE_TIMEOUT") {
        deferredRecovery?.record(id);
        deferredRecovery?.check();
      }
    },
    allowedOrigin: () => apiOrigin,
    resolve: (trackId, signal, opts = {}) => new Promise(resolve => {
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
      pending.set(requestId, { finish, trackId });
      signal.addEventListener("abort", abort, { once: true });
      queued.push({ requestId, trackId, recovery: opts.background === true });
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
    const job = pending.get(requestId);
    job?.finish(grant ?? null);
  };
  const playerSourceRefresh = createCurrentSourceRefresh({onEvent: report});
  let expiredSourceTrack = null, expiredSourceFailedTrack = null;
  let deferredSourceTrack = null, deferredSourceFailedTrack = null;
  let lastExpiredAttemptTrack = null, lastExpiredAttemptAt = 0;
  let lastUnfetchedAttemptTrack = null, lastUnfetchedAttemptAt = 0;
  let lastSourceLeftAttemptTrack = null, lastSourceLeftAttemptAt = 0;
  // Only an approved, CURRENT song may request one bounded source refresh
  // when main-process CDP saw mapping but no GET to CELIKOM's media URL.
  // This is NOT used as proof that the new audio actually became audible.
  window.__celikomBridgeNativeRefreshUnfetched = trackId => {
    if (typeof trackId !== "string" || !/^[1-9][0-9]{0,23}$/.test(trackId) ||
        playerSourceRefresh.currentTrackId() !== trackId ||
        !adapter.enabled || !attached || stopped ||
        !playerSourceRefresh.attached) return false;
    const now = Date.now();
    if (lastUnfetchedAttemptTrack === trackId &&
        now - lastUnfetchedAttemptAt < 120000) return false;
    lastUnfetchedAttemptTrack = trackId;
    lastUnfetchedAttemptAt = now;
    report("SOURCE_UNFETCHED_CURRENT_REFRESH", trackId);
    void playerSourceRefresh.request(trackId).then(
      ok => report(ok ? "SOURCE_UNFETCHED_CURRENT_REFRESH_OK" :
        "SOURCE_UNFETCHED_CURRENT_REFRESH_DEFERRED", trackId),
      () => report("SOURCE_UNFETCHED_CURRENT_REFRESH_DEFERRED", trackId));
    return true;
  };
  sourceRecovery = createTransientSourceRecovery({
    prime: id => adapter.prime(id),
    reload: id => playerSourceRefresh.request(id),
    currentTrackId: () => playerSourceRefresh.currentTrackId(),
    active: () => !stopped && attached && adapter.enabled && playerSourceRefresh.attached,
    onEvent: (code, id) => {
      report(code, id);
      if (code === "SOURCE_RECOVERY_RELOAD_OK" ||
          code === "SOURCE_RECOVERY_DECODER_ALREADY_PLAYING") {
        if (expiredSourceTrack === id) {
          expiredSourceTrack = null;
          expiredSourceFailedTrack = null;
        }
        if (deferredSourceTrack === id) {
          deferredSourceTrack = null;
          deferredSourceFailedTrack = null;
        }
      }
      if (code === "SOURCE_RECOVERY_EXHAUSTED") {
        if (expiredSourceTrack === id) {
          expiredSourceFailedTrack = id;
          expiredSourceTrack = null;
        }
        if (deferredSourceTrack === id) {
          deferredSourceFailedTrack = id;
          deferredSourceTrack = null;
        }
      }
    }
  });
  // W99: if a previously verified current CELIKOM decoder unexpectedly
  // switches to Yandex's original source while still playing, reuse the
  // existing bounded recovery path. Exact current-track + live entitlement
  // are rechecked; original songs that were never mapped are never touched.
  window.__celikomBridgeNativeRecoverSourceLeft = trackId => {
    if (typeof trackId !== "string" || !/^[1-9][0-9]{0,23}$/.test(trackId) ||
        playerSourceRefresh.currentTrackId() !== trackId ||
        !adapter.enabled || !attached || stopped ||
        !playerSourceRefresh.attached) return false;
    const now = Date.now();
    if (lastSourceLeftAttemptTrack === trackId &&
        now - lastSourceLeftAttemptAt < 15000) return false;
    if (!sourceRecovery.schedule(trackId)) return false;
    lastSourceLeftAttemptTrack = trackId;
    lastSourceLeftAttemptAt = now;
    report("SOURCE_LEFT_CURRENT_RECOVERY_SCHEDULED", trackId);
    return true;
  };
  deferredRecovery = createDeferredTrackRecovery({
    currentTrackId: () => playerSourceRefresh.currentTrackId(),
    active: () => !stopped && attached && adapter.enabled &&
      playerSourceRefresh.attached,
    schedule: id => sourceRecovery.schedule(id),
    onEvent: (code, id) => {
      report(code, id);
      if (code === "SOURCE_DEFERRED_PROMOTED") {
        deferredSourceTrack = id;
        deferredSourceFailedTrack = null;
      }
    }
  });
  window.__celikomBridgeNativeCheckDeferred = () => deferredRecovery.check();
  // Only CDP-verified current decoder source may suppress an unfired 403
  // refresh. HTTP206 alone/prefetch/mapping never qualify. No player calls.
  window.__celikomBridgeNativeConfirmedCurrentSource = trackId => {
    if (typeof trackId !== "string" || !/^[1-9][0-9]{0,23}$/.test(trackId) ||
        stopped || !attached || !adapter.enabled ||
        playerSourceRefresh.currentTrackId() !== trackId)
      return false;
    return sourceRecovery.confirmedCurrentSource(trackId);
  };
  // On native media GET 403 for a previously valid but expired grant, allow
  // the main-process witness to request recovery of EXACT current track only.
  // Never touch another track, queue, pause button or URLs from CDP.
  window.__celikomBridgeNativeRecoverExpired = trackId => {
    if (typeof trackId !== "string" || !/^[1-9][0-9]{0,23}$/.test(trackId) ||
        playerSourceRefresh.currentTrackId() !== trackId ||
        !adapter.enabled || !attached || stopped) return false;
    // Yandex may retry the same stale URL in multiple range requests. Never
    // spawn unlimited recovery loops or repeatedly disturb a loaded player.
    const now = Date.now();
    if (lastExpiredAttemptTrack === trackId &&
        now - lastExpiredAttemptAt < 60000) return false;
    if (!sourceRecovery.schedule(trackId)) return false;
    lastExpiredAttemptTrack = trackId;
    lastExpiredAttemptAt = now;
    expiredSourceTrack = trackId;
    expiredSourceFailedTrack = null;
    report("SOURCE_EXPIRED_NATIVE_403", trackId);
    return true;
  };
  // Only the actual current player entity, never a prefetched song.
  // No player controls or media source are changed by this UI-only observer.
  window.__celikomBridgeNativeCurrentTrackId = () => playerSourceRefresh.currentTrackId();
  window.__celikomBridgeNativeCurrentTrack = () => playerSourceRefresh.currentTrack();

  window.__celikomBridgeNativeSetState = next => {
    if (stopped) return;
    const previousActive = adapter.enabled;
    const currentTrackId = playerSourceRefresh.currentTrackId();
    const currentWasMapped = currentTrackId ? adapter.hasMappedTrack(currentTrackId) : false;
    let origin = "";
    try {
      const uri = new URL(next?.apiOrigin);
      if (uri.protocol === "https:" && uri.pathname === "/" &&
          !uri.username && !uri.password && !uri.search && !uri.hash &&
          uri.origin === next.apiOrigin) origin = uri.origin;
    } catch {}
    const originChanged = origin !== apiOrigin;
    if (originChanged) {
      sourceRecovery.cancel();
      deferredRecovery.cancel();
      deferredSourceTrack = null;
      deferredSourceFailedTrack = null;
      expiredSourceTrack = null;
      expiredSourceFailedTrack = null;
      lastExpiredAttemptTrack = null;
      lastExpiredAttemptAt = 0;
      lastSourceLeftAttemptTrack = null;
      lastSourceLeftAttemptAt = 0;
      apiOrigin = origin;
      adapter.disable();
    }
    const shouldEnable = next?.enabled === true && next?.signedIn === true &&
      !!origin && attached;
    if (shouldEnable) adapter.enable();
    else {
      sourceRecovery.cancel();
      deferredRecovery.cancel();
      deferredSourceTrack = null;
      deferredSourceFailedTrack = null;
      expiredSourceTrack = null;
      expiredSourceFailedTrack = null;
      lastExpiredAttemptTrack = null;
      lastExpiredAttemptAt = 0;
      lastSourceLeftAttemptTrack = null;
      lastSourceLeftAttemptAt = 0;
      adapter.disable();
    }
    const nextActive = adapter.enabled;
    const transitionChanged = previousActive !== nextActive || originChanged;
    const transitionGeneration = transitionChanged
      ? ++stateTransitionGeneration : stateTransitionGeneration;

    // ORIGINAL songs are transparent: a VPN/entitlement state transition
    // must not call QUALITY_CHANGE unless CELIKOM previously returned a
    // replacement for this exact current Yandex entity. On re-enable, first
    // ask the authenticated resolver; only a confirmed grant can trigger a
    // source refresh. No local/offline entitlement is inferred here.
    if (stateSeen && transitionChanged && attached && playerSourceRefresh.attached) {
      if (!currentTrackId) {
        report("NATIVE_STATE_CURRENT_SOURCE_UNKNOWN");
      } else if (previousActive && !nextActive) {
        if (currentWasMapped) {
          report("NATIVE_ORIGINAL_SOURCE_RESTORE", currentTrackId);
          void playerSourceRefresh.request(currentTrackId).then(ok => {
            if (transitionGeneration !== stateTransitionGeneration) return;
            if (ok) adapter.forgetMappedTrack(currentTrackId);
            report(ok ? "NATIVE_ORIGINAL_SOURCE_RESTORED" :
              "NATIVE_ORIGINAL_SOURCE_RESTORE_DEFERRED", currentTrackId);
          });
        } else {
          report(adapter.classificationForTrack(currentTrackId) === "ORIGINAL"
            ? "NATIVE_ORIGINAL_SOURCE_NO_RELOAD" : "NATIVE_UNKNOWN_SOURCE_NO_RELOAD",
            currentTrackId);
        }
      } else if (nextActive && (!previousActive || originChanged)) {
        report("NATIVE_CURRENT_SOURCE_REVALIDATE", currentTrackId);
        void adapter.prime(currentTrackId).then(found => {
          if (transitionGeneration !== stateTransitionGeneration || stopped ||
              !adapter.enabled ||
              playerSourceRefresh.currentTrackId() !== currentTrackId) {
            report("NATIVE_CURRENT_SOURCE_REVALIDATE_STALE", currentTrackId);
            return;
          }
          if (found) {
            report("NATIVE_REPLACEMENT_SOURCE_RELOAD", currentTrackId);
            void playerSourceRefresh.request(currentTrackId).then(ok => {
              if (transitionGeneration !== stateTransitionGeneration) return;
              report(ok ? "NATIVE_REPLACEMENT_SOURCE_RELOAD_OK" :
                "NATIVE_REPLACEMENT_SOURCE_RELOAD_DEFERRED", currentTrackId);
            });
          } else if (currentWasMapped) {
            // A prior CELIKOM source may still be loaded under the old route.
            // With no fresh grant, restore Yandex original instead of reusing it.
            report("NATIVE_ORIGINAL_SOURCE_RESTORE", currentTrackId);
            void playerSourceRefresh.request(currentTrackId).then(ok => {
              if (transitionGeneration !== stateTransitionGeneration) return;
              if (ok) adapter.forgetMappedTrack(currentTrackId);
              report(ok ? "NATIVE_ORIGINAL_SOURCE_RESTORED" :
                "NATIVE_ORIGINAL_SOURCE_RESTORE_DEFERRED", currentTrackId);
            });
          } else {
            report(adapter.classificationForTrack(currentTrackId) === "ORIGINAL"
              ? "NATIVE_ORIGINAL_SOURCE_NO_RELOAD" : "NATIVE_UNKNOWN_SOURCE_NO_RELOAD",
              currentTrackId);
          }
        });
      }
    }
    stateSeen = true;
    const status = adapter.enabled ? "NATIVE_CONNECTED" : "ORIGINAL";
    if (status !== lastReported) {
      lastReported = status;
      report(adapter.enabled ? "RENDERER_STATE_ON" : "RENDERER_STATE_OFF");
      console.info("[CELIKOM] Native bridge state received");
    }
  };
  window.__celikomBridgeNativeStatus = () => {
    if (stopped || !attached || !adapter.enabled) return "ORIGINAL";
    const currentId = playerSourceRefresh.currentTrackId();
    if ((expiredSourceTrack && expiredSourceTrack === currentId) ||
        (deferredSourceTrack && deferredSourceTrack === currentId))
      return "NATIVE_RECOVERING";
    if ((expiredSourceFailedTrack && expiredSourceFailedTrack === currentId) ||
        (deferredSourceFailedTrack && deferredSourceFailedTrack === currentId))
      return "NATIVE_SOURCE_FAILED";
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
          // Exact original Yandex 5.126.1, no alternate media player.
          // Failure to bind is safely a no-op; core replacement stays intact.
          playerSourceRefresh.attach(webpackRequire);
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
    sourceRecovery.cancel();
    deferredRecovery.cancel();
    clearInterval(finder);
    clearInterval(deadline);
    for (const job of pending.values()) job.finish(null);
    queued.length = 0;
    playerSourceRefresh.dispose();
    adapter.dispose();
    delete window.__celikomBridgeNativeDrain;
    delete window.__celikomBridgeNativeReceive;
    delete window.__celikomBridgeNativeSetState;
    delete window.__celikomBridgeNativeStatus;
    delete window.__celikomBridgeNativeCurrentTrackId;
    delete window.__celikomBridgeNativeCurrentTrack;
    delete window.__celikomBridgeNativeRecoverExpired;
    delete window.__celikomBridgeNativeRecoverSourceLeft;
    delete window.__celikomBridgeNativeConfirmedCurrentSource;
    delete window.__celikomBridgeNativeRefreshUnfetched;
    delete window.__celikomBridgeNativeCheckDeferred;
    delete window.__celikomBridgeNativeDrainDiagnostics;
  }, { once: true });
})();
