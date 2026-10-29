package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;
/** Never accept an old snapshot across a boundary, and never wait for an alias forever. */
final class SourceTransitionGate {
 static final int ACCEPT=0,WAIT=1,REFRESH=2;static final long MAX_WAIT_MS=1000;
 String expected;long since;boolean pending;
 boolean begin(String next,long now){if(pending&&Objects.equals(expected,next))return false;pending=true;expected=next;since=now;return true;}
 int sample(String actual,long now){if(!pending||expected==null||Objects.equals(expected,actual)){clear();return ACCEPT;}return now-since>=MAX_WAIT_MS?REFRESH:WAIT;}
 /** Only current transport seeks may force a decoder resync.
  * Media3 can deliver a stale PositionInfo after a controller reconnect:
  * e.g. old 3648->61334 while live controller is already at 101197ms.
  * A true large jump is independently noticed from PlaybackSource samples.
  */
 static final long SEEK_EVENT_MAX_SKEW_MS=2000;
 static boolean currentPositionSeek(long livePositionMs,long eventNewPositionMs){
  if(livePositionMs<0||eventNewPositionMs<0)return false;
  return livePositionMs>=eventNewPositionMs
      ? livePositionMs-eventNewPositionMs<=SEEK_EVENT_MAX_SKEW_MS
      : eventNewPositionMs-livePositionMs<=SEEK_EVENT_MAX_SKEW_MS;
 }
 void clear(){pending=false;expected=null;since=0;}
}
