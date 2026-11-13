/**
 * CELIKOM W22: independent source-only adapter for Yandex renderer file-info.
 * Does not patch/launch Yandex. Requires a separately approved host adapter.
 * Resource response research: MIT https://github.com/S4YN3X/FkCensor
 * Uses CELIKOM's own grant validator, NOT PulseSync Client or GPL SDK.
 */
import { exactTrackId, validateCelikomGrant } from '../w15/source-controller.mjs';

const DEFAULT_DEADLINE_MS = 1250;
// Only background recovery can take longer; foreground Next never stalls.
const RECOVERY_DEADLINE_MS = 4500;
const NEGATIVE_TTL_MS = 3000;
const POSITIVE_SAFETY_MS = 12000;
const MAX_CACHE = 24;

function validId(raw) {
  const id = typeof raw === 'number' && Number.isSafeInteger(raw)
    ? String(raw) : typeof raw === 'string' ? raw : '';
  return exactTrackId({ id });
}
// W48 read-only structure witness. Never export field contents, URLs,
// ciphertext, crypto material, Yandex metadata, or signed CELIKOM grants.
// Static shape hints do not prove the native decoder accepted the source.
function observeOriginalFileInfo(info, emit, id) {
  if (!info || typeof info !== 'object' || Array.isArray(info)) return;
  if (Object.prototype.hasOwnProperty.call(info, 'key'))
    emit('FILEINFO_NATIVE_KEY_FIELD', id);
  if (Object.prototype.hasOwnProperty.call(info, 'iv'))
    emit('FILEINFO_NATIVE_IV_FIELD', id);
  if (Object.prototype.hasOwnProperty.call(info, 'transport'))
    emit('FILEINFO_NATIVE_TRANSPORT_FIELD', id);
  if (Object.prototype.hasOwnProperty.call(info, 'urls'))
    emit(Array.isArray(info.urls) ? 'FILEINFO_NATIVE_URLS_ARRAY' : 'FILEINFO_NATIVE_URLS_OTHER', id);
  if (typeof info.codec === 'string') {
    const c = info.codec.trim().toLowerCase();
    emit(c === 'mp3' || c === 'mpeg' ? 'FILEINFO_NATIVE_CODEC_MP3' :
      c.startsWith('aac') || c.startsWith('mp4a') ? 'FILEINFO_NATIVE_CODEC_AAC' :
      'FILEINFO_NATIVE_CODEC_OTHER', id);
  }
}

// W56: Yandex's DownloadInfoSource.src appends "?vsid=...&source_index=..."
// to urls[0] even when it already contains CELIKOM's signed query. Without
// an inert trailing field that becomes "sid=7?vsid=...", which fails PHP's
// strict SID/HMAC checks. Attach this ONLY to an already-validated native
// playback URL; NEVER alter the grant, signer, native renderer or PHP checks.
// Any Yandex-appended "?..." is swallowed by this ignored field's value,
// while token/expires/sid remain exactly as issued. Ordinary Yandex source
// links are not touched.
const NATIVE_SIGNED_QUERY_GUARD = "celikom_native_query_guard=0";
function nativePlaybackUrl(validatedSignedUrl) {
  if (typeof validatedSignedUrl !== "string" ||
      !validatedSignedUrl.startsWith("https://") ||
      !validatedSignedUrl.includes("?token=") ||
      !validatedSignedUrl.includes("&expires=") ||
      validatedSignedUrl.includes("#") ||
      validatedSignedUrl.includes("celikom_native_query_guard")) {
    throw new TypeError("W56_UNVALIDATED_SIGNED_SOURCE");
  }
  return validatedSignedUrl + "&" + NATIVE_SIGNED_QUERY_GUARD;
}

function toDownloadInfo(original, trackId, url, mimeType, quality) {
  const mediaUrl = nativePlaybackUrl(url);
  const result = { ...(original && typeof original === 'object' && !('error' in original) ? original : {}) };
  delete result.key;
  delete result.iv;
  // Keep Yandex's player/clock/queue/transport controls; replace source only.
  return {
    ...result, trackId, realId: trackId,
    codec: mimeType === 'audio/mp4' ? 'aac-mp4' : 'mp3',
    transport: 'raw', quality: result.quality || quality || 'nq',
    // A replaced MP3 must not retain the native AAC stream's reported
    // bitrate. Keep the same nominal MP3-320 contract as F_ckCensor (MIT).
    // This is a compatibility experiment; owner audio remains UNVERIFIED.
    gain: false, bitrate: mimeType === 'audio/mpeg' ? 320
      : (Number.isFinite(result.bitrate) && result.bitrate > 0) ? result.bitrate : undefined,
    urls: [mediaUrl], url: mediaUrl
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
  const mappedTracks = new Set();
  const sourceClassifications = new Map();
  let status = 'OFF';
  function emit(code, id = null) {
    try { onEvent(code, id); } catch { /* Diagnostics must never block the player. */ }
  }
  function setClassification(id, classification) {
    if (!id) return;
    if (sourceClassifications.size >= MAX_CACHE && !sourceClassifications.has(id))
      sourceClassifications.delete(sourceClassifications.keys().next().value);
    sourceClassifications.delete(id);
    sourceClassifications.set(id, classification);
  }
  function markMapped(id) {
    if (!id) return;
    if (mappedTracks.size >= MAX_CACHE && !mappedTracks.has(id))
      mappedTracks.delete(mappedTracks.values().next().value);
    mappedTracks.delete(id);
    mappedTracks.add(id);
  }
  function hasMappedTrack(raw) {
    const id = validId(raw);
    return !!id && mappedTracks.has(id);
  }
  function forgetMappedTrack(raw) {
    const id = validId(raw);
    if (id) mappedTracks.delete(id);
  }
  function classificationForTrack(raw) {
    const id = validId(raw);
    return id ? sourceClassifications.get(id) || 'UNKNOWN' : 'UNKNOWN';
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
  async function lookup(id, revisionAtStart, background = false) {
    if (!enabled || disposed || revisionAtStart !== revision) return null;
    const cached = fromCache(id);
    if (cached !== undefined) {
      setClassification(id, cached ? 'ACTIVE_REPLACEMENT_CANDIDATE' : 'ORIGINAL');
      emit('CACHE_HIT', id);
      return cached;
    }
    let job = pending.get(id);
    if (!job) {
      emit('RESOLVE_START', id);
      const abort = new AbortController();
      let timer;
      const timeout = new Promise(resolveTimeout => {
        timer = setTimeout(() => {
          emit(background ? 'RESOLVE_BACKGROUND_TIMEOUT' : 'RESOLVE_TIMEOUT', id);
          abort.abort(); resolveTimeout(null);
        }, background ? RECOVERY_DEADLINE_MS : deadlineMs);
      });
      const request = Promise.resolve().then(() => resolve(id, abort.signal, { background }))
        .catch(() => null);
      const cancelled = new Promise(resolveCancelled => {
        abort.signal.addEventListener('abort', () => resolveCancelled(null), { once: true });
      });
      const promise = Promise.race([request, timeout, cancelled]).then(grant => {
        // Temporary local timeout/502 differs from an authoritative "not found".
        // Never poison a negative cache with network failure. Schedule an
        // independently bounded current-track recovery, not a second player.
        if (!abort.signal.aborted && grant?.transient === true) {
          setClassification(id, 'UNKNOWN');
          emit(background ? 'RESOLVE_BACKGROUND_TRANSIENT' : 'RESOLVE_TRANSIENT', id);
          return null;
        }
        const origin = typeof allowedOrigin === 'function' ? allowedOrigin() : allowedOrigin;
        const validated = validateCelikomGrant(grant, id, origin, now());
        const usable = validated && (grant?.mimeType === 'audio/mpeg' || grant?.mimeType === 'audio/mp4')
          ? { ...grant, signedUrl: validated } : null;
        if (!abort.signal.aborted && enabled && !disposed && revision === revisionAtStart) {
          setCache(id, usable);
          setClassification(id, grant === null ? 'ORIGINAL' :
            usable ? 'ACTIVE_REPLACEMENT_CANDIDATE' : 'UNKNOWN');
        }
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
    const grant = await lookup(id, rev, true);
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
        if (isLive(id, rev))
          emit(classificationForTrack(id) === 'ORIGINAL' ? 'SOURCE_ORIGINAL' : 'SOURCE_UNKNOWN', id);
        const base = await native;
        if (rev === revision) status = enabled ? 'ORIGINAL' : 'OFF';
        if ('error' in base) throw base.error;
        return base.value;
      }
      // Never fabricate metadata: owner W28 shows late genuine Yandex responses
      // arriving after the old 130 ms synthetic-response cutoff.
      const watch = setTimeout(() => emit('NATIVE_FILEINFO_WAIT', id), 130);
      const base = await native;
      clearTimeout(watch);
      if ('error' in base) throw base.error;
      if (!isLive(id, rev)) return base.value;
      const value = base.value;
      if (!value || typeof value !== 'object' || Array.isArray(value)) {
        emit('FILEINFO_SHAPE_MISSING', id);
        status = 'ORIGINAL';
        return value;
      }
      const field = value.fileInfo && typeof value.fileInfo === 'object'
        ? 'fileInfo' : value.downloadInfo && typeof value.downloadInfo === 'object'
          ? 'downloadInfo' : null;
      if (!field || Array.isArray(value[field])) {
        emit('FILEINFO_SHAPE_MISSING', id);
        status = 'ORIGINAL';
        return value;
      }
      emit(field === 'fileInfo' ? 'FILEINFO_SHAPE_FILE' : 'FILEINFO_SHAPE_DOWNLOAD', id);
      observeOriginalFileInfo(value[field], emit, id);
      const replacement = toDownloadInfo(value[field], id, grant.signedUrl, grant.mimeType, params?.quality);
      markMapped(id);
      setClassification(id, 'ACTIVE_REPLACEMENT');
      emit('SOURCE_ACTIVE_REPLACEMENT', id);
      // Preserve Yandex native player: same decoder, URL-only replacement.
      // gainApplied reflects a verified offline server-render, NOT an in-process
      // DSP claim. Never set native boolean 'gain' to numeric admin dB.
      if (Number.isFinite(grant.gainDb) && grant.gainDb >= -12 &&
          grant.gainDb <= 12 && grant.gainDb !== 0)
        emit(grant.gainApplied === true ? 'GAIN_OFFLINE_VARIANT_MAPPED' :
          'GAIN_CONFIGURED_NATIVE_DSP_NOT_APPLIED', id);
      emit('SOURCE_MAPPED', id);
      status = 'SOURCE_MAPPING_RETURNED_NOT_AUDIO_VERIFIED';
      return { ...value, [field]: replacement };
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
          for (const id of selected)
            emit(classificationForTrack(id) === 'ORIGINAL' ? 'SOURCE_ORIGINAL' : 'SOURCE_UNKNOWN', id);
          if ('error' in result) throw result.error;
          return result.value;
        }
        // Never create imaginary official file-info batches or append missing IDs.
        if ('error' in result) {
          emit('BATCH_FILEINFO_ERROR', hits[0]?.[0] || null);
          throw result.error;
        }
        const base = result.value;
        if (!base || typeof base !== 'object' || Array.isArray(base)) {
          emit('SOURCE_BATCH_ORIGINAL', hits[0]?.[0] || null);
          return base;
        }
        const field = Array.isArray(base.fileInfos) ? 'fileInfos'
          : Array.isArray(base.downloadInfos) ? 'downloadInfos' : null;
        if (!field) {
          emit('SOURCE_BATCH_ORIGINAL', hits[0]?.[0] || null);
          return base;
        }
        const list = [...base[field]];
        let mapped = false;
        for (const [id, grant] of hits) {
          const index = list.findIndex(x => x && validId(x.trackId) === id);
          if (index < 0 || !list[index] || typeof list[index] !== 'object') continue;
          observeOriginalFileInfo(list[index], emit, id);
          list[index] = toDownloadInfo(list[index],
            id, grant.signedUrl, grant.mimeType, params?.quality);
          markMapped(id);
          setClassification(id, 'ACTIVE_REPLACEMENT');
          emit('SOURCE_ACTIVE_REPLACEMENT', id);
          mapped = true;
        }
        if (!mapped) {
          emit('SOURCE_BATCH_ORIGINAL', hits[0]?.[0] || null);
          return base;
        }
        for (const [id, grant] of hits) {
          if (Number.isFinite(grant.gainDb) && grant.gainDb >= -12 &&
              grant.gainDb <= 12 && grant.gainDb !== 0)
            emit(grant.gainApplied === true ? 'GAIN_OFFLINE_VARIANT_MAPPED' :
              'GAIN_CONFIGURED_NATIVE_DSP_NOT_APPLIED', id);
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
    mappedTracks.clear();
    sourceClassifications.clear();
    if (prototype) {
      if (prototype.getFileInfo === ownSingle) prototype.getFileInfo = originalSingle;
      if (originalBatch && prototype.getFileInfoBatch === ownBatch)
        prototype.getFileInfoBatch = originalBatch;
    }
    prototype = null;
  }
  const adapter = Object.freeze({ attach, prime, enable, disable, original,
    trackChanged, hasMappedTrack, forgetMappedTrack, classificationForTrack, dispose,
    get status() { return status; },
    get enabled() { return enabled && !disposed; }
  });
  return adapter;
}
