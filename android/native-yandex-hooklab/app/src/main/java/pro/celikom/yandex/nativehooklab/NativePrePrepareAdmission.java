package pro.celikom.yandex.nativehooklab;

/**
 * Pure-Java coordination MODEL for a future publisher-APPROVED in-process host.
 *
 * NO Yandex private API, hooks, credentials, media player, decoder, network
 * transport, publisher data, APK mutation or source replacement in this class.
 * An external authorized host alone may observe trusted native boundaries.
 *
 * Invariants:
 * - Only exact native track+edition+generation identity may admit alternate.
 * - File-info must match AND the native decoder descriptor must match.
 * - Exactly one pre-prepare decision per selection, never a mid-play flip.
 * - Late responses and callbacks never change a later selection.
 * - Unknown identity / missing rights / unsafe source -> original.
 */
public final class NativePrePrepareAdmission {
    public enum Offer { ACCEPTED_PENDING, REJECTED, STALE }
    public static final class Decision {
        public final boolean applyOnce;
        public final NativeSourceGate.Choice source;
        public final NativeTrackIdentityGate.Verdict identity;
        public final boolean readyToPrepare;

        Decision(boolean applyOnce, NativeSourceGate.Choice source,
                 NativeTrackIdentityGate.Verdict identity) {
            this.applyOnce = applyOnce;
            this.source = source;
            this.identity = identity;
            this.readyToPrepare = applyOnce && source != NativeSourceGate.Choice.UNDECIDED;
        }
    }

    private final NativeSourceGate gate;
    private final NativeTrackIdentityGate identity = new NativeTrackIdentityGate();
    private long generation;
    private long identityGeneration;
    private long sourceRevision;
    private boolean hasExactSelection;
    private boolean committed;
    private boolean aborted;
    private int commits;

    public NativePrePrepareAdmission(long resolveBudgetMs) {
        gate = new NativeSourceGate(resolveBudgetMs);
    }

    /** Every native selection (including replay, Next and radio) starts a generation. */
    public synchronized long begin(String trackId, String edition, long nowMs) {
        generation++;
        identityGeneration = identity.beginNativeTrack(trackId, edition);
        hasExactSelection = exact(trackId) && exact(edition);
        sourceRevision = hasExactSelection
                ? gate.beginTrack(trackId, edition, nowMs) : -1;
        committed = false;
        aborted = false;
        commits = 0;
        return generation;
    }

    /** Call only from a trusted same-generation native FileInfo request observer. */
    public synchronized boolean observeFileInfo(long observedGeneration, String trackId,
                                                String edition) {
        if (observedGeneration != generation || committed || aborted)
            return false;
        return identity.observeFileInfo(identityGeneration, trackId, edition);
    }

    /**
     * Queues an approved and fully validated candidate; never starts playback.
     * Accepted means PENDING: only commitAtNativePrepare may choose it.
     */
    public synchronized Offer offer(long observedGeneration, NativeSourceGate.Candidate candidate,
                                    long nowMs) {
        if (observedGeneration != generation) return Offer.STALE;
        if (committed || aborted || !hasExactSelection) return Offer.REJECTED;
        NativeSourceGate.Result decision = gate.propose(sourceRevision, candidate, nowMs);
        return decision.reason == NativeSourceGate.Reason.ACCEPTED
                ? Offer.ACCEPTED_PENDING : Offer.REJECTED;
    }

    /**
     * Invoke only at the verified SAME decoder descriptor BEFORE prepare.
     * Decision.applyOnce=false means do not apply or repeat this decision.
     * The actual publisher player remains the exclusive owner of audio.
     */
    public synchronized Decision commitAtNativePrepare(long observedGeneration,
                                                       String descriptorTrackId,
                                                       String descriptorEdition,
                                                       long nowMs) {
        if (observedGeneration != generation || aborted)
            return noApply(NativeTrackIdentityGate.Verdict.ORIGINAL_STALE);
        if (committed)
            return noApply(NativeTrackIdentityGate.Verdict.ORIGINAL_DUPLICATE);
        // Seal before source decision so reentrant/late callbacks cannot race.
        committed = true;
        NativeTrackIdentityGate.Verdict verdict =
                identity.sealAtNativePrepare(identityGeneration,
                                             descriptorTrackId, descriptorEdition);
        NativeSourceGate.Choice selected;
        if (!hasExactSelection) {
            selected = NativeSourceGate.Choice.ORIGINAL;
        } else {
            if (verdict != NativeTrackIdentityGate.Verdict.MATCH)
                gate.rejectBeforePrepare(sourceRevision);
            selected = gate.prepare(sourceRevision, nowMs);
        }
        if (selected == NativeSourceGate.Choice.ALTERNATE
                && verdict != NativeTrackIdentityGate.Verdict.MATCH)
            throw new IllegalStateException("NO_ALTERNATE_WITHOUT_EXACT_DECODER_IDENTITY");
        if (++commits != 1)
            throw new IllegalStateException("MORE_THAN_ONE_SOURCE_DECISION");
        return new Decision(true, selected, verdict);
    }

    /** Abort never commits a second source or changes the player's media clock. */
    public synchronized void abort(long observedGeneration) {
        if (observedGeneration != generation || aborted || committed) return;
        aborted = true;
        identity.invalidate(identityGeneration);
        if (hasExactSelection) gate.end(sourceRevision);
    }

    public synchronized void onPlay(long observedGeneration) {
        if (active(observedGeneration)) gate.onPlay(sourceRevision);
    }
    public synchronized void onPause(long observedGeneration) {
        if (active(observedGeneration)) gate.onPause(sourceRevision);
    }
    public synchronized void onSeek(long observedGeneration) {
        if (active(observedGeneration)) gate.onSeek(sourceRevision);
    }
    private boolean active(long observedGeneration) {
        return hasExactSelection && !aborted && committed
                && observedGeneration == generation;
    }

    public synchronized long generation() { return generation; }
    public synchronized int committedSourceDecisions() { return commits; }

    private static Decision noApply(NativeTrackIdentityGate.Verdict reason) {
        return new Decision(false, NativeSourceGate.Choice.ORIGINAL, reason);
    }
    private static boolean exact(String value) {
        if (value == null || value.isEmpty() || value.length() > 128
                || !value.equals(value.trim())) return false;
        for (int i = 0; i < value.length(); i++)
            if (Character.isISOControl(value.charAt(i))) return false;
        return true;
    }
}
