/**
 * CELIKOM W22: independent source-only adapter for Yandex renderer file-info.
 * Does not patch/launch Yandex. Requires a separately approved host adapter.
 * Resource response research: MIT https://github.com/S4YN3X/FkCensor
 * Uses CELIKOM's own grant validator, NOT PulseSync Client or GPL SDK.
 */
import { exactTrackId, validateCelikomGrant } from '../w15/source-controller.mjs';

const DEFAULT_DEADLINE_MS = 1250;
const NEGATIVE_TTL_MS = 3000;
const POSITIVE_SAFETY_MS = 12000;
const MAX_CACHE = 24;

function validId(raw) {
  const id = typeof raw === 'number' && Number.isSafeInteger(raw)
    ? String(raw) : typeof raw === 'string' ? raw : '';
  return exactTrackId({ id });
}
function toDownloadInfo(original, trackId, url, mimeType, quality) {
  const result = { ...(original && typeof original === 'object' && !('error' in original) ? original : {}) };
  delete result.key;
  delete result.iv;
  // Keep Yandex's player/clock/queue/transport controls; replace source only.
  return {
    ...result, trackId, realId: trackId,
    codec: mimeType === 'audio/mp4' ? 'aac-mp4' : 'mp3',
    transport: 'raw', quality: result.quality || quality || 'nq',
    gain: false, urls: [url], url
  };
}

/**
 * Hooks one already-discovered resource prototype. Another version-gated,
 * consented integration component must discover it within Yandex.
 */
export function createNativeResourceAdapter({ resolve, allowedOrigin, now = Date.now, deadlineMs = DEFAULT_DEADLINE_MS }) {
  if (typeof resolve !== 'function' ||
      !(typeof allowedOrigin === 'string' || typeof allowedOrigin === 'function') ||
      !Number.isInteger(deadlineMs) || deadlineMs < 10 || deadlineMs > 8000)
    throw new TypeError('W22_BAD_ADAPTER_CONTRACT');

  let enabled = false, disposed = false, revision = 0, current = null;
  let prototype = null, originalSingle = null, originalBatch = null;
  let ownSingle = null, ownBatch = null;
  const pending = new Map();
  const cache = new Map();
  let status = 'OFF';

  function cancel() {
    revision++;
    for (const op of pending.values()) op.abort.abort();
    pending.clear();
  }
  function removeCache() { cache.clear(); }
  function trackChanged(raw) {
    if (disposed) return;
    const id = validId(raw);
    if (current !== id) {
      current = id;
      cancel();
      status = enabled ? 'ORIGINAL' : 'OFF';
    }
  }
  function enable() {
    if (disposed) return;
    if (!enabled) { enabled = true; cancel(); status = 'ORIGINAL'; }
  }
  function disable() {
    if (disposed) return;
    enabled = false;
    cancel(); removeCache(); status = 'OFF';
  }
  function original() { disable(); }

  function fromCache(id) {
    const entry = cache.get(id);
    if (!entry) return undefined;
    if (entry.until <= now()) { cache.delete(id); return undefined; }
    return entry.grant;
  }
  function setCache(id, grant) {
    if (cache.size >= MAX_CACHE) cache.delete(cache.keys().next().value);
    cache.set(id, {
      grant,
      until: grant ? grant.expiresAt - POSITIVE_SAFETY_MS : now() + NEGATIVE_TTL_MS
    });
  }
  async function lookup(id, revisionAtStart) {
    if (!enabled || disposed || revisionAtStart !== revision) return null;
    const cached = fromCache(id);
    if (cached !== undefined) return cached;
    let job = pending.get(id);
    if (!job) {
      const abort = new AbortController();
      let timer;
      const timeout = new Promise(resolveTimeout => {
        timer = setTimeout(() => { abort.abort(); resolveTimeout(null); }, deadlineMs);
      });
      const request = Promise.resolve().then(() => resolve(id, abort.signal))
        .catch(() => null);
      const cancelled = new Promise(resolveCancelled => {
        abort.signal.addEventListener('abort', () => resolveCancelled(null), { once: true });
      });
      const promise = Promise.race([request, timeout, cancelled]).then(grant => {
        const origin = typeof allowedOrigin === 'function' ? allowedOrigin() : allowedOrigin;
        const validated = validateCelikomGrant(grant, id, origin, now());
        if (!abort.signal.aborted && enabled && !disposed && revision === revisionAtStart)
          setCache(id, validated && (grant.mimeType === 'audio/mpeg' || grant.mimeType === 'audio/mp4')
            ? { ...grant, signedUrl: validated } : null);
        return fromCache(id) ?? null;
      }).finally(() => {
        clearTimeout(timer);
        if (pending.get(id)?.promise === promise) pending.delete(id);
      });
      job = { promise, abort };
      pending.set(id, job);
    }
    return job.promise;
  }

  async function prime(rawTrackId) {
    const id = validId(rawTrackId);
    if (!id || !enabled || disposed) return false;
    const rev = revision;
    const grant = await lookup(id, rev);
    return !!(grant && enabled && !disposed && rev === revision);
  }
  function isLive(id, rev) {
    return enabled && !disposed && revision === rev && current === id;
  }
  function attach(proto) {
    if (disposed || prototype || !proto || typeof proto.getFileInfo !== 'function')
      throw new Error('W22_UNSUPPORTED_RESOURCE');
    prototype = proto;
    originalSingle = proto.getFileInfo;
    originalBatch = typeof proto.getFileInfoBatch === 'function' ? proto.getFileInfoBatch : null;

    ownSingle = async function (params, ...rest) {
      const id = validId(params?.trackId);
      if (!enabled || !id || disposed) return originalSingle.call(this, params, ...rest);
      if (id !== current) trackChanged(id);
      const rev = revision;
      const native = Promise.resolve().then(() => originalSingle.call(this, params, ...rest))
        .then(value => ({ value }), error => ({ error }));
      const grant = await lookup(id, rev);
      const base = await native;
      if (!grant || !isLive(id, rev)) {
        if (rev === revision) status = enabled ? 'ORIGINAL' : 'OFF';
        if ('error' in base) throw base.error;
        return base.value;
      }
      const field = base.value && 'fileInfo' in base.value ? 'fileInfo' : 'downloadInfo';
      const replacement = toDownloadInfo(base.value?.[field], id, grant.signedUrl, grant.mimeType, params?.quality);
      status = 'SOURCE_MAPPING_RETURNED_NOT_AUDIO_VERIFIED';
      return { ...base.value, [field]: replacement };
    };
    proto.getFileInfo = ownSingle;

    if (originalBatch) {
      ownBatch = async function (params, ...rest) {
        // Batch remains instant: only already-prefetched grants, no network.
        const raw = Array.isArray(params?.trackIds)
          ? params.trackIds : typeof params?.trackIds === 'string' ? params.trackIds.split(',') : [];
        const ids = raw.map(validId).filter(Boolean);
        const hits = ids.map(id => [id, fromCache(id)]).filter(([, g]) => !!g);
        if (!enabled || disposed || !hits.length) return originalBatch.call(this, params, ...rest);
        const rev = revision;
        const base = await originalBatch.call(this, params, ...rest);
        if (!enabled || disposed || rev !== revision) return base;
        const field = base && 'fileInfos' in base ? 'fileInfos' : 'downloadInfos';
        const list = Array.isArray(base?.[field]) ? [...base[field]] : [];
        for (const [id, grant] of hits) {
          if (!isLive(id, rev) || fromCache(id) !== grant) continue;
          const index = list.findIndex(x => x && validId(x.trackId) === id);
          const info = toDownloadInfo(index >= 0 ? list[index] : null,
            id, grant.signedUrl, grant.mimeType, params?.quality);
          if (index >= 0) list[index] = info; else list.push(info);
        }
        return { ...base, [field]: list };
      };
      proto.getFileInfoBatch = ownBatch;
    }
    return adapter;
  }
  function dispose() {
    if (disposed) return;
    disable(); disposed = true;
    if (prototype) {
      if (prototype.getFileInfo === ownSingle) prototype.getFileInfo = originalSingle;
      if (originalBatch && prototype.getFileInfoBatch === ownBatch)
        prototype.getFileInfoBatch = originalBatch;
    }
    prototype = null;
  }
  const adapter = Object.freeze({ attach, prime, enable, disable, original,
    trackChanged, dispose,
    get status() { return status; },
    get enabled() { return enabled && !disposed; }
  });
  return adapter;
}
