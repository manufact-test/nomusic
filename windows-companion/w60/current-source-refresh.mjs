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
const CURRENT_STATUS = new Set(["playing", "paused", "stopped"]);
const MODULE_ID = 7123;
const MODULE_EXPORT = "VE";
const KNOWN_RELOAD_REASON = "QUALITY_CHANGE";
const EXACT_ID = /^[1-9][0-9]{0,23}$/;

function currentEntity(state) {
  const current = state?.queueState?.currentEntity?.value;
  const id = current?.entity?.data?.meta?.id;
  const status = state?.playerState?.status?.value;
  const normalizedId = typeof id === "number" && Number.isSafeInteger(id)
    ? String(id) : id;
  if (!CURRENT_STATUS.has(status) || typeof normalizedId !== "string" ||
      !EXACT_ID.test(normalizedId)) return null;
  return { entry: current.entity, id: normalizedId, status };
}

function playable(state) {
  const current = currentEntity(state);
  return !!current && ALLOWED_STATUS.has(current.status);
}

export function createCurrentSourceRefresh({onEvent = () => {}, onPlayerObserved = () => {}} = {}) {
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
        try {
          if (currentEntity(state)) {
            current = new WeakRef(this);
            try { onPlayerObserved(this); } catch {}
          }
        } catch {}
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
  function resourcePrototype() {
    if (disposed || !prototype) return null;
    // W183: the exported state-observer class may be a base class. The live
    // Yandex player can be a derived instance with getFileInfo on its own
    // prototype. Resolve the method owner from the exact instance whose state
    // getter was observed, not from the exported base prototype.
    const player = current?.deref();
    if (!player) return null;
    let owner = player;
    while (owner && owner !== Object.prototype) {
      if (Object.prototype.hasOwnProperty.call(owner, "getFileInfo") &&
          typeof owner.getFileInfo === "function") return owner;
      owner = Object.getPrototypeOf(owner);
    }
    return null;
  }

  function mediaSourceOwner() {
    if (disposed || !prototype) return null;
    const player = current?.deref();
    if (!player) return null;
    let descriptor;
    try { descriptor = Object.getOwnPropertyDescriptor(player, "mediaProvider"); }
    catch { return null; }
    // The pinned Yandex 5.128 player assigns mediaProvider as an own data
    // property. Never invoke a vendor getter while discovering the live path.
    if (!descriptor || !Object.prototype.hasOwnProperty.call(descriptor, "value"))
      return null;
    const provider = descriptor.value;
    if (!provider || (typeof provider !== "object" && typeof provider !== "function"))
      return null;
    let owner = provider;
    while (owner && owner !== Object.prototype) {
      let method;
      try { method = Object.getOwnPropertyDescriptor(owner, "getMediaSource"); }
      catch { return null; }
      if (method && typeof method.value === "function" &&
          method.get === undefined && method.set === undefined) return owner;
      try { owner = Object.getPrototypeOf(owner); } catch { return null; }
    }
    return null;
  }

  function request(expectedTrackId = null) {
    if (disposed) return Promise.resolve(false);
    if (expectedTrackId !== null &&
        (typeof expectedTrackId !== "string" || !EXACT_ID.test(expectedTrackId)))
      return Promise.resolve(false);
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
      const observedId = state.queueState.currentEntity.value.entity.data.meta.id;
      if (expectedTrackId !== null && String(observedId) !== expectedTrackId) {
        note("NATIVE_TOGGLE_RELOAD_DIFFERENT_TRACK");
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
      const current = currentEntity(state);
      if (!current) return null;
      const entry = current.entry;
      const meta = entry.data.meta;
      const id = current.id;
      if (typeof id !== "string" || !EXACT_ID.test(id)) return null;
      const clean = value => typeof value === "string"
        ? value.replace(/[\u0000-\u001f\u007f]/g, " ").trim().slice(0, 180) : "";
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
      return {id, title, artist, durationMs,
        playbackState: current.status.toUpperCase()};
    } catch { return null; }
  }
  function currentTrackId() { return currentTrack()?.id || ""; }

  return Object.freeze({attach, request, dispose, currentTrack, currentTrackId,
    resourcePrototype, mediaSourceOwner,
    get playerObserved() { return !!current?.deref(); },
    get attached() { return !!prototype && !disposed; }});
}
