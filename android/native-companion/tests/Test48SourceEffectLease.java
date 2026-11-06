package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;

/** Test-only field candidate: verified source DSP survives a SAME-session Next. */
public final class Test48SourceEffectLease {
 static int checks;
 static void check(boolean value,String description){checks++;if(!value)throw new AssertionError(description);}

 static ReplacementEngine firstSong()throws Exception{
  TestEngine.reset("ALBUM",true);
  ReplacementEngine e=TestEngine.e;
  e.retainSessionEffectBetweenTracksExperiment=true;
  e.lateSourceEffectAttachExperiment=true;
  e.arm();
  MediaPlayer first=TestEngine.prepare();
  TestCachedAudioRollback.advanceWarmup(first,10,20,8);
  TestCachedAudioRollback.advanceTogether(first,10,20);
  check(e.effect!=null&&e.effect.gain==-100f&&first.volume>0.99f,
    "first song owns exclusive replacement; source verified and muted");
  return e;
 }

 static void nextReusesOneSessionEffect()throws Exception{
  ReplacementEngine e=firstSong();
  DynamicsProcessing original=e.effect;
  int created=DynamicsProcessing.constructionCount;
  e.sourceBoundary("manual_next","2");
  check(e.effect==null&&e.parkedSourceEffect==original&&!original.released
     &&original.getEnabled()&&original.gain==0f,
     "source is audible at unity while old effect remains parked");
  check(e.player==null&&e.audioOwner.state()==AudioOwnership.State.SOURCE_ONLY,
     "old decoder lease is retired before next identity");
  TestEngine.p.current=TestEngine.source("2",1000,true);
  e.identity(LogStore.map("mediaAlias","2","albumId","42","title","Песня",
    "artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","8","method","ALBUM","editionConflict",false));
  check(e.parkedSourceEffect==original,
    "new source identity does not force another native effect allocation");
  MediaPlayer second=TestEngine.prepare();
  TestCachedAudioRollback.advanceWarmup(second,10,20,8);
  TestCachedAudioRollback.advanceTogether(second,10,20);
  check(e.effect==original&&e.parkedSourceEffect==null&&!original.released,
    "clock-verified new song reuses the same source effect safely");
  check(DynamicsProcessing.constructionCount==created
     &&LogStore.events.contains("replacement_source_effect_reused"),
     "no second source DSP construction or engine restart at Next");
  check(second.volume>0.99f&&original.gain==-100f,
    "same exclusive join and correct attenuation after reuse");
  e.close();
  check(original.released,"closing Test releases the reused effect");
 }

 static void timeoutCannotLeaveUnownedEffect()throws Exception{
  ReplacementEngine e=firstSong();DynamicsProcessing original=e.effect;
  e.sourceBoundary("natural_next","2");
  SystemClock.now+=ReplacementEngine.SOURCE_EFFECT_PARK_MS+1;
  TestEngine.p.handler.drain();
  check(e.parkedSourceEffect==null&&original.released&&original.gain==0f,
    "park expires even when no next approved replacement is available");
  e.close();
 }

 static void stopNeverParksEffect()throws Exception{
  ReplacementEngine e=firstSong();DynamicsProcessing original=e.effect;
  e.stop("owner_return_original");
  check(original.released&&e.parkedSourceEffect==null,
    "stop and manual original path always retire the DSP");
 }

 static void sessionChangeForcesFreshEffect()throws Exception{
  ReplacementEngine e=firstSong();DynamicsProcessing original=e.effect;
  e.sourceBoundary("manual_next","2");
  e.trustedSession++;
  TestEngine.p.current=TestEngine.source("2",1000,true);
  e.identity(LogStore.map("mediaAlias","2","albumId","42","title","Песня",
    "artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","8","method","ALBUM","editionConflict",false));
  MediaPlayer second=TestEngine.prepare();
  TestCachedAudioRollback.advanceWarmup(second,10,20,8);
  TestCachedAudioRollback.advanceTogether(second,10,20);
  check(original.released&&e.effect!=original,
    "verified session mismatch must never inherit the previous effect");
  e.close();
 }

 public static void main(String[] args)throws Exception{
  nextReusesOneSessionEffect();
  timeoutCannotLeaveUnownedEffect();
  stopNeverParksEffect();
  sessionChangeForcesFreshEffect();
  System.out.println("PASS: "+checks+" Test.48 source effect session reuse, expiry, stop, session guard");
 }
}
