import test from "node:test";
import assert from "node:assert/strict";
import { createLiveMediaProviderHook } from "./live-media-provider-hook.mjs";

test("W188 follows the official 5.129 VE -> MediaController -> MediaPlayer -> getFileInfoProvider chain", async () => {
  class FileInfoProvider {
    async getFileInfo(params) {
      return { id: params.trackId, entityId: params.entity?.data?.meta?.id };
    }
    async getFileInfoBatchRequest(params) { return { trackIds: params.trackIds }; }
    async getMediaSource(params) { return this.getFileInfo(params); }
  }
  class MediaProvider {
    constructor() { this.getFileInfoProvider = new FileInfoProvider(); }
    getMediaSource(params) { return this.getFileInfoProvider.getMediaSource(params); }
  }
  class YandexMediaPlayer { constructor() { this.mediaProvider = new MediaProvider(); } }
  class CrossMediaPlayer {
    constructor() {
      this.firstMediaPlayer = new YandexMediaPlayer();
      this.secondMediaPlayer = new YandexMediaPlayer();
      this.currentMediaPlayer = this.firstMediaPlayer;
    }
  }
  class Player {
    constructor() {
      const cross = new CrossMediaPlayer();
      const currentMediaPlayer = { value: cross };
      const mediaPlayersStore = { value: { audio: cross } };
      this.mediaController = { currentMediaPlayer, mediaPlayersStore };
      this.playbackState = { currentMediaPlayer, mediaPlayersStore,
        queueState: { currentEntity: { value: {
          entity: { data: { meta: { id: "144530503" } } }
        } } } };
    }
    get state() { return this.playbackState; }
    reloadEntity() {}
  }
  const requireFn = id => id === 7123 ? { VE: Player } : null;
  requireFn.m = { 7123() {} };
  const events = [];
  const adapter = {
    attach(proto) {
      const single = proto.getFileInfo;
      proto.getFileInfo = function(params, ...rest) { return single.call(this, params, ...rest); };
      const batch = proto.getFileInfoBatch;
      if (typeof batch === "function")
        proto.getFileInfoBatch = function(params, ...rest) { return batch.call(this, params, ...rest); };
      return this;
    }
  };
  const hook = createLiveMediaProviderHook({ onEvent: code => events.push(code) });
  assert.equal(hook.attach(requireFn), true);
  const player = new Player();
  void player.state;
  const provider = player.mediaController.currentMediaPlayer.value.currentMediaPlayer
    .mediaProvider.getFileInfoProvider;
  const proto = Object.getPrototypeOf(provider);
  const originalSingle = Object.getOwnPropertyDescriptor(proto, "getFileInfo");
  const originalBatch = Object.getOwnPropertyDescriptor(proto, "getFileInfoBatchRequest");
  assert.equal(hook.findFileInfoProvider(), provider);
  assert.equal(hook.attachAdapter(adapter), true);
  const entity = { data: { meta: { id: "144530503" } } };
  const result = await provider.getFileInfo({ entity, quality: "nq" });
  assert.equal(result.id, "144530503");
  assert.equal(result.entityId, "144530503");
  const batch = await provider.getFileInfoBatchRequest({ trackIds: "144530503,123" });
  assert.equal(batch.trackIds, "144530503,123");
  assert.ok(events.includes("LIVE_PLAYER_STATE_OBSERVER_READY"));
  assert.ok(events.includes("LIVE_PLAYER_INSTANCE_SEEN"));
  assert.ok(events.includes("LIVE_MEDIA_PROVIDER_FOUND"));
  assert.ok(events.includes("LIVE_MEDIA_PROVIDER_ARGUMENT_ADAPTER_READY"));
  hook.dispose();
  assert.deepEqual(Object.getOwnPropertyDescriptor(proto, "getFileInfo"), originalSingle);
  assert.deepEqual(Object.getOwnPropertyDescriptor(proto, "getFileInfoBatchRequest"), originalBatch);
});
