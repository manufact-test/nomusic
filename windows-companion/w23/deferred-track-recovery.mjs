/** W77: keep a transient preload failure until the *same* Yandex song
 * becomes the observed current playing/paused entity. A prefetch is NOT a
 * playback event; never force a reload for any other song.
 */
const VALID_ID = /^[1-9][0-9]{0,23}$/;
export function createDeferredTrackRecovery({
  currentTrackId, active, schedule, onEvent = () => {},
  now = Date.now, maxCandidates = 12, ttlMs = 12 * 60 * 1000
}) {
  if (typeof currentTrackId !== 'function' || typeof active !== 'function' ||
      typeof schedule !== 'function' || typeof now !== 'function' ||
      !Number.isInteger(maxCandidates) || maxCandidates < 1 || maxCandidates > 32 ||
      !Number.isInteger(ttlMs) || ttlMs < 1000 || ttlMs > 30 * 60 * 1000)
    throw new TypeError('W77_INVALID_HANDOFF_CONTRACT');
  const candidates = new Map();
  const emit = (code, id) => { try { onEvent(code, id); } catch {} };
  function prune() {
    const time = now();
    for (const [id, expires] of candidates)
      if (expires <= time) { candidates.delete(id); emit('SOURCE_DEFERRED_EXPIRED',id); }
  }
  function record(id) {
    if (typeof id !== 'string' || !VALID_ID.test(id) || !active()) return false;
    prune();
    if (!candidates.has(id) && candidates.size >= maxCandidates)
      candidates.delete(candidates.keys().next().value);
    const isNew = !candidates.has(id);
    // Repeated timed-out renderer requests for the same song should not
    // extend its life forever.
    if (isNew) {
      candidates.set(id, now() + ttlMs);
      emit('SOURCE_DEFERRED_WAITING', id);
    }
    return isNew;
  }
  function check() {
    if (!active()) return false;
    prune();
    const id = currentTrackId();
    if (typeof id !== 'string' || !VALID_ID.test(id) || !candidates.has(id))
      return false;
    // Schedule once; a failed prime is bounded by the existing W76 recovery
    // contract and must never loop on status polling.
    candidates.delete(id);
    if (!schedule(id)) {
      emit('SOURCE_DEFERRED_SKIPPED', id);
      return false;
    }
    emit('SOURCE_DEFERRED_PROMOTED', id);
    return true;
  }
  function cancel() { candidates.clear(); }
  return Object.freeze({record,check,cancel,
    get candidateCount() { return candidates.size; }
  });
}
