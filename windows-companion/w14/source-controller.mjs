/**
 * W14 candidate source-only bridge for a THIRD-PARTY PulseSync addon host.
 * Pure ESM, no Yandex binary access, profile access, credentials or player.
 *
 * A future CELIKOM Companion supplies an authenticated, narrowly scoped
 * resolve(trackId, signal) callback. No credential lives in this addon.
 * Until a real safe host/companion transport is approved, this is NOT an
 * installable or working Windows CELIKOM integration.
 */

const TRACK_ID = /^[1-9][0-9]{0,17}(?::[1-9][0-9]{0,17})?$/;
const MEDIA_PATH = /^\/api\/v1\/audio\/[A-Za-z0-9_-]{1,128}$/;
const MAX_GRANT_TTL_MS = 10 * 60 * 1000;
const MIN_GRANT_TTL_MS = 5000;

export function exactTrackId(track) {
  const value = track?.id;
  const id = typeof value === "number" && Number.isSafeInteger(value)
    ? String(value) : typeof value === "string" ? value : "";
  return TRACK_ID.test(id) ? id : null;
}

export function validateCelikomGrant(grant, id, allowedOrigin, now = Date.now()) {
  if (grant?.trackId !== id || grant.approved !== true ||
      grant.entitled !== true || typeof grant.audioUrl !== "string" ||
      !Number.isSafeInteger(grant.expiresAt) ||
      grant.expiresAt < now + MIN_GRANT_TTL_MS ||
      grant.expiresAt > now + MAX_GRANT_TTL_MS) return null;

  try {
    const expected = new URL(allowedOrigin);
    const url = new URL(grant.audioUrl);
    if (expected.protocol !== "https:" || expected.pathname !== "/" ||
        expected.search || expected.hash || expected.username || expected.password ||
        url.protocol !== "https:" || url.origin !== expected.origin ||
        url.username || url.password || url.hash ||
        !MEDIA_PATH.test(url.pathname) ||
        !/^[A-Za-z0-9._~-]{16,512}$/.test(url.searchParams.get("token") || "") ||
        !/^[0-9]{9,13}$/.test(url.searchParams.get("expires") || "") ||
        [...url.searchParams.keys()].some(k => k !== "token" && k !== "expires")) return null;
    return url.href;
  } catch { return null; }
}

/**
 * SDK contract required: api.player.getSnapshot/onTrackChange and
 * api.client.setTrackReplacements/clearTrackReplacements, as exposed by the
 * PulseSync addon host and used by FckCensor. No CDP/injection required here.
 */
export function createCelikomSourceController({ api, resolve, allowedOrigin, now = Date.now }) {
  if (typeof resolve !== "function" ||
      typeof api?.player?.getSnapshot !== "function" ||
      typeof api?.player?.onTrackChange !== "function" ||
      typeof api?.client?.setTrackReplacements !== "function" ||
      typeof api?.client?.clearTrackReplacements !== "function" ||
      typeof allowedOrigin !== "string" ||
      !allowedOrigin.startsWith("https://"))
    throw new Error("W14_UNSUPPORTED_HOST_OR_BRIDGE");

  let enabled = false, disposed = false, current = null, originalFor = null;
  let generation = 0, started = false, unsubscribe = () => {};
  let pending = Promise.resolve();
  let writes = Promise.resolve();
  let abort = null;
  let state = "OFF";

  function queueWrite(kind, id, url, revision) {
    const job = writes.catch(() => false).then(async () => {
      if (disposed && kind === "set") return false;
      if (kind === "set" && (revision !== generation || !enabled ||
                             current !== id || originalFor === id)) return false;
      if (kind === "clear") {
        await api.client.clearTrackReplacements();
      } else {
        await api.client.setTrackReplacements({ [id]: url });
        // If Next/Stop/Original happened while SDK awaited the write,
        // a later clear is queued by that transition.
      }
      return true;
    });
    writes = job.catch(() => { state = "HOST_ERROR"; return false; });
    return writes;
  }

  function cancel() {
    generation++;
    abort?.abort();
    abort = null;
  }

  function reconcile() {
    cancel();
    const revision = generation;
    void queueWrite("clear", null, null, revision);
    if (!enabled || disposed) {
      state = "OFF"; return;
    }
    if (!current || originalFor === current) {
      state = originalFor === current ? "ORIGINAL" : "UNAVAILABLE";
      return;
    }
    const requestedId = current;
    const signal = (abort = new AbortController()).signal;
    state = "RESOLVING";
    pending = Promise.resolve().then(() => resolve(requestedId, signal))
      .then(async grant => {
        if (disposed || !enabled || signal.aborted ||
            revision !== generation || current !== requestedId) return;
        const url = validateCelikomGrant(grant, requestedId, allowedOrigin, now());
        if (!url) { state = "ORIGINAL"; return; }
        const accepted = await queueWrite("set", requestedId, url, revision);
        if (accepted && revision === generation && enabled && !disposed)
          state = "SDK_MAPPING_ACCEPTED";
      }).catch(() => {
        if (revision === generation && !disposed) state = "ORIGINAL";
      });
  }

  function observe(track) {
    if (disposed) return;
    const id = exactTrackId(track);
    if (id === current) return;
    current = id;
    originalFor = null;
    reconcile();
  }

  async function start() {
    if (started || disposed) throw new Error("W14_INVALID_LIFECYCLE");
    started = true;
    let gotEvent = false;
    unsubscribe = api.player.onTrackChange(track => {
      gotEvent = true;
      observe(track);
    });
    if (typeof unsubscribe !== "function") throw new Error("W14_NO_HOST_UNSUBSCRIBE");
    try {
      const snapshot = await api.player.getSnapshot();
      if (!gotEvent && !disposed) observe(snapshot?.track);
    } catch {
      // No guessed track identity. Later verified track-change events can work.
      if (!gotEvent && !disposed) observe(null);
    }
    if (api.signal?.addEventListener) api.signal.addEventListener("abort", dispose, { once: true });
    return controller;
  }

  function enable() {
    if (disposed) return;
    if (enabled) return;
    enabled = true;
    reconcile();
  }

  function disable() {
    if (disposed) return;
    enabled = false;
    reconcile();
  }

  function original() {
    if (disposed) return;
    originalFor = current;
    reconcile();
  }

  async function dispose() {
    if (disposed) return;
    disposed = true;
    enabled = false;
    cancel();
    unsubscribe();
    if (api.signal?.removeEventListener) api.signal.removeEventListener("abort", dispose);
    // SDK cleanup, not a second audio engine.
    await queueWrite("clear", null, null, generation);
    state = "OFF";
  }

  async function flush() {
    // For deterministic offline contract tests. No timer and no audio clock.
    await pending.catch(() => {});
    await writes.catch(() => {});
  }

  const controller = Object.freeze({
    start, enable, disable, original, dispose, flush,
    get status() { return state; },
    get trackId() { return current; },
    get enabled() { return enabled && !disposed; }
  });
  return controller;
}
