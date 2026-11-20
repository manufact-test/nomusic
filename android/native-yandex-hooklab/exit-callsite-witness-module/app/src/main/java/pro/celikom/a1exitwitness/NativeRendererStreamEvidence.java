package pro.celikom.a1exitwitness;

import java.lang.ref.WeakReference;
import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Constructor;
import java.util.ArrayList;

/**
 * NAV17 / signed 2025.10.4 only. Passive, in-process identities for exact
 * LmQ8.catch -> androidx.media3.exoplayer.b.package -> b.g -> LR29.read.
 *
 * This never opens, reads or persists stream contents or private metadata.
 * Reference equality is ONLY Java ==; no equals/hashCode/toString is called.
 * This is NOT a currently selected track/edition or audible decoder proof.
 */
final class NativeRendererStreamEvidence {
    private static final int MAX_HANDLES = 12;
    private static final int MAX_HOT_READ_OBSERVATIONS = 256;
    private static final int MAX_READS_PER_ATTACH = 8;
    private static final int MAX_COUNT = 1000;

    static final class Scope {
        final Object renderer, holder;
        final Scope parent;
        Scope(Object renderer, Object holder, Scope parent) {
            this.renderer=renderer;
            this.holder=holder;
            this.parent=parent;
        }
    }
    /**
     * A second, exact 2025 renderer attachment caller: b.super(lQ8, formats,
     * LR29, flags...). Counts callsite relation only, never source contents.
     * This is a caller discriminator, NOT an active-audio assertion.
     */
    static final class CallerFrame {
        final Object renderer, stream;
        final CallerFrame parent;
        CallerFrame(Object renderer,Object stream,CallerFrame parent) {
            this.renderer=renderer;
            this.stream=stream;
            this.parent=parent;
        }
    }
    /** Signed 2025 Exo engine e.catch(Lxh6;IZJ)V holder lifetime only. */
    static final class EngineFrame {
        final Object engine,holder;
        final EngineFrame parent;
        EngineFrame(Object engine,Object holder,EngineFrame parent) {
            this.engine=engine;
            this.holder=holder;
            this.parent=parent;
        }
    }
    private static final class Link {
        final WeakReference<Object> renderer, holder, stream;
        Link(Object renderer,Object holder,Object stream) {
            this.renderer=new WeakReference<>(renderer);
            this.holder=new WeakReference<>(holder);
            this.stream=new WeakReference<>(stream);
        }
    }
    // NAV28: one live native e.h.SLOT_B (queue-holder) -> renderer/stream
    // association, never promoted to selected-song/audio-content identity.
    private static final class LiveQueueLink {
        final WeakReference<Object> engine,holder,renderer,stream;
        LiveQueueLink(Object engine,Object holder,Object renderer,Object stream) {
            this.engine=new WeakReference<>(engine);
            this.holder=new WeakReference<>(holder);
            this.renderer=new WeakReference<>(renderer);
            this.stream=new WeakReference<>(stream);
        }
    }
    // Result of the exact signed LmQ8.try(holder, renderer) comparator.
    // Weak identity only; never exported. Stream is captured through the
    // already-proven renderer getter so reattach/reuse cannot inherit a stale
    // true result for a different stream.
    private static final class ComparatorLink {
        final WeakReference<Object> holder, renderer, stream;
        final boolean result;
        ComparatorLink(Object holder,Object renderer,Object stream,boolean result) {
            this.holder=new WeakReference<>(holder);
            this.renderer=new WeakReference<>(renderer);
            this.stream=new WeakReference<>(stream);
            this.result=result;
        }
    }

    // NAV29: source lineage from exact TrackWrapper-bearing cA9 method
    // through the native Player source setter into the CURRENT live Lo96.
    // Only bounded weak Java reference identity; no IDs, metadata or bytes.
    static final class TrackPlayerScope {
        final Object wrapper;
        final TrackPlayerScope parent;
        TrackPlayerScope(Object wrapper,TrackPlayerScope parent) {
            this.wrapper=wrapper;
            this.parent=parent;
        }
    }
    private static final class PlayerSourceLink {
        final WeakReference<Object> wrapper,source;
        boolean conflicted;
        PlayerSourceLink(Object wrapper,Object source) {
            this.wrapper=new WeakReference<>(wrapper);
            this.source=new WeakReference<>(source);
        }
    }
    // NAV30 signed candidate: associate the original Lp96.goto returned
    // Lwh6 adapter with the exact Lo96 returned by its own synchronous
    // Lp96.transient call on the SAME receiver. No class-name guesses or
    // reading media values. A stale/ambiguous frame never becomes evidence.
    static final class NativePeriodAdapterScope {
        final Object owner;
        final NativePeriodAdapterScope parent;
        Object factoryPeriod;
        boolean ambiguous;
        NativePeriodAdapterScope(Object owner,NativePeriodAdapterScope parent) {
            this.owner=owner;
            this.parent=parent;
        }
    }
    private static final class NativePeriodAdapterLink {
        final WeakReference<Object> returnedPeriod, exactLo96;
        NativePeriodAdapterLink(Object returned,Object inner) {
            this.returnedPeriod=new WeakReference<>(returned);
            this.exactLo96=new WeakReference<>(inner);
        }
    }
    private final ThreadLocal<NativePeriodAdapterScope> inPeriodAdapter=new ThreadLocal<>();
    private final ArrayList<NativePeriodAdapterLink> periodAdapters=new ArrayList<>();
    private int periodAdapterHook,periodFactoryHook;
    private int periodAdapterScopeEnter,periodFactoryInScope,periodFactoryConflict;
    private int periodAdapterLinkCreated,periodAdapterMapped,periodAdapterUnmapped;
    private int livePeriodHolderMissing,livePeriodWrappedMissing,livePeriodNonLo96;
    private int livePeriodDirectLo96,livePeriodSourceNull,livePeriodReflectionFailed;
    // NAV33: exact publisher Lo96 held directly, without Lup1 wrapper.
    private int directHolderSourcePresent,directHolderSourceNull;
    // NAV31: sampled ONLY at exact publisher-proven Lxh6.if() selection
    // and on the already live slot/renderer reference. Phase observations
    // are diagnostics, never proof of selected track/edition or PCM.
    private int holderSelectHook;
    private int selectEnterExact,selectEnterNull,selectEnterOther,selectEnterFail;
    private int selectExitExact,selectExitNull,selectExitOther,selectExitFail;
    private int attachPeriodExact,attachPeriodNull,attachPeriodOther,attachPeriodFail;
    private int livePeriodHolderNull,livePeriodHolderOther;
    private int priorSelectedExactCleared,priorSelectedExactPresent,priorSelectedWeakLost;
    private static final class HolderSelectionLink {
        final WeakReference<Object> holder,wrapper;
        HolderSelectionLink(Object holder,Object wrapper) {
            this.holder=new WeakReference<>(holder);
            this.wrapper=new WeakReference<>(wrapper);
        }
    }
    private final ArrayList<HolderSelectionLink> holderSelectionLinks=new ArrayList<>();
    // NAV32: owner NAV31 phone observed OTHER (not NULL, not Lup1)
    // at select ENTER/EXIT, live SLOT_B attach and started audio read.
    // Classify only known publisher interface wh6 and exact Lo96.
    // Weak identity is restricted to one exact original holder reference;
    // matching NEVER proves selected Track/Album/edition/queue generation.
    private Class<?> publisherMediaPeriodInterface;
    private int otherSelectEnterPeriod,otherSelectExitPeriod,otherAttachPeriod;
    private int otherReadPeriod,otherReadNotPeriod,otherReadLo96;
    private int otherReadSameNameDifferentLoader;
    private int otherSelectReadSame,otherSelectReadDifferent;
    private int otherSelectReadWeakLost,otherSelectReadNoHistory;
    private int otherAttachReadSame,otherAttachReadDifferent;
    private int otherAttachReadWeakLost,otherAttachReadNoHistory;
    private final ArrayList<HolderSelectionLink> otherSelectedLinks=new ArrayList<>();
    private final ArrayList<HolderSelectionLink> otherAttachedLinks=new ArrayList<>();
    private final ThreadLocal<TrackPlayerScope> inPlayerTrack=new ThreadLocal<>();
    private final ArrayList<PlayerSourceLink> playerSources=new ArrayList<>();
    private Field holderWrapperField,wrapperPeriodField,periodSourceField;
    private Class<?> exactWrapperClass,exactPeriodClass;
    private int originalPeriodPrepareHook;
    interface OriginalPeriodBeforePrepareObserver {
        void beforeOriginalPeriodPrepare(long generation,Object originalTrack,
                Object originalAlbum,Object originalSource,Object originalPeriod,
                Object originalDataSourceCandidate);
        void beforeUnverifiedOriginalPeriodPrepare();
    }
    interface OriginalPrePrepareSourceInstanceEvidence {
        Object exact(Object wrapper,Object originalTrack,Object originalAlbum);
    }
    private OriginalPrePrepareSourceInstanceEvidence originalPrePrepareSourceEvidence;
    synchronized void setOriginalPrePrepareSourceInstanceEvidence(
            OriginalPrePrepareSourceInstanceEvidence evidence) {
        originalPrePrepareSourceEvidence=evidence;
    }
    private OriginalPeriodBeforePrepareObserver originalPeriodBeforePrepareObserver;
    synchronized void setOriginalPeriodBeforePrepareObserver(
            OriginalPeriodBeforePrepareObserver observer) {
        originalPeriodBeforePrepareObserver=observer;
    }
    /**
     * Called immediately BEFORE the signed original concrete MediaPeriod
     * prepare method. Same original source reference as the last successful
     * publisher Player setter is required. This is NOT necessarily selected
     * (prefetch is possible) and cannot authorize alternate audio alone.
     */
    synchronized boolean onOriginalPeriodBeforePrepare(Object period) {
        if(originalPeriodPrepareHook<=0 || originalPeriodBeforePrepareObserver==null)
            return false;
        // A real publisher prepare with NO provably matching original source
        // still closes any unresolved CELIKOM candidate for this generation.
        // This prevents a delayed ID/grant from upgrading a player that may
        // already be preparing an unknown/prefetched period.
        if(poisoned || period==null || exactPeriodClass==null
                || !exactPeriodClass.isInstance(period) || periodSourceField==null
                || earlySourceInFlight!=null) {
            sealUnverifiedOriginalPeriodPrepare();
            return false;
        }
        final Object source;
        try {source=periodSourceField.get(period);}
        catch(Throwable ignored) {
            sealUnverifiedOriginalPeriodPrepare();
            return false;
        }
        OriginalSetterLineage saved=exactOriginalSetterLineage;
        if(saved==null || source==null || saved.source.get()!=source) {
            sealUnverifiedOriginalPeriodPrepare();
            return false;
        }
        Object[] evidence=exactEarlySetterSourceAtGeneration(source,saved.generation);
        if(evidence==null) {
            sealUnverifiedOriginalPeriodPrepare();
            return false;
        }
        try {
            Object dataSourceCandidate=null;
            if(originalPrePrepareSourceEvidence!=null) {
                Object wrapper=saved.wrapper.get();
                if(wrapper!=null) {
                    try {
                        dataSourceCandidate=originalPrePrepareSourceEvidence.exact(
                            wrapper,evidence[0],evidence[1]);
                    } catch(Throwable ignored) { }
                }
            }
            originalPeriodBeforePrepareObserver.beforeOriginalPeriodPrepare(
                saved.generation,evidence[0],evidence[1],source,period,
                dataSourceCandidate);
            return true;
        } catch(Throwable ignored) {
            sealUnverifiedOriginalPeriodPrepare();
            return false;
        }
    }
    private void sealUnverifiedOriginalPeriodPrepare() {
        try { originalPeriodBeforePrepareObserver.beforeUnverifiedOriginalPeriodPrepare(); }
        catch(Throwable ignored) { }
    }
    private int trackPlayerScopeHook,nativeSourceSetterHook,livePeriodSourceHook;
    private int trackPlayerScopeEnter,playerSourceSameScope,playerSourceUnscoped;
    private int playerSourceConflict,livePeriodResolved,livePeriodUnavailable;
    private int livePeriodSourceMatched,livePeriodSourceDifferent,livePeriodSourceNoLink;
    // NAV34: ONLY after a strict live-original-source == scoped native
    // Player setter source, inspect the SAME tCa wrapper's Stage B album link.
    // Historical structural link; NEVER selected track, queue generation or PCM.
    interface ScOpedAlbumEvidence { int classify(Object scopedWrapper); }
    private ScOpedAlbumEvidence scopedAlbumEvidence;
    private int scopedAlbumMatch,scopedAlbumNoLink,scopedAlbumConflict;
    // NAV35: separate mutually exclusive reasons under the same exact
    // live-source guard. No identities, content, URLs or durations logged.
    private int scopedReasonWrapperAbsent,scopedReasonWrapperAmbiguous;
    private int scopedReasonTrackWeakLost,scopedReasonAlbumUnset;
    private int scopedReasonAlbumWeakLost,scopedReasonFlowMissing;
    private int scopedReasonTrackAlbumMissing,scopedReasonUnknown;
    // NAV36: finer reasons exclusively UNDER strict-source WRAPPER_ABSENT.
    private int scopedBirthNotInWindow,scopedBirthNoTrackScope;
    private int scopedBirthTrackNotInFlow,scopedBirthFlowNoAlbum;
    private int scopedBirthFlowAlbumButLinkMissing,scopedBirthAmbiguous;
    // NAV40: strictly gated by same live original period/setter source.
    private int scopedLateFlowAlbumSame,scopedLateFlowAlbumMissing;
    private int scopedLateFlowAlbumDifferent,scopedLateFlowReferenceLost;
    synchronized void setScopedAlbumEvidence(ScOpedAlbumEvidence evidence) {
        scopedAlbumEvidence=evidence;
    }
    // One original-reference-only path from NAV40 creator Track+Album to
    // the exact selected native source on the SAME renderer callback.
    // No retained track/album, ID reading, PCM, replacement or second Player.
    interface ExactOriginalTrackAlbumEvidence { Object[] exact(Object wrapper); }
    interface ActiveOriginalTrackObserver {
        void observe(Object originalTrack,Object originalAlbum,Object liveSource);
    }
    private ExactOriginalTrackAlbumEvidence exactOriginalTrackAlbumEvidence;
    private ActiveOriginalTrackObserver activeOriginalTrackObserver;

    // Early original Exo Player source SETTER boundary, before vendor method
    // execution. This is not by itself source prepare/decoder or permission.
    // The only early identity is the exact creator-owned Java Track+Album.
    interface EarlyOriginalSourceEvidence { Object[] exact(Object wrapper); }
    // Only the actual issuer-annotated FileInfo/DownloadInfo proxy trackId
    // already matched to original Gp0 Track + Album + tCa key may supply it.
    // This is a candidate, NOT edition/album/decoder/grant authorisation.
    interface ExactPublisherTrackIdEvidence {
        String exact(Object wrapper,Object originalTrack,Object originalAlbum);
    }
    interface EarlyOriginalSourceObserver {
        // This is invoked on EVERY original setter attempt, including a
        // missing Track/Album or an overlapping setter. No stale generation
        // may survive Next, replay or an unscoped original source.
        default void invalidated(long generation) { }
        // A rejected early attempt (unknown wrapper, overlapping setter,
        // missing original album) has no finish callback. It must still
        // cancel the unresolved native selection reserved by invalidated().
        default void rejected(long generation) { }
        void pending(long generation,Object track,Object album,Object source);
        void completed(long generation,boolean originalSetterSucceeded);
    }
    static final class EarlyOriginalSourceFrame {
        final Object wrapper,track,album,source;
        final long generation;
        final String originalPublisherTrackIdCandidate;
        boolean invalid;
        EarlyOriginalSourceFrame(Object wrapper,Object track,Object album,
                Object source,long generation,String publisherTrackIdCandidate) {
            this.wrapper=wrapper;this.track=track;this.album=album;
            this.source=source;this.generation=generation;
            originalPublisherTrackIdCandidate=publisherTrackIdCandidate;
        }
    }
    private EarlyOriginalSourceEvidence earlyOriginalSourceEvidence;
    private ExactPublisherTrackIdEvidence exactPublisherTrackIdEvidence;
    private EarlyOriginalSourceObserver earlyOriginalSourceObserver;
    private EarlyOriginalSourceFrame earlySourceInFlight;
    private long earlySourceGeneration;
    // Strong Track/Album/source refs live ONLY in the synchronous hook frame;
    // after a successful original setter only weak identity lineage is kept.
    // Never label this object as current PCM or decoder pre-prepare proof.
    private static final class OriginalSetterLineage {
        final WeakReference<Object> wrapper,track,album,source;
        final long generation;
        OriginalSetterLineage(EarlyOriginalSourceFrame frame) {
            wrapper=new WeakReference<>(frame.wrapper);
            track=new WeakReference<>(frame.track);
            album=new WeakReference<>(frame.album);
            source=new WeakReference<>(frame.source);
            generation=frame.generation;
        }
    }
    private OriginalSetterLineage exactOriginalSetterLineage;

    synchronized void setEarlyOriginalSourceEvidence(EarlyOriginalSourceEvidence evidence) {
        earlyOriginalSourceEvidence=evidence;
    }
    synchronized void setExactPublisherTrackIdEvidence(
            ExactPublisherTrackIdEvidence evidence) {
        exactPublisherTrackIdEvidence=evidence;
    }
    synchronized void setEarlyOriginalSourceObserver(EarlyOriginalSourceObserver observer) {
        earlyOriginalSourceObserver=observer;
    }
    private void rejectEarlyOriginalSelection(long generation) {
        if(earlyOriginalSourceObserver!=null) {
            try {earlyOriginalSourceObserver.rejected(generation);}
            catch(Throwable ignored) { }
        }
    }
    synchronized EarlyOriginalSourceFrame beginEarlyOriginalSourceSet(Object source) {
        // Every selection attempt, even one without proof, invalidates prior
        // pending generations. No repeat/Next may inherit the old candidate.
        long generation=++earlySourceGeneration;
        exactOriginalSetterLineage=null; // Next/replay/unscoped setter invalidates it.
        if(earlyOriginalSourceObserver!=null) {
            try {earlyOriginalSourceObserver.invalidated(generation);}
            catch(Throwable ignored) { }
        }
        if(earlySourceInFlight!=null) {
            earlySourceInFlight.invalid=true;
            rejectEarlyOriginalSelection(generation);
            return null; // overlapping/nested setters are never admitted
        }
        TrackPlayerScope scope=inPlayerTrack.get();
        if(poisoned || source==null || scope==null || scope.wrapper==null
                || earlyOriginalSourceEvidence==null) {
            rejectEarlyOriginalSelection(generation);
            return null;
        }
        Object[] pair;
        try {pair=earlyOriginalSourceEvidence.exact(scope.wrapper);}
        catch(Throwable ignored) {
            rejectEarlyOriginalSelection(generation);
            return null;
        }
        if(pair==null || pair.length!=2 || pair[0]==null || pair[1]==null) {
            rejectEarlyOriginalSelection(generation);
            return null;
        }
        String publisherTrackId=null;
        if(exactPublisherTrackIdEvidence!=null) {
            try {
                String candidate=exactPublisherTrackIdEvidence.exact(
                    scope.wrapper,pair[0],pair[1]);
                if(candidate!=null && candidate.matches("[1-9][0-9]{0,23}"))
                    publisherTrackId=candidate;
            } catch(Throwable ignored) { }
        }
        EarlyOriginalSourceFrame frame=new EarlyOriginalSourceFrame(
            scope.wrapper,pair[0],pair[1],source,generation,publisherTrackId);
        earlySourceInFlight=frame;
        // This notification is PENDING, never a source replacement decision.
        // A failed original setter must revoke it in finishEarlyOriginalSourceSet.
        if(earlyOriginalSourceObserver!=null) {
            try {earlyOriginalSourceObserver.pending(
                generation,frame.track,frame.album,frame.source);}
            catch(Throwable ignored) {frame.invalid=true;}
        }
        return frame;
    }
    synchronized void finishEarlyOriginalSourceSet(EarlyOriginalSourceFrame frame,
                                                    boolean originalSucceeded) {
        if(frame==null)return;
        boolean succeeded=originalSucceeded && !frame.invalid
            && earlySourceInFlight==frame
            && earlySourceGeneration==frame.generation
            && inPlayerTrack.get()!=null
            && inPlayerTrack.get().wrapper==frame.wrapper;
        if(earlySourceInFlight==frame)earlySourceInFlight=null;
        if(succeeded)exactOriginalSetterLineage=new OriginalSetterLineage(frame);
        if(earlyOriginalSourceObserver!=null) {
            try {earlyOriginalSourceObserver.completed(frame.generation,succeeded);}
            catch(Throwable ignored) { }
        }
    }
    /**
     * Exact immutable original setter lineage for one successful selection
     * attempt, never a current-player, PCM, edition or ID assertion.
     * Any later source setter invalidates the previous generation first.
     */
    synchronized Object[] exactEarlySetterSourceAtGeneration(
            Object originalSource,long expectedGeneration) {
        OriginalSetterLineage saved=exactOriginalSetterLineage;
        if(poisoned || earlySourceInFlight!=null || originalSource==null
                || saved==null || expectedGeneration!=earlySourceGeneration
                || expectedGeneration!=saved.generation
                || saved.source.get()!=originalSource
                || earlyOriginalSourceEvidence==null)return null;
        Object wrapper=saved.wrapper.get(),track=saved.track.get(),album=saved.album.get();
        if(wrapper==null || track==null || album==null)return null;
        Object[] still;
        try {still=earlyOriginalSourceEvidence.exact(wrapper);}
        catch(Throwable ignored) {return null;}
        if(still==null || still.length!=2
                || still[0]!=track || still[1]!=album)return null;
        return new Object[]{track,album,originalSource};
    }

    synchronized void setExactOriginalTrackAlbumEvidence(ExactOriginalTrackAlbumEvidence evidence) {
        exactOriginalTrackAlbumEvidence=evidence;
    }
    synchronized void setActiveOriginalTrackObserver(ActiveOriginalTrackObserver observer) {
        activeOriginalTrackObserver=observer;
    }
    private static final class ExactOriginalSourceRead {
        final Object source,track,album;
        ExactOriginalSourceRead(Object source,Object track,Object album) {
            this.source=source;this.track=track;this.album=album;
        }
    }
    private final ThreadLocal<Scope> inAttach = new ThreadLocal<>();
    private final ThreadLocal<CallerFrame> inSecondaryCaller = new ThreadLocal<>();
    private final ThreadLocal<EngineFrame> inEngineEnable = new ThreadLocal<>();
    private Field engineHolderStreamArrayField;
    private Field engineQueueField,queueSlotBField;
    private final ArrayList<LiveQueueLink> liveQueueLinks=new ArrayList<>();

    // NAV41 candidate, no vendor mutation: exact publisher e.PlaybackInfo
    // current-period ID versus the already verified live SLOT_B period ID,
    // sampled only on the *same* non-EOS (-4) renderer read.
    // This never declares selected MediaItem, audible PCM or queue generation.
    private Field currentEnginePlaybackInfoField,currentPlaybackIdField;
    private Field currentHolderInfoField,currentHolderIdField;
    private Field currentPeriodUidField,currentPeriodFirstIntField,currentPeriodSecondIntField;
    private int currentPeriodAtReadHook,currentPeriodSameReferenceAtRead;
    private int currentPeriodUidAndIntsAtRead,currentPeriodUidOnlyAtRead;
    private int currentPeriodDifferentAtRead,currentPeriodUnavailableAtRead;
    // NAV42: unknown EOS is NOT promoted to a non-EOS audio sample.
    // On the same strict SLOT_B read, separately classify only structural
    // PlaybackInfo<->holder PeriodID reference/field relationships.
    private int periodUnknownEosSame,periodUnknownEosUidInts;
    private int periodUnknownEosUidOnly,periodUnknownEosDifferent;
    private int periodUnknownEosUnavailable;
    // Same sampled callback only: a current PlaybackInfo-to-SLOT_B ID
    // equality and one unique late-Flow original-source TrackWrapper.
    // Structural evidence only; EOS unknown, not selected edition/audio.
    private int jointUnknownEosPeriodFlowSame;
    private int jointUnknownEosPeriodNoFlow;
    private int jointUnknownEosPeriodSlotChanged;

    // NAV44: strictly same-current-PeriodID / SLOT_B callback, compare the
    // signed original Timeline Window MediaItem reference against the SAME
    // uniquely scoped original LiLb source's MediaItem field. Never read
    // track IDs, titles, URLs, editions, PCM or arbitrary objects.
    private Field selectedPlaybackTimelineField,selectedPeriodWindowIndexField;
    private Field selectedWindowMediaItemField,selectedSourceMediaItemField;
    private Method selectedPeriodByUid,selectedWindowByIndex;
    private Constructor<?> selectedPeriodConstructor,selectedWindowConstructor;
    private int selectedItemSourceHook,selectedItemSame,selectedItemDifferent;
    private int selectedItemUnavailable,selectedItemSlotChanged;
    // NAV45: publisher-signed unique final String field of the very same
    // two MediaItem objects. String values NEVER enter counters, logs or
    // persistent data; blank/default IDs are not a match.
    private Field selectedLogicalItemIdField;
    private int selectedLogicalIdHook,selectedLogicalIdMatch;
    private int selectedLogicalIdDifferent,selectedLogicalIdBlank;
    private int selectedLogicalIdUnavailable;
    synchronized void setSelectedLogicalMediaIdField(Field logicalId) {
        if(logicalId==null || selectedSourceMediaItemField==null
                || selectedWindowMediaItemField==null
                || logicalId.getDeclaringClass()!=selectedSourceMediaItemField.getType()
                || logicalId.getDeclaringClass()!=selectedWindowMediaItemField.getType()
                || logicalId.getType()!=String.class
                || !java.lang.reflect.Modifier.isFinal(logicalId.getModifiers())
                || java.lang.reflect.Modifier.isStatic(logicalId.getModifiers()))
            throw new IllegalArgumentException("NAV45 exact signed immutable MediaItem ID required");
        logicalId.setAccessible(true);
        selectedLogicalItemIdField=logicalId;
    }
    private static final class SelectedItemProbe {
        final WeakReference<Object> holder,source;
        int tries;
        boolean finalResult;
        SelectedItemProbe(Object holder,Object source) {
            this.holder=new WeakReference<>(holder);
            this.source=new WeakReference<>(source);
        }
    }
    private final ArrayList<SelectedItemProbe> selectedItemProbes=new ArrayList<>();

    synchronized void setSelectedMediaItemSourceFields(
            Field playbackTimeline,Field periodWindowIndex,Field windowMediaItem,
            Field sourceMediaItem,Method periodByUid,Method windowByIndex,
            Constructor<?> periodConstructor,Constructor<?> windowConstructor) {
        if(currentPlaybackIdField==null || playbackTimeline==null
                || periodWindowIndex==null || windowMediaItem==null
                || sourceMediaItem==null || periodByUid==null || windowByIndex==null
                || periodConstructor==null || windowConstructor==null
                || playbackTimeline.getDeclaringClass()!=currentPlaybackIdField.getDeclaringClass()
                || periodWindowIndex.getType()!=int.class
                || windowMediaItem.getType()!=sourceMediaItem.getType()
                || periodByUid.getParameterCount()!=2
                || periodByUid.getParameterTypes()[0]!=Object.class
                || periodByUid.getParameterTypes()[1]!=periodWindowIndex.getDeclaringClass()
                || periodByUid.getReturnType()!=periodWindowIndex.getDeclaringClass()
                || !periodByUid.getDeclaringClass().isAssignableFrom(playbackTimeline.getType())
                || windowByIndex.getParameterCount()!=3
                || windowByIndex.getParameterTypes()[0]!=int.class
                || windowByIndex.getParameterTypes()[1]!=windowMediaItem.getDeclaringClass()
                || windowByIndex.getParameterTypes()[2]!=long.class
                || windowByIndex.getReturnType()!=windowMediaItem.getDeclaringClass()
                || !windowByIndex.getDeclaringClass().isAssignableFrom(playbackTimeline.getType())
                || periodConstructor.getDeclaringClass()!=periodWindowIndex.getDeclaringClass()
                || windowConstructor.getDeclaringClass()!=windowMediaItem.getDeclaringClass()) {
            throw new IllegalArgumentException("NAV44 exact original Timeline/MediaItem target required");
        }
        for(Field f:new Field[]{playbackTimeline,periodWindowIndex,
                windowMediaItem,sourceMediaItem}) f.setAccessible(true);
        periodByUid.setAccessible(true);
        windowByIndex.setAccessible(true);
        periodConstructor.setAccessible(true);
        windowConstructor.setAccessible(true);
        selectedPlaybackTimelineField=playbackTimeline;
        selectedPeriodWindowIndexField=periodWindowIndex;
        selectedWindowMediaItemField=windowMediaItem;
        selectedSourceMediaItemField=sourceMediaItem;
        selectedPeriodByUid=periodByUid;
        selectedWindowByIndex=windowByIndex;
        selectedPeriodConstructor=periodConstructor;
        selectedWindowConstructor=windowConstructor;
    }

    private SelectedItemProbe sampleSelectedSource(Object holder,Object source) {
        if(selectedItemSourceHook<=0 || selectedPlaybackTimelineField==null
                || holder==null || source==null)return null;
        for(int i=selectedItemProbes.size()-1;i>=0;i--) {
            SelectedItemProbe prior=selectedItemProbes.get(i);
            if(prior.holder.get()==null || prior.source.get()==null) {
                selectedItemProbes.remove(i);continue;
            }
            if(prior.holder.get()==holder && prior.source.get()==source) {
                if(prior.finalResult || prior.tries>=3)return null;
                prior.tries++;
                return prior;
            }
        }
        if(selectedItemProbes.size()>=24)selectedItemProbes.remove(0);
        SelectedItemProbe fresh=new SelectedItemProbe(holder,source);
        fresh.tries=1;
        selectedItemProbes.add(fresh);
        return fresh;
    }

    private void observeSelectedMediaItemSameRead(Object engine,Object holder,Object source) {
        SelectedItemProbe probe=sampleSelectedSource(holder,source);
        if(probe==null || engine==null)return;
        try {
            if(!selectedSourceMediaItemField.getDeclaringClass().isInstance(source))
                throw new IllegalStateException("NAV44_SOURCE_CLASS_OTHER");
            Object info=currentEnginePlaybackInfoField.get(engine);
            Object holderInfo=currentHolderInfoField.get(holder);
            if(info==null || holderInfo==null)throw new IllegalStateException();
            Object playbackId=currentPlaybackIdField.get(info);
            Object holderId=currentHolderIdField.get(holderInfo);
            if(playbackId==null || holderId==null)throw new IllegalStateException();
            Object uid=currentPeriodUidField.get(playbackId);
            if(uid==null || uid!=currentPeriodUidField.get(holderId)
                    || currentPeriodFirstIntField.getInt(playbackId)
                        !=currentPeriodFirstIntField.getInt(holderId)
                    || currentPeriodSecondIntField.getInt(playbackId)
                        !=currentPeriodSecondIntField.getInt(holderId))
                throw new IllegalStateException();
            int first=currentPeriodFirstIntField.getInt(playbackId);
            int second=currentPeriodSecondIntField.getInt(playbackId);
            Object timeline=selectedPlaybackTimelineField.get(info);
            if(timeline==null)throw new IllegalStateException();
            Object periodScratch=selectedPeriodConstructor.newInstance();
            Object period=selectedPeriodByUid.invoke(timeline,uid,periodScratch);
            if(period!=periodScratch)throw new IllegalStateException();
            int windowIndex=selectedPeriodWindowIndexField.getInt(period);
            if(windowIndex<0)throw new IllegalStateException();
            Object windowScratch=selectedWindowConstructor.newInstance();
            Object window=selectedWindowByIndex.invoke(timeline,windowIndex,windowScratch,0L);
            if(window!=windowScratch)throw new IllegalStateException();
            Object selected=selectedWindowMediaItemField.get(window);
            Object sourceItem=selectedSourceMediaItemField.get(source);
            if(selected==null || sourceItem==null)throw new IllegalStateException();
            // The sampled Player/PeriodID, current Timeline and live holder
            // MUST still be unchanged after both original read-only lookups.
            if(currentEnginePlaybackInfoField.get(engine)!=info
                    || currentPlaybackIdField.get(info)!=playbackId
                    || currentHolderInfoField.get(holder)!=holderInfo
                    || currentHolderIdField.get(holderInfo)!=holderId
                    || selectedPlaybackTimelineField.get(info)!=timeline
                    || currentPeriodUidField.get(playbackId)!=uid
                    || currentPeriodUidField.get(holderId)!=uid
                    || currentPeriodFirstIntField.getInt(playbackId)!=first
                    || currentPeriodFirstIntField.getInt(holderId)!=first
                    || currentPeriodSecondIntField.getInt(playbackId)!=second
                    || currentPeriodSecondIntField.getInt(holderId)!=second
                    || selectedSourceMediaItemField.get(source)!=sourceItem
                    || liveQueueSlotMatches(engine,holder)!=1) {
                selectedItemSlotChanged=inc(selectedItemSlotChanged);
                return;
            }
            // A stable SLOT_B pointer is not enough if its period's
            // underlying source changes without changing the queue holder.
            // Only the signed-direct period/wrapper paths can be re-read;
            // adapter ambiguity fails closed, never borrows an old link.
            Object nested=holderWrapperField.get(holder);
            Object exactPeriod=null;
            if(exactPeriodClass.isInstance(nested))exactPeriod=nested;
            else if(exactWrapperClass.isInstance(nested)) {
                Object original=wrapperPeriodField.get(nested);
                if(exactPeriodClass.isInstance(original))exactPeriod=original;
            }
            if(exactPeriod==null || periodSourceField.get(exactPeriod)!=source) {
                selectedItemSlotChanged=inc(selectedItemSlotChanged);
                return;
            }
            probe.finalResult=true;
            if(selected==sourceItem)selectedItemSame=inc(selectedItemSame);
            else selectedItemDifferent=inc(selectedItemDifferent);
            if(selectedLogicalIdHook>0 && selectedLogicalItemIdField!=null) {
                // Only two immutable String fields; comparison is local.
                // Nonempty equality is candidate logical item identity,
                // NOT a selected edition/generation/PCM proof.
                try {
                    Object a=selectedLogicalItemIdField.get(selected);
                    Object b=selectedLogicalItemIdField.get(sourceItem);
                    if(!(a instanceof String) || !(b instanceof String)
                            || ((String)a).isEmpty() || ((String)b).isEmpty()) {
                        selectedLogicalIdBlank=inc(selectedLogicalIdBlank);
                    } else if(((String)a).equals((String)b)) {
                        selectedLogicalIdMatch=inc(selectedLogicalIdMatch);
                    } else selectedLogicalIdDifferent=inc(selectedLogicalIdDifferent);
                } catch(Throwable ignoredId) {
                    selectedLogicalIdUnavailable=inc(selectedLogicalIdUnavailable);
                }
            }
        } catch(Throwable ignored) {
            selectedItemUnavailable=inc(selectedItemUnavailable);
        }
    }

    synchronized void setCurrentPlaybackPeriodFields(
            Field engineInfo,Field playbackId,Field holderInfo,Field holderId,
            Field uid,Field first,Field second) {
        if(engineInfo==null || playbackId==null || holderInfo==null
                || holderId==null || uid==null || first==null || second==null
                || engineInfo.getType()!=playbackId.getDeclaringClass()
                || holderInfo.getType()!=holderId.getDeclaringClass()
                || playbackId.getType()!=holderId.getType()
                || uid.getDeclaringClass()!=playbackId.getType()
                || first.getDeclaringClass()!=playbackId.getType()
                || second.getDeclaringClass()!=playbackId.getType()
                || uid.getType()!=Object.class
                || first.getType()!=int.class || second.getType()!=int.class
                || first.equals(second))
            throw new IllegalArgumentException("Exact signed PlaybackInfo/holder PeriodID fields required");
        for(Field f:new Field[]{engineInfo,playbackId,holderInfo,holderId,uid,first,second})
            f.setAccessible(true);
        currentEnginePlaybackInfoField=engineInfo;
        currentPlaybackIdField=playbackId;
        currentHolderInfoField=holderInfo;
        currentHolderIdField=holderId;
        currentPeriodUidField=uid;
        currentPeriodFirstIntField=first;
        currentPeriodSecondIntField=second;
    }

    private void observeCurrentPlaybackPeriodAtRead(Object engine,Object holder,boolean eosUnverified) {
        if(currentPeriodAtReadHook<=0 || currentEnginePlaybackInfoField==null
                || engine==null || holder==null)return;
        try {
            Object info=currentEnginePlaybackInfoField.get(engine);
            Object holderInfo=currentHolderInfoField.get(holder);
            if(info==null || holderInfo==null) {
                if(eosUnverified)periodUnknownEosUnavailable=inc(periodUnknownEosUnavailable);
                else currentPeriodUnavailableAtRead=inc(currentPeriodUnavailableAtRead);
                return;
            }
            Object playbackId=currentPlaybackIdField.get(info);
            Object activeId=currentHolderIdField.get(holderInfo);
            if(playbackId==null || activeId==null) {
                if(eosUnverified)periodUnknownEosUnavailable=inc(periodUnknownEosUnavailable);
                else currentPeriodUnavailableAtRead=inc(currentPeriodUnavailableAtRead);
                return;
            }
            Object playerUid=currentPeriodUidField.get(playbackId);
            Object holderUid=currentPeriodUidField.get(activeId);
            int playerFirst=currentPeriodFirstIntField.getInt(playbackId);
            int holderFirst=currentPeriodFirstIntField.getInt(activeId);
            int playerSecond=currentPeriodSecondIntField.getInt(playbackId);
            int holderSecond=currentPeriodSecondIntField.getInt(activeId);
            // Reject replaced PlaybackInfo, holder info or MediaPeriodId during
            // sampling; immutable identity alone is not a generation stamp.
            if(currentEnginePlaybackInfoField.get(engine)!=info
                    || currentHolderInfoField.get(holder)!=holderInfo
                    || currentPlaybackIdField.get(info)!=playbackId
                    || currentHolderIdField.get(holderInfo)!=activeId
                    || currentPeriodUidField.get(playbackId)!=playerUid
                    || currentPeriodUidField.get(activeId)!=holderUid
                    || currentPeriodFirstIntField.getInt(playbackId)!=playerFirst
                    || currentPeriodFirstIntField.getInt(activeId)!=holderFirst
                    || currentPeriodSecondIntField.getInt(playbackId)!=playerSecond
                    || currentPeriodSecondIntField.getInt(activeId)!=holderSecond) {
                if(eosUnverified)periodUnknownEosUnavailable=inc(periodUnknownEosUnavailable);
                else currentPeriodUnavailableAtRead=inc(currentPeriodUnavailableAtRead);
                return;
            }
            // The queue pointer may move while fields are sampled.
            // Never count a stale holder after the second live-slot check.
            if(liveQueueSlotMatches(engine,holder)!=1) {
                if(eosUnverified)periodUnknownEosUnavailable=inc(periodUnknownEosUnavailable);
                else currentPeriodUnavailableAtRead=inc(currentPeriodUnavailableAtRead);
                return;
            }
            if(playbackId==activeId) {
                if(eosUnverified)periodUnknownEosSame=inc(periodUnknownEosSame);
                else currentPeriodSameReferenceAtRead=inc(currentPeriodSameReferenceAtRead);
            } else if(playerUid!=null && playerUid==holderUid
                    && playerFirst==holderFirst && playerSecond==holderSecond) {
                if(eosUnverified)periodUnknownEosUidInts=inc(periodUnknownEosUidInts);
                else currentPeriodUidAndIntsAtRead=inc(currentPeriodUidAndIntsAtRead);
            } else if(playerUid!=null && playerUid==holderUid) {
                if(eosUnverified)periodUnknownEosUidOnly=inc(periodUnknownEosUidOnly);
                else currentPeriodUidOnlyAtRead=inc(currentPeriodUidOnlyAtRead);
            } else {
                if(eosUnverified)periodUnknownEosDifferent=inc(periodUnknownEosDifferent);
                else currentPeriodDifferentAtRead=inc(currentPeriodDifferentAtRead);
            }
        } catch(Throwable ignored) {
            if(eosUnverified)periodUnknownEosUnavailable=inc(periodUnknownEosUnavailable);
            else currentPeriodUnavailableAtRead=inc(currentPeriodUnavailableAtRead);
        }
    }

    /**
     * Candidate selected original PeriodID at the instant of consumption.
     * Fail closed across queue moves, source rebinding, MediaPeriod adapters
     * and replacement of PlaybackInfo/period objects. Never call equals().
     */
    private boolean originalPeriodIdStillCurrent(Object engine,Object holder) {
        if(engine==null || holder==null || currentEnginePlaybackInfoField==null
                || currentPlaybackIdField==null || currentHolderInfoField==null
                || currentHolderIdField==null || currentPeriodUidField==null
                || currentPeriodFirstIntField==null
                || currentPeriodSecondIntField==null)return false;
        try {
            Object info=currentEnginePlaybackInfoField.get(engine);
            Object holderInfo=currentHolderInfoField.get(holder);
            if(info==null || holderInfo==null)return false;
            Object a=currentPlaybackIdField.get(info);
            Object b=currentHolderIdField.get(holderInfo);
            if(a==null || b==null)return false;
            Object uid=currentPeriodUidField.get(a);
            if(uid==null || uid!=currentPeriodUidField.get(b))return false;
            int first=currentPeriodFirstIntField.getInt(a);
            int second=currentPeriodSecondIntField.getInt(a);
            if(first!=currentPeriodFirstIntField.getInt(b)
                    || second!=currentPeriodSecondIntField.getInt(b))return false;
            return currentEnginePlaybackInfoField.get(engine)==info
                && currentHolderInfoField.get(holder)==holderInfo
                && currentPlaybackIdField.get(info)==a
                && currentHolderIdField.get(holderInfo)==b
                && currentPeriodUidField.get(a)==uid
                && currentPeriodUidField.get(b)==uid
                && currentPeriodFirstIntField.getInt(a)==first
                && currentPeriodFirstIntField.getInt(b)==first
                && currentPeriodSecondIntField.getInt(a)==second
                && currentPeriodSecondIntField.getInt(b)==second
                && liveQueueSlotMatches(engine,holder)==1;
        } catch(Throwable ignored) { return false; }
    }

    private boolean holderStillHasOriginalSource(Object holder,Object expectedSource) {
        if(holder==null || expectedSource==null || holderWrapperField==null
                || wrapperPeriodField==null || periodSourceField==null
                || exactPeriodClass==null)return false;
        try {
            Object nested=holderWrapperField.get(holder);
            Object period=null;
            if(exactPeriodClass.isInstance(nested))period=nested;
            else if(exactWrapperClass!=null && exactWrapperClass.isInstance(nested)) {
                Object underlying=wrapperPeriodField.get(nested);
                if(exactPeriodClass.isInstance(underlying))period=underlying;
            }
            return period!=null && periodSourceField.get(period)==expectedSource
                    && holderWrapperField.get(holder)==nested;
        } catch(Throwable ignored) { return false; }
    }

    private int liveQueueSlotHook,queueSlotAttachSame,queueSlotAttachOther;
    private int queueSlotAttachUnavailable,queueSlotReadSame,queueSlotReadOther;
    private int queueSlotReadUnavailable,queueSlotReadMinus4;
    private final ArrayList<Link> engineHolderLinks = new ArrayList<>();
    private final ArrayList<ComparatorLink> comparatorLinks = new ArrayList<>();
    private final ArrayList<Link> links = new ArrayList<>();
    // Unscoped renderer/stream observations are separate: never infer holder identity.
    private final ArrayList<Link> unscopedLinks = new ArrayList<>();
    // 0 not attempted/guarded, 1 registered, -1 failed.
    private int queueHook, attachHook, readHook, detachHook, secondaryCallerHook, engineScopeHook;
    private int engineEnters, engineHolderStreamMatch, engineHolderStreamDifferent;
    private int engineHolderArrayUnavailable, engineReadMinus4, engineReadMinus5;
    private int engineReadMinus3, engineReadOther;
    // NAV24 additional *original method* values: renderer kind 1 and state 2
    // observed on the exact same strict engine-holder-to-read link.
    // Numbers alone do not attest audible PCM, selected track or edition.
    private int typeStateAccessHook, bufferEosAccessHook, rendererComparatorHook;
    private int rendererComparatorTrue, rendererComparatorFalse, rendererComparatorUnavailable;
    // NAV27: read-only timing/alias discriminator. At-call cohorts never
    // upgrade the comparator boolean to selected-track identity.
    private int comparatorAtEngineMatch, comparatorAtEngineOther, comparatorAtNoEngine;
    private int comparatorAtAttachedStream, comparatorAtNoAttachedStream;
    private int comparatorClearedAttachSameTrio, comparatorClearedAttachDifferentStream;
    private int comparatorClearedAttachDifferentHolder, comparatorClearedAttachUnscoped;
    private int engineComparatorType1State2ReadTrue, engineComparatorType1State2ReadFalse;
    private int engineComparatorType1State2ReadTrueMinus4, engineComparatorType1State2ReadFalseMinus4;
    private int engineRendererType1, engineRendererTypeOther;
    private int engineType1State2, engineType1StateOther, engineTypeStateUnavailable;
    private int engineAudioState2Minus4, engineAudioState2Minus5;
    private int engineAudioState2Minus3, engineAudioState2Other;
    // NAV25: the original RF2 buffer's inherited EOS flag, never payload.
    // Non-EOS is a read-buffer witness only, NOT audible PCM or track identity.
    private int engineAudioState2BufferNonEos, engineAudioState2BufferEos;
    private int engineAudioState2BufferUnavailable;
    private int secondaryCallerEnters, secondaryCallerStreamMatches, secondaryCallerStreamDiffers;
    private int unscopedSecondaryMatches, unscopedOutsideSecondary, unscopedSecondaryDiffers;
    private int scopeEnters, pairedAttaches, unknownAttaches, attachConflicts;
    private int readSame, readDifferent, readUnknown, detachCount;
    private int unscopedReadSame, unscopedReadDifferent;
    // Return code of original b.g(), only after a matching attached stream
    // remains present across the call. -4 can also be EOS; never claim audible PCM.
    private int returnMinus4,returnMinus5,returnMinus3,returnOther,returnUnlinked;
    // Separate real queue-holder-scoped returns from weaker unscoped aliases.
    // NAV20 aggregated these, so its MANY(-4) could all be unscoped.
    private int strongMinus4,strongMinus5,strongMinus3,strongOther;
    private int weakMinus4,weakMinus5,weakMinus3,weakOther;
    private int totalReadObservations;
    private int readSamplesRemaining = 8;
    private boolean poisoned;

    Scope enter(Object renderer,Object holder) {
        Scope frame=new Scope(renderer,holder,inAttach.get());
        inAttach.set(frame);
        synchronized(this) { scopeEnters=inc(scopeEnters); }
        return frame;
    }
    void exit(Scope scope) {
        Scope active=inAttach.get();
        if (active==scope) {
            if (scope.parent==null) inAttach.remove();
            else inAttach.set(scope.parent);
        } else {
            // Fail closed. Never let an incomplete scope attest identity.
            inAttach.remove();
            synchronized(this) { poisoned=true; }
        }
    }

    CallerFrame enterSecondaryCaller(Object renderer,Object stream) {
        CallerFrame frame=new CallerFrame(renderer,stream,inSecondaryCaller.get());
        inSecondaryCaller.set(frame);
        synchronized(this) { secondaryCallerEnters=inc(secondaryCallerEnters); }
        return frame;
    }

    void exitSecondaryCaller(CallerFrame frame) {
        CallerFrame active=inSecondaryCaller.get();
        if(active==frame) {
            if(frame.parent==null) inSecondaryCaller.remove();
            else inSecondaryCaller.set(frame.parent);
        } else {
            // Never allow broken nested callsite lifetimes to attest identity.
            inSecondaryCaller.remove();
            synchronized(this) { poisoned=true; }
        }
    }

    /**
     * A version-locked, one-time reflection handle to the Lxh6.[LR29 field.
     * Caller verifies its exact declared type and uniqueness before install.
     * No stream contents or private member values are serialized.
     */
    TrackPlayerScope enterTrackPlayerSource(Object wrapper) {
        TrackPlayerScope frame=new TrackPlayerScope(wrapper,inPlayerTrack.get());
        inPlayerTrack.set(frame);
        synchronized(this) {
            if(wrapper!=null)trackPlayerScopeEnter=inc(trackPlayerScopeEnter);
        }
        return frame;
    }

    void exitTrackPlayerSource(TrackPlayerScope frame) {
        TrackPlayerScope active=inPlayerTrack.get();
        if(active==frame) {
            if(frame.parent==null)inPlayerTrack.remove();
            else inPlayerTrack.set(frame.parent);
        } else {
            inPlayerTrack.remove();
            synchronized(this) { poisoned=true; }
        }
    }

    synchronized void onNativePlayerSourceSetter(Object source) {
        TrackPlayerScope scope=inPlayerTrack.get();
        if(poisoned || source==null)return;
        if(scope==null || scope.wrapper==null) {
            playerSourceUnscoped=inc(playerSourceUnscoped);
            return;
        }
        playerSourceSameScope=inc(playerSourceSameScope);
        for(int i=playerSources.size()-1;i>=0;i--) {
            PlayerSourceLink prior=playerSources.get(i);
            Object oldSource=prior.source.get(),oldWrapper=prior.wrapper.get();
            if(oldSource==null || oldWrapper==null) {
                playerSources.remove(i);
                continue;
            }
            if(oldSource==source) {
                if(oldWrapper!=scope.wrapper) {
                    prior.conflicted=true;
                    playerSourceConflict=inc(playerSourceConflict);
                }
                return;
            }
        }
        if(playerSources.size()>=MAX_HANDLES)playerSources.remove(0);
        playerSources.add(new PlayerSourceLink(scope.wrapper,source));
    }

    NativePeriodAdapterScope enterNativePeriodAdapter(Object owner) {
        NativePeriodAdapterScope frame=new NativePeriodAdapterScope(owner,inPeriodAdapter.get());
        inPeriodAdapter.set(frame);
        synchronized(this) {
            if(owner!=null)periodAdapterScopeEnter=inc(periodAdapterScopeEnter);
        }
        return frame;
    }

    void exitNativePeriodAdapter(NativePeriodAdapterScope frame) {
        NativePeriodAdapterScope current=inPeriodAdapter.get();
        if(current==frame) {
            if(frame.parent==null)inPeriodAdapter.remove();
            else inPeriodAdapter.set(frame.parent);
        } else {
            inPeriodAdapter.remove();
            synchronized(this) { poisoned=true; }
        }
    }

    synchronized void onNativePeriodFactoryResult(Object owner,Object originalPeriod) {
        NativePeriodAdapterScope frame=inPeriodAdapter.get();
        if(frame==null || frame.owner==null || frame.owner!=owner
                || originalPeriod==null || exactPeriodClass==null
                || !exactPeriodClass.isInstance(originalPeriod)
                || poisoned || periodFactoryHook<=0)return;
        periodFactoryInScope=inc(periodFactoryInScope);
        if(frame.factoryPeriod!=null) {
            frame.ambiguous=true;
            periodFactoryConflict=inc(periodFactoryConflict);
        } else frame.factoryPeriod=originalPeriod;
    }

    synchronized void onNativePeriodAdapterReturn(
            NativePeriodAdapterScope frame,Object originalReturn) {
        if(frame==null || inPeriodAdapter.get()!=frame
                || periodAdapterHook<=0 || periodFactoryHook<=0
                || poisoned || frame.ambiguous || frame.factoryPeriod==null
                || originalReturn==null || exactPeriodClass==null)return;
        // Temporal same-frame factory / adapter calls alone do NOT establish
        // an alias. Reject unrelated factory results and prefetch. Require
        // direct Java == OR exact previously signer-verified Lup1 stored
        // Lwh6 field == that original factory period; no type guessing.
        boolean exactAlias=originalReturn==frame.factoryPeriod;
        if(!exactAlias && exactWrapperClass!=null
                && exactWrapperClass.isInstance(originalReturn)
                && wrapperPeriodField!=null) {
            try {
                exactAlias=wrapperPeriodField.get(originalReturn)==frame.factoryPeriod;
            } catch(Throwable ignored) { exactAlias=false; }
        }
        if(!exactAlias)return;
        for(int i=periodAdapters.size()-1;i>=0;i--) {
            NativePeriodAdapterLink old=periodAdapters.get(i);
            Object ret=old.returnedPeriod.get(),inner=old.exactLo96.get();
            if(ret==null || inner==null) { periodAdapters.remove(i); continue; }
            if(ret==originalReturn) {
                if(inner!=frame.factoryPeriod) {
                    frame.ambiguous=true;
                    periodFactoryConflict=inc(periodFactoryConflict);
                    periodAdapters.remove(i);
                }
                return;
            }
        }
        if(periodAdapters.size()>=MAX_HANDLES)periodAdapters.remove(0);
        periodAdapters.add(new NativePeriodAdapterLink(
            originalReturn,frame.factoryPeriod));
        periodAdapterLinkCreated=inc(periodAdapterLinkCreated);
    }

    synchronized void setExactActivePeriodFields(Field holderWrapper,Field wrapperPeriod,
            Field periodSource,Class<?> wrapperClass,Class<?> periodClass,
            Class<?> sourceClass) {
        if(holderWrapper==null || wrapperPeriod==null || periodSource==null
                || wrapperClass==null || periodClass==null || sourceClass==null
                || holderWrapper.getType()!=Object.class
                || wrapperPeriod.getDeclaringClass()!=wrapperClass
                || !wrapperPeriod.getType().isAssignableFrom(periodClass)
                || periodSource.getDeclaringClass()!=periodClass
                || periodSource.getType()!=sourceClass)
            throw new IllegalArgumentException("Publisher-exact period source fields required");
        holderWrapper.setAccessible(true);
        wrapperPeriod.setAccessible(true);
        periodSource.setAccessible(true);
        holderWrapperField=holderWrapper;
        wrapperPeriodField=wrapperPeriod;
        periodSourceField=periodSource;
        exactWrapperClass=wrapperClass;
        exactPeriodClass=periodClass;
    }

    synchronized void setPublisherMediaPeriodInterface(Class<?> periodInterface) {
        if(periodInterface==null || !periodInterface.isInterface())
            throw new IllegalArgumentException("Publisher MediaPeriod interface required");
        publisherMediaPeriodInterface=periodInterface;
    }

    private void rememberOtherHolderObject(ArrayList<HolderSelectionLink> history,
            Object holder,Object object) {
        if(holder==null || object==null)return;
        for(int i=history.size()-1;i>=0;i--) {
            Object previous=history.get(i).holder.get();
            if(previous==null || previous==holder)history.remove(i);
        }
        if(history.size()>=MAX_HANDLES)history.remove(0);
        history.add(new HolderSelectionLink(holder,object));
    }

    // Strict original holder + Java reference equality ONLY. Multiple audio
    // reads can sample the same link, so these are bounded evidence bins,
    // not counts of selected songs, generations or independently unique links.
    private int otherReferenceRelation(ArrayList<HolderSelectionLink> history,
            Object holder,Object observed) {
        for(int i=history.size()-1;i>=0;i--) {
            HolderSelectionLink previous=history.get(i);
            Object oldHolder=previous.holder.get();
            if(oldHolder==null) {history.remove(i);continue;}
            if(oldHolder!=holder)continue;
            Object oldObject=previous.wrapper.get();
            if(oldObject==null)return 2; // weak lost
            return oldObject==observed?1:-1;
        }
        return 0; // no same-holder history, NEVER a negative identity proof
    }

    private void observeHolderWrapperPhase(Object holder,int phase) {
        // phase 0=exact signed select ENTER, 1=select EXIT,
        // 2=already verified current queue holder at stream ATTACH.
        // Never inspect nested fields unless the private field descriptor
        // was validated against the exact issuer-signed DEX.
        if(holder==null || holderWrapperField==null || exactWrapperClass==null)return;
        int state;
        Object nested=null;
        try {
            nested=holderWrapperField.get(holder);
            state=nested==null?0:exactWrapperClass.isInstance(nested)?1:2;
        } catch(Throwable ignored) { state=3; }
        if(phase==0) {
            if(state==0)selectEnterNull=inc(selectEnterNull);
            else if(state==1)selectEnterExact=inc(selectEnterExact);
            else if(state==2)selectEnterOther=inc(selectEnterOther);
            else selectEnterFail=inc(selectEnterFail);
        } else if(phase==1) {
            if(state==0)selectExitNull=inc(selectExitNull);
            else if(state==1)selectExitExact=inc(selectExitExact);
            else if(state==2)selectExitOther=inc(selectExitOther);
            else selectExitFail=inc(selectExitFail);
        } else if(phase==2) {
            if(state==0)attachPeriodNull=inc(attachPeriodNull);
            else if(state==1)attachPeriodExact=inc(attachPeriodExact);
            else if(state==2)attachPeriodOther=inc(attachPeriodOther);
            else attachPeriodFail=inc(attachPeriodFail);
        }
        if(state==2 && nested!=null && holderSelectHook>0) {
            if(publisherMediaPeriodInterface!=null
                    && publisherMediaPeriodInterface.isInstance(nested)) {
                if(phase==0)otherSelectEnterPeriod=inc(otherSelectEnterPeriod);
                else if(phase==1)otherSelectExitPeriod=inc(otherSelectExitPeriod);
                else if(phase==2)otherAttachPeriod=inc(otherAttachPeriod);
            }
            if(phase==1)rememberOtherHolderObject(otherSelectedLinks,holder,nested);
            else if(phase==2)rememberOtherHolderObject(otherAttachedLinks,holder,nested);
        }
        // A weak earlier exact wrapper is only evidence it WAS present
        // on the same holder at a previous select boundary, not that it
        // is the current media period when the audio renderer reads.
        if((phase==0 || phase==1) && state==1
                && holderSelectHook>0 && nested!=null) {
            for(int i=holderSelectionLinks.size()-1;i>=0;i--) {
                HolderSelectionLink prior=holderSelectionLinks.get(i);
                Object old=prior.holder.get();
                if(old==null || old==holder)holderSelectionLinks.remove(i);
            }
            if(holderSelectionLinks.size()>=MAX_HANDLES)holderSelectionLinks.remove(0);
            holderSelectionLinks.add(new HolderSelectionLink(holder,nested));
        }
    }

    synchronized void onExactHolderSelectPhase(Object holder,boolean after) {
        if(holderSelectHook<=0 || poisoned)return;
        observeHolderWrapperPhase(holder,after?1:0);
    }

    private void observePriorSelectWhenLiveRead(Object holder,Object nested) {
        if(holderSelectHook<=0 || poisoned || holder==null)return;
        for(int i=holderSelectionLinks.size()-1;i>=0;i--) {
            HolderSelectionLink old=holderSelectionLinks.get(i);
            Object priorHolder=old.holder.get(),priorWrapper=old.wrapper.get();
            if(priorHolder==null) {holderSelectionLinks.remove(i);continue;}
            if(priorHolder!=holder)continue;
            if(priorWrapper==null)priorSelectedWeakLost=inc(priorSelectedWeakLost);
            else if(priorWrapper==nested)priorSelectedExactPresent=inc(priorSelectedExactPresent);
            else if(nested==null)priorSelectedExactCleared=inc(priorSelectedExactCleared);
            // Different non-null wrapper is a new generation: no promotion.
            break;
        }
    }

    private ExactOriginalSourceRead observeActivePeriodSource(Object currentHolder) {
        if(livePeriodSourceHook<=0 || currentHolder==null)return null;
        if(holderWrapperField==null || wrapperPeriodField==null
                || periodSourceField==null)return null;
        Object source=null;
        Object exactLateFlowSource=null;
        Object exactLateFlowTrack=null,exactLateFlowAlbum=null;
        try {
            Object nested=holderWrapperField.get(currentHolder);
            observePriorSelectWhenLiveRead(currentHolder,nested);
            if(nested==null) {
                livePeriodHolderNull=inc(livePeriodHolderNull);
                livePeriodHolderMissing=inc(livePeriodHolderMissing);
                livePeriodUnavailable=inc(livePeriodUnavailable);
                return null;
            }
            if(!exactWrapperClass.isInstance(nested)) {
                // NAV32: classify NAV31's non-Lup1 original holder Object
                // without scanning its fields, methods, metadata or media.
                if(publisherMediaPeriodInterface!=null
                        && publisherMediaPeriodInterface.isInstance(nested))
                    otherReadPeriod=inc(otherReadPeriod);
                else otherReadNotPeriod=inc(otherReadNotPeriod);
                if(exactPeriodClass!=null && exactPeriodClass.isInstance(nested))
                    otherReadLo96=inc(otherReadLo96);
                if(exactWrapperClass!=null
                        && exactWrapperClass.getName().equals(nested.getClass().getName()))
                    otherReadSameNameDifferentLoader=inc(otherReadSameNameDifferentLoader);
                int selectRelation=otherReferenceRelation(otherSelectedLinks,currentHolder,nested);
                if(selectRelation==1)otherSelectReadSame=inc(otherSelectReadSame);
                else if(selectRelation==-1)otherSelectReadDifferent=inc(otherSelectReadDifferent);
                else if(selectRelation==2)otherSelectReadWeakLost=inc(otherSelectReadWeakLost);
                else otherSelectReadNoHistory=inc(otherSelectReadNoHistory);
                int attachRelation=otherReferenceRelation(otherAttachedLinks,currentHolder,nested);
                if(attachRelation==1)otherAttachReadSame=inc(otherAttachReadSame);
                else if(attachRelation==-1)otherAttachReadDifferent=inc(otherAttachReadDifferent);
                else if(attachRelation==2)otherAttachReadWeakLost=inc(otherAttachReadWeakLost);
                else otherAttachReadNoHistory=inc(otherAttachReadNoHistory);
                livePeriodHolderOther=inc(livePeriodHolderOther);
                // NAV33: exact direct Lo96 observed across owner select,
                // live attach and started read. Use ONLY signed-pinned Sl6
                // field of that very same original period object.
                if(exactPeriodClass!=null && exactPeriodClass.isInstance(nested)) {
                    livePeriodDirectLo96=inc(livePeriodDirectLo96);
                    source=periodSourceField.get(nested);
                    if(source==null) {
                        directHolderSourceNull=inc(directHolderSourceNull);
                        livePeriodSourceNull=inc(livePeriodSourceNull);
                        livePeriodUnavailable=inc(livePeriodUnavailable);
                        return null;
                    }
                    directHolderSourcePresent=inc(directHolderSourcePresent);
                } else {
                    livePeriodHolderMissing=inc(livePeriodHolderMissing);
                    livePeriodUnavailable=inc(livePeriodUnavailable);
                    return null;
                }
            } else {
            Object observed=wrapperPeriodField.get(nested);
            if(observed==null) {
                livePeriodWrappedMissing=inc(livePeriodWrappedMissing);
                livePeriodUnavailable=inc(livePeriodUnavailable);
                return null;
            }
            Object exactPeriod=observed;
            if(!exactPeriodClass.isInstance(observed)) {
                // NAV29 assumed the underlying Lwh6 always IS Lo96. It
                // need not be; never make an unsafe cast or scan fields.
                livePeriodNonLo96=inc(livePeriodNonLo96);
                exactPeriod=null;
                int hits=0;
                for(NativePeriodAdapterLink link:periodAdapters) {
                    if(link.returnedPeriod.get()!=observed)continue;
                    Object inner=link.exactLo96.get();
                    if(inner!=null && exactPeriodClass.isInstance(inner)) {
                        hits++;
                        exactPeriod=inner;
                    }
                }
                if(hits!=1 || periodAdapterHook<=0 || periodFactoryHook<=0) {
                    periodAdapterUnmapped=inc(periodAdapterUnmapped);
                    livePeriodUnavailable=inc(livePeriodUnavailable);
                    return null;
                }
                periodAdapterMapped=inc(periodAdapterMapped);
            } else livePeriodDirectLo96=inc(livePeriodDirectLo96);
            source=periodSourceField.get(exactPeriod);
            if(source==null) {
                livePeriodSourceNull=inc(livePeriodSourceNull);
                livePeriodUnavailable=inc(livePeriodUnavailable);
                return null;
            }
            } // existing Lup1 wrapper and adapter path unchanged
        } catch(Throwable ignored) {
            livePeriodReflectionFailed=inc(livePeriodReflectionFailed);
            livePeriodUnavailable=inc(livePeriodUnavailable);
            return null;
        }
        livePeriodResolved=inc(livePeriodResolved);
        int matches=0;
        boolean conflicting=false;
        Object uniquelyScopedWrapper=null;
        for(PlayerSourceLink link:playerSources) {
            if(link.source.get()!=source)continue;
            Object wrapper=link.wrapper.get();
            if(link.conflicted || wrapper==null)conflicting=true;
            else {
                matches++;
                uniquelyScopedWrapper=wrapper;
            }
        }
        if(!conflicting && matches==1) {
            livePeriodSourceMatched=inc(livePeriodSourceMatched);
            // No classification if source is unresolved, conflicted, stale,
            // matched to multiple scopes or read from a non-live queue holder.
            if(scopedAlbumEvidence!=null && uniquelyScopedWrapper!=null) {
                int result=0;
                try { result=scopedAlbumEvidence.classify(uniquelyScopedWrapper); }
                catch(Throwable ignored) { result=0; }
                if(result==1)scopedAlbumMatch=inc(scopedAlbumMatch);
                else if(result==-1)scopedAlbumConflict=inc(scopedAlbumConflict);
                else {
                    scopedAlbumNoLink=inc(scopedAlbumNoLink);
                    switch(result) {
                        case 2:
                        case 10:
                        case 11:
                        case 12:
                        case 13:
                        case 14:
                        case 15:
                            scopedReasonWrapperAbsent=inc(scopedReasonWrapperAbsent);
                            switch(result) {
                                case 10:scopedBirthNotInWindow=inc(scopedBirthNotInWindow);break;
                                case 11:scopedBirthNoTrackScope=inc(scopedBirthNoTrackScope);break;
                                case 12:scopedBirthTrackNotInFlow=inc(scopedBirthTrackNotInFlow);break;
                                case 13:scopedBirthFlowNoAlbum=inc(scopedBirthFlowNoAlbum);break;
                                case 14:scopedBirthFlowAlbumButLinkMissing=inc(scopedBirthFlowAlbumButLinkMissing);break;
                                case 15:scopedBirthAmbiguous=inc(scopedBirthAmbiguous);break;
                                default:scopedBirthNotInWindow=inc(scopedBirthNotInWindow);break;
                            }
                            break;
                        case 16:scopedLateFlowAlbumSame=inc(scopedLateFlowAlbumSame);
                            exactLateFlowSource=source;
                            if(exactOriginalTrackAlbumEvidence!=null) {
                                try {
                                    Object[] same=exactOriginalTrackAlbumEvidence.exact(
                                        uniquelyScopedWrapper);
                                    if(same!=null && same.length==2
                                            && same[0]!=null && same[1]!=null) {
                                        exactLateFlowTrack=same[0];
                                        exactLateFlowAlbum=same[1];
                                    }
                                } catch(Throwable ignored) { }
                            }
                            break;
                        case 17:scopedLateFlowAlbumMissing=inc(scopedLateFlowAlbumMissing);break;
                        case 18:scopedLateFlowAlbumDifferent=inc(scopedLateFlowAlbumDifferent);break;
                        case 19:scopedLateFlowReferenceLost=inc(scopedLateFlowReferenceLost);break;
                        case 3:scopedReasonWrapperAmbiguous=inc(scopedReasonWrapperAmbiguous);break;
                        case 4:scopedReasonTrackWeakLost=inc(scopedReasonTrackWeakLost);break;
                        case 5:scopedReasonAlbumUnset=inc(scopedReasonAlbumUnset);break;
                        case 6:scopedReasonAlbumWeakLost=inc(scopedReasonAlbumWeakLost);break;
                        case 7:scopedReasonFlowMissing=inc(scopedReasonFlowMissing);break;
                        case 8:scopedReasonTrackAlbumMissing=inc(scopedReasonTrackAlbumMissing);break;
                        default:scopedReasonUnknown=inc(scopedReasonUnknown);break;
                    }
                }
            }
        } else if(matches==0 && !conflicting)
            livePeriodSourceNoLink=inc(livePeriodSourceNoLink);
        else livePeriodSourceDifferent=inc(livePeriodSourceDifferent);
        return exactLateFlowSource==null ? null :
            new ExactOriginalSourceRead(
                exactLateFlowSource,exactLateFlowTrack,exactLateFlowAlbum);
    }

    synchronized void setLiveQueueSlotFields(Field engineField,Field slotField) {
        if(engineField==null || slotField==null
                || engineField.getType()!=slotField.getDeclaringClass())
            throw new IllegalArgumentException("Exact native engine/queue layout required");
        engineField.setAccessible(true);
        slotField.setAccessible(true);
        engineQueueField=engineField;
        queueSlotBField=slotField;
    }

    // 1 live same identity; -1 available and definitely different; 0
    // unavailable/ambiguous. No toString/equals/value/export ever.
    private int liveQueueSlotMatches(Object engine,Object holder) {
        if(engine==null || holder==null || engineQueueField==null
                || queueSlotBField==null || liveQueueSlotHook<=0)return 0;
        try {
            Object queue=engineQueueField.get(engine);
            if(queue==null)return 0;
            Object selectedSlot=queueSlotBField.get(queue);
            if(selectedSlot==null)return 0;
            return selectedSlot==holder ? 1 : -1;
        } catch(Throwable ignored) { return 0; }
    }

    synchronized void setEngineHolderStreamArrayField(Field field) {
        if(field==null || !field.getType().isArray())
            throw new IllegalArgumentException("Exact holder stream array required");
        engineHolderStreamArrayField=field;
    }

    EngineFrame enterEngine(Object holder) {
        return enterEngine(null,holder); // old read-only JVM fixtures
    }
    EngineFrame enterEngine(Object engine,Object holder) {
        EngineFrame frame=new EngineFrame(engine,holder,inEngineEnable.get());
        inEngineEnable.set(frame);
        synchronized(this) { engineEnters=inc(engineEnters); }
        return frame;
    }

    void exitEngine(EngineFrame frame) {
        EngineFrame active=inEngineEnable.get();
        if(active==frame) {
            if(frame.parent==null) inEngineEnable.remove();
            else inEngineEnable.set(frame.parent);
        } else {
            inEngineEnable.remove();
            synchronized(this) { poisoned=true; }
        }
    }

    // Result: 1 exact object member, -1 safely checked but different,
    // 0 unavailable/ambiguous; never infer membership from call nesting alone.
    private int holderArrayHasStream(Object holder,Object stream) {
        Field field=engineHolderStreamArrayField;
        if(holder==null || stream==null || field==null) return 0;
        try {
            Object array=field.get(holder);
            if(array==null || !array.getClass().isArray())return 0;
            int n=Array.getLength(array);
            if(n>32)return 0;
            for(int i=0;i<n;i++)if(Array.get(array,i)==stream)return 1;
            return -1;
        } catch (Throwable ignored) { return 0; }
    }

    synchronized void onHookRegistration(String kind, boolean ok) {
        int status=ok?1:-1;
        switch(kind) {
            case "QUEUE_SCOPE": queueHook=status; break;
            case "STREAM_ATTACH": attachHook=status; break;
            case "SAMPLE_READ": readHook=status; break;
            case "STREAM_DETACH": detachHook=status; break;
            case "SECONDARY_CALLER": secondaryCallerHook=status; break;
            case "ENGINE_HOLDER_SCOPE": engineScopeHook=status; break;
            case "LIVE_QUEUE_SLOT_B": liveQueueSlotHook=status; break;
            case "PLAYER_PERIOD_AT_AUDIO_READ": currentPeriodAtReadHook=status; break;
            case "CURRENT_MEDIAITEM_SOURCE": selectedItemSourceHook=status; break;
            case "CURRENT_MEDIAITEM_LOGICAL_ID": selectedLogicalIdHook=status; break;
            case "TRACK_PLAYER_SOURCE_SCOPE": trackPlayerScopeHook=status; break;
            case "NATIVE_PLAYER_SOURCE_SETTER": nativeSourceSetterHook=status; break;
            case "LIVE_PERIOD_ORIGINAL_SOURCE": livePeriodSourceHook=status; break;
            case "ORIGINAL_PERIOD_PREPARE": originalPeriodPrepareHook=status; break;
            case "HOLDER_SELECT_PHASE": holderSelectHook=status; break;
            case "NATIVE_PERIOD_ADAPTER": periodAdapterHook=status; break;
            case "NATIVE_PERIOD_FACTORY": periodFactoryHook=status; break;
            case "RENDERER_TYPE_STATE_ACCESS": typeStateAccessHook=status; break;
            case "BUFFER_EOS_ACCESS": bufferEosAccessHook=status; break;
            case "RENDERER_COMPARATOR": rendererComparatorHook=status; break;
            default: throw new IllegalArgumentException("Unrecognized hook kind");
        }
    }

    synchronized void onAttach(Object renderer,Object stream) {
        Scope scope=inAttach.get();
        boolean strongScope=!poisoned && scope!=null && renderer!=null && stream!=null
            && scope.renderer==renderer && scope.holder!=null;
        CallerFrame secondary=inSecondaryCaller.get();
        EngineFrame engine=inEngineEnable.get();
        // Any reattach invalidates the previous engine-to-holder reference.
        // Only a fresh exact membership check may create a new engine link.
        if(renderer!=null) {
            // NAV27: classify any comparator witness still pending *before*
            // the existing attach invalidation. Do not retain it as evidence
            // after this transition, even when identical Java refs reappear.
            for(ComparatorLink previous:comparatorLinks) {
                if(previous.renderer.get()!=renderer)continue;
                Object oldHolder=previous.holder.get();
                Object oldStream=previous.stream.get();
                if(oldHolder==null || oldStream==null)continue;
                if(engine==null || engine.holder==null || secondary==null
                        || secondary.renderer!=renderer || secondary.stream!=stream
                        || holderArrayHasStream(engine.holder,stream)!=1) {
                    comparatorClearedAttachUnscoped=inc(comparatorClearedAttachUnscoped);
                } else if(oldStream!=stream) {
                    comparatorClearedAttachDifferentStream=inc(
                        comparatorClearedAttachDifferentStream);
                } else if(oldHolder!=engine.holder) {
                    comparatorClearedAttachDifferentHolder=inc(
                        comparatorClearedAttachDifferentHolder);
                } else {
                    comparatorClearedAttachSameTrio=inc(
                        comparatorClearedAttachSameTrio);
                }
            }
            removeRenderer(engineHolderLinks,renderer);
            removeLiveQueueRenderer(renderer);
            // A new attachment transition invalidates any earlier comparator
            // outcome for this renderer, even if Java references are reused.
            removeComparatorRenderer(renderer);
        }
        if(!poisoned && engineScopeHook>0 && engine!=null
                && secondary!=null && secondary.renderer==renderer
                && secondary.stream==stream && renderer!=null && stream!=null) {
            int member=holderArrayHasStream(engine.holder,stream);
            if(member==1) {
                engineHolderStreamMatch=inc(engineHolderStreamMatch);
                if(engineHolderLinks.size()>=MAX_HANDLES)engineHolderLinks.remove(0);
                engineHolderLinks.add(new Link(renderer,engine.holder,stream));
                if(liveQueueSlotHook>0) {
                    int live=liveQueueSlotMatches(engine.engine,engine.holder);
                    if(live==1) {
                        queueSlotAttachSame=inc(queueSlotAttachSame);
                        observeHolderWrapperPhase(engine.holder,2);
                        if(liveQueueLinks.size()>=MAX_HANDLES)liveQueueLinks.remove(0);
                        liveQueueLinks.add(new LiveQueueLink(
                            engine.engine,engine.holder,renderer,stream));
                    } else if(live<0) {
                        queueSlotAttachOther=inc(queueSlotAttachOther);
                    } else {
                        queueSlotAttachUnavailable=inc(queueSlotAttachUnavailable);
                    }
                }
            } else if(member<0) {
                engineHolderStreamDifferent=inc(engineHolderStreamDifferent);
            } else {
                engineHolderArrayUnavailable=inc(engineHolderArrayUnavailable);
            }
        }
        // The secondary caller has no queue-holder identity by itself.
        // Its same-reference link tells us which exact attach route ran.
        if(!poisoned && secondary!=null && secondary.renderer==renderer) {
            if(stream!=null && secondary.stream==stream) {
                secondaryCallerStreamMatches=inc(secondaryCallerStreamMatches);
                if(!strongScope) unscopedSecondaryMatches=inc(unscopedSecondaryMatches);
            } else {
                secondaryCallerStreamDiffers=inc(secondaryCallerStreamDiffers);
                if(!strongScope) unscopedSecondaryDiffers=inc(unscopedSecondaryDiffers);
            }
        } else if(!poisoned && !strongScope && secondary==null
                  && secondaryCallerHook>0 && renderer!=null && stream!=null) {
            // With the second caller hook registered, this was outside that
            // observed scope. It is not proof of an unknown third caller.
            unscopedOutsideSecondary=inc(unscopedOutsideSecondary);
        }
        if (!strongScope) {
            unknownAttaches=inc(unknownAttaches);
            // Attaches without an observed queue scope still allow a weaker
            // renderer→stream→read same-reference check, never holder identity.
            if(!poisoned && renderer!=null && stream!=null) {
                removeRenderer(unscopedLinks,renderer);
                removeRenderer(links,renderer);
                if(unscopedLinks.size()>=MAX_HANDLES)unscopedLinks.remove(0);
                unscopedLinks.add(new Link(renderer,null,stream));
                readSamplesRemaining=MAX_READS_PER_ATTACH;
            }
            return;
        }
        removeRenderer(unscopedLinks,renderer);
        for(int i=links.size()-1;i>=0;i--) {
            Link old=links.get(i);
            Object candidate=old.renderer.get();
            if(candidate==null || old.holder.get()==null || old.stream.get()==null) {
                links.remove(i); continue;
            }
            if(candidate==renderer) {
                // Transition and prepare may attach a different stream.
                if(old.holder.get()!=scope.holder || old.stream.get()!=stream)
                    attachConflicts=inc(attachConflicts);
                links.remove(i);
            }
        }
        if (links.size()>=MAX_HANDLES) links.remove(0);
        links.add(new Link(renderer,scope.holder,stream));
        pairedAttaches=inc(pairedAttaches);
        readSamplesRemaining=MAX_READS_PER_ATTACH;
    }

    private static void removeRenderer(ArrayList<Link> list,Object renderer) {
        for(int i=list.size()-1;i>=0;i--) {
            Object existing=list.get(i).renderer.get();
            if(existing==null || existing==renderer)list.remove(i);
        }
    }

    private void removeLiveQueueRenderer(Object renderer) {
        for(int i=liveQueueLinks.size()-1;i>=0;i--) {
            Object existing=liveQueueLinks.get(i).renderer.get();
            if(existing==null || existing==renderer)liveQueueLinks.remove(i);
        }
    }

    private void removeComparatorRenderer(Object renderer) {
        for(int i=comparatorLinks.size()-1;i>=0;i--) {
            Object existing=comparatorLinks.get(i).renderer.get();
            if(existing==null || existing==renderer)comparatorLinks.remove(i);
        }
    }

    synchronized boolean shouldSampleRead() {
        if (poisoned || totalReadObservations>=MAX_HOT_READ_OBSERVATIONS
                || readSamplesRemaining<=0) return false;
        totalReadObservations++;
        readSamplesRemaining--;
        return true;
    }

    synchronized void onRead(Object renderer,Object actualFieldStream) {
        if (poisoned || renderer==null || actualFieldStream==null) {
            readUnknown=inc(readUnknown);
            return;
        }
        Link matched=null;
        for(int i=links.size()-1;i>=0;i--) {
            Link link=links.get(i);
            Object candidate=link.renderer.get();
            if(candidate==null || link.stream.get()==null || link.holder.get()==null) {
                links.remove(i);
            } else if(candidate==renderer) {
                if(matched!=null) { poisoned=true; return; }
                matched=link;
            }
        }
        if(matched==null) {
            // A weaker unscoped match cannot increment QUEUED_HOLDER_ATTACHED
            // or ATTACHED_STREAM_READ_MATCH: holder is not established.
            Link unscoped=null;
            for(int i=unscopedLinks.size()-1;i>=0;i--) {
                Link link=unscopedLinks.get(i);
                Object candidate=link.renderer.get();
                if(candidate==null || link.stream.get()==null) {
                    unscopedLinks.remove(i);
                } else if(candidate==renderer) {
                    if(unscoped!=null) { poisoned=true; return; }
                    unscoped=link;
                }
            }
            if(unscoped==null)readUnknown=inc(readUnknown);
            else if(unscoped.stream.get()==actualFieldStream)
                unscopedReadSame=inc(unscopedReadSame);
            else unscopedReadDifferent=inc(unscopedReadDifferent);
        } else if(matched.stream.get()==actualFieldStream) {
            readSame=inc(readSame);
        } else {
            readDifferent=inc(readDifferent);
        }
    }

    synchronized void onReadReturn(Object renderer,Object observedStream,int originalResult) {
        if (poisoned || renderer==null || observedStream==null) {
            returnUnlinked=inc(returnUnlinked);
            return;
        }
        boolean strong=false,weak=false;
        for (Link link:links) {
            if (link.renderer.get()==renderer && link.holder.get()!=null
                    && link.stream.get()==observedStream) { strong=true; break; }
        }
        if (!strong) for (Link link:unscopedLinks) {
            if (link.renderer.get()==renderer
                    && link.stream.get()==observedStream) { weak=true; break; }
        }
        if(!strong && !weak) {
            returnUnlinked=inc(returnUnlinked);
            return;
        }
        // Engine holder is an independent proof cohort: never elevate it to
        // QUEUE_SCOPED counters or audible PCM. Exact holder-array membership,
        // secondary stream alias, and unchanged renderer stream must all match.
        boolean engineMatch=false;
        for(Link link:engineHolderLinks) {
            if(link.renderer.get()==renderer && link.holder.get()!=null
                    && link.stream.get()==observedStream) {
                engineMatch=true;
                break;
            }
        }
        if(engineMatch) {
            switch(originalResult) {
                case -4:engineReadMinus4=inc(engineReadMinus4);break;
                case -5:engineReadMinus5=inc(engineReadMinus5);break;
                case -3:engineReadMinus3=inc(engineReadMinus3);break;
                default:engineReadOther=inc(engineReadOther);break;
            }
        }
        // Preserve NAV20 aggregate read-return bins, but never use them
        // as proof of a queue-scoped holder. A queued holder is strict only
        // if it remains bound at the exact return point.
        switch(originalResult) {
            case -4:
                returnMinus4=inc(returnMinus4);
                if(strong)strongMinus4=inc(strongMinus4);
                else weakMinus4=inc(weakMinus4);
                break;
            case -5:
                returnMinus5=inc(returnMinus5);
                if(strong)strongMinus5=inc(strongMinus5);
                else weakMinus5=inc(weakMinus5);
                break;
            case -3:
                returnMinus3=inc(returnMinus3);
                if(strong)strongMinus3=inc(strongMinus3);
                else weakMinus3=inc(weakMinus3);
                break;
            default:
                returnOther=inc(returnOther);
                if(strong)strongOther=inc(strongOther);
                else weakOther=inc(weakOther);
                break;
        }
    }

    /**
     * NAV24: READ-ONLY status of the original 2025 b.default()I and
     * b.getState()I after untouched original b.g. Only an already verified
     * matching engine holder/renderer stream may count.
     * Track type 1 and state 2 are *numbers*, not audible output assertions.
     */
    synchronized void onRendererTypeStateRead(Object renderer,Object stream,
            int trackType,int state,int originalResult) {
        onRendererTypeStateRead(renderer,stream,trackType,state,originalResult,null);
    }

    synchronized void onRendererComparatorResult(Object holder,Object renderer,
            Object stream,boolean result) {
        if(poisoned || rendererComparatorHook<=0) {
            rendererComparatorUnavailable=inc(rendererComparatorUnavailable);
            return;
        }
        if(holder==null || renderer==null || stream==null) {
            rendererComparatorUnavailable=inc(rendererComparatorUnavailable);
            return;
        }
        if(result)rendererComparatorTrue=inc(rendererComparatorTrue);
        else rendererComparatorFalse=inc(rendererComparatorFalse);
        // Snapshot strictly from already observed references at this instant.
        // Do not infer method semantics, queue generation, or sound output.
        boolean engineSame=false, engineOther=false;
        for(Link link:engineHolderLinks) {
            if(link.renderer.get()!=renderer)continue;
            if(link.holder.get()==holder && link.stream.get()==stream)
                engineSame=true;
            else if(link.holder.get()!=null && link.stream.get()!=null)
                engineOther=true;
        }
        if(engineSame && !engineOther)
            comparatorAtEngineMatch=inc(comparatorAtEngineMatch);
        else if(engineSame || engineOther)
            comparatorAtEngineOther=inc(comparatorAtEngineOther);
        else comparatorAtNoEngine=inc(comparatorAtNoEngine);
        boolean attached=false;
        for(Link link:links) {
            if(link.renderer.get()==renderer && link.stream.get()==stream) {
                attached=true;
                break;
            }
        }
        if(!attached)for(Link link:unscopedLinks) {
            if(link.renderer.get()==renderer && link.stream.get()==stream) {
                attached=true;
                break;
            }
        }
        if(attached)comparatorAtAttachedStream=inc(comparatorAtAttachedStream);
        else comparatorAtNoAttachedStream=inc(comparatorAtNoAttachedStream);
        for(int i=comparatorLinks.size()-1;i>=0;i--) {
            ComparatorLink old=comparatorLinks.get(i);
            if(old.holder.get()==holder && old.renderer.get()==renderer) {
                comparatorLinks.remove(i);
            }
        }
        if(comparatorLinks.size()>=MAX_HANDLES)comparatorLinks.remove(0);
        comparatorLinks.add(new ComparatorLink(holder,renderer,stream,result));
    }

    synchronized void onRendererComparatorUnavailable() {
        if(!poisoned)rendererComparatorUnavailable=inc(rendererComparatorUnavailable);
    }

    synchronized void onRendererTypeStateRead(Object renderer,Object stream,
            int trackType,int state,int originalResult,Boolean endOfStream) {
        if(poisoned || typeStateAccessHook<=0 || renderer==null || stream==null)return;
        Object matchedHolder=null;
        for(Link link:engineHolderLinks) {
            if(link.renderer.get()==renderer && link.holder.get()!=null
                    && link.stream.get()==stream) {
                matchedHolder=link.holder.get();
                break;
            }
        }
        if(matchedHolder==null)return;
        // A stale engine-only link cannot be counted if the actually sampled
        // original b.g stream no longer matches an attached stream alias.
        boolean attached=false;
        for(Link link:links) {
            if(link.renderer.get()==renderer && link.stream.get()==stream) {
                attached=true;
                break;
            }
        }
        if(!attached)for(Link link:unscopedLinks) {
            if(link.renderer.get()==renderer && link.stream.get()==stream) {
                attached=true;
                break;
            }
        }
        if(!attached)return;
        if(trackType!=1) {
            engineRendererTypeOther=inc(engineRendererTypeOther);
            return;
        }
        engineRendererType1=inc(engineRendererType1);
        if(state!=2) {
            engineType1StateOther=inc(engineType1StateOther);
            return;
        }
        engineType1State2=inc(engineType1State2);
        // NAV28: re-read current live queue slot at original started-audio
        // sample time. A prior match at attach cannot survive changed slot.
        for(LiveQueueLink live:liveQueueLinks) {
            if(live.renderer.get()!=renderer || live.stream.get()!=stream
                    || live.holder.get()!=matchedHolder)continue;
            int fresh=liveQueueSlotMatches(live.engine.get(),live.holder.get());
            if(fresh==1) {
                queueSlotReadSame=inc(queueSlotReadSame);
                if(originalResult==-4)queueSlotReadMinus4=inc(queueSlotReadMinus4);
                // Keep unknown-EOS results segregated from true non-EOS.
                // Snapshot counters before the SAME sampled renderer call,
                // never join two positives from unrelated past tracks.
                int beforeUidInts=periodUnknownEosUidInts;
                int beforeSameRef=periodUnknownEosSame;
                int beforeFlowSame=scopedLateFlowAlbumSame;
                int beforeSourceSame=livePeriodSourceMatched;
                if(originalResult==-4 && !Boolean.TRUE.equals(endOfStream))
                    observeCurrentPlaybackPeriodAtRead(
                        live.engine.get(),live.holder.get(),endOfStream==null);
                // Only independently proven exact holder + live SLOT_B.
                ExactOriginalSourceRead exactLateSource=
                    observeActivePeriodSource(live.holder.get());
                // NAV43 narrow admission *witness*, NOT audio replacement:
                // source+late Flow and PlaybackInfo PeriodID must BOTH have
                // advanced on this exact original -4 renderer callback.
                if(originalResult==-4 && endOfStream==null
                        && (periodUnknownEosUidInts>beforeUidInts
                            || periodUnknownEosSame>beforeSameRef)) {
                    if(scopedLateFlowAlbumSame>beforeFlowSame
                            && livePeriodSourceMatched>beforeSourceSame) {
                        // Retest queue after source classification to reject
                        // playback / Next changes during this callback.
                        if(liveQueueSlotMatches(live.engine.get(),live.holder.get())==1) {
                            jointUnknownEosPeriodFlowSame=inc(jointUnknownEosPeriodFlowSame);
                            // NAV44 strictly read-only Timeline/source MediaItem
                            // comparison, after all NAV43 synchronized guards.
                            // This callback is useful for future pre-decoder
                            // identity resolution; only exact original Track +
                            // Album Java references are delivered. An observer
                            // MUST NOT infer trackId, edition or audible PCM.
                            if(exactLateSource!=null
                                    && exactLateSource.track!=null
                                    && exactLateSource.album!=null
                                    && activeOriginalTrackObserver!=null
                                    && originalPeriodIdStillCurrent(
                                        live.engine.get(),live.holder.get())
                                    && holderStillHasOriginalSource(
                                        live.holder.get(),exactLateSource.source)) {
                                try {
                                    activeOriginalTrackObserver.observe(
                                        exactLateSource.track,exactLateSource.album,
                                        exactLateSource.source);
                                } catch(Throwable ignored) { }
                            }
                            observeSelectedMediaItemSameRead(
                                live.engine.get(),live.holder.get(),
                                exactLateSource==null?null:exactLateSource.source);
                        } else jointUnknownEosPeriodSlotChanged=inc(jointUnknownEosPeriodSlotChanged);
                    } else jointUnknownEosPeriodNoFlow=inc(jointUnknownEosPeriodNoFlow);
                }
            } else if(fresh<0)queueSlotReadOther=inc(queueSlotReadOther);
            else queueSlotReadUnavailable=inc(queueSlotReadUnavailable);
            break;
        }
        // Correlate the exact comparator boolean outcome with this same
        // holder/renderer/attached-stream started-audio read. Do not label
        // TRUE as equality until the signed return semantics are independently
        // confirmed; both outcomes remain visible.
        for(ComparatorLink link:comparatorLinks) {
            if(link.holder.get()==matchedHolder && link.renderer.get()==renderer
                    && link.stream.get()==stream) {
                if(link.result) {
                    engineComparatorType1State2ReadTrue=
                        inc(engineComparatorType1State2ReadTrue);
                    if(originalResult==-4)
                        engineComparatorType1State2ReadTrueMinus4=
                            inc(engineComparatorType1State2ReadTrueMinus4);
                } else {
                    engineComparatorType1State2ReadFalse=
                        inc(engineComparatorType1State2ReadFalse);
                    if(originalResult==-4)
                        engineComparatorType1State2ReadFalseMinus4=
                            inc(engineComparatorType1State2ReadFalseMinus4);
                }
                break;
            }
        }
        if(originalResult==-4) {
            // Only the original buffer flag, after a strict same-reference
            // started audio renderer+holder+stream match. Null means unreadable.
            if(bufferEosAccessHook<=0 || endOfStream==null)
                engineAudioState2BufferUnavailable=inc(engineAudioState2BufferUnavailable);
            else if(endOfStream.booleanValue())engineAudioState2BufferEos=inc(engineAudioState2BufferEos);
            else engineAudioState2BufferNonEos=inc(engineAudioState2BufferNonEos);
        }
        switch(originalResult) {
            case -4:engineAudioState2Minus4=inc(engineAudioState2Minus4);break;
            case -5:engineAudioState2Minus5=inc(engineAudioState2Minus5);break;
            case -3:engineAudioState2Minus3=inc(engineAudioState2Minus3);break;
            default:engineAudioState2Other=inc(engineAudioState2Other);break;
        }
    }

    synchronized void onRendererTypeStateUnavailable(Object renderer,Object stream) {
        if(poisoned || typeStateAccessHook<=0 || renderer==null || stream==null)return;
        for(Link link:engineHolderLinks) {
            if(link.renderer.get()==renderer && link.holder.get()!=null
                    && link.stream.get()==stream) {
                engineTypeStateUnavailable=inc(engineTypeStateUnavailable);
                return;
            }
        }
    }

    synchronized void onDetach(Object renderer) {
        if(renderer==null)return;
        removeRenderer(links,renderer);
        removeRenderer(unscopedLinks,renderer);
        removeRenderer(engineHolderLinks,renderer);
        removeLiveQueueRenderer(renderer);
        removeComparatorRenderer(renderer);
        detachCount=inc(detachCount);
    }

    private static int inc(int value) { return Math.min(MAX_COUNT,value+1); }
    private static String band(int value) {
        if(value==0)return "NONE";
        if(value==1)return "ONE";
        if(value<=8)return "FEW";
        return "MANY";
    }
    private static String registrationLine(String category,int status) {
        return "event=AUDIO_NATIVE_RENDERER_HOOK_STATUS;origin="+category
            +";error="+(status>0?"REGISTERED":status<0?"NO_HOOK":"NOT_SEEN")
            +";thread=OTHER";
    }
    private static String line(String category,int value) {
        return "event=AUDIO_NATIVE_RENDERER_SUMMARY;origin=" + category
            + ";error=" + band(value) + ";thread=OTHER";
    }

    synchronized String[] exportLines() {
        // Only fixed finite enums leave MAIN. No raw objects, names or audio.
        return new String[] {
            registrationLine("QUEUE_SCOPE",queueHook),
            registrationLine("STREAM_ATTACH",attachHook),
            registrationLine("SAMPLE_READ",readHook),
            registrationLine("STREAM_DETACH",detachHook),
            registrationLine("SECONDARY_CALLER",secondaryCallerHook),
            registrationLine("ENGINE_HOLDER_SCOPE",engineScopeHook),
            registrationLine("LIVE_QUEUE_SLOT_B",liveQueueSlotHook),
            registrationLine("PLAYER_PERIOD_AT_AUDIO_READ",currentPeriodAtReadHook),
            registrationLine("CURRENT_MEDIAITEM_SOURCE",selectedItemSourceHook),
            registrationLine("CURRENT_MEDIAITEM_LOGICAL_ID",selectedLogicalIdHook),
            registrationLine("TRACK_PLAYER_SOURCE_SCOPE",trackPlayerScopeHook),
            registrationLine("NATIVE_PLAYER_SOURCE_SETTER",nativeSourceSetterHook),
            registrationLine("LIVE_PERIOD_ORIGINAL_SOURCE",livePeriodSourceHook),
            registrationLine("HOLDER_SELECT_PHASE",holderSelectHook),
            registrationLine("NATIVE_PERIOD_ADAPTER",periodAdapterHook),
            registrationLine("NATIVE_PERIOD_FACTORY",periodFactoryHook),
            registrationLine("RENDERER_TYPE_STATE_ACCESS",typeStateAccessHook),
            registrationLine("BUFFER_EOS_ACCESS",bufferEosAccessHook),
            registrationLine("RENDERER_COMPARATOR",rendererComparatorHook),
            line("RENDERER_COMPARATOR_TRUE",rendererComparatorTrue),
            line("RENDERER_COMPARATOR_FALSE",rendererComparatorFalse),
            line("RENDERER_COMPARATOR_UNAVAILABLE",rendererComparatorUnavailable),
            line("COMPARATOR_AT_CALL_ENGINE_MATCH",comparatorAtEngineMatch),
            line("COMPARATOR_AT_CALL_ENGINE_OTHER",comparatorAtEngineOther),
            line("COMPARATOR_AT_CALL_NO_ENGINE",comparatorAtNoEngine),
            line("COMPARATOR_AT_CALL_ATTACHED_STREAM",comparatorAtAttachedStream),
            line("COMPARATOR_AT_CALL_NO_ATTACHED_STREAM",comparatorAtNoAttachedStream),
            line("COMPARATOR_CLEARED_ATTACH_SAME_TRIO",comparatorClearedAttachSameTrio),
            line("COMPARATOR_CLEARED_ATTACH_DIFFERENT_STREAM",
                comparatorClearedAttachDifferentStream),
            line("COMPARATOR_CLEARED_ATTACH_DIFFERENT_HOLDER",
                comparatorClearedAttachDifferentHolder),
            line("COMPARATOR_CLEARED_ATTACH_UNSCOPED",comparatorClearedAttachUnscoped),
            line("ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE",engineComparatorType1State2ReadTrue),
            line("ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_FALSE",engineComparatorType1State2ReadFalse),
            line("ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE_MINUS4",engineComparatorType1State2ReadTrueMinus4),
            line("ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_FALSE_MINUS4",engineComparatorType1State2ReadFalseMinus4),
            line("QUEUE_SCOPE_ENTER",scopeEnters),
            line("SECONDARY_CALLER_ENTER",secondaryCallerEnters),
            line("ENGINE_HOLDER_SCOPE_ENTER",engineEnters),
            line("ENGINE_HOLDER_STREAM_ARRAY_MATCH",engineHolderStreamMatch),
            line("ENGINE_HOLDER_STREAM_ARRAY_DIFFERENT",engineHolderStreamDifferent),
            line("ENGINE_HOLDER_STREAM_ARRAY_UNAVAILABLE",engineHolderArrayUnavailable),
            line("LIVE_QUEUE_SLOT_B_ATTACH_MATCH",queueSlotAttachSame),
            line("LIVE_QUEUE_SLOT_B_ATTACH_OTHER",queueSlotAttachOther),
            line("LIVE_QUEUE_SLOT_B_ATTACH_UNAVAILABLE",queueSlotAttachUnavailable),
            line("LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH",queueSlotReadSame),
            line("LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_OTHER",queueSlotReadOther),
            line("LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_UNAVAILABLE",queueSlotReadUnavailable),
            line("LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MINUS4",queueSlotReadMinus4),
            line("PLAYER_PERIOD_AT_READ_SAME_REFERENCE",currentPeriodSameReferenceAtRead),
            line("PLAYER_PERIOD_AT_READ_UID_AND_INDEX_MATCH",currentPeriodUidAndIntsAtRead),
            line("PLAYER_PERIOD_AT_READ_UID_ONLY",currentPeriodUidOnlyAtRead),
            line("PLAYER_PERIOD_AT_READ_DIFFERENT",currentPeriodDifferentAtRead),
            line("PLAYER_PERIOD_AT_READ_UNAVAILABLE",currentPeriodUnavailableAtRead),
            line("PLAYER_PERIOD_EOS_UNKNOWN_SAME_REF",periodUnknownEosSame),
            line("PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS",periodUnknownEosUidInts),
            line("PLAYER_PERIOD_EOS_UNKNOWN_UID_ONLY",periodUnknownEosUidOnly),
            line("PLAYER_PERIOD_EOS_UNKNOWN_DIFFERENT",periodUnknownEosDifferent),
            line("PLAYER_PERIOD_EOS_UNKNOWN_UNAVAILABLE",periodUnknownEosUnavailable),
            line("PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK",jointUnknownEosPeriodFlowSame),
            line("PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_NO_LINK",jointUnknownEosPeriodNoFlow),
            line("PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SLOT_CHANGED",jointUnknownEosPeriodSlotChanged),
            line("PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_SAME_REF",selectedItemSame),
            line("PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_DIFFERENT",selectedItemDifferent),
            line("PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_UNAVAILABLE",selectedItemUnavailable),
            line("PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_SLOT_CHANGED",selectedItemSlotChanged),
            line("PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_MATCH",selectedLogicalIdMatch),
            line("PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_DIFFERENT",selectedLogicalIdDifferent),
            line("PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_BLANK",selectedLogicalIdBlank),
            line("PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_UNAVAILABLE",selectedLogicalIdUnavailable),
            line("TRACK_PLAYER_SOURCE_SCOPE_ENTER",trackPlayerScopeEnter),
            line("TRACK_PLAYER_SOURCE_SAME_SCOPE",playerSourceSameScope),
            line("TRACK_PLAYER_SOURCE_UNSCOPED",playerSourceUnscoped),
            line("TRACK_PLAYER_SOURCE_CONFLICT",playerSourceConflict),
            line("LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED",livePeriodResolved),
            line("LIVE_PERIOD_ORIGINAL_SOURCE_UNAVAILABLE",livePeriodUnavailable),
            line("NATIVE_PERIOD_ADAPTER_SCOPE_ENTER",periodAdapterScopeEnter),
            line("NATIVE_PERIOD_FACTORY_IN_SCOPE",periodFactoryInScope),
            line("NATIVE_PERIOD_FACTORY_CONFLICT",periodFactoryConflict),
            line("NATIVE_PERIOD_ADAPTER_LINK_CREATED",periodAdapterLinkCreated),
            line("LIVE_PERIOD_HOLDER_WRAPPER_MISSING",livePeriodHolderMissing),
            line("LIVE_PERIOD_HOLDER_WRAPPER_NULL_AT_READ",livePeriodHolderNull),
            line("LIVE_PERIOD_HOLDER_WRAPPER_OTHER_AT_READ",livePeriodHolderOther),
            line("HOLDER_OTHER_WH6_SELECT_ENTER",otherSelectEnterPeriod),
            line("HOLDER_OTHER_WH6_SELECT_EXIT",otherSelectExitPeriod),
            line("HOLDER_OTHER_WH6_ATTACH",otherAttachPeriod),
            line("HOLDER_OTHER_WH6_AT_READ",otherReadPeriod),
            line("HOLDER_OTHER_NON_WH6_AT_READ",otherReadNotPeriod),
            line("HOLDER_OTHER_LO96_AT_READ",otherReadLo96),
            line("HOLDER_OTHER_UP1_NAME_DIFFERENT_LOADER_AT_READ",otherReadSameNameDifferentLoader),
            line("HOLDER_OTHER_SELECT_SAME_AT_READ",otherSelectReadSame),
            line("HOLDER_OTHER_SELECT_DIFFERENT_AT_READ",otherSelectReadDifferent),
            line("HOLDER_OTHER_SELECT_WEAK_LOST_AT_READ",otherSelectReadWeakLost),
            line("HOLDER_OTHER_SELECT_NO_HISTORY_AT_READ",otherSelectReadNoHistory),
            line("HOLDER_OTHER_ATTACH_SAME_AT_READ",otherAttachReadSame),
            line("HOLDER_OTHER_ATTACH_DIFFERENT_AT_READ",otherAttachReadDifferent),
            line("HOLDER_OTHER_ATTACH_WEAK_LOST_AT_READ",otherAttachReadWeakLost),
            line("HOLDER_OTHER_ATTACH_NO_HISTORY_AT_READ",otherAttachReadNoHistory),
            line("HOLDER_SELECT_ENTER_EXACT",selectEnterExact),
            line("HOLDER_SELECT_ENTER_NULL",selectEnterNull),
            line("HOLDER_SELECT_ENTER_OTHER",selectEnterOther),
            line("HOLDER_SELECT_ENTER_FAILED",selectEnterFail),
            line("HOLDER_SELECT_EXIT_EXACT",selectExitExact),
            line("HOLDER_SELECT_EXIT_NULL",selectExitNull),
            line("HOLDER_SELECT_EXIT_OTHER",selectExitOther),
            line("HOLDER_SELECT_EXIT_FAILED",selectExitFail),
            line("HOLDER_ATTACH_EXACT",attachPeriodExact),
            line("HOLDER_ATTACH_NULL",attachPeriodNull),
            line("HOLDER_ATTACH_OTHER",attachPeriodOther),
            line("HOLDER_ATTACH_FAILED",attachPeriodFail),
            line("LIVE_HOLDER_PRIOR_SELECT_EXACT_CLEARED",priorSelectedExactCleared),
            line("LIVE_HOLDER_PRIOR_SELECT_EXACT_PRESENT",priorSelectedExactPresent),
            line("LIVE_HOLDER_PRIOR_SELECT_WEAK_LOST",priorSelectedWeakLost),
            line("LIVE_PERIOD_WRAPPED_PERIOD_MISSING",livePeriodWrappedMissing),
            line("LIVE_PERIOD_WRAPPED_NON_LO96",livePeriodNonLo96),
            line("LIVE_PERIOD_DIRECT_LO96",livePeriodDirectLo96),
            line("LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_PRESENT",directHolderSourcePresent),
            line("LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_NULL",directHolderSourceNull),
            line("LIVE_PERIOD_ADAPTER_MAPPED",periodAdapterMapped),
            line("LIVE_PERIOD_ADAPTER_UNMAPPED",periodAdapterUnmapped),
            line("LIVE_PERIOD_SOURCE_NULL",livePeriodSourceNull),
            line("LIVE_PERIOD_REFLECTION_FAILED",livePeriodReflectionFailed),
            line("LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH",livePeriodSourceMatched),
            line("LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH",scopedAlbumMatch),
            line("LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_NO_LINK",scopedAlbumNoLink),
            line("LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_WRAPPER_ABSENT",scopedReasonWrapperAbsent),
            line("LIVE_PERIOD_SCOPED_TCA_BIRTH_NOT_IN_WINDOW",scopedBirthNotInWindow),
            line("LIVE_PERIOD_SCOPED_TCA_BIRTH_NO_TRACK_SCOPE",scopedBirthNoTrackScope),
            line("LIVE_PERIOD_SCOPED_TCA_BIRTH_TRACK_NOT_IN_FLOW",scopedBirthTrackNotInFlow),
            line("LIVE_PERIOD_SCOPED_TCA_BIRTH_FLOW_NO_ALBUM",scopedBirthFlowNoAlbum),
            line("LIVE_PERIOD_SCOPED_TCA_BIRTH_FLOW_ALBUM_LINK_MISSING",scopedBirthFlowAlbumButLinkMissing),
            line("LIVE_PERIOD_SCOPED_TCA_BIRTH_DUPLICATE_AMBIGUOUS",scopedBirthAmbiguous),
            line("LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME",scopedLateFlowAlbumSame),
            line("LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_MISSING",scopedLateFlowAlbumMissing),
            line("LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_DIFFERENT",scopedLateFlowAlbumDifferent),
            line("LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_REFERENCE_LOST",scopedLateFlowReferenceLost),
            line("LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_WRAPPER_AMBIGUOUS",scopedReasonWrapperAmbiguous),
            line("LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_TRACK_WEAK_LOST",scopedReasonTrackWeakLost),
            line("LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_ALBUM_UNSET",scopedReasonAlbumUnset),
            line("LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_ALBUM_WEAK_LOST",scopedReasonAlbumWeakLost),
            line("LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_FLOW_MISSING",scopedReasonFlowMissing),
            line("LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_TRACK_ALBUM_MISSING",scopedReasonTrackAlbumMissing),
            line("LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_UNKNOWN",scopedReasonUnknown),
            line("LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_CONFLICT",scopedAlbumConflict),
            line("LIVE_PERIOD_TRACK_WRAPPER_SOURCE_OTHER",livePeriodSourceDifferent),
            line("LIVE_PERIOD_TRACK_WRAPPER_SOURCE_NO_LINK",livePeriodSourceNoLink),
            line("ENGINE_HOLDER_READ_RETURN_MINUS4",engineReadMinus4),
            line("ENGINE_HOLDER_READ_RETURN_MINUS5",engineReadMinus5),
            line("ENGINE_HOLDER_READ_RETURN_MINUS3",engineReadMinus3),
            line("ENGINE_HOLDER_READ_RETURN_OTHER",engineReadOther),
            line("ENGINE_HOLDER_RENDERER_TYPE1",engineRendererType1),
            line("ENGINE_HOLDER_RENDERER_TYPE_OTHER",engineRendererTypeOther),
            line("ENGINE_HOLDER_TYPE1_STATE2",engineType1State2),
            line("ENGINE_HOLDER_TYPE1_STATE_NOT2",engineType1StateOther),
            line("ENGINE_HOLDER_TYPE_STATE_UNAVAILABLE",engineTypeStateUnavailable),
            line("ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4",engineAudioState2Minus4),
            line("ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS5",engineAudioState2Minus5),
            line("ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS3",engineAudioState2Minus3),
            line("ENGINE_AUDIO_TYPE1_STATE2_RETURN_OTHER",engineAudioState2Other),
            line("ENGINE_AUDIO_TYPE1_STATE2_BUFFER_NON_EOS",engineAudioState2BufferNonEos),
            line("ENGINE_AUDIO_TYPE1_STATE2_BUFFER_EOS",engineAudioState2BufferEos),
            line("ENGINE_AUDIO_TYPE1_STATE2_BUFFER_UNAVAILABLE",engineAudioState2BufferUnavailable),
            line("SECONDARY_CALLER_STREAM_MATCH",secondaryCallerStreamMatches),
            line("SECONDARY_CALLER_STREAM_DIFFERENT",secondaryCallerStreamDiffers),
            line("UNSCOPED_ATTACH_SECONDARY_MATCH",unscopedSecondaryMatches),
            line("UNSCOPED_ATTACH_SECONDARY_DIFFERENT",unscopedSecondaryDiffers),
            line("UNSCOPED_ATTACH_OUTSIDE_SECONDARY",unscopedOutsideSecondary),
            line("QUEUED_HOLDER_ATTACHED",pairedAttaches),
            line("UNSCOPED_ATTACH",unknownAttaches),
            line("STREAM_REATTACH_TRANSITION",attachConflicts),
            line("ATTACHED_STREAM_READ_MATCH",readSame),
            line("ATTACHED_STREAM_READ_DIFFERENT",readDifferent),
            line("UNSCOPED_ATTACHED_STREAM_READ_MATCH",unscopedReadSame),
            line("UNSCOPED_ATTACHED_STREAM_READ_DIFFERENT",unscopedReadDifferent),
            line("READ_NO_MATCHED_ATTACHMENT",readUnknown),
            line("STREAM_ALIASED_READ_RETURN_MINUS4",returnMinus4),
            line("STREAM_ALIASED_READ_RETURN_MINUS5",returnMinus5),
            line("STREAM_ALIASED_READ_RETURN_MINUS3",returnMinus3),
            line("STREAM_ALIASED_READ_RETURN_OTHER",returnOther),
            line("READ_RETURN_LINK_LOST",returnUnlinked),
            line("QUEUE_SCOPED_READ_RETURN_MINUS4",strongMinus4),
            line("QUEUE_SCOPED_READ_RETURN_MINUS5",strongMinus5),
            line("QUEUE_SCOPED_READ_RETURN_MINUS3",strongMinus3),
            line("QUEUE_SCOPED_READ_RETURN_OTHER",strongOther),
            line("UNSCOPED_READ_RETURN_MINUS4",weakMinus4),
            line("UNSCOPED_READ_RETURN_MINUS5",weakMinus5),
            line("UNSCOPED_READ_RETURN_MINUS3",weakMinus3),
            line("UNSCOPED_READ_RETURN_OTHER",weakOther),
            line("RENDERER_DETACHED",detachCount),
            "event=AUDIO_NATIVE_RENDERER_SUMMARY;origin=IDENTITY_STATUS;error="
              + (poisoned ? "INVALID" : "STRUCTURAL_ONLY") + ";thread=OTHER"
        };
    }
}
