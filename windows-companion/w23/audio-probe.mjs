// Browser-context signed-media probe. Does not alter Yandex's player or
// media APIs; only GETs <=32 initial bytes of at most four approved sources.
// Never exports URLs, session identifiers, headers or media bytes.
export function createSignedAudioProbe({
  getOrigin, fetcher, onEvent = () => {}, timer = setTimeout,
  clearTimer = clearTimeout, maxTracks = 4
}) {
  const seen = new Set();
  function emit(code, trackId) {
    try { onEvent(code, trackId); } catch {}
  }
  async function run(source, rawTrackId) {
    const id = typeof rawTrackId === 'string' && /^[1-9][0-9]{0,17}$/.test(rawTrackId)
      ? rawTrackId : null;
    if (!id || seen.has(id) || seen.size >= maxTracks) return;
    let parsed;
    try {
      parsed = new URL(source);
      if (parsed.protocol !== 'https:' || parsed.origin !== getOrigin() ||
          !/^\/api\/v1\/audio\/[1-9][0-9]{0,17}$/.test(parsed.pathname) ||
          !/^[a-f0-9]{64}$/.test(parsed.searchParams.get('token') || '') ||
          !/^[0-9]{9,12}$/.test(parsed.searchParams.get('expires') || '')) return;
    } catch { return; }
    seen.add(id);
    if (typeof fetcher !== 'function') { emit('AUDIO_PROBE_UNAVAILABLE', id); return; }
    emit('AUDIO_PROBE_STARTED', id);
    const controller = new AbortController();
    let expired = false;
    const timeout = timer(() => { expired = true; controller.abort(); }, 3500);
    try {
      // This is the real Yandex renderer fetch context (CSP, CORS, proxy).
      const response = await fetcher(parsed.href, {
        method: 'GET', mode: 'cors', credentials: 'omit', redirect: 'error',
        cache: 'no-store', headers: { Range: 'bytes=0-31' },
        signal: controller.signal
      });
      const status = Number(response?.status);
      emit(status === 206 ? 'AUDIO_PROBE_HTTP_PARTIAL' :
        status === 200 ? 'AUDIO_PROBE_HTTP_FULL' :
        status === 403 ? 'AUDIO_PROBE_HTTP_FORBIDDEN' :
        status === 401 ? 'AUDIO_PROBE_HTTP_UNAUTHORIZED' :
        status === 404 ? 'AUDIO_PROBE_HTTP_NOT_FOUND' :
        'AUDIO_PROBE_HTTP_OTHER', id);
      if (status !== 200 && status !== 206) return;
      const mime = (response.headers?.get('content-type') || '').split(';')[0].trim().toLowerCase();
      emit(mime === 'audio/mpeg' ? 'AUDIO_PROBE_MIME_MPEG' :
        mime === 'audio/mp4' ? 'AUDIO_PROBE_MIME_MPFOUR' :
        'AUDIO_PROBE_MIME_OTHER', id);
      if (!response.body || typeof response.body.getReader !== 'function') {
        emit('AUDIO_PROBE_BODY_UNAVAILABLE', id); return;
      }
      const reader = response.body.getReader();
      let bytes;
      try {
        const chunk = await reader.read();
        bytes = chunk?.value instanceof Uint8Array ? chunk.value.subarray(0, 32) : new Uint8Array();
      } finally {
        try { void reader.cancel(); } catch {}
      }
      // Only safe format categories. Do not record the actual bytes.
      const mp3 = (bytes.length >= 3 && bytes[0] === 0x49 && bytes[1] === 0x44 && bytes[2] === 0x33) ||
        (bytes.length >= 2 && bytes[0] === 0xff && (bytes[1] & 0xe0) === 0xe0);
      const mp4 = bytes.length >= 8 && bytes[4] === 0x66 && bytes[5] === 0x74 &&
        bytes[6] === 0x79 && bytes[7] === 0x70;
      emit(mp3 ? 'AUDIO_PROBE_BYTES_MPTHREE' :
        mp4 ? 'AUDIO_PROBE_BYTES_MPFOUR' : 'AUDIO_PROBE_BYTES_OTHER', id);
    } catch {
      emit(expired ? 'AUDIO_PROBE_TIMEOUT' : 'AUDIO_PROBE_FETCH_BLOCKED', id);
    } finally {
      clearTimer(timeout);
      controller.abort();
    }
  }
  return Object.freeze({ run });
}
