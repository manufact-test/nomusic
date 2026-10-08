import assert from "node:assert/strict";
import test from "node:test";

await import("../dist/unpacked/player/core.js");
await import("../dist/unpacked/adapters/yandex-music-adapter.js");

const { createAdapter } = globalThis.__CELIKOM_YANDEX_ADAPTER_V1__;

class FakeMedia extends EventTarget {
  constructor() {
    super();
    this.tagName = "AUDIO";
    this.dataset = {};
    this.id = "";
    this.className = "";
    this.parentElement = null;
    this.isConnected = false;
    this.paused = false;
    this.ended = false;
    this.seeking = false;
    this.currentTime = 12;
    this.duration = 193.283;
    this.playbackRate = 1;
    this.volume = 1;
    this.muted = false;
    this.readyState = 4;
    this.networkState = 2;
    this.currentSrc = "https://strm-rad-25.strm.yandex.net/track";
    this.src = this.currentSrc;
    this.listenerBalance = 0;
  }

  addEventListener(type, listener, options) {
    this.listenerBalance += 1;
    return super.addEventListener(type, listener, options);
  }

  removeEventListener(type, listener, options) {
    this.listenerBalance -= 1;
    return super.removeEventListener(type, listener, options);
  }

  play() {
    this.paused = false;
    return Promise.resolve();
  }

  pause() {
    this.paused = true;
  }

  load() {}
  closest() { return null; }
}

function createEnvironment(media) {
  const windowListeners = new Map();
  const intervals = new Set();
  let timerId = 0;
  const document = {
    title: "Smells Like Teen Spirit — ERCODES, SMOLA",
    hidden: false,
    querySelector: () => null,
    querySelectorAll(selector) {
      if (selector === "audio,video") return [media];
      return [];
    }
  };
  const environment = {
    window: null,
    document,
    HTMLMediaElement: FakeMedia,
    MutationObserver: null,
    XMLHttpRequest: null,
    navigator: {
      mediaSession: {
        metadata: {
          title: "Smells Like Teen Spirit",
          artist: "ERCODES, SMOLA",
          album: "Smells Like Teen Spirit",
          artwork: [{ src: "https://avatars.yandex.net/get-music-content/20322863/810d39cc.a.43775051-1/400x400" }]
        }
      }
    },
    location: {
      href: "https://music.yandex.ru/landing/main",
      origin: "https://music.yandex.ru",
      pathname: "/landing/main"
    },
    history: {
      pushState() {},
      replaceState() {}
    },
    __STATE_PATCHES__: [[{
      id: "155343370",
      title: "Smells Like Teen Spirit",
      artists: [{ name: "ERCODES" }, { name: "SMOLA" }],
      albums: [{ id: "43775051", title: "Smells Like Teen Spirit", coverUri: "avatars.yandex.net/get-music-content/20322863/810d39cc.a.43775051-1/%%" }],
      durationMs: 193283
    }]],
    addEventListener(type, listener) {
      if (!windowListeners.has(type)) windowListeners.set(type, new Set());
      windowListeners.get(type).add(listener);
    },
    removeEventListener(type, listener) {
      windowListeners.get(type)?.delete(listener);
    },
    getComputedStyle: () => ({ display: "block", visibility: "visible" }),
    setInterval(callback) {
      const id = ++timerId;
      intervals.add(id);
      return id;
    },
    clearInterval(id) { intervals.delete(id); },
    setTimeout: globalThis.setTimeout.bind(globalThis),
    clearTimeout: globalThis.clearTimeout.bind(globalThis),
    queueMicrotask: globalThis.queueMicrotask.bind(globalThis)
  };
  environment.window = environment;
  return { environment, intervals, windowListeners };
}

test("YandexMusicAdapter mounts idempotently, follows SPA track changes and fully unmounts", async () => {
  const media = new FakeMedia();
  const originalPlay = FakeMedia.prototype.play;
  const originalPushState = () => {};
  const { environment, intervals, windowListeners } = createEnvironment(media);
  environment.history.pushState = originalPushState;
  const adapter = createAdapter(environment);
  const snapshots = [];
  const events = [];
  const sink = {
    onSnapshot: (snapshot) => snapshots.push(snapshot),
    onPlayerEvent: (event) => events.push(event)
  };

  adapter.mount(sink);
  adapter.mount(sink);
  assert.equal(adapter.mounted, true);
  assert.equal(intervals.size, 1);
  assert.equal(windowListeners.get("popstate").size, 1);
  assert.equal(media.listenerBalance, 13);
  assert.notEqual(FakeMedia.prototype.play, originalPlay);
  assert.notEqual(environment.history.pushState, originalPushState);
  assert.equal(snapshots.at(-1).track.id, "155343370");
  assert.equal(snapshots.at(-1).player.mediaId, "media-1");

  media.dispatchEvent(new Event("play"));
  assert.equal(events.at(-1).type, "PLAY");
  assert.equal(events.at(-1).trackId, "155343370");

  Object.assign(environment.navigator.mediaSession.metadata, {
    title: "SWERVIN",
    artist: "OISEAU & PAPILLON, onna badvibes",
    album: "SWERVIN",
    artwork: [{ src: "https://avatars.yandex.net/get-music-content/20622967/c3b9f96b.a.44117847-1/400x400" }]
  });
  media.duration = 193.515;
  environment.__STATE_PATCHES__.push([{
    id: "156177669",
    title: "SWERVIN",
    artists: [{ name: "OISEAU & PAPILLON" }, { name: "onna badvibes" }],
    albums: [{ id: "44117847", title: "SWERVIN", coverUri: "avatars.yandex.net/get-music-content/20622967/c3b9f96b.a.44117847-1/%%" }],
    durationMs: 193515
  }]);
  environment.history.pushState({}, "", "/landing/main");
  await Promise.resolve();
  const trackChanged = events.findLast((event) => event.type === "TRACK_CHANGED");
  assert.equal(trackChanged.previousTrackId, "155343370");
  assert.equal(trackChanged.trackId, "156177669");

  adapter.unmount();
  adapter.unmount();
  assert.equal(adapter.mounted, false);
  assert.equal(intervals.size, 0);
  assert.equal(windowListeners.get("popstate").size, 0);
  assert.equal(media.listenerBalance, 0);
  assert.equal(FakeMedia.prototype.play, originalPlay);
  assert.equal(environment.history.pushState, originalPushState);

  adapter.mount(sink);
  assert.equal(media.listenerBalance, 13);
  media.dispatchEvent(new Event("pause"));
  assert.equal(events.at(-1).type, "PAUSE");
  adapter.unmount();
  assert.equal(media.listenerBalance, 0);
});
