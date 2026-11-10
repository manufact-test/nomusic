package pro.celikom.yandex.nativehooklab;

/**
 * Pure-Java source INSTANCE causality model for an OWNED, future test host.
 *
 * IMPORTANT: No Yandex hook is wired to this class. It cannot determine the
 * active track, edition, generation from Yandex, decoder prepare or audio.
 * Event calls MUST originate from independently verified trusted boundaries.
 * Accepting a synthetic event sequence is NOT permission to substitute audio.
 *
 * Exact Object reference identity is deliberate: Object.equals/hashCode and
 * media metadata cannot prove that two callbacks belong to the SAME source.
 * Only one active epoch is retained; old epochs have no access to new sources.
 * All inspection is in-memory, count-only; no URL, track, edition, or audio.
 */
public final class NativeSourceInstanceFence {
    public enum Verdict {
        RECORDED, STALE, OUT_OF_ORDER, IDENTITY_CONFLICT,
        ALREADY_SEALED, CLOCK_INVALID, UNKNOWN_SOURCE
    }
    public enum Phase {
        IDLE, SELECTED, SOURCE_BOUND, BEFORE_PREPARE, TASK_QUEUED,
        TASK_RUNNING, OPEN, READING, CLOSED, INVALIDATED
    }
    public static final class Snapshot {
        public final Phase phase;
        public final long generation;
        public final int prepareCount, openCount, readCount, closeCount,
                seekCount, rejectedCount;
        /** Only a synthetic observation; NEVER a runtime audio/PASS verdict. */
        public final boolean syntheticSequenceComplete;
        Snapshot(Phase phase,long generation,int prepareCount,int openCount,
                 int readCount,int closeCount,int seekCount,int rejectedCount,
                 boolean complete) {
            this.phase=phase;
            this.generation=generation;
            this.prepareCount=prepareCount;
            this.openCount=openCount;
            this.readCount=readCount;
            this.closeCount=closeCount;
            this.seekCount=seekCount;
            this.rejectedCount=rejectedCount;
            this.syntheticSequenceComplete=complete;
        }
    }
    private long generation;
    private long lastTime=-1;
    private Object selected, owner, source, loader, task, dataSpec;
    private Phase phase=Phase.IDLE;
    private boolean poisoned, everRead, prepared;
    private int prepareCount, openCount, readCount, closeCount, seekCount, rejectedCount;

    /** Start every native selection, including radio and same-track replay. */
    public synchronized long begin(Object selectedSource,long elapsedMs) {
        if (generation==Long.MAX_VALUE)
            throw new IllegalStateException("GENERATION_OVERFLOW_FAIL_CLOSED");
        generation++;
        clearHandles();
        prepareCount=openCount=readCount=closeCount=seekCount=rejectedCount=0;
        poisoned=false;
        everRead=false;
        prepared=false;
        lastTime=elapsedMs>=0?elapsedMs:-1;
        phase=selectedSource!=null && elapsedMs>=0
                ?Phase.SELECTED:Phase.INVALIDATED;
        selected=phase==Phase.SELECTED?selectedSource:null;
        return generation;
    }

    /**
     * Trusted factory witness: selected media-source instance to Lero-like
     * owner and source-reader object. No Yandex class names are required.
     */
    public synchronized Verdict sourceBound(long epoch,Object selection,
                                            Object sourceOwner,Object reader,long at) {
        Verdict v=precheck(epoch,at);
        if (v!=Verdict.RECORDED)return v;
        if (phase!=Phase.SELECTED)return reject(Verdict.OUT_OF_ORDER);
        if (selection!=selected)return poison();
        if (sourceOwner==null||reader==null)return reject(Verdict.UNKNOWN_SOURCE);
        owner=sourceOwner;
        source=reader;
        phase=Phase.SOURCE_BOUND;
        return Verdict.RECORDED;
    }

    /**
     * This is NOT the real decoder prepare hook. In a future authorized host
     * the caller must first prove this is the selected decoder descriptor.
     */
    public synchronized Verdict descriptorBeforePrepare(long epoch,Object selection,
                                                          Object sourceOwner,Object reader,
                                                          long at) {
        Verdict v=precheck(epoch,at);
        if (v!=Verdict.RECORDED)return v;
        if (phase!=Phase.SOURCE_BOUND)return reject(Verdict.OUT_OF_ORDER);
        if (selection!=selected||sourceOwner!=owner||reader!=source)return poison();
        prepared=true;
        prepareCount++;
        phase=Phase.BEFORE_PREPARE;
        return Verdict.RECORDED;
    }

    /** A scheduled Runnable must be attached to the same exact owner. */
    public synchronized Verdict scheduled(long epoch,Object sourceOwner,
                                           Object loaderObject,Object taskObject,long at) {
        Verdict v=precheck(epoch,at);
        if (v!=Verdict.RECORDED)return v;
        if (phase!=Phase.BEFORE_PREPARE)return reject(Verdict.OUT_OF_ORDER);
        if (sourceOwner!=owner)return poison();
        if (loaderObject==null||taskObject==null)return reject(Verdict.UNKNOWN_SOURCE);
        loader=loaderObject;
        task=taskObject;
        phase=Phase.TASK_QUEUED;
        return Verdict.RECORDED;
    }

    public synchronized Verdict dispatched(long epoch,Object sourceOwner,
                                            Object loaderObject,Object taskObject,long at) {
        Verdict v=precheck(epoch,at);
        if (v!=Verdict.RECORDED)return v;
        if (phase!=Phase.TASK_QUEUED)return reject(Verdict.OUT_OF_ORDER);
        if (sourceOwner!=owner||loaderObject!=loader||taskObject!=task)return poison();
        phase=Phase.TASK_RUNNING;
        return Verdict.RECORDED;
    }

    /** Exact reader instance and DataSpec object; never inspect the URI. */
    public synchronized Verdict opened(long epoch,Object loaderObject,
                                        Object reader,Object spec,long at) {
        Verdict v=precheck(epoch,at);
        if (v!=Verdict.RECORDED)return v;
        if (phase!=Phase.TASK_RUNNING && phase!=Phase.CLOSED)
            return reject(Verdict.OUT_OF_ORDER);
        if (loaderObject!=loader||reader!=source)return poison();
        if (spec==null)return reject(Verdict.UNKNOWN_SOURCE);
        if (phase==Phase.CLOSED&&!seekWasRequested)
            return reject(Verdict.OUT_OF_ORDER);
        dataSpec=spec;
        seekWasRequested=false;
        phase=Phase.OPEN;
        openCount++;
        return Verdict.RECORDED;
    }

    public synchronized Verdict read(long epoch,Object loaderObject,
                                     Object reader,Object spec,int bytes,long at) {
        Verdict v=precheck(epoch,at);
        if (v!=Verdict.RECORDED)return v;
        if (phase!=Phase.OPEN && phase!=Phase.READING)
            return reject(Verdict.OUT_OF_ORDER);
        if (loaderObject!=loader||reader!=source||spec!=dataSpec)return poison();
        if (bytes<0)return reject(Verdict.OUT_OF_ORDER);
        if (bytes>0) {
            everRead=true;
            readCount++;
        }
        phase=Phase.READING;
        return Verdict.RECORDED;
    }

    /** Seek is not a new source commit. A subsequent open needs same objects. */
    public synchronized Verdict seek(long epoch,Object sourceOwner,long at) {
        Verdict v=precheck(epoch,at);
        if (v!=Verdict.RECORDED)return v;
        if (!prepared || sourceOwner!=owner)return poison();
        if (phase!=Phase.OPEN&&phase!=Phase.READING&&phase!=Phase.CLOSED)
            return reject(Verdict.OUT_OF_ORDER);
        seekCount++;
        seekWasRequested=true;
        return Verdict.RECORDED;
    }

    public synchronized Verdict closed(long epoch,Object loaderObject,
                                       Object reader,long at) {
        Verdict v=precheck(epoch,at);
        if (v!=Verdict.RECORDED)return v;
        if (phase!=Phase.OPEN&&phase!=Phase.READING)
            return reject(Verdict.OUT_OF_ORDER);
        if (loaderObject!=loader||reader!=source)return poison();
        dataSpec=null;
        closeCount++;
        phase=Phase.CLOSED;
        return Verdict.RECORDED;
    }

    /** Stop / Next: irrevocably drop all object references for this epoch. */
    public synchronized void abort(long epoch) {
        if (epoch!=generation)return;
        clearHandles();
        phase=Phase.INVALIDATED;
        poisoned=true;
    }

    public synchronized Snapshot snapshot() {
        return new Snapshot(phase,generation,prepareCount,openCount,readCount,
                closeCount,seekCount,rejectedCount,
                !poisoned&&phase==Phase.CLOSED&&prepareCount==1
                        &&openCount>=1&&closeCount>=1&&everRead);
    }

    private boolean seekWasRequested;
    private void clearHandles() {
        selected=owner=source=loader=task=dataSpec=null;
        seekWasRequested=false;
    }
    private Verdict precheck(long epoch,long at) {
        if (epoch!=generation)return Verdict.STALE;
        if (phase==Phase.INVALIDATED||phase==Phase.IDLE)
            return Verdict.ALREADY_SEALED;
        if (poisoned)return Verdict.IDENTITY_CONFLICT;
        if (at<0||lastTime<0||at<lastTime) {
            poisoned=true;
            clearHandles();
            phase=Phase.INVALIDATED;
            rejectedCount++;
            return Verdict.CLOCK_INVALID;
        }
        lastTime=at;
        return Verdict.RECORDED;
    }
    private Verdict reject(Verdict verdict) {
        rejectedCount++;
        return verdict;
    }
    private Verdict poison() {
        poisoned=true;
        clearHandles();
        phase=Phase.INVALIDATED;
        rejectedCount++;
        return Verdict.IDENTITY_CONFLICT;
    }
}
