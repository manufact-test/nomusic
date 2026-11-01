package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;

/** Device-derived HONOR 0.3.74 regression: ALIGNMENT ACK latency is not
 * a predictor for subsequent WARM decoder seeks (actual WARM: 40..155ms).
 * No PCM output or phase measurement is inferred from transport clocks.
 */
public final class TestHonor075WarmLatency {
 static int checks;
 static void check(boolean yes,String why){checks++;if(!yes)throw new AssertionError(why);}
 static void source(long ms){TestEngine.p.current=TestEngine.source("1",ms,true);}
 static void replay(int alignmentAckMs,int warmAckMs)throws Exception{
  TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  SystemClock.now+=50;p.position+=50;source(1050);TestEngine.p.handler.drain();
  SystemClock.now+=600;p.position+=600;source(1650);TestEngine.p.handler.drain();
  check(!e.fading&&p.volume==1f&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
      "setup: partial stream is playing on exclusive replacement");
  p.asyncSeek=true;int before=p.seekCalls;
  e.sourceSeekRequested();source(50000);e.update(TestEngine.p.current);
  check(e.seeking&&p.seekCalls==before+1&&e.effect.gain==0f&&p.volume==0f,
      "finger seek leaves the original audible during first alignment");
  SystemClock.now+=alignmentAckMs;source(50000+alignmentAckMs);p.seek.onSeekComplete(p);
  check(!e.seeking&&p.playing&&e.effect.gain==0f&&p.volume==0f,
      "original alignment ACK must not grant an audible decoder");
  SystemClock.now+=110;p.position+=110;source(50110+alignmentAckMs);
  TestEngine.p.handler.drain();
  long expected=50110+alignmentAckMs+ReplacementEngine.WARM_CALLBACK_LEAD_MS;
  check(p.seekCalls==before+2&&p.position==expected
      &&e.fading&&e.effect.gain==0f&&p.volume==0f,
      "slow "+alignmentAckMs+"ms ACK must not add 250ms to the following warm target");
  SystemClock.now+=warmAckMs;source(50110+alignmentAckMs+warmAckMs);
  p.seek.onSeekComplete(p);
  check(!e.audioOwner.seekInFlight(p)&&p.volume==0f&&e.effect.gain==0f,
      "warm ACK is still not an output permission");
  SystemClock.now+=60;p.position+=60;source(50170+alignmentAckMs+warmAckMs);
  TestEngine.p.handler.drain();
  check(p.seekCalls==before+2&&!e.fading&&p.volume==1f
      &&e.effect.gain==-100f&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
      "observed "+warmAckMs+"ms warm ACK must settle with ONE correction, never reverse");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  check(ReplacementEngine.WARM_CALLBACK_LEAD_MS==70,
      "HONOR warm callback median is about 60..80ms, independently of slow HTTP alignment");
  for(int rtt:new int[]{40,45,59,63,76,82,132,146,155})
   check(Math.abs(rtt-ReplacementEngine.WARM_CALLBACK_LEAD_MS)<=100,
       "every 0.3.74 HONOR warm latency fits one 100ms transport gate");
  replay(207,76);
  replay(254,40);
  replay(179,155);
  System.out.println("PASS: "+checks+
      " HONOR 0.3.75 warm-specific latency, no oversized lead, single retained handover");
 }
}
