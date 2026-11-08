package pro.celikom.nativeprobe.identitydiag;

/**
 * Test.76: detection only. The opt-in Android Yandex framework session can
 * prove the old external Media3 controller is on a different song, but it
 * CANNOT by itself authorize which CELIKOM replacement should play.
 *
 * Only a second actual Media3 controller, independently cross-verified against
 * the fresh Yandex framework title+artist+duration, may replace the stale one.
 */
final class YandexIdentityDivergenceGate {
 static final int FRAMEWORK_PLAYING=3,FRAMEWORK_PAUSED=2;
 static final int REMOTE_BUFFERING=2;
 static final long MISMATCH_HOLD_MS=900, MIN_REMOTE_EVENT_AGE_MS=1250;
 static final long REPROBE_MS=5500;
 private String oldKey,platformKey;
 private long mismatchSince=-1,lastProbeAt=-REPROBE_MS-1;
 private boolean mismatchActive;
 static String songKey(String title,String artist,long duration){
  return YandexFrameworkTransportPolicy.norm(title)+"|"+
   YandexFrameworkTransportPolicy.norm(artist)+"|"+duration;
 }
 static boolean sameTrack(String title,String artist,long duration,
                          String platformTitle,String platformArtist,long platformDuration){
  return !YandexFrameworkTransportPolicy.norm(title).isEmpty()&&
    !YandexFrameworkTransportPolicy.norm(artist).isEmpty()&&
    YandexFrameworkTransportPolicy.norm(title).equals(
      YandexFrameworkTransportPolicy.norm(platformTitle))&&
    YandexFrameworkTransportPolicy.norm(artist).equals(
      YandexFrameworkTransportPolicy.norm(platformArtist))&&
    duration>0&&platformDuration>0&&Math.abs(duration-platformDuration)<=2000;
 }
 boolean mismatchActive(){return mismatchActive;}
 void reset(){oldKey=null;platformKey=null;mismatchSince=-1;mismatchActive=false;}
 boolean observe(String alias,String oldTitle,String oldArtist,long oldDuration,
   int oldRemoteState,boolean remotePlaying,long remoteEventAgeMs,
   boolean platformAvailable,int platformCount,String freshTitle,String freshArtist,
   long freshDuration,int freshState,long freshPosition,long freshStateAgeMs,long now){
  boolean fresh=platformAvailable&&platformCount==1&&freshDuration>0
    &&freshTitle!=null&&!freshTitle.trim().isEmpty()&&freshArtist!=null
    &&!freshArtist.trim().isEmpty()&&freshPosition>=0
    &&freshStateAgeMs>=-25&&freshStateAgeMs<=4000
    &&(freshState==FRAMEWORK_PLAYING||freshState==FRAMEWORK_PAUSED);
  boolean mismatch=fresh&&!sameTrack(oldTitle,oldArtist,oldDuration,
    freshTitle,freshArtist,freshDuration);
  // Protect healthy playback and normal track handoffs: the exact owner run
  // had remote Media3 stuck BUFFERING on old song, and framework PLAYING new.
  boolean remoteQuiet=oldRemoteState==REMOTE_BUFFERING&&!remotePlaying
    &&remoteEventAgeMs>=MIN_REMOTE_EVENT_AGE_MS;
  if(!mismatch||!remoteQuiet){
   reset();return false;
  }
  String old=String.valueOf(alias)+"|"+songKey(oldTitle,oldArtist,oldDuration);
  String changed=songKey(freshTitle,freshArtist,freshDuration);
  if(!old.equals(oldKey)||!changed.equals(platformKey)){
   oldKey=old;platformKey=changed;mismatchSince=now;
   mismatchActive=false;return false;
  }
  if(now-mismatchSince<MISMATCH_HOLD_MS)return false;
  mismatchActive=true;
  if(now-lastProbeAt<REPROBE_MS)return false;
  lastProbeAt=now;
  return true;
 }
}
