import assert from "node:assert/strict";
import test from "node:test";

await import("../dist/unpacked/player/core.js");
await import("../dist/unpacked/player/player-bridge.js");

const core = globalThis.__CELIKOM_PLAYER_CORE_V1__;
const { PlayerBridge } = globalThis.__CELIKOM_PLAYER_BRIDGE_V1__;

class FakeWindow {
  constructor() {
    this.listeners = new Set();
    this.posts = [];
    this.intervals = new Set();
    this.timeouts = new Map();
    this.nextTimer = 0;
  }

  addEventListener(type, listener) {
    if (type === "message") this.listeners.add(listener);
  }

  removeEventListener(type, listener) {
    if (type === "message") this.listeners.delete(listener);
  }

  postMessage(message) {
    this.posts.push(message);
  }

  setInterval(callback) {
    const id = ++this.nextTimer;
    this.intervals.add(id);
    return id;
  }

  clearInterval(id) { this.intervals.delete(id); }

  setTimeout(callback) {
    const id = ++this.nextTimer;
    this.timeouts.set(id, callback);
    return id;
  }

  clearTimeout(id) { this.timeouts.delete(id); }

  dispatch(message, source = this) {
    for (const listener of this.listeners) listener({ source, data: message });
  }
}

function message(bridge, type, sequence, payload = {}, overrides = {}) {
  return {
    channel: core.CHANNEL,
    protocolVersion: core.PROTOCOL_VERSION,
    direction: "from-main",
    sessionId: bridge.sessionId,
    sequence,
    type,
    payload,
    ...overrides
  };
}

test("PlayerBridge starts once and ignores stale or foreign events", () => {
  const target = new FakeWindow();
  const bridge = new PlayerBridge(target, { sessionId: "session-123", heartbeatIntervalMs: 1000 });
  const received = [];
  bridge.on("PLAYER_EVENT", (event) => received.push(event));
  bridge.start();
  bridge.start();

  assert.equal(target.listeners.size, 1);
  assert.equal(target.intervals.size, 1);
  assert.equal(target.posts.filter((post) => post.type === "INIT").length, 1);

  target.dispatch(message(bridge, "READY", 1));
  target.dispatch(message(bridge, "PLAYER_EVENT", 3, { type: "PLAY" }));
  target.dispatch(message(bridge, "PLAYER_EVENT", 2, { type: "PAUSE" }));
  target.dispatch(message(bridge, "PLAYER_EVENT", 4, { type: "ENDED" }, { sessionId: "foreign-session" }));
  target.dispatch(message(bridge, "PLAYER_EVENT", 5, { type: "SEEK" }));

  assert.equal(bridge.ready, true);
  assert.deepEqual(received.map((event) => event.type), ["PLAY", "SEEK"]);
  target.dispatch(message(bridge, "BRIDGE_TIMEOUT", 6, { elapsedMs: 13000 }));
  assert.equal(bridge.ready, false);
  assert.equal(target.posts.filter((post) => post.type === "INIT").length, 2);
  target.dispatch(message(bridge, "READY", 1));
  assert.equal(bridge.ready, true);
  bridge.destroy();
  bridge.destroy();
  assert.equal(target.listeners.size, 0);
  assert.equal(target.intervals.size, 0);
  assert.equal(target.posts.at(-1).type, "SHUTDOWN");
});

test("PlayerBridge resolves matching requests and rejects unknown sessions", async () => {
  const target = new FakeWindow();
  const bridge = new PlayerBridge(target, { sessionId: "session-456" }).start();
  const pending = bridge.getSnapshot();
  const request = target.posts.find((post) => post.type === "REQUEST");
  target.dispatch(message(bridge, "RESPONSE", 1, { ok: true, result: { track: { id: "1944599" } } }, {
    requestId: request.requestId
  }));
  assert.equal((await pending).track.id, "1944599");
  assert.equal(target.timeouts.size, 0);
  bridge.destroy();
});
