package pro.celikom.yandex.nativehooklab;

/**
 * Fail-closed identity correlation for a future single native-Yandex source.
 * This pure-Java MODEL neither obtains track IDs nor hooks Yandex. It only
 * accepts IDs already witnessed at exact version-pinned native boundaries.
 * No network, tokens, player instances, file-info payloads or logging.
 */
public final class NativeTrackIdentityGate {
    public enum Verdict { MATCH, ORIGINAL_UNPROVEN, ORIGINAL_MISMATCH,
        ORIGINAL_STALE, ORIGINAL_DUPLICATE }

    private long generation;
    private String activeTrack;
    private String activeEdition;
    private boolean fileInfoMatched;
    private boolean conflictObserved;
    private boolean sealed;
    private Verdict lastVerdict = Verdict.ORIGINAL_UNPROVEN;

    /** Advance on EVERY native playback selection (Next, radio or replay). */
    public synchronized long beginNativeTrack(String trackId, String edition) {
        generation++;
        activeTrack = clean(trackId);
        activeEdition = clean(edition);
        fileInfoMatched = false;
        conflictObserved = false;
        sealed = false;
        lastVerdict = Verdict.ORIGINAL_UNPROVEN;
        return generation;
    }

    /** Only a trusted in-process file-info REQUEST observer may call this. */
    public synchronized boolean observeFileInfo(long observedGeneration,
                                                 String trackId, String edition) {
        if (observedGeneration != generation || sealed) {
            lastVerdict = Verdict.ORIGINAL_STALE;
            return false;
        }
        if (conflictObserved) return false;
        if (activeTrack == null || activeEdition == null
                || clean(trackId) == null || clean(edition) == null) {
            fileInfoMatched = false;
            lastVerdict = Verdict.ORIGINAL_UNPROVEN;
            return false;
        }
        if (!activeTrack.equals(trackId) || !activeEdition.equals(edition)) {
            fileInfoMatched = false;
            conflictObserved = true;
            lastVerdict = Verdict.ORIGINAL_MISMATCH;
            return false;
        }
        fileInfoMatched = true;
        return true;
    }

    /**
     * Call AT the real native decoder's pre-prepare source boundary only.
     * Must receive descriptor identity directly from that same source;
     * UI title, MediaSession ID or delayed download ID is NOT authoritative.
     * Exactly one decision is committed for this generation.
     */
    public synchronized Verdict sealAtNativePrepare(long observedGeneration,
                                                     String descriptorTrackId,
                                                     String descriptorEdition) {
        if (observedGeneration != generation) {
            return Verdict.ORIGINAL_STALE;
        }
        if (sealed) {
            return Verdict.ORIGINAL_DUPLICATE;
        }
        sealed = true;
        if (conflictObserved) {
            lastVerdict = Verdict.ORIGINAL_MISMATCH;
        } else if (activeTrack == null || activeEdition == null || !fileInfoMatched) {
            lastVerdict = Verdict.ORIGINAL_UNPROVEN;
        } else if (!activeTrack.equals(clean(descriptorTrackId))
                || !activeEdition.equals(clean(descriptorEdition))) {
            lastVerdict = Verdict.ORIGINAL_MISMATCH;
        } else {
            lastVerdict = Verdict.MATCH;
        }
        return lastVerdict;
    }

    /** Drop active generation on abort/stop without a new selection. */
    public synchronized void invalidate(long observedGeneration) {
        if (observedGeneration == generation) {
            generation++;
            activeTrack = null;
            activeEdition = null;
            fileInfoMatched = false;
            conflictObserved = false;
            sealed = true;
            lastVerdict = Verdict.ORIGINAL_UNPROVEN;
        }
    }

    public synchronized long generation() { return generation; }
    public synchronized Verdict lastVerdict() { return lastVerdict; }

    private static String clean(String value) {
        if (value == null || value.isEmpty() || value.length() > 128
                || !value.equals(value.trim())) return null;
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            if (Character.isISOControl(ch)) return null;
        }
        return value;
    }
}
