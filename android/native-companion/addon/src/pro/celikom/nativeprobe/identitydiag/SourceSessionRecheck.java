package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;

/**
 * A same-session audio-effect OPEN is only a hint, not proof of a new Yandex
 * track. It can never authorize a replacement. If a Media3 controller has
 * delivered no events while the source is being reopened, first return the
 * original to the user and quarantine the old item until a new read-only
 * controller confirms a changed item or a materially different seek cursor.
 */
final class SourceSessionRecheck {
 static final long MIN_MEDIA_EVENT_SILENCE_MS=3000;
 static final long MIN_RECHECK_INTERVAL_MS=12000;
 static final long CURSOR_DISCONTINUITY_MS=3500;

 String suspectAlias;
 long suspectPositionMs=-1,suspectAtMs=-1,lastRefreshAtMs=-1;
 boolean awaitingFreshSource;

 boolean trigger(boolean activeReplacement,boolean controllerConnected,
                 String alias,long positionMs,int observedSession,int trustedSession,
                 long mediaEventAgeMs,long now){
  if(awaitingFreshSource||!activeReplacement||!controllerConnected||alias==null
      ||positionMs<0||observedSession<=0||observedSession!=trustedSession
      ||mediaEventAgeMs<MIN_MEDIA_EVENT_SILENCE_MS
      ||(lastRefreshAtMs>=0&&now-lastRefreshAtMs<MIN_RECHECK_INTERVAL_MS))return false;
  awaitingFreshSource=true;
  suspectAlias=alias;suspectPositionMs=positionMs;suspectAtMs=now;lastRefreshAtMs=now;
  return true;
 }

 /** Allow only read-only, post-reconnect evidence to release the safety fence. */
 boolean accept(String alias,long positionMs,long now){
  if(!awaitingFreshSource)return true;
  if(alias==null||positionMs<0)return false;
  if(!Objects.equals(suspectAlias,alias)){clear();return true;}
  long expected=suspectPositionMs+Math.max(0,now-suspectAtMs);
  if(Math.abs(positionMs-expected)>=CURSOR_DISCONTINUITY_MS){clear();return true;}
  return false;
 }

 boolean confirmFreshSeek(String alias,long eventPosition,long livePosition){
  if(!awaitingFreshSource||alias==null||!Objects.equals(alias,suspectAlias)
      ||!SourceTransitionGate.currentPositionSeek(livePosition,eventPosition))return false;
  clear();return true;
 }

 void clear(){awaitingFreshSource=false;suspectAlias=null;suspectPositionMs=-1;suspectAtMs=-1;}
}
