import test from "node:test";
import assert from "node:assert/strict";
import { createLiveMediaProviderHook } from "./live-media-provider-hook.mjs";

test("W188 discovers the live player mediaProvider and adapts id to W22 trackId", () => {
  class Provider {
    getMediaSource() { return Promise.resolve("source"); }
    getFileInfo(params) { return params.trackId ?? null; }
  }
  class Player {
    constructor() {
      this.currentMediaPlayer = { mediaProvider: new Provider() };
      this.firstMediaPlayer = this.currentMediaPlayer;
      this.secondMediaPlayer = this.currentMediaPlayer;
      this.snapshot = { queueState: { currentEntity: { value: {
        entity: { data: { meta: { id: "144530503" } } }
      } } } };
    }
    get state() { return this.snapshot; }
    reloadEntity() {}
  }
  const originalState = Object.getOwnPropertyDescriptor(Player.prototype, "state");
  const originalGetFileInfo = Provider.prototype.getFileInfo;
  const requireFn = id => id === 7123 ? { VE: Player } : null;
  requireFn.m = { 7123() {} };
  const events = [];
  const hook = createLiveMediaProviderHook({ onEvent: code => events.push(code) });

  assert.equal(hook.attach(requireFn), true);
  const player = new Player();
  void player.state;
  const proto = hook.findProviderPrototype();
  assert.equal(proto, Provider.prototype);

  // Simulate W22's already-attached wrapper: it only accepts params.trackId.
  proto.getFileInfo = function(params) { return params.trackId ?? null; };
  assert.equal(hook.normalizeAdapterArguments(proto), true);
  const provider = player.currentMediaPlayer.mediaProvider;
  assert.equal(provider.getFileInfo({ id: "144530503" }), "144530503");
  assert.equal(provider.getFileInfo({ entity: { data: { meta: { id: "144530503" } } } }),
    "144530503");
  assert.ok(events.includes("LIVE_PLAYER_STATE_OBSERVER_READY"));
  assert.ok(events.includes("LIVE_MEDIA_PROVIDER_ARGUMENT_ADAPTER_READY"));

  hook.dispose();
  assert.equal(Object.getOwnPropertyDescriptor(Player.prototype, "state").get,
    originalState.get);
  assert.equal(Provider.prototype.getFileInfo({ trackId: "123" }), "123");
  // The adapter wrapper is restored; its original vendor method remains owned by
  // the W22 adapter, which is disposed separately by renderer-entry.
  assert.notEqual(Provider.prototype.getFileInfo, originalGetFileInfo);
});
