/** W76: bounded retry of an approved *current* Yandex track after transient
 * local-bridge failure; never changes player/queue on a different track.
 * Existing Yandex reloadEntity(QUALITY_CHANGE) preserves pause/position.
 */
const TRACK = /^[1-9][0-9]{0,23}$/;
export function createTransientSourceRecovery({
  prime, reload, currentTrackId, active, onEvent = () => {},
  delays = [650, 2400], confirmationDelayMs = 150,
  timer = setTimeout, clearTimer = clearTimeout
}) {
  if (typeof prime !== "function" || typeof reload !== "function" ||
      typeof currentTrackId !== "function" || typeof active !== "function" ||
      !Array.isArray(delays) || delays.length < 1 || delays.length > 3 ||
      delays.some(x => !Number.isInteger(x) || x < 0 || x > 12000) ||
      !Number.isInteger(confirmationDelayMs) || confirmationDelayMs < 0 ||
      confirmationDelayMs > 1000)
    throw new TypeError("W76_BAD_RECOVERY_CONTRACT");
  let epoch = 0;
  const pending = new Map();
  const emit = (code, id) => { try { onEvent(code, id); } catch {} };
  function current(id, job) {
    return pending.get(id) === job && job.epoch === epoch && active() &&
      currentTrackId() === id;
  }
  function finish(id, job) {
    if (pending.get(id) === job) pending.delete(id);
  }
  function attempt(id, job) {
    if (job.attempt >= delays.length) {
      emit("SOURCE_RECOVERY_EXHAUSTED", id); finish(id, job); return;
    }
    const delay = delays[job.attempt++];
    job.phase = "waiting";
    job.timer = timer(async () => {
      job.timer = null;
      if (!current(id, job)) {
        emit("SOURCE_RECOVERY_NO_LONGER_CURRENT", id);
        finish(id, job);
        return;
      }
      job.phase = "prime";
      emit("SOURCE_RECOVERY_RETRY", id);
      let found = false;
      try { found = await prime(id) === true; } catch {}
      if (!current(id, job)) { finish(id, job); return; }
      if (found) {
        emit("SOURCE_RECOVERY_GRANTED", id);
        // Give Yandex's own retry a short chance to surface a fresh, playing
        // decoder URL. CDP confirmation can cancel this window before the
        // player is explicitly reloaded, avoiding a redundant 403→206 pop.
        job.phase = "confirm";
        job.timer = timer(async () => {
          job.timer = null;
          if (!current(id, job)) {
            emit("SOURCE_RECOVERY_NO_LONGER_CURRENT", id);
            finish(id, job);
            return;
          }
          job.phase = "reload";
          let reloaded = false;
          try { reloaded = await reload(id) === true; } catch {}
          if (!current(id, job)) { finish(id, job); return; }
          if (reloaded) {
            emit("SOURCE_RECOVERY_RELOAD_OK", id);
            finish(id, job);
            return;
          }
          emit("SOURCE_RECOVERY_RELOAD_FAILED", id);
          attempt(id, job);
        }, confirmationDelayMs);
        return;
      }
      attempt(id, job);
    }, delay);
  }
  function schedule(id) {
    if (typeof id !== "string" || !TRACK.test(id) ||
        !active() || pending.has(id) || pending.size >= 6) return false;
    const job = {epoch, timer:null, attempt:0};
    pending.set(id, job);
    emit("SOURCE_RECOVERY_SCHEDULED", id);
    attempt(id, job);
    return true;
  }
  // W99/W103: a strong CURRENT decoder kUrl + playing witness proves Yandex
  // has already chosen a fresh CELIKOM stream. Cancel a waiting/prime or
  // post-prime confirmation window, but never interrupt a reload already started.
  function confirmedCurrentSource(id) {
    const job = pending.get(id);
    if (!job || job.phase === "reload" || !current(id,job)) return false;
    if (job.timer !== null) clearTimer(job.timer);
    job.timer = null;
    finish(id,job);
    emit("SOURCE_RECOVERY_DECODER_ALREADY_PLAYING",id);
    return true;
  }
  function cancel() {
    epoch++;
    for (const job of pending.values()) if (job.timer !== null) clearTimer(job.timer);
    pending.clear();
  }
  return Object.freeze({schedule, cancel, confirmedCurrentSource,
    get pendingCount() {return pending.size;}});
}
