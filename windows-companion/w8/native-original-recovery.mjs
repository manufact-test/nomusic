/**
 * W8 -- single-decoder original recovery contract.
 * No audio player is created. The owner (Yandex in a future approved
 * integration) supplies a native element/source setter and a source resolver.
 * Only the already selected active track may be recovered, at most once.
 */
const trackId = value => /^\d{1,20}$/.test(String(value)) ? String(value) : null;
const status = (value) => Object.freeze({ status: value });

export function createNativeOriginalRecovery({
  sourceGate, reacquireOriginal, applyToSameDecoder
}) {
  if (!sourceGate || typeof sourceGate.original !== "function" ||
      typeof reacquireOriginal !== "function" ||
      typeof applyToSameDecoder !== "function")
    throw Error("W8_INVALID_DEPENDENCIES");

  let current = null, generation = 0, attempted = false;
  let disposed = false, stopped = false;
  let restoring = false;
  let successful = 0, ignored = 0, failures = 0;

  const currentIs = (id, epoch) =>
    !disposed && !stopped && current === id && generation === epoch;

  const api = {
    setTrack(value) {
      if (disposed || stopped) throw Error("W8_INACTIVE");
      const id = trackId(value);
      if (!id) throw Error("W8_INVALID_TRACK");
      if (id !== current) {
        current = id;
        ++generation;
        attempted = false;
        restoring = false;
      }
      return generation;
    },
    async onNativeDecodeError(value, snapshot = {}) {
      const id = trackId(value);
      if (disposed) { ignored++; return status("DISPOSED"); }
      if (stopped) { ignored++; return status("STOPPED"); }
      if (!id || current !== id) { ignored++; return status("STALE_TRACK"); }
      if (attempted || restoring) { ignored++; return status("ALREADY_ATTEMPTED"); }
      if (!Number.isFinite(snapshot.positionSec) || snapshot.positionSec < 0 ||
          snapshot.positionSec > 7200 || typeof snapshot.wasPlaying !== "boolean") {
        ignored++; return status("INVALID_SNAPSHOT");
      }

      const epoch = generation;
      attempted = true; restoring = true; // one-shot per track, no retry storm
      try {
        // Change admission decision before issuing any fresh resource request.
        sourceGate.original();
        const original = await reacquireOriginal(id);
        if (!currentIs(id, epoch)) { ignored++; return status("STALE_TRACK"); }
        if (!original || trackId(original.trackId) !== id ||
            !(typeof original.url === "string" && original.url.length > 0 ||
              Array.isArray(original.urls) && original.urls.some(x => typeof x === "string" && x.length > 0))) {
          failures++; return status("INVALID_ORIGINAL_DESCRIPTOR");
        }
        // applyToSameDecoder must check isCurrent right BEFORE native source
        // assignment. No background player and no automatic new elements.
        const applied = await applyToSameDecoder({
          original,
          snapshot: Object.freeze({
            positionSec: snapshot.positionSec,
            wasPlaying: snapshot.wasPlaying
          }),
          isCurrent: () => currentIs(id, epoch)
        });
        if (!currentIs(id, epoch)) { ignored++; return status("STALE_TRACK"); }
        if (applied !== true) { failures++; return status("RESTORE_FAILED"); }
        successful++;
        return status("RESTORED_ORIGINAL");
      } catch {
        failures++;
        return status("RESTORE_FAILED");
      } finally {
        if (generation === epoch) restoring = false;
      }
    },
    stop() {
      if (disposed || stopped) return;
      stopped = true;
      current = null;
      ++generation;
      sourceGate.stop?.();
    },
    dispose() {
      if (disposed) return;
      disposed = true; stopped = true;
      current = null; ++generation;
    },
    diagnostics() {
      return Object.freeze({
        currentTrackKnown: Boolean(current),
        disposed, stopped, restoring, attempted, successful, ignored, failures,
        // never include source URLs, account details, token or track name
      });
    }
  };
  return Object.freeze(api);
}
