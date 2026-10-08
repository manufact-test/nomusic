(function initYandexMusicAdapter(root) {
  "use strict";

  const core = root.__CELIKOM_PLAYER_CORE_V1__;
  if (!core) return;

  const GLOBAL_KEY = "__CELIKOM_YANDEX_ADAPTER_V1__";
  if (root[GLOBAL_KEY]) return;

  const MEDIA_EVENTS = Object.freeze([
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
  ]);
  const PLAYER_CONTAINER_SELECTOR = [
    "[data-testid*='player' i]",
    "[data-test-id*='player' i]",
    "[data-test*='player' i]",
    "[class*='playerbar' i]",
    "[class*='player-bar' i]",
    "[class*='nowplaying' i]",
    "[class*='now-playing' i]"
  ].join(",");
  const MAX_CATALOG_ENTRIES = 1200;
  const MAX_CATALOG_NODES_PER_PAYLOAD = 20000;
  const MAX_CAPTURE_BYTES = 5 * 1024 * 1024;
  const SNAPSHOT_INTERVAL_MS = 500;
  const TIME_EVENT_THROTTLE_MS = 250;

  class YandexMusicAdapter {
    constructor(environment = root) {
      this.environment = environment;
      this.window = environment.window || environment;
      this.document = environment.document || null;
      this.service = "yandex-music";
      this.mounted = false;
      this.sink = null;
      this.knownMedia = new Map();
      this.mediaIds = new WeakMap();
      this.mediaHandlers = new Map();
      this.trackCatalog = new Map();
      this.xhrUrls = new WeakMap();
      this.scannedStateScripts = new WeakSet();
      this.nativeHooks = {};
      this.mediaSequence = 0;
      this.statePatchCursor = 0;
      this.lastEventElement = null;
      this.lastEventAt = 0;
      this.lastTimeEventAt = 0;
      this.lastSnapshotSignature = "";
      this.lastTrackId = null;
      this.snapshotTimer = null;
      this.mutationObserver = null;
      this.mutationDebounceTimer = null;
      this.catalogRefreshTimer = null;
      this.onNavigation = this.onNavigation.bind(this);
    }

    now() {
      return Date.now();
    }

    safeCall(callback, fallback = null) {
      try {
        return callback();
      } catch (_error) {
        return fallback;
      }
    }

    defer(callback) {
      const queue = this.environment.queueMicrotask || globalThis.queueMicrotask;
      if (typeof queue === "function") queue(callback);
      else this.environment.setTimeout(callback, 0);
    }

    round(value, digits = 3) {
      const factor = 10 ** digits;
      return Math.round(core.finiteNumber(value, 0) * factor) / factor;
    }

    isMediaElement(element) {
      const Media = this.environment.HTMLMediaElement;
      return Boolean(Media && element instanceof Media);
    }

    isReplacementElement(element) {
      return this.isMediaElement(element) && element.dataset?.celikomReplacement === "true";
    }

    isKnownAdMedia(element) {
      if (!this.isMediaElement(element)) return false;
      const identity = `${element.id || ""} ${element.className || ""}`;
      if (/(?:^|[\s_-])(?:video-ad-player|ad-player)(?:$|[\s_-])/i.test(identity)) return true;
      if (this.safeCall(() => element.closest("#video-ad-container, [class*='VideoAd_'], [class*='AdContainer_']"), null)) return true;
      return core.isYandexAdMediaCandidate({
        tag: element.tagName,
        source: this.safeCall(() => element.currentSrc || element.src, ""),
        duration: this.safeCall(() => element.duration, 0),
        connected: Boolean(this.safeCall(() => element.isConnected, false))
      });
    }

    isUtilityMedia(element) {
      return this.isMediaElement(element) && core.isUtilityMediaCandidate({
        tag: element.tagName, source: element.currentSrc || element.src || "", duration: element.duration
      });
    }

    registerMedia(element) {
      if (!this.isMediaElement(element) || this.isReplacementElement(element)) return null;

      let id = this.mediaIds.get(element);
      if (!id) {
        id = `media-${++this.mediaSequence}`;
        this.mediaIds.set(element, id);
      }
      if (!this.knownMedia.has(id)) {
        this.knownMedia.set(id, element);
        const handler = (event) => this.onMediaEvent(event);
        this.mediaHandlers.set(id, handler);
        for (const eventName of MEDIA_EVENTS) element.addEventListener(eventName, handler);
      }
      return id;
    }

    unregisterMedia(id, element) {
      const handler = this.mediaHandlers.get(id);
      if (handler) {
        for (const eventName of MEDIA_EVENTS) element.removeEventListener(eventName, handler);
      }
      this.mediaHandlers.delete(id);
      this.knownMedia.delete(id);
    }

    scanMedia() {
      this.safeCall(() => {
        this.document?.querySelectorAll("audio,video").forEach((element) => this.registerMedia(element));
      });

      for (const [id, element] of this.knownMedia) {
        const stale = !element.isConnected && element.paused && !Number.isFinite(this.mediaScore(element)) && element !== this.lastEventElement;
        if (stale) this.unregisterMedia(id, element);
      }
    }

    getMediaElement(mediaId) {
      const element = this.knownMedia.get(mediaId);
      return element && this.isMediaElement(element) && !this.isReplacementElement(element) && !this.isKnownAdMedia(element) && !this.isUtilityMedia(element) ? element : null;
    }

    mediaState(element) {
      if (!this.isMediaElement(element)) return null;
      const mediaId = this.registerMedia(element);
      if (!mediaId) return null;
      const baseUrl = this.safeCall(() => this.environment.location.href, "https://music.yandex.ru/");
      return {
        mediaId,
        tag: String(element.tagName || "").toLocaleLowerCase(),
        paused: Boolean(element.paused),
        ended: Boolean(element.ended),
        seeking: Boolean(element.seeking),
        currentTime: this.round(element.currentTime),
        duration: Number.isFinite(element.duration) ? this.round(element.duration) : null,
        playbackRate: this.round(element.playbackRate),
        volume: this.round(core.clamp(element.volume, 0, 1)),
        muted: Boolean(element.muted),
        readyState: Number(element.readyState || 0),
        networkState: Number(element.networkState || 0),
        source: core.summarizeMediaSource(element.currentSrc || element.src || "", baseUrl),
        connected: Boolean(element.isConnected)
      };
    }

    mediaScore(element) {
      return core.scoreMediaCandidate({
        isMedia: this.isMediaElement(element),
        replacement: this.isReplacementElement(element),
        knownAd: this.isKnownAdMedia(element),
        knownUtility: this.isUtilityMedia(element),
        paused: Boolean(this.safeCall(() => element.paused, true)),
        ended: Boolean(this.safeCall(() => element.ended, false)),
        duration: this.safeCall(() => element.duration, 0),
        currentTime: this.safeCall(() => element.currentTime, 0),
        readyState: this.safeCall(() => element.readyState, 0),
        hasSource: Boolean(this.safeCall(() => element.currentSrc || element.src, "")),
        tag: this.safeCall(() => element.tagName, ""),
        connected: Boolean(this.safeCall(() => element.isConnected, false)),
        recentEvent: element === this.lastEventElement && this.now() - this.lastEventAt < 5000
      });
    }

    selectMaster() {
      this.scanMedia();
      let best = null;
      let bestScore = Number.NEGATIVE_INFINITY;
      for (const element of this.knownMedia.values()) {
        const score = this.mediaScore(element);
        if (score > bestScore) {
          best = element;
          bestScore = score;
        }
      }
      return best;
    }

    mediaCandidateDiagnostics() {
      return [...this.knownMedia.values()].slice(-8).map((element) => {
        const score = this.mediaScore(element);
        const knownAd = this.isKnownAdMedia(element);
        const utility = this.isUtilityMedia(element);
        return {
          mediaId: this.registerMedia(element),
          tag: String(element.tagName || "").toLocaleLowerCase(),
          eligible: Number.isFinite(score),
          score: Number.isFinite(score) ? score : null,
          rejectedReason: knownAd ? "known-ad-media" : utility ? "utility-media" : Number.isFinite(score) ? null : "empty-or-unusable-media",
          paused: Boolean(element.paused),
          currentTime: this.round(element.currentTime),
          duration: Number.isFinite(element.duration) ? this.round(element.duration) : null,
          readyState: Number(element.readyState || 0),
          source: core.summarizeMediaSource(element.currentSrc || element.src || "", this.environment.location?.href),
          connected: Boolean(element.isConnected)
        };
      });
    }

    mediaSessionMetadata() {
      const metadata = this.safeCall(() => this.environment.navigator?.mediaSession?.metadata, null);
      const artwork = this.safeCall(() => Array.from(metadata?.artwork || []), []);
      return {
        title: String(metadata?.title || "").slice(0, 240),
        artist: String(metadata?.artist || "").slice(0, 240),
        album: String(metadata?.album || "").slice(0, 240),
        coverUri: String(artwork.at(-1)?.src || artwork[0]?.src || "").slice(0, 1000)
      };
    }

    playerRoot() {
      const heading = this.document?.querySelector("#player-region");
      return heading?.closest("section") || this.document?.querySelector("[class*='PlayerBar_root__']") || null;
    }

    textFrom(element, selectors) {
      if (!element) return "";
      for (const selector of selectors) {
        const text = String(element.querySelector(selector)?.textContent || "").trim();
        if (text) return text;
      }
      return "";
    }

    playerDomMetadata() {
      const player = this.playerRoot();
      if (!player) return { title: "", artist: "", album: "", coverUri: "", durationMs: 0 };
      const cover = player.querySelector("img[src*='get-music-content'], img[src]");
      const timecode = player.querySelector("input[type='range'][max]");
      const durationSeconds = core.finiteNumber(timecode?.max, 0);
      return {
        title: this.textFrom(player, ["[class*='Meta_title__']", "[class*='title__']"]),
        artist: this.textFrom(player, ["[class*='Meta_artistCaption__']", "[class*='artists__']"]),
        album: "",
        coverUri: String(cover?.currentSrc || cover?.src || ""),
        durationMs: durationSeconds > 0 ? Math.round(durationSeconds * 1000) : 0
      };
    }

    activeCardMetadata() {
      const card = this.document?.querySelector("[class*='CommonTrack_root_current__'], [class*='Track_root_current__']");
      if (!card) return { title: "", artist: "", album: "", coverUri: "", durationMs: 0 };
      const cover = card.querySelector("img[src*='get-music-content'], img[src]");
      return {
        title: this.textFrom(card, ["[class*='Meta_title__']", "[class*='title__']"]),
        artist: this.textFrom(card, ["[class*='Meta_artistCaption__']", "[class*='artists__']"]),
        album: "",
        coverUri: String(cover?.currentSrc || cover?.src || ""),
        durationMs: 0
      };
    }

    playbackMetadata(master) {
      const session = this.mediaSessionMetadata();
      const player = this.playerDomMetadata();
      const card = this.activeCardMetadata();
      const durationMs = Number.isFinite(master?.duration) && master.duration > 0
        ? Math.round(master.duration * 1000)
        : player.durationMs;
      return {
        title: session.title || player.title || card.title,
        artist: session.artist || player.artist || card.artist,
        album: session.album || player.album || card.album,
        coverUri: session.coverUri || player.coverUri || card.coverUri,
        durationMs
      };
    }

    rememberTrack(entry, source) {
      if (!entry?.id) return false;
      const next = { ...entry, source: String(source || entry.source || "page-state"), catalogSeenAt: this.now() };
      const previous = this.trackCatalog.get(next.id);
      const fields = (value) => JSON.stringify({
        title: value?.title,
        artists: value?.artists,
        album: value?.album,
        durationMs: value?.durationMs,
        coverUri: value?.coverUri
      });
      const changed = !previous || fields(previous) !== fields(next);
      if (previous) this.trackCatalog.delete(next.id);
      this.trackCatalog.set(next.id, next);
      while (this.trackCatalog.size > MAX_CATALOG_ENTRIES) {
        this.trackCatalog.delete(this.trackCatalog.keys().next().value);
      }
      return changed;
    }

    ingestTrackPayload(payload, source) {
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
        if (entry && this.rememberTrack(entry, source)) changed += 1;
        for (const child of this.safeCall(() => Object.values(value), [])) {
          if (child && typeof child === "object") stack.push(child);
        }
      }
      return changed;
    }

    jsonValueEnd(source, start) {
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
        if (character === "\"") quoted = true;
        else if (character === "[" || character === "{") depth += 1;
        else if (character === "]" || character === "}") {
          depth -= 1;
          if (depth === 0) return index + 1;
        }
      }
      return -1;
    }

    scanInlineStateScripts() {
      this.safeCall(() => {
        this.document?.querySelectorAll("script:not([src])").forEach((script) => {
          if (this.scannedStateScripts.has(script)) return;
          this.scannedStateScripts.add(script);
          const source = String(script.textContent || "");
          if (!source.includes("__STATE_PATCHES__") || source.length > MAX_CAPTURE_BYTES) return;
          let cursor = 0;
          while (cursor < source.length) {
            const pushAt = source.indexOf(".push(", cursor);
            if (pushAt < 0) break;
            const start = source.indexOf("[", pushAt + 6);
            if (start < 0) break;
            const end = this.jsonValueEnd(source, start);
            if (end < 0) break;
            try {
              this.ingestTrackPayload(JSON.parse(source.slice(start, end)), "yandex-inline-state");
            } catch (_error) {
              // Inline code can contain non-JSON values; those fragments are ignored.
            }
            cursor = end;
          }
        });
      });
    }

    scanStatePatches() {
      const batches = this.safeCall(() => this.environment.__STATE_PATCHES__, null);
      if (Array.isArray(batches)) {
        if (this.statePatchCursor > batches.length) this.statePatchCursor = 0;
        for (; this.statePatchCursor < batches.length; this.statePatchCursor += 1) {
          this.ingestTrackPayload(batches[this.statePatchCursor], "yandex-state-patches");
        }
      }
      this.scanInlineStateScripts();
    }

    elementLooksActive(element) {
      const classText = `${element.className || ""} ${element.parentElement?.className || ""}`;
      return /(?:^|[\s_-])(active|current|playing|selected)(?:$|[\s_-])/i.test(classText);
    }

    insidePlayer(element) {
      return Boolean(this.safeCall(() => element.closest(PLAYER_CONTAINER_SELECTOR), null));
    }

    visibleElement(element) {
      return this.safeCall(() => {
        const style = this.window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      }, false);
    }

    safePath(rawUrl) {
      return this.safeCall(() => new URL(rawUrl, this.environment.location.href).pathname, "");
    }

    collectTrackCandidates(metadata, master) {
      const candidates = [];
      this.scanStatePatches();
      const catalogMatch = core.pickTrackFromCatalog([...this.trackCatalog.values()], metadata, 100);
      candidates.push(...catalogMatch.ranked.filter((candidate) => candidate.score >= 100));

      this.safeCall(() => {
        this.document?.querySelectorAll("a[href*='/track/']").forEach((anchor) => {
          const id = core.parseTrackIdFromUrl(anchor.href);
          if (!id) return;
          let score = 15;
          const signals = [];
          if (this.insidePlayer(anchor)) {
            score += 95;
            signals.push("player-container");
          }
          if (anchor.getAttribute("aria-current") === "true") {
            score += 70;
            signals.push("aria-current");
          }
          if (this.elementLooksActive(anchor)) {
            score += 35;
            signals.push("active-class");
          }
          if (this.visibleElement(anchor)) score += 5;
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
            evidence: `${this.safePath(anchor.href)} ${signals.join(",")}`.trim()
          });
        });
      });

      this.safeCall(() => {
        this.document?.querySelectorAll("[data-track-id], [data-trackid], [data-track_id]").forEach((element) => {
          const raw = element.getAttribute("data-track-id") || element.getAttribute("data-trackid") || element.getAttribute("data-track_id");
          const id = core.normalizeTrackId(raw);
          if (!id) return;
          const inPlayer = this.insidePlayer(element);
          candidates.push({
            id,
            score: inPlayer ? 125 : 45,
            source: "dom-track-data",
            evidence: inPlayer ? "player-container" : "page-data"
          });
        });
      });

      const routeId = core.parseTrackIdFromUrl(this.environment.location?.href);
      if (routeId) {
        const titleSimilarity = core.metadataSimilarity(this.document?.title, metadata);
        candidates.push({
          id: routeId,
          score: 25 + titleSimilarity + (master && !master.paused ? 10 : 0),
          source: "page-route",
          evidence: this.safePath(this.environment.location.href)
        });
      }
      return candidates;
    }

    trackState(master) {
      const metadata = this.playbackMetadata(master);
      const result = core.pickBestTrackCandidate(this.collectTrackCandidates(metadata, master), 70);
      // Guard validation needs independent catalog duration, not a copy of the
      // selected media duration which would make a mismatch check tautological.
      const canonicalDuration = this.trackCatalog.get(result.selected?.id)?.durationMs;
      return {
        id: result.selected?.id || null,
        confidence: result.selected?.score || 0,
        source: result.selected?.source || null,
        evidence: result.selected?.evidence || "",
        ambiguous: result.ambiguous,
        candidates: result.ranked,
        metadata: { ...metadata, durationMs: canonicalDuration > 0 ? canonicalDuration : metadata.durationMs },
        catalogSize: this.trackCatalog.size
      };
    }

    getSnapshot(reason = "request") {
      const master = this.selectMaster();
      const location = this.environment.location;
      return {
        service: this.service,
        reason,
        observedAt: this.now(),
        route: location ? `${location.origin}${location.pathname}` : "",
        track: this.trackState(master),
        player: this.mediaState(master),
        mediaCandidates: this.mediaCandidateDiagnostics(),
        adapterVersion: core.VERSION
      };
    }

    emitTrackTransition(snapshot, nativeEvent) {
      const trackId = snapshot.track?.id || null;
      if (!trackId) return;
      const previousTrackId = this.lastTrackId;
      this.lastTrackId = trackId;
      if (!previousTrackId || previousTrackId === trackId) return;
      this.sink?.onPlayerEvent({
        type: "TRACK_CHANGED",
        nativeEvent,
        observedAt: snapshot.observedAt,
        trackId,
        previousTrackId,
        mediaId: snapshot.player?.mediaId || null,
        snapshot
      });
    }

    emitSnapshot(reason, force = false) {
      if (!this.mounted) return null;
      const snapshot = this.getSnapshot(reason);
      this.emitTrackTransition(snapshot, reason);
      const signature = core.snapshotSignature(snapshot);
      if (force || signature !== this.lastSnapshotSignature) {
        this.lastSnapshotSignature = signature;
        this.sink?.onSnapshot(snapshot);
      }
      return snapshot;
    }

    onMediaEvent(event) {
      const element = event.target;
      if (!this.isMediaElement(element) || this.isReplacementElement(element) || !this.mounted) return;
      const mediaId = this.registerMedia(element);
      this.lastEventElement = element;
      this.lastEventAt = this.now();
      if (event.type === "timeupdate" && this.now() - this.lastTimeEventAt < TIME_EVENT_THROTTLE_MS) return;
      if (event.type === "timeupdate") this.lastTimeEventAt = this.now();

      const snapshot = this.getSnapshot(`event:${event.type}`);
      this.emitTrackTransition(snapshot, event.type);
      this.lastSnapshotSignature = core.snapshotSignature(snapshot);
      const type = core.normalizeNativeEventType(event.type);
      if (!type || snapshot.player?.mediaId !== mediaId) return;
      this.sink?.onPlayerEvent({
        type,
        nativeEvent: event.type,
        observedAt: snapshot.observedAt,
        trackId: snapshot.track?.id || null,
        mediaId: snapshot.player?.mediaId || null,
        snapshot
      });
    }

    scheduleCatalogSnapshot(source) {
      if (this.catalogRefreshTimer) return;
      this.catalogRefreshTimer = this.environment.setTimeout(() => {
        this.catalogRefreshTimer = null;
        this.emitSnapshot(`catalog:${source}`, true);
      }, 40);
    }

    isYandexNetworkUrl(rawUrl) {
      return this.safeCall(() => {
        const hostname = new URL(String(rawUrl || ""), this.environment.location.href).hostname.toLocaleLowerCase();
        return ["yandex.ru", "yandex.net", "yandex.com", "yandex.by", "yandex.kz"]
          .some((domain) => hostname === domain || hostname.endsWith(`.${domain}`));
      }, false);
    }

    captureJsonResponse(response, source) {
      const contentType = this.safeCall(() => response.headers.get("content-type"), "") || "";
      const contentLength = Number(this.safeCall(() => response.headers.get("content-length"), 0) || 0);
      if (!this.isYandexNetworkUrl(response.url) || !/\bjson\b/i.test(contentType) || contentLength > MAX_CAPTURE_BYTES) return;
      this.safeCall(() => {
        response.clone().text().then((body) => {
          if (body.length > MAX_CAPTURE_BYTES) return;
          if (this.ingestTrackPayload(JSON.parse(body), source) > 0) this.scheduleCatalogSnapshot(source);
        }).catch(() => undefined);
      });
    }

    installNetworkHooks() {
      if (!this.nativeHooks.fetch && typeof this.environment.fetch === "function") {
        const adapter = this;
        this.nativeHooks.fetch = this.environment.fetch;
        this.nativeHooks.fetchWrapper = async function celikomObservedFetch(...args) {
          const response = await Reflect.apply(adapter.nativeHooks.fetch, this, args);
          adapter.captureJsonResponse(response, "fetch-json");
          return response;
        };
        this.environment.fetch = this.nativeHooks.fetchWrapper;
      }

      const prototype = this.environment.XMLHttpRequest?.prototype;
      if (!prototype || this.nativeHooks.xhrOpen) return;
      const adapter = this;
      this.nativeHooks.xhrOpen = prototype.open;
      this.nativeHooks.xhrSend = prototype.send;
      this.nativeHooks.xhrOpenWrapper = function celikomObservedXhrOpen(method, url, ...args) {
        adapter.safeCall(() => adapter.xhrUrls.set(this, String(url || "")));
        return Reflect.apply(adapter.nativeHooks.xhrOpen, this, [method, url, ...args]);
      };
      this.nativeHooks.xhrSendWrapper = function celikomObservedXhrSend(...args) {
        this.addEventListener("loadend", () => {
          if (!adapter.isYandexNetworkUrl(adapter.xhrUrls.get(this))) return;
          const contentType = adapter.safeCall(() => this.getResponseHeader("content-type"), "") || "";
          if (!/\bjson\b/i.test(contentType)) return;
          try {
            const payload = this.responseType === "json" ? this.response : JSON.parse(String(this.responseText || ""));
            if (adapter.ingestTrackPayload(payload, "xhr-json") > 0) adapter.scheduleCatalogSnapshot("xhr-json");
          } catch (_error) {
            // Ignore inaccessible or non-JSON responses.
          }
        }, { once: true });
        return Reflect.apply(adapter.nativeHooks.xhrSend, this, args);
      };
      prototype.open = this.nativeHooks.xhrOpenWrapper;
      prototype.send = this.nativeHooks.xhrSendWrapper;
    }

    restoreNetworkHooks() {
      if (this.nativeHooks.fetch && this.environment.fetch === this.nativeHooks.fetchWrapper) {
        this.environment.fetch = this.nativeHooks.fetch;
      }
      const prototype = this.environment.XMLHttpRequest?.prototype;
      if (prototype && this.nativeHooks.xhrOpen && prototype.open === this.nativeHooks.xhrOpenWrapper) {
        prototype.open = this.nativeHooks.xhrOpen;
      }
      if (prototype && this.nativeHooks.xhrSend && prototype.send === this.nativeHooks.xhrSendWrapper) {
        prototype.send = this.nativeHooks.xhrSend;
      }
      for (const key of ["fetch", "fetchWrapper", "xhrOpen", "xhrSend", "xhrOpenWrapper", "xhrSendWrapper"]) {
        delete this.nativeHooks[key];
      }
    }

    installPrototypeHooks() {
      const prototype = this.environment.HTMLMediaElement?.prototype;
      if (!prototype) return;
      const adapter = this;
      for (const name of ["play", "pause", "load"]) {
        if (this.nativeHooks[name] || typeof prototype[name] !== "function") continue;
        this.nativeHooks[name] = prototype[name];
        this.nativeHooks[`${name}Wrapper`] = function celikomObservedMediaMethod(...args) {
          if (!adapter.isReplacementElement(this)) {
            adapter.registerMedia(this);
            if (name !== "load") {
              adapter.lastEventElement = this;
              adapter.lastEventAt = adapter.now();
            }
            adapter.defer(() => adapter.emitSnapshot(`method:${name}`, true));
          }
          return Reflect.apply(adapter.nativeHooks[name], this, args);
        };
        prototype[name] = this.nativeHooks[`${name}Wrapper`];
      }
    }

    restorePrototypeHooks() {
      const prototype = this.environment.HTMLMediaElement?.prototype;
      if (!prototype) return;
      for (const name of ["play", "pause", "load"]) {
        if (this.nativeHooks[name] && prototype[name] === this.nativeHooks[`${name}Wrapper`]) {
          prototype[name] = this.nativeHooks[name];
        }
        delete this.nativeHooks[name];
        delete this.nativeHooks[`${name}Wrapper`];
      }
    }

    installHistoryHooks() {
      const history = this.environment.history;
      if (!history) return;
      const adapter = this;
      for (const name of ["pushState", "replaceState"]) {
        if (this.nativeHooks[name] || typeof history[name] !== "function") continue;
        this.nativeHooks[name] = history[name];
        this.nativeHooks[`${name}Wrapper`] = function celikomObservedHistory(...args) {
          const result = Reflect.apply(adapter.nativeHooks[name], this, args);
          adapter.defer(() => adapter.emitSnapshot(`history:${name}`, true));
          return result;
        };
        history[name] = this.nativeHooks[`${name}Wrapper`];
      }
    }

    restoreHistoryHooks() {
      const history = this.environment.history;
      if (!history) return;
      for (const name of ["pushState", "replaceState"]) {
        if (this.nativeHooks[name] && history[name] === this.nativeHooks[`${name}Wrapper`]) {
          history[name] = this.nativeHooks[name];
        }
        delete this.nativeHooks[name];
        delete this.nativeHooks[`${name}Wrapper`];
      }
    }

    onNavigation() {
      this.defer(() => this.emitSnapshot("navigation", true));
    }

    mount(sink) {
      if (this.mounted) return this;
      if (!sink || typeof sink.onSnapshot !== "function" || typeof sink.onPlayerEvent !== "function") {
        throw new TypeError("YandexMusicAdapter requires a ServiceAdapterSink");
      }
      this.sink = sink;
      this.mounted = true;
      this.installPrototypeHooks();
      this.installHistoryHooks();
      this.installNetworkHooks();
      this.window.addEventListener?.("popstate", this.onNavigation);
      this.window.addEventListener?.("hashchange", this.onNavigation);

      const Observer = this.environment.MutationObserver;
      if (Observer && this.document) {
        this.mutationObserver = new Observer(() => {
          if (this.mutationDebounceTimer) return;
          this.mutationDebounceTimer = this.environment.setTimeout(() => {
            this.mutationDebounceTimer = null;
            this.scanMedia();
            this.emitSnapshot("dom-mutation");
          }, 80);
        });
        this.mutationObserver.observe(this.document, {
          childList: true,
          subtree: true,
          attributes: true,
          attributeFilter: ["href", "aria-current", "data-track-id", "data-trackid", "data-track_id"]
        });
      }

      this.scanMedia();
      this.snapshotTimer = this.environment.setInterval(() => this.emitSnapshot("poll"), SNAPSHOT_INTERVAL_MS);
      this.emitSnapshot("adapter-mount", true);
      return this;
    }

    unmount() {
      if (!this.mounted) return;
      this.mounted = false;
      this.window.removeEventListener?.("popstate", this.onNavigation);
      this.window.removeEventListener?.("hashchange", this.onNavigation);
      this.mutationObserver?.disconnect();
      this.mutationObserver = null;
      this.environment.clearTimeout(this.mutationDebounceTimer);
      this.environment.clearTimeout(this.catalogRefreshTimer);
      this.environment.clearInterval(this.snapshotTimer);
      this.mutationDebounceTimer = null;
      this.catalogRefreshTimer = null;
      this.snapshotTimer = null;
      this.restorePrototypeHooks();
      this.restoreHistoryHooks();
      this.restoreNetworkHooks();
      for (const [id, element] of this.knownMedia) this.unregisterMedia(id, element);
      this.sink = null;
      this.lastSnapshotSignature = "";
      this.lastTrackId = null;
      this.lastEventElement = null;
    }
  }

  Object.defineProperty(root, GLOBAL_KEY, {
    value: Object.freeze({
      service: "yandex-music",
      YandexMusicAdapter,
      createAdapter: (environment) => new YandexMusicAdapter(environment)
    }),
    configurable: false,
    enumerable: false,
    writable: false
  });
})(globalThis);
