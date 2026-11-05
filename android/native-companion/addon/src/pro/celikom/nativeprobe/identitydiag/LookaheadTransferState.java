package pro.celikom.nativeprobe.identitydiag;

/** One verified speculative file transfer, promoted to current-track priority
 * only after the live resolve confirms the exact replacement edition. */
final class LookaheadTransferState {
 static final long INITIAL_WAIT_MS=1200, MAX_EXTRA_WAIT_MS=1400, PROGRESS_FRESH_MS=450;
 private volatile boolean foreground;
 private volatile long received,expected=-1,updatedAt=-1;

 void promote(){foreground=true;}
 boolean foreground(){return foreground;}
 void progress(long bytes,long total,long now){
  if(bytes<0||total<=0||bytes>total)return;
  received=bytes;expected=total;updatedAt=now;
 }
 long received(){return received;}
 long expected(){return expected;}
 /** Do not discard an almost-complete validated download just because the
  * fixed initial handoff timer fired. Never extend a stalled/unknown transfer. */
 boolean finishInsteadOfRestart(long now,long waitStarted){
  long total=expected,bytes=received,updated=updatedAt;
  return foreground&&total>0&&bytes>=1048576
    &&bytes*100/total>=60&&bytes<total
    &&updated>=0&&now>=updated&&now-updated<=PROGRESS_FRESH_MS
    &&now>=waitStarted&&now-waitStarted<INITIAL_WAIT_MS+MAX_EXTRA_WAIT_MS;
 }
}
