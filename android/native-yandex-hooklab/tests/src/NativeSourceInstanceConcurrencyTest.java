import pro.celikom.yandex.nativehooklab.NativeSourceInstanceFence;
import pro.celikom.yandex.nativehooklab.NativeSourceInstanceFence.Verdict;
import pro.celikom.yandex.nativehooklab.NativeSourceInstanceFence.Phase;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Deterministic hostile interleavings of OWN in-memory source instances.
 * Neither the real Android player nor vendor FileInfo/decoder is exercised.
 */
public final class NativeSourceInstanceConcurrencyTest {
    private static int checks;
    private static void yes(boolean c,String msg){
        checks++;
        if(!c)throw new AssertionError(msg+" #"+checks);
    }
    private static void eq(Object a,Object b,String msg){yes(a==b||a.equals(b),msg);}
    private static void waitFor(CountDownLatch latch)throws Exception{
        if(!latch.await(15,TimeUnit.SECONDS))
            throw new AssertionError("EXPLICIT_BARRIER_TIMEOUT");
    }
    private static void oneExactDescriptorEvenWithParallelCallbacks()throws Exception{
        NativeSourceInstanceFence fence=new NativeSourceInstanceFence();
        Object selection=new Object(),owner=new Object(),reader=new Object();
        long epoch=fence.begin(selection,100);
        eq(Verdict.RECORDED,fence.sourceBound(epoch,selection,owner,reader,101),
                "owned factory");
        ExecutorService pool=Executors.newFixedThreadPool(8);
        CountDownLatch start=new CountDownLatch(1);
        AtomicInteger success=new AtomicInteger(),rejected=new AtomicInteger();
        List<Future<?>> tasks=new ArrayList<>();
        try{
            for(int i=0;i<8;i++)tasks.add(pool.submit(()->{
                try{
                    waitFor(start);
                    Verdict result=fence.descriptorBeforePrepare(
                            epoch,selection,owner,reader,102);
                    if(result==Verdict.RECORDED)success.incrementAndGet();
                    else if(result==Verdict.OUT_OF_ORDER)rejected.incrementAndGet();
                    else throw new AssertionError("UNEXPECTED_VERDICT "+result);
                }catch(Exception e){throw new RuntimeException(e);}
            }));
            start.countDown();
            for(Future<?> task:tasks)task.get(20,TimeUnit.SECONDS);
            eq(1,success.get(),"exactly one source decision");
            eq(7,rejected.get(),"seven duplicate preprepare observers fail");
            eq(1,fence.snapshot().prepareCount,"model committed once");
            eq(Phase.BEFORE_PREPARE,fence.snapshot().phase,"correct phase");
        }finally{
            pool.shutdownNow();
            yes(pool.awaitTermination(10,TimeUnit.SECONDS),"executor cleaned");
        }
    }
    private static void oldAsyncSourceAndNewActiveSameObjectNotConfused()throws Exception{
        final NativeSourceInstanceFence fence=new NativeSourceInstanceFence();
        final Object selection=new Object(),owner=new Object(),
                reader=new Object(),loader=new Object(),task=new Object(),spec=new Object();
        long old=fence.begin(selection,100);
        eq(Verdict.RECORDED,fence.sourceBound(old,selection,owner,reader,101),
                "old factory accepted");
        eq(Verdict.RECORDED,
                fence.descriptorBeforePrepare(old,selection,owner,reader,102),
                "old prepare");
        long current=fence.begin(selection,200);
        // Reuse SAME object handles deliberately. Generation must fence them.
        ExecutorService pool=Executors.newFixedThreadPool(5);
        CountDownLatch start=new CountDownLatch(1);
        AtomicInteger stale=new AtomicInteger();
        List<Future<?>> callbacks=new ArrayList<>();
        try {
            for(int i=0;i<4;i++)callbacks.add(pool.submit(()->{
                try {
                    waitFor(start);
                    for(int n=0;n<200;n++){
                        Verdict[] v={
                            fence.scheduled(old,owner,loader,task,201),
                            fence.dispatched(old,owner,loader,task,201),
                            fence.opened(old,loader,reader,spec,201),
                            fence.read(old,loader,reader,spec,1024,201),
                            fence.closed(old,loader,reader,201),
                            fence.seek(old,owner,201)
                        };
                        for(Verdict result:v){
                            if(result!=Verdict.STALE)
                                throw new AssertionError("STALE_RESURRECTED "+result);
                            stale.incrementAndGet();
                        }
                    }
                }catch(Exception e){throw new RuntimeException(e);}
            }));
            start.countDown();
            eq(Verdict.RECORDED,fence.sourceBound(current,selection,owner,reader,210),
                    "new generation source");
            eq(Verdict.RECORDED,
                    fence.descriptorBeforePrepare(current,selection,owner,reader,211),
                    "new generation preprepare");
            eq(Verdict.RECORDED,fence.scheduled(current,owner,loader,task,212),
                    "new task");
            eq(Verdict.RECORDED,fence.dispatched(current,owner,loader,task,213),
                    "new task dispatched");
            eq(Verdict.RECORDED,fence.opened(current,loader,reader,spec,214),"new open");
            eq(Verdict.RECORDED,fence.read(current,loader,reader,spec,100,215),"new bytes");
            eq(Verdict.RECORDED,fence.closed(current,loader,reader,216),"new close");
            for(Future<?> f:callbacks)f.get(20,TimeUnit.SECONDS);
            eq(4*200*6,stale.get(),"every callback fenced");
            eq(0,fence.snapshot().rejectedCount,"stale callbacks do not poison new");
            eq(1,fence.snapshot().prepareCount,"new epoch only one prepare");
            yes(fence.snapshot().syntheticSequenceComplete,"new own-only sequence works");
        }finally{
            pool.shutdownNow();
            yes(pool.awaitTermination(10,TimeUnit.SECONDS),"workers closed");
        }
    }
    private static void twoTasksRacingCannotBothDispatch()throws Exception{
        NativeSourceInstanceFence fence=new NativeSourceInstanceFence();
        Object select=new Object(),owner=new Object(),reader=new Object(),
                loader=new Object(),task=new Object();
        long g=fence.begin(select,100);
        eq(Verdict.RECORDED,fence.sourceBound(g,select,owner,reader,101),"bound");
        eq(Verdict.RECORDED,
                fence.descriptorBeforePrepare(g,select,owner,reader,102),"prepared");
        eq(Verdict.RECORDED,fence.scheduled(g,owner,loader,task,103),"queued");
        ExecutorService pool=Executors.newFixedThreadPool(2);
        CountDownLatch begin=new CountDownLatch(1);
        try{
            Future<Verdict> valid=pool.submit(()->{
                waitFor(begin);return fence.dispatched(g,owner,loader,task,104);
            });
            Future<Verdict> wrong=pool.submit(()->{
                waitFor(begin);
                return fence.dispatched(g,owner,loader,new Object(),104);
            });
            begin.countDown();
            Verdict a=valid.get(20,TimeUnit.SECONDS);
            Verdict b=wrong.get(20,TimeUnit.SECONDS);
            yes(!(a==Verdict.RECORDED&&b==Verdict.RECORDED),
                    "only one dispatch can succeed");
            if(b==Verdict.IDENTITY_CONFLICT)
                eq(Phase.INVALIDATED,fence.snapshot().phase,
                        "wrong task poisons before or after if it hits queued phase");
            else eq(Verdict.OUT_OF_ORDER,b,"wrong task after good dispatch rejected");
            yes(!fence.snapshot().syntheticSequenceComplete,
                    "scheduled task is not audio output");
        }finally{
            pool.shutdownNow();
            yes(pool.awaitTermination(10,TimeUnit.SECONDS),"shutdown");
        }
    }
    public static void main(String[] args)throws Exception{
        oneExactDescriptorEvenWithParallelCallbacks();
        oldAsyncSourceAndNewActiveSameObjectNotConfused();
        twoTasksRacingCannotBothDispatch();
        System.out.println("PASS: NativeSourceInstanceConcurrency "+checks
                +" assertions; 4800 stale cross-thread callbacks, exactly-one prepare,"
                +" executor teardown; synthetic host only, no original Android player");
    }
}
