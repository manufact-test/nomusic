import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import vm from "node:vm";
import { webcrypto } from "node:crypto";
const fixture = process.env.CELIKOM_NATIVE_FIXTURE || "/tmp/celikom-native-source-fixture";
const bytes = await readFile(fixture + "/short.mp3");
const moduleRoot = new URL("./", import.meta.url);
const sandbox = () => {
  const root = { crypto: webcrypto, TextEncoder, TextDecoder, URL, URLSearchParams, performance, setTimeout, clearTimeout, Blob, Response, AbortController, console };
  root.self = root; root.window = root; return vm.createContext(root);
};
const engineContext = sandbox();
vm.runInContext(await readFile(fixture + "/webpack-fixture.js", "utf8"), engineContext);
vm.runInContext(await readFile(new URL("engine-port.js", moduleRoot), "utf8"), engineContext);
const reloadExports = engineContext.__nativeFixture.req(engineContext.__nativeFixture.reloadModule);
const ReloadCore = reloadExports.__testReloadCore, statuses = reloadExports.MT, Playback = reloadExports.VE;
const { EnginePort } = engineContext.__CELIKOM_NATIVE_ENGINE_PORT__;
function gate() { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; }
function nativeEngine() {
  const applied = [], audio = new EventTarget();
  const entity = { data: { meta: { id: "1001", durationMs: 8000 } }, mediaSourceData: {} };
  const core = Object.create(ReloadCore.prototype);
  Object.defineProperties(core, {
    state: { value: { progress: { value: { position: 4.2 } }, status: { value: statuses.PLAYING } } },
    hooks: { value: Object.fromEntries(["beforeMediaSourceContentReload", "afterMediaSourceContentReload", "afterError"].map(k => [k, { promise: async () => {} }])) },
    currentAudioElement: { value: { value: audio } },
    getMediaSource: { value: async () => ({ data: { transport: "encraw", key: "fixture-original-key" } }), writable: true, configurable: true },
    corePlay: { value: async args => { applied.push(args); }, configurable: true },
    core: { value: { setSrc: args => { applied.push(args); } } }
  });
  const playback = Object.create(Playback.prototype);
  playback.playbackState = { queueState: { currentEntity: { value: { entity } } }, currentMediaPlayer: { value: core } };
  const controller = { getState: () => playback.state, playbackController: { getPlayback: () => playback } };
  const port = new EnginePort({ getController: () => controller });
  return { port, core, audio, entity, applied, playback, controller };
}

vm.runInContext(await readFile(new URL("native-session.js", moduleRoot), "utf8"), engineContext);
function sessionFixture() {
  const n = nativeEngine(), registered = new Map(), revoked = [];
  const resource = { enabled: false, setEnabled(value) { this.enabled = value; },
    register(id, url) { registered.set(id, url); }, unregister(id) { registered.delete(id); } };
  n.audio.src = "https://fixture.example/original"; n.audio.currentSrc = n.audio.src; n.audio.readyState = 4;
  n.core.getMediaSource = async ({ entity }) => ({ data: { url: resource.enabled && registered.get(entity.data.meta.id) || "https://fixture.example/original" } });
  const apply = async ({ source }) => { n.audio.src = source.data.url; n.audio.currentSrc = n.audio.src; n.audio.dispatchEvent(new Event("loadedmetadata")); };
  Object.defineProperty(n.core, "corePlay", { value: apply, configurable: true }); n.core.core.setSrc = apply;
  let serial = 0;
  const session = new engineContext.__CELIKOM_NATIVE_SESSION__.NativeSession({ port: n.port, resource,
    environment: { setTimeout, clearTimeout, URL: { createObjectURL: () => "blob:https://fixture.example/" + ++serial, revokeObjectURL: url => revoked.push(url) } } });
  const publish = () => session.publish({ trackId: "1001", generation: 1, durationMs: 8000,
    expiresAt: Date.now() + 60000, blob: new Blob([bytes], { type: "audio/mpeg" }) });
  return { ...n, resource, registered, revoked, session, publish };
}
test("native session stages bytes without registering a source before admission", async () => {
  const n = sessionFixture(); await n.session.configure(true, 1); n.publish();
  assert.equal(n.registered.size, 0); assert.equal(n.session.inspect().activeTrackId, null);
});
test("actual Yandex reload switches current source and restores original before revoking Blob", async () => {
  const n = sessionFixture(); await n.session.configure(true, 1); n.publish();
  assert.equal((await n.session.activate("1001", 1)).active, true);
  assert.equal(n.session.inspect().activeTrackId, "1001");
  await n.session.configure(false, 2);
  assert.equal(n.audio.src, "https://fixture.example/original"); assert.equal(n.revoked.length, 1);
  assert.equal(n.session.inspect().activeTrackId, null); assert.equal(n.registered.size, 0);
});
test("stale session, missing track, duration mismatch and duplicate publication are denied", async () => {
  const n = sessionFixture(); await n.session.configure(true, 1); n.publish();
  assert.throws(n.publish, /already_present/);
  await assert.rejects(n.session.activate("1001", 0), /not_admitted/);
  await assert.rejects(n.session.activate("1002", 1), /not_admitted/);
  n.entity.data.meta.durationMs = 12000;
  await assert.rejects(n.session.activate("1001", 1), /not_admitted/);
  assert.equal(n.registered.size, 0);
});
test("Stop while source read is pending cannot apply the prepared source", async () => {
  const n = sessionFixture(); await n.session.configure(true, 1); n.publish();
  const entered = gate(), delayed = gate();
  n.core.getMediaSource = async () => { entered.resolve(); return delayed.promise; };
  const activation = n.session.activate("1001", 1); await entered.promise;
  const stopped = n.session.configure(false, 2);
  delayed.resolve({ data: { url: "blob:https://fixture.example/1" } });
  await assert.rejects(activation, /stale/); await stopped;
  assert.equal(n.audio.src, "https://fixture.example/original"); assert.equal(n.session.assets.size, 0);
});
test("Next before activation leaves the new song untouched", async () => {
  const n = sessionFixture(); await n.session.configure(true, 1); n.publish();
  n.playback.state.queueState.currentEntity.value = { entity: { data: { meta: { id: "1002", durationMs: 8000 } } } };
  await assert.rejects(n.session.activate("1001", 1), /not_admitted/); assert.equal(n.registered.size, 0);
});
test("stale revoke cannot disable a newer authorized session", async () => {
  const n = sessionFixture(); await n.session.configure(true, 2);
  await n.session.revoke({ generation: 1 }); assert.equal(n.session.enabled, true);
});
test("original restore failure retains the URL instead of revoking a playing source", async () => {
  const n = sessionFixture(); await n.session.configure(true, 1); n.publish(); await n.session.activate("1001", 1);
  n.core.getMediaSource = async () => { throw Error("controlled-network-error"); };
  await assert.rejects(n.session.configure(false, 2), /controlled-network-error/);
  assert.equal(n.revoked.length, 0); assert.equal(n.session.enabled, false); assert.equal(n.registered.size, 0);
});

test("isolated controller uses existing downloader and MAIN RPC without a legacy player owner", async () => {
  const n = sessionFixture();
  const script = async name => vm.runInContext(await readFile(new URL(name, moduleRoot), "utf8"), engineContext);
  const originalRegistry = engineContext.__CELIKOM_REPLACEMENT_CONTROLLER_V1__;
  assert.equal(originalRegistry, undefined);
  const messages = [], timers = new Set();
  Object.assign(engineContext, { AbortController, Event, EventTarget, queueMicrotask, setTimeout, clearTimeout,
    __CELIKOM_NATIVE_SOURCE_RESEARCH__: n.resource,
    __CELIKOM_PLAYER_CORE_V1__: { CHANNEL: "CELIKOM_PLAYER_V1", PROTOCOL_VERSION: 1 },
    document: { hidden: false, querySelectorAll: () => [{ __reactFiber$fixture: { memoizedProps: { value: n.controller } } }] },
    __messages: messages,
    setInterval: fn => { timers.add(fn); return fn; }
  });
  vm.runInContext(`{
    const listeners = new Map();
    globalThis.addEventListener = (key, fn) => { if (!listeners.has(key)) listeners.set(key, new Set()); listeners.get(key).add(fn); };
    globalThis.removeEventListener = (key, fn) => listeners.get(key)?.delete(fn);
    globalThis.postMessage = data => queueMicrotask(() => {
      __messages.push(data);
      for (const fn of listeners.get("message") || []) fn({ source: globalThis, data });
    });
  }`, engineContext);
  await script("../../extension/dist/unpacked/player/replacement-player.js");
  await script("prefetch-coordinator.js"); await script("desktop-prefetch-adapter.js");
  const parser = (await readFile(new URL("../../extension/dist/unpacked/upload/mp3-duration.js", moduleRoot), "utf8")).replaceAll("export function ", "function ");
  vm.runInContext(parser + "\nglobalThis.__CELIKOM_NATIVE_MP3_DURATION__ = mp3DurationMs;", engineContext);
  await script("native-runtime.js"); await script("native-controller.js");
  const requests = [];
  engineContext.fetch = async (url, options) => {
    requests.push({ url, range: options.headers.Range });
    const match = /^bytes=(\d+)-(\d+)$/.exec(options.headers.Range);
    const from = Number(match[1]), end = Math.min(Number(match[2]), bytes.length - 1);
    return new Response(bytes.subarray(from, end + 1), { status: 206, headers: {
      "Content-Type": "audio/mpeg", "Content-Range": `bytes ${from}-${end}/${bytes.length}`, ETag: '"fixture-1"'
    } });
  };
  engineContext.__resolve = async id => ({ found: true, url: "https://fixture.example/audio", mimeType: "audio/mpeg", gainDb: 0,
    replacementId: 1, version: 1, durationMs: 8000, expiresAt: Date.now() + 60000 });
  vm.runInContext(`
    globalThis.__testBridge = {
      sessionId: "fixture-controller-session", isHealthy: () => true,
      post: (type, payload = {}) => postMessage({ channel: "CELIKOM_PLAYER_V1", protocolVersion: 1, direction: "to-main", sessionId: "fixture-controller-session", type, payload })
    };
    __testBridge.post("INIT");
    globalThis.__testController = new __CELIKOM_REPLACEMENT_CONTROLLER_V1__.ReplacementController(__testBridge, globalThis, { resolveAsset: __resolve });
  `, engineContext);
  const controller = engineContext.__testController;
  await new Promise(resolve => setImmediate(resolve)); controller.configure(true, ""); await controller.control;
  assert.equal(controller.lastError, null);
  await controller.poll();
  assert.equal(controller.phase, "REPLACEMENT_ACTIVE"); assert.equal(controller.activationCount, 1);
  assert.ok(n.audio.src.startsWith("blob:")); assert.equal(requests.length, 1);
  assert.ok(messages.some(m => m.type === "publish" && m.payload.blob?.type === "audio/mpeg"));
  assert.ok(messages.filter(m => m.type === "POLICY_UPDATE").every(m => m.payload.enabled === false));
  controller.manualRestore(); await controller.control;
  assert.equal(n.audio.src, "https://fixture.example/original"); assert.equal(controller.operation, null);
  await controller.poll(); assert.equal(controller.phase, "IDLE");
  controller.configure(false, ""); await controller.control; controller.destroy();
});
test("Next with new metadata waits for the native transition instead of reloading at the old position", async () => {
  const n = sessionFixture(); await n.session.configure(true, 1); n.publish(); await n.session.activate("1001", 1);
  n.playback.state.queueState.currentEntity.value = { entity: { data: { meta: { id: "1002", durationMs: 8000 } } } };
  let reads = 0; n.core.getMediaSource = async () => { reads++; throw Error("must not reload new song"); };
  const stopped = n.session.configure(false, 2);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(reads, 0); assert.equal(n.revoked.length, 0);
  n.audio.src = "https://fixture.example/next"; n.audio.currentSrc = n.audio.src;
  n.audio.dispatchEvent(new Event("loadedmetadata")); await stopped;
  assert.equal(n.revoked.length, 1); assert.equal(reads, 0);
});
