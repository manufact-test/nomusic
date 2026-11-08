package pro.celikom.nativeprobe.identitydiag;
import java.util.ArrayDeque;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Current and speculative resolves may use different network lanes, but
 * speculative work never gets queued ahead of an outstanding current lookup.
 * The pending queue is bounded by ReplacementEngine's one-next lease; stale
 * jobs still have to pass their own account/item-generation checks.
 */
final class ResolveLaneRouter {
 private final Executor foreground,lookahead;
 private final AtomicInteger currentPending=new AtomicInteger();
 private final ArrayDeque<Runnable> heldLookahead=new ArrayDeque<>();
 ResolveLaneRouter(Executor foreground,Executor lookahead){
  this.foreground=foreground;this.lookahead=lookahead;
 }
 void submit(boolean speculative,Runnable job){
  if(!speculative){
   currentPending.incrementAndGet();
   try{foreground.execute(()->{
    try{job.run();}finally{currentDone();}
   });}catch(RuntimeException rejected){currentDone();throw rejected;}
   return;
  }
  synchronized(this){
   if(currentPending.get()>0){heldLookahead.addLast(job);return;}
   lookahead.execute(job);
  }
 }
 private void currentDone(){
  if(currentPending.decrementAndGet()!=0)return;
  synchronized(this){
   // A late current request can win again; stale speculative requests will
   // fail the caller's generation/identity lease before touching the network.
   if(currentPending.get()!=0)return;
   while(!heldLookahead.isEmpty())lookahead.execute(heldLookahead.removeFirst());
  }
 }
 int pendingCurrent(){return currentPending.get();}
 synchronized int heldSpeculative(){return heldLookahead.size();}
}
