package pro.celikom.yandex.nativehooklab;

/**
 * Read-only, exact-class source-dispatch observer for pinned signed #170gpr.
 *
 * A factory -> t -> Lmb4 reader -> open/read/close match is evidence of
 * same-reference execution, NOT evidence of selected player or decoder
 * prepare. Bounded reference retention (16 slots/15s); no URLs, track IDs,
 * names, keys, audio buffers, titles or remote calls are inspected.
 */
public final class NativeSourceDispatchWitness {
    private static final String[] TYPES={
        "alt","chg","ero","ocv","ojz","t67","t6f","xq7"
    };
    private static final long WINDOW_MS=15000L;
    private final Object[] objects=new Object[16];
    private final Object[] readers=new Object[16];
    private final boolean[] started=new boolean[16];
    private final long[] storedAt=new long[16];
    private int next;
    private int factories,lifecycleCalls,matchedCalls,unmatchedCalls,removals;
    private int rejectedUnknown,clockDiscontinuities;
    private int sourceReaderLinks,completedReaderChains,unmatchedReaders;

    private int type(Object object) {
        if(object==null)return -1;
        String name=object.getClass().getName();
        for(int i=0;i<TYPES.length;i++)if(TYPES[i].equals(name))return i;
        return -1;
    }
    private void clear(int i){
        objects[i]=null;
        readers[i]=null;
        started[i]=false;
        storedAt[i]=0;
    }
    private void expire(long now){
        for(int i=0;i<objects.length;i++){
            if(objects[i]!=null
                    && (now<storedAt[i] || now-storedAt[i]>WINDOW_MS)){
                if(now<storedAt[i])clockDiscontinuities++;
                clear(i);
            }
        }
    }
    public synchronized void onFactory(Object returned,long elapsedMs){
        if(elapsedMs<0||type(returned)<0){rejectedUnknown++;return;}
        expire(elapsedMs);
        for(int i=0;i<objects.length;i++){
            if(objects[i]==returned){storedAt[i]=elapsedMs;factories++;return;}
        }
        clear(next);
        objects[next]=returned;
        storedAt[next]=elapsedMs;
        next=(next+1)%objects.length;
        factories++;
    }
    public synchronized void onLifecycleT(Object receiver,long elapsedMs){
        if(elapsedMs<0||type(receiver)<0){rejectedUnknown++;return;}
        expire(elapsedMs);
        lifecycleCalls++;
        for(int i=0;i<objects.length;i++){
            if(objects[i]==receiver){
                matchedCalls++;
                started[i]=true;
                return;
            }
        }
        unmatchedCalls++;
    }
    /**
     * Only a factory-returned Lero that entered t() can bind its exact typed
     * Lmb4 reader. Called from the hook with the reference read from Lero's
     * single, version-pinned typed field. No field contents are serialized.
     */
    public synchronized boolean onOwnedReader(Object source,Object reader,long at){
        if(at<0||source==null||reader==null
                ||!"ero".equals(source.getClass().getName())
                ||!"mb4".equals(reader.getClass().getName())){
            rejectedUnknown++;
            return false;
        }
        expire(at);
        for(int i=0;i<objects.length;i++){
            if(objects[i]==source&&started[i]){
                readers[i]=reader;
                sourceReaderLinks++;
                return true;
            }
        }
        return false;
    }
    /** Called only after a complete in-thread Lmb4.a/ha4 open/read/close. */
    public synchronized boolean onCompletedReader(Object reader,long at){
        if(at<0||reader==null
                ||!"mb4".equals(reader.getClass().getName())){
            rejectedUnknown++;
            return false;
        }
        expire(at);
        for(int i=0;i<objects.length;i++){
            if(readers[i]==reader&&objects[i]!=null&&started[i]){
                completedReaderChains++;
                return true;
            }
        }
        unmatchedReaders++;
        return false;
    }
    public synchronized void onRemove(Object receiver,long elapsedMs){
        if(elapsedMs<0||type(receiver)<0){rejectedUnknown++;return;}
        expire(elapsedMs);
        removals++;
        for(int i=0;i<objects.length;i++)if(objects[i]==receiver)clear(i);
    }
    public synchronized Snapshot snapshot(){
        return new Snapshot(factories,lifecycleCalls,matchedCalls,unmatchedCalls,
                removals,rejectedUnknown,clockDiscontinuities,sourceReaderLinks,
                completedReaderChains,unmatchedReaders);
    }
    public static final class Snapshot {
        public final int factories,lifecycleCalls,matchedCalls,unmatchedCalls,
                removals,rejectedUnknown,clockDiscontinuities,sourceReaderLinks,
                completedReaderChains,unmatchedReaders;
        private Snapshot(int f,int c,int m,int u,int r,int unknown,int rollback,
                         int links,int chains,int unmatched){
            factories=f;lifecycleCalls=c;matchedCalls=m;unmatchedCalls=u;
            removals=r;rejectedUnknown=unknown;clockDiscontinuities=rollback;
            sourceReaderLinks=links;completedReaderChains=chains;
            unmatchedReaders=unmatched;
        }
    }
}
