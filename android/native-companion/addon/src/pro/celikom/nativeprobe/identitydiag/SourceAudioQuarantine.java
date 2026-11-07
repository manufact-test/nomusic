package pro.celikom.nativeprobe.identitydiag;

import java.util.Objects;

/** Fail-open safety fence for a source-audio restart that the existing Media3
 * controller does not report. Audio activity is anonymous: this never asserts
 * a track ID or a pause, and never sends a command to Yandex. */
final class SourceAudioQuarantine {
 static final long MIN_QUIET_MEDIA3_MS=3000;
 static final long RECENT_AUDIO_RESTART_MS=450;
 private String suspectAlias;
 private long sinceMs=-1;

 boolean trigger(boolean armed,boolean controllerConnected,boolean replacementAudible,
                 boolean sourcePlaying,String currentAlias,
                 int observedSession,int trustedSession,long media3EventAgeMs,
                 int activeMediaPlayers,long audioActivityAgeMs,long now){
  if(active()||!armed||!controllerConnected||!replacementAudible||!sourcePlaying
    ||currentAlias==null||currentAlias.isEmpty()
    ||observedSession<=0||observedSession!=trustedSession
    ||media3EventAgeMs<MIN_QUIET_MEDIA3_MS
    ||activeMediaPlayers!=1||audioActivityAgeMs<0||audioActivityAgeMs>RECENT_AUDIO_RESTART_MS)
    return false;
  suspectAlias=currentAlias;sinceMs=now;return true;
 }
 boolean active(){return suspectAlias!=null;}
 String alias(){return suspectAlias;}
 long age(long now){return active()?Math.max(0,now-sinceMs):-1;}
 /** Only a different item in the already-authorized controller clears the
  * fence. Repeated position polls and same-alias events cannot reauthorize
  * a potentially wrong replacement. */
 boolean allow(String liveAlias){
  if(!active())return true;
  if(liveAlias!=null&&!Objects.equals(suspectAlias,liveAlias)){clear();return true;}
  return false;
 }
 void clear(){suspectAlias=null;sinceMs=-1;}
}
