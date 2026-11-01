package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;

/** Replay 0.3.73 HONOR cold-join drift and bounded silent fallback.
 * Transport clock alignment is NOT acoustic/PCM phase verification.
 */
public final class TestHonor074StrictJoin {
 static int checks;
 static void check(boolean yes,String why){checks++;if(!yes)throw new AssertionError(why);}
 static void source(long pos){TestEngine.p.current=TestEngine.source("1",pos,true);}
 static void leadBoundaries(){
  check(ReplacementEngine.predictedWarmLeadMs(0)==70,"unknown latency uses conservative bounded lead");
  check(ReplacementEngine.predictedWarmLeadMs(111)==151,"HONOR 111ms ACK predicts a 151ms lead");
  check(ReplacementEngine.predictedWarmLeadMs(182)==222,"HONOR 182ms warm ACK updates lead");
  check(ReplacementEngine.predictedWarmLeadMs(635)==250,"HONOR 635ms range wait cannot overshoot more than 250ms");
  check(ReplacementEngine.predictedWarmTargetMs(1000,182,120000)==1222,"predictive warm target is absolute");
  check(ReplacementEngine.predictedWarmTargetMs(119800,635,120000)==119849,"tail clamp keeps decoder inside duration");
 }
 static void realEngineRejoinsAfterSilentCorrection()throws Exception {
  TestStreamingEngine.Buffer buffer=TestStreamingEngine.start();
  ReplacementEngine engine=TestEngine.e;MediaPlayer player=engine.player;
  int initialSeeks=player.seekCalls;
  // 0.3.73 observed 115..344ms source-vs-decoder transport drift at cold entry.
  SystemClock.now+=180;player.position+=40;source(1180);
  TestEngine.p.handler.drain();
  check(engine.fading&&player.seekCalls==initialSeeks+1,
      "140ms startup drift triggers ONE muted warm correction before any blend");
  check(engine.effect!=null&&engine.effect.gain==0f&&player.volume==0f,
      "original remains fully audible while correcting replacement decoder");
  check(player.position>1180&&player.position<=1430,
      "warm seek targets predicted source future rather than late current position");
  // The real decoder advances only after the warm ACK, never trust ACK alone.
  SystemClock.now+=65;player.position+=65;source(1245);
  TestEngine.p.handler.drain();
  check(engine.fading&&engine.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND,
      "one bounded seek permits the existing complementary entry only after clock progress");
  SystemClock.now+=90;player.position+=90;source(1335);TestEngine.p.handler.drain();
  check(player.volume>0f&&player.volume<1f&&engine.originalMix>0f,
      "the same single join ramp retains complementary gains");
  SystemClock.now+=90;player.position+=90;source(1425);TestEngine.p.handler.drain();
  check(!engine.fading&&player.volume>0.99f&&engine.effect.gain==-100f,
      "cleanly aligned stream reaches exclusive replacement without a second mode");
  engine.close();
 }
 static void twoCorrectionsCannotLoop()throws Exception {
  TestStreamingEngine.Buffer buffer=TestStreamingEngine.start();
  ReplacementEngine engine=TestEngine.e;MediaPlayer player=engine.player;
  int initialSeeks=player.seekCalls;
  SystemClock.now+=180;player.position+=40;source(1180);TestEngine.p.handler.drain();
  check(player.seekCalls==initialSeeks+1&&player.volume==0f,
      "first drift correction is issued silently");
  SystemClock.now+=60;player.position+=40;source(2000);TestEngine.p.handler.drain();
  check(player.seekCalls==initialSeeks+2&&player.volume==0f&&engine.effect.gain==0f,
      "second correction still leaves original fully audible");
  SystemClock.now+=60;player.position+=40;source(3000);TestEngine.p.handler.drain();
  check(player.seekCalls==initialSeeks+2&&engine.player==null
      &&engine.effect==null&&engine.completedKey!=null,
      "third mismatch falls back to original instead of looping indefinitely");
  engine.close();
 }
 static void unresponsiveWarmSeekNeverMutesOriginal()throws Exception {
  TestStreamingEngine.Buffer buffer=TestStreamingEngine.start();
  ReplacementEngine engine=TestEngine.e;MediaPlayer player=engine.player;
  player.asyncSeek=true;int initialSeeks=player.seekCalls;
  SystemClock.now+=200;player.position+=40;source(1200);TestEngine.p.handler.drain();
  check(player.seekCalls==initialSeeks+1&&engine.audioOwner.seekInFlight(player),
      "slow warm ACK is fenced by one decoder ticket");
  check(player.volume==0f&&engine.effect!=null&&engine.effect.gain==0f,
      "original audible, replacement silent during pending warm ACK");
  SystemClock.now+=ReplacementEngine.STRICT_JOIN_BUDGET_MS+5;source(4205);
  TestEngine.p.handler.drain();
  check(engine.player==null&&engine.effect==null&&engine.armed()
      &&engine.completedKey!=null,
      "bounded gate failure restores original and skips this track");
  int resolves=TestEngine.api.resolves;
  engine.update(TestEngine.p.current);
  check(engine.player==null&&TestEngine.api.resolves==resolves,
      "fallback cannot oscillate or retry this same track");
  engine.close();
 }
 public static void main(String[] args)throws Exception {
  leadBoundaries();realEngineRejoinsAfterSilentCorrection();
  twoCorrectionsCannotLoop();unresponsiveWarmSeekNeverMutesOriginal();
  System.out.println("PASS: "+checks+" HONOR 0.3.74 strict transport gate and bounded original fallback");
 }
}
