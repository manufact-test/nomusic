package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;

/** Replays the 0.3.66 HONOR ordering: decoder seek completion and muted
 * handover startup precede a short Media3 BUFFERING/READY pulse. The one
 * production entry mode must preserve this independent seek path.
 */
public final class TestHonor066SeekBufferReplay {
 static int checks;
 static void check(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
 static void source(long position,boolean playing){
  TestEngine.p.current=playing?TestEngine.source("1",position,true):TestEngine.buffering(position);
 }
 static void advance(long ms,long position){
  SystemClock.now+=ms;source(position,true);TestEngine.p.handler.drain();
 }
 static void postSeekReadyBuffer()throws Exception{
  TestStreamingEngine.Buffer partial=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;
  MediaPlayer p=e.player;
  // Complete the cold join with an advancing, still-incomplete stream.
  p.position+=50;advance(50,1050);
  p.position+=600;advance(600,1650);
  check(!partial.complete()&&!e.fading&&p.volume>0.99f,
    "partial-stream cold join finishes in the single production mode");

  p.asyncSeek=true;
  e.sourceSeekRequested();source(30000,true);e.update(TestEngine.p.current);
  check(e.seeking&&p.volume==0f&&e.effect.gain==0f,
    "seek restores the audible original before waiting for decoder");
  SystemClock.now+=35;source(30035,true);p.seek.onSeekComplete(p);
  check(!e.seeking&&e.fading&&e.audioOwner.handoverAwaitingClock()
      &&p.playing&&p.volume==0f,
    "decoder seek finished, but verified advancement still gates handover");

  SystemClock.now+=8;source(30035,false);e.update(TestEngine.p.current);
  check(e.pausedAt<0&&e.fading&&e.audioOwner.handoverAwaitingClock()
      &&p.playing&&p.volume==0f&&e.effect.gain==0f,
    "RED 0.3.66: short READY/BUFFERING reorder must not revoke the muted handover");
  // Runnable must remain live while buffering, and resume from the same ticket.
  SystemClock.now+=20;TestEngine.p.handler.drain();
  check(e.pausedAt<0&&e.fading&&p.volume==0f,
    "buffer frame must neither restart decoder nor expose secondary audio");
  source(30055,true);e.update(TestEngine.p.current);
  p.position+=90;advance(90,30145);
  check(!e.fading&&e.pausedAt<0&&p.volume>0.99f&&e.effect.gain==-100f
      &&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
    "single resumed alignment grants exclusive replacement");
  e.close();
 }
 static ReplacementEngine pendingMutedSeek()throws Exception{
  TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;
  MediaPlayer p=e.player;
  p.position+=50;advance(50,1050);
  p.position+=600;advance(600,1650);
  p.asyncSeek=true;e.sourceSeekRequested();source(30000,true);e.update(TestEngine.p.current);
  SystemClock.now+=35;source(30035,true);p.seek.onSeekComplete(p);
  check(e.fading&&e.audioOwner.handoverAwaitingClock()&&p.volume==0f,
    "setup: muted seek handover is awaiting its live decoder clock");
  SystemClock.now+=8;source(30035,false);e.update(TestEngine.p.current);
  check(e.fading&&e.pausedAt<0,"setup: transient BUFFERING retains the handover");
  return e;
 }
 static void longBufferFallsBack()throws Exception{
  ReplacementEngine e=pendingMutedSeek();MediaPlayer p=e.player;
  SystemClock.now+=350;source(30035,false);e.update(TestEngine.p.current);
  check(!e.fading&&e.pausedAt>=0&&!p.playing&&p.volume==0f,
    "a genuine long BUFFERING interval revokes handover and pauses decoder");
  check(e.effect!=null&&e.effect.gain==0f,
    "long buffer leaves original restored and same effect retained");
  SystemClock.now+=350;TestEngine.p.handler.drain();
  check(e.player==p&&!p.released&&e.pausedAt>=0,
    "stale held-ramp callback cannot revive the decoder through long buffering");
  e.close();
 }
 static void pauseOrNextRevokesHold()throws Exception{
  ReplacementEngine e=pendingMutedSeek();MediaPlayer p=e.player;
  TestEngine.p.current=TestEngine.source("1",30035,false);e.update(TestEngine.p.current);
  check(!e.fading&&!p.playing&&e.pausedAt>=0&&p.volume==0f,
    "real user pause interrupts held seek handover immediately");
  e.close();
  e=pendingMutedSeek();p=e.player;
  e.sourceBoundary("next_during_short_buffer");
  check(p.released&&e.player==null&&e.effect==null,
    "manual Next retires old decoder and restores native output immediately");
  SystemClock.now+=1500;TestEngine.p.handler.drain();
  check(e.player==null&&e.effect==null,
    "retired short-buffer ramp never grants stale audio on the next track");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  postSeekReadyBuffer();
  longBufferFallsBack();
  pauseOrNextRevokesHold();
  System.out.println("PASS: "+checks+" HONOR 0.3.66 short Media3 buffering-after-seek handover checks");
 }
}
