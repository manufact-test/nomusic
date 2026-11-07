package pro.celikom.nativeprobe.identitydiag;

import java.util.Objects;

/** Holds a fresh, read-only Media3 transport snapshot while the primary binder
 * catches up. It never sends play, pause or seek commands to Yandex. */
final class SourceTransportOverride {
 static final long POSITION_MATCH_MS=1500,SEEK_CONFIRM_MS=2500;
 private PlaybackSource snapshot;

 boolean active(){return snapshot!=null;}

 boolean accept(PlaybackSource live,PlaybackSource fresh,long expectedPositionMs,long now){
  if(live==null||fresh==null||!Objects.equals(live.key,fresh.key)
      ||!Objects.equals(live.alias,fresh.alias)||fresh.position<0
      ||fresh.duration<=0||fresh.position>fresh.duration+2000)return false;
  if(expectedPositionMs>=0&&Math.abs(fresh.position-expectedPositionMs)>SEEK_CONFIRM_MS)return false;
  long livePosition=project(live,now),freshPosition=project(fresh,now);
  if(sameState(live,fresh)&&Math.abs(livePosition-freshPosition)<=POSITION_MATCH_MS){
   snapshot=null;return true;
  }
  snapshot=fresh;return true;
 }

 PlaybackSource apply(PlaybackSource live,long now){
  if(snapshot==null)return live;
  if(live==null||!Objects.equals(snapshot.key,live.key)){
   snapshot=null;return live;
  }
  long expected=project(snapshot,now),actual=project(live,now);
  if(sameState(snapshot,live)&&Math.abs(expected-actual)<=POSITION_MATCH_MS){
   snapshot=null;return live;
  }
  return new PlaybackSource(live,expected,snapshot.playing,snapshot.connected,
    snapshot.speed,snapshot.wantsToPlay,snapshot.buffering,now);
 }

 void clear(){snapshot=null;}

 private static boolean sameState(PlaybackSource a,PlaybackSource b){
  return a.playing==b.playing&&a.wantsToPlay==b.wantsToPlay&&a.buffering==b.buffering;
 }
 private static long project(PlaybackSource source,long now){
  if(source==null)return -1;
  long position=source.position;
  if(source.playing&&source.speed>0&&Float.isFinite(source.speed))
   position+=Math.max(0,Math.round(Math.max(0,now-source.observed)*source.speed));
  return position;
 }
}
