package pro.celikom.yandex.nativehooklab;

import java.util.concurrent.atomic.AtomicLong;

/**
 * No-content, read-only observer for the *actual invocation nesting*
 * Lmb4.a() -> Lha4.b(La58) -> Lha4.read(byte[],int,int) -> Lha4.close().
 *
 * A complete same-thread invocation is stronger evidence than a DEX callsite,
 * but it is NOT evidence of which player selected the source or any audible
 * Yandex output. This class never inspects DataSpec, buffers, URI or results
 * beyond the caller-provided boolean that a read returned positive length.
 *
 * Source references live only on the active thread stack; every normal,
 * exceptional, and reentrant exit restores/removes the ThreadLocal frame.
 */
public final class NativeReaderExecutionWitness {
    public static final class Scope {
        private final Scope previous;
        private final Object reader;
        private Object openedSource;
        private boolean opened,read,closed,conflict,finished;
        private Scope(Scope previous,Object reader){
            this.previous=previous;
            this.reader=reader;
        }
    }
    private final ThreadLocal<Scope> inReader=new ThreadLocal<>();
    private final AtomicLong readers=new AtomicLong();
    private final AtomicLong completed=new AtomicLong();
    private final AtomicLong threw=new AtomicLong();
    private final AtomicLong openWithin=new AtomicLong();
    private final AtomicLong positiveReadWithin=new AtomicLong();
    private final AtomicLong closeWithin=new AtomicLong();
    private final AtomicLong fullSameSource=new AtomicLong();
    private final AtomicLong openOutside=new AtomicLong();
    private final AtomicLong readOutside=new AtomicLong();
    private final AtomicLong closeOutside=new AtomicLong();
    private final AtomicLong receiverMismatch=new AtomicLong();
    private final AtomicLong invalidClose=new AtomicLong();

    public Scope begin(Object reader){
        // Invoke-scoped only: never attach an unknown object, or a second
        // source in another worker thread, to a live execution frame.
        if(reader==null||!"mb4".equals(reader.getClass().getName()))return null;
        Scope scope=new Scope(inReader.get(),reader);
        inReader.set(scope);
        readers.incrementAndGet();
        return scope;
    }

    /** Called AFTER exact Lha4.b(La58):long has returned normally. */
    public void open(Object receiver){
        Scope scope=inReader.get();
        if(scope==null){openOutside.incrementAndGet();return;}
        if(!acceptSource(scope,receiver))return;
        scope.opened=true;
    }

    /** Called AFTER exact Lha4.read returns a positive byte count. */
    public void positiveRead(Object receiver){
        Scope scope=inReader.get();
        if(scope==null){readOutside.incrementAndGet();return;}
        if(!acceptSource(scope,receiver))return;
        if(scope.opened)scope.read=true;
    }

    /** Called AFTER exact Lha4.close returns normally. */
    public void close(Object receiver){
        Scope scope=inReader.get();
        if(scope==null){closeOutside.incrementAndGet();return;}
        if(!acceptSource(scope,receiver))return;
        if(scope.opened && scope.read)scope.closed=true;
        else invalidClose.incrementAndGet();
    }

    private boolean acceptSource(Scope scope,Object receiver){
        if(scope.finished||receiver==null
                ||!"ha4".equals(receiver.getClass().getName())) {
            scope.conflict=true;
            receiverMismatch.incrementAndGet();
            return false;
        }
        if(scope.openedSource==null)scope.openedSource=receiver;
        if(scope.openedSource!=receiver){
            scope.conflict=true;
            receiverMismatch.incrementAndGet();
            return false;
        }
        return true;
    }

    /**
     * Must execute in finally on the SAME thread that called begin().
     * Never preserves Object refs after the last exit from the current thread.
     */
    public boolean finish(Scope scope,boolean returnedNormally){
        if(scope==null)return false;
        Scope current=inReader.get();
        if(current!=scope||scope.finished){
            // Do not silently attribute an event to a different reader.
            receiverMismatch.incrementAndGet();
            inReader.remove();
            return false;
        }
        scope.finished=true;
        if(scope.previous==null)inReader.remove();else inReader.set(scope.previous);
        if(returnedNormally)completed.incrementAndGet();else threw.incrementAndGet();
        if(scope.opened)openWithin.incrementAndGet();
        if(scope.read)positiveReadWithin.incrementAndGet();
        if(scope.closed)closeWithin.incrementAndGet();
        boolean full=returnedNormally && scope.opened && scope.read
                && scope.closed && !scope.conflict;
        if(full)fullSameSource.incrementAndGet();
        scope.openedSource=null;
        return full;
    }

    public Snapshot snapshot(){
        return new Snapshot(readers.get(),completed.get(),threw.get(),
                openWithin.get(),positiveReadWithin.get(),closeWithin.get(),
                fullSameSource.get(),openOutside.get(),readOutside.get(),
                closeOutside.get(),receiverMismatch.get(),invalidClose.get());
    }
    public static final class Snapshot {
        public final long readers,completed,threw,openWithin,
                positiveReadWithin,closeWithin,fullSameSource,openOutside,
                readOutside,closeOutside,receiverMismatch,invalidClose;
        private Snapshot(long a,long b,long c,long d,long e,long f,long g,
                         long h,long i,long j,long k,long l){
            readers=a;completed=b;threw=c;openWithin=d;positiveReadWithin=e;
            closeWithin=f;fullSameSource=g;openOutside=h;readOutside=i;
            closeOutside=j;receiverMismatch=k;invalidClose=l;
        }
    }
}
