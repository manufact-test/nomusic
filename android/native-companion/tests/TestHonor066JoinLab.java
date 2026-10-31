package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;

/** Device-facing A/B experiment, never a claim of sample-phase alignment. */
public final class TestHonor066JoinLab {
 static int checks;
 static long sourcePosition;
 static void check(boolean yes,String msg){checks++;if(!yes)throw new AssertionError(msg);}
 static ReplacementEngine start(boolean lab)throws Exception{
  TestEngine.reset("ALBUM");TestEngine.p.correlatedLab=lab;
  sourcePosition=1000;
  ReplacementEngine e=TestEngine.e;e.arm();TestEngine.prepare();
  check(e.fading&&e.effect!=null&&e.player.volume==0f,
    "cold join begins with only original audible");return e;
 }
 static void advance(long elapsed){
  SystemClock.now+=elapsed;
  sourcePosition+=elapsed;
  TestEngine.p.current=TestEngine.source("1",sourcePosition,true);
  TestEngine.p.handler.drain();
 }
 static void labLinearJoin()throws Exception{
  ReplacementEngine e=start(true);MediaPlayer p=e.player;
  check(e.effect.gain==0f&&e.originalMix==1f,"admin lab does not mute before decoder grant");
  advance(ReplacementEngine.CORRELATED_JOIN_LAB_MS/2);
  check(e.fading&&e.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND,
    "midpoint is a separately authorized same-song blend state");
  check(p.volume>0.49f&&p.volume<0.51f&&e.originalMix>0.49f&&e.originalMix<0.51f,
    "correlated linear midpoint has complementary half gains, not equal-power +3dB");
  check(e.effect.gain< -5f&&e.effect.gain> -7f,
    "source DSP has complementary -6dB commanded gain");
  advance(ReplacementEngine.CORRELATED_JOIN_LAB_MS/2+20);
  check(!e.fading&&p.volume==1f&&e.effect.gain==-100f&&e.originalMix==0f,
    "final grant mutes source and enables only replacement");
  e.close();
 }
 static void defaultRemainsExclusive()throws Exception{
  ReplacementEngine e=start(false);MediaPlayer p=e.player;
  advance(ReplacementEngine.COLD_JOIN_DIP_MS/2);
  check(p.volume==0f&&e.effect.gain==-100f,
    "unselected admin experiment cannot silently change release-safe default");
  advance(ReplacementEngine.COLD_JOIN_DIP_MS/2+20);
  check(p.volume==1f&&e.effect.gain==-100f,"default completes exclusive handover");
  e.close();
 }
 static void midJoinBoundaryInvalidatesTicket()throws Exception{
  ReplacementEngine e=start(true);MediaPlayer p=e.player;
  advance(ReplacementEngine.CORRELATED_JOIN_LAB_MS/2);
  e.sourceBoundary("manual_next_during_correlated_join");
  check(p.released&&e.player==null&&e.effect==null&&e.originalMix==1f,
    "Next silences old decoder and restores native output");
  advance(1000);
  check(e.effect==null&&e.player==null,"stale ramp cannot revive a retired song");
  e.close();
 }
 static void midJoinPauseRetainsSource()throws Exception{
  ReplacementEngine e=start(true);MediaPlayer p=e.player;
  advance(ReplacementEngine.CORRELATED_JOIN_LAB_MS/2);
  TestEngine.p.current=TestEngine.source("1",1080,false);
  e.update(TestEngine.p.current);
  check(!e.fading&&p.volume==0f&&e.effect!=null&&e.effect.gain==0f,
    "pause during blend revokes decoder output and restores source gain");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  labLinearJoin();defaultRemainsExclusive();midJoinBoundaryInvalidatesTicket();midJoinPauseRetainsSource();
  System.out.println("PASS: "+checks+" HONOR A/B correlated join lab and failure-ownership checks");
 }
}
