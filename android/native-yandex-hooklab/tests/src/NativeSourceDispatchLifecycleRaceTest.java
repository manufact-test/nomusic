import pro.celikom.yandex.nativehooklab.NativeSourceDispatchWitness;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;

/** Deterministic synthetic attacks: a queued async reader is NOT t-success. */
public final class NativeSourceDispatchLifecycleRaceTest {
    private static int count;
    private static void check(boolean condition,String message){
        count++;
        if(!condition)throw new AssertionError(message+" #"+count);
    }
    public static void main(String[] ignored)throws Exception{
        // A worker may complete the reader before the original t returns.
        // A thrown t must discard that apparently complete chain.
        NativeSourceDispatchWitness witness=new NativeSourceDispatchWitness();
        ero throwing=new ero();
        mb4 reader=new mb4();
        witness.onConstructed(throwing,100);
        witness.onLifecycleTBegin(throwing,101);
        check(witness.onOwnedReader(throwing,reader,102),
                "pending real t may tentatively hold its only known reader");
        check(!witness.onCompletedReader(reader,103),
                "early async complete not yet a successful t");
        check(witness.snapshot().pendingReaderCompletions==1
                &&witness.snapshot().completedReaderChains==0,
                "pending work must never be advertised as completed");
        check(!witness.onLifecycleTFinish(throwing,false,104),
                "throwing t invalidates pending source");
        check(witness.snapshot().pendingReadersDiscarded==1
                &&witness.snapshot().failedTCalls==1
                &&witness.snapshot().completedReaderChains==0,
                "no manufactured reader completion after exception");
        check(!witness.onCompletedReader(reader,105),
                "orphaned reader never reattaches to another source");

        // Same early worker completion may become valid exactly ONCE
        // after the original t returns normally.
        ero successful=new ero();
        mb4 goodReader=new mb4();
        witness.onConstructed(successful,200);
        witness.onLifecycleTBegin(successful,201);
        check(witness.onOwnedReader(successful,goodReader,202),"own reader");
        check(!witness.onCompletedReader(goodReader,203),
                "pending reader cannot advertise success");
        check(witness.onLifecycleTFinish(successful,true,204),
                "real t succeeded, pending reader promoted");
        check(witness.snapshot().completedReaderChains==1
                &&witness.snapshot().constructedTCalls==1
                &&witness.snapshot().pendingReaderCompletions==0,
                "one promotion only on t success");
        witness.onRemove(successful,205);
        check(!witness.onCompletedReader(goodReader,206),
                "late callback after remove cannot reappear");

        // Unknown source + wrong class is NOT a source when it happens to
        // call t, even when it looks like an owner from its method name.
        NativeSourceDispatchWitness unknown=new NativeSourceDispatchWitness();
        ero unobserved=new ero();
        unknown.onLifecycleTBegin(unobserved,300);
        check(!unknown.onOwnedReader(unobserved,new mb4(),301),
                "unobserved t receiver cannot own reader");
        check(!unknown.onLifecycleTFinish(unobserved,true,302),
                "unknown source cannot promote a selected source");

        // Concurrent/reentrant t on the SAME object before first returns
        // must not count two source commitments or steal pending readers.
        NativeSourceDispatchWitness overlap=new NativeSourceDispatchWitness();
        ero one=new ero();
        overlap.onConstructed(one,400);
        overlap.onLifecycleTBegin(one,401);
        check(overlap.onOwnedReader(one,new mb4(),402),"first tentative reader");
        overlap.onLifecycleTBegin(one,403);
        check(!overlap.onLifecycleTFinish(one,true,404),"overlap invalidates");
        check(overlap.snapshot().ambiguousTCalls==1
                &&overlap.snapshot().matchedCalls==0,
                "ambiguous overlap cannot manufacture a player source");

        // A different reader object of same mb4 CLASS cannot replace
        // the pending reader while a source is processing t().
        NativeSourceDispatchWitness conflict=new NativeSourceDispatchWitness();
        ero src=new ero();
        conflict.onFactory(src,500);
        conflict.onLifecycleTBegin(src,501);
        check(conflict.onOwnedReader(src,new mb4(),502),"first reader accepted");
        check(!conflict.onOwnedReader(src,new mb4(),503),
                "different reader must invalidate identity");
        check(!conflict.onLifecycleTFinish(src,true,504),
                "invalidated slot cannot be resurrected");

        // 5k asynchronous source switches. Each cycle begins, queues
        // a read, and either fails or succeeds. No prior generation may
        // leak its pending source into the next one.
        NativeSourceDispatchWitness many=new NativeSourceDispatchWitness();
        for(int i=0;i<5000;i++){
            long t=1000L+5L*i;
            ero current=new ero();
            mb4 currentReader=new mb4();
            many.onConstructed(current,t);
            many.onLifecycleTBegin(current,t+1);
            check(many.onOwnedReader(current,currentReader,t+2),
                    "one source owner "+i);
            check(!many.onCompletedReader(currentReader,t+3),
                    "pending before t returns "+i);
            boolean good=i%3!=0;
            check(many.onLifecycleTFinish(current,good,t+4)==good,
                    "t-success only when original succeeds "+i);
            many.onRemove(current,t+4);
            check(!many.onCompletedReader(currentReader,t+4),
                    "stale reader after NEXT "+i);
        }
        int expectedSuccess=5000-1667;
        check(many.snapshot().completedReaderChains==expectedSuccess,
                "only true successful sources committed");
        check(many.snapshot().pendingReadersDiscarded==1667
                &&many.snapshot().failedTCalls==1667,
                "all failed t pending readers discarded");
        check(many.snapshot().pendingReaderCompletions==0,
                "no source held pending after 5k switching events");

        // The async callback runs on a separate thread and must not be
        // accidentally counted as successful before t returns.
        NativeSourceDispatchWitness raced=new NativeSourceDispatchWitness();
        ero concurrent=new ero();
        mb4 shared=new mb4();
        raced.onConstructed(concurrent,30000);
        raced.onLifecycleTBegin(concurrent,30001);
        raced.onOwnedReader(concurrent,shared,30002);
        CountDownLatch done=new CountDownLatch(1);
        AtomicReference<Throwable> error=new AtomicReference<>();
        Thread thread=new Thread(()->{
            try{check(!raced.onCompletedReader(shared,30003),
                    "async callback is only pending");}
            catch(Throwable ex){error.set(ex);}
            finally{done.countDown();}
        });
        thread.start();
        done.await();
        thread.join();
        check(error.get()==null,"async reader callback never crashed");
        check(raced.snapshot().completedReaderChains==0,
                "concurrent pending evidence not an audible success");
        raced.onLifecycleTFinish(concurrent,false,30004);
        check(raced.snapshot().completedReaderChains==0
                &&raced.snapshot().pendingReadersDiscarded==1,
                "failed original source rejects concurrent completed reader");

        System.out.println("PASS: "+count+
            " native source transaction assertions; 5000 Next/exception/reader"
            +" races; ALL SYNTHETIC, no Yandex player or decoder proof");
    }
}
