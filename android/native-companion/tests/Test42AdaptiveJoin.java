package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;
import org.json.JSONObject;
import java.io.File;

/** Test.42: smooth command steps, boosted-track gain and recoverable guard. */
public final class Test42AdaptiveJoin {
 static int checks;
 static void check(boolean good,String why){checks++;if(!good)throw new AssertionError(why);}

 static void boundedMixAndClockPolicy(){
  check(JoinTransitionPolicy.durationMs(0,10)==220,"near-zero drift uses gentle transition");
  check(JoinTransitionPolicy.durationMs(42,10)==190,"moderate offset shortens uncertain overlap");
  check(JoinTransitionPolicy.durationMs(90,10)==140,"large offset does not sustain long overlapping editions");
  check(JoinTransitionPolicy.durationMs(0,500)==160,"stale source observation never claims reliable phase");
  float last=0f;
  for(int i=0;i<7;i++){
   float next=JoinTransitionPolicy.boundedMix(800,140,last);
   check(next>=last&&next-last<=0.16001f,"late handler tick is gain-step limited");
   last=next;
  }
  check(last==1f,"catch-up ramp finishes in bounded ticks");
  check(JoinTransitionPolicy.retryMs(1)==1200&&JoinTransitionPolicy.retryMs(2)==2400
    &&JoinTransitionPolicy.retryMs(5)==9600,"guard backoff bounded by 9.6 seconds");
 }

 static void sameTrackRecoverable(){
  TestEngine.reset("ALBUM",true);
  ReplacementEngine e=TestEngine.e;
  e.adaptiveJoinExperiment=true;e.arm();
  e.skipUnstableJoin("join_alignment_unstable",180,2);
  check(e.armed()&&e.player==null&&e.effect==null&&e.completedKey==null,
    "failed alignment keeps original, releases effects, and does not condemn whole song");
  check(e.joinRetryAttempts==1&&e.nextLookup-SystemClock.now==1200,
    "first failed join schedules a short same-song retry");
  long time=e.nextLookup;int before=TestEngine.api.resolves;
  SystemClock.now=time;TestEngine.p.current=TestEngine.source("1",2200,true);
  e.update(TestEngine.p.current);
  check(TestEngine.api.resolves==before+1,"same song re-resolves without Next or manual activation");
  e.skipUnstableJoin("decoder_start_timeout",75,1);
  check(e.joinRetryAttempts==2&&e.nextLookup-SystemClock.now==2400,
    "a second unstable attempt retries with longer delay, never a permanent skip");
  e.close();
 }

 static void boostedJoinDoesNotJumpAtEnd()throws Exception{
  TestEngine.reset("ALBUM",true);
  ReplacementEngine e=TestEngine.e;
  e.adaptiveJoinExperiment=true;e.arm();
  JSONObject approved=TestEngine.found().put("gain_db",6);
  TestEngine.api.resolved.done(approved,null);
  File audio=File.createTempFile("celikom-42-boost-", ".audio");
  TestEngine.api.downloaded.done(audio,null);
  MediaPlayer decoder=e.player;decoder.prepared.onPrepared(decoder);
  TestCachedAudioRollback.advanceWarmup(decoder,10,20,8);
  TestCachedAudioRollback.advanceTogether(decoder,5,20);
  check(e.fading&&e.loudness!=null&&e.loudness.enabled
    &&e.loudness.gain>0&&e.loudness.gain<600,
    "boost is already ramping while both outputs are crossfading");
  TestCachedAudioRollback.advanceTogether(decoder,20,20);
  check(!e.fading&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT
    &&e.loudness.gain==600&&decoder.volume>0.99f,
    "boost reaches its final level before the handover completes");
  check(e.joinRetryAttempts==0,"successful transition clears same-track failure backoff");
  e.close();
 }

 public static void main(String[]args)throws Exception{
  boundedMixAndClockPolicy();sameTrackRecoverable();boostedJoinDoesNotJumpAtEnd();
  System.out.println("PASS: "+checks+" Test.42 bounded gain, same-track retry and boosted fade");
 }
}
