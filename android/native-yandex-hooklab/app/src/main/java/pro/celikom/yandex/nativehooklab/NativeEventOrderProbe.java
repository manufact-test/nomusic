package pro.celikom.yandex.nativehooklab;

/**
 * Privacy-preserving temporal observation, NOT native track matching.
 * Never stores IDs, editions, source URLs, metadata, keys or audio.
 * A close FileInfo and MediaSession event can refer to different tracks
 * (radio, Next, prefetch). No verdict can authorize a source substitution.
 */
public final class NativeEventOrderProbe {
    public enum Verdict {
        SINGLE_RECENT_FILEINFO_TEMPORAL_ONLY,
        MULTIPLE_FILEINFO_AMBIGUOUS,
        METADATA_WITHOUT_RECENT_FILEINFO,
        CLOCK_DISCONTINUITY
    }

    private final long windowMs;
    private int pendingSources;
    private long firstPendingMs = -1;
    private long lastSeenMs = -1;

    private long fileInfoCallbacks;
    private long metadataCallbacks;
    private long oneSourceWindows;
    private long ambiguousWindows;
    private long noSourceWindows;
    private long clockDiscontinuities;

    public NativeEventOrderProbe(long windowMs) {
        if (windowMs < 1 || windowMs > 60000)
            throw new IllegalArgumentException("BAD_EVENT_WINDOW");
        this.windowMs = windowMs;
    }

    private boolean clockMovedBackwards(long nowMs) {
        if (nowMs < 0 || (lastSeenMs >= 0 && nowMs < lastSeenMs)) {
            clearPending();
            lastSeenMs = nowMs >= 0 ? nowMs : -1;
            clockDiscontinuities++;
            return true;
        }
        lastSeenMs = nowMs;
        return false;
    }

    private void clearPending() {
        pendingSources = 0;
        firstPendingMs = -1;
    }

    /** No DTO or request fields are read by this class. */
    public synchronized void onFileInfo(long elapsedMs) {
        if (clockMovedBackwards(elapsedMs)) return;
        fileInfoCallbacks++;
        if (pendingSources == 0 || elapsedMs - firstPendingMs > windowMs) {
            pendingSources = 1;
            firstPendingMs = elapsedMs;
        } else if (pendingSources < 2) {
            // Saturate: 2 means >=2, never retain a growing event queue.
            pendingSources = 2;
        }
    }

    /** A metadata update is NOT necessarily a new audible track. */
    public synchronized Verdict onMetadata(long elapsedMs) {
        if (clockMovedBackwards(elapsedMs))
            return Verdict.CLOCK_DISCONTINUITY;
        metadataCallbacks++;
        final Verdict verdict;
        if (pendingSources == 0 || elapsedMs - firstPendingMs > windowMs) {
            noSourceWindows++;
            verdict = Verdict.METADATA_WITHOUT_RECENT_FILEINFO;
        } else if (pendingSources == 1) {
            oneSourceWindows++;
            verdict = Verdict.SINGLE_RECENT_FILEINFO_TEMPORAL_ONLY;
        } else {
            ambiguousWindows++;
            verdict = Verdict.MULTIPLE_FILEINFO_AMBIGUOUS;
        }
        // A subsequent metadata event cannot reuse the same source witness.
        clearPending();
        return verdict;
    }

    public synchronized Snapshot snapshot() {
        return new Snapshot(fileInfoCallbacks, metadataCallbacks,
                oneSourceWindows, ambiguousWindows, noSourceWindows,
                clockDiscontinuities, pendingSources);
    }

    public static final class Snapshot {
        public final long fileInfoCallbacks, metadataCallbacks, oneSourceWindows,
                ambiguousWindows, noSourceWindows, clockDiscontinuities;
        public final int pendingSourceCountBounded;

        private Snapshot(long fileInfoCallbacks, long metadataCallbacks,
                long oneSourceWindows, long ambiguousWindows, long noSourceWindows,
                long clockDiscontinuities, int pendingSourceCountBounded) {
            this.fileInfoCallbacks = fileInfoCallbacks;
            this.metadataCallbacks = metadataCallbacks;
            this.oneSourceWindows = oneSourceWindows;
            this.ambiguousWindows = ambiguousWindows;
            this.noSourceWindows = noSourceWindows;
            this.clockDiscontinuities = clockDiscontinuities;
            this.pendingSourceCountBounded = pendingSourceCountBounded;
        }
    }
}
