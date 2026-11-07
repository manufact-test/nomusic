package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
final class PlaybackSource {
 final String key,alias,title,artist,albumId;final long duration,position,observed;final boolean playing,connected,wantsToPlay,buffering;final float speed;
 PlaybackSource(String alias,String title,String artist,long duration,String cover,long position,boolean playing,boolean connected,float speed){
  this(alias,title,artist,duration,cover,position,playing,connected,speed,playing,false);
 }
 PlaybackSource(String alias,String title,String artist,long duration,String cover,long position,boolean playing,boolean connected,float speed,boolean wantsToPlay,boolean buffering){
  this.alias=alias;this.title=title;this.artist=artist;this.duration=duration;albumId=AlbumMatch.albumId(cover);
  key=key(alias,albumId,title,artist,duration);this.position=position;this.playing=playing;
  this.connected=connected;this.speed=speed;this.wantsToPlay=wantsToPlay;this.buffering=buffering;
  observed=SystemClock.elapsedRealtime();
 }
 /** Same immutable track identity, but a pause-controlled media clock. No
  * change to the audio decoder's source, duration, or canonical track ID. */
 PlaybackSource(PlaybackSource live,long projectedPosition,boolean effectivePlaying,boolean effectiveWantsToPlay){
  alias=live.alias;title=live.title;artist=live.artist;albumId=live.albumId;duration=live.duration;
  key=live.key;position=projectedPosition;playing=effectivePlaying;connected=live.connected;
  speed=live.speed;wantsToPlay=effectiveWantsToPlay;buffering=false;
  observed=SystemClock.elapsedRealtime();
 }
 static String key(String alias,Object album,String title,String artist,long duration){return alias+"|"+album+"|"+title+"|"+artist+"|"+duration;}
}
