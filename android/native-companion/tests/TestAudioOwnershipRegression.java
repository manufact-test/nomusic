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
