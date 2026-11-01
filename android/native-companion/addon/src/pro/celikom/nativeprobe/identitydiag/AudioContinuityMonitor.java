package pro.celikom.nativeprobe.identitydiag;

/** Records commanded audio gaps and overlaps, NEVER claims to measure the speaker. */
final class AudioContinuityMonitor {
 static final long MIN_REPORT_MS=40;
 static final class Finding {
  final String kind,trackId,cause,classification;
  final long durationMs;
  final boolean expectedByOwnerState;
  Finding(String kind,String trackId,String cause,long durationMs,String classification,boolean expected){
   this.kind=kind;this.trackId=trackId;this.cause=cause;this.durationMs=durationMs;
   this.classification=classification;expectedByOwnerState=expected;
  }
 }
 private boolean inGap,inOverlap;
 private long gapSince;
 private String gapTrack,gapCause;
 Finding observe(long now,String track,String cause,boolean sourcePlaying,
                 boolean nativeMuted,boolean replacementPlaying,float replacementVolume) {
  return observe(now,track,cause,sourcePlaying,nativeMuted,replacementPlaying,replacementVolume,null);
 }
 Finding observe(long now,String track,String cause,boolean sourcePlaying,
                 boolean nativeMuted,boolean replacementPlaying,float replacementVolume,
                 AudioOwnership.State ownerState) {
  boolean sourceAudibleCommand=sourcePlaying&&!nativeMuted;
  boolean replacementAudibleCommand=replacementPlaying&&replacementVolume>0.001f;
  boolean both=sourceAudibleCommand&&replacementAudibleCommand;
  if(both&&!inOverlap){
   inOverlap=true;
   boolean expected=ownerState==AudioOwnership.State.SAME_SONG_BLEND;
   return new Finding("overlap_commands",track,cause,0,
       expected?"expected_same_song_blend":"unexpected_overlap",expected);
  }
  if(!both)inOverlap=false;
  boolean silence=sourcePlaying&&!sourceAudibleCommand&&!replacementAudibleCommand;
  if(silence){if(!inGap){inGap=true;gapSince=now;gapTrack=track;gapCause=cause;}return null;}
  if(inGap){inGap=false;long duration=Math.max(0,now-gapSince);
   if(duration>=MIN_REPORT_MS)return new Finding("commanded_silence",gapTrack,gapCause,duration,
       "unexpected_commanded_silence",false);
  }
  return null;
 }
 void reset(){inGap=false;inOverlap=false;}
}
