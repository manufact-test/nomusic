import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import vm from "node:vm";
import { webcrypto, createHash } from "node:crypto";
import { createApiBroker } from "../../extension/dist/unpacked/api/api-broker.js";
import { mp3DurationMs } from "../../extension/dist/unpacked/upload/mp3-duration.js";

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
const ReloadCore = reloadExports.__testReloadCore, statuses = reloadExports.MT;
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
  const playback = { queueState: { currentEntity: { value: { entity } } }, currentMediaPlayer: { value: core } };
  const controller = { getState: () => ({}), playbackController: { getPlayback: () => playback } };
  const port = new EnginePort({ getController: () => controller });
  return { port, core, audio, entity, applied, playback, controller };
}
test("actual Yandex reload retains position and encrypted source through native core", async () => {
  const n = nativeEngine(), method = n.core.getMediaSource;
  assert.equal((await n.port.reload("1001")).restored, true);
  assert.equal(n.applied.length, 1); assert.equal(n.applied[0].positionSec, 4.2);
  assert.equal(n.applied[0].source.data.transport, "encraw");
  assert.equal(n.applied[0].source.data.key, "fixture-original-key");
  assert.equal(n.core.getMediaSource, method);
});
test("actual native reload preserves paused state without corePlay", async () => {
  const n = nativeEngine(); n.core.state.status.value = statuses.PAUSED;
  let played = false; Object.defineProperty(n.core, "corePlay", { value: async () => { played = true; } });
  await n.port.reload("1001"); assert.equal(played, false); assert.equal(n.applied.length, 1);
  assert.equal(n.core.state.status.value, statuses.PAUSED);
});
test("native reload bypasses its old source cache and keeps the resource receiver", async () => {
  const n = nativeEngine();
  n.core.getMediaSource = async function (options) {
    assert.equal(this, n.core); assert.equal(options.entity, n.entity); assert.equal(options.disableCache, true);
    return { data: { transport: "encraw" } };
  };
  await n.port.reload("1001"); assert.equal(n.applied.length, 1);
});
test("Next during an asynchronous native before-reload hook cannot apply the old source", async () => {
  const n = nativeEngine(), entered = gate(), release = gate();
  n.core.hooks.beforeMediaSourceContentReload.promise = async () => { entered.resolve(); await release.promise; };
  const run = n.port.reload("1001"); await entered.promise;
  n.playback.queueState.currentEntity.value = { entity: { data: { meta: { id: "1002" } } } };
  release.resolve(); await assert.rejects(run, /native_reload_stale/); assert.equal(n.applied.length, 0);
});
for (const change of ["next", "media-player", "pause", "seek", "cancel", "authority"]) {
  test("late original reload cannot override " + change, async () => {
    const n = nativeEngine(), deferred = gate(), entered = gate(); let valid = true;
    n.core.getMediaSource = async () => { entered.resolve(); return deferred.promise; };
    const run = n.port.reload("1001", { isCurrent: () => valid }); await entered.promise;
    if (change === "next") n.playback.queueState.currentEntity.value = { entity: { data: { meta: { id: "1002" } } } };
    if (change === "media-player") n.playback.currentMediaPlayer.value = {};
    if (change === "pause") n.audio.dispatchEvent(new Event("pause"));
    if (change === "seek") n.audio.dispatchEvent(new Event("seeking"));
    if (change === "cancel") n.port.cancel();
    if (change === "authority") valid = false;
    deferred.resolve({ data: { transport: "encraw" } });
    await assert.rejects(run, /native_reload_(stale|intent_changed)/);
    assert.equal(n.applied.length, 0); assert.equal(n.port.pending, null);
  });
}
test("one pending reload per binding and no automatic retry", async () => {
  const n = nativeEngine(), entered = gate(), deferred = gate(); let requests = 0;
  n.core.getMediaSource = async () => { requests++; entered.resolve(); return deferred.promise; };
  const run = n.port.reload("1001"); await entered.promise;
  assert.equal(n.port.reload("1001"), run);
  await assert.rejects(n.port.reload("1002"), /native_reload_busy/);
  n.port.cancel(); deferred.resolve({}); await assert.rejects(run, /native_reload_stale/); assert.equal(requests, 1);
});
test("reload cleanup does not overwrite a newer owner's method", async () => {
  const n = nativeEngine(), entered = gate(), deferred = gate();
  n.core.getMediaSource = async () => { entered.resolve(); return deferred.promise; };
  const run = n.port.reload("1001"); await entered.promise;
  const foreign = async () => ({}); n.core.getMediaSource = foreign;
  deferred.resolve({}); await run; assert.equal(n.core.getMediaSource, foreign);
});
test("DOM discovery follows bounded React providers without exposing account data", () => {
  const n = nativeEngine(), controller = n.controller;
  const fiber = { memoizedProps: { value: controller }, return: null };
  const node = { __reactFiber$fixture: { memoizedProps: {}, return: fiber } };
  assert.equal(engineContext.__CELIKOM_NATIVE_ENGINE_PORT__.discoverController({ querySelectorAll: () => [node] }), controller);
  assert.equal(n.port.inspect().trackId, "1001");
});

async function pipeline() {
  const root = sandbox();
  for (const file of ["../../extension/dist/unpacked/player/replacement-player.js", "prefetch-coordinator.js", "desktop-prefetch-adapter.js"]) {
    vm.runInContext(await readFile(new URL(file, moduleRoot), "utf8"), root);
  }
  let allowed = true, loggedIn = true, duration = 8000, gain = 0, version = 1, audioStatus = 206, downloads = 0, calls = 0;
  const published = [], revoked = [], now = Date.now(), expires = Math.floor(now / 1000) + 600;
  const api = { runtime: { id: "fixture-extension", getManifest: () => ({ version: "0.4.73" }) } };
  const broker = createApiBroker(api, {
    now: () => now, readConfig: async () => ({ baseUrl: "https://celikom.example" }),
    withAccess: async fn => { if (!loggedIn) throw Error("invalid_session"); return fn({ access_token: "fixture-only-bearer-no-real-account" }); },
    entitlement: async () => ({ allowed }),
    fetch: async url => { calls++; return new Response(JSON.stringify(url.endsWith("config")
      ? { api_version: 1, minimum_extension_version: "0.4.0", maintenance: false, features: { replacements: true, analytics: false } }
      : { found: true, replacement_id: 7, version, duration_ms: duration, gain_db: gain, mime_type: "audio/mpeg", expires_at: expires, audio_url: `/api/v1/audio/7?token=${"a".repeat(64)}&expires=${expires}` }), { headers: { "Content-Type": "application/json" } }); }
  });
  const engine = { resolveAsset: async id => {
    const answer = await broker({ type: "CELIKOM_API_RESOLVE", service: "yandex", trackId: id, forceRefresh: true }, { id: api.runtime.id, url: "https://music.yandex.ru/" });
    if (!answer.ok) throw Error(answer.error); return answer.asset;
  } };
  const environment = { setTimeout, clearTimeout, AbortController, fetch: async (url, options) => {
    downloads++; assert.equal(new URL(url).origin, "https://celikom.example");
    assert.equal(options.credentials, "omit"); assert.ok(!options.headers.Authorization);
    if (audioStatus !== 206) return new Response("", { status: audioStatus });
    const match = /^bytes=(\d+)-(\d+)$/.exec(options.headers.Range); assert.ok(match);
    const from = Number(match[1]), last = Math.min(Number(match[2]), bytes.length - 1);
    return new Response(bytes.subarray(from, last + 1), { status: 206, headers: { "Content-Type": "audio/mpeg", "Content-Range": `bytes ${from}-${last}/${bytes.length}`, ETag: '"' + createHash("sha256").update(bytes).digest("hex") + '-1"' } });
  } };
  const coordinator = root.__CELIKOM_NATIVE_DESKTOP_ADAPTER__.createDesktopPrefetch({ engine, environment, mp3DurationMs,
    publish: async item => published.push(item), revoke: async item => revoked.push(item), now: () => now });
  return { coordinator, published, revoked, engine, environment, stats: () => ({ calls, downloads }),
    change: values => { if ("allowed" in values) allowed = values.allowed; if ("loggedIn" in values) loggedIn = values.loggedIn;
      if ("duration" in values) duration = values.duration; if ("gain" in values) gain = values.gain; if ("version" in values) version = values.version; if ("audioStatus" in values) audioStatus = values.audioStatus; } };
}
test("existing broker, complete Range downloader and MP3 inspector publish only admitted bytes", async () => {
  const p = await pipeline(); await p.coordinator.configure(true);
  assert.ok(await p.coordinator.request({ id: "1001", durationMs: 8000 }));
  assert.equal(p.published.length, 1); const message = p.published[0];
  assert.deepEqual(Object.keys(message).sort(), ["blob", "durationMs", "expiresAt", "generation", "trackId"]);
  assert.deepEqual(Buffer.from(await message.blob.arrayBuffer()), bytes);
  assert.equal(JSON.stringify(message).includes("token"), false); assert.equal(p.stats().downloads, 1);
  assert.ok(await p.coordinator.admit("1001")); assert.equal(p.stats().calls, 4);
});
for (const condition of ["logged-out", "no-entitlement", "duration", "gain", "403"]) {
  test("prefetch fails closed for " + condition, async () => {
    const p = await pipeline(); await p.coordinator.configure(true);
    if (condition === "logged-out") p.change({ loggedIn: false });
    if (condition === "no-entitlement") p.change({ allowed: false });
    if (condition === "duration") p.change({ duration: 20000 });
    if (condition === "gain") p.change({ gain: 3 });
    if (condition === "403") p.change({ audioStatus: 403 });
    assert.equal(await p.coordinator.request({ id: "1001", durationMs: 8000 }), null);
    assert.equal(p.published.length, 0); assert.equal(p.stats().downloads, condition === "403" ? 1 : 0);
  });
}
for (const condition of ["access-loss", "new-version"]) {
  test("cached native bytes require fresh broker admission: " + condition, async () => {
    const p = await pipeline(); await p.coordinator.configure(true); await p.coordinator.request({ id: "1001", durationMs: 8000 });
    p.change(condition === "access-loss" ? { allowed: false } : { version: 2 });
    assert.equal(await p.coordinator.admit("1001"), null); assert.equal(p.coordinator.ready.size, 0);
    assert.ok(p.revoked.some(x => x.reason === "admission-denied" && x.trackId === "1001"));
  });
}
test("Stop cancels an in-flight download and never publishes it", async () => {
  const p = await pipeline(), entered = gate(), delayed = gate();
  p.environment.fetch = async (_url, options) => { entered.resolve(); assert.equal(options.signal.aborted, false); await delayed.promise; assert.equal(options.signal.aborted, true); throw Error("cancelled"); };
  await p.coordinator.configure(true); const task = p.coordinator.request({ id: "1001", durationMs: 8000 });
  await entered.promise; await p.coordinator.stop(); delayed.resolve(); await task;
  assert.equal(p.published.length, 0); assert.equal(p.coordinator.pending.size, 0);
});
test("late publication cleanup is scoped to its old session generation", async () => {
  const root = sandbox(); vm.runInContext(await readFile(new URL("prefetch-coordinator.js", moduleRoot), "utf8"), root);
  const published = gate(), complete = gate(), revoked = [];
  const coordinator = new root.__CELIKOM_NATIVE_PREFETCH__.PrefetchCoordinator({ now: Date.now,
    resolve: async () => ({ found: true, mimeType: "audio/mpeg", gainDb: 0, durationMs: 8000, expiresAt: Date.now() + 60000 }),
    download: async () => new Blob([bytes], { type: "audio/mpeg" }), inspectDuration: () => 8000,
    publish: async () => { published.resolve(); await complete.promise; }, revoke: async item => revoked.push(item) });
  await coordinator.configure(true); const oldGeneration = coordinator.generation;
  const task = coordinator.request({ id: "1001", durationMs: 8000 }); await published.promise;
  await coordinator.stop(); await coordinator.configure(true); complete.resolve(); await task;
  assert.ok(revoked.some(x => x.reason === "late-publish" && x.generation === oldGeneration));
  assert.ok(!revoked.some(x => x.reason === "late-publish" && x.generation === coordinator.generation));
});
