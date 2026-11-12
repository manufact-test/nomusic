/** W76: bounded retry of an approved *current* Yandex track after transient
 * local-bridge failure; never changes player/queue on a different track.
 * Existing Yandex reloadEntity(QUALITY_CHANGE) preserves pause/position.
 */
const TRACK = /^[1-9][0-9]{0,23}$/;
export function createTransientSourceRecovery({
  prime, reload, currentTrackId, active, onEvent = () => {},
  delays = [650, 2400], timer = setTimeout, clearTimer = clearTimeout
}) {
  if (typeof prime !== "function" || typeof reload !== "function" ||
      typeof currentTrackId !== "function" || typeof active !== "function" ||
      !Array.isArray(delays) || delays.length < 1 || delays.length > 3 ||
      delays.some(x => !Number.isInteger(x) || x < 0 || x > 12000))
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
    job.timer = timer(async () => {
      job.timer = null;
      if (!current(id, job)) { finish(id, job); return; }
      emit("SOURCE_RECOVERY_RETRY", id);
      let found = false;
      try { found = await prime(id) === true; } catch {}
      if (!current(id, job)) { finish(id, job); return; }
      if (found) {
        emit("SOURCE_RECOVERY_GRANTED", id);
        let reloaded = false;
        try { reloaded = await reload() === true; } catch {}
        if (!current(id, job)) { finish(id, job); return; }
        if (reloaded) { emit("SOURCE_RECOVERY_RELOAD_OK", id); finish(id, job); return; }
        emit("SOURCE_RECOVERY_RELOAD_FAILED", id);
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
  function cancel() {
    epoch++;
    for (const job of pending.values()) if (job.timer !== null) clearTimer(job.timer);
    pending.clear();
  }
  return Object.freeze({schedule, cancel,
    get pendingCount() {return pending.size;}});
}
