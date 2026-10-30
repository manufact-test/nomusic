package pro.celikom.nativeprobe.identitydiag;

/** Fail open if two independent playback clocks diverge for a sustained period.
 * This checks commanded decoder/controller positions, not acoustic output.
 */
final class DriftGuard {
 static final long MAX_SUSTAINED_DRIFT_MS=700;
 static final long CONFIRM_MS=1500;
 private long since=-1;
 boolean confirmed(boolean aligned,boolean active,long drift,long now){
  if(!aligned||!active||Math.abs(drift)<=MAX_SUSTAINED_DRIFT_MS){reset();return false;}
  if(since<0){since=now;return false;}
  return now-since>=CONFIRM_MS;
 }
 void reset(){since=-1;}
}
