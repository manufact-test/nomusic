package pro.celikom.nativeprobe.identitydiag;

import java.util.Objects;

/**
 * Test.50-only EXPERIMENT. Prevent repeat same-track native seek timeout
 * reconnect loops by keeping the original source until the next boundary.
 *
 * This is NOT evidence that Yandex's own pause/seek transport is working,
 * not a source-first FileInfo replacement, and never sends media commands.
 * All timestamps must come from SystemClock.elapsedRealtime().
 */
final class SeekTimeoutCircuitBreaker {
 static final long WINDOW_MS = 60000L;
 static final int MAX_TIMEOUTS = 2;
 private String key;
 private long lastFailureAt = -1L;
 private int consecutive;
 private boolean latched;

 static final class Decision {
  final boolean originalUntilBoundary;
  final int observedTimeouts;
  final boolean newLatch;
  Decision(boolean block,int count,boolean first){
   originalUntilBoundary=block;
   observedTimeouts=count;
   newLatch=first;
  }
 }

 Decision timeout(String currentKey,long at) {
  if(currentKey==null||currentKey.isEmpty()||at<0L) {
   reset();
   return new Decision(false,0,false);
  }
  if(!Objects.equals(key,currentKey)) reset();
  if(latched) return new Decision(true,consecutive,false);
  if(lastFailureAt<0 || at<lastFailureAt || at-lastFailureAt>WINDOW_MS)
   consecutive=0;
  key=currentKey;
  lastFailureAt=at;
  consecutive++;
  boolean trip=consecutive>=MAX_TIMEOUTS;
  if(trip)latched=true;
  return new Decision(latched,consecutive,trip);
 }

 void successfulSeek(String currentKey) {
  // Only an ACK for this exact source is allowed to clear its timeout streak.
  // Never release a latched fail-safe before a real track boundary.
  if(!latched&&Objects.equals(key,currentKey)) {
   consecutive=0;
   lastFailureAt=-1;
  }
 }

 void boundary() { reset(); }
 boolean blocked(String currentKey){
  return latched&&Objects.equals(key,currentKey);
 }
 private void reset(){
  key=null;
  lastFailureAt=-1;
  consecutive=0;
  latched=false;
 }
}
