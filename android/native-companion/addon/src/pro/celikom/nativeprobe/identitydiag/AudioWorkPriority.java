package pro.celikom.nativeprobe.identitydiag;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BooleanSupplier;

/* One serialized audio lane: queued current downloads may revoke speculative transfers. */
final class AudioWorkPriority {
 private final AtomicInteger foregroundPending=new AtomicInteger();
 void beginForeground(){foregroundPending.incrementAndGet();}
 void endForeground(){foregroundPending.updateAndGet(count->Math.max(0,count-1));}
 boolean lookaheadAllowed(BooleanSupplier candidateValid){
  return foregroundPending.get()==0&&candidateValid.getAsBoolean();
 }
 int pendingForeground(){return foregroundPending.get();}
}
