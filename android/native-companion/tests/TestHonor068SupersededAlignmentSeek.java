package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;

/** Regression for a newer Media3 source seek arriving while an older native
 * ALIGNMENT seek is still awaiting its untagged MediaPlayer callback. */
public final class TestHonor068SupersededAlignmentSeek {
 static int checks;
 static void check(boolean yes,String message){checks++;if(!yes)throw new AssertionError(message);}
 static void ready(long position){TestEngine.p.current=TestEngine.source("1",position,true);}
 static TestStreamingEngine.Buffer pendingInitialAlignment()throws Exception{
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;TestEngine.e.arm();TestEngine.resolve();
  TestStreamingEngine.Buffer audio=new TestStreamingEngine.Buffer();
  TestEngine.api.streamed.done(audio,null);
  MediaPlayer player=TestEngine.e.player;player.asyncSeek=true;player.prepared.onPrepared(player);
  return audio;
 }
 static void media3DiscontinuitiesSupersedeColdAlignment()throws Exception{
  TestStreamingEngine.Buffer audio=pendingInitialAlignment();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;DynamicsProcessing fx=e.effect;
  check(e.seeking&&e.audioOwner.seekInFlight(p)&&p.seekCalls==1,
    "cold stream alignment owns exactly one pending native seek");
  long operation=e.audioOwner.operationEpoch();
  e.sourceSeekRequested();ready(36000);e.update(TestEngine.p.current);
  check(e.seekRetargetPending&&e.audioOwner.operationEpoch()==operation+1
      &&e.audioOwner.seekInFlight(p)&&p.seekCalls==1&&p.volume==0f
      &&e.effect==fx&&fx.gain==0f,
    "first Media3 seek revokes old ticket but preserves one native callback and audible source");
  long supersededOperation=e.audioOwner.operationEpoch();
  e.sourceSeekRequested();ready(86000);e.update(TestEngine.p.current);
  check(e.audioOwner.operationEpoch()==supersededOperation&&e.seekRetargetPending
      &&e.audioOwner.seekInFlight(p)&&p.seekCalls==1,
    "additional finger seeks coalesce without repeatedly invalidating or issuing native seeks");
  SystemClock.now+=1173;ready(87000);p.seek.onSeekComplete(p);
  check(p.seekCalls==2&&e.seeking&&e.audioOwner.seekInFlight(p)
      &&e.audioOwner.inFlightTargetMs(p)==87000&&!e.seekRetargetPending
      &&!e.explicitSourceSeek&&p.volume==0f&&e.effect==fx&&fx.gain==0f,
    "superseded callback drains silently and exactly one seek targets the latest source position");
  e.close();
 }
 static void pollingDetectedJumpAlsoSupersedes()throws Exception{
  TestStreamingEngine.Buffer audio=pendingInitialAlignment();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  long operation=e.audioOwner.operationEpoch();
  e.previousSource=TestEngine.source("1",1000,true);
  ready(36000);e.update(TestEngine.p.current);
  check(e.seekRetargetPending&&e.audioOwner.operationEpoch()==operation+1
      &&e.audioOwner.seekInFlight(p)&&p.seekCalls==1,
    "polling-detected source discontinuity also invalidates the old alignment ticket");
  SystemClock.now+=1173;ready(37000);p.seek.onSeekComplete(p);
  check(p.seekCalls==2&&e.seeking&&e.audioOwner.inFlightTargetMs(p)==37000
      &&p.volume==0f&&e.effect!=null&&e.effect.gain==0f,
    "polling fallback issues one current-position seek after the old callback");
  e.close();
 }
 static void alreadyAlignedRetargetDoesNotSeekAgain()throws Exception{
  TestStreamingEngine.Buffer audio=pendingInitialAlignment();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;int issued=p.seekCalls;
  e.sourceSeekRequested();ready(1000);e.update(TestEngine.p.current);
  SystemClock.now+=10;ready(1010);p.seek.onSeekComplete(p);
  check(p.seekCalls==issued&&!e.seeking&&!e.seekRetargetPending&&!e.explicitSourceSeek,
    "a superseded callback already within the strict pause-position tolerance is reused without a duplicate seek");
  check(e.player==p&&e.effect!=null&&p.volume==0f&&e.effect.gain==0f,
    "nearby retarget still remains muted until the normal decoder-clock handover gate");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  media3DiscontinuitiesSupersedeColdAlignment();
  pollingDetectedJumpAlsoSupersedes();
  alreadyAlignedRetargetDoesNotSeekAgain();
  System.out.println("PASS: "+checks+" HONOR 0.3.84 superseded alignment seek checks");
 }
}
