(function (root) {
  "use strict";
  /* Research-only MAIN-world module. Not loaded by the CELIKOM manifest. */
  if (root.__CELIKOM_NATIVE_SOURCE_RESEARCH__) return;
  const assets = new Map(), patches = [], patched = new WeakSet();
  const scanned = new Map();
  const metrics = { resourceClasses: 0, urlNormalization: false, singles: 0, batches: 0, replacements: 0 };
  let enabled = true, stopped = false, timer = null, requireApp = null, attempts = 0;
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const idOf = value => /^\d{1,20}$/.test(String(value)) ? String(value) : null;
  const assetFor = value => {
    const id = idOf(value), asset = id && assets.get(id);
    return enabled && !stopped && metrics.urlNormalization && asset && asset.expiresAt > Date.now() ? asset : null;
  };
  function normalizeOwnedUrl(url) {
    if (typeof url !== "string") return url;
    for (const asset of assets.values()) {
      if (!url.startsWith(asset.url + "?")) continue;
      const fragment = url.indexOf("#", asset.url.length);
      return asset.url + (fragment < 0 ? "" : url.slice(fragment));
    }
    return url;
  }
  const mediaProto = root.HTMLMediaElement?.prototype;
  const mediaSrc = mediaProto && Object.getOwnPropertyDescriptor(mediaProto, "src");
  if (mediaSrc?.configurable && mediaSrc.set) {
    const setter = function (url) { return Reflect.apply(mediaSrc.set, this, [normalizeOwnedUrl(url)]); };
    Object.defineProperty(mediaProto, "src", { ...mediaSrc, set: setter });
    patches.push(() => {
      if (Object.getOwnPropertyDescriptor(mediaProto, "src")?.set === setter) Object.defineProperty(mediaProto, "src", mediaSrc);
    });
    metrics.urlNormalization = true;
  }
  function replaceInfo(base, id) {
    const asset = assetFor(id);
    if (!asset || !base || typeof base !== "object" || own(base, "error") || String(base.trackId) !== String(id)) return base;
    metrics.replacements++;
    return { trackId: String(id), realId: String(id), quality: base.quality || "nq", codec: "mp3", bitrate: asset.bitrate,
      transport: "raw", gain: false, urls: [asset.url], url: asset.url };
  }
  function wrap(proto, name, factory) {
    const descriptor = Object.getOwnPropertyDescriptor(proto, name);
    if (!descriptor || typeof descriptor.value !== "function" || !descriptor.configurable || !descriptor.writable) return false;
    const wrapped = factory(descriptor.value);
    Object.defineProperty(proto, name, { ...descriptor, value: wrapped });
    patches.push(() => {
      if (proto[name] === wrapped) Object.defineProperty(proto, name, descriptor);
    });
    return true;
  }
  function inspect(exports) {
    if (!exports || typeof exports !== "object") return;
    for (const key of Object.keys(exports)) {
      let C; try { C = exports[key]; } catch { continue; }
      if (typeof C !== "function" || !C.prototype || patched.has(C.prototype)) continue;
      const proto = C.prototype;
      if (typeof proto.getFileInfo !== "function" || typeof proto.getFileInfoBatch !== "function") continue;
      if (!wrap(proto, "getFileInfo", original => async function (params, ...rest) {
        const result = await Reflect.apply(original, this, [params, ...rest]);
        metrics.singles++;
        if (rest[0]?.signal?.aborted || !result || typeof result !== "object") return result;
        const field = own(result, "fileInfo") ? "fileInfo" : own(result, "downloadInfo") ? "downloadInfo" : null;
        if (!field) return result;
        const info = replaceInfo(result[field], params?.trackId);
        return info === result[field] ? result : { ...result, [field]: info };
      })) continue;
      wrap(proto, "getFileInfoBatch", original => async function (params, ...rest) {
        const result = await Reflect.apply(original, this, [params, ...rest]);
        metrics.batches++;
        if (rest[0]?.signal?.aborted || !result || typeof result !== "object") return result;
        const ids = new Set((Array.isArray(params?.trackIds) ? params.trackIds : String(params?.trackIds || "").split(",")).map(String));
        const field = own(result, "fileInfos") ? "fileInfos" : own(result, "downloadInfos") ? "downloadInfos" : null;
        if (!field || !Array.isArray(result[field])) return result;
        let changed = false;
        const list = result[field].map(info => {
          if (!ids.has(String(info?.trackId))) return info;
          const replaced = replaceInfo(info, info?.trackId); changed ||= replaced !== info; return replaced;
        });
        return changed ? { ...result, [field]: list } : result;
      });
      patched.add(proto); metrics.resourceClasses++;
    }
  }
  function scan() {
    if (stopped) return;
    if (!requireApp) {
      const chunks = root.webpackChunk_N_E;
      if (!Array.isArray(chunks) || chunks.push === Array.prototype.push) return;
      chunks.push([[Symbol("celikom-native-research")], {}, r => { requireApp = r; }]);
    }
    if (!requireApp?.m) return;
    const modules = Object.keys(requireApp.m);
    if (modules.length > 20000) return;
    for (const id of modules) {
      if (scanned.get(id) === requireApp.m[id]) continue;
      let src; try { src = Function.prototype.toString.call(requireApp.m[id]); } catch { continue; }
      const resource = src.includes("getFileInfoBatch") && (src.includes('"get-file-info"') || src.includes('"resources/v2/file-info"'));
      if (!resource) { scanned.set(id, requireApp.m[id]); continue; }
      try { inspect(requireApp(id)); scanned.set(id, requireApp.m[id]); } catch { /* Retry only matching resources whose dependencies were not ready. */ }
    }
  }
  if (root.Element?.prototype && metrics.urlNormalization) {
    wrap(root.Element.prototype, "setAttribute", original => function (name, value) {
      if (this instanceof root.HTMLMediaElement && String(name).toLowerCase() === "src") value = normalizeOwnedUrl(value);
      return Reflect.apply(original, this, [name, value]);
    });
  }
  const api = {
    register(id, url, { expiresAt, bitrate = 320 } = {}) {
      const normalized = idOf(id);
      if (!normalized || typeof url !== "string" || !url.startsWith("blob:" + root.location.origin + "/")
        || !Number.isFinite(expiresAt) || expiresAt <= Date.now() || expiresAt > Date.now() + 300000
        || ![128, 192, 256, 320].includes(bitrate) || (assets.size >= 2 && !assets.has(normalized))) throw Error("invalid_research_asset");
      assets.set(normalized, { url, expiresAt, bitrate });
    },
    setEnabled(value) { enabled = value === true; },
    diagnostics() { return { ...metrics, enabled, stopped, assets: assets.size, attempts }; },
    scan,
    dispose() {
      stopped = true; enabled = false; root.clearTimeout(timer);
      for (const undo of patches.reverse()) undo();
      assets.clear(); scanned.clear();
    }
  };
  Object.defineProperty(root, "__CELIKOM_NATIVE_SOURCE_RESEARCH__", { value: api, configurable: true });
  function poll() {
    attempts++; scan();
    if (!stopped && attempts < 150) timer = root.setTimeout(poll, 200);
  }
  poll();
})(globalThis);
