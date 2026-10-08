import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { createControllerBootstrap, isSupportedPage } from "../dist/unpacked/background/controller-bootstrap.js";

const manifest = JSON.parse(await readFile(new URL("../dist/unpacked/manifest.json", import.meta.url), "utf8"));
const connected = { phase: "READY", track: { id: "1944599" }, bridge: { ready: true, healthy: true } };

function fixture(initial = null) {
  const state = { status: initial, injections: [], reads: 0, denied: false, starts: true };
  const api = {
    runtime: { getManifest: () => manifest },
    tabs: {
      get: async () => ({ id: 42, url: "https://music.yandex.ru/landing/main" }),
      query: async () => [{ id: 42, url: "https://music.yandex.ru/landing/main" }],
      sendMessage: async () => {
        state.reads += 1;
        if (!state.status) throw new Error("Could not establish connection. Receiving end does not exist.");
        return { ok: true, status: state.status };
      }
    },
    scripting: {
      executeScript: async (injection) => {
        if (state.denied) throw new Error("Cannot access contents of the page.");
        state.injections.push(injection);
        if (injection.world === "ISOLATED" && state.starts) state.status = connected;
      }
    }
  };
  return { state, api };
}

test("bootstrap recovers a previously open tab with no content-script receiver", async () => {
  const { state, api } = fixture();
  const bootstrap = createControllerBootstrap(api, { wait: async () => undefined });
  const result = await bootstrap.ensure(42);
  assert.equal(result.error, null);
  assert.equal(result.recovered, true);
  assert.equal(result.status.track.id, "1944599");
  assert.deepEqual(state.injections.map((call) => call.world), ["MAIN", "ISOLATED"]);
  for (const injection of state.injections) {
    assert.deepEqual(injection.target, { tabId: 42 });
    assert.deepEqual(injection.files, manifest.content_scripts.find((group) => group.world === injection.world).js);
  }
});

test("healthy controllers are not reinjected", async () => {
  const { state, api } = fixture(connected);
  const result = await createControllerBootstrap(api).ensure(42);
  assert.equal(result.recovered, false);
  assert.equal(state.injections.length, 0);
});

test("an upgraded extension reports stale page globals instead of pretending the old build is current", async () => {
  for (const old of [{ stage: 2 }, { buildVersion: "0.2.1" }, { bridge: { ...connected.bridge, bridgeVersion: "0.2.1" } }]) {
    const { state, api } = fixture({ ...connected, ...old });
    const result = await createControllerBootstrap(api).ensure(42);
    assert.equal(result.error, "stale-page-controller");
    assert.match(result.detail, /Обновите вкладку/);
    assert.equal(state.injections.length, 0);
  }
});

test("concurrent popup status/start requests share one injection", async () => {
  const { state, api } = fixture();
  const bootstrap = createControllerBootstrap(api, { wait: async () => undefined });
  const [first, second] = await Promise.all([bootstrap.ensure(42), bootstrap.ensure(42)]);
  assert.equal(first, second);
  assert.equal(state.injections.length, 2);
});

test("script permission denial is visible and is not retried via another access path", async () => {
  const { state, api } = fixture();
  state.denied = true;
  const bootstrap = createControllerBootstrap(api);
  const result = await bootstrap.ensure(42);
  assert.equal(result.error, "script-injection-failed");
  assert.match(result.detail, /Cannot access contents/);
  assert.equal(state.injections.length, 0);
  const reads = state.reads;
  await bootstrap.ensure(42);
  assert.equal(state.reads, reads);
  state.denied = false;
  assert.equal((await bootstrap.ensure(42, true)).error, null);
  assert.equal(state.injections.length, 2);
});

test("missing controller produces bounded, actionable diagnostics instead of permanent CONNECTING", async () => {
  const { state, api } = fixture();
  state.starts = false;
  const result = await createControllerBootstrap(api, { attempts: 3, wait: async () => undefined }).ensure(42);
  assert.equal(result.error, "controller-start-timeout");
  assert.match(result.detail, /Chrome/);
  assert.equal(state.reads, 5);
});

test("a failed MAIN handshake and startup errors have distinct diagnostic codes", async () => {
  const { state, api } = fixture({ bridge: { ready: false, healthy: false } });
  state.starts = false;
  const bootstrap = createControllerBootstrap(api, { attempts: 1, wait: async () => undefined });
  assert.equal((await bootstrap.ensure(42)).error, "bridge-connect-timeout");
  state.status.startupError = "Storage initialization failed";
  assert.equal((await bootstrap.ensure(42)).error, "controller-start-failed");
});

test("polling a failed controller does not reinject or repeatedly wake it", async () => {
  const { state, api } = fixture({ stage: 3, buildVersion: manifest.version, startupError: "Cannot read properties of undefined (reading 'normalizeTrackId')", bridge: { ready: false, healthy: false } });
  const bootstrap = createControllerBootstrap(api);
  for (let i = 0; i < 10; i++) {
    const result = await bootstrap.ensure(42);
    assert.equal(result.error, "controller-start-failed"); assert.match(result.detail, /Обновите вкладку/);
  }
  assert.equal(state.injections.length, 0);
  assert.equal((await bootstrap.ensure(42, true)).error, "controller-start-failed");
  assert.equal(state.injections.length, 0, "Retry cannot repair already registered broken globals");
  // A navigation destroys the page context and gives the ordinary bootstrap a
  // fresh receiver. No permanent failure cache may block recovery after reload.
  state.status = null;
  assert.equal((await bootstrap.ensure(42)).error, null);
  assert.equal(state.injections.length, 2);
});

test("bootstrap operates only within existing Yandex host permissions", async () => {
  for (const url of ["https://music.yandex.ru/landing/main", "https://music.yandex.ru/album/1/track/2"]) {
    assert.equal(isSupportedPage(url), true);
  }
  for (const url of ["https://example.com/", "https://music.yandex.ru.example.com/", "http://music.yandex.ru/", ""]) {
    assert.equal(isSupportedPage(url), false);
  }
  const { state, api } = fixture();
  api.tabs.get = async () => ({ id: 42, url: "https://example.com/" });
  assert.equal((await createControllerBootstrap(api).ensure(42)).error, "unsupported-page");
  assert.equal(state.injections.length, 0);
});
