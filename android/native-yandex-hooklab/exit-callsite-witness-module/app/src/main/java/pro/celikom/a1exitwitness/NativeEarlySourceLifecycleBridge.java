package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeReplacementLifecycle;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;
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
    private boolean originalPeriodAmbiguous;
    private boolean originalPeriodPrepareSealed;
    private WeakReference<Object> trackRef;
    private WeakReference<Object> albumRef;
    private WeakReference<Object> sourceRef;

    NativeEarlySourceLifecycleBridge() {
        this(() -> System.nanoTime() / 1_000_000L);
    }
    NativeEarlySourceLifecycleBridge(LongSupplier clock) {
        if(clock==null)throw new IllegalArgumentException("CLOCK_REQUIRED");
        elapsedClock=clock;
    }
    private void clear() {
        confirmedCurrentOriginalGeneration=-1;
        originalPeriodPrePrepareGeneration=-1;
        originalPeriodRef=null;
        originalPeriodAmbiguous=false;
        originalPeriodPrepareSealed=false;
        originalSetterSucceeded=false;
        trackRef=null;
        albumRef=null;
        sourceRef=null;
    }

    @Override public synchronized void invalidated(long generation) {
        // Even an unknown original selection supersedes the previous one.
        // No candidate can inherit another track's revision.
        latestSetterGeneration=generation;
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

    @Override public synchronized void beforeOriginalPeriodPrepare(
            long generation,Object track,Object album,Object source,Object period) {
        if(period==null || originalPeriodAmbiguous
                || !isSuccessfulOriginalSource(generation,track,album,source))
            return;
        // At most ONE exact original period for this setter generation.
        // A distinct period (prefetch/retry ambiguity) permanently revokes
        // this generation, even if the first period appears again later.
        if(originalPeriodRef!=null && originalPeriodRef.get()!=period) {
            originalPeriodPrePrepareGeneration=-1;
            originalPeriodRef=null;
            originalPeriodAmbiguous=true;
            return;
        }
        originalPeriodRef=new WeakReference<>(period);
        originalPeriodPrePrepareGeneration=generation;
        // This IS the publisher's original prepare boundary, not a late
        // renderer read. When no independently verified descriptor IDs
        // and approved source exist, commit ORIGINAL for this generation
        // before the publisher prepare proceeds. Late ID/grant replies may
        // never upgrade the already prepared original player source.
        if(!originalPeriodPrepareSealed) {
            originalPeriodPrepareSealed=true;
            lifecycle.atNativePrepare(lifecycleGeneration,
                null,null,null,elapsedClock.getAsLong());
        }
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
