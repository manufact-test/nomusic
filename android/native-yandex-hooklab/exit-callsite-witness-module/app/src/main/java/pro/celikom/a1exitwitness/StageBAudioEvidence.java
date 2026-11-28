package pro.celikom.a1exitwitness;

import java.util.concurrent.atomic.AtomicLong;
import java.lang.ref.WeakReference;
import java.util.ArrayList;

/**
 * Session-local privacy-safe Stage B evidence from the *actual scoped native
 * module*, not the separate B42 JS / Java models. It records only finite,
 * categorised framework source-reader observations; never bytes, offsets,
 * source addresses, account values, identifiers, signed URLs or file paths.
 *
 * A reader invocation, even one linked by Java identity to MediaExtractor,
 * is NOT proof of the audible current track or an applied CELIKOM replacement.
 * Export runs only when the owner explicitly saves diagnostics.
 */
final class StageBAudioEvidence {
    // Android's Retrofit executor invokes the signed FileInfoApi method on a
    // DIFFERENT thread from the issuer's Gp0/Track request. Bind that exact
    // issuer-supplied numeric key only to a same-key signed tCa creator and
    // exact original player source setter, never to a guessed current track.
    private static final long ASYNC_ISSUER_MAX_AGE_MS = 30_000L;
    private final java.util.function.LongSupplier issuerClock;
    StageBAudioEvidence() { this(() -> System.nanoTime()/1_000_000L); }
    StageBAudioEvidence(java.util.function.LongSupplier clock) {
        if(clock==null) throw new IllegalArgumentException("ISSUER_CLOCK_REQUIRED");
        issuerClock=clock;
    }
    // Up to 16 real descriptor objects weakly held, reference (==) only.
    // Neither source identity, URL nor track fields are ever serialized.
    private final ArrayList<WeakReference<Object>> nativeDescriptors = new ArrayList<>();
    private final ArrayList<WeakReference<Object>> exoSourceInstances = new ArrayList<>();
    // True distinct source *instances*, even after rebind/retry. This bounded
    // weak identity set is independent of track-link generations.
    private final ArrayList<WeakReference<Object>> distinctLinkedReadSources =
        new ArrayList<>();
    private final AtomicLong exoSourceReadProbeBudget = new AtomicLong();
    private final AtomicLong exoSourceInstancesCreated = new AtomicLong();
    private final AtomicLong exoSourceInstancesOpened = new AtomicLong();
    private final AtomicLong exoSourceInstancesRead = new AtomicLong();
    private final AtomicLong exoDescriptorResults = new AtomicLong();
    private final AtomicLong exoFactorySameDescriptor = new AtomicLong();
    private final AtomicLong exoFactoryResults = new AtomicLong();
    private final AtomicLong originalMediaItemAnchors = new AtomicLong();
    private final AtomicLong originalMediaItemDescriptors = new AtomicLong();
    private final AtomicLong originalMediaItemConflicts = new AtomicLong();
    // BETA15: finite labels only, never MediaItem values, identities or URLs.
    // These split the unlinked BETA14 child-factory seam into exact reasons.
    private final AtomicLong originalChildHookRegistered = new AtomicLong();
    private final AtomicLong originalChildEntered = new AtomicLong();
    private final AtomicLong originalChildCreatorMatched = new AtomicLong();
    private final AtomicLong originalChildCreatorMissing = new AtomicLong();
    private final AtomicLong originalChildSetterMatched = new AtomicLong();
    private final AtomicLong originalChildSetterMissing = new AtomicLong();
    private final AtomicLong originalChildSetterSourceDifferent = new AtomicLong();
    // BETA16: bounded nonsecret reason buckets. All original Java identity,
    // scope and grant gates remain fail-closed; no values/IDs/URLs emitted.
    private final AtomicLong childNullItem = new AtomicLong();
    private final AtomicLong childNoAnchors = new AtomicLong();
    private final AtomicLong childLiveDifferentItem = new AtomicLong();
    private final AtomicLong childOnlyExpiredItems = new AtomicLong();
    private final AtomicLong childDuplicateItemAnchor = new AtomicLong();
    private final AtomicLong childConflictedItemAnchor = new AtomicLong();
    private final AtomicLong childWeakWrapperLost = new AtomicLong();
    private final AtomicLong childWeakSourceLost = new AtomicLong();
    private final AtomicLong childWrapperLinkMissing = new AtomicLong();
    private final AtomicLong childWrapperLinkAmbiguous = new AtomicLong();
    private final AtomicLong childOriginalCreatorRejected = new AtomicLong();
    private final AtomicLong childBetaCreatorRejected = new AtomicLong();
    // BETA17: read-only, identity-only comparison of the caller dA9/gA9
    // objects in signed iLb.<init> and lLb.if. NOT an approval/binding gate.
    private final AtomicLong childCallerContextUnavailable = new AtomicLong();
    private final AtomicLong childCallerPairSameItem = new AtomicLong();
    private final AtomicLong childCallerPairDifferentItem = new AtomicLong();
    private final AtomicLong childCallerPairAmbiguous = new AtomicLong();
    private final AtomicLong childCallerOwnerOnly = new AtomicLong();
    private final AtomicLong childCallerConfigOnly = new AtomicLong();
    private final AtomicLong childCallerNoMatch = new AtomicLong();
    private final AtomicLong childCoroutineScopeMatch = new AtomicLong();
    private final AtomicLong childCoroutineScopeReject = new AtomicLong();
    private final AtomicLong childCoroutineDescriptorLinks = new AtomicLong();
    private final AtomicLong exoOpenResults = new AtomicLong();
    private final AtomicLong exoPositiveReads = new AtomicLong();
    private final AtomicLong exoEndOfSource = new AtomicLong();
    private final AtomicLong exoFailures = new AtomicLong();
    private final AtomicLong fileInfoResults = new AtomicLong();
    private final AtomicLong directDownloadInfoResults = new AtomicLong();
    private final AtomicLong reader0 = new AtomicLong();
    private final AtomicLong reader1 = new AtomicLong();
    private final AtomicLong extractor0 = new AtomicLong();
    private final AtomicLong extractor1 = new AtomicLong();
    private final AtomicLong extractorOther = new AtomicLong();
    private final AtomicLong sameObjectReads = new AtomicLong();
    private final AtomicLong positiveReads = new AtomicLong();
    private final AtomicLong endOfSourceReads = new AtomicLong();
    private final AtomicLong failedReads = new AtomicLong();

    // Exact selected-track Flow -> native wrapper -> descriptor -> Exo factory
    // continuity. All identities are compared only with ==. The exact
    // descriptor is temporarily retained after the factory handoff.
    private static final class NativeTrackSourceLink {
        WeakReference<Object> track;
        WeakReference<Object> wrapper;
        WeakReference<Object> descriptor;
        // BETA27: bounded lineage-local retention, not an alternative identity
        // or approval path. Keep the witnessed descriptor alive through first
        // OPEN; release on touch or descriptor rebind.
        Object firstOpenDescriptorPin;
        WeakReference<Object> factoryResult;
        WeakReference<Object> sourceInstance;
        WeakReference<Object> pendingFirstOpenSource;
        WeakReference<Object> albumInstance;
        // True only for the signed creator-owned tCa born BEFORE its Track
        // entered Flow. Keep NAV40 historical 12/16 verdicts unchanged,
        // while allowing exact original Exo descriptor continuity.
        boolean creatorOnlyAtBirth;
        // A positive read is only attributable after open() succeeded on
        // THIS source and THIS lineage. Never rely on aggregate read counts.
        boolean sourceOpened;
        boolean sourceEverTouched;
        boolean sourceReadAfterOpen;
        boolean sourceAlbumReadAfterOpen;
        // Durable, value-free proof that sourceInstance was linked through the
        // exact descriptor -> factory identity chain. Vendor descriptor/factory
        // objects may be collected after first OPEN; this bit remains bound to
        // the current weak sourceInstance and resets on every lineage rebind.
        boolean factorySourceIdentityBound;
        // NAV53: only a DataSource whose deferred route arm succeeded is
        // committed for this descriptor generation. Pending arm is protected
        // separately so concurrent sibling products cannot race the decision.
        boolean firstOpenSourceCommitted;
    }
    private static final class TrackAlbumLink {
        WeakReference<Object> track;
        WeakReference<Object> album;
        boolean conflicted;
    }
    private static final class TrackContinuationLink {
        WeakReference<Object> continuation;
        WeakReference<Object> track;
        boolean conflicted;
    }
    // Exact Fp0 continuation instances only; no reads of Track or coroutine fields.
    private final ArrayList<TrackContinuationLink> trackContinuations = new ArrayList<>();
    private static final class MainSourceContinuationLink {
        WeakReference<Object> continuation;
        WeakReference<Object> wrapper;
        boolean conflicted;
    }
    private final ArrayList<MainSourceContinuationLink> mainSourceContinuations =
        new ArrayList<>();
    private final ArrayList<WeakReference<Object>> nativeTrackFlowItems = new ArrayList<>();
    private final ArrayList<TrackAlbumLink> nativeTrackAlbumLinks = new ArrayList<>();
    private final ArrayList<NativeTrackSourceLink> nativeTrackSourceLinks = new ArrayList<>();
    /**
     * Factory products are not necessarily opened in creation order.
     * Preserve every bounded original instance identity independently of
     * the link's latest construction witness. Never select by newest item.
     */
    private static final class ExactFactorySourceBirth {
        final WeakReference<Object> source;
        final WeakReference<Object> factory;
        final WeakReference<Object> nestedFactory;
        final NativeTrackSourceLink link;
        boolean conflicted;
        ExactFactorySourceBirth(Object source,Object factory,
                NativeTrackSourceLink link,Object nestedFactory) {
            this.source=new WeakReference<>(source);
            this.factory=new WeakReference<>(factory);
            this.nestedFactory=nestedFactory==null
                ?null:new WeakReference<>(nestedFactory);
            this.link=link;
        }
    }
    private final ArrayList<ExactFactorySourceBirth> exactFactorySourceBirths=
        new ArrayList<>();
    private boolean exactFactoryBirthsSaturated;

    private static final class PendingNestedFactorySourceBirth {
        final WeakReference<Object> source;
        final WeakReference<Object> nestedFactory;
        PendingNestedFactorySourceBirth(Object source,Object nestedFactory) {
            this.source=new WeakReference<>(source);
            this.nestedFactory=new WeakReference<>(nestedFactory);
        }
    }
    // A scope exists only while the exact signed outer c.for factory is
    // executing. Its nested $b.for products are held briefly until c.for
    // returns and onExoFactoryCreated() has installed the descriptor link.
    static final class ExactNestedFactorySourceScope {
        final ExactNestedFactorySourceScope previous;
        final ArrayList<PendingNestedFactorySourceBirth> births=
            new ArrayList<>();
        boolean saturated;
        ExactNestedFactorySourceScope(ExactNestedFactorySourceScope previous) {
            this.previous=previous;
        }
    }
    private final ThreadLocal<ExactNestedFactorySourceScope>
        activeExactNestedFactorySourceScope=new ThreadLocal<>();

    // BETA25: finite first-open rejection evidence. These counters never
    // export object identities, IDs, URLs, source addresses or audio bytes.
    private final AtomicLong firstOpenHookEntered = new AtomicLong();
    private final AtomicLong firstOpenCandidateRejected = new AtomicLong();
    private final AtomicLong firstOpenSourceNull = new AtomicLong();
    private final AtomicLong firstOpenFactoryBirthsSaturated = new AtomicLong();
    private final AtomicLong firstOpenTouchedHistorySaturated = new AtomicLong();
    private final AtomicLong firstOpenSourceAlreadyTouched = new AtomicLong();
    private final AtomicLong firstOpenBirthNotFound = new AtomicLong();
    private final AtomicLong firstOpenBirthAmbiguous = new AtomicLong();
    private final AtomicLong firstOpenBirthConflicted = new AtomicLong();
    private final AtomicLong firstOpenFactoryWeakLost = new AtomicLong();
    private final AtomicLong firstOpenLinkMissing = new AtomicLong();
    private final AtomicLong firstOpenFactoryLinkMismatch = new AtomicLong();
    private final AtomicLong firstOpenDescriptorLost = new AtomicLong();
    private final AtomicLong firstOpenTrackLost = new AtomicLong();
    private final AtomicLong firstOpenWrapperLost = new AtomicLong();
    private final AtomicLong firstOpenAlreadyOpened = new AtomicLong();
    private final AtomicLong firstOpenAlreadyTouched = new AtomicLong();
    private final AtomicLong firstOpenReadAfterOpen = new AtomicLong();
    private final AtomicLong firstOpenSiblingTouched = new AtomicLong();
    private final AtomicLong firstOpenWrapperLinkMissing = new AtomicLong();
    private final AtomicLong firstOpenWrapperLinkAmbiguous = new AtomicLong();
    private final AtomicLong firstOpenWrapperLinkRebound = new AtomicLong();
    private final AtomicLong firstOpenFactoryLinkMissing = new AtomicLong();
    private final AtomicLong firstOpenFactoryLinkAmbiguous = new AtomicLong();
    private final AtomicLong firstOpenFactoryLinkRebound = new AtomicLong();
    private final AtomicLong firstOpenOriginalCreatorMissing = new AtomicLong();
    private final AtomicLong firstOpenBetaCreatorMissing = new AtomicLong();
    private final AtomicLong firstOpenCreatorTrackMismatch = new AtomicLong();
    private final AtomicLong firstOpenCreatorTokenMissing = new AtomicLong();
    private final AtomicLong firstOpenAlbumMismatch = new AtomicLong();
    private final AtomicLong firstOpenCandidateAccepted = new AtomicLong();
    private final AtomicLong firstOpenSetterMatch = new AtomicLong();
    private final AtomicLong firstOpenSetterMissing = new AtomicLong();
    private final AtomicLong firstOpenDeferredArmCalled = new AtomicLong();
    private final AtomicLong firstOpenDeferredArmAccepted = new AtomicLong();
    private final AtomicLong firstOpenDeferredArmRejected = new AtomicLong();
    private final AtomicLong firstOpenArmExceptions = new AtomicLong();

    // Original iLb source anchor; child Of6 may be a different Java object.
    // No global/latest wrapper, value-based equality or vendor fields.
    private static final class OriginalMediaSourceItemLink {
        final WeakReference<Object> source,item,wrapper,owner,configuration;
        boolean conflicted;
        OriginalMediaSourceItemLink(Object source,Object item,Object wrapper,
                Object owner,Object configuration) {
            this.source=new WeakReference<>(source);
            this.item=new WeakReference<>(item);
            this.wrapper=new WeakReference<>(wrapper);
            this.owner=new WeakReference<>(owner);
            this.configuration=new WeakReference<>(configuration);
        }
    }
    private final ArrayList<OriginalMediaSourceItemLink>
        originalMediaSourceItems = new ArrayList<>();
    private static final class OriginalChildCoroutineCapture {
        final WeakReference<Object> coroutine,source;
        boolean conflict;
        OriginalChildCoroutineCapture(Object coroutine,Object source) {
            this.coroutine=new WeakReference<>(coroutine);
            this.source=new WeakReference<>(source);
        }
    }
    private final ArrayList<OriginalChildCoroutineCapture> originalChildCaptures =
        new ArrayList<>();
    private final ThreadLocal<ArrayList<OriginalChildCoroutineCapture>>
        activeOriginalChildSourceScopes = new ThreadLocal<>();
    // First open/read/close permanently disqualifies this Java instance as a
    // *fresh* candidate even if a later factory links that SAME instance.
    // Weak, bounded, identity-only; saturation fails closed.
    private final ArrayList<WeakReference<Object>> touchedSourceInstances =
        new ArrayList<>();
    private WeakReference<Object> lastTouchedSource;
    private boolean touchedHistorySaturated;
    private static final int MAX_TOUCHED_SOURCE_INSTANCES = 256;
    private boolean wasSourceTouched(Object source) {
        if(source==null || touchedHistorySaturated)return true;
        if(lastTouchedSource!=null && lastTouchedSource.get()==source)return true;
        for(int i=touchedSourceInstances.size()-1;i>=0;i--) {
            Object prior=touchedSourceInstances.get(i).get();
            if(prior==source) {
                lastTouchedSource=touchedSourceInstances.get(i);
                return true;
            }
            if(prior==null)touchedSourceInstances.remove(i);
        }
        return false;
    }
    private void markSourceTouched(Object source) {
        if(source==null)return;
        // Release only the exact factory lineage, including a touched sibling.
        // Birth records are bounded; do not retain the publisher descriptor
        // after any member has started original or alternate I/O.
        for(ExactFactorySourceBirth birth:exactFactorySourceBirths) {
            if(birth.source.get()!=source)continue;
            NativeTrackSourceLink link=birth.link;
            Object factory=birth.factory.get();
            if(factory!=null && link.factoryResult!=null
                    && link.factoryResult.get()==factory)
                link.firstOpenDescriptorPin=null;
        }
        if(wasSourceTouched(source))return;
        if(touchedSourceInstances.size()>=MAX_TOUCHED_SOURCE_INSTANCES) {
            // No evicted live source may ever be accidentally treated as
            // a new unopened DataSource on a future factory rebind.
            if(touchedSourceInstances.get(0).get()!=null)
                touchedHistorySaturated=true;
            touchedSourceInstances.remove(0);
        }
        lastTouchedSource=new WeakReference<>(source);
        touchedSourceInstances.add(lastTouchedSource);
    }
    // NAV40: exact original tCa creator-owned Track + Album, weak only.
    private static final class WrapperBirth {
        final WeakReference<Object> wrapper;
        // Observed Track is diagnostic identity only. Only creatorTrack below
        // can authorize a Track/Album lineage.
        final WeakReference<Object> observedTrack;
        final WeakReference<Object> creatorTrack;
        final WeakReference<Object> albumAtBirth;
        final int scopeAtBirth;
        final String originalConstructorKey;
        final long bornElapsedMs;
        boolean laterFlowEmitted;
        boolean conflicted;
        WrapperBirth(Object wrapper,int scopeAtBirth,Object observedTrack,Object track,
                Object album,String constructorKey,long bornElapsedMs) {
            this.wrapper=new WeakReference<>(wrapper);
            this.scopeAtBirth=scopeAtBirth;
            this.observedTrack=observedTrack==null?null:new WeakReference<>(observedTrack);
            this.creatorTrack=track==null?null:new WeakReference<>(track);
            this.albumAtBirth=album==null?null:new WeakReference<>(album);
            this.originalConstructorKey=constructorKey;
            this.bornElapsedMs=bornElapsedMs;
        }
    }
    private final ArrayList<WrapperBirth> wrapperBirths = new ArrayList<>();
    // Provenance must originate from the issuer-annotated trackId method on
    // a REAL concrete Retrofit proxy, inside the exact Gp0 Track request.
    // String IDs are never included in exported diagnostics or saved files.
    private static final class PublisherTrackIdLink {
        WeakReference<Object> track,album;
        String id;
        boolean conflict;
    }
    private final ArrayList<PublisherTrackIdLink> publisherTrackIds=new ArrayList<>();
    // Issuer annotation-proven IDs waiting for an exact signed original
    // tCa(String) creator. In-memory only; IDs never leave in diagnostic TXT.
    private static final class AsyncIssuerObservation {
        final String id;
        long observedElapsedMs;
        AsyncIssuerObservation(String value,long now) {
            id=value;observedElapsedMs=now;
        }
    }
    private final ArrayList<AsyncIssuerObservation> unscopedIssuerObservations =
        new ArrayList<>();
    private static boolean inIssuerWindow(long a,long b) {
        if(a<0 || b<0)return false;
        long delta=a>=b?a-b:b-a;
        return delta<=ASYNC_ISSUER_MAX_AGE_MS;
    }
    private void noteUnscopedPublisherId(String id) {
        if(!NativeTrackIdBetaPolicy.allows(id))return;
        long now=issuerClock.getAsLong();
        for(int i=unscopedIssuerObservations.size()-1;i>=0;i--) {
            AsyncIssuerObservation previous=unscopedIssuerObservations.get(i);
            if(!inIssuerWindow(now,previous.observedElapsedMs)
                    || now<previous.observedElapsedMs)
                unscopedIssuerObservations.remove(i);
            else if(id.equals(previous.id)) {
                previous.observedElapsedMs=now;
                NativeTrackIdBetaPolicy.mark(
                    NativeTrackIdBetaPolicy.Step.ISSUER_ASYNC_ID_OBSERVED);
                return;
            }
        }
        if(unscopedIssuerObservations.size()>=3)return; // no eviction of live IDs
        unscopedIssuerObservations.add(new AsyncIssuerObservation(id,now));
        NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.ISSUER_ASYNC_ID_OBSERVED);
    }
    // An expired issuer ticket is a hard rejection: it must never turn into
    // a weaker constructor-only fallback when the callback arrived too late.
    private boolean hasObservedPublisherTicket(String id) {
        for(AsyncIssuerObservation observed:unscopedIssuerObservations)
            if(id!=null && id.equals(observed.id))return true;
        return false;
    }
    private boolean issuerTicketMatchesCreator(WrapperBirth birth) {
        if(birth==null || !NativeTrackIdBetaPolicy.allows(
                birth.originalConstructorKey))return false;
        long now=issuerClock.getAsLong();
        for(AsyncIssuerObservation ticket:unscopedIssuerObservations) {
            if(!birth.originalConstructorKey.equals(ticket.id))continue;
            if(now<ticket.observedElapsedMs
                    || !inIssuerWindow(now,ticket.observedElapsedMs)
                    || !inIssuerWindow(birth.bornElapsedMs,ticket.observedElapsedMs)) {
                NativeTrackIdBetaPolicy.mark(
                    NativeTrackIdBetaPolicy.Step.ISSUER_ASYNC_CREATOR_STALE);
                return false;
            }
            return true;
        }
        return false;
    }
    private WrapperBirth uniqueOriginalCreatorBirth(Object wrapper) {
        if(wrapper==null)return null;
        WrapperBirth birth=null;
        for(WrapperBirth item:wrapperBirths) {
            if(item.wrapper.get()!=wrapper)continue;
            if(birth!=null)return null;
            birth=item;
        }
        return birth;
    }
    // 10AGE/Ramil' beta: publisher-annotated trackId was observed inside
    // exact native Gp0(Track) request, but the publisher's Album Java object
    // was not observed on the owner handset. Separate from strict triple IDs.
    private static final class BetaTrackIdLink {
        final WeakReference<Object> track;
        final String signedId;
        boolean conflict;
        BetaTrackIdLink(Object track,String id) {
            this.track=new WeakReference<>(track);
            signedId=id;
        }
    }
    private final ArrayList<BetaTrackIdLink> betaTrackIds=new ArrayList<>();
    interface AuthenticatedPublisherTrackPrefetch {void warm(String id);}
    private AuthenticatedPublisherTrackPrefetch ownerTrackPrefetch;
    synchronized void setAuthenticatedPublisherTrackPrefetch(
            AuthenticatedPublisherTrackPrefetch prefetch) {
        ownerTrackPrefetch=prefetch;
    }
    private static String numericOriginalId(Object raw) {
        if(!(raw instanceof String) && !(raw instanceof Long)
                && !(raw instanceof Integer))return null;
        String id=String.valueOf(raw);
        return id.matches("[1-9][0-9]{0,23}")?id:null;
    }
    synchronized void onPublisherAnnotatedTrackId(Object raw) {
        // Metadata-only issuer argument witness. Never persist the actual ID,
        // titles, request parameters, selected objects or network URLs.
        if(raw==null) {
            NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.ISSUER_VALUE_NULL);
            return;
        }
        String id=numericOriginalId(raw);
        if(id==null) {
            NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.ISSUER_VALUE_NONNUMERIC);
            return;
        }
        final boolean allowed=NativeTrackIdBetaPolicy.allows(id);
        if(allowed)
            NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.ISSUER_VALUE_TARGET_ALLOWLISTED);
        else if("38436680".equals(id)) // known *other* Ramil' edition, NOT allowed
            NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.ISSUER_VALUE_KNOWN_OTHER_VERSION);
        else
            NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.ISSUER_VALUE_OTHER_NUMERIC);
        Object track=currentScope(activeTrackScopes);
        if(track==null) {
            NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.ISSUER_VALUE_SCOPE_ABSENT);
            if(allowed) {
                NativeTrackIdBetaPolicy.mark(
                    NativeTrackIdBetaPolicy.Step.ISSUER_TRACK_SCOPE_MISSING);
                noteUnscopedPublisherId(id);
                // Start the SAME authenticated prefetch normally started by
                // the in-scope issuer path; no source or grant is admitted here.
                AuthenticatedPublisherTrackPrefetch prefetch=ownerTrackPrefetch;
                if(prefetch!=null)prefetch.warm(id);
            }
            return;
        }
        NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.ISSUER_VALUE_SCOPE_PRESENT);
        Object album=findTrackAlbum(track);
        if(NativeTrackIdBetaPolicy.allows(id)) {
            NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.ISSUER_TRACKID);
            BetaTrackIdLink known=null;
            for(int i=betaTrackIds.size()-1;i>=0;i--) {
                BetaTrackIdLink previous=betaTrackIds.get(i);
                if(previous.track.get()==null)betaTrackIds.remove(i);
                else if(previous.track.get()==track) {
                    if(known!=null) {known.conflict=true;previous.conflict=true;}
                    else known=previous;
                }
            }
            if(known==null) {
                if(betaTrackIds.size()>=32)betaTrackIds.remove(0);
                betaTrackIds.add(new BetaTrackIdLink(track,id));
            } else if(!id.equals(known.signedId)) known.conflict=true;
            AuthenticatedPublisherTrackPrefetch prefetch=ownerTrackPrefetch;
            if(prefetch!=null)prefetch.warm(id);
        }
        // Existing strict triple remains untouched by the beta-only ledger.
        if(album==null)return;
        PublisherTrackIdLink match=null;
        for(int i=publisherTrackIds.size()-1;i>=0;i--) {
            PublisherTrackIdLink link=publisherTrackIds.get(i);
            if(link.track.get()==null || link.album.get()==null)
                publisherTrackIds.remove(i);
            else if(link.track.get()==track) {
                if(match!=null) {
                    match.conflict=true;
                    link.conflict=true;
                    return;
                }
                match=link;
            }
        }
        if(match!=null) {
            if(match.album.get()!=album || !id.equals(match.id))
                match.conflict=true;
            return;
        }
        if(publisherTrackIds.size()>=32)publisherTrackIds.remove(0);
        PublisherTrackIdLink link=new PublisherTrackIdLink();
        link.track=new WeakReference<>(track);
        link.album=new WeakReference<>(album);
        link.id=id;
        publisherTrackIds.add(link);
        AuthenticatedPublisherTrackPrefetch prefetch=ownerTrackPrefetch;
        if(prefetch!=null)prefetch.warm(id);
    }
    /** Exact creator Track+Album + signed tCa(String) key + API trackId. */
    synchronized String exactPublisherTrackIdForCreator(
            Object wrapper,Object originalTrack,Object originalAlbum) {
        Object[] creator=exactCreatorTrackAlbumBeforeSourceSet(wrapper);
        if(creator==null || creator[0]!=originalTrack
                || creator[1]!=originalAlbum)return null;
        WrapperBirth birthMatch=null;
        for(WrapperBirth birth:wrapperBirths) {
            if(birth.wrapper.get()!=wrapper)continue;
            if(birthMatch!=null)return null;
            birthMatch=birth;
        }
        if(birthMatch==null || birthMatch.originalConstructorKey==null)
            return null;
        PublisherTrackIdLink matchingId=null;
        for(PublisherTrackIdLink link:publisherTrackIds) {
            if(link.track.get()!=originalTrack)continue;
            if(matchingId!=null)return null;
            matchingId=link;
        }
        return matchingId!=null && !matchingId.conflict
            && matchingId.album.get()==originalAlbum
            && birthMatch.originalConstructorKey.equals(matchingId.id)
            ?matchingId.id:null;
    }
    /**
     * Owner-approved trackId-only route: exact original tCa birth with
     * original concrete Track reference + its ORIGINAL numeric constructor
     * key equal to the real issuer @Query("trackId") in Gp0(Track) scope.
     * Return the *wrapper itself* as explicit beta scope token in the
     * pair's second slot, NEVER pretend that it is the original Album.
     */
    synchronized Object[] exactBetaCreatorWithoutAlbum(Object wrapper) {
        if(wrapper==null)return null;
        WrapperBirth birth=null;
        for(WrapperBirth item:wrapperBirths) {
            if(item.wrapper.get()!=wrapper)continue;
            if(birth!=null)return null;
            birth=item;
        }
        if(birth==null || birth.creatorTrack==null
                || (birth.scopeAtBirth!=12 && birth.scopeAtBirth!=13)
                || !NativeTrackIdBetaPolicy.allows(birth.originalConstructorKey))
            return null;
        Object track=birth.creatorTrack.get();
        if(track==null)return null;
        BetaTrackIdLink match=null;
        for(BetaTrackIdLink item:betaTrackIds) {
            if(item.track.get()!=track)continue;
            if(match!=null)return null;
            match=item;
        }
        if(match==null) {
            // Cached original audio can skip the Retrofit FileInfo call.
            // The unchanged publisher tCa(String) constructor is an alternate
            // source of the SAME allowlisted track key, but ONLY for its exact
            // creator-owned Track, subsequently seen in original Flow.
            if((birth.scopeAtBirth==12 && !birth.laterFlowEmitted)
                    || !wasNativeTrackFlowItem(track))return null;
            boolean hadIssuer=issuerTicketMatchesCreator(birth);
            if(!hadIssuer && hasObservedPublisherTicket(birth.originalConstructorKey))
                return null; // stale ticket, never weaken its window
            match=new BetaTrackIdLink(track,birth.originalConstructorKey);
            if(betaTrackIds.size()>=32)betaTrackIds.remove(0);
            betaTrackIds.add(match);
            NativeTrackIdBetaPolicy.mark(hadIssuer
                ?NativeTrackIdBetaPolicy.Step.ISSUER_ASYNC_CREATOR_BOUND
                :NativeTrackIdBetaPolicy.Step.ORIGINAL_CREATOR_KEY_CONFIRMED);
            if(hadIssuer)NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.ISSUER_TRACKID);
        }
        if(match.conflict
                || !birth.originalConstructorKey.equals(match.signedId))return null;
        NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.EXACT_BETA_CREATOR);
        return new Object[]{track,wrapper};
    }
    synchronized Object[] exactCreatorTrackAlbumOrBetaBeforeSourceSet(Object wrapper) {
        Object[] original=exactCreatorTrackAlbumBeforeSourceSet(wrapper);
        return original!=null?original:exactBetaCreatorWithoutAlbum(wrapper);
    }

    /**
     * Bounded pre-prepare wait is justified only for this exact album-present
     * tCa creator birth whose allowlisted Track has not yet emitted its same
     * original Flow item. Stale unscoped issuer tickets never extend the wait.
     */
    synchronized boolean mayResolvePublisherTrackIdAfterFlow(
            Object wrapper,Object track,Object album) {
        if(wrapper==null || track==null || album==null)return false;
        WrapperBirth birth=null;
        for(WrapperBirth item:wrapperBirths) {
            if(item.wrapper.get()!=wrapper)continue;
            if(birth!=null)return false;
            birth=item;
        }
        if(birth==null || birth.scopeAtBirth!=12 || birth.laterFlowEmitted
                || birth.creatorTrack==null || birth.creatorTrack.get()!=track
                || !NativeTrackIdBetaPolicy.allows(birth.originalConstructorKey))
            return false;
        Object albumAtBirth=birth.albumAtBirth==null?null:birth.albumAtBirth.get();
        if(albumAtBirth!=album || findTrackAlbum(track)!=album)return false;
        return !hasObservedPublisherTicket(birth.originalConstructorKey)
            || issuerTicketMatchesCreator(birth);
    }

    synchronized String exactPublisherTrackIdForCreatorOrBeta(
            Object wrapper,Object track,Object albumOrBetaToken) {
        if(albumOrBetaToken==wrapper) {
            Object[] exact=exactBetaCreatorWithoutAlbum(wrapper);
            if(exact==null || exact[0]!=track)return null;
            WrapperBirth birth=null;
            for(WrapperBirth item:wrapperBirths) {
                if(item.wrapper.get()==wrapper) {
                    if(birth!=null)return null;
                    birth=item;
                }
            }
            return birth==null?null:birth.originalConstructorKey;
        }
        String strict=exactPublisherTrackIdForCreator(
            wrapper,track,albumOrBetaToken);
        if(strict!=null)return strict;
        // The album-present route has the issuer's REAL original Album Java
        // identity, so bind within that stronger original creator chain.
        Object[] exact=exactCreatorTrackAlbumBeforeSourceSet(wrapper);
        if(exact==null || exact[0]!=track || exact[1]!=albumOrBetaToken)
            return null;
        WrapperBirth birth=uniqueOriginalCreatorBirth(wrapper);
        if(birth==null || !NativeTrackIdBetaPolicy.allows(
                birth.originalConstructorKey))return null;
        for(PublisherTrackIdLink existing:publisherTrackIds)
            if(existing.track.get()==track)return null; // conflict never overwritten
        for(BetaTrackIdLink existing:betaTrackIds)
            if(existing.track.get()==track)return null;
        if(!issuerTicketMatchesCreator(birth)) {
            if(hasObservedPublisherTicket(birth.originalConstructorKey)
                    || !wasNativeTrackFlowItem(track)
                    || (birth.scopeAtBirth==12 && !birth.laterFlowEmitted))
                return null;
            // Original signed tCa(String), same Track+Album+wrapper and Flow.
            // No guessed latest ID, UI title, network rewriting or second player.
            NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.ORIGINAL_CREATOR_KEY_CONFIRMED);
            return birth.originalConstructorKey;
        }
        if(publisherTrackIds.size()>=32)publisherTrackIds.remove(0);
        PublisherTrackIdLink linked=new PublisherTrackIdLink();
        linked.track=new WeakReference<>(track);
        linked.album=new WeakReference<>(albumOrBetaToken);
        linked.id=birth.originalConstructorKey;
        publisherTrackIds.add(linked);
        NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.ISSUER_ASYNC_CREATOR_BOUND);
        NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.ISSUER_TRACKID);
        return exactPublisherTrackIdForCreator(
            wrapper,track,albumOrBetaToken);
    }
    private final ThreadLocal<ArrayList<WeakReference<Object>>> activeTrackScopes = new ThreadLocal<>();
    private final ThreadLocal<ArrayList<WeakReference<Object>>> activeWrapperScopes = new ThreadLocal<>();
    // NAV37: exact signed tCa creator method -> owner parameter -> Track field scope.
    private final ThreadLocal<ArrayList<WeakReference<Object>>> activeTcaCreatorOwners =
        new ThreadLocal<>();
    private final AtomicLong nativeTrackFlowEmits = new AtomicLong();
    private final AtomicLong nativeTrackAlbumConstructorLinks = new AtomicLong();
    private final AtomicLong nativeTrackAlbumFlowLinks = new AtomicLong();
    private final AtomicLong nativeTrackAlbumConflicts = new AtomicLong();
    private final AtomicLong trackWrapperAlbumLinks = new AtomicLong();
    private final AtomicLong trackDescriptorAlbumLinks = new AtomicLong();
    private final AtomicLong trackFactoryAlbumLinks = new AtomicLong();
    private final AtomicLong trackSourceAlbumLinks = new AtomicLong();
    private final AtomicLong trackSourceAlbumOpenLinks = new AtomicLong();
    private final AtomicLong trackSourceAlbumReadLinks = new AtomicLong();
    private final AtomicLong nativeTrackSourceRequests = new AtomicLong();
    private final AtomicLong flowTrackSourceSameObject = new AtomicLong();
    private final AtomicLong nativeTrackWrapperLinks = new AtomicLong();
    private final AtomicLong nativeTrackWrapperLinksRestored = new AtomicLong();
    // NAV49 / BETA24 owner export: one Track may own several live tCa wrappers. Keep each wrapper's
    // descriptor/factory/source chain independent; never rebind by Track alone.
    private final AtomicLong nativeTrackWrapperSameTrackParallel = new AtomicLong();
    private final AtomicLong nativeTrackWrapperSameIdentityRefresh = new AtomicLong();
    private final AtomicLong nativeTrackWrapperIdentityConflict = new AtomicLong();
    private final AtomicLong nativeTrackWrapperRestoredWithSameTrackSibling = new AtomicLong();
    private final AtomicLong nativeTrackWrapperConstructed = new AtomicLong();
    private final AtomicLong tcaCreatorOwnerEnter = new AtomicLong();
    private final AtomicLong tcaCreatorOwnerNull = new AtomicLong();
    private final AtomicLong tcaCreatorTrackFieldRead = new AtomicLong();
    private final AtomicLong tcaCreatorTrackFieldNull = new AtomicLong();
    private final AtomicLong tcaCreatorTrackFieldFailed = new AtomicLong();
    private final AtomicLong tcaCreatorWrapperConstructed = new AtomicLong();
    private final AtomicLong tcaCreatorWrapperNoTrack = new AtomicLong();
    private final AtomicLong tcaCreatorWrapperNotFlow = new AtomicLong();
    private final AtomicLong tcaCreatorWrapperFlowMatch = new AtomicLong();
    private final AtomicLong tcaCreatorWrapperNoAlbum = new AtomicLong();
    private final AtomicLong tcaCreatorWrapperAlbumLink = new AtomicLong();
    // NAV38: last 32 weak exact creator-owned Track refs not in Flow at birth.
    private final ArrayList<WeakReference<Object>> creatorAwaitingFlow = new ArrayList<>();
    private final AtomicLong creatorNotFlowAlbumObserved = new AtomicLong();
    private final AtomicLong creatorNotFlowAlbumUnobserved = new AtomicLong();
    private final AtomicLong creatorFlowLaterSameTrack = new AtomicLong();
    private final AtomicLong creatorFlowLaterAlbumObserved = new AtomicLong();
    private final AtomicLong nativeMainSourceEnters = new AtomicLong();
    private final AtomicLong nativeTrackContinuationConstructed = new AtomicLong();
    private final AtomicLong trackContinuationRecovered = new AtomicLong();
    private final AtomicLong trackContinuationConflict = new AtomicLong();
    private final AtomicLong mainContinuationConstructed = new AtomicLong();
    private final AtomicLong mainContinuationRecovered = new AtomicLong();
    private final AtomicLong mainContinuationConflict = new AtomicLong();
    private final AtomicLong wrapperMainSourceRequests = new AtomicLong();
    private final AtomicLong wrapperDescriptorLinks = new AtomicLong();
    private final AtomicLong trackDescriptorFactoryLinks = new AtomicLong();
    private final AtomicLong trackFactorySourceLinks = new AtomicLong();
    private final AtomicLong trackSourceOpenLinks = new AtomicLong();
    private final AtomicLong trackSourceReadLinks = new AtomicLong();
    private final AtomicLong trackSourceUnopenedReads = new AtomicLong();
    private final AtomicLong trackSourceDistinctPositiveReads = new AtomicLong();
    private final AtomicLong trackSourceReadProbeBudget = new AtomicLong();
    private final AtomicLong trackSourceUnopenedProbeBudget = new AtomicLong();
    // At most 256 positive read identity scans per linked source window.
    private final AtomicLong trackSourceReadInspectionBudget = new AtomicLong();
    private final AtomicLong trackSourceInspectionExhausted = new AtomicLong();
    private final AtomicLong linkedSourceCloseCalls = new AtomicLong();
    private final AtomicLong liveLinkedSourceLookups = new AtomicLong();
    private final AtomicLong liveLinkedSourceCreatorMatched = new AtomicLong();
    private final AtomicLong liveLinkedSourceCreatorMissing = new AtomicLong();
    private final AtomicLong liveLinkedSourceWrapperLinkMissing = new AtomicLong();
    private final AtomicLong liveLinkedSourceLinkMismatch = new AtomicLong();
    private final AtomicLong liveLinkedSourceFactorySourceUnbound = new AtomicLong();
    private final AtomicLong liveLinkedSourceInstanceNotLinked = new AtomicLong();
    private final AtomicLong liveLinkedSourceInstanceWeakLost = new AtomicLong();
    private final AtomicLong liveLinkedSourceReverseLinkMismatch = new AtomicLong();
    private final AtomicLong liveLinkedSourceBetaRecheckFailed = new AtomicLong();
    private final AtomicLong liveLinkedSourceAlbumMismatch = new AtomicLong();
    private final AtomicLong liveLinkedSourceResolved = new AtomicLong();
    private volatile boolean hasTrackSourceLink;

    // Bounded without storing URLs, media bytes, offsets or returned sizes.
    private static void mark(AtomicLong bucket) {
        for (;;) {
            long old = bucket.get();
            if (old >= 32) return;
            if (bucket.compareAndSet(old, old + 1)) return;
        }
    }


    private static void pushScope(
            ThreadLocal<ArrayList<WeakReference<Object>>> local, Object value) {
        // A null nested frame must shadow its parent rather than expose a
        // stale outer selected track/wrapper. The weak ref may hold null.
        ArrayList<WeakReference<Object>> stack = local.get();
        if (stack == null) {
            stack = new ArrayList<>();
            local.set(stack);
        }
        stack.add(new WeakReference<>(value));
    }

    private static Object currentScope(
            ThreadLocal<ArrayList<WeakReference<Object>>> local) {
        ArrayList<WeakReference<Object>> stack = local.get();
        if (stack == null || stack.isEmpty()) return null;
        // Never fall back to an outer frame if a nested frame was null or GC'd.
        return stack.get(stack.size()-1).get();
    }

    private static void popScope(
            ThreadLocal<ArrayList<WeakReference<Object>>> local) {
        ArrayList<WeakReference<Object>> stack = local.get();
        if (stack == null) return;
        if (!stack.isEmpty()) stack.remove(stack.size()-1);
        if (stack.isEmpty()) local.remove();
    }

    private static boolean hasScope(
            ThreadLocal<ArrayList<WeakReference<Object>>> local) {
        ArrayList<WeakReference<Object>> stack=local.get();
        return stack!=null && !stack.isEmpty();
    }

    void enterNativeTcaCreatorOwner(Object owner) {
        pushScope(activeTcaCreatorOwners,owner);
        mark(tcaCreatorOwnerEnter);
        if(owner==null)mark(tcaCreatorOwnerNull);
    }

    boolean hasNativeTcaCreatorOwnerScope() {
        return hasScope(activeTcaCreatorOwners);
    }

    Object currentNativeTcaCreatorOwner() {
        return currentScope(activeTcaCreatorOwners);
    }

    void exitNativeTcaCreatorOwner() {
        popScope(activeTcaCreatorOwners);
    }

    // status: 1 exact Track-typed field read, 2 null field/owner, 3 failed or
    // mismatched field. A null frame deliberately shadows any outer Gp0 scope.
    void enterNativeTcaCreatorTrackScope(Object track,int status) {
        pushScope(activeTrackScopes,track);
        if(status==1 && track!=null)mark(tcaCreatorTrackFieldRead);
        else if(status==2 || track==null)mark(tcaCreatorTrackFieldNull);
        else mark(tcaCreatorTrackFieldFailed);
    }

    void exitNativeTcaCreatorTrackScope() {
        popScope(activeTrackScopes);
    }

    private Object findTrackAlbum(Object track) {
        if (track==null) return null;
        TrackAlbumLink match=null;
        for (int i=nativeTrackAlbumLinks.size()-1;i>=0;i--) {
            TrackAlbumLink link=nativeTrackAlbumLinks.get(i);
            Object linkedTrack=link.track==null ? null : link.track.get();
            if (linkedTrack==null) {
                nativeTrackAlbumLinks.remove(i);
                continue;
            }
            if (linkedTrack==track) {
                if (match!=null) return null;
                match=link;
            }
        }
        return match==null || match.conflicted || match.album==null
            ? null : match.album.get();
    }

    synchronized void onNativeTrackAlbumConstructed(Object track,Object album) {
        if (track==null || album==null) return;
        for (int i=nativeTrackAlbumLinks.size()-1;i>=0;i--) {
            TrackAlbumLink link=nativeTrackAlbumLinks.get(i);
            Object linkedTrack=link.track==null ? null : link.track.get();
            if (linkedTrack==null) {
                nativeTrackAlbumLinks.remove(i);
                continue;
            }
            if (linkedTrack==track) {
                if (link.conflicted || link.album==null || link.album.get()!=album) {
                    link.conflicted=true;
                    link.album=null;
                    mark(nativeTrackAlbumConflicts);
                    for (NativeTrackSourceLink source:nativeTrackSourceLinks) {
                        if (source.track!=null && source.track.get()==track) {
                            source.albumInstance=null;
                            source.sourceAlbumReadAfterOpen=false;
                        }
                    }
                }
                return;
            }
        }
        if (nativeTrackAlbumLinks.size()>=32) nativeTrackAlbumLinks.remove(0);
        TrackAlbumLink link=new TrackAlbumLink();
        link.track=new WeakReference<>(track);
        link.album=new WeakReference<>(album);
        nativeTrackAlbumLinks.add(link);
        mark(nativeTrackAlbumConstructorLinks);
    }

    // NAV35: resolve NAV34's real-phone NO_LINK=MANY, without selecting a
    // guessed Track/Album. All checks use weak == Java refs only.
    // 1 exact historical Flow/Track/Album/tCa, -1 explicit different album;
    // 2 exact tCa missing, 3 multiple tracks share tCa, 4 track weak-lost,
    // 5 no album captured at wrapper creation, 6 album weak-lost,
    // 7 Flow track not retained, 8 constructor album absent/conflicted.
    // Even MATCH is historical structural identity, NEVER selected edition
    // or queue generation and NEVER permission to replace original audio.
    synchronized int classifyNativeTrackAlbumForWrapper(Object wrapper) {
        if(wrapper==null)return 2;
        NativeTrackSourceLink found=null;
        for(NativeTrackSourceLink candidate:nativeTrackSourceLinks) {
            if(candidate.wrapper==null || candidate.wrapper.get()!=wrapper)continue;
            if(found!=null)return 3;
            found=candidate;
        }
        if(found==null || found.creatorOnlyAtBirth)
            return classifyMissingWrapperBirth(wrapper);
        Object track=found.track==null?null:found.track.get();
        if(track==null)return 4;
        if(found.albumInstance==null)return 5;
        Object album=found.albumInstance.get();
        if(album==null)return 6;
        if(!wasNativeTrackFlowItem(track))return 7;
        Object observed=findTrackAlbum(track);
        if(observed==null)return 8;
        return observed==album?1:-1;
    }

    /**
     * Resolves only the exact original Track + Album Java objects already
     * proven for this wrapper. Called synchronously from the live original
     * source/PeriodID renderer gate; no names, IDs, fields or sound bytes read.
     *
     * A holder from a different track/Flow, any ambiguous wrapper, a changed
     * Album association or an expired weak link fails closed. Returning these
     * objects does NOT by itself prove edition, replay generation or PCM.
     * Caller must never cache the returned pair across Play/Next/reopen.
     */
    synchronized Object[] exactOriginalTrackAlbumForWrapper(Object wrapper) {
        int status=classifyNativeTrackAlbumForWrapper(wrapper);
        if(status!=1 && status!=16 && status!=20)return null;
        Object track=null,album=null;
        if(status==1) {
            NativeTrackSourceLink matched=null;
            for(NativeTrackSourceLink link:nativeTrackSourceLinks) {
                if(link.wrapper==null || link.wrapper.get()!=wrapper)continue;
                if(matched!=null)return null;
                matched=link;
            }
            if(matched==null || matched.track==null
                    || matched.albumInstance==null)return null;
            track=matched.track.get();
            album=matched.albumInstance.get();
        } else {
            WrapperBirth matched=null;
            for(WrapperBirth birth:wrapperBirths) {
                if(birth.wrapper.get()!=wrapper)continue;
                if(matched!=null)return null;
                matched=birth;
            }
            if(matched==null || matched.creatorTrack==null
                    || matched.albumAtBirth==null
                    || status==16 && (matched.scopeAtBirth!=12 || !matched.laterFlowEmitted)
                    || status==20 && matched.scopeAtBirth!=14)return null;
            track=matched.creatorTrack.get();
            album=matched.albumAtBirth.get();
        }
        if(track==null || album==null || !wasNativeTrackFlowItem(track)
                || findTrackAlbum(track)!=album)return null;
        // Recheck within the same monitor: no stale positive classification
        // can be turned into a handle after an object identity conflict.
        if(classifyNativeTrackAlbumForWrapper(wrapper)!=status)return null;
        return new Object[]{track,album};
    }

    /**
     * Original creator-owned Track + Album BEFORE the player source setter.
     * This is NOT the later Flow/renderer proof and is not a semantic ID.
     * Only one exact wrapper birth and the unchanged original Album are valid.
     * No strings, vendor ID fields, cached source, or media values are read.
     */
    synchronized Object[] exactCreatorTrackAlbumBeforeSourceSet(Object wrapper) {
        if(wrapper==null)return null;
        WrapperBirth found=null;
        for(WrapperBirth birth:wrapperBirths) {
            if(birth.wrapper.get()!=wrapper)continue;
            if(found!=null)return null;
            found=birth;
        }
        if(found==null || (found.scopeAtBirth!=12 && found.scopeAtBirth!=14))
            return null;
        Object track,album;
        if(found.creatorTrack!=null && found.albumAtBirth!=null) {
            // Both creator paths retain their exact weak Track+Album birth
            // references. Scope 12 later enters Flow; scope 14 was already
            // in Flow at birth. Neither depends on the shorter 16-link ring.
            track=found.creatorTrack.get();
            album=found.albumAtBirth.get();
        } else {
            NativeTrackSourceLink linked=findByWrapper(wrapper);
            if(linked==null || linked.track==null || linked.albumInstance==null)
                return null;
            track=linked.track.get();
            album=linked.albumInstance.get();
        }
        if(found.scopeAtBirth==14 && !wasNativeTrackFlowItem(track))return null;
        if(track==null || album==null || findTrackAlbum(track)!=album)return null;
        // A rebinding or conflicting later Flow cannot recycle creator proof.
        for(NativeTrackSourceLink link:nativeTrackSourceLinks) {
            if(link.wrapper==null || link.wrapper.get()!=wrapper)continue;
            if(link.track==null || link.track.get()!=track)return null;
            if(link.albumInstance!=null && link.albumInstance.get()!=album)return null;
        }
        return new Object[]{track,album};
    }

    synchronized void onNativeTrackFlowEmission(Object track) {
        if (track == null) return;
        // Exact same Track emitted after THIS tCa birth; never bind player.
        for(WrapperBirth birth:wrapperBirths) {
            if(birth.scopeAtBirth==12 && birth.creatorTrack!=null
                    && birth.creatorTrack.get()==track)
                birth.laterFlowEmitted=true;
        }
        // Exact == of previously weak-held creator Track; no selected queue claim.
        for(int i=creatorAwaitingFlow.size()-1;i>=0;i--) {
            Object prior=creatorAwaitingFlow.get(i).get();
            if(prior==null)creatorAwaitingFlow.remove(i);
            else if(prior==track) {
                mark(creatorFlowLaterSameTrack);
                if(findTrackAlbum(track)!=null)mark(creatorFlowLaterAlbumObserved);
                creatorAwaitingFlow.remove(i);
            }
        }
        mark(nativeTrackFlowEmits);
        if (findTrackAlbum(track)!=null) mark(nativeTrackAlbumFlowLinks);
        for (int i=nativeTrackFlowItems.size()-1;i>=0;i--) {
            if (nativeTrackFlowItems.get(i).get()==null)
                nativeTrackFlowItems.remove(i);
        }
        if (nativeTrackFlowItems.size()>=32) nativeTrackFlowItems.remove(0);
        nativeTrackFlowItems.add(new WeakReference<>(track));
    }

    private synchronized boolean wasNativeTrackFlowItem(Object track) {
        if (track == null) return false;
        for (WeakReference<Object> item:nativeTrackFlowItems)
            if (item.get()==track) return true;
        return false;
    }

    private TrackContinuationLink findTrackContinuation(Object continuation) {
        if (continuation == null) return null;
        for (int i=trackContinuations.size()-1;i>=0;i--) {
            TrackContinuationLink link=trackContinuations.get(i);
            if (link.continuation==null || link.continuation.get()==null) {
                trackContinuations.remove(i);
                continue;
            }
            if (link.continuation.get()==continuation) return link;
        }
        return null;
    }

    synchronized void onNativeTrackContinuationConstructed(Object continuation) {
        Object track=currentScope(activeTrackScopes);
        if (continuation==null || track==null || !wasNativeTrackFlowItem(track))
            return;
        TrackContinuationLink prior=findTrackContinuation(continuation);
        if (prior!=null) {
            // A continuation reused for a different track is permanently
            // ambiguous for its lifetime, even if called again with null.
            if (prior.track==null || prior.track.get()!=track) {
                prior.conflicted=true;
                prior.track=null;
                mark(trackContinuationConflict);
            }
            return;
        }
        if (trackContinuations.size()>=16) trackContinuations.remove(0);
        TrackContinuationLink link=new TrackContinuationLink();
        link.continuation=new WeakReference<>(continuation);
        link.track=new WeakReference<>(track);
        trackContinuations.add(link);
        mark(nativeTrackContinuationConstructed);
    }

    synchronized void enterNativeTrackSourceRequest(Object track, Object continuation) {
        Object scopedTrack=track;
        TrackContinuationLink link=findTrackContinuation(continuation);
        if (link!=null) {
            Object remembered=link.track==null ? null : link.track.get();
            if (link.conflicted || remembered==null) {
                scopedTrack=null;
            } else if (track==null) {
                // Generated coroutine resume may pass null as its track arg.
                // Recover ONLY by exact instance == of a prior Fp0 constructor.
                scopedTrack=remembered;
                mark(trackContinuationRecovered);
            } else if (track!=remembered) {
                scopedTrack=null;
                link.conflicted=true;
                link.track=null;
                mark(trackContinuationConflict);
            }
        }
        pushScope(activeTrackScopes,scopedTrack); // balanced even for null
        mark(nativeTrackSourceRequests);
        // This counter means the exact Track object was an actual Gp0.new
        // argument. A recovered Fp0 continuation is a different evidence
        // category and must NEVER inflate FLOW_TRACK_SAME_OBJECT.
        if (scopedTrack!=null && scopedTrack==track
                && wasNativeTrackFlowItem(scopedTrack))
            mark(flowTrackSourceSameObject);
    }

    void exitNativeTrackSourceRequest() {
        popScope(activeTrackScopes);
    }

    // NAV40: 16 = same original creator Track/Album entered Flow AFTER birth;
    // 20 = same exact Track/Album was already in Flow AT birth. Both remain
    // historical structural identity only, never selected edition or PCM.
    // 17 absent/conflicted Album; 18 different Album; 19 weak Track/Flow lost.
    private WrapperBirth uniqueWrapperBirth(Object wrapper) {
        if(wrapper==null)return null;
        WrapperBirth found=null;
        for(WrapperBirth birth:wrapperBirths) {
            if(birth.wrapper.get()!=wrapper)continue;
            if(found!=null || birth.conflicted)return null;
            found=birth;
        }
        return found;
    }

    private int classifyMissingWrapperBirth(Object wrapper) {
        if(wrapper==null)return 10;
        WrapperBirth found=null;
        for(WrapperBirth birth:wrapperBirths) {
            if(birth.wrapper.get()!=wrapper)continue;
            if(found!=null)return 15;
            found=birth;
        }
        if(found==null)return 10;
        if(found.conflicted)return 15;
        if(found.scopeAtBirth==14) {
            // Non-tCa wrappers retain the historical missing-link result;
            // only exact creator births carry the Track+Album proof for 20.
            if(found.creatorTrack==null || found.albumAtBirth==null)return 14;
            Object track=found.creatorTrack.get();
            if(track==null || !wasNativeTrackFlowItem(track))return 19;
            Object album=found.albumAtBirth==null?null:found.albumAtBirth.get();
            Object observed=findTrackAlbum(track);
            if(album==null || observed==null)return 17;
            return album==observed?20:18;
        }
        if(found.scopeAtBirth!=12 || !found.laterFlowEmitted)
            return found.scopeAtBirth;
        Object track=found.creatorTrack==null?null:found.creatorTrack.get();
        if(track==null || !wasNativeTrackFlowItem(track))return 19;
        Object album=found.albumAtBirth==null?null:found.albumAtBirth.get();
        Object observed=findTrackAlbum(track);
        if(album==null || observed==null)return 17;
        return album==observed?16:18;
    }

    /**
     * Restore only a lost bounded Track->wrapper link from the unique signed
     * tCa creator birth. The original Track+Album must still be the same live
     * Flow objects. A sibling wrapper for the same Track is a separate lineage,
     * not a conflict; only a duplicate or mismatched identity for THIS wrapper
     * is rejected.
     */
    private NativeTrackSourceLink restoreWrapperLinkFromCreatorBirth(Object wrapper) {
        WrapperBirth birth=uniqueWrapperBirth(wrapper);
        if(birth==null || (birth.scopeAtBirth!=12 && birth.scopeAtBirth!=14)
                || birth.creatorTrack==null || birth.albumAtBirth==null)
            return null;
        if(birth.scopeAtBirth==12 && !birth.laterFlowEmitted)return null;
        Object track=birth.creatorTrack.get(),album=birth.albumAtBirth.get();
        if(track==null || album==null || !wasNativeTrackFlowItem(track)
                || findTrackAlbum(track)!=album)return null;
        boolean siblingSameTrack=false;
        for(int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink existing=nativeTrackSourceLinks.get(i);
            Object existingTrack=existing.track==null?null:existing.track.get();
            Object existingWrapper=existing.wrapper==null?null:existing.wrapper.get();
            if(existingTrack==null || existingWrapper==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if(existingWrapper==wrapper) {
                if(existingTrack!=track)return null;
                return existing;
            }
            if(existingTrack==track)siblingSameTrack=true;
        }
        if(nativeTrackSourceLinks.size()>=16)nativeTrackSourceLinks.remove(0);
        NativeTrackSourceLink restored=new NativeTrackSourceLink();
        restored.track=new WeakReference<>(track);
        restored.wrapper=new WeakReference<>(wrapper);
        restored.albumInstance=new WeakReference<>(album);
        restored.creatorOnlyAtBirth=birth.scopeAtBirth==12;
        nativeTrackSourceLinks.add(restored);
        mark(nativeTrackWrapperLinksRestored);
        if(siblingSameTrack)mark(nativeTrackWrapperRestoredWithSameTrackSibling);
        return restored;
    }
    synchronized void onNativeTrackWrapperCreated(Object wrapper) {
        onNativeTrackWrapperCreated(wrapper,null);
    }
    synchronized void onNativeTrackWrapperCreated(Object wrapper,Object originalConstructorArg) {
        mark(nativeTrackWrapperConstructed);
        boolean fromExactTcaCreator=hasNativeTcaCreatorOwnerScope();
        if(fromExactTcaCreator)mark(tcaCreatorWrapperConstructed);
        Object track=currentScope(activeTrackScopes);
        if(fromExactTcaCreator) {
            if(track==null)mark(tcaCreatorWrapperNoTrack);
            else if(!wasNativeTrackFlowItem(track)) {
                mark(tcaCreatorWrapperNotFlow);
                if(findTrackAlbum(track)!=null)mark(creatorNotFlowAlbumObserved);
                else mark(creatorNotFlowAlbumUnobserved);
                // Only bounded historical observation, never a source/player link.
                if(wrapper!=null) {
                    boolean seen=false;
                    for(int i=creatorAwaitingFlow.size()-1;i>=0;i--) {
                        Object prior=creatorAwaitingFlow.get(i).get();
                        if(prior==null)creatorAwaitingFlow.remove(i);
                        else if(prior==track)seen=true;
                    }
                    if(!seen) {
                        if(creatorAwaitingFlow.size()>=32)creatorAwaitingFlow.remove(0);
                        creatorAwaitingFlow.add(new WeakReference<>(track));
                    }
                }
            }
            else {
                mark(tcaCreatorWrapperFlowMatch);
                if(findTrackAlbum(track)==null)mark(tcaCreatorWrapperNoAlbum);
                else mark(tcaCreatorWrapperAlbumLink);
            }
        }
        boolean wrapperBirthIdentityConflict=false;
        if(wrapper!=null) {
            int atBirth=track==null?11:!wasNativeTrackFlowItem(track)?12:
                findTrackAlbum(track)==null?13:14;
            Object birthTrack=fromExactTcaCreator
                && (atBirth==12 || atBirth==13 || atBirth==14)?track:null;
            Object birthAlbum=fromExactTcaCreator && (atBirth==12 || atBirth==14)
                ?findTrackAlbum(track):null;
            String birthKey=fromExactTcaCreator
                ?numericOriginalId(originalConstructorArg):null;
            WrapperBirth prior=uniqueWrapperBirth(wrapper);
            boolean wrapperSeen=false;
            if(prior==null) {
                for(WrapperBirth existing:wrapperBirths) {
                    if(existing.wrapper.get()!=wrapper)continue;
                    wrapperSeen=true;
                    existing.conflicted=true;
                }
            }
            if(prior==null && !wrapperSeen) {
                if(wrapperBirths.size()>=64)wrapperBirths.remove(0);
                wrapperBirths.add(new WrapperBirth(wrapper,atBirth,track,birthTrack,
                    birthAlbum,birthKey,issuerClock.getAsLong()));
            } else if(prior==null) {
                wrapperBirthIdentityConflict=true;
            } else {
                Object priorObservedTrack=prior.observedTrack==null
                    ?null:prior.observedTrack.get();
                Object priorTrack=prior.creatorTrack==null?null:prior.creatorTrack.get();
                Object priorAlbum=prior.albumAtBirth==null?null:prior.albumAtBirth.get();
                boolean sameKey=prior.originalConstructorKey==null
                    ?birthKey==null:prior.originalConstructorKey.equals(birthKey);
                if(prior.scopeAtBirth!=atBirth || priorObservedTrack!=track
                        || priorTrack!=birthTrack || priorAlbum!=birthAlbum || !sameKey) {
                    prior.conflicted=true;
                    wrapperBirthIdentityConflict=true;
                }
            }
        }
        if (track==null || wrapper==null) return;
        // Warm a strictly allowlisted first-party constructor key even if
        // original FileInfo is already cached and Retrofit is never invoked.
        // Warm never authorizes a source: the real setter and signed grant do.
        if(fromExactTcaCreator) {
            String key=numericOriginalId(originalConstructorArg);
            if(NativeTrackIdBetaPolicy.allows(key)) {
                AuthenticatedPublisherTrackPrefetch prefetch=ownerTrackPrefetch;
                if(prefetch!=null)prefetch.warm(key);
            }
        }
        // In the issuer-signed creator, Track may reach Flow AFTER tCa
        // construction. Preserve the creator's exact Album/source lineage
        // without falsely promoting historical NAV40 Flow status.
        // atBirth is local to the weak birth-record branch above;
        // equivalent immutable birth condition is verified here again.
        boolean creatorOnlyAtBirth=fromExactTcaCreator
            && !wasNativeTrackFlowItem(track)
            && (findTrackAlbum(track)!=null || NativeTrackIdBetaPolicy.allows(
                numericOriginalId(originalConstructorArg)));
        if(!wasNativeTrackFlowItem(track) && !creatorOnlyAtBirth)return;
        NativeTrackSourceLink link=null;
        boolean sameTrackSibling=false;
        boolean existingSameWrapperConflict=false;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink candidate=nativeTrackSourceLinks.get(i);
            Object candidateTrack=candidate.track==null?null:candidate.track.get();
            Object candidateWrapper=candidate.wrapper==null?null:candidate.wrapper.get();
            if (candidateTrack==null || candidateWrapper==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if(candidateWrapper==wrapper) {
                if(wrapperBirthIdentityConflict || candidateTrack!=track) {
                    // Preserve both conflicting identities in the bounded
                    // registry. findByWrapper() will now see two exact wrapper
                    // entries and reject them as ambiguous (status 3).
                    existingSameWrapperConflict=true;
                    mark(nativeTrackWrapperIdentityConflict);
                    continue;
                }
                // A duplicate observation of the SAME wrapper is not a new
                // lineage generation. Preserve its descriptor/factory/source
                // and all touched/open state; never make it fresh again.
                mark(nativeTrackWrapperSameIdentityRefresh);
                Object album=findTrackAlbum(track);
                Object priorAlbum=candidate.albumInstance==null
                    ?null:candidate.albumInstance.get();
                if(priorAlbum!=null && album!=null && priorAlbum!=album) {
                    existingSameWrapperConflict=true;
                    mark(nativeTrackWrapperIdentityConflict);
                    continue;
                }
                if(candidate.albumInstance==null && album!=null)
                    candidate.albumInstance=new WeakReference<>(album);
                if(album!=null)mark(trackWrapperAlbumLinks);
                return;
            }
            if(candidateTrack==track)sameTrackSibling=true;
        }
        if(wrapperBirthIdentityConflict && !existingSameWrapperConflict) {
            mark(nativeTrackWrapperIdentityConflict);
            return;
        }
        if (link==null) {
            if (nativeTrackSourceLinks.size()>=16) nativeTrackSourceLinks.remove(0);
            link=new NativeTrackSourceLink();
            link.track=new WeakReference<>(track);
            link.wrapper=new WeakReference<>(wrapper);
            nativeTrackSourceLinks.add(link);
            if(sameTrackSibling)mark(nativeTrackWrapperSameTrackParallel);
        }
        Object album=findTrackAlbum(track);
        link.albumInstance=album==null ? null : new WeakReference<>(album);
        if (album!=null) mark(trackWrapperAlbumLinks);
        link.creatorOnlyAtBirth=creatorOnlyAtBirth;
        link.descriptor=null;
        link.firstOpenDescriptorPin=null;
        link.factoryResult=null;
        link.sourceInstance=null;
        link.factorySourceIdentityBound=false;
        link.sourceOpened=false;
        link.sourceEverTouched=false;
        link.sourceReadAfterOpen=false;
        link.sourceAlbumReadAfterOpen=false;
        if(!creatorOnlyAtBirth)mark(nativeTrackWrapperLinks);
    }

    private MainSourceContinuationLink findMainSourceContinuation(Object continuation) {
        if (continuation==null) return null;
        for (int i=mainSourceContinuations.size()-1;i>=0;i--) {
            MainSourceContinuationLink link=mainSourceContinuations.get(i);
            if (link.continuation==null || link.continuation.get()==null) {
                mainSourceContinuations.remove(i);
                continue;
            }
            if (link.continuation.get()==continuation) return link;
        }
        return null;
    }

    synchronized void onNativeMainContinuationConstructed(Object continuation) {
        Object wrapper=currentScope(activeWrapperScopes);
        if (continuation==null || wrapper==null || !hasWrapperLink(wrapper)) return;
        MainSourceContinuationLink prior=findMainSourceContinuation(continuation);
        if (prior!=null) {
            if (prior.wrapper==null || prior.wrapper.get()!=wrapper) {
                prior.conflicted=true;
                prior.wrapper=null;
                mark(mainContinuationConflict);
            }
            return;
        }
        if (mainSourceContinuations.size()>=16) mainSourceContinuations.remove(0);
        MainSourceContinuationLink link=new MainSourceContinuationLink();
        link.continuation=new WeakReference<>(continuation);
        link.wrapper=new WeakReference<>(wrapper);
        mainSourceContinuations.add(link);
        mark(mainContinuationConstructed);
    }

    synchronized void enterNativeMainSourceRequest(Object wrapper,Object continuation) {
        Object scopedWrapper=wrapper;
        MainSourceContinuationLink link=findMainSourceContinuation(continuation);
        if (link!=null) {
            Object remembered=link.wrapper==null ? null : link.wrapper.get();
            if (link.conflicted || remembered==null) {
                scopedWrapper=null;
            } else if (wrapper==null) {
                // Signed RAa.invokeSuspend re-enters o.for with null wrapper,
                // and the SAME RAa continuation. No vendor fields are read.
                scopedWrapper=remembered;
                mark(mainContinuationRecovered);
            } else if (wrapper!=remembered) {
                scopedWrapper=null;
                link.conflicted=true;
                link.wrapper=null;
                mark(mainContinuationConflict);
            }
        }
        pushScope(activeWrapperScopes,scopedWrapper);
        mark(nativeMainSourceEnters);
        // Direct exact argument and recovered coroutine identity are distinct.
        if (scopedWrapper!=null && scopedWrapper==wrapper
                && hasWrapperLink(scopedWrapper))
            mark(wrapperMainSourceRequests);
    }

    void exitNativeMainSourceRequest() {
        popScope(activeWrapperScopes);
    }

    /**
     * The signed cA9.extends selection call is the exact TrackWrapper-bearing
     * caller of the original Player source setter. Keep that same wrapper in
     * scope while the vendor builds its source descriptor; this is distinct
     * from claiming that download2.o.for was entered.
     */
    synchronized void enterNativePlayerSourceSelection(Object wrapper) {
        Object scopedWrapper=wrapper;
        if(scopedWrapper==null || !hasWrapperLink(scopedWrapper))
            scopedWrapper=null;
        pushScope(activeWrapperScopes,scopedWrapper);
    }

    void exitNativePlayerSourceSelection() {
        popScope(activeWrapperScopes);
    }

    private synchronized boolean hasWrapperLink(Object wrapper) {
        return findByWrapper(wrapper)!=null;
    }

    /**
     * Runs only AFTER the signed iLb constructor completed under cA9's
     * original TrackWrapper source-selection scope. This is a structural
     * candidate, not an approved source, a current MediaItem or a ticket.
     */
    synchronized void onOriginalMediaSourceConstructed(Object source,Object item) {
        onOriginalMediaSourceConstructed(source,item,null,null);
    }
    synchronized void onOriginalMediaSourceConstructed(Object source,Object item,
            Object owner,Object configuration) {
        Object wrapper=currentScope(activeWrapperScopes);
        if(source==null || item==null || wrapper==null
                || findByWrapper(wrapper)==null)return;
        for(int i=originalMediaSourceItems.size()-1;i>=0;i--) {
            OriginalMediaSourceItemLink old=originalMediaSourceItems.get(i);
            Object oldSource=old.source.get(),oldItem=old.item.get();
            if(oldSource==null || oldItem==null || old.wrapper.get()==null) {
                originalMediaSourceItems.remove(i);
                continue;
            }
            if(oldSource==source || oldItem==item) {
                old.conflicted=true;
                mark(originalMediaItemConflicts);
                return; // multiple originals may never share a selection
            }
        }
        if(originalMediaSourceItems.size()>=16)return; // fail closed, no live eviction
        originalMediaSourceItems.add(new OriginalMediaSourceItemLink(
            source,item,wrapper,owner,configuration));
        mark(originalMediaItemAnchors);
    }

    /**
     * Passive identity diagnostic only. The original strict MediaItem == gate
     * below is unchanged even for a unique owner/config match. This reveals
     * whether the constructor and coroutine child share an exact caller
     * context without using equals(), IDs, values or leaked source details.
     */
    synchronized void onOriginalChildContextComparison(
            Object owner,Object configuration,Object item) {
        if(owner==null || configuration==null || item==null) {
            mark(childCallerContextUnavailable);
            return;
        }
        int exact=0,ownerOnly=0,configOnly=0;
        boolean sameItem=false;
        for(OriginalMediaSourceItemLink link:originalMediaSourceItems) {
            // Dead source/wrapper anchors never become valid witnesses.
            if(link.source.get()==null || link.wrapper.get()==null
                    || link.item.get()==null)continue;
            Object anchoredOwner=link.owner.get();
            Object anchoredConfig=link.configuration.get();
            if(anchoredOwner==null || anchoredConfig==null)continue;
            if(anchoredOwner==owner && anchoredConfig==configuration) {
                exact++;
                if(link.item.get()==item)sameItem=true;
            } else if(anchoredOwner==owner) ownerOnly++;
            else if(anchoredConfig==configuration) configOnly++;
        }
        if(exact>1) mark(childCallerPairAmbiguous);
        else if(exact==1)
            mark(sameItem?childCallerPairSameItem:childCallerPairDifferentItem);
        else if(ownerOnly>0)mark(childCallerOwnerOnly);
        else if(configOnly>0)mark(childCallerConfigOnly);
        else mark(childCallerNoMatch);
    }

    /**
     * MediaItem == across original iLb constructor and later lLb.if.
     * Returns the *actual iLb source object* too: caller MUST require == with
     * the source that the successful original Player setter accepted.
     */
    synchronized Object[] exactOriginalMediaItemCreator(Object item) {
        if(item==null) {
            mark(childNullItem);
            return null;
        }
        OriginalMediaSourceItemLink unique=null;
        boolean liveItem=false,expiredItem=false;
        for(OriginalMediaSourceItemLink candidate:originalMediaSourceItems) {
            Object stored=candidate.item.get();
            if(stored==null)expiredItem=true;
            else liveItem=true;
            if(stored!=item)continue; // no equals(), IDs or last-seen fallback
            if(unique!=null) {
                mark(childDuplicateItemAnchor);
                return null;
            }
            unique=candidate;
        }
        if(unique==null) {
            // Context only: a collected item cannot be attributed to this child.
            mark(liveItem?childLiveDifferentItem:
                expiredItem?childOnlyExpiredItems:childNoAnchors);
            return null;
        }
        return originalCreatorFromAnchor(unique);
    }

    private Object[] originalCreatorFromAnchor(OriginalMediaSourceItemLink unique) {
        if(unique.conflicted) {
            mark(childConflictedItemAnchor);
            return null;
        }
        Object wrapper=unique.wrapper.get(),source=unique.source.get();
        if(wrapper==null) {
            mark(childWeakWrapperLost);
            return null;
        }
        if(source==null) {
            mark(childWeakSourceLost);
            return null;
        }
        if(findByWrapper(wrapper)==null) {
            int live=0;
            for(NativeTrackSourceLink link:nativeTrackSourceLinks) {
                if(link.wrapper!=null && link.wrapper.get()==wrapper
                        && link.track!=null && link.track.get()!=null)
                    live++;
            }
            mark(live>1?childWrapperLinkAmbiguous:childWrapperLinkMissing);
            return null;
        }
        Object[] creator=exactCreatorTrackAlbumBeforeSourceSet(wrapper);
        if(creator==null) {
            // The beta path still requires its own exact issuer/Track/Flow proof.
            mark(childOriginalCreatorRejected);
            creator=exactBetaCreatorWithoutAlbum(wrapper);
            if(creator==null) {
                mark(childBetaCreatorRejected);
                return null;
            }
        }
        return new Object[]{wrapper,creator[0],creator[1],source};
    }

    // Actual constructor argument must be the identical final source field.
    synchronized void onOriginalChildCoroutineConstructed(Object coroutine,
            Object argument,Object captured) {
        if(coroutine==null)return;
        for(int i=originalChildCaptures.size()-1;i>=0;i--) {
            OriginalChildCoroutineCapture prior=originalChildCaptures.get(i);
            Object instance=prior.coroutine.get();
            if(instance==null) {originalChildCaptures.remove(i);continue;}
            if(instance==coroutine) {prior.conflict=true;return;}
        }
        if(originalChildCaptures.size()>=32)return;
        boolean valid=argument!=null && argument==captured;
        OriginalChildCoroutineCapture witness=
            new OriginalChildCoroutineCapture(coroutine,valid?argument:null);
        witness.conflict=!valid;
        originalChildCaptures.add(witness);
    }

    synchronized void enterOriginalChildCoroutineResume(Object coroutine,Object captured) {
        OriginalChildCoroutineCapture witness=null;
        if(coroutine!=null && captured!=null) {
            for(OriginalChildCoroutineCapture prior:originalChildCaptures) {
                if(prior.coroutine.get()!=coroutine)continue;
                if(!prior.conflict && prior.source.get()==captured)witness=prior;
                break;
            }
        }
        ArrayList<OriginalChildCoroutineCapture> stack=activeOriginalChildSourceScopes.get();
        if(stack==null) {
            stack=new ArrayList<>();
            activeOriginalChildSourceScopes.set(stack);
        }
        stack.add(witness); // a null inner frame masks the outer frame
        mark(witness!=null?childCoroutineScopeMatch:childCoroutineScopeReject);
    }

    void exitOriginalChildCoroutineResume() {
        ArrayList<OriginalChildCoroutineCapture> stack=activeOriginalChildSourceScopes.get();
        if(stack==null)return;
        if(!stack.isEmpty())stack.remove(stack.size()-1);
        if(stack.isEmpty())activeOriginalChildSourceScopes.remove();
    }

    synchronized Object[] exactOriginalChildCoroutineCreator(Object item) {
        ArrayList<OriginalChildCoroutineCapture> stack=activeOriginalChildSourceScopes.get();
        if(stack==null || stack.isEmpty() || item==null)return null;
        OriginalChildCoroutineCapture witness=stack.get(stack.size()-1);
        if(witness==null || witness.conflict || witness.coroutine.get()==null)return null;
        Object source=witness.source.get();
        if(source==null)return null;
        OriginalMediaSourceItemLink unique=null;
        for(OriginalMediaSourceItemLink anchor:originalMediaSourceItems) {
            Object anchoredSource=anchor.source.get(),anchoredItem=anchor.item.get();
            if(anchoredItem==item && anchoredSource!=source)return null;
            if(anchoredSource!=source)continue;
            if(unique!=null || anchoredItem==null)return null;
            unique=anchor;
        }
        return unique==null?null:originalCreatorFromAnchor(unique);
    }

    synchronized boolean onOriginalChildCoroutineDescriptor(Object item,
            Object wrapper,Object descriptor) {
        Object[] creator=exactOriginalChildCoroutineCreator(item);
        if(creator==null || creator[0]!=wrapper || descriptor==null)return false;
        if(!bindOriginalDescriptor(wrapper,descriptor))return false;
        mark(childCoroutineDescriptorLinks);
        return true;
    }

    /** Validated immutable child coroutine iLb source identity only. */
    synchronized Object exactOriginalChildCoroutineSource() {
        ArrayList<OriginalChildCoroutineCapture> scopes=activeOriginalChildSourceScopes.get();
        if(scopes==null || scopes.isEmpty())return null;
        OriginalChildCoroutineCapture frame=scopes.get(scopes.size()-1);
        return frame==null || frame.conflict || frame.coroutine.get()==null
            ?null:frame.source.get();
    }

    /**
     * The signed child receives an Of6 produced by another original method,
     * not the parent iLb constructor Of6. Only the exact immutable iLb
     * source + successful original Player setter + constructor owner/config
     * + creator-owned Track/Album-or-beta references can bridge it.
     * Never choose by title, latest playing item or inferred track ID.
     */
    synchronized boolean onOriginalChildSelectedSetterDescriptor(
            Object owner,Object configuration,Object item,Object source,
            Object wrapper,Object track,Object albumOrBeta,Object descriptor) {
        if(owner==null || configuration==null || item==null || source==null ||
                source!=exactOriginalChildCoroutineSource() ||
                wrapper==null || track==null || albumOrBeta==null ||
                descriptor==null)return false;
        OriginalMediaSourceItemLink unique=null;
        for(OriginalMediaSourceItemLink candidate:originalMediaSourceItems) {
            if(candidate.source.get()!=source)continue;
            if(unique!=null)return false;
            unique=candidate;
        }
        if(unique==null || unique.conflicted || unique.wrapper.get()!=wrapper ||
                unique.owner.get()!=owner ||
                unique.configuration.get()!=configuration ||
                unique.item.get()==null)return false;
        NativeTrackSourceLink link=findByWrapper(wrapper);
        if(link==null || link.track==null || link.track.get()!=track)return false;
        Object[] creator=exactCreatorTrackAlbumOrBetaBeforeSourceSet(wrapper);
        if(creator==null || creator.length!=2 || creator[0]!=track ||
                creator[1]!=albumOrBeta)return false;
        if(!bindOriginalDescriptor(wrapper,descriptor))return false;
        mark(childCoroutineDescriptorLinks);
        return true;
    }

    synchronized void onOriginalChildHookRegistered() {
        mark(originalChildHookRegistered);
    }
    synchronized void onOriginalChildEntered() {
        mark(originalChildEntered);
    }
    synchronized void onOriginalChildCreatorMatch(boolean matched) {
        mark(matched?originalChildCreatorMatched:originalChildCreatorMissing);
    }
    synchronized void onOriginalChildSetterMatch(boolean matched) {
        mark(matched?originalChildSetterMatched:originalChildSetterMissing);
    }
    synchronized void onOriginalChildSetterSourceDifferent() {
        mark(originalChildSetterSourceDifferent);
    }

    /** Only the exact original iLb MediaItem matched by == may bind QAa. */
    synchronized boolean onOriginalMediaItemDescriptor(Object item,
            Object wrapper,Object descriptor) {
        Object[] creator=exactOriginalMediaItemCreator(item);
        if(creator==null || creator[0]!=wrapper || descriptor==null)return false;
        return bindOriginalDescriptor(wrapper,descriptor);
    }

    private boolean bindOriginalDescriptor(Object wrapper,Object descriptor) {
        NativeTrackSourceLink link=findByWrapper(wrapper);
        if(link==null || link.factoryResult!=null || link.sourceInstance!=null
                || link.descriptor!=null && link.descriptor.get()!=descriptor)
            return false;
        if(link.descriptor==null) {
            link.descriptor=new WeakReference<>(descriptor);
            mark(wrapperDescriptorLinks);
            if(link.albumInstance!=null && link.albumInstance.get()!=null)
                mark(trackDescriptorAlbumLinks);
        }
        mark(originalMediaItemDescriptors);
        return true;
    }

    synchronized void onNativeExoDescriptorBuiltForCurrentWrapper(Object descriptor) {
        Object wrapper=currentScope(activeWrapperScopes);
        if (wrapper==null || descriptor==null) return;
        NativeTrackSourceLink link=findByWrapper(wrapper);
        if (link!=null) {
            link.descriptor=new WeakReference<>(descriptor);
            link.firstOpenDescriptorPin=null;
            link.factoryResult=null;
            link.sourceInstance=null;
            link.pendingFirstOpenSource=null;
            link.factorySourceIdentityBound=false;
            link.firstOpenSourceCommitted=false;
            link.sourceOpened=false;
            link.sourceReadAfterOpen=false;
            link.sourceAlbumReadAfterOpen=false;
            if (link.albumInstance!=null && link.albumInstance.get()!=null)
                mark(trackDescriptorAlbumLinks);
            mark(wrapperDescriptorLinks);
        }
    }


    /**
     * The already observed original creator Track + Album -> wrapper ->
     * descriptor -> factory -> un-opened Exo DataSource instance.
     * This only nominates a possible future byte source in the SAME
     * original wrapper lineage; it is NOT selected decoder/PCM or an
     * alternate entitlement. If the instance is opened/read, ambiguous,
     * absent or rebound, never reuse it for a pre-prepare candidate.
     */
    synchronized Object exactFreshSourceInstanceForCreator(
            Object wrapper,Object expectedTrack,Object expectedAlbum) {
        if(expectedTrack==null || expectedAlbum==null)return null;
        Object[] creator=exactCreatorTrackAlbumBeforeSourceSet(wrapper);
        if(creator==null || creator[0]!=expectedTrack || creator[1]!=expectedAlbum)
            return null;
        NativeTrackSourceLink link=findByWrapper(wrapper);
        if(link==null || link.track==null || link.track.get()!=expectedTrack
                || link.albumInstance==null || link.albumInstance.get()!=expectedAlbum
                || link.descriptor==null || link.factoryResult==null
                || link.sourceInstance==null || link.sourceOpened
                || link.sourceEverTouched || link.sourceReadAfterOpen)return null;
        Object descriptor=link.descriptor.get(),factory=link.factoryResult.get();
        Object dataSource=link.sourceInstance.get();
        if(dataSource==null || wasSourceTouched(dataSource)
                || findBySource(dataSource)!=link)return null;
        return descriptor!=null && factory!=null ? dataSource : null;
    }

    /**
     * The SAME original Track/Album/tCa -> descriptor -> factory -> FRESH
     * DataSource identity that the original publisher just constructed.
     * Never claim current playback, audio rights or edition from this alone.
     */
    synchronized Object[] exactFreshCreatorForDataSource(Object dataSource) {
        if(dataSource==null || touchedHistorySaturated
                || wasSourceTouched(dataSource))return null;
        NativeTrackSourceLink link=findBySource(dataSource);
        if(link==null || link.sourceInstance==null
                || link.sourceInstance.get()!=dataSource
                || link.sourceOpened || link.sourceEverTouched
                || link.sourceReadAfterOpen || link.descriptor==null
                || link.descriptor.get()==null || link.factoryResult==null
                || link.factoryResult.get()==null || link.wrapper==null
                || link.track==null || link.albumInstance==null)return null;
        Object wrapper=link.wrapper.get(),track=link.track.get();
        Object album=link.albumInstance.get();
        if(wrapper==null || track==null || album==null)return null;
        Object[] original=exactCreatorTrackAlbumBeforeSourceSet(wrapper);
        return original!=null && original.length==2
            && original[0]==track && original[1]==album
            ?new Object[]{wrapper,track,album}:null;
    }

    /**
     * Fresh native Exo source for exact same issuer Track/tCa when original
     * Album was absent. Requires the full original descriptor/factory/source
     * object chain; no guessed global newest source or prefetch object.
     */
    synchronized Object exactFreshSourceInstanceForCreatorOrBeta(
            Object wrapper,Object track,Object albumOrBetaToken) {
        if(albumOrBetaToken!=wrapper)
            return exactFreshSourceInstanceForCreator(wrapper,track,albumOrBetaToken);
        Object[] creator=exactBetaCreatorWithoutAlbum(wrapper);
        if(creator==null || creator[0]!=track)return null;
        NativeTrackSourceLink link=findByWrapper(wrapper);
        if(link==null || link.track==null || link.track.get()!=track
                || link.descriptor==null || link.factoryResult==null
                || link.sourceInstance==null || link.sourceOpened
                || link.sourceEverTouched || link.sourceReadAfterOpen)
            return null;
        Object instance=link.sourceInstance.get();
        if(instance==null || wasSourceTouched(instance)
                || findBySource(instance)!=link
                || link.descriptor.get()==null || link.factoryResult.get()==null)
            return null;
        return instance;
    }

    /**
     * Read-only live-period lookup: resolve the exact DataSource already linked
     * to this original Track wrapper, even after open/read. Unlike the
     * exactFresh* admission helpers, this never nominates or arms a source.
     * Full creator Track+Album and the owner-consented track-only BETA token
     * remain separate, exact identity paths.
     */
    synchronized Object linkedSourceInstanceForCreatorOrBeta(Object wrapper) {
        mark(liveLinkedSourceLookups);
        NativeTrackSourceLink link=findByWrapper(wrapper);
        if(link==null) {
            mark(liveLinkedSourceWrapperLinkMissing);
            return null;
        }
        if(link.wrapper==null || link.wrapper.get()!=wrapper
                || link.track==null || link.track.get()==null) {
            mark(liveLinkedSourceLinkMismatch);
            return null;
        }
        // NAV56: a successful first-open arm already validated the exact
        // creator Track/Album-or-BETA token, player setter, descriptor,
        // factory and this DataSource identity. Keep that admission proof on
        // this exact wrapper/source link. Do not re-run the bounded creator,
        // TrackAlbum or Flow registries on every renderer read: they can be
        // evicted after admission even while this committed source is alive.
        boolean committed=link.firstOpenSourceCommitted;
        Object[] creator=null;
        if(committed) {
            mark(liveLinkedSourceCreatorMatched);
        } else {
            creator=exactCreatorTrackAlbumOrBetaBeforeSourceSet(wrapper);
            if(creator==null || creator.length!=2
                    || creator[0]==null || creator[1]==null) {
                mark(liveLinkedSourceCreatorMissing);
                return null;
            }
            if(link.track.get()!=creator[0]) {
                mark(liveLinkedSourceLinkMismatch);
                return null;
            }
            mark(liveLinkedSourceCreatorMatched);
        }
        // Do not require the vendor descriptor/factory weak references to stay
        // alive after OPEN. Their exact identity chain was already verified
        // when this very sourceInstance was attached to the link.
        if(!link.factorySourceIdentityBound) {
            mark(liveLinkedSourceFactorySourceUnbound);
            return null;
        }
        if(link.sourceInstance==null) {
            mark(liveLinkedSourceInstanceNotLinked);
            return null;
        }
        Object instance=link.sourceInstance.get();
        if(instance==null) {
            mark(liveLinkedSourceInstanceWeakLost);
            return null;
        }
        if(findBySource(instance)!=link) {
            mark(liveLinkedSourceReverseLinkMismatch);
            return null;
        }
        // Before commit, retain the original strict creator recheck. After
        // commit, firstOpenSourceCommitted is the durable result of that same
        // check and is scoped to this exact DataSource on this exact link.
        if(!committed && creator[1]==wrapper) {
            Object[] beta=exactBetaCreatorWithoutAlbum(wrapper);
            if(beta==null || beta.length!=2
                    || beta[0]!=creator[0] || beta[1]!=wrapper) {
                mark(liveLinkedSourceBetaRecheckFailed);
                return null;
            }
        } else if(!committed && (link.albumInstance==null
                || link.albumInstance.get()!=creator[1])) {
            mark(liveLinkedSourceAlbumMismatch);
            return null;
        }
        mark(liveLinkedSourceResolved);
        return instance;
    }

    synchronized Object[] exactFreshCreatorOrBetaForDataSource(Object dataSource) {
        Object[] original=exactFreshCreatorForDataSource(dataSource);
        if(original!=null)return original;
        if(dataSource==null || touchedHistorySaturated
                || wasSourceTouched(dataSource))return null;
        NativeTrackSourceLink link=findBySource(dataSource);
        if(link==null || link.sourceInstance==null
                || link.sourceInstance.get()!=dataSource
                || link.sourceOpened || link.sourceEverTouched
                || link.sourceReadAfterOpen || link.descriptor==null
                || link.descriptor.get()==null || link.factoryResult==null
                || link.factoryResult.get()==null || link.wrapper==null
                || link.track==null)return null;
        Object wrapper=link.wrapper.get(),track=link.track.get();
        Object[] token=exactBetaCreatorWithoutAlbum(wrapper);
        return token!=null && token[0]==track
            ?new Object[]{wrapper,track,token[1]}:null;
    }

    private NativeTrackSourceLink findByWrapper(Object wrapper) {
        if (wrapper==null) return null;
        NativeTrackSourceLink match=null;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink link=nativeTrackSourceLinks.get(i);
            if (link.track==null || link.track.get()==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if (link.wrapper!=null && link.wrapper.get()==wrapper) {
                // Multiple active tracks sharing one object is ambiguous.
                if (match!=null) return null;
                match=link;
            }
        }
        return match!=null?match:restoreWrapperLinkFromCreatorBirth(wrapper);
    }

    private NativeTrackSourceLink findByDescriptor(Object descriptor) {
        if (descriptor==null) return null;
        NativeTrackSourceLink match=null;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink link=nativeTrackSourceLinks.get(i);
            if (link.track==null || link.track.get()==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if (link.descriptor!=null && link.descriptor.get()==descriptor) {
                // Multiple active tracks sharing one object is ambiguous.
                if (match!=null) return null;
                match=link;
            }
        }
        return match;
    }

    private NativeTrackSourceLink findByFactory(Object factory) {
        if (factory==null) return null;
        NativeTrackSourceLink match=null;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink link=nativeTrackSourceLinks.get(i);
            if (link.track==null || link.track.get()==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if (link.factoryResult!=null && link.factoryResult.get()==factory) {
                // Multiple active tracks sharing one object is ambiguous.
                if (match!=null) return null;
                match=link;
            }
        }
        return match;
    }

    private NativeTrackSourceLink findBySource(Object source) {
        if (source==null) return null;
        NativeTrackSourceLink match=null;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink link=nativeTrackSourceLinks.get(i);
            if (link.track==null || link.track.get()==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if (link.sourceInstance!=null && link.sourceInstance.get()==source) {
                // Multiple active tracks sharing one object is ambiguous.
                if (match!=null) return null;
                match=link;
            }
        }
        return match;
    }

    private boolean hasLiveFirstOpenSource(NativeTrackSourceLink link) {
        if(link==null)return false;
        if(link.firstOpenSourceCommitted) {
            if(link.sourceInstance!=null && link.sourceInstance.get()!=null)
                return true;
            link.firstOpenSourceCommitted=false;
        }
        if(link.pendingFirstOpenSource!=null) {
            if(link.pendingFirstOpenSource.get()!=null)return true;
            link.pendingFirstOpenSource=null;
        }
        return false;
    }

    synchronized void onExoDescriptorBuilt(Object source) {
        if (source == null) return;
        // Identity comparisons never invoke vendor equals, hashCode or toString.
        for (int i=nativeDescriptors.size()-1; i>=0; i--) {
            Object prior=nativeDescriptors.get(i).get();
            if (prior==source) return;
            if (prior==null) nativeDescriptors.remove(i);
        }
        if (nativeDescriptors.size()>=16) nativeDescriptors.remove(0);
        nativeDescriptors.add(new WeakReference<>(source));
        mark(exoDescriptorResults);
    }

    synchronized void onExoFactoryCreated(Object descriptor) {
        onExoFactoryCreated(descriptor,null);
    }

    synchronized void onExoFactoryCreated(Object descriptor,Object factoryResult) {
        mark(exoFactoryResults);
        if (descriptor == null) return;
        for (WeakReference<Object> ref:nativeDescriptors) {
            if (ref.get()==descriptor) {
                mark(exoFactorySameDescriptor);
                break;
            }
        }
        NativeTrackSourceLink link=findByDescriptor(descriptor);
        if (link!=null && factoryResult!=null) {
            // findByDescriptor already verified exact Java identity. A strong
            // pin here prevents GC between this handoff and source first OPEN.
            // Once a first-open source is pending or committed, a later
            // factory callback on this descriptor is not a new selected lineage.
            if(hasLiveFirstOpenSource(link)) {
                link.firstOpenDescriptorPin=null;
            } else {
                link.firstOpenDescriptorPin=link.sourceEverTouched?null:descriptor;
                link.factoryResult=new WeakReference<>(factoryResult);
                link.sourceInstance=null;
                link.factorySourceIdentityBound=false;
                link.sourceOpened=false;
                link.sourceReadAfterOpen=false;
                link.sourceAlbumReadAfterOpen=false;
            }
            if (link.albumInstance!=null && link.albumInstance.get()!=null)
                mark(trackFactoryAlbumLinks);
            mark(trackDescriptorFactoryLinks);
        }
    }

    private static boolean firstAtMost(AtomicLong count, int limit) {
        for (;;) {
            long old = count.get();
            if (old >= limit) return false;
            if (count.compareAndSet(old, old+1)) return true;
        }
    }

    synchronized void onExoSourceInstanceCreated(Object source) {
        if (source == null) return;
        for (int i=exoSourceInstances.size()-1;i>=0;i--) {
            Object item = exoSourceInstances.get(i).get();
            if (item == source) return;
            if (item == null) exoSourceInstances.remove(i);
        }
        if (exoSourceInstances.size()>=16) exoSourceInstances.remove(0);
        exoSourceInstances.add(new WeakReference<>(source));
        mark(exoSourceInstancesCreated);
    }

    synchronized void onExoSourceInstanceCreated(Object source,Object factoryObject) {
        onExoSourceInstanceCreated(source,factoryObject,null);
    }

    synchronized void onExoSourceInstanceCreated(Object source,Object factoryObject,
            Object nestedFactory) {
        onExoSourceInstanceCreated(source);
        NativeTrackSourceLink link=findByFactory(factoryObject);
        if (link!=null && source!=null) {
            ExactFactorySourceBirth existing=null;
            for(int i=exactFactorySourceBirths.size()-1;i>=0;i--) {
                ExactFactorySourceBirth birth=exactFactorySourceBirths.get(i);
                Object older=birth.source.get();
                if(older==null)exactFactorySourceBirths.remove(i);
                else if(older==source) {
                    boolean sameNestedFactory=birth.nestedFactory==null
                        ?nestedFactory==null
                        :birth.nestedFactory.get()==nestedFactory;
                    if(existing!=null || birth.link!=link
                            || birth.factory.get()!=factoryObject
                            || !sameNestedFactory) {
                        birth.conflicted=true;
                        exactFactoryBirthsSaturated=true; // never guess
                    } else existing=birth;
                }
            }
            if(existing==null && !exactFactoryBirthsSaturated) {
                if(exactFactorySourceBirths.size()>=64)
                    exactFactoryBirthsSaturated=true;
                else exactFactorySourceBirths.add(
                    new ExactFactorySourceBirth(source,factoryObject,link,
                        nestedFactory));
            }
            // Keep recording exact factory births for every sibling, but do
            // not let a later product replace the source committed at first
            // open. A descriptor rebind is the only reset boundary.
            if(!hasLiveFirstOpenSource(link)) {
                link.sourceInstance=new WeakReference<>(source);
                link.factorySourceIdentityBound=true;
                link.sourceOpened=false;
                link.sourceEverTouched=wasSourceTouched(source);
                if(link.sourceEverTouched || exactFactoryBirthsSaturated)
                    link.firstOpenDescriptorPin=null;
                link.sourceReadAfterOpen=false;
                link.sourceAlbumReadAfterOpen=false;
            }
            trackSourceReadInspectionBudget.set(0);
            hasTrackSourceLink=true;
            if (link.albumInstance!=null && link.albumInstance.get()!=null)
                mark(trackSourceAlbumLinks);
            mark(trackFactorySourceLinks);
        }
    }

    private boolean hasExactFactorySourceBirth(Object source,Object factoryObject,
            Object nestedFactory) {
        NativeTrackSourceLink link=findByFactory(factoryObject);
        if(link==null)return false;
        for(ExactFactorySourceBirth birth:exactFactorySourceBirths) {
            if(birth.source.get()==source && birth.factory.get()==factoryObject
                    && birth.nestedFactory!=null
                    && birth.nestedFactory.get()==nestedFactory
                    && birth.link==link && !birth.conflicted)return true;
        }
        return false;
    }


    /**
     * The signed c.for result is an outer wrapper. The pinned nested
     * $b.for source factory must be Java-identity reachable by one unique
     * bounded path from that exact descriptor's outer factory result.
     * Do not pass an unbound DataSource to the playback admission gate.
     */
    synchronized Object exactOuterFactoryForNested(Object nestedFactory,
            java.util.function.BiPredicate<Object,Object> uniquePath,
            java.util.function.BiPredicate<Object,Object> anyPath) {
        if(nestedFactory==null || uniquePath==null || anyPath==null)return null;
        Object result=null;
        for(NativeTrackSourceLink link:nativeTrackSourceLinks) {
            if(link.track==null || link.track.get()==null ||
                    link.wrapper==null || link.wrapper.get()==null ||
                    link.descriptor==null || link.descriptor.get()==null ||
                    link.factoryResult==null)continue;
            Object outer=link.factoryResult.get();
            if(outer==null)continue;
            boolean referenced,unique;
            try {
                referenced=anyPath.test(outer,nestedFactory);
                if(!referenced)continue;
                unique=uniquePath.test(outer,nestedFactory);
            } catch(Throwable ignored) {return null;}
            if(!unique)return null; // a possibly related but ambiguous outer blocks admission
            if(result!=null)return null;
            result=outer;
        }
        return result;
    }

    synchronized ExactNestedFactorySourceScope beginExactNestedFactorySourceScope() {
        ExactNestedFactorySourceScope scope=new ExactNestedFactorySourceScope(
            activeExactNestedFactorySourceScope.get());
        activeExactNestedFactorySourceScope.set(scope);
        return scope;
    }

    /**
     * The pinned nested $b.for hook can run while the outer signed c.for
     * method is still inside chain.proceed(). In that call order the exact
     * descriptor -> outer-factory link does not exist yet. Keep only the
     * exact source + nested-factory identities in that invocation's bounded
     * scope; do not nominate or arm anything until the outer hook returns.
     */
    synchronized boolean onExoNestedSourceInstanceCreated(Object source,
            Object nestedFactory,
            java.util.function.BiPredicate<Object,Object> uniquePath,
            java.util.function.BiPredicate<Object,Object> anyPath) {
        onExoSourceInstanceCreated(source);
        if(source==null || nestedFactory==null || uniquePath==null
                || anyPath==null)return false;
        ExactNestedFactorySourceScope scope=
            activeExactNestedFactorySourceScope.get();
        if(scope!=null) {
            for(int i=scope.births.size()-1;i>=0;i--) {
                PendingNestedFactorySourceBirth prior=scope.births.get(i);
                Object priorSource=prior.source.get();
                if(priorSource==null) {
                    scope.births.remove(i);
                    continue;
                }
                if(priorSource==source) {
                    if(prior.nestedFactory.get()!=nestedFactory) {
                        scope.saturated=true;
                        exactFactoryBirthsSaturated=true;
                    }
                    return false;
                }
            }
            if(scope.births.size()>=64) {
                scope.saturated=true;
                exactFactoryBirthsSaturated=true;
                return false;
            }
            scope.births.add(
                new PendingNestedFactorySourceBirth(source,nestedFactory));
            return false; // exact outer binding is deliberately deferred
        }
        Object outer=exactOuterFactoryForNested(nestedFactory,uniquePath,anyPath);
        if(outer==null || findByFactory(outer)==null)return false;
        onExoSourceInstanceCreated(source,outer,nestedFactory);
        return hasExactFactorySourceBirth(source,outer,nestedFactory);
    }

    /**
     * Complete the same c.for invocation after its exact descriptor/factory
     * link has been recorded. The nested factory must still be reachable by
     * one unique bounded Java-identity path from this exact outer object.
     * A later outer factory that shares the nested object invalidates the
     * earlier nested birth instead of allowing ambiguous lineage selection.
     */
    synchronized int finishExactNestedFactorySourceScope(
            ExactNestedFactorySourceScope scope,Object outerFactory,
            java.util.function.BiPredicate<Object,Object> uniquePath,
            java.util.function.BiPredicate<Object,Object> anyPath) {
        if(scope==null)return 0;
        if(activeExactNestedFactorySourceScope.get()!=scope) {
            exactFactoryBirthsSaturated=true;
            activeExactNestedFactorySourceScope.remove();
            return 0;
        }
        if(scope.previous==null)activeExactNestedFactorySourceScope.remove();
        else activeExactNestedFactorySourceScope.set(scope.previous);
        if(outerFactory==null || uniquePath==null
                || anyPath==null || findByFactory(outerFactory)==null)return 0;
        if(scope.saturated) {
            exactFactoryBirthsSaturated=true;
            invalidateNestedFactoryBirthsSharedWithOuter(outerFactory,anyPath);
            return 0;
        }
        int linked=0;
        for(PendingNestedFactorySourceBirth pending:scope.births) {
            Object source=pending.source.get();
            Object nestedFactory=pending.nestedFactory.get();
            if(source==null || nestedFactory==null)continue;
            if(exactOuterFactoryForNested(nestedFactory,uniquePath,anyPath)!=outerFactory)
                continue;
            onExoSourceInstanceCreated(source,outerFactory,nestedFactory);
            if(hasExactFactorySourceBirth(source,outerFactory,nestedFactory))linked++;
        }
        invalidateNestedFactoryBirthsSharedWithOuter(outerFactory,anyPath);
        return linked;
    }

    private void invalidateNestedFactoryBirthsSharedWithOuter(Object outerFactory,
            java.util.function.BiPredicate<Object,Object> anyPath) {
        for(ExactFactorySourceBirth birth:exactFactorySourceBirths) {
            if(birth.nestedFactory==null)continue;
            Object nestedFactory=birth.nestedFactory.get();
            Object priorOuter=birth.factory.get();
            if(nestedFactory==null || priorOuter==null) {
                birth.conflicted=true;
                continue;
            }
            if(priorOuter==outerFactory)continue;
            boolean shared;
            try {shared=anyPath.test(outerFactory,nestedFactory);}
            catch(Throwable ignored) {shared=true;}
            if(shared)birth.conflicted=true;
        }
    }

    /**
     * Called BEFORE the first actual native Exo open(), not at factory
     * construction. The first created object can be an unopened prefetch;
     * later factory products may be the instance that actually loads audio.
     *
     * Only the exact original wrapper/descriptor/factory identity and the
     * original creator's Track/Album-or-allowlisted-beta token are accepted.
     * A sibling already touched by ANY vendor open/read/close means the
     * family cannot be switched without mixing bytes: fail closed.
     */
    synchronized void onExoFirstOpenHookEnter() {
        mark(firstOpenHookEntered);
    }
    synchronized void onExoFirstOpenSetterResult(boolean matched) {
        mark(matched?firstOpenSetterMatch:firstOpenSetterMissing);
    }
    synchronized void onExoFirstOpenDeferredArmCalled() {
        mark(firstOpenDeferredArmCalled);
    }
    synchronized void onExoFirstOpenDeferredArmResult(boolean armed,Object source) {
        NativeTrackSourceLink link=findBySource(source);
        if(link!=null && link.pendingFirstOpenSource!=null
                && link.pendingFirstOpenSource.get()==source) {
            link.pendingFirstOpenSource=null;
            if(armed)link.firstOpenSourceCommitted=true;
        }
        mark(armed?firstOpenDeferredArmAccepted:firstOpenDeferredArmRejected);
    }
    synchronized void onExoFirstOpenArmException() {
        mark(firstOpenArmExceptions);
    }
    private Object[] rejectFirstOpenCandidate(AtomicLong reason) {
        mark(firstOpenCandidateRejected);
        mark(reason);
        return null;
    }
    private int liveWrapperLinkCount(Object wrapper) {
        int count=0;
        for(NativeTrackSourceLink link:nativeTrackSourceLinks) {
            Object candidateWrapper=link.wrapper==null?null:link.wrapper.get();
            Object candidateTrack=link.track==null?null:link.track.get();
            if(candidateWrapper==wrapper && candidateTrack!=null)count++;
        }
        return count;
    }
    private int liveFactoryLinkCount(Object factory) {
        int count=0;
        for(NativeTrackSourceLink link:nativeTrackSourceLinks) {
            Object candidateFactory=link.factoryResult==null
                ?null:link.factoryResult.get();
            Object candidateTrack=link.track==null?null:link.track.get();
            if(candidateFactory==factory && candidateTrack!=null)count++;
        }
        return count;
    }

    /**
     * Called BEFORE the first actual native Exo open(), not at factory
     * construction. The first created object can be an unopened prefetch;
     * later factory products may be the instance that actually loads audio.
     *
     * This preserves every existing fail-closed condition while naming the
     * first rejection, so a missing arm is no longer an unexplained zero.
     */
    synchronized Object[] exactFreshCreatorOrBetaAtFirstOpen(Object source) {
        if(source==null)
            return rejectFirstOpenCandidate(firstOpenSourceNull);
        if(exactFactoryBirthsSaturated)
            return rejectFirstOpenCandidate(firstOpenFactoryBirthsSaturated);
        if(touchedHistorySaturated)
            return rejectFirstOpenCandidate(firstOpenTouchedHistorySaturated);
        if(wasSourceTouched(source))
            return rejectFirstOpenCandidate(firstOpenSourceAlreadyTouched);
        ExactFactorySourceBirth found=null;
        for(int i=exactFactorySourceBirths.size()-1;i>=0;i--) {
            ExactFactorySourceBirth birth=exactFactorySourceBirths.get(i);
            Object candidate=birth.source.get();
            if(candidate==null) {
                exactFactorySourceBirths.remove(i);
                continue;
            }
            if(candidate==source) {
                if(found!=null)
                    return rejectFirstOpenCandidate(firstOpenBirthAmbiguous);
                found=birth;
            }
        }
        if(found==null)
            return rejectFirstOpenCandidate(firstOpenBirthNotFound);
        if(found.conflicted)
            return rejectFirstOpenCandidate(firstOpenBirthConflicted);
        Object factory=found.factory.get();
        if(factory==null)
            return rejectFirstOpenCandidate(firstOpenFactoryWeakLost);
        NativeTrackSourceLink link=found.link;
        if(link==null)
            return rejectFirstOpenCandidate(firstOpenLinkMissing);
        if(link.factoryResult==null || link.factoryResult.get()!=factory)
            return rejectFirstOpenCandidate(firstOpenFactoryLinkMismatch);
        if(link.descriptor==null || link.descriptor.get()==null)
            return rejectFirstOpenCandidate(firstOpenDescriptorLost);
        Object track=link.track==null?null:link.track.get();
        if(track==null)
            return rejectFirstOpenCandidate(firstOpenTrackLost);
        Object wrapper=link.wrapper==null?null:link.wrapper.get();
        if(wrapper==null)
            return rejectFirstOpenCandidate(firstOpenWrapperLost);
        if(link.sourceOpened)
            return rejectFirstOpenCandidate(firstOpenAlreadyOpened);
        if(link.sourceReadAfterOpen)
            return rejectFirstOpenCandidate(firstOpenReadAfterOpen);
        if(link.sourceEverTouched)
            return rejectFirstOpenCandidate(firstOpenAlreadyTouched);
        // A previous original read/open from any member of this factory's
        // source family forbids a late alternate switch on a sibling.
        for(ExactFactorySourceBirth birth:exactFactorySourceBirths) {
            if(birth.link!=link)continue;
            Object sibling=birth.source.get();
            if(sibling!=null && sibling!=source && wasSourceTouched(sibling))
                return rejectFirstOpenCandidate(firstOpenSiblingTouched);
        }
        NativeTrackSourceLink wrapperLink=findByWrapper(wrapper);
        if(wrapperLink!=link) {
            int matches=liveWrapperLinkCount(wrapper);
            return rejectFirstOpenCandidate(matches>1
                ?firstOpenWrapperLinkAmbiguous
                :matches==1?firstOpenWrapperLinkRebound:firstOpenWrapperLinkMissing);
        }
        NativeTrackSourceLink factoryLink=findByFactory(factory);
        if(factoryLink!=link) {
            int matches=liveFactoryLinkCount(factory);
            return rejectFirstOpenCandidate(matches>1
                ?firstOpenFactoryLinkAmbiguous
                :matches==1?firstOpenFactoryLinkRebound:firstOpenFactoryLinkMissing);
        }
        Object[] creator=exactCreatorTrackAlbumBeforeSourceSet(wrapper);
        if(creator==null) {
            mark(firstOpenOriginalCreatorMissing);
            creator=exactBetaCreatorWithoutAlbum(wrapper);
            if(creator==null)
                return rejectFirstOpenCandidate(firstOpenBetaCreatorMissing);
        }
        if(creator.length!=2 || creator[1]==null)
            return rejectFirstOpenCandidate(firstOpenCreatorTokenMissing);
        if(creator[0]!=track)
            return rejectFirstOpenCandidate(firstOpenCreatorTrackMismatch);
        if(creator[1]!=wrapper && link.albumInstance!=null
                && link.albumInstance.get()!=creator[1])
            return rejectFirstOpenCandidate(firstOpenAlbumMismatch);
        if(hasLiveFirstOpenSource(link)) {
            Object selected=link.pendingFirstOpenSource!=null
                ?link.pendingFirstOpenSource.get()
                :(link.sourceInstance==null?null:link.sourceInstance.get());
            if(selected!=source)
                return rejectFirstOpenCandidate(firstOpenAlreadyOpened);
        }
        // The birth above proves that THIS source came from THIS exact
        // signed factory. Protect it while the deferred arm is in flight;
        // promote to committed only if the route arm succeeds.
        link.sourceInstance=new WeakReference<>(source);
        link.pendingFirstOpenSource=new WeakReference<>(source);
        link.factorySourceIdentityBound=true;
        link.sourceOpened=false;
        link.sourceEverTouched=false;
        link.sourceReadAfterOpen=false;
        link.sourceAlbumReadAfterOpen=false;
        mark(firstOpenCandidateAccepted);
        return new Object[]{wrapper,track,creator[1]};
    }
    private synchronized boolean sameExoSource(Object source) {
        if (source == null) return false;
        for (WeakReference<Object> item:exoSourceInstances)
            if (item.get()==source) return true;
        return false;
    }

    void onExoSourceInstanceOpenAttempt(Object source) {
        synchronized(this) {
            markSourceTouched(source);
            NativeTrackSourceLink link=findBySource(source);
            if (link!=null) {
                link.sourceOpened=false;
                link.sourceEverTouched=true;
                link.sourceAlbumReadAfterOpen=false;
                trackSourceReadInspectionBudget.set(0);
            }
            // An open attempt that throws must revoke earlier proof. A
            // successful attempt separately restores it after proceed().
        }
    }

    void onExoSourceInstanceOpenFailure(Object source) {
        // A failed open is not a fresh source; do not rewind after failure.
        synchronized(this) {
            markSourceTouched(source);
            NativeTrackSourceLink link=findBySource(source);
            if (link!=null) {
                link.sourceOpened=false;
                link.sourceEverTouched=true;
            }
        }
    }

    void onExoSourceInstanceClose(Object source) {
        // Fail closed before the unmodified vendor close(), even if it throws.
        synchronized(this) {
            markSourceTouched(source);
            NativeTrackSourceLink link=findBySource(source);
            if (link!=null) {
                link.sourceOpened=false;
                link.sourceEverTouched=true;
                mark(linkedSourceCloseCalls);
            }
        }
    }

    void onExoSourceInstanceOpen(Object source) {
        if (sameExoSource(source)) mark(exoSourceInstancesOpened);
        synchronized(this) {
            markSourceTouched(source);
            NativeTrackSourceLink link=findBySource(source);
            if (link!=null) {
                // Called after the original vendor open() returned normally.
                link.sourceOpened=true;
                link.sourceEverTouched=true;
                link.sourceAlbumReadAfterOpen=false;
                if (link.albumInstance!=null && link.albumInstance.get()!=null)
                    mark(trackSourceAlbumOpenLinks);
                mark(trackSourceOpenLinks);
            }
        }
    }

    private void markDistinctLinkedReadSource(Object source) {
        if (source==null) return;
        for (int i=distinctLinkedReadSources.size()-1;i>=0;i--) {
            Object prior=distinctLinkedReadSources.get(i).get();
            if (prior==source) return;
            if (prior==null) distinctLinkedReadSources.remove(i);
        }
        if (distinctLinkedReadSources.size()>=16)
            distinctLinkedReadSources.remove(0);
        distinctLinkedReadSources.add(new WeakReference<>(source));
        mark(trackSourceDistinctPositiveReads);
    }

    /** Invoked before publisher read(), not after its first bytes. */
    synchronized void onExoSourceInstanceReadAttempt(Object source) {
        NativeTrackSourceLink link=findBySource(source);
        if(link!=null && link.sourceEverTouched)return;
        markSourceTouched(source);
        if(link!=null)link.sourceEverTouched=true;
    }

    void onExoSourceInstanceRead(Object source,int count) {
        onExoSourceInstanceReadAttempt(source);
        // Privacy-safe, bounded first reads only. No buffers, offsets,
        // DataSpec, titles, URLs, content or vendor toString() are inspected.
        if (count > 0 && firstAtMost(exoSourceReadProbeBudget,16)
                && sameExoSource(source))
            mark(exoSourceInstancesRead);
        if (count > 0 && hasTrackSourceLink
                && (trackSourceReadProbeBudget.get()<16
                    || trackSourceUnopenedProbeBudget.get()<16)) {
            if (!firstAtMost(trackSourceReadInspectionBudget,256)) {
                firstAtMost(trackSourceInspectionExhausted,1);
                return; // bounded weak-link scan, not indefinite on read()
            }
            synchronized(this) {
                NativeTrackSourceLink link=findBySource(source);
                if (link==null) return;
                if (link.sourceOpened) {
                    if (firstAtMost(trackSourceReadProbeBudget,16)) {
                        mark(trackSourceReadLinks);
                        if (!link.sourceReadAfterOpen) {
                            link.sourceReadAfterOpen=true;
                            markDistinctLinkedReadSource(source);
                        }
                        if (!link.sourceAlbumReadAfterOpen
                                && link.albumInstance!=null
                                && link.albumInstance.get()!=null) {
                            link.sourceAlbumReadAfterOpen=true;
                            mark(trackSourceAlbumReadLinks);
                        }
                    }
                } else if (firstAtMost(trackSourceUnopenedProbeBudget,16)) {
                    // A positive read without our observed successful open
                    // is an UNVERIFIED source/lineage, not chain proof.
                    mark(trackSourceUnopenedReads);
                }
            }
        }
    }

    void onExoOpen() { mark(exoOpenResults); }
    void onExoReadResult(int result) {
        if (result > 0) mark(exoPositiveReads);
        else if (result == -1) mark(exoEndOfSource);
    }
    void onExoFailure() { mark(exoFailures); }

    void onFileInfoResult() { fileInfoResults.incrementAndGet(); }

    void onDirectDownloadInfoResult() { directDownloadInfoResults.incrementAndGet(); }

    void onReader(int candidate, boolean wasPassedToExtractor) {
        if (candidate == 0) reader0.incrementAndGet();
        else if (candidate == 1) reader1.incrementAndGet();
        if (wasPassedToExtractor) sameObjectReads.incrementAndGet();
    }

    void onExtractorSource(int candidate) {
        if (candidate == 0) extractor0.incrementAndGet();
        else if (candidate == 1) extractor1.incrementAndGet();
        else extractorOther.incrementAndGet();
    }

    void onReadReturn(int count) {
        if (count > 0) positiveReads.incrementAndGet();
        else if (count < 0 && count != Integer.MIN_VALUE)
            endOfSourceReads.incrementAndGet();
    }

    void onReadException() {
        failedReads.incrementAndGet();
    }

    private static String band(long count) {
        if (count <= 0) return "NONE";
        if (count == 1) return "ONE";
        if (count <= 8) return "FEW";
        return "MANY";
    }

    private static String event(String category, AtomicLong counter) {
        return "event=AUDIO_STAGE_B_SUMMARY;origin=" + category
            + ";error=" + band(counter.get()) + ";thread=OTHER";
    }

    String[] exportLines() {
        return new String[] {
            event("FILEINFO_DTO", fileInfoResults),
            event("DOWNLOADINFO_DTO", directDownloadInfoResults),
            event("READER_0", reader0),
            event("READER_1", reader1),
            event("EXTRACTOR_0", extractor0),
            event("EXTRACTOR_1", extractor1),
            event("EXTRACTOR_OTHER", extractorOther),
            event("SAME_SOURCE_OBJECT", sameObjectReads),
            event("POSITIVE_READS", positiveReads),
            event("SOURCE_END", endOfSourceReads),
            event("READ_EXCEPTIONS", failedReads),
            event("EXO_FACTORY_CREATED", exoFactoryResults),
            event("EXO_OPEN_OK", exoOpenResults),
            event("EXO_READ_POSITIVE", exoPositiveReads),
            event("EXO_SOURCE_END", exoEndOfSource),
            event("EXO_IO_FAILURE", exoFailures),
            event("EXO_DESCRIPTOR_BUILT", exoDescriptorResults),
            event("EXO_SAME_DESCRIPTOR", exoFactorySameDescriptor),
            event("EXO_SOURCE_INSTANCE", exoSourceInstancesCreated),
            event("EXO_INSTANCE_OPENED", exoSourceInstancesOpened),
            event("EXO_INSTANCE_READ", exoSourceInstancesRead),
            event("NATIVE_TRACK_FLOW_EMIT", nativeTrackFlowEmits),
            event("NATIVE_TRACK_SOURCE_REQUEST", nativeTrackSourceRequests),
            event("FLOW_TRACK_SAME_OBJECT", flowTrackSourceSameObject),
            event("TRACK_WRAPPER_LINK", nativeTrackWrapperLinks),
            event("TRACK_WRAPPER_LINK_RESTORED", nativeTrackWrapperLinksRestored),
            event("TRACK_WRAPPER_SAME_TRACK_PARALLEL",nativeTrackWrapperSameTrackParallel),
            event("TRACK_WRAPPER_SAME_IDENTITY_REFRESH",nativeTrackWrapperSameIdentityRefresh),
            event("TRACK_WRAPPER_IDENTITY_CONFLICT",nativeTrackWrapperIdentityConflict),
            event("TRACK_WRAPPER_LINK_RESTORED_WITH_SAME_TRACK_SIBLING",
                nativeTrackWrapperRestoredWithSameTrackSibling),
            event("WRAPPER_MAIN_SOURCE", wrapperMainSourceRequests),
            event("WRAPPER_DESCRIPTOR_LINK", wrapperDescriptorLinks),
            event("ORIGINAL_MEDIAITEM_SOURCE_ANCHOR", originalMediaItemAnchors),
            event("ORIGINAL_MEDIAITEM_DESCRIPTOR_LINK", originalMediaItemDescriptors),
            event("ORIGINAL_MEDIAITEM_IDENTITY_CONFLICT", originalMediaItemConflicts),
            event("ORIGINAL_CHILD_HOOK_REGISTERED", originalChildHookRegistered),
            event("ORIGINAL_CHILD_ENTER", originalChildEntered),
            event("ORIGINAL_CHILD_CREATOR_MATCH", originalChildCreatorMatched),
            event("ORIGINAL_CHILD_CREATOR_MISSING", originalChildCreatorMissing),
            event("ORIGINAL_CHILD_ITEM_NULL", childNullItem),
            event("ORIGINAL_CHILD_NO_ITEM_ANCHORS", childNoAnchors),
            event("ORIGINAL_CHILD_LIVE_OTHER_ITEM_ANCHOR", childLiveDifferentItem),
            event("ORIGINAL_CHILD_ONLY_EXPIRED_ITEM_ANCHORS", childOnlyExpiredItems),
            event("ORIGINAL_CHILD_ITEM_ANCHOR_DUPLICATE", childDuplicateItemAnchor),
            event("ORIGINAL_CHILD_ITEM_ANCHOR_CONFLICT", childConflictedItemAnchor),
            event("ORIGINAL_CHILD_WEAK_WRAPPER_LOST", childWeakWrapperLost),
            event("ORIGINAL_CHILD_WEAK_SOURCE_LOST", childWeakSourceLost),
            event("ORIGINAL_CHILD_WRAPPER_LINK_MISSING", childWrapperLinkMissing),
            event("ORIGINAL_CHILD_WRAPPER_LINK_AMBIGUOUS", childWrapperLinkAmbiguous),
            event("ORIGINAL_CHILD_ORIGINAL_TRACK_ALBUM_REJECT", childOriginalCreatorRejected),
            event("ORIGINAL_CHILD_BETA_CREATOR_REJECT", childBetaCreatorRejected),
            event("ORIGINAL_CHILD_CALLER_CONTEXT_UNAVAILABLE",
                childCallerContextUnavailable),
            event("ORIGINAL_CHILD_CALLER_PAIR_SAME_ITEM", childCallerPairSameItem),
            event("ORIGINAL_CHILD_CALLER_PAIR_DIFFERENT_ITEM",
                childCallerPairDifferentItem),
            event("ORIGINAL_CHILD_CALLER_PAIR_AMBIGUOUS",
                childCallerPairAmbiguous),
            event("ORIGINAL_CHILD_CALLER_OWNER_ONLY", childCallerOwnerOnly),
            event("ORIGINAL_CHILD_CALLER_CONFIG_ONLY", childCallerConfigOnly),
            event("ORIGINAL_CHILD_CALLER_NO_MATCH", childCallerNoMatch),
            event("ORIGINAL_CHILD_COROUTINE_SOURCE_SCOPE_MATCH", childCoroutineScopeMatch),
            event("ORIGINAL_CHILD_COROUTINE_SOURCE_SCOPE_REJECT", childCoroutineScopeReject),
            event("ORIGINAL_CHILD_COROUTINE_DESCRIPTOR_LINK", childCoroutineDescriptorLinks),
            event("ORIGINAL_CHILD_SETTER_MATCH", originalChildSetterMatched),
            event("ORIGINAL_CHILD_SETTER_MISSING", originalChildSetterMissing),
            event("ORIGINAL_CHILD_SETTER_SOURCE_DIFFERENT",
                originalChildSetterSourceDifferent),
            event("TRACK_DESCRIPTOR_FACTORY_LINK", trackDescriptorFactoryLinks),
            event("TRACK_FACTORY_SOURCE_LINK", trackFactorySourceLinks),
            event("TRACK_SOURCE_OPEN_LINK", trackSourceOpenLinks),
            event("TRACK_SOURCE_READ_LINK", trackSourceReadLinks),
            event("NATIVE_TRACK_WRAPPER_CONSTRUCTED", nativeTrackWrapperConstructed),
            event("TCA_CREATOR_OWNER_ENTER", tcaCreatorOwnerEnter),
            event("TCA_CREATOR_OWNER_NULL", tcaCreatorOwnerNull),
            event("TCA_CREATOR_TRACK_FIELD_READ", tcaCreatorTrackFieldRead),
            event("TCA_CREATOR_TRACK_FIELD_NULL", tcaCreatorTrackFieldNull),
            event("TCA_CREATOR_TRACK_FIELD_FAILED", tcaCreatorTrackFieldFailed),
            event("TCA_CREATOR_WRAPPER_CONSTRUCTED", tcaCreatorWrapperConstructed),
            event("TCA_CREATOR_WRAPPER_NO_TRACK", tcaCreatorWrapperNoTrack),
            event("TCA_CREATOR_WRAPPER_NOT_FLOW", tcaCreatorWrapperNotFlow),
            event("TCA_CREATOR_WRAPPER_FLOW_MATCH", tcaCreatorWrapperFlowMatch),
            event("TCA_CREATOR_WRAPPER_NO_ALBUM", tcaCreatorWrapperNoAlbum),
            event("TCA_CREATOR_WRAPPER_ALBUM_LINK", tcaCreatorWrapperAlbumLink),
            event("NATIVE_MAIN_SOURCE_ENTER", nativeMainSourceEnters),
            event("NATIVE_TRACK_CONTINUATION_CONSTRUCTED", nativeTrackContinuationConstructed),
            event("TRACK_CONTINUATION_RECOVERED", trackContinuationRecovered),
            event("TRACK_CONTINUATION_CONFLICT", trackContinuationConflict),
            event("NATIVE_MAIN_CONTINUATION_CONSTRUCTED", mainContinuationConstructed),
            event("MAIN_CONTINUATION_RECOVERED", mainContinuationRecovered),
            event("MAIN_CONTINUATION_CONFLICT", mainContinuationConflict),
            event("TRACK_SOURCE_UNOPENED_READ", trackSourceUnopenedReads),
            event("TRACK_SOURCE_DISTINCT_POSITIVE_READ", trackSourceDistinctPositiveReads),
            event("TRACK_SOURCE_CLOSE_LINK", linkedSourceCloseCalls),
            event("TRACK_SOURCE_READ_SCAN_EXHAUSTED", trackSourceInspectionExhausted),
            event("TRACK_ALBUM_CONSTRUCTOR_LINK", nativeTrackAlbumConstructorLinks),
            event("FLOW_TRACK_ALBUM_LINK", nativeTrackAlbumFlowLinks),
            event("TRACK_WRAPPER_ALBUM_LINK", trackWrapperAlbumLinks),
            event("TRACK_DESCRIPTOR_ALBUM_LINK", trackDescriptorAlbumLinks),
            event("TRACK_FACTORY_ALBUM_LINK", trackFactoryAlbumLinks),
            event("TRACK_SOURCE_ALBUM_LINK", trackSourceAlbumLinks),
            event("TRACK_SOURCE_ALBUM_OPEN_LINK", trackSourceAlbumOpenLinks),
            event("TRACK_SOURCE_ALBUM_READ_LINK", trackSourceAlbumReadLinks),
            event("TRACK_ALBUM_IDENTITY_CONFLICT", nativeTrackAlbumConflicts),
            event("TCA_CREATOR_NOT_FLOW_ALBUM_OBSERVED", creatorNotFlowAlbumObserved),
            event("TCA_CREATOR_NOT_FLOW_ALBUM_UNOBSERVED", creatorNotFlowAlbumUnobserved),
            event("TCA_CREATOR_FLOW_LATER_SAME_TRACK", creatorFlowLaterSameTrack),
            event("TCA_CREATOR_FLOW_LATER_ALBUM_OBSERVED", creatorFlowLaterAlbumObserved),
            // Strict triple-proof legacy status remains intentionally read-only;
            // separate BETA stage counters below make real audio proof explicit.
            "event=AUDIO_STAGE_B_STATUS;origin=CELIKOM_REPLACEMENT;error=NOT_CONNECTED;thread=OTHER",
            event("FIRST_OPEN_HOOK_ENTERED",firstOpenHookEntered),
            event("FIRST_OPEN_CANDIDATE_REJECTED",firstOpenCandidateRejected),
            event("FIRST_OPEN_SOURCE_NULL",firstOpenSourceNull),
            event("FIRST_OPEN_FACTORY_BIRTHS_SATURATED",firstOpenFactoryBirthsSaturated),
            event("FIRST_OPEN_TOUCHED_HISTORY_SATURATED",firstOpenTouchedHistorySaturated),
            event("FIRST_OPEN_SOURCE_ALREADY_TOUCHED",firstOpenSourceAlreadyTouched),
            event("FIRST_OPEN_BIRTH_NOT_FOUND",firstOpenBirthNotFound),
            event("FIRST_OPEN_BIRTH_AMBIGUOUS",firstOpenBirthAmbiguous),
            event("FIRST_OPEN_BIRTH_CONFLICTED",firstOpenBirthConflicted),
            event("FIRST_OPEN_FACTORY_WEAK_LOST",firstOpenFactoryWeakLost),
            event("FIRST_OPEN_LINK_MISSING",firstOpenLinkMissing),
            event("FIRST_OPEN_FACTORY_LINK_MISMATCH",firstOpenFactoryLinkMismatch),
            event("FIRST_OPEN_DESCRIPTOR_LOST",firstOpenDescriptorLost),
            event("FIRST_OPEN_TRACK_LOST",firstOpenTrackLost),
            event("FIRST_OPEN_WRAPPER_LOST",firstOpenWrapperLost),
            event("FIRST_OPEN_ALREADY_OPENED",firstOpenAlreadyOpened),
            event("FIRST_OPEN_ALREADY_TOUCHED",firstOpenAlreadyTouched),
            event("FIRST_OPEN_READ_AFTER_OPEN",firstOpenReadAfterOpen),
            event("FIRST_OPEN_SIBLING_TOUCHED",firstOpenSiblingTouched),
            event("FIRST_OPEN_WRAPPER_LINK_MISSING",firstOpenWrapperLinkMissing),
            event("FIRST_OPEN_WRAPPER_LINK_AMBIGUOUS",firstOpenWrapperLinkAmbiguous),
            event("FIRST_OPEN_WRAPPER_LINK_REBOUND",firstOpenWrapperLinkRebound),
            event("FIRST_OPEN_FACTORY_LINK_MISSING",firstOpenFactoryLinkMissing),
            event("FIRST_OPEN_FACTORY_LINK_AMBIGUOUS",firstOpenFactoryLinkAmbiguous),
            event("FIRST_OPEN_FACTORY_LINK_REBOUND",firstOpenFactoryLinkRebound),
            event("FIRST_OPEN_ORIGINAL_CREATOR_MISSING",firstOpenOriginalCreatorMissing),
            event("FIRST_OPEN_BETA_CREATOR_MISSING",firstOpenBetaCreatorMissing),
            event("FIRST_OPEN_CREATOR_TRACK_MISMATCH",firstOpenCreatorTrackMismatch),
            event("FIRST_OPEN_CREATOR_TOKEN_MISSING",firstOpenCreatorTokenMissing),
            event("FIRST_OPEN_ALBUM_MISMATCH",firstOpenAlbumMismatch),
            event("FIRST_OPEN_CANDIDATE_ACCEPTED",firstOpenCandidateAccepted),
            event("FIRST_OPEN_SETTER_MATCH",firstOpenSetterMatch),
            event("FIRST_OPEN_SETTER_MISSING",firstOpenSetterMissing),
            event("FIRST_OPEN_DEFERRED_ARM_CALLED",firstOpenDeferredArmCalled),
            event("FIRST_OPEN_DEFERRED_ARM_ACCEPTED",firstOpenDeferredArmAccepted),
            event("FIRST_OPEN_DEFERRED_ARM_REJECTED",firstOpenDeferredArmRejected),
            event("FIRST_OPEN_ARM_EXCEPTION",firstOpenArmExceptions),
            event("LIVE_PERIOD_SOURCE_LOOKUP_CALL",liveLinkedSourceLookups),
            event("LIVE_PERIOD_SOURCE_CREATOR_MATCH",liveLinkedSourceCreatorMatched),
            event("LIVE_PERIOD_SOURCE_CREATOR_MISSING",liveLinkedSourceCreatorMissing),
            event("LIVE_PERIOD_SOURCE_WRAPPER_LINK_MISSING",liveLinkedSourceWrapperLinkMissing),
            event("LIVE_PERIOD_SOURCE_LINK_MISMATCH",liveLinkedSourceLinkMismatch),
            event("LIVE_PERIOD_SOURCE_FACTORY_LINK_UNBOUND",liveLinkedSourceFactorySourceUnbound),
            event("LIVE_PERIOD_SOURCE_INSTANCE_NOT_LINKED",liveLinkedSourceInstanceNotLinked),
            event("LIVE_PERIOD_SOURCE_INSTANCE_WEAK_LOST",liveLinkedSourceInstanceWeakLost),
            event("LIVE_PERIOD_SOURCE_REVERSE_LINK_MISMATCH",liveLinkedSourceReverseLinkMismatch),
            event("LIVE_PERIOD_SOURCE_BETA_RECHECK_FAILED",liveLinkedSourceBetaRecheckFailed),
            event("LIVE_PERIOD_SOURCE_ALBUM_MISMATCH",liveLinkedSourceAlbumMismatch),
            event("LIVE_PERIOD_SOURCE_LOOKUP_RESOLVED",liveLinkedSourceResolved)
        };
    }
}
