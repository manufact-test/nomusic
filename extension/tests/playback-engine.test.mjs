import assert from "node:assert/strict";
import test from "node:test";
await import("../dist/unpacked/player/core.js");
await import("../dist/unpacked/player/original-audio-guard.js");
await import("../dist/unpacked/player/sync-engine.js");
await import("../dist/unpacked/player/replacement-player.js");
await import("../dist/unpacked/player/fail-open-controller.js");
await import("../dist/unpacked/player/replacement-controller.js");
const { OriginalAudioGuard } = globalThis.__CELIKOM_ORIGINAL_GUARD_V1__;
const { SyncEngine, targetTime, projectTime, driftAt } = globalThis.__CELIKOM_SYNC_ENGINE_V1__;
const { ReplacementController } = globalThis.__CELIKOM_REPLACEMENT_CONTROLLER_V1__;
const { ReplacementPlayer } = globalThis.__CELIKOM_REPLACEMENT_PLAYER_V1__;
const settle = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
const deferred = () => { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; };

class Media extends EventTarget {
  constructor() { super(); this.physicalVolume = 0.5; this.physicalMuted = false; this.currentTime = 0; this.duration = 4; this.paused = true; this.readyState = 4; this.dataset = {}; }
  get volume() { return this.physicalVolume; }
  set volume(value) { if (value < 0 || value > 1) throw new RangeError("volume"); this.physicalVolume = Number(value); queueMicrotask(() => this.dispatchEvent(new Event("volumechange"))); }
  get muted() { return this.physicalMuted; }
  set muted(value) { if (this.physicalMuted === Boolean(value)) return; this.physicalMuted = Boolean(value); queueMicrotask(() => this.dispatchEvent(new Event("volumechange"))); }
  play() { this.paused = false; return Promise.resolve(); }
  pause() { this.paused = true; }
  load() {}
  remove() { this.removed = true; }
  removeAttribute(name) { if (name === "src") this.src = ""; }
}

test("guard preserves logical volume/mute while silencing physical original", async () => {
  const media = new Media(); const guard = new OriginalAudioGuard();
  guard.engage(media, "m1", "s:1");
  assert.equal(media.physicalMuted, true);
  assert.equal(media.muted, false, "site sees user intent, not forced mute");
  media.volume = 0.012; media.muted = true;
  await settle();
  assert.equal(guard.state().volume, 0.012);
  assert.equal(guard.state().muted, true);
  media.muted = false;
  assert.equal(media.physicalMuted, true, "site cannot unmute original while guarded");
  guard.release("s:1"); await settle();
  assert.equal(media.volume, 0.012); assert.equal(media.muted, false);
  assert.equal(Object.hasOwn(media, "muted"), false);
});
test("guard restores initially muted media and rejects stale release leases", () => {
  const media = new Media(); media.muted = true;
  const guard = new OriginalAudioGuard();
  guard.engage(media, "m1", "s:2"); guard.engage(media, "m1", "s:2");
  assert.equal(guard.release("s:1").released, false);
  assert.throws(() => guard.engage(media, "m1", "s:3"), /leased/);
  guard.release("s:2"); assert.equal(media.muted, true);
});
test("guard tracks native prototype volume writes without mistaking own mute for user intent", async () => {
  const media = new Media(); const guard = new OriginalAudioGuard();
  guard.engage(media, "m", "t"); await settle();
  Object.getOwnPropertyDescriptor(Media.prototype, "volume").set.call(media, 0.2);
  Object.getOwnPropertyDescriptor(Media.prototype, "muted").set.call(media, false);
  await settle();
  assert.equal(media.physicalMuted, true); assert.equal(media.volume, 0.2); assert.equal(media.muted, false);
  guard.release(); assert.equal(media.physicalMuted, false);
});
test("uninterceptable original properties fail before any mute mutation", () => {
  const media = new Media(); Object.defineProperty(media, "muted", { value: false, configurable: false });
  const guard = new OriginalAudioGuard();
  assert.throws(() => guard.engage(media, "m", "t"), /guarded safely/);
  assert.equal(media.physicalMuted, false); assert.equal(guard.state().active, false);
});
test("sync projects only a running ready clock and wraps only explicit synthetic assets", () => {
  const state = { currentTime: 5, playbackRate: 2, duration: 20, readyState: 4 };
  assert.equal(projectTime(state, 1000, 1500), 6);
  for (const extra of [{ paused: true }, { seeking: true }, { ended: true }, { readyState: 2 }]) assert.equal(projectTime({ ...state, ...extra }, 1000, 1500), 5);
  assert.equal(projectTime(state, 1000, 9000), 8, "projection is bounded");
  assert.equal(targetTime(19, 4, true), 3);
  assert.throws(() => targetTime(19, 4, false), /ended/);
  assert.equal(driftAt(0.02, 3.98, 4, true), 40);
});

function snapshot(id = "2", extra = {}) {
  return { observedAt: Date.now(), track: { id, confidence: 260, ambiguous: false, metadata: { durationMs: 200000 } }, player: { mediaId: "master", paused: false, ended: false, seeking: false, readyState: 4, currentTime: 7, duration: 200, volume: 0.012, muted: false, playbackRate: 1 }, ...extra };
}
function fixture({ loadGate, guardGate, rejectGuard = false, playerThrows = false } = {}) {
  const players = []; const requests = []; let current = snapshot(); let healthy = true;
  const bridge = {
    sessionId: "session-123", isHealthy: () => healthy, getSnapshot: async () => current,
    request: async (type, payload) => {
      requests.push({ type, ...payload });
      if (type === "GUARD_ENGAGE") {
        if (guardGate) await guardGate.promise;
        if (rejectGuard) throw new Error("guard rejected");
        return { snapshot: current };
      }
      return { released: true };
    },
    post: (type, payload) => requests.push({ type, ...payload })
  };
  const environment = { chrome: { runtime: { getURL: (name) => `chrome-extension://test/${name}` } }, document: { hidden: false } };
  const engine = new ReplacementController(bridge, environment, { createPlayer: (fatal) => {
    if (playerThrows) throw new Error("constructor failed");
    const player = {
      audio: new Media(), demoLoop: true, fatal, destroyed: false,
      prepare: async () => { if (loadGate) await loadGate.promise; },
      applyState: (state) => { player.audio.volume = state.volume; player.audio.muted = state.muted; player.audio.playbackRate = state.playbackRate; },
      play: () => { player.audio.paused = false; }, pause: () => { player.audio.paused = true; },
      destroy: () => { player.destroyed = true; player.audio.paused = true; }
    };
    players.push(player); return player;
  } });
  engine.configure(true, "2");
  const update = (next, event) => { current = next; engine.update(next, event); };
  return { engine, bridge, players, requests, update, unhealthy: () => { healthy = false; } };
}
test("A(original) → B(replacement) → C(original) uses exact ID and one player", async () => {
  const f = fixture(); f.update(snapshot("1")); await settle(); assert.equal(f.players.length, 0);
  f.update(snapshot("2")); await settle(); assert.equal(f.engine.phase, "REPLACEMENT_ACTIVE");
  assert.equal(f.players[0].audio.volume, 0.012);
  f.update(snapshot("3")); assert.equal(f.players[0].destroyed, true); await settle();
  assert.equal(f.engine.phase, "IDLE"); assert.equal(f.players.length, 1);
});
test("manual original stays bypassed on same track; unrelated settings do not rearm", async () => {
  const f = fixture(); f.update(snapshot()); await settle(); f.engine.manualRestore(); await settle();
  for (let i = 0; i < 10; i++) { f.update(snapshot()); f.engine.configure(true, "2"); f.engine.tick(); }
  await settle(); assert.equal(f.players.length, 1); assert.equal(f.engine.manualBypass.trackId, "2");
  f.engine.configure(true, "2", true); await settle(); assert.equal(f.players.length, 2);
  f.engine.manualRestore(); await settle(); f.update(snapshot("3")); assert.equal(f.engine.manualBypass, null);
});
test("unknown track never clears manual bypass; next exact track does", async () => {
  const f = fixture(); f.update(snapshot()); await settle(); f.engine.manualRestore(); await settle();
  f.update(snapshot(null)); f.update(snapshot()); await settle(); assert.equal(f.players.length, 1);
  f.update(snapshot("3")); f.update(snapshot()); await settle(); assert.equal(f.players.length, 2);
});
test("rapid next → next → previous invalidates old loads and never guards a stale track", async () => {
  const gate = deferred(); const f = fixture({ loadGate: gate });
  f.update(snapshot()); f.update(snapshot("3")); await settle(); f.update(snapshot("4")); f.update(snapshot());
  gate.resolve(); await settle();
  assert.equal(f.players.length, 2); assert.equal(f.players[0].destroyed, true);
  assert.equal(f.requests.filter((r) => r.type === "GUARD_ENGAGE").length, 1);
  assert.equal(f.engine.phase, "REPLACEMENT_ACTIVE");
});
test("disable while loading cancels replacement before acquiring any guard", async () => {
  const gate = deferred(); const f = fixture({ loadGate: gate }); f.update(snapshot());
  f.engine.configure(false, "2"); gate.resolve(); await settle();
  assert.equal(f.engine.phase, "IDLE"); assert.equal(f.players[0].destroyed, true);
  assert.equal(f.requests.some((r) => r.type === "GUARD_ENGAGE"), false);
});
test("late guard acknowledgement after manual restore is released by its own lease", async () => {
  const gate = deferred(); const f = fixture({ guardGate: gate }); f.update(snapshot()); await settle();
  f.engine.manualRestore(); await settle(); gate.resolve(); await settle();
  assert.equal(f.engine.phase, "IDLE"); assert.equal(f.players[0].audio.paused, true);
  assert.equal(f.requests.at(-1).type, "RELEASE_NOW");
  assert.equal(f.requests.at(-1).token, "session-123:1");
});
test("stale error from disposed replacement cannot affect a later generation", async () => {
  const f = fixture(); f.update(snapshot()); await settle(); const old = f.players[0];
  f.update(snapshot("3")); await settle(); f.update(snapshot()); await settle(); old.fatal("old media error");
  assert.equal(f.engine.phase, "REPLACEMENT_ACTIVE"); assert.equal(f.players[1].destroyed, false);
});
test("seek + pause immediately positions and pauses replacement, then resume follows master", async () => {
  const f = fixture(); f.update(snapshot()); await settle();
  const paused = snapshot(); paused.player.currentTime = 18; paused.player.paused = true;
  f.update(paused, "SEEK"); assert.equal(f.players[0].audio.currentTime, 2); assert.equal(f.players[0].audio.paused, true);
  paused.player.paused = false; f.update(paused, "PLAY"); assert.equal(f.players[0].audio.paused, false);
});
test("guard denial and player construction errors fail open without automatic retry storms", async () => {
  for (const options of [{ rejectGuard: true }, { playerThrows: true }]) {
    const f = fixture(options); f.update(snapshot()); await settle();
    assert.equal(f.engine.phase, "IDLE"); assert.ok(f.engine.lastError);
    const count = f.players.length; f.update(snapshot()); f.engine.tick(); await settle(); assert.equal(f.players.length, count);
  }
});
test("ambiguity, mismatched media duration and unhealthy bridge cannot engage a guard", async () => {
  for (const mutate of [s => { s.track.ambiguous = true; }, s => { s.player.duration = 15; }, s => { s.track.confidence = 20; }]) {
    const f = fixture(); const s = snapshot(); mutate(s); f.update(s); await settle(); assert.equal(f.players.length, 0);
  }
  const f = fixture(); f.update(snapshot()); await settle(); f.unhealthy(); f.engine.tick();
  assert.equal(f.players[0].destroyed, true); await settle(); assert.equal(f.engine.phase, "IDLE");
});
test("sync cooldown prevents correction ping-pong; force seek bypasses cooldown", () => {
  const f = fixture(); const s = snapshot(); s.observedAt = 1000;
  const p = { audio: new Media(), demoLoop: true, applyState() {}, play() {}, pause() {} };
  const sync = new SyncEngine(); sync.sync(p, s, true, 1000); assert.equal(p.audio.currentTime, 3);
  p.audio.currentTime = 1; sync.sync(p, s, false, 1100); assert.equal(p.audio.currentTime, 1);
  s.player.paused = true; s.player.currentTime = 10; sync.sync(p, s, true, 1200); assert.equal(p.audio.currentTime, 2);
});
test("native ReplacementPlayer cancels loads, rejects blocked play and stays paused after late play", async () => {
  const media = new Media(); const fatal = [];
  const env = { document: { createElement: () => media, documentElement: { append() {} } }, setTimeout, clearTimeout, AbortController, URL, fetch: async () => ({ ok: true, blob: async () => new Blob(["synthetic fixture"]) }) };
  const player = new ReplacementPlayer(env, (reason) => fatal.push(reason));
  await player.prepare({ url: "chrome-extension://test/assets/test-audio.mp3", demoLoop: true });
  assert.equal(media.loop, true); assert.equal(media.muted, true);
  media.play = () => Promise.reject(new Error("NotAllowedError")); player.play(); await settle();
  assert.deepEqual(fatal, ["replacement-play-blocked"]);
  const gate = deferred(); media.play = () => gate.promise;
  player.play(); player.pause(); gate.resolve(); await settle(); assert.equal(media.paused, true);
  player.destroy(); assert.equal(media.removed, true); assert.equal(media.muted, true);
  const loading = new Media(); loading.readyState = 0;
  const p2 = new ReplacementPlayer({ ...env, document: { ...env.document, createElement: () => loading } }, () => {});
  const ready = p2.prepare({ url: "local", demoLoop: false }); p2.destroy(); await assert.rejects(ready, /cancelled/);
});

test("long native pause keeps the guard and replacement available for resume", async () => {
  const f = fixture(); const s = snapshot(); s.player.paused = true; s.observedAt = Date.now() - 20000;
  f.update(s); await settle(); f.engine.tick();
  assert.equal(f.engine.phase, "REPLACEMENT_ACTIVE"); assert.equal(f.players[0].audio.paused, true);
});
test("failed restore acknowledgement sends a token-scoped emergency signal", async () => {
  const f = fixture(); f.update(snapshot()); await settle();
  f.bridge.request = async () => { throw new Error("connection lost"); };
  f.engine.manualRestore(); assert.equal(f.players[0].destroyed, true); await settle();
  assert.equal(f.requests.at(-1).type, "RELEASE_NOW"); assert.equal(f.engine.phase, "IDLE");
});
test("destroy while demo fetch resolves does not leak or attach a playable asset", async () => {
  const gate = deferred(); const media = new Media(); let created = 0;
  const env = { document: { createElement: () => media, documentElement: { append() {} } }, setTimeout, clearTimeout, AbortController, fetch: () => gate.promise,
    URL: { createObjectURL: () => { created++; return "blob:test"; }, revokeObjectURL() {} } };
  const player = new ReplacementPlayer(env, () => {});
  const ready = player.prepare({ url: "packaged", demoLoop: true }); player.destroy();
  gate.resolve({ ok: true, blob: async () => new Blob(["fixture"]) });
  await assert.rejects(ready, /cancelled/); assert.equal(created, 0); assert.equal(media.paused, true);
});
