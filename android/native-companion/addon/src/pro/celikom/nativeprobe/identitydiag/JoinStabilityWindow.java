package pro.celikom.nativeprobe.identitydiag;

/**
 * Test.40 cold-entry safety fence. A single Media3 cursor sample within
 * 100ms was never proof of a stable handover: Test.39's error sometimes grew
 * from 28ms to 88ms during its 160ms mix. Observe several moving samples
 * while the replacement is still inaudible, and keep the original when the
 * transport clocks cannot agree. Neither this nor MediaPlayer timestamps
 * measure source PCM phase, output latency or mastering loudness.
 */
final class JoinStabilityWindow {
 static final long HOLD_MS=100;
 static final long MAX_DRIFT_MS=60;
 static final long MAX_SPREAD_MS=22;
 static final long LOCAL_DEADLINE_MS=1400;
 static final long STREAM_DEADLINE_MS=1800;
 enum Decision {WAIT, READY, UNSAFE}

 long started=-1,min=Long.MAX_VALUE,max=Long.MIN_VALUE,last=-1;
 int samples;

 void reset(){started=-1;min=Long.MAX_VALUE;max=Long.MIN_VALUE;last=-1;samples=0;}

 Decision observe(long now,long drift,long gateStarted,long deadlineMs){
  if(now-gateStarted>=deadlineMs)return Decision.UNSAFE;
  if(Math.abs(drift)>MAX_DRIFT_MS){reset();return Decision.WAIT;}
  if(started<0){started=now;min=drift;max=drift;samples=1;last=now;return Decision.WAIT;}
  if(now<=last)return Decision.WAIT;
  last=now;samples++;
  min=Math.min(min,drift);max=Math.max(max,drift);
  if(max-min>MAX_SPREAD_MS){reset();return Decision.WAIT;}
  return now-started>=HOLD_MS&&samples>=4?Decision.READY:Decision.WAIT;
 }
}
