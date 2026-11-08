package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;

/**
 * Test.71: passive second view of the official Yandex media session.
 * Android MediaBrowser's PlaybackState may be backed by the SAME Yandex service
 * as Media3; this is not independent PCM or proof of speaker presentation.
 * Only a fresh, title/artist-matched PAUSED disagreement may fail closed.
 * This class never issues remote transport commands or changes decoder clocks.
 */
final class NativeTransportWitness {
 static final int LEGACY_PAUSED=2, LEGACY_PLAYING=3, MEDIA3_READY=3;
 static final long MAX_STATE_AGE_MS=1800, CONFIRM_MS=300, MIN_MEDIA3_EVENT_AGE_MS=350;
 static final long POST_SEEK_SAMPLE_MS=300, POST_SEEK_LATE_MS=1400;
 static boolean watched(String trackId){
  return "42884423".equals(trackId)||"39949113".equals(trackId);
 }
 static final class Verdict {
  final String stage;
  final boolean report,restore,matchedIdentity,freshState,freshAfterSeek,quarantined;
  final long seekAgeMs,positionDifferenceMs,legacyStateAgeMs;
  Verdict(String stage,boolean report,boolean restore,boolean identity,boolean fresh,
          boolean afterSeek,boolean quarantined,long seekAge,long delta,long age){
   this.stage=stage;this.report=report;this.restore=restore;matchedIdentity=identity;
   freshState=fresh;freshAfterSeek=afterSeek;this.quarantined=quarantined;
   seekAgeMs=seekAge;positionDifferenceMs=delta;legacyStateAgeMs=age;
  }
 }
 private String alias,track;
 private boolean quarantined,initialReported,seekEarlyReported,seekLateReported;
 private long mismatchSince=-1,seekAt=-1,seekTarget=-1;
 private int seekNumber;
 private void reset(String mediaAlias,String trackId){
  alias=mediaAlias;track=trackId;quarantined=false;initialReported=false;
  seekEarlyReported=false;seekLateReported=false;mismatchSince=-1;
  seekAt=-1;seekTarget=-1;seekNumber=0;
 }
 void noteSeek(String mediaAlias,String trackId,long target,long now){
  if(!watched(trackId)||mediaAlias==null||target<0)return;
  if(!Objects.equals(alias,mediaAlias)||!Objects.equals(track,trackId))reset(mediaAlias,trackId);
  seekAt=now;seekTarget=target;seekNumber++;
  mismatchSince=-1;seekEarlyReported=false;seekLateReported=false;
 }
 boolean quarantined(String mediaAlias,String trackId){
  return watched(trackId)&&quarantined&&Objects.equals(alias,mediaAlias)&&Objects.equals(track,trackId);
 }
 int seekNumber(){return seekNumber;}
 Verdict observe(String mediaAlias,String trackId,boolean matchingMetadata,int platformState,
                 long platformPosition,long platformAge,long media3Position,boolean media3Playing,
                 boolean media3WantsToPlay,int media3State,long media3EventAge,long now){
  if(!watched(trackId)||mediaAlias==null)return new Verdict("out_of_scope",false,false,false,false,false,false,-1,-1,platformAge);
  if(!Objects.equals(alias,mediaAlias)||!Objects.equals(track,trackId))reset(mediaAlias,trackId);
  long seekAge=seekAt<0?-1:Math.max(0,now-seekAt);
  long delta=platformPosition<0||media3Position<0?-1:platformPosition-media3Position;
  boolean fresh=platformAge>=0&&platformAge<=MAX_STATE_AGE_MS;
  // A recent legacy snapshot after the seek is diagnostic evidence only;
  // getPosition and Media3.getCurrentPosition can both be projections.
  boolean freshAfterSeek=seekAt>=0&&fresh&&now-platformAge>=seekAt;
  String stage=null;
  if(!initialReported){initialReported=true;stage="initial";}
  if(seekAge>=POST_SEEK_SAMPLE_MS&&!seekEarlyReported){
   seekEarlyReported=true;stage="post_seek_early";
  }
  if(seekAge>=POST_SEEK_LATE_MS&&!seekLateReported){
   seekLateReported=true;stage="post_seek_late";
  }
  boolean disagreement=matchingMetadata&&fresh&&platformState==LEGACY_PAUSED
   &&media3Playing&&media3WantsToPlay&&media3State==MEDIA3_READY
   &&media3EventAge>=MIN_MEDIA3_EVENT_AGE_MS;
  if(!disagreement)mismatchSince=-1;
  else if(!quarantined){
   if(mismatchSince<0){mismatchSince=now;stage="pause_disagreement_candidate";}
   else if(now-mismatchSince>=CONFIRM_MS){
    quarantined=true;stage="pause_disagreement_fail_closed";
   }
  }
  boolean restore=quarantined&&"pause_disagreement_fail_closed".equals(stage);
  return new Verdict(stage,stage!=null,restore,matchingMetadata,fresh,
      freshAfterSeek,quarantined,seekAge,delta,platformAge);
 }
}
