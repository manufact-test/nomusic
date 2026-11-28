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
 * Strict exact Track+Album+Edition admission remains disabled. The
 * owner-consented limited BETA path may request a signed trackId-only grant
 * for its allowlisted original Track/source lineage; it does not prove the
 * selected renderer period or edition. The original player remains the only
 * player and the original source setter/period lifecycle remains authoritative.
 */
final class NativeEarlySourceLifecycleBridge
        implements NativeRendererStreamEvidence.EarlyOriginalSourceObserver,
                   NativeRendererStreamEvidence.ActiveOriginalTrackObserver,
                   NativeRendererStreamEvidence.OriginalPeriodBeforePrepareObserver {
    // A3s owner-only Exo grace must share the exact same source budget.
    // Otherwise valid first-download grants still expire at the old 850ms gate.
    private final NativeReplacementLifecycle lifecycle =
        new NativeReplacementLifecycle(3000);
    private final LongSupplier elapsedClock;
    private final LongSupplier unixClock;
    private final NativeExoAlternateByteRoute nativeExoBytes;
    // Only a real original Retrofit trackId matched to same source creator
    // may enter this coordinator. Album+edition are still independently needed.
    private String originalPublisherTrackIdCandidate;
    private String requestedLimitedBetaTrackId;
    private boolean publisherTrackIdConflict;
    private boolean publisherTrackIdCandidatePending;
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
    // The native Exo factory may instantiate its first DataSource AFTER
    // MediaPeriod.prepare. The already committed pre-prepare ALTERNATE may be
    // armed only on the exact same original creator's first UNOPENED DataSource.
    private PendingApprovedAudio deferredIssuedAudio;
    private long deferredIssuedGeneration=-1;
    private boolean exactAlternateDataSourceInstalled;
    // BETA25: first-open deferred-arm rejection reasons; no private values.
    private long deferredArmEnter,deferredArmNoPending,deferredArmGenerationMismatch;
    private long deferredArmSourceNull,deferredArmPeriodAmbiguous;
    private long deferredArmPrepareNotSealed,deferredArmPeriodMissing;
    private long deferredArmPrepareNotProven,deferredArmSourceMismatch;
    private long deferredArmOwnerDisabled,deferredArmNativeRouteRejected;
    private long deferredArmAccepted;
    interface AuthenticatedSourceGrantRequester {
        void request(long generation,Object originalTrack,Object originalAlbum,
            Object originalSource,String trackId,String albumId,
            String editionId,long originalDurationMs);
    }
    private AuthenticatedSourceGrantRequester authenticatedRequester;
    synchronized void setAuthenticatedSourceGrantRequester(
            AuthenticatedSourceGrantRequester requester) {
        authenticatedRequester=requester;
    }

    /** The user's two-ID beta is separate from exact-triple admission. */
    interface LimitedBetaGrantRequester {
        void request(long generation,Object originalTrack,Object originalAlbum,
            Object originalSource,String exactPublisherTrackId);
    }
    private LimitedBetaGrantRequester limitedBetaRequester;
    synchronized void setLimitedBetaGrantRequester(LimitedBetaGrantRequester requester) {
        limitedBetaRequester=requester;
    }
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
    synchronized void startForAuthenticatedOwner() {
        lifecycle.start();
        requestLimitedBetaIfReady(latestSetterGeneration);
    }
    synchronized void stopForAuthenticatedOwner() {
        lifecycle.stop();
        requestedLimitedBetaTrackId=null;
        pendingApprovedAudio=null;
        deferredIssuedAudio=null;
        deferredIssuedGeneration=-1;
        notifyAll();
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
        requestedLimitedBetaTrackId=null;
        publisherTrackIdConflict=false;
        publisherTrackIdCandidatePending=false;
        pendingApprovedAudio=null;
        deferredIssuedAudio=null;
        deferredIssuedGeneration=-1;
        exactAlternateDataSourceInstalled=false;
        notifyAll();
    }

    @Override public synchronized void invalidated(long generation) {
        // Even an unknown original selection supersedes the previous one.
        // No candidate can inherit another track's revision.
        latestSetterGeneration=generation;
        // A source setter starts a new admission generation, not necessarily
        // a completed playback switch. Revoke the old open right immediately,
        // but let its already committed exact cursor finish until native close.
        nativeExoBytes.supersedeSelection();
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
        if(generation!=latestSetterGeneration || originalPeriodPrepareSealed
                || originalPeriodRef!=null || publisherTrackIdConflict
                || !NativeGrantContract.isExactTrackId(originalId))return;
        if(originalPublisherTrackIdCandidate!=null
                && !originalPublisherTrackIdCandidate.equals(originalId)) {
            // A second identity for one setter generation is ambiguity, not
            // a reason to replace the first grant candidate.
            publisherTrackIdConflict=true;
            publisherTrackIdCandidatePending=false;
            originalPublisherTrackIdCandidate=null;
            pendingApprovedAudio=null;
            lifecycle.cancelPendingNativeSelection(lifecycleGeneration);
            notifyAll();
            return;
        }
        originalPublisherTrackIdCandidate=originalId;
        publisherTrackIdCandidatePending=false;
        notifyAll();
        requestLimitedBetaIfReady(generation);
    }

    @Override public synchronized void publisherTrackIdCandidatePending(
            long generation,boolean pending) {
        if(generation!=latestSetterGeneration || originalPeriodPrepareSealed
                || originalPeriodRef!=null || publisherTrackIdConflict
                || originalPublisherTrackIdCandidate!=null)return;
        publisherTrackIdCandidatePending=pending;
        notifyAll();
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
            return;
        }
        // The source setter may complete before its creator Track enters
        // Flow. A later exact same-Track Flow observation can supply the
        // publisher ID and will re-enter this same guarded request path.
        requestLimitedBetaIfReady(generation);
    }

    private void requestLimitedBetaIfReady(long generation) {
        if(generation!=latestSetterGeneration || !originalSetterSucceeded
                || publisherTrackIdConflict || !lifecycle.isEnabled()
                || originalPeriodPrepareSealed || originalPeriodRef!=null
                || limitedBetaRequester==null
                || !NativeTrackIdBetaPolicy.allows(originalPublisherTrackIdCandidate))
            return;
        if(requestedLimitedBetaTrackId!=null) {
            if(requestedLimitedBetaTrackId.equals(originalPublisherTrackIdCandidate))return;
            publisherTrackIdConflict=true;
            publisherTrackIdCandidatePending=false;
            originalPublisherTrackIdCandidate=null;
            pendingApprovedAudio=null;
            lifecycle.cancelPendingNativeSelection(lifecycleGeneration);
            notifyAll();
            return;
        }
        Object track=trackRef==null?null:trackRef.get();
        Object album=albumRef==null?null:albumRef.get();
        Object source=sourceRef==null?null:sourceRef.get();
        if(track==null || album==null || source==null)return;
        requestedLimitedBetaTrackId=originalPublisherTrackIdCandidate;
        NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.ORIGINAL_SETTER);
        try {
            limitedBetaRequester.request(generation,track,album,source,
                requestedLimitedBetaTrackId);
        } catch(Throwable ignored) {
            requestedLimitedBetaTrackId=null;
            NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.OWNER_NETWORK_OR_RESPONSE_ERROR);
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
     * Full original same-source identity AND separately proven original duration.
     * No caller may supply its duration or edition from CELIKOM's server reply.
     * Fail closed on absent/late proof. Network is asynchronous and cannot
     * upgrade a period once actual publisher prepare has begun.
     */
    synchronized boolean onCertifiedOriginalSourceWithDuration(
            long generation,Object originalTrack,Object originalAlbum,
            Object originalSource,String track,String album,String edition,
            long originalDurationMs) {
        if(originalDurationMs<=0 || originalDurationMs>86_400_000
                || originalPeriodPrepareSealed
                || !onSourceBoundPublisherFileInfo(generation,originalTrack,
                    originalAlbum,originalSource,track,album,edition))
            return false;
        AuthenticatedSourceGrantRequester requester=authenticatedRequester;
        if(requester!=null)requester.request(generation,originalTrack,
            originalAlbum,originalSource,track,album,edition,originalDurationMs);
        return true;
    }

    /**
     * Explicit owner-consented two-song trackId-only BETA. Never infer an
     * original Album/Edition or duration from the server; the strict native
     * source/track reference and original issuer Retrofit trackId MUST match.
     * The signed CELIKOM server duration/album placeholders are scope tags
     * inside the existing admission gate, never publisher identity evidence.
     */
    synchronized boolean offerLimitedBetaSignedAudio(long generation,
            Object originalTrack,Object originalAlbum,Object originalSource,
            String exactPublisherTrackId,NativeGrantContract.Grant serverGrant,
            String allowedOrigin) {
        if(!lifecycle.isEnabled() || publisherTrackIdConflict
                || originalPeriodPrepareSealed || originalPeriodRef!=null
                || pendingApprovedAudio!=null
                || !isSuccessfulOriginalSource(generation,originalTrack,
                    originalAlbum,originalSource)
                || originalPublisherTrackIdCandidate==null
                || !originalPublisherTrackIdCandidate.equals(exactPublisherTrackId))
            return false;
        long now=unixClock.getAsLong();
        NativeGrantContract.Grant scoped=NativeTrackIdBetaPolicy.signedTrialGrant(
            exactPublisherTrackId,serverGrant,allowedOrigin,now);
        if(scoped==null || !"audio/mpeg".equals(scoped.mimeType))
            return false;
        long elapsed=elapsedClock.getAsLong();
        if(!lifecycle.certifyNativeIdentity(lifecycleGeneration,scoped.trackId,
                scoped.albumId,scoped.editionId,elapsed)
                || !lifecycle.observeFileInfo(lifecycleGeneration,scoped.trackId,
                    scoped.albumId,scoped.editionId))
            return false;
        NativeSourceGate.Candidate candidate=new NativeSourceGate.Candidate(
            scoped.trackId,scoped.albumId,scoped.editionId,
            true,true,true,true,true,true);
        if(lifecycle.offerValidated(lifecycleGeneration,candidate,scoped,
                allowedOrigin,scoped.durationMs,elapsed,now)
                !=NativePrePrepareAdmission.Offer.ACCEPTED_PENDING)
            return false;
        pendingApprovedAudio=new PendingApprovedAudio(
            scoped.trackId,scoped.albumId,scoped.editionId,allowedOrigin,
            scoped.durationMs,scoped);
        NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.GRANT_ADMITTED);
        notifyAll(); // bounded Exo pre-prepare beta wait only
        return true;
    }

    /** Optional bounded grace window on the native Exo worker, never UI thread. */
    synchronized void awaitLimitedBetaGrantAtPrepare(long maxMs) {
        if(!lifecycle.isEnabled() || !originalSetterSucceeded
                || publisherTrackIdConflict || limitedBetaRequester==null
                || pendingApprovedAudio!=null || originalPeriodPrepareSealed
                || maxMs<=0
                || (!publisherTrackIdCandidatePending
                    && !NativeTrackIdBetaPolicy.allows(originalPublisherTrackIdCandidate)))
            return;
        // Owner-only allowlisted first-prepare grace: the original network
        // preflight + signed MPEG Range check can outlast the former 450ms.
        // Still worker-only, capped and always fail-open to original audio.
        long finish=System.nanoTime()+Math.min(maxMs,3000L)*1000000L;
        while(pendingApprovedAudio==null && !originalPeriodPrepareSealed
                && originalSetterSucceeded && lifecycle.isEnabled()
                && !publisherTrackIdConflict
                && (publisherTrackIdCandidatePending
                    || NativeTrackIdBetaPolicy.allows(originalPublisherTrackIdCandidate))) {
            long remaining=finish-System.nanoTime();
            if(remaining<=0)break;
            try {wait(Math.max(1L,(remaining+999999L)/1000000L));}
            catch(InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                break;
            }
        }
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
        if(approved==null
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
        NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.DECISION_ALTERNATE);
        if(unopenedOriginalDataSource==null) {
            // Selection is committed BEFORE publisher prepare, but factory
            // instantiation must still prove the original creator and source.
            deferredIssuedAudio=approved;
            deferredIssuedGeneration=generation;
            return true;
        }
        boolean routed=nativeExoBytes.armApproved(
            lifecycleGeneration,unopenedOriginalDataSource,
            approved.track,approved.album,approved.edition,approved.durationMs,
            approved.grant,approved.origin,unixClock.getAsLong(),
            decision.source);
        exactAlternateDataSourceInstalled=routed;
        if(routed)NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.DATASOURCE_ARMED);
        if(!routed)lifecycle.stop(); // never report an uninstalled ALTERNATE
        return routed;
    }

    /**
     * A genuine publisher factory-return hook calls this BEFORE the first
     * original open, using the SAME creator Track/Album/source generation and
     * the exact newly constructed DataSource instance. Any prefetch, reused
     * object, Next, owner Stop or second prepare permanently fails closed.
     */
    synchronized boolean armDeferredOriginalDataSource(long generation,
            Object originalTrack,Object originalAlbum,Object originalSource,
            Object unopenedOriginalDataSource) {
        deferredArmEnter++;
        PendingApprovedAudio approved=deferredIssuedAudio;
        if(approved==null) {
            deferredArmNoPending++;
            return false;
        }
        if(deferredIssuedGeneration!=generation) {
            deferredArmGenerationMismatch++;
            return false;
        }
        if(unopenedOriginalDataSource==null) {
            deferredArmSourceNull++;
            return false;
        }
        if(originalPeriodAmbiguous) {
            deferredArmPeriodAmbiguous++;
            return false;
        }
        if(!originalPeriodPrepareSealed) {
            deferredArmPrepareNotSealed++;
            return false;
        }
        if(originalPeriodRef==null) {
            deferredArmPeriodMissing++;
            return false;
        }
        if(!sawOriginalPeriodPrePrepare(generation,originalPeriodRef.get())) {
            deferredArmPrepareNotProven++;
            return false;
        }
        if(!isSuccessfulOriginalSource(generation,originalTrack,
                originalAlbum,originalSource)) {
            deferredArmSourceMismatch++;
            return false;
        }
        if(!lifecycle.isEnabled()) {
            deferredArmOwnerDisabled++;
            return false;
        }
        // One opportunity only. An ambiguous second factory call cannot
        // reuse an earlier ticket; the native route itself checks exact grants.
        deferredIssuedAudio=null;
        deferredIssuedGeneration=-1;
        boolean routed=nativeExoBytes.armApproved(
            lifecycleGeneration,unopenedOriginalDataSource,
            approved.track,approved.album,approved.edition,approved.durationMs,
            approved.grant,approved.origin,unixClock.getAsLong(),
            NativeSourceGate.Choice.ALTERNATE);
        exactAlternateDataSourceInstalled=routed;
        if(routed) {
            NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.DATASOURCE_ARMED);
            deferredArmAccepted++;
        } else {
            deferredArmNativeRouteRejected++;
        }
        return routed;
    }

    private static String diagnosticBucket(long count) {
        return count==0?"NONE":count==1?"ONE":count<=4?"FEW":"MANY";
    }
    private static String diagnosticLine(String origin,long count) {
        return "event=AUDIO_EARLY_ADMISSION_SUMMARY;origin="+origin
            +";error="+diagnosticBucket(count)+";thread=OTHER";
    }
    synchronized String[] exportLines() {
        return new String[] {
            diagnosticLine("DEFERRED_ARM_ENTER",deferredArmEnter),
            diagnosticLine("DEFERRED_ARM_NO_PENDING_APPROVED",deferredArmNoPending),
            diagnosticLine("DEFERRED_ARM_GENERATION_MISMATCH",deferredArmGenerationMismatch),
            diagnosticLine("DEFERRED_ARM_SOURCE_NULL",deferredArmSourceNull),
            diagnosticLine("DEFERRED_ARM_PERIOD_AMBIGUOUS",deferredArmPeriodAmbiguous),
            diagnosticLine("DEFERRED_ARM_PREPARE_NOT_SEALED",deferredArmPrepareNotSealed),
            diagnosticLine("DEFERRED_ARM_PERIOD_MISSING",deferredArmPeriodMissing),
            diagnosticLine("DEFERRED_ARM_PREPARE_NOT_PROVEN",deferredArmPrepareNotProven),
            diagnosticLine("DEFERRED_ARM_SOURCE_MISMATCH",deferredArmSourceMismatch),
            diagnosticLine("DEFERRED_ARM_OWNER_DISABLED",deferredArmOwnerDisabled),
            diagnosticLine("DEFERRED_ARM_NATIVE_ROUTE_REJECTED",deferredArmNativeRouteRejected),
            diagnosticLine("DEFERRED_ARM_ACCEPTED",deferredArmAccepted)
        };
    }

    @Override public synchronized void beforeUnverifiedOriginalPeriodPrepare() {
        // An unlinked original MediaPeriod has entered actual prepare.
        // Even if a same-source period later prepares, this generation is
        // no longer UNIQUE; revoke all historical pre-prepare candidates.
        originalPeriodAmbiguous=true;
        deferredIssuedAudio=null;
        deferredIssuedGeneration=-1;
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
                deferredIssuedAudio=null;
                deferredIssuedGeneration=-1;
            } else {
                // Original prepare already executed on this same period;
                // the first pre-open candidate is NOT a reusable ticket.
                // A newly linked/opened source cannot promote a duplicate
                // prepare to a fresh alternate decision.
                prePrepareSourceInstanceRef=null;
            }
            return;
        }
        NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.EXACT_PREPARE);
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
        return exactAlternateDataSourceInstalled
            ?lifecycle.lastIssuedSource():NativeSourceGate.Choice.ORIGINAL;
    }
    synchronized long reservedNativeGeneration() {return lifecycleGeneration;}
    synchronized long currentNativeGeneration() {return lifecycle.generation();}
}
