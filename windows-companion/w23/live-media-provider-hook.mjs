export function createLiveMediaProviderHook({onEvent = () => {}} = {}) {
  let playerPrototype = null, originalState = null, observedState = null;
  let currentPlayer = null, disposed = false, wrappedPrototype = null;
  let adapterMethod = null, normalizedMethod = null;
  const note = code => { try { onEvent(code); } catch {} };
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
          const id = state?.queueState?.currentEntity?.value?.entity?.data?.meta?.id;
          if ((typeof id === "string" && /^[1-9][0-9]{0,23}$/.test(id)) ||
              (typeof id === "number" && Number.isSafeInteger(id) && id > 0))
            currentPlayer = new WeakRef(this);
          note("LIVE_PLAYER_INSTANCE_SEEN");
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
  function findProviderPrototype() {
    if (disposed) return null;
    const player = currentPlayer?.deref();
    if (!player) return null;
    let candidates;
    try {
      candidates = [player.currentMediaPlayer?.mediaProvider,
        player.firstMediaPlayer?.mediaProvider, player.secondMediaPlayer?.mediaProvider,
        player.mediaProvider];
    } catch { return null; }
    for (const provider of candidates) {
      try {
        if (!provider || typeof provider.getMediaSource !== "function" ||
            typeof provider.getFileInfo !== "function") continue;
        const proto = Object.getPrototypeOf(provider) || provider;
        if (typeof proto.getFileInfo === "function") { note("LIVE_MEDIA_PROVIDER_FOUND"); return proto; }
        note("LIVE_MEDIA_PROVIDER_FOUND"); return provider;
      } catch {}
    }
    return null;
  }
  function normalizeAdapterArguments(proto) {
    if (disposed || !proto || typeof proto.getFileInfo !== "function" || wrappedPrototype) return false;
    const patched = proto.getFileInfo;
    const normalized = function(params, ...rest) {
      let raw;
      try { raw = params?.trackId ?? params?.id ?? params?.entity?.data?.meta?.id ??
        params?.entity?.data?.id ?? params?.entity?.id; } catch {}
      const id = typeof raw === "number" && Number.isSafeInteger(raw) && raw > 0
        ? String(raw) : typeof raw === "string" && /^[1-9][0-9]{0,23}$/.test(raw) ? raw : null;
      const next = id && params && typeof params === "object" && params.trackId !== id
        ? { ...params, trackId: id } : params;
      return patched.call(this, next, ...rest);
    };
    try { proto.getFileInfo = normalized; } catch { return false; }
    wrappedPrototype = proto; adapterMethod = patched; normalizedMethod = normalized;
    note("LIVE_MEDIA_PROVIDER_ARGUMENT_ADAPTER_READY");
    return true;
  }
  function dispose() {
    if (disposed) return;
    disposed = true; currentPlayer = null;
    if (wrappedPrototype && normalizedMethod && wrappedPrototype.getFileInfo === normalizedMethod) {
      try { wrappedPrototype.getFileInfo = adapterMethod; } catch {}
    }
    if (playerPrototype && originalState &&
        Object.getOwnPropertyDescriptor(playerPrototype, "state")?.get === observedState) {
      try { Object.defineProperty(playerPrototype, "state", originalState); } catch {}
    }
    wrappedPrototype = adapterMethod = normalizedMethod = null;
    playerPrototype = originalState = observedState = null;
  }
  return { attach, findProviderPrototype, normalizeAdapterArguments, dispose };
}
