/**
 * W60: version-pinned signed original Yandex in-place source refresh.
 * Observe the official 5.126.1 player class's existing state getter only.
 * Never create alternate player, change queue/media keys/track position, read
 * accounts or serialize track IDs/URLs into diagnostics.
 * Vendor confirms class 7123.VE.reloadEntity("QUALITY_CHANGE") delegates to
 * mediaController.reload -> getMediaSource(disableCache:true), preserving
 * playback position and paused status.
 */
const ALLOWED_STATUS = new Set(["playing", "paused"]);
const MODULE_ID = 7123;
const MODULE_EXPORT = "VE";
const KNOWN_RELOAD_REASON = "QUALITY_CHANGE";
const EXACT_ID = /^[1-9][0-9]{0,23}$/;

function playable(state) {
  const current = state?.queueState?.currentEntity?.value;
  const id = current?.entity?.data?.meta?.id;
  const status = state?.playerState?.status?.value;
  return ALLOWED_STATUS.has(status) &&
    EXACT_ID.test(typeof id === "number" && Number.isSafeInteger(id) ? String(id) : id);
}

export function createCurrentSourceRefresh({onEvent = () => {}} = {}) {
  let prototype = null, original = null, patchedGetter = null;
  let current = null, disposed = false, generation = 0;
  let chain = Promise.resolve();
  function note(code) {
    try { onEvent(code); } catch { /* diagnostic only */ }
  }

  function attach(webpackRequire) {
    if (disposed) return false;
    if (prototype) return true;
    if (typeof webpackRequire !== "function" ||
        typeof webpackRequire.m !== "object" ||
        typeof webpackRequire.m[MODULE_ID] !== "function") return false;
    let klass;
    try { klass = webpackRequire(MODULE_ID)?.[MODULE_EXPORT]; }
    catch { return false; }
    if (typeof klass !== "function" || !klass.prototype ||
        typeof klass.prototype.reloadEntity !== "function") return false;
    const proto = klass.prototype;
    const descriptor = Object.getOwnPropertyDescriptor(proto, "state");
    if (!descriptor?.configurable || typeof descriptor.get !== "function" ||
        descriptor.set !== undefined) return false;

    const observedGet = function() {
      const state = descriptor.get.call(this);
      if (!disposed) {
        // The vendor getter must keep its exact return/throw behavior even if
        // an exotic entity's metadata accessor rejects our observer.
        try { if (playable(state)) current = new WeakRef(this); } catch {}
      }
      return state;
    };
    try {
      Object.defineProperty(proto, "state", { ...descriptor, get: observedGet });
    } catch { return false; }
    prototype = proto;
    original = descriptor;
    patchedGetter = observedGet;
    note("NATIVE_TOGGLE_PLAYER_OBSERVER_READY");
    return true;
  }

  function request() {
    if (disposed) return Promise.resolve(false);
    const ticket = ++generation;
    const task = chain.then(async () => {
      if (disposed || ticket !== generation) return false;
      const player = current?.deref();
      if (!player || typeof player.reloadEntity !== "function") {
        note("NATIVE_TOGGLE_RELOAD_DEFERRED");
        return false;
      }
      let state;
      try { state = player.state; } catch { /* state can vanish on navigation */ }
      if (!playable(state)) {
        note("NATIVE_TOGGLE_RELOAD_DEFERRED");
        return false;
      }
      note("NATIVE_TOGGLE_RELOAD_REQUEST");
      try {
        await player.reloadEntity(KNOWN_RELOAD_REASON);
        if (!disposed) note("NATIVE_TOGGLE_RELOAD_OK");
        return !disposed;
      } catch {
        if (!disposed) note("NATIVE_TOGGLE_RELOAD_FAILED");
        return false;
      }
    });
    chain = task.catch(() => false);
    return task;
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    ++generation;
    current = null;
    if (prototype && original &&
        Object.getOwnPropertyDescriptor(prototype, "state")?.get === patchedGetter) {
      try { Object.defineProperty(prototype, "state", original); } catch {}
    }
    prototype = null;
    original = null;
    patchedGetter = null;
  }
  // Only the currently playing/paused queue entity, not a prefetched item.
  // Read bounded DISPLAY metadata only. Never expose URLs, tokens, account
  // information, Yandex state objects or internal player references.
  function currentTrack() {
    if (disposed) return null;
    const player = current?.deref();
    if (!player) return null;
    try {
      const state = player.state;
      if (!playable(state)) return null;
      const entry = state.queueState.currentEntity.value.entity;
      const meta = entry.data.meta;
      const id = typeof meta.id === "number" && Number.isSafeInteger(meta.id)
        ? String(meta.id) : meta.id;
      if (typeof id !== "string" || !EXACT_ID.test(id)) return null;
      const clean = value => typeof value === "string"
        ? value.replace(/[\\u0000-\\u001f\\u007f]/g, " ").trim().slice(0, 180) : "";
      const raw = entry.data || {};
      const sources = [meta.artists, raw.artists, raw.track?.artists,
        meta.albumArtists, raw.metadata?.artists, raw.track?.meta?.artists];
      const list = sources.find(Array.isArray) || [];
      const artists = list.slice(0, 4).map(a => clean(
        typeof a === "string" ? a :
          a?.name ?? a?.artist?.name ?? a?.artistName ?? a?.title)).filter(Boolean);
      const title = clean(meta.title) || clean(meta.name) ||
        clean(raw.title) || clean(raw.track?.title) || clean(raw.metadata?.title);
      const fallbackArtist = [meta.artist, raw.artist, meta.mainArtist,
        raw.track?.artist, meta.artistName, meta.artistsName,
        raw.metadata?.artist, raw.track?.meta?.artist].map(a =>
          clean(typeof a === "string" ? a : a?.name ?? a?.title)).find(Boolean) || "";
      const artist = artists.join(", ") || fallbackArtist;
      const rawDuration = meta.durationMs ?? raw.durationMs ??
        raw.track?.durationMs ?? raw.metadata?.durationMs ??
        meta.duration_milliseconds;
      const durationMs = Number.isSafeInteger(rawDuration) &&
        rawDuration >= 1000 && rawDuration <= 86400000 ? rawDuration : null;
      return {id, title, artist, durationMs};
    } catch { return null; }
  }
  function currentTrackId() { return currentTrack()?.id || ""; }

  return Object.freeze({attach, request, dispose, currentTrack, currentTrackId,
    get attached() { return !!prototype && !disposed; }});
}
