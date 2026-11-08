package pro.celikom.nativeprobe.identitydiag;

import java.util.Objects;

/**
 * One bounded user-requested pause retry. Never auto-issues commands for
 * original Yandex UI actions: only a verified CELIKOM notification pause
 * that was accepted then reverted may be retried exactly once.
 */
final class ProblemTransportRecoveryPolicy {
 static final long CHECK_MS=710, CONFIRM_LIMIT_MS=450, LATEST_RETRY_MS=1400;
 private String alias,track;
 private long pauseAt=-1,serial;
 private boolean confirmed,retried;
 long cancel(){alias=null;track=null;pauseAt=-1;confirmed=false;retried=false;return ++serial;}
 long arm(String alias,String track,long now){
  cancel();
  if(alias!=null&&track!=null&&now>=0){
   this.alias=alias;this.track=track;pauseAt=now;
  }
  return serial;
 }
 boolean confirm(long ticket,String alias,String track,long now,boolean paused){
  if(valid(ticket,alias,track,now)&&now-pauseAt<=CONFIRM_LIMIT_MS&&paused){
   confirmed=true;return true;
  }
  return false;
 }
 boolean consumeRetry(long ticket,String alias,String track,long now,boolean currentlyPlaying){
  if(!valid(ticket,alias,track,now)||!confirmed||retried||!currentlyPlaying
    ||now-pauseAt<CHECK_MS-80||now-pauseAt>LATEST_RETRY_MS)return false;
  retried=true;return true;
 }
 boolean valid(long ticket,String currentAlias,String currentTrack,long now){
  return pauseAt>=0&&ticket==serial&&now>=pauseAt
    &&Objects.equals(alias,currentAlias)&&Objects.equals(track,currentTrack);
 }
 boolean retryUsed(){return retried;}
}
