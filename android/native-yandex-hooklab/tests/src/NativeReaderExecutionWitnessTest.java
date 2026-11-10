import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;
import pro.celikom.yandex.nativehooklab.NativeReaderExecutionWitness;

public final class NativeReaderExecutionWitnessTest {
    private static int assertions;
    private static void check(boolean result,String reason){
        assertions++;
        if(!result)throw new AssertionError(reason+" assertion "+assertions);
    }
    public static void main(String[] args)throws Exception{
        NativeReaderExecutionWitness w=new NativeReaderExecutionWitness();
        mb4 reader=new mb4();
        ha4 source=new ha4();
        NativeReaderExecutionWitness.Scope s=w.begin(reader);
        w.open(source);
        w.positiveRead(source);
        w.close(source);
        check(w.finish(s,true),"real nested reader/source open/positive-read/close");
        check(!w.finish(s,true),"duplicate scope finish cannot count again");

        // Same type does NOT mean same source reference.
        s=w.begin(reader);
        w.open(source);
        w.positiveRead(new ha4());
        w.close(source);
        check(!w.finish(s,true),"different ha4 receiver vetoes a full chain");

        // No read => no evidence of content being consumed.
        s=w.begin(reader);
        w.open(source);
        w.close(source);
        check(!w.finish(s,true),"open+close without positive read is incomplete");

        s=w.begin(reader);
        w.open(source);
        w.positiveRead(source);
        w.close(source);
        check(!w.finish(s,false),"reader exception makes full chain invalid");

        // Reentrant Lmb4.a can nest without mixing two readers.
        s=w.begin(reader);
        w.open(source);
        NativeReaderExecutionWitness.Scope inner=w.begin(new mb4());
        ha4 innerSource=new ha4();
        w.open(innerSource);
        w.positiveRead(innerSource);
        w.close(innerSource);
        check(w.finish(inner,true),"inner frame completes");
        w.positiveRead(source);
        w.close(source);
        check(w.finish(s,true),"outer frame restored");

        // Independent thread must never inherit the current reader context.
        s=w.begin(reader);
        w.open(source);
        CountDownLatch latch=new CountDownLatch(1);
        AtomicReference<Throwable> error=new AtomicReference<>();
        Thread worker=new Thread(()->{
            try {
                w.open(source);
                w.positiveRead(source);
                w.close(source);
            }catch(Throwable ex){error.set(ex);}
            finally{latch.countDown();}
        });
        worker.start();
        latch.await();
        worker.join();
        check(error.get()==null,"parallel reporter did not crash");
        w.positiveRead(source);
        w.close(source);
        check(w.finish(s,true),"cross-thread callbacks do not poison outer scope");

        // 10000 bounded full cycles should not keep or leak stale scopes.
        for(int i=0;i<10000;i++){
            NativeReaderExecutionWitness.Scope cycle=w.begin(new mb4());
            ha4 current=new ha4();
            w.open(current);
            w.positiveRead(current);
            w.close(current);
            check(w.finish(cycle,true),"same-thread reader cycle "+i);
        }
        NativeReaderExecutionWitness.Snapshot totals=w.snapshot();
        check(totals.fullSameSource==10004,"full chain count");
        check(totals.readers==10007,"reader execution count");
        check(totals.completed==10006&&totals.threw==1,
                "exceptions and completed reader accounting");
        check(totals.openOutside>=1&&totals.readOutside>=1
                    &&totals.closeOutside>=1,"unrelated thread callbacks kept outside");
        check(totals.receiverMismatch>=2,"invalid/double-finish and receiver mismatch");
        check(totals.invalidClose>=1,"close without read recorded only as incomplete");

        // Random future method calls outside a reader are never attributed.
        w.open(source);
        w.positiveRead(source);
        w.close(source);
        check(w.snapshot().fullSameSource==10004,
                "no surviving ThreadLocal can attach late async callbacks");

        System.out.println("PASS: "+assertions
          +" real nesting, source identity, 10000 successful cycles, exceptions,"
          +" cross-thread isolation, reentrance and stale events; OWN SYNTHETIC only");
    }
}
