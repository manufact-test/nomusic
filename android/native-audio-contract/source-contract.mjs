/**
 * CELIKOM Android A1 issue #42 — source-choice contract, NOT a player or hook.
 * Pure ESM, no Android/Yandex/HTTP imports. All callbacks supplied by an
 * authorized integration adapter. Native decoder and playback clock remain
 * exclusively owned by the host.
 */
const TRACK_ID = /^[1-9][0-9]{0,23}$/;
const AUDIO_PATH = /^\/api\/v1\/audio\/[1-9][0-9]{0,17}$/;
const TOKEN = /^[0-9a-f]{64}$/;
const SID = /^[1-9][0-9]{0,17}$/;
const MIME = new Set(["audio/mpeg", "audio/mp4", "audio/wav", "audio/x-wav"]);
const MAX_TTL_MS = 30 * 60_000;

function positiveId(value) {
  const text = typeof value === "number" && Number.isSafeInteger(value)
    ? String(value) : typeof value === "string" ? value : "";
  return TRACK_ID.test(text) ? text : null;
}
function validMs(value) { return Number.isSafeInteger(value) && value >= 0; }
function header(headers, key) {
  if (typeof headers?.get === "function") return headers.get(key);
  if (!headers || typeof headers !== "object") return null;
  const hit = Object.entries(headers).find(([name]) => name.toLowerCase() === key);
  return hit ? String(hit[1]) : null;
}
function isStrongEtag(value) { return /^"[^"\r\n]+"$/.test(value || ""); }
function canonicalPositiveLength(value) {
  // PHP AudioController sends base-10 Content-Length. Avoid interpreting
  // exponent/hex/whitespace/leading-zero text that the real server never emits.
  if (typeof value !== "string" || !/^[1-9][0-9]*$/.test(value)) return null;
  const number = Number(value);
  return Number.isSafeInteger(number) && number > 0 ? number : null;
}
function normalizedTrack(raw) {
  const trackId = positiveId(raw?.trackId);
  if (!trackId || !Number.isSafeInteger(raw?.durationMs) || raw.durationMs <= 0)
    return null;
  const albumId = raw.albumId == null ? null : positiveId(raw.albumId);
  // Host identity is an *opaque exact string*. Never coerce an object, a
  // number or a custom toString() value into a trusted native edition ID.
  // Control characters are not a valid edition identity and are not safe
  // across an Android/JS host boundary.
  const editionId = raw.editionId == null ? null : raw.editionId;
  if ((raw.albumId != null && !albumId) ||
      (editionId !== null &&
        (typeof editionId !== "string" || editionId.length < 1 ||
         editionId.length > 128 || /[\x00-\x1f\x7f]/.test(editionId))))
    return null;
  const replacementVersion = raw.replacementVersion == null ? null : raw.replacementVersion;
  if (replacementVersion !== null && (!Number.isSafeInteger(replacementVersion) || replacementVersion < 1))
    return null;
  return {
    trackId, albumId, editionId, replacementVersion,
    durationMs: raw.durationMs,
    paused: raw.paused === true,
    positionMs: validMs(raw.positionMs) ? Math.min(raw.positionMs, raw.durationMs) : 0
  };
}

/**
 * Caller MUST supply an authenticated, server-entitlement-checked normalized
 * grant. Actual PHP ResolveService returns found/audio_url/duration_ms/
 * mime_type/version/expires_at; see task doc for trusted adapter mapping.
 * Never rely on matching song title/artist/cover as identity.
 */
export function validateGrant(raw, track, origin, nowMs, safetyMs = 30_000, durationToleranceMs = 2_000) {
  // A track ID alone may refer to several editions in the native player.
  // If the host cannot attest both exact album and edition, never turn a
  // server track-level resolve into a purportedly selected native source.
  if (!track?.albumId || !track?.editionId ||
      !raw?.albumId || !raw?.editionId) return null;
  if (!raw || !track || raw.trackId !== track.trackId ||
      raw.approved !== true || raw.entitled !== true ||
      !Number.isSafeInteger(raw.version) || raw.version < 1 ||
      (track.replacementVersion != null && raw.version !== track.replacementVersion) ||
      !Number.isSafeInteger(raw.durationMs) || raw.durationMs <= 0 ||
      Math.abs(raw.durationMs - track.durationMs) > durationToleranceMs ||
      !MIME.has(raw.mimeType) || typeof raw.audioUrl !== "string" ||
      !Number.isSafeInteger(raw.expiresAt) ||
      raw.expiresAt <= nowMs + safetyMs || raw.expiresAt > nowMs + MAX_TTL_MS)
    return null;

  // Exact edition and album must be attested by the catalog adapter when
  // present in the host snapshot; current PHP resolve does not return these.
  if ((track.albumId !== null && raw.albumId !== track.albumId) ||
      (track.editionId !== null && raw.editionId !== track.editionId))
    return null;

  try {
    const base = new URL(origin);
    const url = new URL(raw.audioUrl);
    if (base.protocol !== "https:" || base.pathname !== "/" || base.search ||
        base.hash || base.username || base.password ||
        url.protocol !== "https:" || url.origin !== base.origin ||
        url.username || url.password || url.hash || !AUDIO_PATH.test(url.pathname))
      return null;
    const keys = [...url.searchParams.keys()];
    if (keys.length !== 3 || new Set(keys).size !== 3 ||
        keys.some(k => !["token", "expires", "sid"].includes(k)) ||
        !TOKEN.test(url.searchParams.get("token") || "") ||
        !SID.test(url.searchParams.get("sid") || "") ||
        !/^[0-9]{9,12}$/.test(url.searchParams.get("expires") || "") ||
        Number(url.searchParams.get("expires")) * 1000 !== raw.expiresAt)
      return null;
    return Object.freeze({
      url: url.href, expiresAt: raw.expiresAt, version: raw.version,
      mimeType: raw.mimeType, durationMs: raw.durationMs
    });
  } catch { return null; }
}

/** PHP AudioController returns HEAD 200, accepts only single GET byte ranges. */
export function validateHeadResponse(response, expectedMime) {
  const h = response?.headers;
  const size = canonicalPositiveLength(header(h, "content-length"));
  const etag = header(h, "etag");
  if (response?.status !== 200 || !MIME.has(expectedMime) ||
      header(h, "content-type") !== expectedMime ||
      header(h, "accept-ranges")?.toLowerCase() !== "bytes" ||
      size === null || !isStrongEtag(etag))
    return null;
  return Object.freeze({ size, etag, mimeType: expectedMime });
}

/** Only a native host may convert a seek position into a known byte offset. */
export function buildByteRangeHeaders(start, end = null, etag = null) {
  if (!validMs(start) || (end !== null && (!validMs(end) || end < start)) ||
      (etag !== null && !isStrongEtag(etag)))
    throw new TypeError("INVALID_BYTE_RANGE");
  const headers = { Range: "bytes=" + start + "-" + (end === null ? "" : end) };
  if (etag !== null) headers["If-Range"] = etag;
  return Object.freeze(headers);
}
export function validateRangeResponse(response, start, requestedEnd = null, expected = null) {
  if (!validMs(start) || (requestedEnd !== null && (!validMs(requestedEnd) || requestedEnd < start)))
    return Object.freeze({ ok: false, code: "INVALID_RANGE" });
  // Seek/range is only valid against a previously verified immutable HEAD.
  // Without it, a valid-looking 206 from another version must fail closed.
  if (!expected || !Number.isSafeInteger(expected.size) || expected.size <= 0 ||
      !isStrongEtag(expected.etag) ||
      !MIME.has(expected.mimeType))
    return Object.freeze({ ok: false, code: "HEAD_WITNESS_REQUIRED" });
  const h = response?.headers;
  const range = header(h, "content-range");
  if (response?.status === 416) {
    const match = /^bytes \*\/([1-9][0-9]*)$/.exec(range || "");
    if (!match) return Object.freeze({ ok: false, code: "INVALID_416" });
    const total = Number(match[1]);
    if (!Number.isSafeInteger(total) || total !== expected.size || start < total)
      return Object.freeze({ ok: false, code: "RANGE_MISMATCH" });
    return Object.freeze({ ok: false, code: "RANGE_UNSATISFIABLE" });
  }
  if (response?.status !== 206) return Object.freeze({ ok: false, code: "RANGE_NOT_PARTIAL" });
  const parts = /^bytes ([0-9]+)-([0-9]+)\/([1-9][0-9]*)$/.exec(range || "");
  if (!parts) return Object.freeze({ ok: false, code: "INVALID_CONTENT_RANGE" });
  const begin = Number(parts[1]), end = Number(parts[2]), total = Number(parts[3]);
  const length = canonicalPositiveLength(header(h, "content-length"));
  const etag = header(h, "etag");
  const mime = header(h, "content-type");
  // A valid Range may still be a content-negotiation/redirect mistake.
  // The same decoder must not receive a different MIME than verified HEAD.
  // Match the actual unchanged PHP AudioController's Content-Type exactly.
  // ByteRange::parse on CELIKOM PHP returns the full requested inclusive
  // end (capped to EOF), never an arbitrarily truncated 206. Detect short
  // responses now, before handing them to the single native decoder.
  const expectedEnd = requestedEnd === null ? expected.size - 1
    : Math.min(requestedEnd, expected.size - 1);
  if (![begin, end, total].every(Number.isSafeInteger) ||
      begin !== start || end < begin || end >= total ||
      end !== expectedEnd ||
      length !== end - begin + 1 ||
      total !== expected.size || etag !== expected.etag ||
      mime !== expected.mimeType)
    return Object.freeze({ ok: false, code: "RANGE_MISMATCH" });
  return Object.freeze({ ok: true, start: begin, end, total });
}

export function createAudioSourceContract({
  origin, resolve, probeHead, now = Date.now,
  deadlineMs = 1250, safetyMs = 30_000, durationToleranceMs = 2_000,
  setTimer = setTimeout, clearTimer = clearTimeout, onEvent = () => {}
}) {
  if (typeof origin !== "string" || typeof resolve !== "function" ||
      typeof probeHead !== "function" || typeof now !== "function" ||
      typeof setTimer !== "function" || typeof clearTimer !== "function" ||
      !Number.isSafeInteger(deadlineMs) || deadlineMs < 1 || deadlineMs > 8000 ||
      !Number.isSafeInteger(safetyMs) || safetyMs < 0 || safetyMs > 120_000 ||
      !Number.isSafeInteger(durationToleranceMs) ||
      durationToleranceMs < 0 || durationToleranceMs > 10_000) {
    throw new TypeError("INVALID_SOURCE_CONTRACT");
  }
  // Reject invalid origin before any request.
  try {
    const base = new URL(origin);
    if (base.protocol !== "https:" || base.pathname !== "/" ||
        base.search || base.hash || base.username || base.password)
      throw new Error("bad origin");
  } catch { throw new TypeError("INVALID_AUDIO_ORIGIN"); }

  let generation = 0, requestSeq = 0, track = null, enabled = false;
  let forcedOriginal = false, disposed = false, pending = null, state = "OFF";
  // Only decisions issued by THIS instance may be applied, once.
  const issuedTickets = new WeakSet();
  const consumedTickets = new WeakSet();
  function note(code) {
    // Diagnostics deliberately receive ONLY enumerated codes, never IDs,
    // signed URLs, transport secrets or exception messages.
    try { onEvent(code); } catch { /* optional diagnostics */ }
  }
  function invalidate() {
    generation++;
    requestSeq++;
    pending?.abort();
    pending = null;
  }
  function current(g, seq) {
    return !disposed && generation === g && requestSeq === seq;
  }
  function choice(action, code, g = generation, seq = requestSeq, more = {}) {
    const ticket = Object.freeze({
      action, code, generation: g, requestSeq: seq, ...more
    });
    issuedTickets.add(ticket);
    return ticket;
  }
  function original(code) {
    state = enabled && !disposed ? "ORIGINAL" : "OFF";
    note(code);
    return choice("ORIGINAL", code);
  }
  function observeTrack(raw, reason = "TRACK_CHANGED") {
    if (disposed) return false;
    invalidate();
    track = normalizedTrack(raw);
    forcedOriginal = false;
    state = enabled ? "ORIGINAL" : "OFF";
    note(track ? (reason === "MY_WAVE" ? "MY_WAVE" : reason === "NEXT" ? "NEXT" : "TRACK_CHANGED") : "IDENTITY_UNKNOWN");
    return !!track;
  }
  function next(raw) { return observeTrack(raw, "NEXT"); }
  function myWave(raw) { return observeTrack(raw, "MY_WAVE"); }
  function transport({ paused, positionMs } = {}) {
    if (disposed || !track) return;
    if (typeof paused === "boolean") track.paused = paused;
    if (validMs(positionMs)) track.positionMs = Math.min(positionMs, track.durationMs);
  }
  function pause() { transport({ paused: true }); }
  function resume() { transport({ paused: false }); }
  function seek(positionMs) { transport({ positionMs }); }
  function enable() {
    if (disposed || (enabled && !forcedOriginal)) return;
    invalidate(); enabled = true; forcedOriginal = false;
    state = "ORIGINAL"; note("ENABLED_REEVALUATE_CURRENT");
  }
  function disable() {
    if (disposed || !enabled) return;
    invalidate(); enabled = false; forcedOriginal = false;
    state = "OFF"; note("DISABLED_RELOAD_ORIGINAL");
  }
  function preferOriginal() {
    if (disposed) return;
    invalidate(); forcedOriginal = true;
    state = enabled ? "ORIGINAL" : "OFF"; note("FORCED_ORIGINAL");
  }
  function ended() {
    if (disposed) return;
    invalidate(); track = null;
    state = enabled ? "ORIGINAL" : "OFF"; note("TRACK_ENDED");
  }
  function dispose() {
    if (disposed) return;
    invalidate(); enabled = false; track = null; disposed = true;
    state = "OFF"; note("DISPOSED");
  }
  async function requestSource() {
    if (disposed) return choice("IGNORE", "DISPOSED");
    if (!enabled || forcedOriginal || !track ||
        track.albumId === null || track.editionId === null)
      return original(!enabled ? "DISABLED_ORIGINAL" : "NO_IDENTITY_OR_ORIGINAL");
    // New request supersedes an older one even on the same track.
    requestSeq++;
    pending?.abort();
    const seq = requestSeq, g = generation;
    const captured = { ...track };
    const abort = new AbortController();
    pending = abort;
    state = "RESOLVING"; note("RESOLVE_START");
    let timer = null;
    const cancelled = new Promise(done => {
      abort.signal.addEventListener("abort", () => done({ cancelled: true }), { once: true });
    });
    timer = setTimer(() => abort.abort(), deadlineMs);
    const work = Promise.resolve().then(async () => {
      if (abort.signal.aborted) return { cancelled: true };
      const grant = await resolve(Object.freeze({
        trackId: captured.trackId, albumId: captured.albumId,
        editionId: captured.editionId, durationMs: captured.durationMs
      }), abort.signal);
      if (abort.signal.aborted) return { cancelled: true };
      const accepted = validateGrant(grant, captured, origin, now(), safetyMs, durationToleranceMs);
      if (!accepted) return { rejected: true };
      const head = await probeHead(accepted.url, abort.signal);
      if (abort.signal.aborted) return { cancelled: true };
      const verified = validateHeadResponse(head, accepted.mimeType);
      return verified ? { accepted, verified } : { rejected: true };
    }).catch(() => ({ rejected: true }));
    try {
      const result = await Promise.race([work, cancelled]);
      if (!current(g, seq)) return choice("IGNORE", "STALE_RESPONSE", g, seq);
      if (result.cancelled || result.rejected) return original(result.cancelled ? "RESOLVE_TIMEOUT" : "ORIGINAL_FALLBACK");
      // Expiry can change while HEAD is in flight. Never return stale grants.
      if (result.accepted.expiresAt <= now() + safetyMs)
        return original("GRANT_EXPIRED");
      state = "READY_NOT_APPLIED"; note("SOURCE_VALIDATED_NOT_AUDIBLE");
      return choice("REPLACEMENT", "VALIDATED_SOURCE", g, seq, {
        url: result.accepted.url, expiresAt: result.accepted.expiresAt,
        mimeType: result.accepted.mimeType, replacementVersion: result.accepted.version,
        byteLength: result.verified.size, etag: result.verified.etag,
        trackId: captured.trackId, albumId: captured.albumId,
        editionId: captured.editionId, positionMs: track.positionMs,
        paused: track.paused
      });
    } finally {
      clearTimer(timer);
      if (pending === abort) pending = null;
    }
  }
  function isCurrent(decision) {
    return decision !== null && typeof decision === "object" &&
      issuedTickets.has(decision) && !consumedTickets.has(decision) &&
      current(decision.generation, decision.requestSeq) &&
      (decision.action !== "REPLACEMENT" ||
        (enabled && !forcedOriginal && track?.trackId === decision.trackId &&
         track?.albumId === decision.albumId && track?.editionId === decision.editionId &&
         decision.expiresAt > now() + safetyMs));
  }
  function commit(decision, applied) {
    if (!isCurrent(decision) || decision.action === "IGNORE") return false;
    // Source application is one-shot: no double reload on repeated callback.
    consumedTickets.add(decision);
    if (decision.action === "REPLACEMENT") {
      state = applied === true ? "SOURCE_SELECTED_NOT_AUDIBLE_VERIFIED" : "ORIGINAL";
      note(applied === true ? "NATIVE_SOURCE_ACCEPTED_NOT_AUDIO_VERIFIED" : "NATIVE_SOURCE_REJECTED");
    } else {
      state = enabled ? "ORIGINAL" : "OFF";
      note("ORIGINAL_SOURCE_SELECTED");
    }
    return applied === true;
  }
  function snapshot() {
    return Object.freeze({
      state, enabled: enabled && !disposed, generation,
      trackId: track?.trackId ?? null, paused: track?.paused ?? true,
      positionMs: track?.positionMs ?? 0
    });
  }
  return Object.freeze({
    observeTrack, next, myWave, transport, pause, resume, seek,
    enable, disable, preferOriginal, ended, dispose,
    requestSource, isCurrent, commit, snapshot
  });
}
