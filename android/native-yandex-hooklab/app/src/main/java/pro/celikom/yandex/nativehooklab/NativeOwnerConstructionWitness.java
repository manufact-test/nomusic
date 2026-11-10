package pro.celikom.yandex.nativehooklab;

/**
 * Runtime, same-thread, concrete owner-constructor causality witness.
 *
 * The signed original has an ocv.i0():void path which directly constructs
 * ero(wzi,ga4...) rather than returning it from the kvs.A factory.
 * Count a child only when the exact ero constructor RETURNS while an exact
 * ocv.i0 frame is running on the SAME thread. This does not touch original
 * args, private fields, URI, metadata, track IDs, audio or player controls.
 *
 * Never infer decoder selection, current track, or active media source from
 * this structural observation. A completed owner/child pair is merely an
 * unambiguous same-thread method-nesting fact.
 */
public final class NativeOwnerConstructionWitness {
    public static final class Scope {
        private Scope previous;
        private Object owner;
        private Object child;
        private boolean ambiguous,finished;
        private Scope(Scope old,Object owner){
            previous=old;
            this.owner=owner;
        }
    }
    public static final class Match {
        public final Object owner,child;
        Match(Object owner,Object child){this.owner=owner;this.child=child;}
    }
    private final ThreadLocal<Scope> inI0=new ThreadLocal<>();
    private long enterCalls,successfulExits,failedExits,exactPairs;
    private long multipleChildren,orphanConstructors,badFrames;

    public Scope begin(Object owner){
        if(owner==null||!"ocv".equals(owner.getClass().getName())){
            synchronized(this){badFrames++;}
            return null;
        }
        Scope scope=new Scope(inI0.get(),owner);
        inI0.set(scope);
        synchronized(this){enterCalls++;}
        return scope;
    }

    public void onConstructed(Object child){
        Scope scope=inI0.get();
        if(scope==null){
            synchronized(this){orphanConstructors++;}
            return;
        }
        if(scope.finished||child==null
                ||!"ero".equals(child.getClass().getName())){
            scope.ambiguous=true;
            synchronized(this){badFrames++;}
            return;
        }
        if(scope.child==null){
            scope.child=child;
        } else if(scope.child!=child){
            // Two genuinely different ero objects in one owner i0 cannot
            // be distinguished as the selected output by nesting alone.
            scope.ambiguous=true;
            synchronized(this){multipleChildren++;}
        }
        // Delegating 2-arg to 3-arg constructors for SAME object is okay.
    }

    public Match finish(Scope scope,boolean returnedNormally){
        if(scope==null)return null;
        if(scope.finished||inI0.get()!=scope){
            synchronized(this){badFrames++;}
            inI0.remove();
            return null;
        }
        scope.finished=true;
        if(scope.previous==null)inI0.remove();else inI0.set(scope.previous);
        Object owner=scope.owner;
        Object child=scope.child;
        boolean good=returnedNormally&&!scope.ambiguous&&owner!=null&&child!=null;
        scope.previous=null;
        scope.owner=null;
        scope.child=null;
        synchronized(this){
            if(returnedNormally)successfulExits++;else failedExits++;
            if(good)exactPairs++;
        }
        return good?new Match(owner,child):null;
    }

    public synchronized Snapshot snapshot(){
        return new Snapshot(enterCalls,successfulExits,failedExits,exactPairs,
                multipleChildren,orphanConstructors,badFrames);
    }
    public static final class Snapshot {
        public final long enters,successes,failures,exactPairs,multipleChildren,
                orphanConstructors,badFrames;
        private Snapshot(long e,long s,long f,long pair,long ambiguous,
                         long orphan,long bad){
            enters=e;successes=s;failures=f;exactPairs=pair;
            multipleChildren=ambiguous;orphanConstructors=orphan;badFrames=bad;
        }
    }
}
