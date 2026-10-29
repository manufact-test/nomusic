package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;

/** Owner-reported Android regressions: fails on 0.3.47 until the audio ownership design is corrected. */
public final class TestAudioOwnershipRegression {
 static void sample(long position,boolean playing){
  TestEngine.p.current=TestEngine.source("1",position,playing);
  TestEngine.e.update(TestEngine.p.current);
 }
 public static void main(String[] args)throws Exception {
  String failures="";
  TestEngine.playing();
  ReplacementEngine engine=TestEngine.e;
  MediaPlayer player=engine.player;
  SystemClock.now+=180;
  sample(1180,true);
  TestEngine.p.handler.drain();
  if(engine.originalMix>0.05f&&player.volume>0.05f){
   failures+="exclusive_audio: original and replacement simultaneously have positive audible gain ("
    +engine.originalMix+", "+player.volume+"); ";
  }
  engine.close();

  TestEngine.playing();
  engine=TestEngine.e;
  player=engine.player;
  SystemClock.now+=ReplacementEngine.FADE_MS+25;
  sample(1160,true);
  TestEngine.p.handler.drain();
  player.asyncSeek=true;
  sample(61334,true);
  sample(61334,false);
  DynamicsProcessing original=engine.effect;
  SystemClock.now+=2;
  sample(61336,true);
  if(!engine.seeking||engine.pausedAt>=0)throw new AssertionError("precondition not a resumed pending seek");
  // Out-of-order transport snapshot while the prior pause timer remains queued.
  TestEngine.p.current=TestEngine.source("1",61334,false);
  SystemClock.now+=410;
  TestEngine.p.handler.drain();
  if(engine.effect!=original||original.released){
   failures+="stale_pause_timeout: old callback altered effect of resumed in-flight seek; ";
  }
  engine.close();
  if(!failures.isEmpty())throw new AssertionError("0.3.47 known audio regressions: "+failures);
  System.out.println("PASS: exclusive-audio and stale-callback ownership invariants");
 }
}
