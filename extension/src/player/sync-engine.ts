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
    constructor(thresholdMs = 350) { this.thresholdMs = thresholdMs; this.lastSeekAt = 0; this.lastSeekTarget = null; this.driftMs = null; this.mode = "aligned"; this.seekCount = 0; this.lastCorrection = null; }
    sync(replacement, snapshot, force = false, now = Date.now()) {
      const player = snapshot.player;
      replacement.applyState(player);
      const target = targetTime(projectTime(player, snapshot.observedAt, now), replacement.audio.duration, replacement.demoLoop);
      this.driftMs = driftAt(replacement.audio.currentTime, target, replacement.audio.duration, replacement.demoLoop);
      // currentTime assignment starts a new asynchronous decoder seek, even at
      // the same position. Let that seek finish instead of chasing the moving
      // master clock every 800 ms. A genuinely new user seek still wins.
      const aligned = Math.abs(this.driftMs) <= (force ? 40 : this.thresholdMs);
      const newSeek = force && (this.lastSeekTarget === null
        || Math.abs(driftAt(this.lastSeekTarget, target, replacement.audio.duration, replacement.demoLoop)) > this.thresholdMs);
      // Keep an already sounding decoder running for small clock errors. A
      // decoder seek can itself remove current data and create an audible hole.
      // Explicit user seeks and larger mismatches still reposition immediately.
      const running = !player.paused && !player.ended && !player.seeking && player.readyState >= 3
        && !replacement.audio.paused && !replacement.audio.seeking && replacement.audio.readyState >= 3;
      const gentle = !force && !replacement.demoLoop && running && Math.abs(this.driftMs) <= 1200
        && Math.abs(this.driftMs) > (this.mode === "rate" ? 80 : this.thresholdMs);
      this.mode = gentle ? "rate" : "aligned";
      if (gentle) {
        const baseRate = player.playbackRate > 0 ? player.playbackRate : 1;
        replacement.audio.playbackRate = baseRate * (this.driftMs < 0 ? 1.04 : 0.96);
      }
      const deferMinorSeek = !force && !replacement.demoLoop && !replacement.audio.paused
        && Math.abs(this.driftMs) <= 1200 && (replacement.audio.readyState < 3 || player.readyState < 3);
      if (deferMinorSeek) this.mode = "buffering";
      if (!deferMinorSeek && !gentle && !aligned && (!replacement.audio.seeking || newSeek)
          && (force || now - this.lastSeekAt >= 800)) {
        replacement.audio.currentTime = target;
        this.lastSeekAt = now;
        this.lastSeekTarget = target;
        this.seekCount++;
        this.mode = "seek";
        this.lastCorrection = { at:now, targetMs:Math.round(target*1000), driftMs:this.driftMs, explicit:force };
      }
      if (player.paused || player.ended || player.seeking || player.readyState < 3) replacement.pause();
      else replacement.play();
      return this.driftMs;
    }
  }
  Object.defineProperty(root, KEY, { value: Object.freeze({ SyncEngine, projectTime, targetTime, driftAt }), writable: false });
})(globalThis);

