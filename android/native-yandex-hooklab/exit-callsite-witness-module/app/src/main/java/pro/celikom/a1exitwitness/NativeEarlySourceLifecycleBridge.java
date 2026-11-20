package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeReplacementLifecycle;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;
import pro.celikom.yandex.nativehooklab.NativePrePrepareAdmission;
import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import java.lang.ref.WeakReference;
import java.util.function.LongSupplier;

/**
 * The original publisher Player source setter -> existing CELIKOM lifecycle.
 *
 * This bridge records only exact original Java reference identity, never
 * trackId/albumId/editionId, URLs, media bytes, account data or filenames.
 * Crucially it does not infer semantic IDs from a Track or a MediaItem.
 *
 * CELIKOM admission is OFF until a real owner-enabled controller and exact
 * semantic-ID + decoder pre-prepare witness are wired independently.
 * Both original source and original player always execute unchanged.
 */
final class NativeEarlySourceLifecycleBridge
        implements NativeRendererStreamEvidence.EarlyOriginalSourceObserver,
                   NativeRendererStreamEvidence.ActiveOriginalTrackObserver,
                   NativeRendererStreamEvidence.OriginalPeriodBeforePrepareObserver {
    private final NativeReplacementLifecycle lifecycle =
        new NativeReplacementLifecycle(850);
    private final LongSupplier elapsedClock;
    private final LongSupplier unixClock;
    private final NativeExoAlternateByteRoute nativeExoBytes;
    // Only a real original Retrofit trackId matched to same source creator
    // may enter this coordinator. Album+edition are still independently needed.
    private String originalPublisherTrackIdCandidate;
    private static final class PendingApprovedAudio {
        final String track,album,edition,origin;
        final long durationMs;
        final NativeGrantContract.Grant grant;
        PendingApprovedAudio(String track,String album,String edition,
                String origin,long durationMs,NativeGrantContract.Grant grant) {
            this.track=track;this.album=album;this.edition=edition;
            this.origin=origin;this.durationMs=durationMs;this.grant=grant;
        }
    }
    private PendingApprovedAudio pendingApprovedAudio;
    private long latestSetterGeneration = -1;
    private long lifecycleGeneration;
    private boolean originalSetterSucceeded;
    // A late original player/PeriodID/SLOT_B renderer read must match the
    // SAME earlier original source generation, never a queue/prefetch guess.
    private long confirmedCurrentOriginalGeneration = -1;
    // This is a PRE-proceed original MediaPeriod event, distinct from the
    // late CURRENT player confirmation; prefetch must not count as selected.
    private long originalPeriodPrePrepareGeneration = -1;
    private WeakReference<Object> originalPeriodRef;
    private WeakReference<Object> prePrepareSourceInstanceRef;
    private boolean originalPeriodAmbiguous;
    private boolean originalPeriodPrepareSealed;
    private WeakReference<Object> trackRef;
    private WeakReference<Object> albumRef;
    private WeakReference<Object> sourceRef;

    NativeEarlySourceLifecycleBridge() {
        this(() -> System.nanoTime() / 1_000_000L);
    }
    NativeEarlySourceLifecycleBridge(LongSupplier clock) {
        this(clock,new NativeExoAlternateByteRoute(),System::currentTimeMillis);
    }
    NativeEarlySourceLifecycleBridge(LongSupplier clock,
            NativeExoAlternateByteRoute route,LongSupplier unixMillis) {
        if(clock==null || route==null || unixMillis==null)
            throw new IllegalArgumentException("SOURCE_CLOCK_REQUIRED");
        elapsedClock=clock;
        unixClock=unixMillis;
        nativeExoBytes=route;
    }

    /** Only an explicit CELIKOM owner-authenticated UI action may call this. */
    synchronized void startForAuthenticatedOwner() { lifecycle.start(); }
    synchronized void stopForAuthenticatedOwner() {
        lifecycle.stop();
        pendingApprovedAudio=null;
        // Never cut already issued/native Exo bytes mid-song on Stop.
    }
    private void clear() {
        confirmedCurrentOriginalGeneration=-1;
        originalPeriodPrePrepareGeneration=-1;
        originalPeriodRef=null;
        prePrepareSourceInstanceRef=null;
        originalPeriodAmbiguous=false;
        originalPeriodPrepareSealed=false;
        originalSetterSucceeded=false;
        trackRef=null;
        albumRef=null;
        sourceRef=null;
        originalPublisherTrackIdCandidate=null;
        pendingApprovedAudio=null;
    }

    @Override public synchronized void invalidated(long generation) {
        // Even an unknown original selection supersedes the previous one.
        // No candidate can inherit another track's revision.
        latestSetterGeneration=generation;
        // A newly selected original player source retires old Exo alternate
        // bytes before a new grant can arm a different DataSource instance.
        nativeExoBytes.cancelForNext();
        clear();
        lifecycleGeneration=lifecycle.beginUnresolvedNativeSelection(
            elapsedClock.getAsLong());
    }

    @Override public synchronized void rejected(long generation) {
        if(generation!=latestSetterGeneration)return;
        clear();
        lifecycle.cancelPendingNativeSelection(lifecycleGeneration);
    }

    @Override public synchronized void pending(long generation,
            Object originalTrack,Object originalAlbum,Object originalSource) {
        if(generation!=latestSetterGeneration || originalTrack==null
                || originalAlbum==null || originalSource==null)return;
        trackRef=new WeakReference<>(originalTrack);
        albumRef=new WeakReference<>(originalAlbum);
        sourceRef=new WeakReference<>(originalSource);
    }

    @Override public synchronized void originalPublisherTrackIdCandidate(
            long generation,String originalId) {
        if(generation==latestSetterGeneration
                && originalId!=null
                && NativeGrantContract.isExactTrackId(originalId))
            originalPublisherTrackIdCandidate=originalId;
    }

    @Override public synchronized void completed(long generation,boolean succeeded) {
        if(generation!=latestSetterGeneration)return;
        // A throwing/nested original setter is never a valid selection.
        originalSetterSucceeded=succeeded && trackRef!=null
                && albumRef!=null && sourceRef!=null
                && trackRef.get()!=null && albumRef.get()!=null
                && sourceRef.get()!=null;
        if(!originalSetterSucceeded) {
            clear();
            // A failed publisher setter must also abort an in-flight model
            // admission: a later FileInfo callback must not resurrect it.
            lifecycle.cancelPendingNativeSelection(lifecycleGeneration);
        }
    }

    /**
     * Invoke ONLY when an independently inspected original native
     * FileInfo request proves the exact SAME source/Track/Album plus the
     * publisher's own numeric trackId, albumId and editionId values.
     * The current original Retrofit API only annotates trackId: this
     * method has NO production caller until the other two are proven.
     */
    synchronized boolean onSourceBoundPublisherFileInfo(
            long generation,Object originalTrack,Object originalAlbum,
            Object originalSource,String track,String album,String edition) {
        if(!isSuccessfulOriginalSource(generation,originalTrack,
                originalAlbum,originalSource)
                || originalPublisherTrackIdCandidate==null
                || !originalPublisherTrackIdCandidate.equals(track))
            return false;
        long elapsed=elapsedClock.getAsLong();
        return lifecycle.certifyNativeIdentity(lifecycleGeneration,
                track,album,edition,elapsed)
            && lifecycle.observeFileInfo(lifecycleGeneration,
                track,album,edition);
    }

    /**
     * ONLY after the separate CELIKOM authenticated resolve and real audio
     * compatibility/range checks. No request or credentials are handled here.
     * Accepted means PENDING, not audible source issuance.
     */
    synchronized boolean offerAuthenticatedApprovedAudio(
            long generation,Object originalTrack,Object originalAlbum,
            Object originalSource,NativeSourceGate.Candidate candidate,
            NativeGrantContract.Grant grant,String allowedOrigin,
            long originalDurationMs) {
        if(!isSuccessfulOriginalSource(generation,originalTrack,
                originalAlbum,originalSource)
                || originalPublisherTrackIdCandidate==null
                || candidate==null
                || !originalPublisherTrackIdCandidate.equals(candidate.track)
                || pendingApprovedAudio!=null)
            return false;
        if(lifecycle.offerValidated(lifecycleGeneration,candidate,grant,
                allowedOrigin,originalDurationMs,
                elapsedClock.getAsLong(),unixClock.getAsLong())
                !=NativePrePrepareAdmission.Offer.ACCEPTED_PENDING)
            return false;
        pendingApprovedAudio=new PendingApprovedAudio(
            candidate.track,candidate.album,candidate.edition,
            allowedOrigin,originalDurationMs,grant);
        return true;
    }

    private boolean commitApprovedAtOriginalPrepare(
            long generation,Object originalTrack,Object originalAlbum,
            Object originalSource,Object unopenedOriginalDataSource) {
        PendingApprovedAudio approved=pendingApprovedAudio;
        if(approved==null || unopenedOriginalDataSource==null
                || !isSuccessfulOriginalSource(generation,originalTrack,
                    originalAlbum,originalSource))
            return false;
        pendingApprovedAudio=null;
        NativePrePrepareAdmission.Decision decision=lifecycle.atNativePrepare(
            lifecycleGeneration,approved.track,approved.album,
            approved.edition,elapsedClock.getAsLong());
        if(decision.source!=NativeSourceGate.Choice.ALTERNATE
                || !decision.applyOnce)
            return false;
        boolean routed=nativeExoBytes.armApproved(
            lifecycleGeneration,unopenedOriginalDataSource,
            approved.track,approved.album,approved.edition,approved.durationMs,
            approved.grant,approved.origin,unixClock.getAsLong(),
            decision.source);
        if(!routed)lifecycle.stop(); // never report an uninstalled ALTERNATE
        return routed;
    }

    @Override public synchronized void beforeUnverifiedOriginalPeriodPrepare() {
        // An unlinked original MediaPeriod has entered actual prepare.
        // Even if a same-source period later prepares, this generation is
        // no longer UNIQUE; revoke all historical pre-prepare candidates.
        originalPeriodAmbiguous=true;
        originalPeriodPrePrepareGeneration=-1;
        originalPeriodRef=null;
        prePrepareSourceInstanceRef=null;
        sealUnknownNativePrepare();
    }

    private void sealUnknownNativePrepare() {
        if(originalPeriodPrepareSealed)return;
        originalPeriodPrepareSealed=true;
        lifecycle.atNativePrepare(lifecycleGeneration,
            null,null,null,elapsedClock.getAsLong());
    }

    @Override public synchronized void beforeOriginalPeriodPrepare(
            long generation,Object track,Object album,Object source,Object period,
            Object originalDataSourceCandidate) {
        if(period==null || originalPeriodAmbiguous
                || !isSuccessfulOriginalSource(generation,track,album,source))
            return;
        // At most ONE exact original period for this setter generation.
        // A distinct period (prefetch/retry ambiguity) permanently revokes
        // this generation, even if the first period appears again later.
        if(originalPeriodRef!=null) {
            if(originalPeriodRef.get()!=period) {
                originalPeriodPrePrepareGeneration=-1;
                originalPeriodRef=null;
                prePrepareSourceInstanceRef=null;
                originalPeriodAmbiguous=true;
            } else {
                // Original prepare already executed on this same period;
                // the first pre-open candidate is NOT a reusable ticket.
                // A newly linked/opened source cannot promote a duplicate
                // prepare to a fresh alternate decision.
                prePrepareSourceInstanceRef=null;
            }
            return;
        }
        originalPeriodRef=new WeakReference<>(period);
        prePrepareSourceInstanceRef=originalDataSourceCandidate==null?null:
            new WeakReference<>(originalDataSourceCandidate);
        originalPeriodPrePrepareGeneration=generation;
        // Only an already authenticated, exact issuer triple can commit
        // the alternate BEFORE this actual publisher MediaPeriod prepare.
        // Without a fresh exact original Exo DataSource instance, original
        // playback proceeds and later grants cannot upgrade it.
        if(commitApprovedAtOriginalPrepare(generation,track,album,source,
                originalDataSourceCandidate)) {
            originalPeriodPrepareSealed=true;
        } else {
            sealUnknownNativePrepare();
        }
    }

    /** A structural, original-only candidate for this exact period, never a grant. */
    synchronized boolean wasPrePrepareOriginalSourceInstance(long generation,
            Object period,Object dataSource) {
        return dataSource!=null
            && sawOriginalPeriodPrePrepare(generation,period)
            && prePrepareSourceInstanceRef!=null
            && prePrepareSourceInstanceRef.get()==dataSource;
    }

    synchronized boolean sawOriginalPeriodPrePrepare(long generation,Object period) {
        return !originalPeriodAmbiguous
            && generation==originalPeriodPrePrepareGeneration
            && period!=null && originalPeriodRef!=null
            && originalPeriodRef.get()==period
            && originalSetterSucceeded;
    }

    /**
     * This is invoked ONLY by the pre-existing strict current PlaybackInfo
     * PeriodID + SLOT_B + -4 same-call read guard. It is intentionally late:
     * cannot authorize pre-prepare or upgrade the source mid-play.
     */
    @Override public synchronized void observe(
            Object originalTrack,Object originalAlbum,Object activeOriginalSource) {
        if(isSuccessfulOriginalSource(latestSetterGeneration,
                originalTrack,originalAlbum,activeOriginalSource))
            confirmedCurrentOriginalGeneration=latestSetterGeneration;
    }

    synchronized boolean wasCurrentOriginalSource(long generation,
            Object originalTrack,Object originalAlbum,Object originalSource) {
        return generation==confirmedCurrentOriginalGeneration
            && isSuccessfulOriginalSource(generation,
                originalTrack,originalAlbum,originalSource);
    }

    /** Weak same-original-source witness, not an admission/decoder decision. */
    synchronized boolean isSuccessfulOriginalSource(long generation,
            Object originalTrack,Object originalAlbum,Object originalSource) {
        return originalSetterSucceeded && generation==latestSetterGeneration
                && trackRef!=null && trackRef.get()==originalTrack
                && originalTrack!=null && albumRef!=null
                && albumRef.get()==originalAlbum && originalAlbum!=null
                && sourceRef!=null && sourceRef.get()==originalSource
                && originalSource!=null;
    }

    synchronized long generation() {return latestSetterGeneration;}

    /** No owner-enable or exact decoder source exists in this module yet. */
    synchronized boolean replacementEnabled() {return lifecycle.isEnabled();}
    synchronized NativeSourceGate.Choice chosenSource() {
        return lifecycle.lastIssuedSource();
    }
    synchronized long reservedNativeGeneration() {return lifecycleGeneration;}
    synchronized long currentNativeGeneration() {return lifecycle.generation();}
}
