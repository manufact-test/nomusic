package pro.celikom.a1exitwitness;

import java.lang.ref.WeakReference;
import java.lang.reflect.Array;
import java.lang.reflect.Field;
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
    private final ThreadLocal<TrackPlayerScope> inPlayerTrack=new ThreadLocal<>();
    private final ArrayList<PlayerSourceLink> playerSources=new ArrayList<>();
    private Field holderWrapperField,wrapperPeriodField,periodSourceField;
    private Class<?> exactWrapperClass,exactPeriodClass;
    private int trackPlayerScopeHook,nativeSourceSetterHook,livePeriodSourceHook;
    private int trackPlayerScopeEnter,playerSourceSameScope,playerSourceUnscoped;
    private int playerSourceConflict,livePeriodResolved,livePeriodUnavailable;
    private int livePeriodSourceMatched,livePeriodSourceDifferent,livePeriodSourceNoLink;
    private final ThreadLocal<Scope> inAttach = new ThreadLocal<>();
    private final ThreadLocal<CallerFrame> inSecondaryCaller = new ThreadLocal<>();
    private final ThreadLocal<EngineFrame> inEngineEnable = new ThreadLocal<>();
    private Field engineHolderStreamArrayField;
    private Field engineQueueField,queueSlotBField;
    private final ArrayList<LiveQueueLink> liveQueueLinks=new ArrayList<>();
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

    private void observeActivePeriodSource(Object currentHolder) {
        if(livePeriodSourceHook<=0 || currentHolder==null)return;
        if(holderWrapperField==null || wrapperPeriodField==null
                || periodSourceField==null)return;
        Object source=null;
        try {
            Object nested=holderWrapperField.get(currentHolder);
            if(nested==null || !exactWrapperClass.isInstance(nested)) {
                livePeriodHolderMissing=inc(livePeriodHolderMissing);
                livePeriodUnavailable=inc(livePeriodUnavailable);
                return;
            }
            Object observed=wrapperPeriodField.get(nested);
            if(observed==null) {
                livePeriodWrappedMissing=inc(livePeriodWrappedMissing);
                livePeriodUnavailable=inc(livePeriodUnavailable);
                return;
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
                    return;
                }
                periodAdapterMapped=inc(periodAdapterMapped);
            } else livePeriodDirectLo96=inc(livePeriodDirectLo96);
            source=periodSourceField.get(exactPeriod);
            if(source==null) {
                livePeriodSourceNull=inc(livePeriodSourceNull);
                livePeriodUnavailable=inc(livePeriodUnavailable);
                return;
            }
        } catch(Throwable ignored) {
            livePeriodReflectionFailed=inc(livePeriodReflectionFailed);
            livePeriodUnavailable=inc(livePeriodUnavailable);
            return;
        }
        livePeriodResolved=inc(livePeriodResolved);
        int matches=0;
        boolean conflicting=false;
        for(PlayerSourceLink link:playerSources) {
            if(link.source.get()!=source)continue;
            if(link.conflicted || link.wrapper.get()==null)conflicting=true;
            else matches++;
        }
        if(!conflicting && matches==1)
            livePeriodSourceMatched=inc(livePeriodSourceMatched);
        else if(matches==0 && !conflicting)
            livePeriodSourceNoLink=inc(livePeriodSourceNoLink);
        else livePeriodSourceDifferent=inc(livePeriodSourceDifferent);
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
            case "TRACK_PLAYER_SOURCE_SCOPE": trackPlayerScopeHook=status; break;
            case "NATIVE_PLAYER_SOURCE_SETTER": nativeSourceSetterHook=status; break;
            case "LIVE_PERIOD_ORIGINAL_SOURCE": livePeriodSourceHook=status; break;
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
                // Only on independently proven same holder + live SLOT_B
                // + started audio stream, never on merely prepared periods.
                observeActivePeriodSource(live.holder.get());
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
            registrationLine("TRACK_PLAYER_SOURCE_SCOPE",trackPlayerScopeHook),
            registrationLine("NATIVE_PLAYER_SOURCE_SETTER",nativeSourceSetterHook),
            registrationLine("LIVE_PERIOD_ORIGINAL_SOURCE",livePeriodSourceHook),
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
            line("LIVE_PERIOD_WRAPPED_PERIOD_MISSING",livePeriodWrappedMissing),
            line("LIVE_PERIOD_WRAPPED_NON_LO96",livePeriodNonLo96),
            line("LIVE_PERIOD_DIRECT_LO96",livePeriodDirectLo96),
            line("LIVE_PERIOD_ADAPTER_MAPPED",periodAdapterMapped),
            line("LIVE_PERIOD_ADAPTER_UNMAPPED",periodAdapterUnmapped),
            line("LIVE_PERIOD_SOURCE_NULL",livePeriodSourceNull),
            line("LIVE_PERIOD_REFLECTION_FAILED",livePeriodReflectionFailed),
            line("LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH",livePeriodSourceMatched),
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
