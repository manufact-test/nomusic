package pro.celikom.nativeprobe.identitydiag;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public final class TestAudioWorkPriority {
 static int checks;
 static void check(boolean ok,String message){checks++;if(!ok)throw new AssertionError(message);}
 public static void main(String[] ignored)throws Exception {
  AudioWorkPriority gate=new AudioWorkPriority();
  AtomicBoolean candidateValid=new AtomicBoolean(true);
  check(gate.lookaheadAllowed(candidateValid::get),"idle serial lane permits lookahead");
  gate.beginForeground();
  check(!gate.lookaheadAllowed(candidateValid::get),"current transfer preempts speculative");
  gate.beginForeground();
  gate.endForeground();
  check(!gate.lookaheadAllowed(candidateValid::get),"second queued current remains priority");
  gate.endForeground();
  check(gate.lookaheadAllowed(candidateValid::get),"lookahead resumes after all foreground work");
  candidateValid.set(false);
  check(!gate.lookaheadAllowed(candidateValid::get),"stale speculative token is still rejected");
  candidateValid.set(true);
  ExecutorService lane=Executors.newSingleThreadExecutor();
  CountDownLatch speculativeStarted=new CountDownLatch(1);
  AtomicBoolean speculationCancelled=new AtomicBoolean();
  AtomicBoolean currentCompleted=new AtomicBoolean();
  try {
   Future<?> speculative=lane.submit(()->{
    speculativeStarted.countDown();
    long until=System.nanoTime()+TimeUnit.SECONDS.toNanos(2);
    while(gate.lookaheadAllowed(candidateValid::get)&&System.nanoTime()<until) {
     try{Thread.sleep(5);}catch(InterruptedException ex){Thread.currentThread().interrupt();break;}
    }
    speculationCancelled.set(!gate.lookaheadAllowed(candidateValid::get));
   });
   check(speculativeStarted.await(1,TimeUnit.SECONDS),"speculative worker started");
   gate.beginForeground();
   Future<?> current=lane.submit(()->{
    currentCompleted.set(true);
    gate.endForeground();
   });
   speculative.get(2,TimeUnit.SECONDS);
   current.get(2,TimeUnit.SECONDS);
   check(speculationCancelled.get(),"in-flight lookahead releases the one lane for current");
   check(currentCompleted.get(),"foreground work completes without parallel network lane");
   check(gate.pendingForeground()==0&&gate.lookaheadAllowed(candidateValid::get),
     "future prefetch permitted after foreground completion");
  }finally {lane.shutdownNow();}
  System.out.println("PASS: "+checks+" serial foreground-priority and speculative-cancellation checks");
 }
}
