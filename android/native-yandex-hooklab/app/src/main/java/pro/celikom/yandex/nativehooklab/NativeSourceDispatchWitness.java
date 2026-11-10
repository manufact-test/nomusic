package pro.celikom.yandex.nativehooklab;

/**
 * Read-only, exact-class *candidate* source dispatch observer for the pinned
 * publisher-signed #170gpr host. Never a source admission or decoder proof.
 *
 * Holds at most 16 short-lived object references in RAM, never any metadata,
 * ID, URI, URL, title, token or audio bytes. Equality is reference identity.
 * A factory->t pair proves only that the same object reached an interface
 * lifecycle call; background/preload and active player remain indistinguishable.
 */
public final class NativeSourceDispatchWitness {
    private static final String[] TYPES={
        "alt","chg","ero","ocv","ojz","t67","t6f","xq7"
    };
    private static final long WINDOW_MS=15000L;
    private final Object[] objects=new Object[16];
    private final long[] storedAt=new long[16];
    private int next;
    private int factories, lifecycleCalls, matchedCalls, unmatchedCalls, removals;
    private int rejectedUnknown, clockDiscontinuities;

    private int type(Object object) {
        if(object==null)return -1;
        String name=object.getClass().getName();
        for(int i=0;i<TYPES.length;i++)if(TYPES[i].equals(name))return i;
        return -1;
    }
    private void expire(long now) {
        for(int i=0;i<objects.length;i++) {
            if(objects[i]!=null
                    && (now<storedAt[i] || now-storedAt[i]>WINDOW_MS)) {
                if(now<storedAt[i])clockDiscontinuities++;
                objects[i]=null;
            }
        }
    }
    public synchronized void onFactory(Object returned,long elapsedMs) {
        if(elapsedMs<0||type(returned)<0){rejectedUnknown++;return;}
        expire(elapsedMs);
        for(int i=0;i<objects.length;i++){
            if(objects[i]==returned){storedAt[i]=elapsedMs;factories++;return;}
        }
        objects[next]=returned;
        storedAt[next]=elapsedMs;
        next=(next+1)%objects.length;
        factories++;
    }
    public synchronized void onLifecycleT(Object receiver,long elapsedMs) {
        if(elapsedMs<0||type(receiver)<0){rejectedUnknown++;return;}
        expire(elapsedMs);
        lifecycleCalls++;
        for(int i=0;i<objects.length;i++){
            if(objects[i]==receiver){matchedCalls++;return;}
        }
        unmatchedCalls++;
    }
    public synchronized void onRemove(Object receiver,long elapsedMs) {
        if(elapsedMs<0||type(receiver)<0){rejectedUnknown++;return;}
        expire(elapsedMs);
        removals++;
        for(int i=0;i<objects.length;i++)if(objects[i]==receiver)objects[i]=null;
    }
    public synchronized Snapshot snapshot() {
        return new Snapshot(factories,lifecycleCalls,matchedCalls,unmatchedCalls,
                removals,rejectedUnknown,clockDiscontinuities);
    }
    public static final class Snapshot {
        public final int factories,lifecycleCalls,matchedCalls,unmatchedCalls,
                removals,rejectedUnknown,clockDiscontinuities;
        private Snapshot(int f,int c,int m,int u,int r,int unknown,int rollback){
            factories=f;lifecycleCalls=c;matchedCalls=m;unmatchedCalls=u;
            removals=r;rejectedUnknown=unknown;clockDiscontinuities=rollback;
        }
    }
}
