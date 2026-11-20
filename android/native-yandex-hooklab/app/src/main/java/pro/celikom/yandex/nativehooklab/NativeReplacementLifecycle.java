package pro.celikom.yandex.nativehooklab;

/**
 * Portable one-native-player lifecycle CONTRACT based on the owner's
 * working Windows W22 adapter and W58 real Stop semantics.
 *
 * OFF means no NEW alternate admissions. It does NOT rewrite already handed
 * decoder URLs, revoke valid server grants, flush Yandex buffers, change its
 * play/pause, or manipulate a media clock. No Android hook is wired here.
 *
 * Every Next, radio selection, Stop, re-enable invalidates earlier revisions.
 * All candidate work uses the pure-Java NativePrePrepareAdmission gate and
 * NativeGrantContract, but a real Android source/decoder boundary is still
 * required before ANY audible integration.
 */
public final class NativeReplacementLifecycle {
    public enum StopVerdict {
        ALREADY_OFF,
        CANCELLED_PENDING,
        ALREADY_ISSUED_SOURCE_UNCHANGED,
        NO_SOURCE_ISSUED
    }

    private final long resolveBudgetMs;
    private boolean enabled;
    private long generation;
    private NativePrePrepareAdmission active;
    private long activeRevision;
    private boolean issued;
    private NativeSourceGate.Choice issuedSource = NativeSourceGate.Choice.ORIGINAL;

    public NativeReplacementLifecycle(long resolveBudgetMs) {
        // Also validates deadline range, independent of the real player.
        new NativePrePrepareAdmission(resolveBudgetMs);
        this.resolveBudgetMs = resolveBudgetMs;
    }

    /** Turn on FUTURE mapping only. Do not restart or seek native music. */
    public synchronized void start() {
        if (enabled) return;
        enabled = true;
        generation++;
        active = null;
        issued = false;
        issuedSource = NativeSourceGate.Choice.ORIGINAL;
    }

    /**
     * Stop cancels pending source grants/decisions by invalidating generation.
     * A previously created Yandex media source remains in the native player;
     * stopping CELIKOM alone cannot change already delivered audio.
     */
    public synchronized StopVerdict stop() {
        if (!enabled) return StopVerdict.ALREADY_OFF;
        StopVerdict verdict;
        if (active == null) {
            verdict = issued ? StopVerdict.ALREADY_ISSUED_SOURCE_UNCHANGED
                             : StopVerdict.NO_SOURCE_ISSUED;
        } else if (!issued) {
            active.abort(activeRevision);
            verdict = StopVerdict.CANCELLED_PENDING;
        } else {
            verdict = StopVerdict.ALREADY_ISSUED_SOURCE_UNCHANGED;
        }
        enabled = false;
        active = null;
        generation++;
        issued = false;
        issuedSource = NativeSourceGate.Choice.ORIGINAL;
        return verdict;
    }

    /**
     * Native track selection (not just metadata change), includes radio/Next.
     * Returns a generation token; no raw ID is retained outside the gate.
     * Disabled mapping returns a token but cannot offer/commit anything.
     */
    /**
     * Reserve the ORIGINAL playback selection before the original source
     * setter has trustworthy track/album/edition String values.
     * No replacement candidate may be offered at this stage. Generation
     * advances exactly once for this selection; Next/replay always retires it.
     */
    public synchronized long beginUnresolvedNativeSelection(long elapsedRealtimeMs) {
        if (active != null && !issued) active.abort(activeRevision);
        generation++;
        active=null;
        issued=false;
        issuedSource=NativeSourceGate.Choice.ORIGINAL;
        return generation;
    }

    /**
     * Only a semantically verified SAME-original-source identity may be
     * certified, before the original decoder's prepare boundary. This does
     * not read IDs or certify an arbitrary Track field by itself.
     * A late FileInfo reply after ORIGINAL was prepared CANNOT upgrade it.
     */
    public synchronized boolean certifyNativeIdentity(long token,
            String trackId,String albumId,String edition,long elapsedRealtimeMs) {
        if(!enabled || token!=generation || issued || active!=null
                || !NativeGrantContract.isExactTrackId(trackId)
                || !exactText(albumId) || !exactText(edition))return false;
        NativePrePrepareAdmission admission=new NativePrePrepareAdmission(resolveBudgetMs);
        long revision=admission.begin(trackId,albumId,edition,elapsedRealtimeMs);
        active=admission;
        activeRevision=revision;
        return true;
    }

    private static boolean exactText(String value) {
        if(value==null || value.isEmpty() || value.length()>128
                || !value.trim().equals(value))return false;
        for(int i=0;i<value.length();i++)
            if(Character.isISOControl(value.charAt(i)))return false;
        return true;
    }

    public synchronized long beginTrack(String trackId, String albumId, String edition,
                                        long elapsedRealtimeMs) {
        if (active != null && !issued) active.abort(activeRevision);
        generation++;
        active = null;
        issued = false;
        issuedSource = NativeSourceGate.Choice.ORIGINAL;
        if (enabled) {
            active = new NativePrePrepareAdmission(resolveBudgetMs);
            activeRevision = active.begin(trackId, albumId, edition, elapsedRealtimeMs);
        }
        return generation;
    }

    public synchronized boolean observeFileInfo(long generationToken,
                                                 String trackId, String albumId, String edition) {
        return live(generationToken) && !issued
                && active.observeFileInfo(activeRevision, trackId, albumId, edition);
    }

    /**
     * Both the exact native candidate and its *independently verified*
     * approved CELIKOM grant must pass, before actual native prepare.
     *
     * Supply two clocks: elapsedRealtimeMs for timeout/race fencing and
     * unixEpochMs for the server's signed URL expiration.
     */
    public synchronized NativePrePrepareAdmission.Offer offerValidated(
            long generationToken, NativeSourceGate.Candidate candidate,
            NativeGrantContract.Grant grant, String apiOrigin,
            long originalDurationMs, long elapsedRealtimeMs, long unixEpochMs) {
        if (generationToken != generation) return NativePrePrepareAdmission.Offer.STALE;
        if (!enabled || active == null || issued || candidate == null)
            return NativePrePrepareAdmission.Offer.REJECTED;
        if (!NativeGrantContract.isAcceptable(
                grant, candidate.track, candidate.album, candidate.edition,
                originalDurationMs, apiOrigin, unixEpochMs))
            return NativePrePrepareAdmission.Offer.REJECTED;
        return active.offer(activeRevision, candidate, elapsedRealtimeMs);
    }

    /**
     * Only the real decoder's pre-prepare boundary may call this later.
     * If disabled/stale, do NOT mutate/replace the original source.
     */
    public synchronized NativePrePrepareAdmission.Decision atNativePrepare(
            long generationToken, String decoderTrackId, String decoderAlbumId,
            String decoderEdition,
            long elapsedRealtimeMs) {
        if (!enabled || generationToken != generation || issued) {
            return new NativePrePrepareAdmission.Decision(false,
                    NativeSourceGate.Choice.ORIGINAL,
                    NativeTrackIdentityGate.Verdict.ORIGINAL_STALE);
        }
        // A real original prepare while IDs are still unresolved *seals*
        // ORIGINAL forever for this generation. It must NOT be possible
        // to certify afterwards and apply an alternate mid-play.
        if (active == null) {
            issued = true;
            issuedSource = NativeSourceGate.Choice.ORIGINAL;
            return new NativePrePrepareAdmission.Decision(false,
                    NativeSourceGate.Choice.ORIGINAL,
                    NativeTrackIdentityGate.Verdict.ORIGINAL_UNPROVEN);
        }
        NativePrePrepareAdmission.Decision decision =
                active.commitAtNativePrepare(activeRevision,
                        decoderTrackId, decoderAlbumId, decoderEdition, elapsedRealtimeMs);
        if (decision.applyOnce) {
            issued = true;
            issuedSource = decision.source;
        }
        return decision;
    }

    public synchronized void onNativePlay(long generationToken) {
        if (live(generationToken) && issued) active.onPlay(activeRevision);
    }
    public synchronized void onNativePause(long generationToken) {
        if (live(generationToken) && issued) active.onPause(activeRevision);
    }
    public synchronized void onNativeSeek(long generationToken) {
        if (live(generationToken) && issued) active.onSeek(activeRevision);
    }

    public synchronized boolean isEnabled() { return enabled; }
    public synchronized long generation() { return generation; }
    public synchronized NativeSourceGate.Choice lastIssuedSource() {
        return issuedSource;
    }

    private boolean live(long token) {
        return enabled && active != null && token == generation;
    }
}
