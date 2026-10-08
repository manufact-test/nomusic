(function registerSyncEngine(root) {
  "use strict";
  const KEY = "__CELIKOM_SYNC_ENGINE_V1__";
  if (root[KEY]) return;
  function projectTime(player, observedAt, now) {
    const elapsed = player.paused || player.ended || player.seeking || player.readyState < 3
      ? 0 : Math.max(0, Math.min(1500, now - observedAt)) / 1000;
    const projected = Math.max(0, player.currentTime + elapsed * (player.playbackRate || 1));
    return Number.isFinite(player.duration) ? Math.min(projected, player.duration) : projected;
  }
  function targetTime(masterTime, duration, demoLoop) {
    if (!Number.isFinite(duration) || duration <= 0) throw new Error("Replacement duration is invalid");
    if (demoLoop) return ((masterTime % duration) + duration) % duration;
    if (masterTime >= duration) throw new Error("Replacement ended before original");
    return Math.max(0, masterTime);
  }
  function driftAt(actual, target, duration, demoLoop) {
    let drift = actual - target;
    if (demoLoop && duration > 0) drift = ((drift + duration / 2) % duration + duration) % duration - duration / 2;
    return Math.round(drift * 1000);
  }
  class SyncEngine {
    constructor(thresholdMs = 350) { this.thresholdMs = thresholdMs; this.lastSeekAt = 0; this.driftMs = null; }
    sync(replacement, snapshot, force = false, now = Date.now()) {
      const player = snapshot.player;
      replacement.applyState(player);
      const target = targetTime(projectTime(player, snapshot.observedAt, now), replacement.audio.duration, replacement.demoLoop);
      this.driftMs = driftAt(replacement.audio.currentTime, target, replacement.audio.duration, replacement.demoLoop);
      // Do not fight an in-progress native seek or repeatedly correct its lagging clock.
      if ((force || Math.abs(this.driftMs) > this.thresholdMs) && (force || now - this.lastSeekAt >= 800)) {
        replacement.audio.currentTime = target;
        this.lastSeekAt = now;
      }
      if (player.paused || player.ended || player.seeking || player.readyState < 3) replacement.pause();
      else replacement.play();
      return this.driftMs;
    }
  }
  Object.defineProperty(root, KEY, { value: Object.freeze({ SyncEngine, projectTime, targetTime, driftAt }), writable: false });
})(globalThis);
