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
    gain: false, bitrate: (Number.isFinite(result.bitrate) && result.bitrate > 0)
      ? result.bitrate : mimeType === 'audio/mpeg' ? 320 : undefined,
    urls: [url], url
  };
}

/**
 * Hooks one already-discovered resource prototype. Another version-gated,
 * consented integration component must discover it within Yandex.
 */
export function createNativeResourceAdapter({ resolve, allowedOrigin, now = Date.now,
  deadlineMs = DEFAULT_DEADLINE_MS, onEvent = () => {} }) {
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
  function emit(code, id = null) {
    try { onEvent(code, id); } catch { /* Diagnostics must never block the player. */ }
  }

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
      emit('TRACK_CHANGED', id);
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
    if (cached !== undefined) { emit('CACHE_HIT', id); return cached; }
    let job = pending.get(id);
    if (!job) {
      emit('RESOLVE_START', id);
      const abort = new AbortController();
      let timer;
      const timeout = new Promise(resolveTimeout => {
        timer = setTimeout(() => { emit('RESOLVE_TIMEOUT', id); abort.abort(); resolveTimeout(null); }, deadlineMs);
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
      emit('NATIVE_FILEINFO_REQUEST', id);
      const rev = revision;
      const native = Promise.resolve().then(() => originalSingle.call(this, params, ...rest))
        .then(value => { emit('NATIVE_FILEINFO_OK', id); return { value }; },
              error => { emit('NATIVE_FILEINFO_ERROR', id); return { error }; });
      const grant = await lookup(id, rev);
      if (!grant || !isLive(id, rev)) {
        emit('SOURCE_ORIGINAL', id);
        const base = await native;
        if (rev === revision) status = enabled ? 'ORIGINAL' : 'OFF';
        if ('error' in base) throw base.error;
        return base.value;
      }
      // The approved source must not hang behind a stalled official resource.
      // Give the genuine Yandex response a short chance to supply metadata,
      // then preserve its outer response contract with only a new source.
      let graceTimer;
      const grace = new Promise(resolve => {
        graceTimer = setTimeout(() => resolve({ slow: true }), 130);
      });
      const base = await Promise.race([native, grace]);
      clearTimeout(graceTimer);
      if ('slow' in base) emit('NATIVE_FILEINFO_SLOW', id);
      if (!isLive(id, rev)) {
        const original = await native;
        if ('error' in original) throw original.error;
        return original.value;
      }
      const value = 'value' in base && base.value && typeof base.value === 'object'
        ? base.value : null;
      const field = value && 'fileInfo' in value ? 'fileInfo' : 'downloadInfo';
      emit(!value ? 'SOURCE_SYNTHETIC_RESPONSE' :
        field === 'fileInfo' ? 'FILEINFO_SHAPE_FILE' :
        value.downloadInfo ? 'FILEINFO_SHAPE_DOWNLOAD' : 'FILEINFO_SHAPE_MISSING', id);
      const replacement = toDownloadInfo(value?.[field], id, grant.signedUrl, grant.mimeType, params?.quality);
      emit('SOURCE_MAPPED', id);
      status = 'SOURCE_MAPPING_RETURNED_NOT_AUDIO_VERIFIED';
      return { responseTime: 0, url: '', ...value, [field]: replacement };
    };
    proto.getFileInfo = ownSingle;

    if (originalBatch) {
      ownBatch = async function (params, ...rest) {
        const raw = Array.isArray(params?.trackIds)
          ? params.trackIds : typeof params?.trackIds === 'string' ? params.trackIds.split(',') : [];
        const ids = [...new Set(raw.map(validId).filter(Boolean))];
        if (!enabled || disposed || ids.length === 0) return originalBatch.call(this, params, ...rest);
        emit('SOURCE_BATCH_REQUEST', ids[0]);
        const rev = revision;
        // Batch is often requested BEFORE any single file-info. Resolve a small
        // bounded window to avoid falling back for every playlist/Next request.
        // Continue requesting Yandex's own response in parallel.
        const native = Promise.resolve().then(() => originalBatch.call(this, params, ...rest))
          .then(value => ({ value }), error => ({ error }));
        const preferred = current && ids.includes(current) ? [current] : [];
        const selected = [...new Set([...preferred, ...ids])].slice(0, 3);
        const results = await Promise.all(selected.map(async id => [id, await lookup(id, rev)]));
        const result = await native;
        if (!enabled || disposed || revision !== rev) {
          if ('error' in result) throw result.error;
          return result.value;
        }
        const hits = results.filter(([id, grant]) => !!grant && ids.includes(id) &&
          fromCache(id) === grant);
        if (hits.length === 0) {
          if ('error' in result) throw result.error;
          return result.value;
        }
        const base = 'error' in result ? {} : result.value;
        const field = base && 'fileInfos' in base ? 'fileInfos' : 'downloadInfos';
        const list = Array.isArray(base?.[field]) ? [...base[field]] : [];
        for (const [id, grant] of hits) {
          const index = list.findIndex(x => x && validId(x.trackId) === id);
          const info = toDownloadInfo(index >= 0 ? list[index] : null,
            id, grant.signedUrl, grant.mimeType, params?.quality);
          if (index >= 0) list[index] = info; else list.push(info);
        }
        emit('SOURCE_BATCH_MAPPED', hits[0]?.[0] || null);
        status = 'SOURCE_MAPPING_RETURNED_NOT_AUDIO_VERIFIED';
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
