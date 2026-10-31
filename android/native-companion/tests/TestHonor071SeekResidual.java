package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;

/** RED reproduction for the 0.3.71 HONOR residuals (283/330ms).
 * This test deliberately records the current unsafe acceptance as a RED
 * finding while keeping the CI green. Flip the expectation only after an
 * approved fail-open policy passes the full seek/pause/Next matrix.
 * Transport estimates are not speaker waveform measurements.
 */
public final class TestHonor071SeekResidual {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static void start(ReplacementEngine e,MediaPlayer p){
  p.position+=50;SystemClock.now+=50;TestEngine.p.current=TestEngine.source("1",1050,true);e.update(TestEngine.p.current);
  p.position+=600;SystemClock.now+=600;TestEngine.p.current=TestEngine.source("1",1650,true);TestEngine.p.handler.drain();
  check(!e.fading&&p.volume>0.99f&&e.effect!=null&&e.effect.gain==-100f,
    "precondition: replacement owns output after verified initial join");
 }
 static void current350msGateAccepts330msResidual()throws Exception{
  TestStreamingEngine.Buffer partial=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;start(e,p);
  DynamicsProcessing original=e.effect;
  p.asyncSeek=true;e.sourceSeekRequested();TestEngine.p.current=TestEngine.source("1",50000,true);e.update(TestEngine.p.current);
  check(e.seeking&&!p.playing&&p.volume==0f&&original.gain==0f,
    "seek restores original output and keeps replacement silent");
  // Match the reported shape: a slow callback and 330ms residual.
  SystemClock.now+=400;TestEngine.p.current=TestEngine.source("1",50330,true);p.position=50000;p.seek.onSeekComplete(p);
  check(!e.seeking&&e.fading&&e.audioOwner.handoverAwaitingClock()&&p.volume==0f,
    "first gate is muted while decoder clock is not yet advancing");
  // Decoder advances only 40ms; transport residual remains 283ms, below 350ms.
  SystemClock.now+=40;p.position+=40;TestEngine.p.current=TestEngine.source("1",50370,true);
  TestEngine.p.handler.drain();
  check(!e.audioOwner.handoverAwaitingClock()
      &&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT&&p.volume>0.99f
      &&original.gain==-100f,
    "RED reproduced: current 350ms gate grants full replacement with 283ms residual");
  // This is an intentionally documented RED, not an approved audio fix.
  e.close();check(partial.closed&&e.effect==null,"cleanup restores source and closes partial stream");
 }
 static void pauseAndNextStillRevokePendingSlowSeek()throws Exception{
  TestStreamingEngine.Buffer partial=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;start(e,p);p.asyncSeek=true;
  e.sourceSeekRequested();TestEngine.p.current=TestEngine.source("1",70000,true);e.update(TestEngine.p.current);
  SystemClock.now+=311;TestEngine.p.current=TestEngine.source("1",70283,true);p.position=70000;p.seek.onSeekComplete(p);
  check(e.fading&&e.audioOwner.handoverAwaitingClock()&&p.volume==0f,
    "283ms residual enters a muted handover before clock validation");
  TestEngine.p.current=TestEngine.source("1",70283,false);e.update(TestEngine.p.current);
  check(!e.fading&&!p.playing&&e.pausedAt>=0&&p.volume==0f,
    "genuine pause revokes pending handover");
  MediaPlayer.OnSeekCompleteListener stale=p.seek;e.sourceBoundary("manual_next_during_residual_gate");stale.onSeekComplete(p);
  check(p.released&&e.player==null&&e.effect==null&&partial.closed,
    "Next retires old partial decoder/effect and stale ACK cannot revive it");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  current350msGateAccepts330msResidual();pauseAndNextStillRevokePendingSlowSeek();
  System.out.println("PASS: "+checks+" HONOR 0.3.71 RED reproduction + pause/Next safety checks (RED intentionally recorded)");
 }
}
