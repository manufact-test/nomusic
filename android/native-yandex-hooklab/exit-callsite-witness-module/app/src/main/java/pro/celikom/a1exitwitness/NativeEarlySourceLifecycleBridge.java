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
        implements NativeRendererStreamEvidence.EarlyOriginalSourceObserver {
    private final NativeReplacementLifecycle lifecycle =
        new NativeReplacementLifecycle(850);
    private final LongSupplier elapsedClock;
    private long latestSetterGeneration = -1;
    private long lifecycleGeneration;
    private boolean originalSetterSucceeded;
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
