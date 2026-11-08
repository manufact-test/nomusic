(function (root) {
  "use strict";
  if (root.__CELIKOM_NATIVE_DESKTOP_ADAPTER__) return;
  function createDesktopPrefetch(options) {
    const Coordinator = root.__CELIKOM_NATIVE_PREFETCH__?.PrefetchCoordinator;
    const Player = root.__CELIKOM_REPLACEMENT_PLAYER_V1__?.ReplacementPlayer;
    if (!Coordinator || !Player || typeof options.engine?.resolveAsset !== "function" || typeof options.mp3DurationMs !== "function") throw Error("native_dependencies_unavailable");
    return new Coordinator({
      resolve: (id, flags) => options.engine.resolveAsset(id, flags),
      download: async (asset, signal) => {
        const abort = new options.environment.AbortController();
        const cancelled = () => abort.abort();
        signal.addEventListener("abort", cancelled, { once: true });
        if (signal.aborted) cancelled();
        const holder = { environment: options.environment, destroyed: false, fetchAbort: abort, streamState: {} };
        try { return await Player.prototype.fetchNativeAsset.call(holder, asset); }
        finally { signal.removeEventListener("abort", cancelled); }
      },
      inspectDuration: options.mp3DurationMs,
      publish: options.publish,
      revoke: options.revoke,
      now: options.now
    });
  }
  Object.defineProperty(root, "__CELIKOM_NATIVE_DESKTOP_ADAPTER__", { value: { createDesktopPrefetch }, configurable: true });
})(globalThis);
