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
    }
    private final ArrayList<WeakReference<Object>> nativeTrackFlowItems = new ArrayList<>();
    private final ArrayList<NativeTrackSourceLink> nativeTrackSourceLinks = new ArrayList<>();
    private final ThreadLocal<ArrayList<WeakReference<Object>>> activeTrackScopes = new ThreadLocal<>();
    private final ThreadLocal<ArrayList<WeakReference<Object>>> activeWrapperScopes = new ThreadLocal<>();
    private final AtomicLong nativeTrackFlowEmits = new AtomicLong();
    private final AtomicLong nativeTrackSourceRequests = new AtomicLong();
    private final AtomicLong flowTrackSourceSameObject = new AtomicLong();
    private final AtomicLong nativeTrackWrapperLinks = new AtomicLong();
    private final AtomicLong wrapperMainSourceRequests = new AtomicLong();
    private final AtomicLong wrapperDescriptorLinks = new AtomicLong();
    private final AtomicLong trackDescriptorFactoryLinks = new AtomicLong();
    private final AtomicLong trackFactorySourceLinks = new AtomicLong();
    private final AtomicLong trackSourceOpenLinks = new AtomicLong();
    private final AtomicLong trackSourceReadLinks = new AtomicLong();
    private final AtomicLong trackSourceReadProbeBudget = new AtomicLong();

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
        if (value == null) return;
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
        if (stack == null) return null;
        while (!stack.isEmpty()) {
            Object value = stack.get(stack.size()-1).get();
            if (value != null) return value;
            stack.remove(stack.size()-1);
        }
        local.remove();
        return null;
    }

    private static void popScope(
            ThreadLocal<ArrayList<WeakReference<Object>>> local) {
        ArrayList<WeakReference<Object>> stack = local.get();
        if (stack == null) return;
        if (!stack.isEmpty()) stack.remove(stack.size()-1);
        if (stack.isEmpty()) local.remove();
    }

    synchronized void onNativeTrackFlowEmission(Object track) {
        if (track == null) return;
        mark(nativeTrackFlowEmits);
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

    void enterNativeTrackSourceRequest(Object track) {
        if (track == null) return;
        pushScope(activeTrackScopes,track);
        mark(nativeTrackSourceRequests);
        if (wasNativeTrackFlowItem(track)) mark(flowTrackSourceSameObject);
    }

    void exitNativeTrackSourceRequest() {
        popScope(activeTrackScopes);
    }

    synchronized void onNativeTrackWrapperCreated(Object wrapper) {
        Object track=currentScope(activeTrackScopes);
        if (track==null || wrapper==null || !wasNativeTrackFlowItem(track)) return;
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
        link.wrapper=new WeakReference<>(wrapper);
        mark(nativeTrackWrapperLinks);
    }

    void enterNativeMainSourceRequest(Object wrapper) {
        if (wrapper==null) return;
        pushScope(activeWrapperScopes,wrapper);
        if (hasWrapperLink(wrapper)) mark(wrapperMainSourceRequests);
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
            mark(wrapperDescriptorLinks);
        }
    }

    private NativeTrackSourceLink findByWrapper(Object wrapper) {
        if (wrapper==null) return null;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink link=nativeTrackSourceLinks.get(i);
            if (link.track==null || link.track.get()==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if (link.wrapper!=null && link.wrapper.get()==wrapper) return link;
        }
        return null;
    }

    private NativeTrackSourceLink findByDescriptor(Object descriptor) {
        if (descriptor==null) return null;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink link=nativeTrackSourceLinks.get(i);
            if (link.track==null || link.track.get()==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if (link.descriptor!=null && link.descriptor.get()==descriptor) return link;
        }
        return null;
    }

    private NativeTrackSourceLink findByFactory(Object factory) {
        if (factory==null) return null;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink link=nativeTrackSourceLinks.get(i);
            if (link.track==null || link.track.get()==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if (link.factoryResult!=null && link.factoryResult.get()==factory) return link;
        }
        return null;
    }

    private NativeTrackSourceLink findBySource(Object source) {
        if (source==null) return null;
        for (int i=nativeTrackSourceLinks.size()-1;i>=0;i--) {
            NativeTrackSourceLink link=nativeTrackSourceLinks.get(i);
            if (link.track==null || link.track.get()==null) {
                nativeTrackSourceLinks.remove(i);
                continue;
            }
            if (link.sourceInstance!=null && link.sourceInstance.get()==source) return link;
        }
        return null;
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
            mark(trackFactorySourceLinks);
        }
    }

    private synchronized boolean sameExoSource(Object source) {
        if (source == null) return false;
        for (WeakReference<Object> item:exoSourceInstances)
            if (item.get()==source) return true;
        return false;
    }

    void onExoSourceInstanceOpen(Object source) {
        if (sameExoSource(source)) mark(exoSourceInstancesOpened);
        synchronized(this) {
            if (findBySource(source)!=null) mark(trackSourceOpenLinks);
        }
    }

    void onExoSourceInstanceRead(Object source,int count) {
        // At most the first 16 nonzero reads inspect a bounded weak list.
        // Subsequent readAt hot-path callbacks do not scan objects or log.
        if (count > 0 && firstAtMost(exoSourceReadProbeBudget,16)
                && sameExoSource(source))
            mark(exoSourceInstancesRead);
        if (count > 0 && trackSourceReadProbeBudget.get()<16) {
            synchronized(this) {
                if (findBySource(source)!=null
                        && firstAtMost(trackSourceReadProbeBudget,16))
                    mark(trackSourceReadLinks);
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
            "event=AUDIO_STAGE_B_STATUS;origin=CELIKOM_REPLACEMENT;error=NOT_CONNECTED;thread=OTHER"
        };
    }
}
