package pro.celikom.yandex.nativehooklab;

/**
 * Bounded, nonmutating source reference witness for the pinned signed host.
 *
 * A successful Lero.t() may schedule an asynchronous Lmb4 reader. The
 * previous version incorrectly promoted the source as 'started' BEFORE
 * calling the real t(); a throwing t() could therefore manufacture a
 * false-positive factory -> t -> reader chain.
 *
 * Now a t() is a transaction: BEGIN can bind one reader but all evidence
 * remains PENDING until the unmodified original t() returns successfully.
 * Early worker completion before t() returns is deferred, and discarded on
 * failure. Ambiguous overlapping t() calls invalidate that source.
 *
 * No selected player/decoder/track/edition evidence, URL, buffer, token or
 * metadata is ever observed; no audio is replaced.
 */
public final class NativeSourceDispatchWitness {
    private static final String[] TYPES={
            "alt","chg","ero","ocv","ojz","t67","t6f","xq7"
    };
    private static final long WINDOW_MS=15000L;
    private static final int LIMIT=16;
    private final Object[] objects=new Object[LIMIT];
    private final Object[] readers=new Object[LIMIT];
    private final boolean[] constructed=new boolean[LIMIT];
    private final boolean[] factoryReturned=new boolean[LIMIT];
    private final boolean[] started=new boolean[LIMIT];
    private final boolean[] tInFlight=new boolean[LIMIT];
    private final int[] pendingReaders=new int[LIMIT];
    private final long[] storedAt=new long[LIMIT];
    private int next;
    private int factories,lifecycleCalls,matchedCalls,unmatchedCalls,removals;
    private int rejectedUnknown,clockDiscontinuities;
    private int sourceReaderLinks,completedReaderChains,unmatchedReaders;
    private int constructors,constructedTCalls,factoryTCalls;
    private int failedTCalls,ambiguousTCalls,pendingReadersDiscarded;

    private int type(Object obj){
        if(obj==null)return -1;
        String name=obj.getClass().getName();
        for(int i=0;i<TYPES.length;i++)if(TYPES[i].equals(name))return i;
        return -1;
    }
    private void clear(int i){
        pendingReadersDiscarded+=pendingReaders[i];
        pendingReaders[i]=0;
        objects[i]=null;
        readers[i]=null;
        constructed[i]=false;
        factoryReturned[i]=false;
        started[i]=false;
        tInFlight[i]=false;
        storedAt[i]=0;
    }
    private void expire(long now){
        for(int i=0;i<LIMIT;i++){
            if(objects[i]!=null
                    &&(now<storedAt[i]||now-storedAt[i]>WINDOW_MS)){
                if(now<storedAt[i])clockDiscontinuities++;
                clear(i);
            }
        }
    }
    private int remember(Object obj,long now){
        for(int i=0;i<LIMIT;i++){
            if(objects[i]==obj){
                storedAt[i]=now;
                return i;
            }
        }
        int i=next;
        clear(i);
        objects[i]=obj;
        storedAt[i]=now;
        next=(next+1)%LIMIT;
        return i;
    }
    public synchronized void onFactory(Object returned,long now){
        if(now<0||type(returned)<0){rejectedUnknown++;return;}
        expire(now);
        int i=remember(returned,now);
        factoryReturned[i]=true;
        factories++;
    }
    public synchronized void onConstructed(Object source,long now){
        if(now<0||source==null
                ||!"ero".equals(source.getClass().getName())){
            rejectedUnknown++;
            return;
        }
        expire(now);
        int i=remember(source,now);
        if(!constructed[i])constructors++;
        constructed[i]=true;
    }

    /** A pre-invocation witness is provisional, never a successful t(). */
    public synchronized void onLifecycleTBegin(Object receiver,long now){
        if(now<0||type(receiver)<0){rejectedUnknown++;return;}
        expire(now);
        lifecycleCalls++;
        for(int i=0;i<LIMIT;i++){
            if(objects[i]!=receiver)continue;
            if(tInFlight[i]){
                ambiguousTCalls++;
                unmatchedCalls++;
                clear(i);
                return;
            }
            if(started[i]){
                // Repeated t() does not create new trusted source evidence.
                matchedCalls++;
                return;
            }
            tInFlight[i]=true;
            return;
        }
        unmatchedCalls++;
    }

    /**
     * Called only AFTER the original t() returns, or in catch if it throws.
     * A reader could complete on another thread before successful t return.
     */
    public synchronized boolean onLifecycleTFinish(Object receiver,
                                                   boolean returnedNormally,long now){
        // BEGIN has already classified/rejected the receiver. FINISH
        // must not double-count an untrusted receiver or admit one.
        if(now<0||type(receiver)<0)return false;
        expire(now);
        for(int i=0;i<LIMIT;i++){
            if(objects[i]!=receiver||!tInFlight[i])continue;
            if(!returnedNormally){
                failedTCalls++;
                clear(i);
                return false;
            }
            tInFlight[i]=false;
            started[i]=true;
            matchedCalls++;
            if(constructed[i])constructedTCalls++;
            if(factoryReturned[i])factoryTCalls++;
            completedReaderChains+=pendingReaders[i];
            pendingReaders[i]=0;
            return true;
        }
        return false;
    }

    /** Compatibility helper ONLY for synthetic completed-success callbacks. */
    public synchronized void onLifecycleT(Object receiver,long now){
        onLifecycleTBegin(receiver,now);
        onLifecycleTFinish(receiver,true,now);
    }

    /** A pending reader is not proof of a successful source start. */
    public synchronized boolean onOwnedReader(Object source,Object reader,long now){
        if(now<0||source==null||reader==null
                ||!"ero".equals(source.getClass().getName())
                ||!"mb4".equals(reader.getClass().getName())){
            rejectedUnknown++;
            return false;
        }
        expire(now);
        for(int i=0;i<LIMIT;i++){
            if(objects[i]==source&&(started[i]||tInFlight[i])){
                // A second, different reader while the first is still active
                // is ambiguous; fail closed rather than moving ownership.
                if(readers[i]!=null&&readers[i]!=reader){
                    ambiguousTCalls++;
                    clear(i);
                    return false;
                }
                readers[i]=reader;
                sourceReaderLinks++;
                return true;
            }
        }
        return false;
    }
    /** Exact completed reader reference; deferred until t success if needed. */
    public synchronized boolean onCompletedReader(Object reader,long now){
        if(now<0||reader==null||!"mb4".equals(reader.getClass().getName())){
            rejectedUnknown++;
            return false;
        }
        expire(now);
        for(int i=0;i<LIMIT;i++){
            if(readers[i]!=reader || objects[i]==null)continue;
            if(started[i]){
                completedReaderChains++;
                return true;
            }
            if(tInFlight[i]){
                if(pendingReaders[i]>=8){
                    unmatchedReaders++;
                    return false;
                }
                pendingReaders[i]++;
                // False: not yet admitted as completed source lifecycle.
                return false;
            }
        }
        unmatchedReaders++;
        return false;
    }
    public synchronized void onRemove(Object receiver,long now){
        if(now<0||type(receiver)<0){rejectedUnknown++;return;}
        expire(now);
        removals++;
        for(int i=0;i<LIMIT;i++)if(objects[i]==receiver)clear(i);
    }

    public synchronized Snapshot snapshot(){
        int pending=0;
        for(int i=0;i<LIMIT;i++)pending+=pendingReaders[i];
        return new Snapshot(factories,lifecycleCalls,matchedCalls,unmatchedCalls,
                removals,rejectedUnknown,clockDiscontinuities,sourceReaderLinks,
                completedReaderChains,unmatchedReaders,constructors,
                constructedTCalls,factoryTCalls,failedTCalls,ambiguousTCalls,
                pending,pendingReadersDiscarded);
    }
    public static final class Snapshot {
        public final int factories,lifecycleCalls,matchedCalls,unmatchedCalls,
                removals,rejectedUnknown,clockDiscontinuities,sourceReaderLinks,
                completedReaderChains,unmatchedReaders,constructors,
                constructedTCalls,factoryTCalls,failedTCalls,ambiguousTCalls,
                pendingReaderCompletions,pendingReadersDiscarded;
        private Snapshot(int f,int calls,int match,int unmatch,int remove,
                         int reject,int rollback,int links,int completed,
                         int unmatchedReaders,int ctor,int ctorT,int factoryT,
                         int failed,int overlap,int pending,int discarded){
            factories=f;lifecycleCalls=calls;matchedCalls=match;
            unmatchedCalls=unmatch;removals=remove;rejectedUnknown=reject;
            clockDiscontinuities=rollback;sourceReaderLinks=links;
            completedReaderChains=completed;this.unmatchedReaders=unmatchedReaders;
            constructors=ctor;constructedTCalls=ctorT;factoryTCalls=factoryT;
            failedTCalls=failed;ambiguousTCalls=overlap;
            pendingReaderCompletions=pending;pendingReadersDiscarded=discarded;
        }
    }
}
