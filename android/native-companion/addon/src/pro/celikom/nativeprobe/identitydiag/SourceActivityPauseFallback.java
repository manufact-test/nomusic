package pro.celikom.nativeprobe.identitydiag;

import java.util.Objects;

/**
 * HONOR 50, Yandex Music 2026.09.5: during some UI pauses the Media3
 * controller incorrectly continues to report isPlaying/playWhenReady=true.
 *
 * This permissionless fallback reacts only to a *persistent* loss of one
 * platform media player while the replacement is already audibly exclusive.
 * It never infers a new song/trackId, issues a Yandex transport command, or
 * disconnects a controller. Brief transitions (the Test.53 regression) are
 * ignored.
 */
final class SourceActivityPauseFallback {
 static final long PAUSE_CONFIRM_MS=900;
 static final long MIN_MEDIA_EVENT_AGE_MS=900;
 static final long RECONCILE_TOLERANCE_MS=650;
 enum Mode { LIVE, PAUSED, RESUMED_CLOCK }
 static final class Snapshot {
  final Mode mode;final long positionMs;final boolean justPaused,justResumed;
  Snapshot(Mode mode,long positionMs,boolean justPaused,boolean justResumed){
   this.mode=mode;this.positionMs=positionMs;this.justPaused=justPaused;this.justResumed=justResumed;
  }
  boolean override(){return mode!=Mode.LIVE;}
 }
 private String alias;
 private int mediaCount=-1;
 private long countOneSince=-1,candidatePosition=-1;
 private boolean sawZero;
 private Mode mode=Mode.LIVE;
 private long frozenPosition=-1,resumedAt=-1;

 /** Called only from the Android playback-config callback on the service's
  * serialized main handler. Source position is a previously observed clock. */
 void activity(int count,String currentAlias,long estimatedPositionMs,long now){
  if(count<0)return;
  if(!Objects.equals(alias,currentAlias))clearForAlias(currentAlias);
  final int prior=mediaCount;
  if(mode==Mode.PAUSED){
   if(count==0)sawZero=true;
   else if((sawZero&&count>=1)||count>=2){
    mode=Mode.RESUMED_CLOCK;resumedAt=now;sawZero=false;
   }
  }else if(count==1&&prior>=2&&currentAlias!=null&&estimatedPositionMs>=0){
   countOneSince=now;candidatePosition=estimatedPositionMs;
  }else if(count!=1){
   countOneSince=-1;candidatePosition=-1;
  }
  mediaCount=count;
 }

 Snapshot sample(String currentAlias,boolean nativePlaying,boolean wantsToPlay,boolean buffering,
                 boolean exclusiveAudible,long nativePositionMs,long durationMs,float speed,
                 long media3EventAgeMs,long now){
  if(currentAlias==null||!Objects.equals(alias,currentAlias)){
   clearForAlias(currentAlias);
   return new Snapshot(Mode.LIVE,nativePositionMs,false,false);
  }
  if(!nativePlaying||!wantsToPlay||buffering||nativePositionMs<0||durationMs<=0){
   if(mode!=Mode.LIVE)resetMode();
   return new Snapshot(Mode.LIVE,nativePositionMs,false,false);
  }
  if(mode==Mode.PAUSED)return new Snapshot(mode,frozenPosition,false,false);
  if(mode==Mode.RESUMED_CLOCK){
   long delta=Math.max(0,Math.round(Math.max(0,now-resumedAt)*safeSpeed(speed)));
   long virtualPosition=Math.min(durationMs,Math.max(0,frozenPosition+delta));
   if(Math.abs(nativePositionMs-virtualPosition)<=RECONCILE_TOLERANCE_MS){
    resetMode();return new Snapshot(Mode.LIVE,nativePositionMs,false,false);
   }
   return new Snapshot(mode,virtualPosition,false,false);
  }
  if(countOneSince>=0&&mediaCount==1&&exclusiveAudible
    &&now-countOneSince>=PAUSE_CONFIRM_MS&&media3EventAgeMs>=MIN_MEDIA_EVENT_AGE_MS){
   mode=Mode.PAUSED;
   frozenPosition=Math.min(durationMs,Math.max(0,candidatePosition));
   countOneSince=-1;candidatePosition=-1;sawZero=false;
   return new Snapshot(mode,frozenPosition,true,false);
  }
  return new Snapshot(Mode.LIVE,nativePositionMs,false,false);
 }

 void sourceSeek(){resetMode();}
 void reset(){alias=null;mediaCount=-1;resetMode();}
 Mode mode(){return mode;}
 private void resetMode(){
  mode=Mode.LIVE;countOneSince=-1;candidatePosition=-1;sawZero=false;
  frozenPosition=-1;resumedAt=-1;
 }
 private void clearForAlias(String nextAlias){
  alias=nextAlias;mediaCount=-1;resetMode();
 }
 private static float safeSpeed(float speed){return Float.isFinite(speed)&&speed>0?speed:1f;}
}
