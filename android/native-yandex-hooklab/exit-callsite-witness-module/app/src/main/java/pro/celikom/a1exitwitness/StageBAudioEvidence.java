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
    // continuity. Every object is weakly held and compared only with ==.
    private static final class NativeTrackSourceLink {
        WeakReference<Object> track;
        WeakReference<Object> wrapper;
        WeakReference<Object> descriptor;
        WeakReference<Object> factoryResult;
        WeakReference<Object> sourceInstance;
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
        if(source==null || wasSourceTouched(source))return;
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
        final WeakReference<Object> creatorTrack;
        final WeakReference<Object> albumAtBirth;
        final int scopeAtBirth;
        final String originalConstructorKey;
        boolean laterFlowEmitted;
        WrapperBirth(Object wrapper,int scopeAtBirth,Object track,Object album,
                String constructorKey) {
            this.wrapper=new WeakReference<>(wrapper);
            this.scopeAtBirth=scopeAtBirth;
            this.creatorTrack=track==null?null:new WeakReference<>(track);
            this.albumAtBirth=album==null?null:new WeakReference<>(album);
            this.originalConstructorKey=constructorKey;
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
        String id=numericOriginalId(raw);
        Object track=currentScope(activeTrackScopes),album=findTrackAlbum(track);
        if(id==null || track==null || album==null)return;
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
        if(status!=1 && status!=16)return null;
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
            if(matched==null || matched.scopeAtBirth!=12
                    || !matched.laterFlowEmitted
                    || matched.creatorTrack==null
                    || matched.albumAtBirth==null)return null;
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
        if(found.scopeAtBirth==12) {
            // Signed original creator Track not in Flow at wrapper birth.
            if(found.creatorTrack==null || found.albumAtBirth==null)return null;
            track=found.creatorTrack.get();
            album=found.albumAtBirth.get();
        } else {
            // The same original creator Track had ALREADY entered the
            // original Flow when the wrapper was constructed. Its exact
            // Track+Album reference is in the unique at-birth wrapper link.
            NativeTrackSourceLink linked=findByWrapper(wrapper);
            if(linked==null || linked.track==null || linked.albumInstance==null)
                return null;
            track=linked.track.get();
            album=linked.albumInstance.get();
            if(!wasNativeTrackFlowItem(track))return null;
        }
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

    // NAV40: only SAME original creator Track seen in Flow AFTER THIS
    // wrapper's birth. 16 same birth Album; 17 absent/conflicted Album;
    // 18 different Album; 19 weak Track/Flow window lost. Historical ONLY.
    private int classifyMissingWrapperBirth(Object wrapper) {
        if(wrapper==null)return 10;
        WrapperBirth found=null;
        for(WrapperBirth birth:wrapperBirths) {
            if(birth.wrapper.get()==wrapper) {
                if(found!=null)return 15;
                found=birth;
            }
        }
        if(found==null)return 10;
        if(found.scopeAtBirth!=12 || !found.laterFlowEmitted)
            return found.scopeAtBirth;
        Object track=found.creatorTrack==null?null:found.creatorTrack.get();
        if(track==null || !wasNativeTrackFlowItem(track))return 19;
        Object album=found.albumAtBirth==null?null:found.albumAtBirth.get();
        Object observed=findTrackAlbum(track);
        if(album==null || observed==null)return 17;
        return album==observed?16:18;
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
        if(wrapper!=null) {
            int atBirth=track==null?11:!wasNativeTrackFlowItem(track)?12:
                findTrackAlbum(track)==null?13:14;
            if(wrapperBirths.size()>=64)wrapperBirths.remove(0);
            Object birthAlbum=fromExactTcaCreator && atBirth==12
                ?findTrackAlbum(track):null;
            wrapperBirths.add(new WrapperBirth(wrapper,atBirth,
                fromExactTcaCreator && atBirth==12?track:null,birthAlbum,
                fromExactTcaCreator?numericOriginalId(originalConstructorArg):null));
        }
        if (track==null || wrapper==null) return;
        // In the issuer-signed creator, Track may reach Flow AFTER tCa
        // construction. Preserve the creator's exact Album/source lineage
        // without falsely promoting historical NAV40 Flow status.
        // atBirth is local to the weak birth-record branch above;
        // equivalent immutable birth condition is verified here again.
        boolean creatorOnlyAtBirth=fromExactTcaCreator
            && !wasNativeTrackFlowItem(track) && findTrackAlbum(track)!=null;
        if(!wasNativeTrackFlowItem(track) && !creatorOnlyAtBirth)return;
        NativeTrackSourceLink link=null;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink candidate=nativeTrackSourceLinks.get(i);
            if (candidate.track==null || candidate.track.get()==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if (candidate.track.get()==track) { link=candidate; break; }
        }
        if (link==null) {
            if (nativeTrackSourceLinks.size()>=16) nativeTrackSourceLinks.remove(0);
            link=new NativeTrackSourceLink();
            link.track=new WeakReference<>(track);
            nativeTrackSourceLinks.add(link);
        }
        Object album=findTrackAlbum(track);
        link.albumInstance=album==null ? null : new WeakReference<>(album);
        if (album!=null) mark(trackWrapperAlbumLinks);
        // Reconstructing a wrapper creates a new lineage generation. Old
        // descriptor/factory/source links must never be inherited by it.
        link.wrapper=new WeakReference<>(wrapper);
        link.creatorOnlyAtBirth=creatorOnlyAtBirth;
        link.descriptor=null;
        link.factoryResult=null;
        link.sourceInstance=null;
        link.sourceOpened=false;
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

    private synchronized boolean hasWrapperLink(Object wrapper) {
        return findByWrapper(wrapper)!=null;
    }

    synchronized void onNativeExoDescriptorBuiltForCurrentWrapper(Object descriptor) {
        Object wrapper=currentScope(activeWrapperScopes);
        if (wrapper==null || descriptor==null) return;
        NativeTrackSourceLink link=findByWrapper(wrapper);
        if (link!=null) {
            link.descriptor=new WeakReference<>(descriptor);
            link.factoryResult=null;
            link.sourceInstance=null;
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
        return match;
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
            link.factoryResult=new WeakReference<>(factoryResult);
            link.sourceInstance=null;
            link.sourceOpened=false;
            link.sourceReadAfterOpen=false;
            link.sourceAlbumReadAfterOpen=false;
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
        onExoSourceInstanceCreated(source);
        NativeTrackSourceLink link=findByFactory(factoryObject);
        if (link!=null && source!=null) {
            link.sourceInstance=new WeakReference<>(source);
            link.sourceOpened=false;
            link.sourceEverTouched=wasSourceTouched(source);
            link.sourceReadAfterOpen=false;
            link.sourceAlbumReadAfterOpen=false;
            trackSourceReadInspectionBudget.set(0);
            hasTrackSourceLink=true;
            if (link.albumInstance!=null && link.albumInstance.get()!=null)
                mark(trackSourceAlbumLinks);
            mark(trackFactorySourceLinks);
        }
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
            event("WRAPPER_MAIN_SOURCE", wrapperMainSourceRequests),
            event("WRAPPER_DESCRIPTOR_LINK", wrapperDescriptorLinks),
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
            "event=AUDIO_STAGE_B_STATUS;origin=CELIKOM_REPLACEMENT;error=NOT_CONNECTED;thread=OTHER"
        };
    }
}
