package pro.celikom.nativeprobe.identitydiag;

/** No Yandex, no MediaPlayer, no audio input; deterministic Test.50 gate. */
public final class TestSeekTimeoutCircuitBreaker {
 static int checks;
 static void check(boolean ok,String msg){
  checks++;
  if(!ok)throw new AssertionError(msg+" assertion="+checks);
 }
 static void basic() {
  SeekTimeoutCircuitBreaker g=new SeekTimeoutCircuitBreaker();
  SeekTimeoutCircuitBreaker.Decision first=g.timeout("A|album",1000);
  check(!first.originalUntilBoundary&&first.observedTimeouts==1&&!first.newLatch,
   "one slow range is NOT enough to reject a usable replacement");
  SeekTimeoutCircuitBreaker.Decision second=g.timeout("A|album",2000);
  check(second.originalUntilBoundary&&second.observedTimeouts==2&&second.newLatch,
   "two same-source failures within the window must keep original");
  check(g.blocked("A|album")&&!g.blocked("B|album"),
   "safety latch uses exact track key");
  g.successfulSeek("A|album");
  check(g.blocked("A|album"),
   "old seek ACK cannot unlock a latched failed song");
  g.boundary();
  check(!g.blocked("A|album"),"Next clears only the retired latch");
  check(!g.timeout("B|album",3000).originalUntilBoundary,
   "Next starts with a clean timeout allowance");
 }
 static void resetAndNoCrossTrackCarryover() {
  SeekTimeoutCircuitBreaker g=new SeekTimeoutCircuitBreaker();
  g.timeout("A",100);
  check(!g.timeout("B",101).originalUntilBoundary,
   "A failure cannot consume B budget");
  check(!g.timeout("A",102).originalUntilBoundary,
   "switching back to A starts new generation");
  g.timeout("A",103);
  check(g.blocked("A"),"second A timeout");
  check(!g.timeout("C",104).originalUntilBoundary,
   "first C failure after old A latch has clean budget");
 }
 static void realAckAndLongDelay() {
  SeekTimeoutCircuitBreaker g=new SeekTimeoutCircuitBreaker();
  g.timeout("A",100);
  g.successfulSeek("B");
  check(g.timeout("A",500).originalUntilBoundary,
   "unrelated callback may not erase A timeout");
  g.boundary();
  g.timeout("A",1000);
  g.successfulSeek("A");
  check(!g.timeout("A",1100).originalUntilBoundary,
   "real successful A seek resets A streak");
  check(!g.timeout("A",63001).originalUntilBoundary,
   "older-than-window timeouts cannot accumulate");
  check(!g.timeout("A",200).originalUntilBoundary,
   "monotonic clock rollback starts fresh count");
 }
 static void missingIdentityIsNotRetained() {
  SeekTimeoutCircuitBreaker g=new SeekTimeoutCircuitBreaker();
  check(!g.timeout(null,0).originalUntilBoundary,"null cannot latch");
  check(!g.timeout("",1).originalUntilBoundary,"empty cannot latch");
  check(!g.timeout("A",-1).originalUntilBoundary,"invalid time cannot latch");
  check(!g.timeout("A",100).originalUntilBoundary,"new valid A starts clean");
 }
 static void foreignOrUnknownFailureMustNotUnlock() {
  SeekTimeoutCircuitBreaker g=new SeekTimeoutCircuitBreaker();
  g.timeout("A",1000);
  g.timeout("A",1100);
  check(g.blocked("A"),"A latched before stale callbacks");
  check(!g.timeout(null,1200).originalUntilBoundary&&g.blocked("A"),
   "unidentified timeout cannot clear the A latch");
  check(!g.timeout("",1201).originalUntilBoundary&&g.blocked("A"),
   "empty identity cannot clear the A latch");
  check(!g.timeout("A",-1).originalUntilBoundary&&g.blocked("A"),
   "invalid clock cannot clear the A latch");
  SeekTimeoutCircuitBreaker.Decision other=g.timeout("B",1300);
  check(!other.originalUntilBoundary&&other.observedTimeouts==0&&g.blocked("A"),
   "foreign source callback cannot clear A or poison B");
  check(g.timeout("A",1400).originalUntilBoundary&&g.blocked("A"),
   "old source remains original-only until a real boundary");
  g.boundary();
  check(!g.blocked("A")&&!g.timeout("B",1600).originalUntilBoundary,
   "only true boundary starts clean B");
 }
 static void manyHealthySongsNeverBlock() {
  SeekTimeoutCircuitBreaker g=new SeekTimeoutCircuitBreaker();
  for(int i=0;i<50000;i++){
   String key="track|"+(i%37);
   check(!g.timeout(key,i*100L).originalUntilBoundary,
       "one seek timeout on a new track must not block");
   g.successfulSeek(key);
   check(!g.blocked(key),"valid ACK keeps same-track audio path enabled");
  }
 }
 static void longSameSongTimeouts() {
  SeekTimeoutCircuitBreaker g=new SeekTimeoutCircuitBreaker();
  for(int i=0;i<1000;i++){
   String key="A"+i;
   g.boundary();
   check(!g.timeout(key,10000).originalUntilBoundary,"first seek timeout");
   check(g.timeout(key,11000).originalUntilBoundary,"second failure latches");
   for(int j=0;j<4;j++)
    check(g.timeout(key,12000+j*100).originalUntilBoundary,
        "late callback must never resuscitate failed track");
  }
 }
 public static void main(String[] args){
  basic();
  resetAndNoCrossTrackCarryover();
  realAckAndLongDelay();
  missingIdentityIsNotRetained();
  foreignOrUnknownFailureMustNotUnlock();
  manyHealthySongsNeverBlock();
  longSameSongTimeouts();
  System.out.println("PASS: Test.50 isolated seek timeout fail-open gate "+checks+
                     " own-model checks; no Android playback tested");
 }
}
