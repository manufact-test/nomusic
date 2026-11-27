export function createLiveMediaProviderHook({onEvent = () => {}} = {}) {
  let playerPrototype = null, originalState = null, observedState = null;
  let currentPlayer = null, disposed = false;
  let providerPrototype = null, originalSingleDescriptor = null;
  let originalBatchDescriptor = null, singleBridge = null, batchBridge = null;
  let adapterShim = null;
  const note = code => { try { onEvent(code); } catch {} };
  const validId = raw => {
    if (typeof raw === "number" && Number.isSafeInteger(raw) && raw > 0) return String(raw);
    return typeof raw === "string" && /^[1-9][0-9]{0,23}$/.test(raw) ? raw : null;
  };
  const values = ref => {
    const value = ref && typeof ref === "object" && "value" in ref ? ref.value : ref;
    if (Array.isArray(value)) return value;
    if (value && typeof value === "object") return Object.values(value);
    return [];
  };
  function attach(webpackRequire) {
    if (disposed) return false;
    if (playerPrototype) return true;
    if (typeof webpackRequire !== "function" || typeof webpackRequire.m !== "object" ||
        typeof webpackRequire.m[7123] !== "function") return false;
    let Player;
    try { Player = webpackRequire(7123)?.VE; } catch { return false; }
    if (typeof Player !== "function" || !Player.prototype ||
        typeof Player.prototype.reloadEntity !== "function") return false;
    const descriptor = Object.getOwnPropertyDescriptor(Player.prototype, "state");
    if (!descriptor?.configurable || typeof descriptor.get !== "function" || descriptor.set !== undefined) return false;
    const getter = function() {
      const state = descriptor.get.call(this);
      if (!disposed) {
        try {
          const id = validId(state?.queueState?.currentEntity?.value?.entity?.data?.meta?.id);
          if (id) { currentPlayer = new WeakRef(this); note("LIVE_PLAYER_INSTANCE_SEEN"); }
        } catch {}
      }
      return state;
    };
    try { Object.defineProperty(Player.prototype, "state", { ...descriptor, get: getter }); }
    catch { return false; }
    playerPrototype = Player.prototype; originalState = descriptor; observedState = getter;
    note("LIVE_PLAYER_STATE_OBSERVER_READY");
    return true;
  }
  function findFileInfoProvider() {
    if (disposed) return null;
    const player = currentPlayer?.deref();
    if (!player) return null;
    // Official 5.129: VE -> mediaController.currentMediaPlayer.value ->
    // crossfade current/first/second player -> mediaProvider.getFileInfoProvider.
    const roots = [], seen = new Set();
    const add = value => {
      if (!value || typeof value !== "object" || seen.has(value)) return;
      seen.add(value); roots.push(value);
    };
    try {
      const controller = player.mediaController, state = player.playbackState;
      add(controller?.currentMediaPlayer?.value);
      add(controller?.currentMediaPlayer);
      add(state?.currentMediaPlayer?.value);
      add(state?.currentMediaPlayer);
      for (const value of values(controller?.mediaPlayersStore)) add(value);
      for (const value of values(state?.mediaPlayersStore)) add(value);
      add(controller);
    } catch { return null; }
    const mediaPlayers = [], mediaSeen = new Set();
    const addMediaPlayer = value => {
      if (!value || typeof value !== "object" || mediaSeen.has(value)) return;
      mediaSeen.add(value); mediaPlayers.push(value);
    };
    for (const root of roots) {
      addMediaPlayer(root);
      try {
        addMediaPlayer(root.currentMediaPlayer?.value ?? root.currentMediaPlayer);
        addMediaPlayer(root.firstMediaPlayer);
        addMediaPlayer(root.secondMediaPlayer);
      } catch {}
    }
    for (const mediaPlayer of mediaPlayers) {
      let providers = [];
      try { providers = [mediaPlayer.mediaProvider, mediaPlayer]; } catch {}
      for (const mediaProvider of providers) {
        try {
          const fileInfoProvider = mediaProvider?.getFileInfoProvider;
          if (typeof mediaProvider?.getMediaSource === "function" &&
              typeof fileInfoProvider?.getMediaSource === "function" &&
              typeof fileInfoProvider?.getFileInfo === "function") {
            note("LIVE_MEDIA_PROVIDER_FOUND");
            return fileInfoProvider;
          }
        } catch {}
      }
    }
    return null;
  }
  function attachAdapter(adapter) {
    if (disposed || !adapter || typeof adapter.attach !== "function") return false;
    if (adapterShim) return true;
    const fileInfoProvider = findFileInfoProvider();
    if (!fileInfoProvider) return false;
    const proto = Object.getPrototypeOf(fileInfoProvider) || fileInfoProvider;
    const singleDescriptor = Object.getOwnPropertyDescriptor(proto, "getFileInfo");
    const batchDescriptor = Object.getOwnPropertyDescriptor(proto, "getFileInfoBatchRequest");
    const originalSingle = singleDescriptor?.value, originalBatch = batchDescriptor?.value;
    if (typeof originalSingle !== "function" ||
        (singleDescriptor.configurable === false && singleDescriptor.writable === false)) return false;
    // W22 expects trackId; Yandex 5.129's high-level getFileInfo accepts entity.
    // The shim also routes the real getFileInfoBatchRequest through W22's batch contract.
    const shim = Object.create(null);
    shim.getFileInfo = function(params, ...rest) { return originalSingle.call(this, params, ...rest); };
    if (typeof originalBatch === "function")
      shim.getFileInfoBatch = function(params, ...rest) { return originalBatch.call(this, params, ...rest); };
    try { if (!adapter.attach(shim)) return false; } catch { return false; }
    const bridgeSingle = function(params, ...rest) {
      let raw;
      try { raw = params?.trackId ?? params?.entity?.data?.meta?.id ??
        params?.entity?.data?.id ?? params?.entity?.id; } catch {}
      const id = validId(raw);
      const next = id && params && typeof params === "object" && params.trackId !== id
        ? { ...params, trackId: id } : params;
      return shim.getFileInfo.call(this, next, ...rest);
    };
    let bridgeBatch = null;
    try {
      Object.defineProperty(proto, "getFileInfo", { ...singleDescriptor, value: bridgeSingle });
      if (typeof originalBatch === "function") {
        if (!batchDescriptor ||
            (batchDescriptor.configurable === false && batchDescriptor.writable === false))
          throw new Error("W188_BATCH_METHOD_NOT_PATCHABLE");
        bridgeBatch = function(params, ...rest) {
          return shim.getFileInfoBatch.call(this, params, ...rest);
        };
        Object.defineProperty(proto, "getFileInfoBatchRequest", { ...batchDescriptor, value: bridgeBatch });
      }
    } catch {
      try { Object.defineProperty(proto, "getFileInfo", singleDescriptor); } catch {}
      try { adapter.dispose(); } catch {}
      return false;
    }
    providerPrototype = proto;
    originalSingleDescriptor = singleDescriptor;
    originalBatchDescriptor = batchDescriptor || null;
    singleBridge = bridgeSingle; batchBridge = bridgeBatch; adapterShim = shim;
    note("LIVE_MEDIA_PROVIDER_ARGUMENT_ADAPTER_READY");
    return true;
  }
  function dispose() {
    if (disposed) return;
    disposed = true; currentPlayer = null;
    if (providerPrototype && singleBridge && providerPrototype.getFileInfo === singleBridge) {
      try { Object.defineProperty(providerPrototype, "getFileInfo", originalSingleDescriptor); } catch {}
    }
    if (providerPrototype && batchBridge && providerPrototype.getFileInfoBatchRequest === batchBridge) {
      try { Object.defineProperty(providerPrototype, "getFileInfoBatchRequest", originalBatchDescriptor); } catch {}
    }
    if (playerPrototype && originalState &&
        Object.getOwnPropertyDescriptor(playerPrototype, "state")?.get === observedState) {
      try { Object.defineProperty(playerPrototype, "state", originalState); } catch {}
    }
    providerPrototype = originalSingleDescriptor = originalBatchDescriptor = null;
    singleBridge = batchBridge = adapterShim = null;
    playerPrototype = originalState = observedState = null;
  }
  return { attach, findFileInfoProvider, attachAdapter, dispose };
}
