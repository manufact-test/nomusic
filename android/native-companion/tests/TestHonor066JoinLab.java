package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;

/** One production entry policy: complementary linear, phase still unverified. */
public final class TestHonor066JoinLab {
 static int checks;
 static long sourcePosition;
 static void check(boolean yes,String msg){checks++;if(!yes)throw new AssertionError(msg);}
 static ReplacementEngine start()throws Exception{
  TestEngine.reset("ALBUM");
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
 static void unifiedLinearJoin()throws Exception{
  ReplacementEngine e=start();MediaPlayer p=e.player;
  check(e.effect.gain==0f&&e.originalMix==1f,"single entry keeps original audible before decoder grant");
  advance(ReplacementEngine.UNIFIED_JOIN_MS/2);
  check(e.fading&&e.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND,
    "midpoint is an explicitly authorized same-song blend state");
  check(p.volume>0.49f&&p.volume<0.51f&&e.originalMix>0.49f&&e.originalMix<0.51f,
    "unified entry has complementary half gains, not equal-power +3dB");
  check(e.effect.gain< -5f&&e.effect.gain> -7f,
    "source DSP has complementary -6dB commanded gain");
  advance(ReplacementEngine.UNIFIED_JOIN_MS/2+20);
  check(!e.fading&&p.volume==1f&&e.effect.gain==-100f&&e.originalMix==0f,
    "final grant mutes source and enables only replacement");
  e.close();
 }
 static void midJoinBoundaryInvalidatesTicket()throws Exception{
  ReplacementEngine e=start();MediaPlayer p=e.player;
  advance(ReplacementEngine.UNIFIED_JOIN_MS/2);
  e.sourceBoundary("manual_next_during_correlated_join");
  check(p.released&&e.player==null&&e.effect==null&&e.originalMix==1f,
    "Next silences old decoder and restores native output");
  advance(1000);
  check(e.effect==null&&e.player==null,"stale ramp cannot revive a retired song");
  e.close();
 }
 static void midJoinPauseRetainsSource()throws Exception{
  ReplacementEngine e=start();MediaPlayer p=e.player;
  advance(ReplacementEngine.UNIFIED_JOIN_MS/2);
  TestEngine.p.current=TestEngine.source("1",1080,false);
  e.update(TestEngine.p.current);
  check(!e.fading&&p.volume==0f&&e.effect!=null&&e.effect.gain==0f,
    "pause during blend revokes decoder output and restores source gain");
  e.close();
 }
 static void longPauseReattachesWithSameJoin()throws Exception{
  ReplacementEngine e=start();MediaPlayer p=e.player;
  advance(ReplacementEngine.UNIFIED_JOIN_MS+20);
  check(!e.fading&&e.effect!=null&&e.originalMix==0f,
    "initial entry completed before genuine long pause");
  TestEngine.p.current=TestEngine.source("1",sourcePosition,false);
  e.update(TestEngine.p.current);
  SystemClock.now+=ReplacementEngine.PAUSE_GRACE_MS+100;
  TestEngine.p.current=TestEngine.source("1",sourcePosition,false);
  TestEngine.p.handler.drain();
  check(e.effect==null&&!p.playing&&p.volume==0f,
    "long real pause restores original and retires old source DSP effect="+e.effect
      +" playing="+p.playing+" volume="+p.volume+" pauseMode="+e.audioOwner.pauseMode());
  TestEngine.p.current=TestEngine.source("1",sourcePosition,true);
  e.update(TestEngine.p.current);
  check(e.effect!=null&&e.fading&&p.volume==0f,
    "long-pause resume reattaches through the same verified entry, not instant full-volume cut");
  advance(ReplacementEngine.UNIFIED_JOIN_MS/2);
  check(e.fading&&e.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND
      &&p.volume>0.49f&&p.volume<0.51f,
    "reattached long-pause session also uses one complementary linear policy");
  e.close();
 }
 static void detachedLongPauseResyncBeforeJoin()throws Exception{
  ReplacementEngine e=start();MediaPlayer p=e.player;
  advance(ReplacementEngine.UNIFIED_JOIN_MS+20);
  p.position=sourcePosition; // a synchronized decoder before the real pause
  TestEngine.p.current=TestEngine.source("1",sourcePosition,false);
  e.update(TestEngine.p.current);
  p.asyncSeek=true;
  SystemClock.now+=ReplacementEngine.PAUSE_GRACE_MS+5704;
  TestEngine.p.current=TestEngine.source("1",sourcePosition,false);
  TestEngine.p.handler.drain();
  check(e.effect==null&&!p.playing,"35.7s pause releases the native DSP effect");
  int before=p.seekCalls;
  sourcePosition+=132; // HONOR 0.3.69: observed coarse drift on detached resume
  TestEngine.p.current=TestEngine.source("1",sourcePosition,true);
  e.update(TestEngine.p.current);
  check(p.seekCalls==before+1&&e.seeking&&e.effect==null,
    "132ms after detached long pause cannot begin an uncorrected join");
  check(p.volume==0f&&!p.playing&&e.originalMix==1f,
    "original remains audible and replacement silent during resync");
  p.seek.onSeekComplete(p);
  check(!e.seeking&&e.effect!=null&&p.playing&&e.fading,
    "only seek completion authorizes the reattachment");
  advance(ReplacementEngine.UNIFIED_JOIN_MS+20);
  check(!e.fading&&e.effect.gain==-100f&&p.volume==1f,
    "detached resume completes the existing one-mode join");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  unifiedLinearJoin();midJoinBoundaryInvalidatesTicket();midJoinPauseRetainsSource();longPauseReattachesWithSameJoin();detachedLongPauseResyncBeforeJoin();
  System.out.println("PASS: "+checks+" unified HONOR entry and failure-ownership checks");
 }
}
