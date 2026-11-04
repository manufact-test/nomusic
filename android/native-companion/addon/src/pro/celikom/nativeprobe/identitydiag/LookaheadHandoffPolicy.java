package pro.celikom.nativeprobe.identitydiag;

/** A live verified current-track download is more valuable than restarting from zero. */
final class LookaheadHandoffPolicy {
 static final long INITIAL_WAIT_MS=10000;
 static final long MAX_CURRENT_WAIT_MS=45000;
 static final long PROGRESS_STALE_MS=8000;
 static final long RECHECK_MS=2000;

 static boolean keepInFlight(long now,long waitStartedAt,long lastProgressAt,long bytes,String phase){
  if(now<waitStartedAt||now-waitStartedAt>=MAX_CURRENT_WAIT_MS)return false;
  return "downloading".equals(phase)&&bytes>0&&lastProgressAt>=0
   &&now>=lastProgressAt&&now-lastProgressAt<=PROGRESS_STALE_MS;
 }
 private LookaheadHandoffPolicy(){}
}
