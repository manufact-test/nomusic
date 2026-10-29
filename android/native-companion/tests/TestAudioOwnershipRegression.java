package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
/** Release-blocking real-engine checks from 0.3.47 HONOR owner reports. */
public final class TestAudioOwnershipRegression {
 static int checks;
 static void check(boolean ok,String message){checks++;if(!ok)throw new AssertionError(message);}
 static void sample(long pos,boolean playing){TestEngine.p.current=TestEngine.source("1",pos,playing);TestEngine.e.update(TestEngine.p.current);}
 static void assertExclusive(ReplacementEngine e){float source=e.effect==null?1f:e.originalMix;float secondary=e.player==null?0f:e.player.volume;check(AudioOwnership.exclusive(source,secondary),"original/replacement audible at once "+source+"/"+secondary);}
 public static void main(String[] args)throws Exception {
  TestEngine.playing();ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  for(int i=0;i<10;i++){SystemClock.now+=47;sample(1000+i*47,true);TestEngine.p.handler.drain();assertExclusive(e);}
  check(p.volume>0.9f&&e.originalMix==0f,"replacement reached 100% with native audio fully muted");
  e.returnOriginal();for(int i=0;i<10;i++){SystemClock.now+=47;sample(1500+i*47,true);TestEngine.p.handler.drain();assertExclusive(e);}
  check(e.effect==null&&e.player==null,"manual return restored native-only audio");
  e.close();

  // The 0.3.47 pause timer was not invalidated by resume during asynchronous seek.
  TestEngine.playing();e=TestEngine.e;p=e.player;
  SystemClock.now+=ReplacementEngine.FADE_MS+30;sample(1160,true);TestEngine.p.handler.drain();
  p.asyncSeek=true;sample(61334,true);sample(61334,false);
  DynamicsProcessing before=e.effect;long paused=e.pausedAt;
  SystemClock.now+=2;sample(61336,true);
  check(e.seeking&&e.pausedAt<0&&paused>=0,"resumed seek retains its decoder and invalidates pause status");
  // Old/out-of-order transport snapshot arrives while queued Android task runs.
  TestEngine.p.current=TestEngine.source("1",61334,false);
  SystemClock.now+=410;TestEngine.p.handler.drain();
  check(e.effect==before&&!before.released,"a stale pause timer cannot restore native while a new seek owns effect");
  sample(61744,true);p.seek.onSeekComplete(p);
  check(e.player==p&&e.effect==before,"current seek completes without stale effect replacement");
  assertExclusive(e);
  e.close();

  // HONOR 0.3.48: Media3 replayed an old 3648->61334ms seek while the
  // live controller was already at 101197ms. Do not turn it into a new
  // explicit source seek: that would interrupt a correctly aligned decoder.
  check(!SourceTransitionGate.currentPositionSeek(101197,61334),
      "old Media3 seek replay must not force a replacement decoder seek");
  check(SourceTransitionGate.currentPositionSeek(119151,119147),
      "real HONOR seek 119147ms must be accepted");
  check(SourceTransitionGate.currentPositionSeek(157648,157636),
      "real HONOR seek 157636ms must be accepted");
  check(SourceTransitionGate.currentPositionSeek(101197,101197+1500),
      "minor controller clock lag is not a stale event");
  check(!SourceTransitionGate.currentPositionSeek(-1,61334),
      "unknown controller position cannot validate a seek");

  // HONOR 0.3.49: old 99->100 callback arrived while 100 was already playing.
  check(!SourceTransitionGate.currentItemBoundary("100","100","100",false),
      "stale previous-to-current boundary never tears down the active decoder");
  check(!SourceTransitionGate.currentItemBoundary("100","101","100",false),
      "event does not override current controller media item");
  check(SourceTransitionGate.currentItemBoundary("100","101","101",false),
      "real change to new active item still retires previous decoder");
  check(SourceTransitionGate.currentItemBoundary("100","100","100",true),
      "genuine same-track repeat is retained");
  check(!SourceTransitionGate.repeatAtBeginning(0,0,40000),
      "stale zero-position replay when live player at 40s is not a repeat");
  check(SourceTransitionGate.repeatAtBeginning(119500,0,40),
      "real song tail-to-head loop is a repeat");
  // Exercise actual ReplacementEngine, not just the pure seek-position gate.
  // Stale callback must not force a second decoder seek on a short pause/resume
  // when audio is already aligned within 206ms (0.3.48 HONOR timeline).
  TestEngine.playing();e=TestEngine.e;p=e.player;
  SystemClock.now+=ReplacementEngine.FADE_MS+30;sample(1160,true);TestEngine.p.handler.drain();
  p.position=1160;int seeksBeforeStale=p.seekCalls;
  if(SourceTransitionGate.currentPositionSeek(101197,61334))e.sourceSeekRequested();
  sample(1160,false);SystemClock.now+=879;sample(1366,true);
  check(p.seekCalls==seeksBeforeStale+1 && p.position==1366,
      "stale Media3 callback does not trigger a seek; the real 206ms pause offset is corrected once before playback");
  check(e.player==p&&e.effect!=null,
      "the aligned player and verified effect survive stale seek replay");
  e.close();

  // HONOR 0.3.48: a transient non-playing snapshot while seek is in flight
  // clears 'aligned'. Once seek completes at the correct position, do not
  // submit a redundant second MediaPlayer.seekTo just to restore that flag.
  TestEngine.playing();e=TestEngine.e;p=e.player;
  SystemClock.now+=ReplacementEngine.FADE_MS+30;sample(1160,true);TestEngine.p.handler.drain();
  p.asyncSeek=true;sample(60000,true);
  check(e.seeking,"seek in flight before transient native pause");
  sample(60000,false);sample(60000,true);
  int submittedSeekCalls=p.seekCalls;p.seek.onSeekComplete(p);
  check(p.seekCalls==submittedSeekCalls&&!e.seeking,
      "completed aligned seek may not schedule another seek after transient pause");
  check(e.player==p&&e.effect!=null,
      "completed seek keeps original verified effect and decoder alive");
  e.close();

  // Track boundaries must silence any older decoder BEFORE releasing native attenuation.
  TestEngine.playing();e=TestEngine.e;p=e.player;
  SystemClock.now+=ReplacementEngine.FADE_MS+30;sample(1160,true);TestEngine.p.handler.drain();
  e.sourceBoundary("next_track");
  check(p.volume==0f&&!p.playing&&p.released&&e.effect==null,"old decoder cannot overlap the following native track");
  SystemClock.now+=1000;TestEngine.p.handler.drain();check(e.player==null&&e.effect==null,"stale callbacks cannot reanimate the retired track");
  e.close();
  System.out.println("PASS: "+checks+" mandatory exclusive-audio, pause/seek race, boundary ownership checks");
 }
}
