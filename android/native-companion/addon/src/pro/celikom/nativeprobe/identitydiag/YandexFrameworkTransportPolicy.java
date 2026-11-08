package pro.celikom.nativeprobe.identitydiag;
import java.util.Locale;

/**
 * Test.75: verified native-framework Yandex pause and seek observation.
 * Pure deterministic safety gate: this class never sends media commands.
 * The opt-in platform session only becomes authoritative for a track when
 * proven to disagree with the external Media3 transport.
 */
final class YandexFrameworkTransportPolicy {
 static final int PLATFORM_PAUSED=2, PLATFORM_PLAYING=3, PLATFORM_BUFFERING=6;
 static final long PLAYING_FRESH_MS=15000, BUFFERING_FRESH_MS=5000;
 static final long PAUSED_FRESH_MS=300000, SEEK_GAP_MS=1600, SEEK_JUMP_MS=1200;
 static final class Decision {
  final boolean usePlatform,failClosed,firstRecovery,seekObserved,playing,wantsToPlay,buffering;
  final long position;
  final String reason;
  Decision(boolean usePlatform,boolean failClosed,boolean firstRecovery,boolean seekObserved,
           long position,boolean playing,boolean wantsToPlay,boolean buffering,String reason){
   this.usePlatform=usePlatform;this.failClosed=failClosed;
   this.firstRecovery=firstRecovery;this.seekObserved=seekObserved;
   this.position=position;this.playing=playing;
   this.wantsToPlay=wantsToPlay;this.buffering=buffering;this.reason=reason;
  }
 }
 private String key;
 private boolean platformAuthority;
 private long previousPosition=-1,previousAt=-1;
 private int previousState=-1;
 static String norm(String s){
  return s==null?"":s.trim().replaceAll("\\s+"," ").toLowerCase(Locale.ROOT);
 }
 private void ensureTrack(String key){
  if(!key.equals(this.key)){
   this.key=key;platformAuthority=false;
   previousPosition=-1;previousAt=-1;previousState=-1;
  }
 }
 private Decision remote(String why){
  return new Decision(false,false,false,false,-1,false,false,false,why);
 }
 private Decision unsafe(String why){
  return new Decision(false,true,false,false,-1,false,false,false,why);
 }
 boolean platformAuthority(){return platformAuthority;}
 Decision reconcile(String alias,String title,String artist,long duration,
    long remotePos,boolean remotePlaying,
    boolean available,int sessions,String platformTitle,String platformArtist,
    long platformDuration,int platformState,long rawPosition,long stateAgeMs,
    float platformSpeed,long now){
  String currentKey=String.valueOf(alias)+"|"+title+"|"+artist+"|"+duration;
  ensureTrack(currentKey);
  boolean state=platformState==PLATFORM_PAUSED||platformState==PLATFORM_PLAYING||
                platformState==PLATFORM_BUFFERING;
  long freshness=platformState==PLATFORM_PAUSED?PAUSED_FRESH_MS:
     platformState==PLATFORM_BUFFERING?BUFFERING_FRESH_MS:PLAYING_FRESH_MS;
  boolean identity=alias!=null&&sessions==1&&available&&duration>0
    &&norm(title).length()>0&&norm(artist).length()>0
    &&norm(title).equals(norm(platformTitle))
    &&norm(artist).equals(norm(platformArtist))
    &&platformDuration>0&&Math.abs(platformDuration-duration)<=2000;
  boolean fresh=state&&stateAgeMs>=0&&stateAgeMs<=freshness&&rawPosition>=0
    &&rawPosition<=duration+2000&&Float.isFinite(platformSpeed)
    &&platformSpeed>=0&&platformSpeed<=2;
  if(!identity||!fresh)
   return platformAuthority?unsafe(!identity?"source_or_session_mismatch":"platform_state_stale"):
     remote(!identity?"no_verified_platform_session":"unusable_platform_state");

  long platformPos=rawPosition;
  if(platformState==PLATFORM_PLAYING&&platformSpeed>0.1f){
   platformPos+=Math.round(Math.min(stateAgeMs,PLAYING_FRESH_MS)*platformSpeed);
  }
  platformPos=Math.max(0,Math.min(duration,platformPos));
  boolean statePlaying=platformState==PLATFORM_PLAYING;
  boolean stateBuffering=platformState==PLATFORM_BUFFERING;
  boolean gap=remotePos>=0&&Math.abs(platformPos-remotePos)>=SEEK_GAP_MS;
  boolean conflictingPause=(platformState==PLATFORM_PAUSED&&remotePlaying);
  boolean conflictingPlay=(platformState==PLATFORM_PLAYING&&!remotePlaying);
  // BUFFERING happens for 15–70ms on scrubs; only treat it as evidence if
  // framework cursor is already far from remote cursor.
  boolean discrepancy=gap||conflictingPause||conflictingPlay;
  if(!platformAuthority&&!discrepancy)return remote("remote_and_platform_agree");
  boolean first=!platformAuthority;
  platformAuthority=true;
  boolean jump=false;
  if(previousAt>=0&&now>=previousAt){
   long expected=previousPosition+((previousState==PLATFORM_PLAYING)?
     Math.max(0,now-previousAt):0);
   jump=Math.abs(platformPos-expected)>SEEK_JUMP_MS;
  } else if(first&&gap&&!conflictingPause){
   jump=true;
  }
  previousPosition=platformPos;previousAt=now;previousState=platformState;
  return new Decision(true,false,first,jump,platformPos,
      statePlaying,statePlaying||stateBuffering,stateBuffering,
      first?(conflictingPause?"missed_native_pause":gap?"delayed_native_seek":"missed_native_play"):
      "verified_platform_session");
 }
}
