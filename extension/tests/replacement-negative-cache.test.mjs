import assert from "node:assert/strict";
import test from "node:test";
import vm from "node:vm";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../dist/unpacked/player/replacement-controller.js", import.meta.url), "utf8");

test("Stage 6.6: unapproved/missing remote audio never engages the guard or mutes the original", async () => {
  let now = 2000000; let calls = 0; let guardEvents = 0; let restores = 0;
  const context = vm.createContext({
    Date: { now: () => now },
    __CELIKOM_PLAYER_CORE_V1__: { normalizeTrackId: id => /^[1-9]\d+$/.test(id || "") ? id : null },
    __CELIKOM_REPLACEMENT_PLAYER_V1__: { ReplacementPlayer: class {} },
    __CELIKOM_SYNC_ENGINE_V1__: { SyncEngine: class {} },
    __CELIKOM_FAIL_OPEN_V1__: { FailOpenController: class {
      restore() { restores++; return Promise.resolve(); }
    } }
  });
  vm.runInContext(source, context);
  const Controller = context.__CELIKOM_REPLACEMENT_CONTROLLER_V1__.ReplacementController;
  const bridge = {
    sessionId: "fixture", isHealthy: () => true,
    request: async () => { guardEvents++; throw new Error("no guard on missing audio"); }
  };
  const engine = new Controller(bridge, { document: { hidden: false } }, {
    createPlayer: () => { throw new Error("No replacement player for an unmapped track"); },
    resolveAsset: async () => { calls++; return { found: false, retryAfterMs: 5000 }; }
  });
  engine.configure(true, "");
  engine.update({
    observedAt: now, track: { id: "999998", confidence: 100, ambiguous: false, metadata: { durationMs: 201000 } },
    player: { mediaId: "media-ci", readyState: 4, ended: false, duration: 201, paused: false }
  });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(engine.operation, null);
  assert.equal(engine.phase, "IDLE");
  assert.equal(engine.blockedTrackId, null);
  assert.equal(guardEvents, 0);
  assert.equal(restores, 0);
  for (let t = 0; t < 10; t++) engine.tick();
  assert.equal(calls, 1, "no network storm while staying on an unmapped track");
  now += 5001;
  engine.tick();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(calls, 2, "retry after bounded negative TTL");
  assert.equal(guardEvents, 0, "original remains untouched after negative refresh");
  engine.destroy();
});

test("Stage 6.5 controller honors a five-second negative TTL without repeated tick polling", async () => {
  let clock = 1000000; let calls = 0;
  const context = vm.createContext({
    Date: { now: () => clock },
    __CELIKOM_PLAYER_CORE_V1__: { normalizeTrackId: id => /^[1-9]\d+$/.test(id || "") ? id : null },
    __CELIKOM_REPLACEMENT_PLAYER_V1__: { ReplacementPlayer: class {} },
    __CELIKOM_SYNC_ENGINE_V1__: { SyncEngine: class {} },
    __CELIKOM_FAIL_OPEN_V1__: { FailOpenController: class { restore() { return Promise.resolve(); } } }
  });
  vm.runInContext(source, context);
  const Controller = context.__CELIKOM_REPLACEMENT_CONTROLLER_V1__.ReplacementController;
  const bridge = { sessionId: "fixture", isHealthy: () => true };
  const ctrl = new Controller(bridge, { document: { hidden: false } }, {
    resolveAsset: async () => { calls++; return { found: false, retryAfterMs: 5000 }; }
  });
  const snapshot = {
    observedAt: clock,
    track: { id: "1944599", confidence: 100, ambiguous: false, metadata: { durationMs: 201000 } },
    player: { mediaId: "media-1", readyState: 4, ended: false, duration: 201, paused: false }
  };
  const flush = async () => new Promise(resolve => setImmediate(resolve));
  ctrl.configure(true, "");
  ctrl.update(snapshot);
  await flush();
  assert.equal(calls, 1);
  assert.equal(ctrl.negativeResolution.until, 1005000);
  for (let n = 0; n < 20; n++) ctrl.tick();
  assert.equal(calls, 1, "no per-tick resolve within TTL");
  clock += 4999;
  ctrl.tick(); await flush();
  assert.equal(calls, 1);
  clock += 2;
  ctrl.tick(); await flush();
  assert.equal(calls, 2, "controller retries after server TTL, not fixed 15s");
  ctrl.destroy();
});
