(function (root) {
  "use strict";
  const ENGINE_PORT_VERSION = 3;
  if (root.__CELIKOM_NATIVE_ENGINE_PORT__?.version === ENGINE_PORT_VERSION) return;
  const numericId = value => /^\d{1,24}$/.test(String(value)) ? String(value) : null;
  const safe = fn => { try { return fn(); } catch { return null; } };
  let lastDiscovery = null;
  function discoverController(document = root.document) {
    const started = Date.now(), visitedNodes = new Set(), visitedFibers = new Set(), visitedValues = new Set();
    const report = { version: ENGINE_PORT_VERSION, nodes: 0, fiberRoots: 0, fibers: 0, contexts: 0, candidates: 0,
      nonEnumerableRoots: 0, propertyErrors: 0, limited: false, matchSource: null, elapsedMs: 0, seeds: {} };
    lastDiscovery = report;
    const read = fn => { try { return fn(); } catch { report.propertyErrors++; return null; } };
    const within = () => {
      if (Date.now() - started > 100 || report.nodes >= 4096 || report.fibers >= 12000 || report.candidates >= 4000) { report.limited = true; return false; }
      return true;
    };
    const finish = result => { report.elapsedMs = Date.now() - started; return result; };
    function candidate(value, source, depth = 0) {
      if (!value || !["object", "function"].includes(typeof value) || visitedValues.has(value) || !within()) return null;
      visitedValues.add(value); report.candidates++;
      if (read(() => typeof value.getState === "function" && typeof value.playbackController?.getPlayback === "function")) {
        report.matchSource = source; return value;
      }
      if (depth >= 2) return null;
      for (const key of ["controller", "sonata", "sonataController", "playerController", "value", "current"]) {
        const found = candidate(read(() => value[key]), source, depth + 1);
        if (found) return found;
      }
      return null;
    }
    function fiberTree(start) {
      const queue = [start]; let cursor = 0;
      while (cursor < queue.length && cursor < 320 && within()) {
        const fiber = queue[cursor++];
        if (!fiber || typeof fiber !== "object" || visitedFibers.has(fiber)) continue;
        visitedFibers.add(fiber); report.fibers++;
        const props = read(() => fiber.memoizedProps);
        for (const value of [props?.value, props?.controller, props?.sonata]) {
          const found = candidate(value, "fiber-props"); if (found) return found;
        }
        let context = read(() => fiber.dependencies?.firstContext);
        const contexts = new Set();
        while (context && contexts.size < 32 && !contexts.has(context) && within()) {
          contexts.add(context); report.contexts++;
          const found = candidate(read(() => context.memoizedValue), "fiber-context"); if (found) return found;
          context = read(() => context.next);
        }
        if (context && contexts.size >= 32) report.limited = true;
        const parent = read(() => fiber.return), alternate = read(() => fiber.alternate);
        if (parent) queue.push(parent);
        if (alternate) queue.push(alternate);
      }
      if (cursor < queue.length) report.limited = true;
      return null;
    }
    function nodeController(node) {
      if (!node || visitedNodes.has(node) || !within()) return null;
      visitedNodes.add(node); report.nodes++;
      const keys = read(() => Object.getOwnPropertyNames(node)) || [];
      for (const key of keys.filter(name => /^__react(?:Fiber|InternalInstance|Container)\$/.test(name)).slice(0, 3)) {
        const fiber = read(() => node[key]); report.fiberRoots++;
        if (!Object.prototype.propertyIsEnumerable.call(node, key)) report.nonEnumerableRoots++;
        for (const start of [fiber, read(() => fiber?.current), read(() => fiber?.stateNode?.current)]) {
          const found = fiberTree(start); if (found) return found;
        }
      }
      return null;
    }
    /* A request/player UI can be rendered through context consumers and
       portals. Read bounded committed context dependencies, not only props. */
    for (const [name, selector] of [
      ["player", '[data-test-id="PLAYERBAR_DESKTOP"], [data-test-id="VIBE_PLAYERBAR"]'],
      ["controls", '[data-test-id="PLAY_BUTTON"], [data-test-id="PAUSE_BUTTON"], [role="slider"]'],
      ["media", "audio,video"]
    ]) {
      const nodes = read(() => document?.querySelectorAll(selector)); report.seeds[name] = nodes?.length || 0;
      for (const node of Array.from(nodes || []).slice(0, 64)) { const found = nodeController(node); if (found) return finish(found); }
    }
    const walker = read(() => document?.createTreeWalker?.(document.body || document.documentElement, 1));
    if (walker) {
      let node = walker.currentNode;
      while (node && within()) { const found = nodeController(node); if (found) return finish(found); node = read(() => walker.nextNode()); }
    } else {
      for (const node of Array.from(read(() => document?.querySelectorAll("*")) || []).slice(0, 4096)) {
        if (!within()) break; const found = nodeController(node); if (found) return finish(found);
      }
    }
    return finish(null);
  }
  class EnginePort {
    constructor(options = {}) {
      this.getController = options.getController || (() => discoverController());
      this.pending = null; this.sequence = 0;
    }
    binding(controller = this.getController()) {
      return safe(() => {
        const playback = controller?.playbackController?.getPlayback();
        const state = playback?.state;
        const pair = state?.queueState?.currentEntity?.value;
        const entity = pair?.entity, id = numericId(entity?.data?.meta?.id);
        const player = state?.currentMediaPlayer?.value;
        let core = player;
        for (let depth = 0; core && typeof core.getMediaSource !== "function" && depth < 3; depth++) core = core.currentMediaPlayer;
        const audio = core?.currentAudioElement?.value;
        if (!id || !entity || !core || typeof core.reload !== "function" || typeof core.getMediaSource !== "function" || !audio) return null;
        return { controller, playback, state, pair, entity, id, player, core, audio };
      });
    }
    inspect() {
      const controller = safe(() => this.getController()), b = this.binding(controller);
      const shape = safe(() => {
        const playback = controller?.playbackController?.getPlayback();
        const state = playback?.state;
        const pair = state?.queueState?.currentEntity?.value, entity = pair?.entity, player = state?.currentMediaPlayer?.value;
        let core = player, depth = 0;
        while (core && typeof core.getMediaSource !== "function" && depth++ < 3) core = core.currentMediaPlayer;
        return { playback: Boolean(playback), playbackState: Boolean(state), queuePair: Boolean(pair), entity: Boolean(entity), entityTrackId: numericId(entity?.data?.meta?.id),
          player: Boolean(player), sourceLoader: typeof core?.getMediaSource === "function", reload: typeof core?.reload === "function",
          mediaRef: Boolean(core?.currentAudioElement?.value), nestedPlayerDepth: depth };
      });
      const canFence = (object, key) => {
        if (!object || typeof object[key] !== "function") return false;
        const descriptor = Object.getOwnPropertyDescriptor(object, key);
        return descriptor ? descriptor.configurable === true : Object.isExtensible(object);
      };
      return { readerVersion: ENGINE_PORT_VERSION, controllerFound: Boolean(controller), found: Boolean(b), trackId: b?.id || null, durationMs: Number(b?.entity?.data?.meta?.durationMs) || null,
        pending: Boolean(this.pending), nativeReload: Boolean(b?.core?.reload), encryptedRestoreViaEngine: Boolean(b?.core?.reload),
        mediaEvents: typeof b?.audio?.addEventListener === "function" && typeof b?.audio?.removeEventListener === "function",
        sourceFence: canFence(b?.core, "getMediaSource"), playFence: canFence(b?.core, "corePlay"), setSourceFence: canFence(b?.core?.core, "setSrc"),
        nativeHooks: typeof b?.core?.hooks?.beforeMediaSourceContentReload?.promise === "function" && typeof b?.core?.hooks?.afterMediaSourceContentReload?.promise === "function", shape,
        discovery: lastDiscovery ? JSON.parse(JSON.stringify(lastDiscovery)) : null };
    }
    same(binding) {
      const current = this.binding();
      return current && ["controller", "playback", "state", "pair", "entity", "id", "player", "core", "audio"].every(key => current[key] === binding[key]);
    }
    reload(trackId, options = {}) {
      if (this.pending) return this.pending.id === String(trackId) ? this.pending.promise : Promise.reject(Error("native_reload_busy"));
      const binding = this.binding();
      if (!binding || binding.id !== String(trackId)) return Promise.reject(Error("native_binding_unavailable"));
      const operation = { ...binding, generation: ++this.sequence, cancelled: false, intentChanged: false };
      const { core, audio, entity } = binding, original = core.getMediaSource;
      const ownDescriptor = Object.getOwnPropertyDescriptor(core, "getMediaSource");
      const guards = [], ownedSources = new WeakSet();
      let readStarted = false;
      const changed = () => { operation.intentChanged = true; };
      const assertCurrent = () => {
        if (operation.cancelled || !this.same(binding) || options.isCurrent?.() === false) throw Error("native_reload_stale");
        if (operation.intentChanged) throw Error("native_reload_intent_changed");
      };
      const guarded = async function (...args) {
        if (readStarted || args[0]?.entity !== entity) return Reflect.apply(original, this, args);
        readStarted = true;
        assertCurrent();
        const source = await Reflect.apply(original, this, args);
        assertCurrent();
        if (source && ["object", "function"].includes(typeof source)) ownedSources.add(source);
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
          const wrapper = function (...args) {
            if (ownedSources.has(args[0]?.source)) assertCurrent();
            return Reflect.apply(method, this, args);
          };
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
  Object.defineProperty(root, "__CELIKOM_NATIVE_ENGINE_PORT__", { value: { version: ENGINE_PORT_VERSION, EnginePort, discoverController }, configurable: true });
})(globalThis);
