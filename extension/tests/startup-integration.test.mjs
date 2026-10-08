import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";
import { createControllerBootstrap } from "../dist/unpacked/background/controller-bootstrap.js";

const unpacked = new URL("../dist/unpacked/", import.meta.url);
const manifest = JSON.parse(await readFile(new URL("manifest.json", unpacked), "utf8"));
const scriptFiles = [...new Set(manifest.content_scripts.flatMap((entry) => entry.js))];
const sources = new Map(await Promise.all(scriptFiles.map(async (file) => [file, await readFile(new URL(file, unpacked), "utf8")])));

function browserFixture() {
  const runtimeListeners = new Set();
  const storageListeners = new Set();
  const errors = [];
  const worlds = new Map();
  const eventListeners = new Map();
  let timerId = 0;
  const timers = new Map();
  const document = {
    documentElement: { dataset: {} },
    hidden: false,
    title: "Папиросы — Зануда",
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener() {},
    removeEventListener() {}
  };
  class FakeMedia {}
  FakeMedia.prototype.play = function () {};
  FakeMedia.prototype.pause = function () {};
  FakeMedia.prototype.load = function () {};
  const runtime = {
    getManifest: () => manifest,
    onMessage: {
      addListener: (callback) => runtimeListeners.add(callback),
      removeListener: (callback) => runtimeListeners.delete(callback)
    }
  };
  const chrome = {
    runtime,
    storage: {
      local: { get: async () => ({ enabled: true }) },
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
  return { api, worlds, runtimeListeners, storageListeners, errors, timers };
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
  vm.runInContext("globalThis.__CELIKOM_CONTENT_CONTROLLER_V2__.destroy()", fixture.worlds.get("ISOLATED"));
});
