/*
 * CELIKOM Windows W4 — experimental resource response adapter.
 * No injection, app.asar changes, separate playback clock or audio decoder.
 * This is a contract fixture until the official Windows renderer seam is proven.
 */
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
const id = value => /^\d{1,20}$/.test(String(value)) ? String(value) : null;
const matchBlob = (url, origin) => typeof url === "string" &&
  url.startsWith("blob:" + origin + "/") && !/[?#]/.test(url.slice(("blob:" + origin + "/").length));

export function createWindowsSourceBridge({ origin, now = () => Date.now() }) {
  if (typeof origin !== "string" || !/^https?:\/\/[^/]+$/.test(origin))
    throw Error("fixture origin required");
  const assets = new Map(), unhooks = [], installed = new WeakSet();
  let activeId = null, enabled = false, forceOriginal = false, revision = 0, disposed = false;
  const stats = { installed: 0, substituted: 0, stale: 0, original: 0 };

  const choice = (requestId, generation) => {
    const trackId = id(requestId), asset = trackId && assets.get(trackId);
    if (disposed || !enabled || forceOriginal || generation !== revision ||
        !trackId || trackId !== activeId || !asset || asset.expiresAt <= now() + 30000)
      return null;
    return asset;
  };

  const replace = (base, requestId, generation) => {
    if (!base || typeof base !== "object" || own(base, "error") ||
        id(base.trackId) !== id(requestId)) { stats.original++; return base; }
    const asset = choice(requestId, generation);
    if (!asset) { stats.original++; return base; }
    // Never mutate original response or preserve a stale encrypted key.
    const output = { ...base, codec: "mp3", transport: "raw", bitrate: asset.bitrate,
      url: asset.url, urls: [asset.url], trackId: String(requestId), realId: String(requestId) };
    delete output.key;
    delete output.encryptionKey;
    delete output.secretKey;
    stats.substituted++;
    return output;
  };

  const patch = (proto, name, factory) => {
    const descriptor = Object.getOwnPropertyDescriptor(proto, name);
    if (!descriptor || typeof descriptor.value !== "function" ||
        !descriptor.configurable || !descriptor.writable) throw Error("unsupported_method_" + name);
    const wrapped = factory(descriptor.value);
    Object.defineProperty(proto, name, { ...descriptor, value: wrapped });
    unhooks.push(() => {
      if (Object.getOwnPropertyDescriptor(proto, name)?.value === wrapped)
        Object.defineProperty(proto, name, descriptor);
    });
  };

  const mutateSingle = (result, params, captured) => {
    if (!result || typeof result !== "object") return result;
    const key = own(result, "fileInfo") ? "fileInfo" : own(result, "downloadInfo") ? "downloadInfo" : null;
    if (!key) return result;
    const value = replace(result[key], params?.trackId, captured);
    return value === result[key] ? result : { ...result, [key]: value };
  };

  const mutateBatch = (result, params, captured) => {
    if (!result || typeof result !== "object") return result;
    const key = own(result, "fileInfos") ? "fileInfos" : own(result, "downloadInfos") ? "downloadInfos" : null;
    if (!key || !Array.isArray(result[key])) return result;
    const requestIds = Array.isArray(params?.trackIds) ? params.trackIds
      : typeof params?.trackIds === "string" ? params.trackIds.split(",") : [];
    const allowed = new Set(requestIds.map(id).filter(Boolean));
    let changed = false;
    const list = result[key].map(item => {
      if (!item || !allowed.has(id(item.trackId))) return item;
      const replacement = replace(item, item.trackId, captured);
      if (replacement !== item) changed = true;
      return replacement;
    });
    return changed ? { ...result, [key]: list } : result;
  };

  return Object.freeze({
    setTrack(trackId) {
      if (disposed) throw Error("disposed");
      const exact = id(trackId);
      if (!exact) throw Error("exact_track_id_required");
      if (activeId !== exact) { activeId = exact; forceOriginal = false; revision++; }
    },
    setEnabled(value) {
      if (disposed) throw Error("disposed");
      enabled = value === true; revision++;
    },
    registerPreparedAsset({ trackId, url, expiresAt, bitrate = 320,
      approved, entitled, durationMatched, audioValidated }) {
      if (disposed) throw Error("disposed");
      const exact = id(trackId);
      if (!exact || !matchBlob(url, origin) || !Number.isFinite(expiresAt) ||
          expiresAt <= now() + 30000 || expiresAt > now() + 300000 ||
          ![128,192,256,320].includes(bitrate) || !approved || !entitled ||
          !durationMatched || !audioValidated || (assets.size >= 2 && !assets.has(exact)))
        throw Error("invalid_prepared_asset");
      assets.set(exact, { url, bitrate, expiresAt });
    },
    clearPreparedAssets() { assets.clear(); revision++; },
    original() { forceOriginal = true; revision++; },
    stop() { enabled = false; revision++; assets.clear(); },
    install(resourcePrototype) {
      if (disposed) throw Error("disposed");
      if (!resourcePrototype || typeof resourcePrototype !== "object")
        throw Error("resource_prototype_required");
      if (installed.has(resourcePrototype)) throw Error("already_installed");
      const getInfo = Object.getOwnPropertyDescriptor(resourcePrototype, "getFileInfo");
      const getBatch = Object.getOwnPropertyDescriptor(resourcePrototype, "getFileInfoBatch");
      if (![getInfo, getBatch].every(d => d && d.configurable && d.writable && typeof d.value === "function"))
        throw Error("unsupported_resource_shape");
      patch(resourcePrototype, "getFileInfo", fn => async function(params, options, ...rest) {
        const captured = revision;
        const response = await Reflect.apply(fn, this, [params, options, ...rest]);
        if (options?.signal?.aborted) return response;
        if (captured !== revision) stats.stale++;
        return mutateSingle(response, params, captured);
      });
      patch(resourcePrototype, "getFileInfoBatch", fn => async function(params, options, ...rest) {
        const captured = revision;
        const response = await Reflect.apply(fn, this, [params, options, ...rest]);
        if (options?.signal?.aborted) return response;
        if (captured !== revision) stats.stale++;
        return mutateBatch(response, params, captured);
      });
      installed.add(resourcePrototype);
      stats.installed++;
    },
    diagnostics() { return { ...stats, enabled, disposed, currentTrackKnown: Boolean(activeId), assetCount: assets.size }; },
    dispose() {
      if (disposed) return;
      disposed = true; enabled = false; assets.clear(); activeId = null; revision++;
      for (const undo of unhooks.reverse()) undo();
    }
  });
}
