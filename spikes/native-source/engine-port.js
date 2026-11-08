(function (root) {
  "use strict";
  if (root.__CELIKOM_NATIVE_ENGINE_PORT__) return;
  const numericId = value => /^\d{1,24}$/.test(String(value)) ? String(value) : null;
  const safe = fn => { try { return fn(); } catch { return null; } };
  function discoverController(document = root.document) {
    const nodes = Array.from(document?.querySelectorAll('[data-test-id="PLAYERBAR_DESKTOP"], [data-test-id="VIBE_PLAYERBAR"], [data-test-id="PLAYERBAR_DESKTOP"] button, audio') || []).slice(0, 16);
    const visited = new Set();
    for (const node of nodes) {
      const fiberKey = Object.keys(node).find(key => key.startsWith("__reactFiber$"));
      let fiber = fiberKey && node[fiberKey];
      for (let depth = 0; fiber && depth < 160 && !visited.has(fiber); depth++, fiber = fiber.return) {
        visited.add(fiber);
        const props = safe(() => fiber.memoizedProps);
        for (const value of [props?.value, props?.controller, props?.sonata]) {
          if (value && typeof value.getState === "function" && typeof value.playbackController?.getPlayback === "function") return value;
        }
      }
    }
    return null;
  }
  class EnginePort {
    constructor(options = {}) {
      this.getController = options.getController || (() => discoverController());
      this.pending = null; this.sequence = 0;
    }
    binding() {
      return safe(() => {
        const controller = this.getController();
        const playback = controller?.playbackController?.getPlayback();
        const pair = playback?.queueState?.currentEntity?.value;
        const entity = pair?.entity, id = numericId(entity?.data?.meta?.id);
        const player = playback?.currentMediaPlayer?.value;
        let core = player;
        for (let depth = 0; core && typeof core.getMediaSource !== "function" && depth < 3; depth++) core = core.currentMediaPlayer;
        const audio = core?.currentAudioElement?.value;
        if (!id || !entity || !core || typeof core.reload !== "function" || typeof core.getMediaSource !== "function" || !audio) return null;
        return { controller, playback, pair, entity, id, player, core, audio };
      });
    }
    inspect() {
      const b = this.binding();
      const shape = safe(() => {
        const controller = this.getController(), playback = controller?.playbackController?.getPlayback();
        const pair = playback?.queueState?.currentEntity?.value, entity = pair?.entity, player = playback?.currentMediaPlayer?.value;
        let core = player, depth = 0;
        while (core && typeof core.getMediaSource !== "function" && depth++ < 3) core = core.currentMediaPlayer;
        return { playback: Boolean(playback), queuePair: Boolean(pair), entity: Boolean(entity), entityTrackId: numericId(entity?.data?.meta?.id),
          player: Boolean(player), sourceLoader: typeof core?.getMediaSource === "function", reload: typeof core?.reload === "function",
          mediaRef: Boolean(core?.currentAudioElement?.value), nestedPlayerDepth: depth };
      });
      const canFence = (object, key) => {
        if (!object || typeof object[key] !== "function") return false;
        const descriptor = Object.getOwnPropertyDescriptor(object, key);
        return descriptor ? descriptor.configurable === true : Object.isExtensible(object);
      };
      return { controllerFound: Boolean(safe(() => this.getController())), found: Boolean(b), trackId: b?.id || null, durationMs: Number(b?.entity?.data?.meta?.durationMs) || null,
        pending: Boolean(this.pending), nativeReload: Boolean(b?.core?.reload), encryptedRestoreViaEngine: Boolean(b?.core?.reload),
        mediaEvents: typeof b?.audio?.addEventListener === "function" && typeof b?.audio?.removeEventListener === "function",
        sourceFence: canFence(b?.core, "getMediaSource"), playFence: canFence(b?.core, "corePlay"), setSourceFence: canFence(b?.core?.core, "setSrc"),
        nativeHooks: typeof b?.core?.hooks?.beforeMediaSourceContentReload?.promise === "function" && typeof b?.core?.hooks?.afterMediaSourceContentReload?.promise === "function", shape };
    }
    same(binding) {
      const current = this.binding();
      return current && ["controller", "playback", "pair", "entity", "id", "player", "core", "audio"].every(key => current[key] === binding[key]);
    }
    reload(trackId, options = {}) {
      if (this.pending) return this.pending.id === String(trackId) ? this.pending.promise : Promise.reject(Error("native_reload_busy"));
      const binding = this.binding();
      if (!binding || binding.id !== String(trackId)) return Promise.reject(Error("native_binding_unavailable"));
      const operation = { ...binding, generation: ++this.sequence, cancelled: false, intentChanged: false };
      const { core, audio, entity } = binding, original = core.getMediaSource;
      const ownDescriptor = Object.getOwnPropertyDescriptor(core, "getMediaSource");
      const guards = [];
      const changed = () => { operation.intentChanged = true; };
      const assertCurrent = () => {
        if (operation.cancelled || !this.same(binding) || options.isCurrent?.() === false) throw Error("native_reload_stale");
        if (operation.intentChanged) throw Error("native_reload_intent_changed");
      };
      const guarded = async function (...args) {
        assertCurrent();
        const source = await Reflect.apply(original, this, args);
        assertCurrent();
        return source;
      };
      operation.promise = Promise.resolve().then(async () => {
        for (const event of ["pause", "play", "seeking"]) audio.addEventListener(event, changed);
        assertCurrent();
        Object.defineProperty(core, "getMediaSource", { value: guarded, configurable: true, writable: true });
        for (const [target, key] of [[core, "corePlay"], [core.core, "setSrc"]]) {
          const method = target?.[key];
          if (typeof method !== "function") continue;
          const descriptor = Object.getOwnPropertyDescriptor(target, key);
          const wrapper = function (...args) { assertCurrent(); return Reflect.apply(method, this, args); };
          Object.defineProperty(target, key, { value: wrapper, writable: true, configurable: true });
          guards.push(() => {
            if (target[key] !== wrapper) return;
            if (descriptor) Object.defineProperty(target, key, descriptor); else delete target[key];
          });
        }
        /* Stock reload requests disableCache:true and retains the native key,
           position and paused state. Never assign encrypted bytes to audio.src. */
        await Reflect.apply(core.reload, core, [entity]);
        if (!this.same(binding)) return { restored: false, stale: true };
        return { restored: true, trackId: binding.id };
      }).finally(() => {
        for (const event of ["pause", "play", "seeking"]) audio.removeEventListener(event, changed);
        for (const undo of guards.reverse()) undo();
        if (core.getMediaSource === guarded) {
          if (ownDescriptor) Object.defineProperty(core, "getMediaSource", ownDescriptor);
          else delete core.getMediaSource;
        }
        if (this.pending === operation) this.pending = null;
      });
      this.pending = operation;
      return operation.promise;
    }
    cancel() { if (this.pending) this.pending.cancelled = true; }
  }
  Object.defineProperty(root, "__CELIKOM_NATIVE_ENGINE_PORT__", { value: { EnginePort, discoverController }, configurable: true });
})(globalThis);
