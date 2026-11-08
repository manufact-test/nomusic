package pro.celikom.nativeprobe.identitydiag;

import java.util.Objects;

/**
 * Passive detector for non-advancing Yandex Media3 positions while READY and
 * playing. Detects an untrustworthy source clock; NEVER synthesizes a seek,
 * pauses the native app or predicts audio from a stalled position.
 */
final class ProblemSourceClockPolicy {
 static final long STALL_MS=2100, MOTION_MS=120, END_MARGIN_MS=1200;
 private String alias;
 private long at=-1,position=-1;
 private boolean reported;
 void reset(){alias=null;at=-1;position=-1;reported=false;}
 boolean observe(String currentAlias,long sourcePosition,long duration,
                 boolean isPlaying,boolean isReady,long now){
  if(currentAlias==null||sourcePosition<0||duration<=END_MARGIN_MS
    ||sourcePosition>=duration-END_MARGIN_MS||!isPlaying||!isReady||now<0){
   reset();return false;
  }
  if(!Objects.equals(alias,currentAlias)||at<0||Math.abs(sourcePosition-position)>MOTION_MS){
   alias=currentAlias;at=now;position=sourcePosition;reported=false;return false;
  }
  if(!reported&&now-at>=STALL_MS){
   reported=true;return true;
  }
  return false;
 }
 long stalledSince(){return at;}
 long anchorPosition(){return position;}
}
