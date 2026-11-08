package pro.celikom.nativeprobe.identitydiag;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public final class TestResolveLaneRouter {
 static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
 public static void main(String[] args)throws Exception{
  ExecutorService current=Executors.newSingleThreadExecutor(),next=Executors.newSingleThreadExecutor();
  try{
   ResolveLaneRouter router=new ResolveLaneRouter(current,next);
   CountDownLatch holdCurrent=new CountDownLatch(1),currentRunning=new CountDownLatch(1),nextRan=new CountDownLatch(1);
   AtomicInteger calls=new AtomicInteger();
   router.submit(false,()->{currentRunning.countDown();try{holdCurrent.await(2,TimeUnit.SECONDS);}catch(InterruptedException e){Thread.currentThread().interrupt();}});
   check(currentRunning.await(1,TimeUnit.SECONDS),"current must start");
   router.submit(true,()->{calls.incrementAndGet();nextRan.countDown();});
   check(router.heldSpeculative()==1,"next must wait behind current");
   check(!nextRan.await(70,TimeUnit.MILLISECONDS),"next cannot steal current lane");
   holdCurrent.countDown();
   check(nextRan.await(2,TimeUnit.SECONDS),"next starts once current completes");
   check(calls.get()==1&&router.pendingCurrent()==0,"exactly one prefetch and no stuck foreground");
   CountDownLatch holdNext=new CountDownLatch(1),nextRunning=new CountDownLatch(1),newCurrent=new CountDownLatch(1);
   router.submit(true,()->{nextRunning.countDown();try{holdNext.await(2,TimeUnit.SECONDS);}catch(InterruptedException e){Thread.currentThread().interrupt();}});
   check(nextRunning.await(1,TimeUnit.SECONDS),"speculative request should start");
   router.submit(false,newCurrent::countDown);
   check(newCurrent.await(1,TimeUnit.SECONDS),"current must NOT wait for in-flight slow next");
   holdNext.countDown();
   // Rapid Next: check the existing per-item lease after a deterministic
   // executor barrier, not a racy thread-scheduling assumption.
   AtomicInteger generation=new AtomicInteger(1),committed=new AtomicInteger();
   CountDownLatch blocked=new CountDownLatch(1),allowNext=new CountDownLatch(1);
   router.submit(true,()->{blocked.countDown();try{allowNext.await(2,TimeUnit.SECONDS);}catch(InterruptedException e){Thread.currentThread().interrupt();}});
   check(blocked.await(1,TimeUnit.SECONDS),"next executor barrier entered");
   router.submit(true,()->{if(generation.get()==1)committed.incrementAndGet();});
   generation.incrementAndGet();
   allowNext.countDown();
   next.submit(()->{}).get(2,TimeUnit.SECONDS);
   check(committed.get()==0,"stale next must not publish after generation change");
   System.out.println("PASS: current-before-next resolve, independent lanes, stale candidate fence");
  }finally{current.shutdownNow();next.shutdownNow();}
 }
}
