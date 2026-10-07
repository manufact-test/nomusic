(function startCelikomMainWorldBridge() {
  "use strict";

  const core = globalThis.__CELIKOM_POC_CORE__;
  if (!core) {
    return;
  }

  const BRIDGE_KEY = "__CELIKOM_POC_MAIN_BRIDGE_V4__";
  if (globalThis[BRIDGE_KEY]) {
    globalThis[BRIDGE_KEY].announce?.();
    return;
  }

  const MESSAGE_DIRECTION_IN = "to-main";
  const MESSAGE_DIRECTION_OUT = "from-main";
  const HEARTBEAT_VISIBLE_TIMEOUT_MS = 12000;
  const HEARTBEAT_HIDDEN_TIMEOUT_MS = 120000;
  const SNAPSHOT_INTERVAL_MS = 500;
  const TIME_EVENT_THROTTLE_MS = 250;
  const MAX_CATALOG_ENTRIES = 1200;
  const MAX_CATALOG_NODES_PER_PAYLOAD = 20000;
  const PLAYER_CONTAINER_SELECTOR = [
    "[data-testid*='player' i]",
    "[data-test-id*='player' i]",
    "[data-test*='player' i]",
    "[class*='playerbar' i]",
    "[class*='player-bar' i]",
    "[class*='nowplaying' i]",
    "[class*='now-playing' i]"
  ].join(",");

  let controllerSession = null;
  let lastHeartbeatAt = 0;
  let hooksInstalled = false;
  let mutationObserver = null;
  let mutationDebounceTimer = null;
  let snapshotTimer = null;
  let lastSnapshotSignature = "";
  let lastTimeEventAt = 0;
  let lastEventElement = null;
  let lastEventAt = 0;
  let guard = null;
  let mediaSequence = 0;
  let statePatchCursor = 0;
  let catalogRefreshTimer = null;

  const knownMedia = new Map();
  const mediaIds = new WeakMap();
  const nativeHooks = {};
  const trackCatalog = new Map();
  const xhrUrls = new WeakMap();
  const scannedStateScripts = new WeakSet();

  function now() {
    return Date.now();
  }

  function safeCall(callback, fallback = null) {
    try {
      return callback();
    } catch (_error) {
      return fallback;
    }
  }

  function round(value, digits = 3) {
    const factor = 10 ** digits;
    return Math.round(core.finiteNumber(value, 0) * factor) / factor;
  }

  function isReplacementElement(element) {
    return element instanceof HTMLMediaElement && element.dataset?.celikomReplacement === "true";
  }

  function isKnownAdMedia(element) {
    if (!(element instanceof HTMLMediaElement)) return false;
    const identity = `${element.id || ""} ${element.className || ""}`;
    if (/(?:^|[\s_-])(?:video-ad-player|ad-player)(?:$|[\s_-])/i.test(identity)) return true;
    if (safeCall(() => element.closest("#video-ad-container, [class*='VideoAd_'], [class*='AdContainer_']"), null)) return true;

    if (core.isYandexAdMediaCandidate({
      tag: element.tagName,
      source: safeCall(() => element.currentSrc || element.src, ""),
      duration: safeCall(() => element.duration, 0),
      connected: Boolean(safeCall(() => element.isConnected, false))
    })) return true;

    return false;
  }

  function registerMedia(element) {
    if (!(element instanceof HTMLMediaElement) || isReplacementElement(element)) {
      return null;
    }

    let id = mediaIds.get(element);
    if (!id) {
      mediaSequence += 1;
      id = `media-${mediaSequence}`;
      mediaIds.set(element, id);
      knownMedia.set(id, element);
    }
    return id;
  }

  function scanMedia() {
    safeCall(() => {
      document.querySelectorAll("audio,video").forEach(registerMedia);
    });

    for (const [id, element] of knownMedia) {
      const stale = !element.isConnected && element.paused && !Number.isFinite(mediaScore(element)) && element !== lastEventElement && guard?.element !== element;
      if (stale) {
        knownMedia.delete(id);
      }
    }
  }

  function desiredVolumeState(element) {
    if (guard?.element === element) {
      return {
        volume: guard.desiredVolume,
        muted: guard.desiredMuted,
        guarded: true
      };
    }
    return {
      volume: core.clamp(safeCall(() => element.volume, 1), 0, 1),
      muted: Boolean(safeCall(() => element.muted, false)),
      guarded: false
    };
  }

  function mediaState(element) {
    if (!(element instanceof HTMLMediaElement)) {
      return null;
    }

    const id = registerMedia(element);
    if (!id) {
      return null;
    }

    const desired = desiredVolumeState(element);
    return {
      mediaId: id,
      tag: element.tagName.toLowerCase(),
      paused: Boolean(element.paused),
      ended: Boolean(element.ended),
      seeking: Boolean(element.seeking),
      currentTime: round(element.currentTime),
      duration: Number.isFinite(element.duration) ? round(element.duration) : null,
      playbackRate: round(element.playbackRate),
      volume: round(desired.volume),
      muted: desired.muted,
      guarded: desired.guarded,
      readyState: Number(element.readyState || 0),
      networkState: Number(element.networkState || 0),
      source: core.summarizeMediaSource(element.currentSrc || element.src || ""),
      connected: Boolean(element.isConnected)
    };
  }

  function mediaScore(element) {
    return core.scoreMediaCandidate({
      isMedia: element instanceof HTMLMediaElement,
      replacement: isReplacementElement(element),
      knownAd: isKnownAdMedia(element),
      paused: Boolean(safeCall(() => element.paused, true)),
      ended: Boolean(safeCall(() => element.ended, false)),
      duration: safeCall(() => element.duration, 0),
      currentTime: safeCall(() => element.currentTime, 0),
      readyState: safeCall(() => element.readyState, 0),
      networkState: safeCall(() => element.networkState, 0),
      hasSource: Boolean(safeCall(() => element.currentSrc || element.src, "")),
      tag: safeCall(() => element.tagName, ""),
      connected: Boolean(safeCall(() => element.isConnected, false)),
      recentEvent: element === lastEventElement && now() - lastEventAt < 5000
    });
  }

  function selectMaster() {
    if (guard?.element instanceof HTMLMediaElement) {
      return guard.element;
    }

    scanMedia();
    let best = null;
    let bestScore = -Infinity;
    for (const element of knownMedia.values()) {
      const score = mediaScore(element);
      if (score > bestScore) {
        best = element;
        bestScore = score;
      }
    }
    return best;
  }

  function mediaCandidateDiagnostics() {
    return [...knownMedia.values()].slice(-8).map((element) => {
      const score = mediaScore(element);
      const source = element.currentSrc || element.src || "";
      let rejectedReason = null;
      if (isKnownAdMedia(element)) rejectedReason = "known-ad-media";
      else if (!Number.isFinite(score)) rejectedReason = "empty-or-unusable-media";
      return {
        mediaId: registerMedia(element),
        tag: element.tagName.toLowerCase(),
        eligible: Number.isFinite(score),
        score: Number.isFinite(score) ? score : null,
        rejectedReason,
        paused: Boolean(element.paused),
        currentTime: round(element.currentTime),
        duration: Number.isFinite(element.duration) ? round(element.duration) : null,
        readyState: Number(element.readyState || 0),
        source: core.summarizeMediaSource(source),
        connected: Boolean(element.isConnected)
      };
    });
  }

  function mediaSessionMetadata() {
    const metadata = safeCall(() => navigator.mediaSession?.metadata, null);
    const artwork = safeCall(() => Array.from(metadata?.artwork || []), []);
    return {
      title: String(metadata?.title || "").slice(0, 240),
      artist: String(metadata?.artist || "").slice(0, 240),
      album: String(metadata?.album || "").slice(0, 240),
      coverUri: String(artwork.at(-1)?.src || artwork[0]?.src || "").slice(0, 1000)
    };
  }

  function elementLooksActive(element) {
    const classText = String(element.className || "") + " " + String(element.parentElement?.className || "");
    return /(?:^|[\s_-])(active|current|playing|selected)(?:$|[\s_-])/i.test(classText);
  }

  function insidePlayer(element) {
    return Boolean(safeCall(() => element.closest(PLAYER_CONTAINER_SELECTOR), null));
  }

  function visibleElement(element) {
    return safeCall(() => {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    }, false);
  }

  function safePath(rawUrl) {
    return safeCall(() => new URL(rawUrl, location.href).pathname, "");
  }

  function rememberTrack(entry, source) {
    if (!entry?.id) return false;
    const next = {
      ...entry,
      source: String(source || entry.source || "page-state"),
      catalogSeenAt: now()
    };
    const previous = trackCatalog.get(next.id);
    const changed = !previous || JSON.stringify({
      title: previous.title,
      artists: previous.artists,
      album: previous.album,
      durationMs: previous.durationMs,
      coverUri: previous.coverUri
    }) !== JSON.stringify({
      title: next.title,
      artists: next.artists,
      album: next.album,
      durationMs: next.durationMs,
      coverUri: next.coverUri
    });

    if (previous) trackCatalog.delete(next.id);
    trackCatalog.set(next.id, next);
    while (trackCatalog.size > MAX_CATALOG_ENTRIES) {
      trackCatalog.delete(trackCatalog.keys().next().value);
    }
    return changed;
  }

  function ingestTrackPayload(payload, source) {
    if (!payload || typeof payload !== "object") return 0;

    const stack = [payload];
    const seen = new WeakSet();
    let visited = 0;
    let changed = 0;

    while (stack.length && visited < MAX_CATALOG_NODES_PER_PAYLOAD) {
      const value = stack.pop();
      if (!value || typeof value !== "object" || seen.has(value)) continue;
      seen.add(value);
      visited += 1;

      const entry = core.trackCatalogEntryFromValue(value);
      if (entry && rememberTrack(entry, source)) changed += 1;

      const children = safeCall(() => Object.values(value), []);
      for (const child of children) {
        if (child && typeof child === "object") stack.push(child);
      }
    }
    return changed;
  }

  function scanStatePatches() {
    const batches = safeCall(() => globalThis.__STATE_PATCHES__, null);
    if (Array.isArray(batches)) {
      if (statePatchCursor > batches.length) statePatchCursor = 0;
      for (; statePatchCursor < batches.length; statePatchCursor += 1) {
        ingestTrackPayload(batches[statePatchCursor], "yandex-state-patches");
      }
    }
    scanInlineStateScripts();
  }

  function jsonValueEnd(source, start) {
    let depth = 0;
    let quoted = false;
    let escaped = false;
    for (let index = start; index < source.length; index += 1) {
      const character = source[index];
      if (quoted) {
        if (escaped) escaped = false;
        else if (character === "\\") escaped = true;
        else if (character === "\"") quoted = false;
        continue;
      }
      if (character === "\"") {
        quoted = true;
      } else if (character === "[" || character === "{") {
        depth += 1;
      } else if (character === "]" || character === "}") {
        depth -= 1;
        if (depth === 0) return index + 1;
      }
    }
    return -1;
  }

  function scanInlineStateScripts() {
    safeCall(() => {
      document.querySelectorAll("script:not([src])").forEach((script) => {
        if (scannedStateScripts.has(script)) return;
        scannedStateScripts.add(script);
        const source = String(script.textContent || "");
        if (!source.includes("__STATE_PATCHES__") || source.length > 5 * 1024 * 1024) return;

        let cursor = 0;
        while (cursor < source.length) {
          const pushAt = source.indexOf(".push(", cursor);
          if (pushAt < 0) break;
          const start = source.indexOf("[", pushAt + 6);
          if (start < 0) break;
          const end = jsonValueEnd(source, start);
          if (end < 0) break;
          try {
            ingestTrackPayload(JSON.parse(source.slice(start, end)), "yandex-inline-state");
          } catch (_error) {
            // Ignore non-JSON inline code while retaining the live-state path.
          }
          cursor = end;
        }
      });
    });
  }

  function scheduleCatalogSnapshot(source) {
    if (catalogRefreshTimer) return;
    catalogRefreshTimer = setTimeout(() => {
      catalogRefreshTimer = null;
      emitSnapshot(`catalog:${source}`, true);
    }, 40);
  }

  function captureJsonResponse(response, source) {
    const contentType = safeCall(() => response.headers.get("content-type"), "") || "";
    const contentLength = Number(safeCall(() => response.headers.get("content-length"), 0) || 0);
    if (!isYandexNetworkUrl(response.url) || !/\bjson\b/i.test(contentType) || contentLength > 5 * 1024 * 1024) return;

    safeCall(() => {
      response.clone().text().then((body) => {
        if (body.length > 5 * 1024 * 1024) return;
        const payload = JSON.parse(body);
        if (ingestTrackPayload(payload, source) > 0) scheduleCatalogSnapshot(source);
      }).catch(() => {});
    });
  }

  function isYandexNetworkUrl(rawUrl) {
    return safeCall(() => {
      const hostname = new URL(String(rawUrl || ""), location.href).hostname.toLocaleLowerCase();
      return ["yandex.ru", "yandex.net", "yandex.com", "yandex.by", "yandex.kz"]
        .some((domain) => hostname === domain || hostname.endsWith(`.${domain}`));
    }, false);
  }

  function installNetworkHooks() {
    if (!nativeHooks.fetch && typeof globalThis.fetch === "function") {
      nativeHooks.fetch = globalThis.fetch;
      nativeHooks.fetchWrapper = async function celikomObservedFetch(...args) {
        const response = await Reflect.apply(nativeHooks.fetch, this, args);
        captureJsonResponse(response, "fetch-json");
        return response;
      };
      globalThis.fetch = nativeHooks.fetchWrapper;
    }

    const prototype = globalThis.XMLHttpRequest?.prototype;
    if (!prototype || nativeHooks.xhrOpen) return;
    nativeHooks.xhrOpen = prototype.open;
    nativeHooks.xhrSend = prototype.send;
    nativeHooks.xhrOpenWrapper = function celikomObservedXhrOpen(method, url, ...args) {
      safeCall(() => xhrUrls.set(this, String(url || "")));
      return Reflect.apply(nativeHooks.xhrOpen, this, [method, url, ...args]);
    };
    nativeHooks.xhrSendWrapper = function celikomObservedXhrSend(...args) {
      this.addEventListener("loadend", () => {
        if (!isYandexNetworkUrl(xhrUrls.get(this))) return;
        const contentType = safeCall(() => this.getResponseHeader("content-type"), "") || "";
        if (!/\bjson\b/i.test(contentType)) return;
        try {
          const payload = this.responseType === "json"
            ? this.response
            : JSON.parse(String(this.responseText || ""));
          if (ingestTrackPayload(payload, "xhr-json") > 0) scheduleCatalogSnapshot("xhr-json");
        } catch (_error) {
          // Non-JSON and inaccessible responses are irrelevant to track discovery.
        }
      }, { once: true });
      return Reflect.apply(nativeHooks.xhrSend, this, args);
    };
    prototype.open = nativeHooks.xhrOpenWrapper;
    prototype.send = nativeHooks.xhrSendWrapper;
  }

  function restoreNetworkHooks() {
    if (nativeHooks.fetch && globalThis.fetch === nativeHooks.fetchWrapper) {
      globalThis.fetch = nativeHooks.fetch;
    }
    const prototype = globalThis.XMLHttpRequest?.prototype;
    if (prototype && nativeHooks.xhrOpen && prototype.open === nativeHooks.xhrOpenWrapper) {
      prototype.open = nativeHooks.xhrOpen;
    }
    if (prototype && nativeHooks.xhrSend && prototype.send === nativeHooks.xhrSendWrapper) {
      prototype.send = nativeHooks.xhrSend;
    }
    for (const key of ["fetch", "fetchWrapper", "xhrOpen", "xhrSend", "xhrOpenWrapper", "xhrSendWrapper"]) {
      delete nativeHooks[key];
    }
  }

  function playerRoot() {
    const heading = document.querySelector("#player-region");
    return heading?.closest("section") || document.querySelector("[class*='PlayerBar_root__']");
  }

  function textFrom(root, selectors) {
    if (!root) return "";
    for (const selector of selectors) {
      const text = String(root.querySelector(selector)?.textContent || "").trim();
      if (text) return text;
    }
    return "";
  }

  function playerDomMetadata() {
    const root = playerRoot();
    if (!root) return { title: "", artist: "", album: "", coverUri: "", durationMs: 0 };

    const cover = root.querySelector("img[src*='get-music-content'], img[src]");
    const timecode = root.querySelector("input[type='range'][max]");
    const durationSeconds = core.finiteNumber(timecode?.max, 0);
    return {
      title: textFrom(root, ["[class*='Meta_title__']", "[class*='title__']"]),
      artist: textFrom(root, ["[class*='Meta_artistCaption__']", "[class*='artists__']"]),
      album: "",
      coverUri: String(cover?.currentSrc || cover?.src || ""),
      durationMs: durationSeconds > 0 ? Math.round(durationSeconds * 1000) : 0
    };
  }

  function activeCardMetadata() {
    const root = document.querySelector("[class*='CommonTrack_root_current__'], [class*='Track_root_current__']");
    if (!root) return { title: "", artist: "", album: "", coverUri: "", durationMs: 0 };
    const cover = root.querySelector("img[src*='get-music-content'], img[src]");
    return {
      title: textFrom(root, ["[class*='Meta_title__']", "[class*='title__']"]),
      artist: textFrom(root, ["[class*='Meta_artistCaption__']", "[class*='artists__']"]),
      album: "",
      coverUri: String(cover?.currentSrc || cover?.src || ""),
      durationMs: 0
    };
  }

  function playbackMetadata(master) {
    const session = mediaSessionMetadata();
    const player = playerDomMetadata();
    const activeCard = activeCardMetadata();
    const durationMs = Number.isFinite(master?.duration) && master.duration > 0
      ? Math.round(master.duration * 1000)
      : player.durationMs;

    return {
      title: session.title || player.title || activeCard.title,
      artist: session.artist || player.artist || activeCard.artist,
      album: session.album || player.album || activeCard.album,
      coverUri: session.coverUri || player.coverUri || activeCard.coverUri,
      durationMs
    };
  }

  function collectTrackCandidates(metadata, master) {
    const candidates = [];

    scanStatePatches();
    const catalogMatch = core.pickTrackFromCatalog([...trackCatalog.values()], metadata, 100);
    candidates.push(...catalogMatch.ranked.filter((candidate) => candidate.score >= 100));

    safeCall(() => {
      document.querySelectorAll("a[href*='/track/']").forEach((anchor) => {
        const id = core.parseTrackIdFromUrl(anchor.href);
        if (!id) return;

        let score = 15;
        const signals = [];
        if (insidePlayer(anchor)) {
          score += 95;
          signals.push("player-container");
        }
        if (anchor.getAttribute("aria-current") === "true") {
          score += 70;
          signals.push("aria-current");
        }
        if (elementLooksActive(anchor)) {
          score += 35;
          signals.push("active-class");
        }
        if (visibleElement(anchor)) {
          score += 5;
        }

        const nearbyText = `${anchor.textContent || ""} ${anchor.parentElement?.textContent || ""}`.slice(0, 1000);
        const similarity = core.metadataSimilarity(nearbyText, metadata);
        if (similarity > 0) {
          score += similarity;
          signals.push("metadata-match");
        }

        candidates.push({
          id,
          score,
          source: "dom-track-link",
          evidence: `${safePath(anchor.href)} ${signals.join(",")}`.trim()
        });
      });
    });

    safeCall(() => {
      document.querySelectorAll("[data-track-id], [data-trackid], [data-track_id]").forEach((element) => {
        const raw = element.getAttribute("data-track-id") || element.getAttribute("data-trackid") || element.getAttribute("data-track_id");
        const id = core.normalizeTrackId(raw);
        if (!id) return;
        const inPlayer = insidePlayer(element);
        candidates.push({
          id,
          score: inPlayer ? 125 : 45,
          source: "dom-track-data",
          evidence: inPlayer ? "player-container" : "page-data"
        });
      });
    });

    const routeId = core.parseTrackIdFromUrl(location.href);
    if (routeId) {
      const titleSimilarity = core.metadataSimilarity(document.title, metadata);
      const playingBonus = master && !master.paused ? 10 : 0;
      candidates.push({
        id: routeId,
        score: 25 + titleSimilarity + playingBonus,
        source: "page-route",
        evidence: safePath(location.href)
      });
    }

    return candidates;
  }

  function trackState(master) {
    const metadata = playbackMetadata(master);
    const result = core.pickBestTrackCandidate(collectTrackCandidates(metadata, master), 70);
    return {
      id: result.selected?.id || null,
      confidence: result.selected?.score || 0,
      source: result.selected?.source || null,
      evidence: result.selected?.evidence || "",
      ambiguous: result.ambiguous,
      candidates: result.ranked,
      metadata,
      catalogSize: trackCatalog.size
    };
  }

  function buildSnapshot(reason) {
    const master = selectMaster();
    return {
      reason,
      observedAt: now(),
      route: `${location.origin}${location.pathname}`,
      track: trackState(master),
      player: mediaState(master),
      mediaCandidates: mediaCandidateDiagnostics(),
      guardActive: Boolean(guard),
      bridgeVersion: core.VERSION
    };
  }

  function snapshotSignature(snapshot) {
    return JSON.stringify({
      trackId: snapshot.track.id,
      source: snapshot.track.source,
      ambiguous: snapshot.track.ambiguous,
      mediaId: snapshot.player?.mediaId || null,
      paused: snapshot.player?.paused ?? true,
      ended: snapshot.player?.ended ?? false,
      seeking: snapshot.player?.seeking ?? false,
      timeBucket: Math.floor((snapshot.player?.currentTime || 0) * 2),
      volume: snapshot.player?.volume ?? 1,
      muted: snapshot.player?.muted ?? false,
      guardActive: snapshot.guardActive
    });
  }

  function post(type, payload = {}, requestId = null) {
    if (!controllerSession && type !== "BRIDGE_PRESENT") {
      return;
    }

    window.postMessage({
      channel: core.CHANNEL,
      direction: MESSAGE_DIRECTION_OUT,
      sessionId: controllerSession,
      type,
      requestId,
      payload,
      sentAt: now()
    }, "*");
  }

  function emitSnapshot(reason, force = false) {
    if (!controllerSession) {
      return;
    }
    const snapshot = buildSnapshot(reason);
    const signature = snapshotSignature(snapshot);
    if (force || signature !== lastSnapshotSignature) {
      lastSnapshotSignature = signature;
      post("PLAYER_STATE", snapshot);
    }
  }

  function markMediaEvent(element, eventType) {
    if (!(element instanceof HTMLMediaElement) || isReplacementElement(element)) {
      return;
    }
    registerMedia(element);
    lastEventElement = element;
    lastEventAt = now();

    if (eventType === "timeupdate" && now() - lastTimeEventAt < TIME_EVENT_THROTTLE_MS) {
      return;
    }
    if (eventType === "timeupdate") {
      lastTimeEventAt = now();
    }

    const snapshot = buildSnapshot(`event:${eventType}`);
    lastSnapshotSignature = snapshotSignature(snapshot);
    post("PLAYER_EVENT", {
      event: eventType,
      snapshot
    });
  }

  function onMediaEvent(event) {
    markMediaEvent(event.target, event.type);
  }

  const MEDIA_EVENTS = [
    "play",
    "playing",
    "pause",
    "seeking",
    "seeked",
    "timeupdate",
    "ended",
    "ratechange",
    "volumechange",
    "loadedmetadata",
    "durationchange",
    "emptied",
    "error"
  ];

  function installPrototypeHooks() {
    const prototype = HTMLMediaElement.prototype;
    if (!nativeHooks.play) {
      nativeHooks.play = prototype.play;
      nativeHooks.playWrapper = function celikomObservedPlay(...args) {
        if (!isReplacementElement(this)) {
          registerMedia(this);
          lastEventElement = this;
          lastEventAt = now();
          queueMicrotask(() => emitSnapshot("method:play", true));
        }
        return Reflect.apply(nativeHooks.play, this, args);
      };
      prototype.play = nativeHooks.playWrapper;
    }

    if (!nativeHooks.pause) {
      nativeHooks.pause = prototype.pause;
      nativeHooks.pauseWrapper = function celikomObservedPause(...args) {
        if (!isReplacementElement(this)) {
          registerMedia(this);
          lastEventElement = this;
          lastEventAt = now();
          queueMicrotask(() => emitSnapshot("method:pause", true));
        }
        return Reflect.apply(nativeHooks.pause, this, args);
      };
      prototype.pause = nativeHooks.pauseWrapper;
    }

    if (!nativeHooks.load) {
      nativeHooks.load = prototype.load;
      nativeHooks.loadWrapper = function celikomObservedLoad(...args) {
        if (!isReplacementElement(this)) {
          registerMedia(this);
          queueMicrotask(() => emitSnapshot("method:load", true));
        }
        return Reflect.apply(nativeHooks.load, this, args);
      };
      prototype.load = nativeHooks.loadWrapper;
    }
  }

  function restorePrototypeHooks() {
    const prototype = HTMLMediaElement.prototype;
    if (nativeHooks.play && prototype.play === nativeHooks.playWrapper) {
      prototype.play = nativeHooks.play;
    }
    if (nativeHooks.pause && prototype.pause === nativeHooks.pauseWrapper) {
      prototype.pause = nativeHooks.pause;
    }
    if (nativeHooks.load && prototype.load === nativeHooks.loadWrapper) {
      prototype.load = nativeHooks.load;
    }
    delete nativeHooks.play;
    delete nativeHooks.playWrapper;
    delete nativeHooks.pause;
    delete nativeHooks.pauseWrapper;
    delete nativeHooks.load;
    delete nativeHooks.loadWrapper;
  }

  function installHistoryHooks() {
    for (const name of ["pushState", "replaceState"]) {
      if (nativeHooks[name]) continue;
      nativeHooks[name] = history[name];
      nativeHooks[`${name}Wrapper`] = function celikomObservedHistory(...args) {
        const result = Reflect.apply(nativeHooks[name], this, args);
        queueMicrotask(() => emitSnapshot(`history:${name}`, true));
        return result;
      };
      history[name] = nativeHooks[`${name}Wrapper`];
    }
  }

  function restoreHistoryHooks() {
    for (const name of ["pushState", "replaceState"]) {
      if (nativeHooks[name] && history[name] === nativeHooks[`${name}Wrapper`]) {
        history[name] = nativeHooks[name];
      }
      delete nativeHooks[name];
      delete nativeHooks[`${name}Wrapper`];
    }
  }

  function installHooks() {
    if (hooksInstalled) return;
    hooksInstalled = true;
    installPrototypeHooks();
    installHistoryHooks();
    installNetworkHooks();
    MEDIA_EVENTS.forEach((eventName) => document.addEventListener(eventName, onMediaEvent, true));
    window.addEventListener("popstate", onNavigation);
    window.addEventListener("hashchange", onNavigation);

    mutationObserver = new MutationObserver(() => {
      if (mutationDebounceTimer) return;
      mutationDebounceTimer = setTimeout(() => {
        mutationDebounceTimer = null;
        scanMedia();
        emitSnapshot("dom-mutation");
      }, 80);
    });
    mutationObserver.observe(document, { childList: true, subtree: true, attributes: true, attributeFilter: ["href", "aria-current", "data-track-id", "data-trackid", "data-track_id"] });

    scanMedia();
    snapshotTimer = setInterval(() => emitSnapshot("poll"), SNAPSHOT_INTERVAL_MS);
  }

  function teardownHooks() {
    if (!hooksInstalled) return;
    hooksInstalled = false;
    MEDIA_EVENTS.forEach((eventName) => document.removeEventListener(eventName, onMediaEvent, true));
    window.removeEventListener("popstate", onNavigation);
    window.removeEventListener("hashchange", onNavigation);
    mutationObserver?.disconnect();
    mutationObserver = null;
    clearTimeout(mutationDebounceTimer);
    mutationDebounceTimer = null;
    clearInterval(snapshotTimer);
    snapshotTimer = null;
    clearTimeout(catalogRefreshTimer);
    catalogRefreshTimer = null;
    restorePrototypeHooks();
    restoreHistoryHooks();
    restoreNetworkHooks();
  }

  function onNavigation() {
    queueMicrotask(() => emitSnapshot("navigation", true));
  }

  function forceMuted(element) {
    if (!guard || guard.element !== element) return;
    guard.ignoreVolumeEventsUntil = performance.now() + 150;
    safeCall(() => {
      element.muted = true;
    });
  }

  function onGuardVolumeChange() {
    if (!guard) return;
    const element = guard.element;
    const internalChange = performance.now() < guard.ignoreVolumeEventsUntil && element.muted === true;
    if (!internalChange) {
      guard.desiredVolume = core.clamp(element.volume, 0, 1);
      guard.desiredMuted = Boolean(element.muted);
    }
    if (!element.muted) {
      forceMuted(element);
    }
    post("VOLUME_INTENT", {
      volume: guard.desiredVolume,
      muted: guard.desiredMuted
    });
  }

  function engageGuard(mediaId) {
    const element = knownMedia.get(String(mediaId || "")) || selectMaster();
    if (!(element instanceof HTMLMediaElement) || isReplacementElement(element)) {
      throw new Error("Original media element is unavailable");
    }

    releaseGuard("re-engage");
    guard = {
      element,
      mediaId: registerMedia(element),
      desiredVolume: core.clamp(element.volume, 0, 1),
      desiredMuted: Boolean(element.muted),
      ignoreVolumeEventsUntil: 0,
      engagedAt: now()
    };
    element.addEventListener("volumechange", onGuardVolumeChange);
    forceMuted(element);
    emitSnapshot("guard:engaged", true);
    return {
      mediaId: guard.mediaId,
      volume: guard.desiredVolume,
      muted: guard.desiredMuted
    };
  }

  function releaseGuard(reason = "unspecified") {
    if (!guard) {
      return { released: false, reason };
    }

    const current = guard;
    guard = null;
    current.element.removeEventListener("volumechange", onGuardVolumeChange);
    safeCall(() => {
      current.element.volume = core.clamp(current.desiredVolume, 0, 1);
      current.element.muted = Boolean(current.desiredMuted);
    });
    emitSnapshot(`guard:released:${reason}`, true);
    return { released: true, reason };
  }

  function stopReplacementElements() {
    safeCall(() => {
      document.querySelectorAll("[data-celikom-replacement='true']").forEach((element) => {
        if (element instanceof HTMLMediaElement) {
          safeCall(() => element.pause());
          safeCall(() => element.removeAttribute("src"));
          safeCall(() => element.load());
        }
        safeCall(() => element.remove());
      });
    });
  }

  function emergencyRestore(reason) {
    stopReplacementElements();
    const result = releaseGuard(reason);
    emitSnapshot(`emergency:${reason}`, true);
    return result;
  }

  function handleRequest(type, payload) {
    switch (type) {
      case "GET_SNAPSHOT":
        return buildSnapshot("request");
      case "GUARD_ENGAGE":
        return engageGuard(payload?.mediaId);
      case "GUARD_RELEASE":
        return releaseGuard(payload?.reason || "content-request");
      case "EMERGENCY_RESTORE":
        return emergencyRestore(payload?.reason || "content-emergency");
      default:
        throw new Error(`Unknown bridge request: ${type}`);
    }
  }

  function onWindowMessage(event) {
    if (event.source !== window) return;
    const message = event.data;
    if (!message || message.channel !== core.CHANNEL || message.direction !== MESSAGE_DIRECTION_IN) return;
    if (typeof message.sessionId !== "string" || message.sessionId.length < 8 || message.sessionId.length > 128) return;

    if (message.type === "INIT") {
      if (controllerSession && controllerSession !== message.sessionId) {
        emergencyRestore("controller-replaced");
      }
      controllerSession = message.sessionId;
      lastHeartbeatAt = now();
      installHooks();
      post("READY", { bridgeVersion: core.VERSION });
      emitSnapshot("init", true);
      return;
    }

    if (message.sessionId !== controllerSession) return;
    lastHeartbeatAt = now();

    if (message.type === "HEARTBEAT") {
      post("HEARTBEAT_ACK", {
        bridgeVersion: core.VERSION,
        hidden: document.hidden
      });
      return;
    }

    if (message.type === "SHUTDOWN") {
      emergencyRestore("content-shutdown");
      teardownHooks();
      controllerSession = null;
      return;
    }

    if (message.type === "REQUEST" && typeof message.requestId === "string") {
      try {
        const result = handleRequest(message.payload?.type, message.payload?.payload);
        post("RESPONSE", { ok: true, result }, message.requestId);
      } catch (error) {
        emergencyRestore("bridge-request-error");
        post("RESPONSE", { ok: false, error: String(error?.message || error) }, message.requestId);
      }
    }
  }

  function announce() {
    window.postMessage({
      channel: core.CHANNEL,
      direction: MESSAGE_DIRECTION_OUT,
      sessionId: controllerSession,
      type: "BRIDGE_PRESENT",
      payload: { bridgeVersion: core.VERSION },
      sentAt: now()
    }, "*");
  }

  window.addEventListener("message", onWindowMessage);
  window.addEventListener("pagehide", () => emergencyRestore("pagehide"), { capture: true });
  window.addEventListener("beforeunload", () => emergencyRestore("beforeunload"), { capture: true });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) return;
    if (controllerSession && now() - lastHeartbeatAt > HEARTBEAT_VISIBLE_TIMEOUT_MS) {
      post("BRIDGE_TIMEOUT", { elapsedMs: now() - lastHeartbeatAt, hidden: false });
      emergencyRestore("visibility-heartbeat-timeout");
      teardownHooks();
      controllerSession = null;
    }
    announce();
  });

  setInterval(() => {
    if (!controllerSession) return;
    const timeoutMs = document.hidden ? HEARTBEAT_HIDDEN_TIMEOUT_MS : HEARTBEAT_VISIBLE_TIMEOUT_MS;
    if (now() - lastHeartbeatAt <= timeoutMs) return;
    post("BRIDGE_TIMEOUT", { elapsedMs: now() - lastHeartbeatAt, hidden: document.hidden });
    emergencyRestore("heartbeat-timeout");
    teardownHooks();
    controllerSession = null;
  }, 500);

  Object.defineProperty(globalThis, BRIDGE_KEY, {
    value: Object.freeze({ announce, emergencyRestore }),
    configurable: false,
    enumerable: false,
    writable: false
  });

  announce();
})();
