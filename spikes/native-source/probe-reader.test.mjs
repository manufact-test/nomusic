import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";
import { spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";
const output = path.join(os.tmpdir(), "celikom-engine-reader-test");
const built = spawnSync(process.execPath, ["spikes/native-source/build-probe.mjs", output], { encoding: "utf8" });
assert.equal(built.status, 0, built.stderr);
const source = await readFile(path.join(output, "reader.js"), "utf8");
function fixture() {
  let mutations = 0;
  const forbidden = () => { mutations++; throw Error("mutation"); };
  const audio = { addEventListener: forbidden, removeEventListener: forbidden };
  const core = { getMediaSource: forbidden, reload: forbidden, corePlay: forbidden, core: { setSrc: forbidden }, currentAudioElement: { value: audio },
    hooks: { beforeMediaSourceContentReload: { promise: forbidden }, afterMediaSourceContentReload: { promise: forbidden } } };
  const pair = { entity: { data: { meta: { id: "1001", durationMs: 8000 } } } };
  const playback = { queueState: { currentEntity: { value: pair } }, currentMediaPlayer: { value: core } };
  const controller = { getState: forbidden, playbackController: { getPlayback: () => playback } };
  const node = {};
  Object.defineProperty(node, "__reactFiber$fixture", { value: { memoizedProps: {}, dependencies: { firstContext: { memoizedValue: controller, next: null } } }, enumerable: false });
  const sandbox = vm.createContext({ document: { querySelectorAll: selector => selector === "*" ? [node] : [] } });
  return { sandbox, mutations: () => mutations };
}
test("generated reader replaces an old reader on the same already open tab", () => {
  const f = fixture();
  vm.runInContext('Object.defineProperty(globalThis,"__CELIKOM_ENGINE_READONLY_PROBE__",{value:{inspect:()=>({controllerFound:false})},configurable:true})', f.sandbox);
  vm.runInContext(source, f.sandbox);
  const reader = f.sandbox.__CELIKOM_ENGINE_READONLY_PROBE__, result = reader.inspect();
  assert.equal(reader.version, 2); assert.equal(result.readerVersion, 2); assert.equal(result.found, true);
  assert.equal(result.discovery.matchSource, "fiber-context"); assert.equal(result.discovery.nonEnumerableRoots, 1);
  assert.equal(f.mutations(), 0);
});
test("same-version reinjection is idempotent and fresh inspection reads current DOM", () => {
  const f = fixture(); vm.runInContext(source, f.sandbox);
  const reader = f.sandbox.__CELIKOM_ENGINE_READONLY_PROBE__; assert.equal(reader.inspect().found, true);
  vm.runInContext(source, f.sandbox); assert.equal(f.sandbox.__CELIKOM_ENGINE_READONLY_PROBE__, reader);
  f.sandbox.document = { querySelectorAll: () => [] };
  const absent = reader.inspect(); assert.equal(absent.found, false); assert.equal(absent.discovery.nodes, 0);
  assert.equal(f.mutations(), 0);
});
test("read-only artifact exposes inspection only and serializes no private object", () => {
  const f = fixture(); vm.runInContext(source, f.sandbox); const reader = f.sandbox.__CELIKOM_ENGINE_READONLY_PROBE__;
  assert.deepEqual(Object.keys(reader).sort(), ["inspect", "version"]);
  const data = JSON.stringify(reader.inspect());
  assert.ok(!data.includes("playbackController")); assert.ok(!data.includes("memoizedValue"));
  assert.ok(!data.includes("token")); assert.ok(!data.includes("cookies")); assert.equal(f.mutations(), 0);
});
