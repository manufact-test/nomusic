import assert from "node:assert/strict";
import test from "node:test";
import vm from "node:vm";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../dist/unpacked/player/replacement-controller.js", import.meta.url), "utf8");

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
