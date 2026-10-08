import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";
import { createControllerBootstrap } from "../dist/unpacked/background/controller-bootstrap.js";
import { contentScriptGroups } from "../scripts/content-script-groups.mjs";

const unpacked = new URL("../dist/unpacked/", import.meta.url);
const manifest = JSON.parse(await readFile(new URL("manifest.json", unpacked), "utf8"));
const scriptFiles = [...new Set([...manifest.content_scripts.flatMap((entry) => entry.js), ...contentScriptGroups.flatMap((group) => group.modules)])];
const sources = new Map(await Promise.all(scriptFiles.map(async (file) => [file, await readFile(new URL(file, unpacked), "utf8")])));

function browserFixture() {
  const runtimeListeners = new Set();
  const storageListeners = new Set();
  const errors = [];
  const worlds = new Map();
  const eventListeners = new Map();
  let timerId = 0;
  const timers = new Map();
  const elements = new Set();
  const stored = { enabled: true, testTrackId: "" };
  const document = {
    documentElement: { dataset: {}, append: (element) => { elements.add(element); element.isConnected = true; } },
    hidden: false,
    title: "Папиросы — Зануда",
    querySelector: () => null,
    querySelectorAll: (selector) => selector.includes("data-celikom-replacement")
      ? [...elements].filter((element) => element.dataset.celikomReplacement === "true") : [...elements],
    createElement: () => new FakeMedia(),
    addEventListener() {},
    removeEventListener() {}
  };
  class FakeMedia extends EventTarget {
    constructor() {
      super(); Object.assign(this, { physicalMuted: false, physicalVolume: 0.012, paused: true, ended: false, seeking: false, readyState: 4, duration: 201, currentTime: 9, playbackRate: 1, tagName: "AUDIO", src: "https://strm-fra-03.strm.yandex.net/test", dataset: {}, isConnected: false });
    }
    get volume() { return this.physicalVolume; }
    set volume(value) { if (this.physicalVolume === value) return; this.physicalVolume = value; queueMicrotask(() => this.dispatchEvent(new Event("volumechange"))); }
    get muted() { return this.physicalMuted; }
    set muted(value) { if (this.physicalMuted === Boolean(value)) return; this.physicalMuted = Boolean(value); queueMicrotask(() => this.dispatchEvent(new Event("volumechange"))); }
    play() { this.paused = false; queueMicrotask(() => this.dispatchEvent(new Event("play"))); return Promise.resolve(); }
    pause() { this.paused = true; queueMicrotask(() => this.dispatchEvent(new Event("pause"))); }
    load() {}
    removeAttribute(name) { if (name === "src") this.src = ""; }
    remove() { elements.delete(this); this.isConnected = false; }
  }
  const runtime = {
    sendMessage: async () => ({ ok: true, configured: false, asset: { found: false, retryAfterMs: 60000 } }),
    getManifest: () => manifest,
    getURL: (file) => `chrome-extension://test/${file}`,
    onMessage: {
      addListener: (callback) => runtimeListeners.add(callback),
      removeListener: (callback) => runtimeListeners.delete(callback)
    }
  };
  const chrome = {
    runtime,
    storage: {
      local: { get: async () => ({ ...stored }) },
      onChanged: {
        addListener: (callback) => storageListeners.add(callback),
        removeListener: (callback) => storageListeners.delete(callback)
      }
    }
  };

  for (const name of ["MAIN", "ISOLATED"]) {
    const listeners = new Map();
    eventListeners.set(name, listeners);
    const context = vm.createContext({
      URL,
      Event,
      AbortController,
      fetch: async () => ({ ok: true, blob: async () => new Blob(["synthetic fixture"]) }),
      console,
      crypto: globalThis.crypto,
      chrome: name === "ISOLATED" ? chrome : undefined,
      document,
      HTMLMediaElement: FakeMedia,
      navigator: {
        mediaSession: { metadata: { title: "Папиросы", artist: "Зануда", album: "Папиросы", artwork: [] } }
      },
      location: new URL("https://music.yandex.ru/album/192577/track/1944599"),
      history: { pushState() {}, replaceState() {} },
      __STATE_PATCHES__: [[{
        id: "1944599", title: "Папиросы", durationMs: 201000,
        artists: [{ name: "Зануда" }], albums: [{ id: "192577", title: "Папиросы" }]
      }]],
      queueMicrotask,
      setTimeout: (callback, ms) => setTimeout(callback, ms),
      clearTimeout,
      setInterval: (callback) => {
        const id = ++timerId;
        timers.set(id, callback);
        return id;
      },
      clearInterval: (id) => timers.delete(id),
      addEventListener: (type, callback) => {
        if (!listeners.has(type)) listeners.set(type, new Set());
        listeners.get(type).add(callback);
      },
      removeEventListener: (type, callback) => listeners.get(type)?.delete(callback),
      postMessage: (message) => {
        // postMessage is asynchronous; each world sees its own WindowProxy as source.
        queueMicrotask(() => {
          for (const [targetName, target] of worlds) {
            const source = vm.runInContext("globalThis", target);
            for (const listener of eventListeners.get(targetName).get("message") || []) {
              try {
                listener({ source, data: structuredClone(message) });
              } catch (error) {
                errors.push(error);
              }
            }
          }
        });
      }
    });
    worlds.set(name, context);
  }

  const api = {
    runtime,
    tabs: {
      get: async () => ({ id: 42, url: "https://music.yandex.ru/album/192577/track/1944599" }),
      sendMessage: async (_tabId, message) => {
        for (const listener of runtimeListeners) {
          let response;
          listener(message, {}, (value) => { response = value; });
          if (response) return response;
        }
        throw new Error("Receiving end does not exist");
      }
    },
    scripting: {
      executeScript: async ({ files, world }) => {
        for (const file of files) vm.runInContext(sources.get(file), worlds.get(world), { filename: file });
      }
    }
  };
  const changeStorage = (changes) => {
    for (const [key, change] of Object.entries(changes)) stored[key] = change.newValue;
    for (const listener of storageListeners) listener(changes, "local");
  };
  return { api, worlds, runtimeListeners, storageListeners, errors, timers, changeStorage, elements };
}

test("packaged MAIN + ISOLATED scripts bootstrap an already-open tab end to end", async () => {
  const fixture = browserFixture();
  const bootstrap = createControllerBootstrap(fixture.api, { wait: () => new Promise((resolve) => setTimeout(resolve, 5)) });
  const result = await bootstrap.ensure(42);
  assert.equal(result.error, null, result.detail);
  assert.equal(result.status.bridge.ready, true);
  assert.equal(result.status.bridge.healthy, true);
  assert.equal(result.status.track.id, "1944599");
  assert.equal(fixture.runtimeListeners.size, 1);
  assert.deepEqual(fixture.errors.map((error) => error.message), []);

  // Repeated packaged-file injection must not throw on immutable globals or
  // duplicate controller/listener/adapter state.
  for (const group of manifest.content_scripts) {
    await fixture.api.scripting.executeScript({ files: group.js, world: group.world });
  }
  await new Promise((resolve) => setTimeout(resolve, 5));
  assert.equal(fixture.runtimeListeners.size, 1);
  assert.equal(fixture.storageListeners.size, 1);
  assert.deepEqual(fixture.errors.map((error) => error.message), []);
  vm.runInContext("globalThis.__CELIKOM_CONTENT_CONTROLLER_V2__.destroy()", fixture.worlds.get("ISOLATED"));
  await new Promise((resolve) => setTimeout(resolve, 5));
  vm.runInContext("globalThis.__CELIKOM_MAIN_BRIDGE_V1__.destroy()", fixture.worlds.get("MAIN"));
  assert.equal(fixture.timers.size, 0);
});

test("playback registration before core availability does not poison subsequent packaged startup", async () => {
  for (const early of [["player/replacement-controller.js"], [
    "player/sync-engine.js", "player/replacement-player.js", "player/fail-open-controller.js", "player/replacement-controller.js"
  ]]) {
    const f = browserFixture();
    await f.api.scripting.executeScript({ world: "ISOLATED", files: early });
    const result = await createControllerBootstrap(f.api, { wait: () => new Promise((resolve) => setTimeout(resolve, 5)) }).ensure(42);
    assert.equal(result.status?.startupError, null, JSON.stringify(result));
    assert.equal(result.error, null);
    assert.equal(result.status.bridge.healthy, true);
    assert.equal(result.status.track.id, "1944599");
    for (const group of manifest.content_scripts) await f.api.scripting.executeScript({ world: group.world, files: group.js });
    await new Promise((resolve) => setTimeout(resolve, 5));
    assert.equal(f.runtimeListeners.size, 1); assert.equal(f.storageListeners.size, 1);
    assert.deepEqual(f.errors.map((error) => error.message), []);
    vm.runInContext("__CELIKOM_CONTENT_CONTROLLER_V2__.destroy()", f.worlds.get("ISOLATED"));
    await new Promise((resolve) => setTimeout(resolve, 5));
    vm.runInContext("__CELIKOM_MAIN_BRIDGE_V1__.destroy()", f.worlds.get("MAIN"));
    assert.equal(f.timers.size, 0);
  }
});

test("packaged playback guards exact master, follows controls, bypasses and independently restores on lost heartbeat", async () => {
  const f = browserFixture();
  const bootstrap = createControllerBootstrap(f.api, { wait: () => new Promise((resolve) => setTimeout(resolve, 5)) });
  await bootstrap.ensure(42);
  const main = f.worlds.get("MAIN"); const isolated = f.worlds.get("ISOLATED");
  vm.runInContext("globalThis.original = new HTMLMediaElement(); original.play();", main);
  await new Promise((resolve) => setTimeout(resolve, 5));
  f.changeStorage({ testTrackId: { newValue: "1944599" } });
  await new Promise((resolve) => setTimeout(resolve, 5));
  let response = await f.api.tabs.sendMessage(42, { type: "CELIKOM_CONTROLLER_STATUS_GET" });
  assert.equal(response.status.phase, "REPLACEMENT_ACTIVE", JSON.stringify(response.status));
  assert.equal(vm.runInContext("original.physicalMuted", main), true);
  assert.equal(response.status.player.muted, false);
  assert.equal(response.status.guardActive, true);
  assert.equal(f.elements.size, 1, "one CELIKOM media instance; master is detached");
  const replacement = [...f.elements][0]; assert.equal(replacement.paused, false);
  vm.runInContext("original.volume = 0.2; original.pause();", main);
  await new Promise((resolve) => setTimeout(resolve, 5));
  assert.equal(replacement.paused, true); assert.equal(replacement.volume, 0.2);
  await f.api.tabs.sendMessage(42, { type: "CELIKOM_RESTORE_ORIGINAL" });
  await new Promise((resolve) => setTimeout(resolve, 5));
  assert.equal(vm.runInContext("original.physicalMuted", main), false);
  assert.equal(vm.runInContext("original.volume", main), 0.2);
  assert.equal(f.elements.size, 0);
  await assert.rejects(vm.runInContext("__CELIKOM_CONTENT_CONTROLLER_V2__.bridge.request('GUARD_ENGAGE', { token: __CELIKOM_CONTENT_CONTROLLER_V2__.bridge.sessionId + ':1', trackId: '1944599', mediaId: 'media-1' })", isolated), /cancelled guard lease/);
  vm.runInContext("original.play();", main); await new Promise((resolve) => setTimeout(resolve, 5));
  assert.equal(f.elements.size, 0, "same-track state must not rearm manual bypass");
  await f.api.tabs.sendMessage(42, { type: "CELIKOM_REPLACEMENT_RETRY" });
  await new Promise((resolve) => setTimeout(resolve, 5));
  assert.equal(vm.runInContext("original.physicalMuted", main), true);
  // Simulate a dead extension context without running its cleanup. MAIN watchdog
  // must stop replacement and restore original using only shared DOM + native state.
  vm.runInContext("Date = { now: () => 9999999999999 };", main);
  for (const callback of [...f.timers.values()]) callback();
  await new Promise((resolve) => setTimeout(resolve, 5));
  assert.equal(vm.runInContext("original.physicalMuted", main), false);
  assert.equal([...f.elements][0]?.paused ?? true, true);
  assert.equal([...f.elements][0]?.muted ?? true, true);
  vm.runInContext("globalThis.__CELIKOM_CONTENT_CONTROLLER_V2__.destroy()", isolated);
  await new Promise((resolve) => setTimeout(resolve, 5));
  vm.runInContext("globalThis.__CELIKOM_MAIN_BRIDGE_V1__.destroy()", main);
  assert.deepEqual(f.errors.map((error) => error.message), []);
});

test("controller diagnostics still respond when async startup fails", async () => {
  const fixture = browserFixture();
  vm.runInContext("chrome.storage.local.get = async () => { throw new Error('storage unavailable'); }", fixture.worlds.get("ISOLATED"));
  const group = manifest.content_scripts.find((entry) => entry.world === "ISOLATED");
  await fixture.api.scripting.executeScript({ files: group.js, world: "ISOLATED" });
  await new Promise((resolve) => setTimeout(resolve, 5));
  const response = await fixture.api.tabs.sendMessage(42, { type: "CELIKOM_CONTROLLER_STATUS_GET" });
  assert.equal(response.ok, true);
  assert.equal(response.status.startupError, "storage unavailable");
  assert.equal(response.status.bridge.ready, false);
  const before = response.status.recentLog.length;
  for (let i = 0; i < 5; i++) await fixture.api.scripting.executeScript({ files: group.js, world: "ISOLATED" });
  await new Promise((resolve) => setTimeout(resolve, 5));
  const after = await fixture.api.tabs.sendMessage(42, { type: "CELIKOM_CONTROLLER_STATUS_GET" });
  assert.equal(after.status.recentLog.length, before, "reinjection must not flood a failed startup with settings errors");
  vm.runInContext("globalThis.__CELIKOM_CONTENT_CONTROLLER_V2__.destroy()", fixture.worlds.get("ISOLATED"));
});

test("packaged playback keeps one lease through utility events and metadata-only seek, then fails open on stream rebinding", async () => {
  const f = browserFixture();
  const main = f.worlds.get("MAIN"); const isolated = f.worlds.get("ISOLATED");
  await createControllerBootstrap(f.api, { wait: () => new Promise((resolve) => setTimeout(resolve, 5)) }).ensure(42);
  try {
    vm.runInContext("globalThis.original = new HTMLMediaElement(); original.play();", main);
    await new Promise((resolve) => setTimeout(resolve, 5));
    f.changeStorage({ testTrackId: { newValue: "1944599" } });
    await new Promise((resolve) => setTimeout(resolve, 5));
    const status = async () => (await f.api.tabs.sendMessage(42, { type: "CELIKOM_CONTROLLER_STATUS_GET" })).status;
    const initial = await status();
    assert.equal(initial.phase, "REPLACEMENT_ACTIVE", JSON.stringify(initial));
    const replacement = [...f.elements][0];
    vm.runInContext("original.pause(); globalThis.utility = new HTMLMediaElement(); utility.src = 'data:audio/wav;base64,fixture'; utility.duration = 0.015; utility.currentTime = 0; utility.play(); utility.pause();", main);
    await new Promise((resolve) => setTimeout(resolve, 5));
    let next = await status();
    assert.equal(next.active?.generation, initial.active.generation, JSON.stringify(next));
    assert.equal(next.player.mediaId, initial.player.mediaId);
    const fresh = await vm.runInContext("__CELIKOM_CONTENT_CONTROLLER_V2__.bridge.getSnapshot()", isolated);
    assert.equal(fresh.player.mediaId, initial.player.mediaId);
    // Detached, paused utility media may already have been pruned.
    assert.ok(fresh.mediaCandidates.filter(c => c.duration === 0.015).every(c => c.rejectedReason === "utility-media"));
    assert.equal(replacement.paused, true); assert.equal(vm.runInContext("original.physicalMuted", main), true);
    vm.runInContext("original.readyState = 1; original.seeking = true; original.currentTime = 80; original.dispatchEvent(new Event('seeking'));", main);
    await new Promise((resolve) => setTimeout(resolve, 5));
    next = await status();
    assert.equal(next.active?.generation, initial.active.generation, JSON.stringify(next));
    assert.equal(replacement.paused, true);
    vm.runInContext("original.seeking = false; original.readyState = 4; original.dispatchEvent(new Event('seeked')); original.play();", main);
    await new Promise((resolve) => setTimeout(resolve, 5));
    next = await status();
    assert.equal(next.active?.generation, initial.active.generation, JSON.stringify(next));
    assert.equal(next.playback.activationCount, 1); assert.equal(next.playback.restoreCount, 0);
    assert.equal(replacement.paused, false); assert.equal(f.elements.size, 1);

    // Old metadata may outlive native stream rebinding: restore immediately and
    // hold this Track ID until a new identity or explicit retry is observed.
    vm.runInContext("original.src = 'https://strm-fra-04.strm.yandex.net/new?private_signature=secret'; original.dispatchEvent(new Event('loadedmetadata'));", main);
    await new Promise((resolve) => setTimeout(resolve, 5));
    next = await status();
    assert.equal(next.active, null, JSON.stringify(next));
    assert.equal(next.playback.restoreCount, 1);
    assert.equal(next.playback.lastRestore.detail.reason, "media-source-changed");
    assert.equal(vm.runInContext("original.physicalMuted", main), false);
    assert.equal(replacement.paused, true); assert.equal(f.elements.size, 0);
    for (const callback of [...f.timers.values()]) callback();
    await new Promise((resolve) => setTimeout(resolve, 5));
    next = await status();
    assert.equal(next.active, null); assert.equal(next.playback.activationCount, 1);
    assert.equal(JSON.stringify(next).includes("private_signature"), false);
    assert.equal(JSON.stringify(next).includes("secret"), false);
    assert.deepEqual(f.errors.map(error => error.message), []);
  } finally {
    vm.runInContext("__CELIKOM_CONTENT_CONTROLLER_V2__.destroy()", isolated);
    await new Promise((resolve) => setTimeout(resolve, 5));
    vm.runInContext("__CELIKOM_MAIN_BRIDGE_V1__.destroy()", main);
  }
});
