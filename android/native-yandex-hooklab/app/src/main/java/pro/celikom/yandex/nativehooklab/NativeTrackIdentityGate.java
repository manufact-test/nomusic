package pro.celikom.yandex.nativehooklab;

/**
 * Fail-closed identity correlation model for a future single native-Yandex source.
 * Pure Java only: does not obtain IDs, hook Yandex, access network or mutate audio.
 * Exact identity is the triple track + album + edition.
 */
public final class NativeTrackIdentityGate {
    public enum Verdict { MATCH, ORIGINAL_UNPROVEN, ORIGINAL_MISMATCH,
        ORIGINAL_STALE, ORIGINAL_DUPLICATE }

    private long generation;
    private String activeTrack;
    private String activeAlbum;
    private String activeEdition;
    private boolean fileInfoMatched;
    private boolean conflictObserved;
    private boolean sealed;
    private Verdict lastVerdict = Verdict.ORIGINAL_UNPROVEN;

    /** Advance on EVERY native playback selection (Next, radio or replay). */
    public synchronized long beginNativeTrack(String trackId, String albumId, String edition) {
        generation++;
        activeTrack = clean(trackId);
        activeAlbum = clean(albumId);
        activeEdition = clean(edition);
        fileInfoMatched = false;
        conflictObserved = false;
        sealed = false;
        lastVerdict = Verdict.ORIGINAL_UNPROVEN;
        return generation;
    }

    /** Only a trusted in-process file-info REQUEST observer may call this. */
    public synchronized boolean observeFileInfo(long observedGeneration,
            String trackId, String albumId, String edition) {
        if (observedGeneration != generation || sealed) {
            lastVerdict = Verdict.ORIGINAL_STALE;
            return false;
        }
        if (conflictObserved) return false;
        if (activeTrack == null || activeAlbum == null || activeEdition == null
                || clean(trackId) == null || clean(albumId) == null || clean(edition) == null) {
            fileInfoMatched = false;
            lastVerdict = Verdict.ORIGINAL_UNPROVEN;
            return false;
        }
        if (!activeTrack.equals(trackId) || !activeAlbum.equals(albumId)
                || !activeEdition.equals(edition)) {
            fileInfoMatched = false;
            conflictObserved = true;
            lastVerdict = Verdict.ORIGINAL_MISMATCH;
            return false;
        }
        fileInfoMatched = true;
        return true;
    }

    /**
     * Call at the real native decoder's pre-prepare source boundary only.
     * Descriptor identity must come from that same source, not title or cover.
     */
    public synchronized Verdict sealAtNativePrepare(long observedGeneration,
            String descriptorTrackId, String descriptorAlbumId, String descriptorEdition) {
        if (observedGeneration != generation) return Verdict.ORIGINAL_STALE;
        if (sealed) return Verdict.ORIGINAL_DUPLICATE;
        sealed = true;
        if (conflictObserved) {
            lastVerdict = Verdict.ORIGINAL_MISMATCH;
        } else if (activeTrack == null || activeAlbum == null || activeEdition == null
                || !fileInfoMatched) {
            lastVerdict = Verdict.ORIGINAL_UNPROVEN;
        } else if (!activeTrack.equals(clean(descriptorTrackId))
                || !activeAlbum.equals(clean(descriptorAlbumId))
                || !activeEdition.equals(clean(descriptorEdition))) {
            lastVerdict = Verdict.ORIGINAL_MISMATCH;
        } else {
            lastVerdict = Verdict.MATCH;
        }
        return lastVerdict;
    }

    public synchronized void invalidate(long observedGeneration) {
        if (observedGeneration == generation) {
            generation++;
            activeTrack = null;
            activeAlbum = null;
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
            if (Character.isISOControl(value.charAt(i))) return null;
        }
        return value;
    }
}
