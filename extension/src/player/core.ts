(function initCelikomPlayerCore(root, factory) {
  "use strict";

  if (root.__CELIKOM_PLAYER_CORE_V1__) return;
  const api = factory();
  Object.defineProperty(root, "__CELIKOM_PLAYER_CORE_V1__", {
    value: api,
    configurable: false,
    enumerable: false,
    writable: false
  });
})(globalThis, function createCelikomPlayerCore() {
  "use strict";

  const VERSION = "0.2.1";
  const PROTOCOL_VERSION = 1;
  const CHANNEL = "CELIKOM_PLAYER_V1";
  const PLAYER_EVENT_TYPES = Object.freeze([
    "TRACK_CHANGED",
    "PLAY",
    "PAUSE",
    "SEEK",
    "TIME_UPDATE",
    "VOLUME_CHANGED",
    "RATE_CHANGED",
    "METADATA_CHANGED",
    "ENDED",
    "ERROR"
  ]);

  function finiteNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }

  function clamp(value, min, max) {
    const safeValue = finiteNumber(value, min);
    const safeMin = finiteNumber(min, 0);
    const safeMax = finiteNumber(max, safeMin);
    return Math.min(Math.max(safeValue, safeMin), Math.max(safeMin, safeMax));
  }

  function normalizeTrackId(value) {
    const normalized = String(value ?? "").trim();
    return /^\d{1,24}$/.test(normalized) ? normalized : null;
  }

  function parseTrackIdFromUrl(rawUrl) {
    if (!rawUrl) return null;

    try {
      const url = new URL(String(rawUrl), "https://music.yandex.ru/");
      if (url.protocol !== "https:" && url.protocol !== "http:") return null;
      const pathMatch = url.pathname.match(/(?:^|\/)track\/(\d{1,24})(?:\/|$)/i);
      if (pathMatch) return normalizeTrackId(pathMatch[1]);

      const endpointMatch = url.pathname.match(/(?:^|\/)(?:tracks?|track-info)\/(\d{1,24})(?:\/|$)/i);
      if (endpointMatch) return normalizeTrackId(endpointMatch[1]);

      for (const key of ["trackId", "track_id", "track-id"]) {
        const fromQuery = normalizeTrackId(url.searchParams.get(key));
        if (fromQuery) return fromQuery;
      }
    } catch (_error) {
      return null;
    }

    return null;
  }

  function normalizeText(value) {
    return String(value ?? "")
      .normalize("NFKC")
      .toLocaleLowerCase()
      .replace(/[\u2010-\u2015]/g, "-")
      .replace(/[^\p{L}\p{N}]+/gu, " ")
      .trim()
      .replace(/\s+/g, " ");
  }

  function metadataSimilarity(text, metadata) {
    const haystack = normalizeText(text);
    if (!haystack) return 0;

    const title = normalizeText(metadata?.title);
    const artist = normalizeText(metadata?.artist);
    let score = 0;
    if (title && haystack.includes(title)) score += 35;
    if (artist && haystack.includes(artist)) score += 25;
    return score;
  }

  function normalizeArtworkKey(rawUrl) {
    let source = String(rawUrl || "").trim();
    if (!source) return "";

    source = source.split(",")[0].trim().split(/\s+/)[0];
    source = source.replace(/\/%%(?:[?#].*)?$/i, "");
    if (/^[\w.-]+\.[a-z]{2,}(?:\/|$)/i.test(source)) source = `https://${source}`;

    try {
      const url = new URL(source, "https://music.yandex.ru/");
      const path = decodeURIComponent(url.pathname)
        .replace(/\/(?:%%|\d{1,4}x\d{1,4})(?:\/)?$/i, "")
        .replace(/\/+$/, "");
      return `${url.hostname.toLocaleLowerCase()}${path}`;
    } catch (_error) {
      return "";
    }
  }

  function trackCatalogEntryFromValue(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;

    const id = normalizeTrackId(value.realId ?? value.id);
    const title = String(value.title || "").trim();
    const durationMs = finiteNumber(value.durationMs, 0);
    if (!id || !title || durationMs <= 0) return null;

    const artists = Array.isArray(value.artists)
      ? value.artists.map((artist) => String(artist?.name ?? artist ?? "").trim()).filter(Boolean)
      : [];
    const album = Array.isArray(value.albums) ? value.albums[0] : value.album;

    return {
      id,
      title,
      artists,
      album: String(typeof album === "string" ? album : album?.title || "").trim(),
      albumId: normalizeTrackId(album?.id ?? value.albumId),
      durationMs: Math.round(durationMs),
      coverUri: String(value.coverUri || album?.coverUri || "").trim()
    };
  }

  function scoreTrackCatalogEntry(entry, playback = {}) {
    const candidateTitle = normalizeText(entry?.title);
    const playbackTitle = normalizeText(playback?.title);
    if (!candidateTitle || !playbackTitle) return { score: 0, signals: [] };

    let score = 0;
    const signals = [];
    if (candidateTitle === playbackTitle) {
      score += 75;
      signals.push("title-exact");
    } else if (
      Math.min(candidateTitle.length, playbackTitle.length) >= 4 &&
      (candidateTitle.includes(playbackTitle) || playbackTitle.includes(candidateTitle))
    ) {
      score += 35;
      signals.push("title-partial");
    } else {
      return { score: 0, signals: [] };
    }

    const playbackArtist = normalizeText(playback?.artist);
    const candidateArtists = (entry?.artists || []).map(normalizeText).filter(Boolean);
    const joinedArtists = normalizeText(candidateArtists.join(" "));
    if (playbackArtist && candidateArtists.some((artist) => artist === playbackArtist)) {
      score += 65;
      signals.push("artist-exact");
    } else if (
      playbackArtist && joinedArtists &&
      (joinedArtists.includes(playbackArtist) || playbackArtist.includes(joinedArtists))
    ) {
      score += 45;
      signals.push("artist-compatible");
    }

    const playbackAlbum = normalizeText(playback?.album);
    if (playbackAlbum && playbackAlbum === normalizeText(entry?.album)) {
      score += 15;
      signals.push("album-exact");
    }

    const playbackDurationMs = finiteNumber(playback?.durationMs, 0);
    if (playbackDurationMs > 0 && finiteNumber(entry?.durationMs, 0) > 0) {
      const delta = Math.abs(entry.durationMs - playbackDurationMs);
      if (delta <= 1500) {
        score += 50;
        signals.push("duration-1.5s");
      } else if (delta <= 4000) {
        score += 30;
        signals.push("duration-4s");
      } else if (delta <= 10000) {
        score += 10;
        signals.push("duration-10s");
      }
    }

    const playbackCover = normalizeArtworkKey(playback?.coverUri);
    const candidateCover = normalizeArtworkKey(entry?.coverUri);
    if (playbackCover && playbackCover === candidateCover) {
      score += 55;
      signals.push("cover-exact");
    }

    return { score, signals };
  }

  function pickBestTrackCandidate(candidates, minimumScore = 70) {
    const byId = new Map();
    for (const candidate of Array.isArray(candidates) ? candidates : []) {
      const id = normalizeTrackId(candidate?.id);
      const score = finiteNumber(candidate?.score, 0);
      if (!id || score <= 0) continue;

      const normalized = {
        id,
        score,
        source: String(candidate.source || "unknown"),
        evidence: String(candidate.evidence || "").slice(0, 240)
      };
      const previous = byId.get(id);
      if (!previous || previous.score < normalized.score) byId.set(id, normalized);
    }

    const ranked = [...byId.values()].sort((left, right) => right.score - left.score || left.id.localeCompare(right.id));
    const best = ranked[0] || null;
    const runnerUp = ranked[1] || null;
    const ambiguous = Boolean(best && runnerUp && best.id !== runnerUp.id && Math.abs(best.score - runnerUp.score) < 10);
    return {
      selected: best && best.score >= minimumScore && !ambiguous ? best : null,
      ambiguous,
      ranked: ranked.slice(0, 8)
    };
  }

  function pickTrackFromCatalog(entries, playback, minimumScore = 100) {
    const candidates = [];
    for (const entry of Array.isArray(entries) ? entries : []) {
      const parsed = trackCatalogEntryFromValue(entry);
      const normalized = parsed ? { ...parsed, source: entry?.source } : entry;
      const id = normalizeTrackId(normalized?.id);
      if (!id) continue;
      const match = scoreTrackCatalogEntry(normalized, playback);
      const hasIdentitySignal = match.signals.some((signal) => /^(?:artist-|cover-|album-)/.test(signal));
      if (match.score <= 0 || !hasIdentitySignal) continue;
      candidates.push({
        id,
        score: match.score,
        source: String(normalized.source || "state-track-catalog"),
        evidence: match.signals.join(",")
      });
    }
    return pickBestTrackCandidate(candidates, minimumScore);
  }

  function summarizeMediaSource(rawUrl, baseUrl = "https://music.yandex.ru/") {
    if (!rawUrl) return "none";
    try {
      const url = new URL(String(rawUrl), baseUrl);
      if (url.protocol === "blob:") return "blob";
      if (url.protocol === "data:") return "data";
      if (url.protocol === "chrome-extension:") return "extension-asset";
      return `${url.protocol}//${url.hostname}`;
    } catch (_error) {
      return "opaque";
    }
  }

  function isYandexAdMediaCandidate(candidate = {}) {
    if (String(candidate.tag || "").toLocaleLowerCase() !== "video") return false;
    let hostname = String(candidate.hostname || "").trim().toLocaleLowerCase();
    if (!hostname && candidate.source) {
      try {
        hostname = new URL(String(candidate.source), "https://music.yandex.ru").hostname.toLocaleLowerCase();
      } catch (_error) {
        hostname = "";
      }
    }
    if (hostname === "strm.yandex.ru") return true;
    const duration = finiteNumber(candidate.duration, 0);
    return Boolean(
      candidate.connected && duration > 0 && duration <= 60 &&
      /(?:^|\.)strm\.yandex\.(?:ru|net)$/.test(hostname)
    );
  }

  function scoreMediaCandidate(candidate = {}) {
    if (!candidate.isMedia || candidate.replacement || candidate.knownAd) return Number.NEGATIVE_INFINITY;

    const duration = finiteNumber(candidate.duration, 0);
    const currentTime = Math.max(0, finiteNumber(candidate.currentTime, 0));
    const readyState = Math.max(0, finiteNumber(candidate.readyState, 0));
    const hasSource = Boolean(candidate.hasSource);
    const paused = candidate.paused !== false;
    const hasUsableSignal = hasSource || duration > 1 || currentTime > 0 || readyState > 0 || !paused;
    if (!hasUsableSignal) return Number.NEGATIVE_INFINITY;

    let score = 0;
    if (!paused && !candidate.ended) score += 120;
    if (readyState >= 2) score += 25;
    if (duration > 1) score += 25;
    if (hasSource) score += 20;
    if (currentTime > 0) score += 15;
    if (String(candidate.tag || "").toLocaleLowerCase() === "audio") score += 80;
    if (candidate.connected) score += 5;
    if (candidate.recentEvent) score += 70;
    if (candidate.ended) score -= 150;
    return score;
  }

  function createSessionId() {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
    return `celikom-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  }

  function normalizeNativeEventType(nativeType) {
    const type = String(nativeType || "").toLocaleLowerCase();
    if (type === "play" || type === "playing") return "PLAY";
    if (type === "pause") return "PAUSE";
    if (type === "seeking" || type === "seeked") return "SEEK";
    if (type === "timeupdate") return "TIME_UPDATE";
    if (type === "volumechange") return "VOLUME_CHANGED";
    if (type === "ratechange") return "RATE_CHANGED";
    if (type === "loadedmetadata" || type === "durationchange" || type === "emptied") return "METADATA_CHANGED";
    if (type === "ended") return "ENDED";
    if (type === "error") return "ERROR";
    return null;
  }

  function snapshotSignature(snapshot) {
    return JSON.stringify({
      trackId: snapshot?.track?.id || null,
      source: snapshot?.track?.source || null,
      ambiguous: Boolean(snapshot?.track?.ambiguous),
      mediaId: snapshot?.player?.mediaId || null,
      paused: snapshot?.player?.paused ?? true,
      ended: snapshot?.player?.ended ?? false,
      seeking: snapshot?.player?.seeking ?? false,
      timeBucket: Math.floor(finiteNumber(snapshot?.player?.currentTime, 0) * 2),
      volume: snapshot?.player?.volume ?? 1,
      muted: snapshot?.player?.muted ?? false,
      route: snapshot?.route || ""
    });
  }

  return Object.freeze({
    VERSION,
    PROTOCOL_VERSION,
    CHANNEL,
    PLAYER_EVENT_TYPES,
    clamp,
    createSessionId,
    finiteNumber,
    isYandexAdMediaCandidate,
    metadataSimilarity,
    normalizeArtworkKey,
    normalizeNativeEventType,
    normalizeText,
    normalizeTrackId,
    parseTrackIdFromUrl,
    pickBestTrackCandidate,
    pickTrackFromCatalog,
    scoreMediaCandidate,
    scoreTrackCatalogEntry,
    snapshotSignature,
    summarizeMediaSource,
    trackCatalogEntryFromValue
  });
});
