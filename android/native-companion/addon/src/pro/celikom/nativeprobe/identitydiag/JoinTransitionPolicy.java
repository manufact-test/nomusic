package pro.celikom.nativeprobe.identitydiag;

/** Test.42: bounded command-level fade, based only on transport evidence.
 *  This cannot infer whether two independent audio sessions carry identical PCM. */
final class JoinTransitionPolicy {
 static long durationMs(long driftMs,long sourceObservationAgeMs,boolean failedLongFadeRetry){
  // An error during a long fade is not evidence that repeating it is safe.
  // Test.41's successful 160ms path is the bounded same-song recovery mode.
  return failedLongFadeRetry?160:durationMs(driftMs,sourceObservationAgeMs);
 }
 static long durationMs(long driftMs,long sourceObservationAgeMs){
  long drift=Math.abs(driftMs);
  // Aligned timelines can tolerate a longer, gentler fade. A larger offset
  // should not produce a long, phase-uncertain overlapping chorus.
  if(sourceObservationAgeMs>350)return 160;
  if(drift<=20)return 220;
  if(drift<=45)return 190;
  if(drift<=75)return 160;
  return 140;
 }
 static float boundedMix(long elapsedMs,long durationMs,float previous){
  float requested=TransitionMix.progress(elapsedMs,durationMs);
  // A delayed Android handler callback must not jump from near silence to a
  // loud decoder in one pair of asynchronously applied audio commands.
  return Math.max(previous,Math.min(requested,previous+0.16f));
 }
 static long retryMs(int attempt){
  return 1200L << Math.min(3,Math.max(0,attempt-1));
 }
}
