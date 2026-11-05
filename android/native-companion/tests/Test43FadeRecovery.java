package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;
import java.io.File;

/** Replays the real Test.42 failure shape: an active blend aborts, then retries. */
public final class Test43FadeRecovery {
 static int checks;
 static void check(boolean good,String message){checks++;if(!good)throw new AssertionError(message);}

 static void failedBlendFallsBackOnSameTrack()throws Exception{
  TestEngine.reset("ALBUM",true);
  ReplacementEngine e=TestEngine.e;
  e.adaptiveJoinExperiment=true;e.arm();
  TestEngine.api.resolved.done(TestEngine.found(),null);
  File audio=File.createTempFile("celikom-43-failed-blend-", ".audio");
  TestEngine.api.downloaded.done(audio,null);
  MediaPlayer decoder=e.player;
  decoder.prepared.onPrepared(decoder);
  TestCachedAudioRollback.advanceWarmup(decoder,10,20,8);
  TestCachedAudioRollback.advanceTogether(decoder,5,20);
  check(e.fading&&e.effect!=null&&e.originalMix<1f,
    "first attempt begins an audible handover");
  e.effect.control=false; // Reproduce an interrupted source-effect command.
  TestCachedAudioRollback.advanceTogether(decoder,1,20);
  check(!e.fading&&e.effect==null&&e.player==null,
    "exception must silence decoder and restore the original");
  check(e.armed()&&e.completedKey==null&&e.joinRetryPreferBaseline,
    "the original remains audible and the same track is eligible for a safe retry");
  check(e.recentAudio.containsValue(audio)&&audio.isFile(),
    "a ready local file survives a failed fade, avoiding another download");
  check(e.nextLookup-SystemClock.now==1200&&e.joinRetryAttempts==1,
    "the first fade failure retries after 1.2s, not the former fixed 5s");
  check(LogStore.events.contains("replacement_join_exception")
    &&LogStore.events.contains("replacement_join_guard_fallback"),
    "failure stage and baseline retry are visible to the next diagnosis");
  check(JoinTransitionPolicy.durationMs(0,10,true)==160
    &&JoinTransitionPolicy.durationMs(0,10,false)==220,
    "only the retry forces the older 160ms transition");

  SystemClock.now=e.nextLookup;
  TestEngine.p.current=TestEngine.source("1",2200,true);
  int before=TestEngine.api.resolves;
  e.update(TestEngine.p.current);
  check(TestEngine.api.resolves==before+1,"retry re-resolves the unchanged song");
  int downloads=TestEngine.api.downloads;
  TestEngine.api.resolved.done(TestEngine.found(),null);
  check(TestEngine.api.downloads==downloads,
    "fresh authorized resolve reuses the verified local file without network fetch");
  MediaPlayer retryDecoder=e.player;
  retryDecoder.prepared.onPrepared(retryDecoder);
  TestCachedAudioRollback.advanceWarmup(retryDecoder,10,20,8);
  TestCachedAudioRollback.advanceTogether(retryDecoder,10,20);
  check(!e.fading&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
    "fallback entry eventually completes with current audio ownership");
  check(e.joinRetryAttempts==0&&!e.joinRetryPreferBaseline&&e.joinRetryKey==null,
    "success clears the one-song fallback policy");
  e.close();
 }

 static void repeatedFailureIsBounded(){
  TestEngine.reset("ALBUM",true);
  ReplacementEngine e=TestEngine.e;
  e.adaptiveJoinExperiment=true;e.arm();
  e.recoverFailedJoin(new IllegalStateException("same-song blend lacks verified current owner"),
    "same_song_mix",220,0.88f);
  check(e.joinRetryAttempts==1&&e.nextLookup-SystemClock.now==1200,
    "first failure gets a short recovery window");
  e.recoverFailedJoin(new IllegalStateException("same-song blend lacks verified current owner"),
    "same_song_mix",160,0.88f);
  check(e.joinRetryAttempts==2&&e.nextLookup-SystemClock.now==2400,
    "repeat failure backs off rather than hammering the effect");
  e.close();
 }

 public static void main(String[] args)throws Exception{
  failedBlendFallsBackOnSameTrack();
  repeatedFailureIsBounded();
  System.out.println("PASS: "+checks+" Test.43 fade fault, original restoration and safe same-track fallback");
 }
}
