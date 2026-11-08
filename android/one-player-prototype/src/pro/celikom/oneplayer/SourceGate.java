package pro.celikom.oneplayer;

/**
 * Offline, platform-independent prototype of a pre-play source decision.
 * This is NOT a hook into Yandex and does not access its private data.
 * A compatible, authorized host must supply verified catalog identities.
 */
public final class SourceGate {
    private SourceGate() {}

    public enum Evidence { INTERNAL_CATALOG, EXTERNAL_ALIAS, TITLE_MATCH }
    public enum Selection { ORIGINAL, REPLACEMENT }

    public static final class Track {
        public final String catalogId;
        public final String editionId;
        public final String originalUri;
        public final long durationMs;
        public final Evidence evidence;
        public Track(String catalogId, String editionId, String originalUri,
                     long durationMs, Evidence evidence) {
            this.catalogId = catalogId;
            this.editionId = editionId;
            this.originalUri = originalUri;
            this.durationMs = durationMs;
            this.evidence = evidence;
        }
    }

    public static final class Candidate {
        public final String catalogId;
        public final String editionId;
        public final String uri;
        public final long durationMs;
        public final boolean approved;
        public final boolean entitled;
        public final boolean fullyCached;
        public final boolean integrityVerified;
        public Candidate(String catalogId, String editionId, String uri, long durationMs,
                         boolean approved, boolean entitled, boolean fullyCached,
                         boolean integrityVerified) {
            this.catalogId = catalogId;
            this.editionId = editionId;
            this.uri = uri;
            this.durationMs = durationMs;
            this.approved = approved;
            this.entitled = entitled;
            this.fullyCached = fullyCached;
            this.integrityVerified = integrityVerified;
        }
    }

    public static final class Decision {
        public final Selection selection;
        public final String uri;
        public final String reason;
        private Decision(Selection selection, String uri, String reason) {
            this.selection = selection;
            this.uri = uri;
            this.reason = reason;
        }
    }

    /**
     * Pure synchronous decision made BEFORE the host invokes its single player.
     * Input content URI must be locally readable through narrow scoped access.
     * No network and no mid-track swapping. The host rechecks URI readability.
     */
    public static Decision select(Track track, Candidate candidate) {
        if (track == null || !validOriginal(track.originalUri))
            throw new IllegalArgumentException("A playable original source is required");
        if (track.evidence != Evidence.INTERNAL_CATALOG || !numericId(track.catalogId))
            return original(track, "catalog_identity_unverified");
        if (candidate == null) return original(track, "no_replacement");
        if (!candidate.approved || !candidate.entitled)
            return original(track, "permission_denied");
        if (!candidate.fullyCached || !candidate.integrityVerified)
            return original(track, "not_ready");
        if (!track.catalogId.equals(candidate.catalogId))
            return original(track, "catalog_mismatch");
        if (track.editionId == null || track.editionId.isEmpty() ||
            !track.editionId.equals(candidate.editionId))
            return original(track, "edition_unverified");
        if (track.durationMs <= 0 || candidate.durationMs <= 0 ||
            Math.abs(track.durationMs - candidate.durationMs) > 1500)
            return original(track, "duration_mismatch");
        if (candidate.uri == null || !candidate.uri.startsWith("content://") ||
            candidate.uri.length() <= "content://".length())
            return original(track, "untrusted_replacement_uri");
        return new Decision(Selection.REPLACEMENT, candidate.uri, "approved_cached_source");
    }

    private static boolean validOriginal(String uri) {
        return uri != null && !uri.trim().isEmpty();
    }

    private static boolean numericId(String id) {
        if (id == null || id.isEmpty()) return false;
        for (int i = 0; i < id.length(); i++) {
            if (id.charAt(i) < '0' || id.charAt(i) > '9') return false;
        }
        return true;
    }

    private static Decision original(Track t, String reason) {
        return new Decision(Selection.ORIGINAL, t.originalUri, reason);
    }
}
