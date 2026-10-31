package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;

/** Actual-engine replay of HONOR 0.3.67 partial HTTP stream on cellular+VPN.
 * The first decoder seek waited 2792ms while Media3 advanced through two
 * further finger positions; later decoder callbacks needed 933ms and 17ms.
 * Positions are scaled inside the 120s fake fixture (the HONOR real song was
 * longer), but the callback timings and ownership ordering are preserved.
 * Original output must remain audible via the SAME verified full-gain effect
 * through the entire superseded seek, without a second DSP attach.
 */
public final class TestHonor067SlowStreamSeek {
 static int checks;
 static void check(boolean yes,String message){checks++;if(!yes)throw new AssertionError(message);}
 static void ready(long position){TestEngine.p.current=TestEngine.source("1",position,true);}
 static void startPlayback(ReplacementEngine e,MediaPlayer p){
  SystemClock.now+=50;p.position+=50;ready(1050);TestEngine.p.handler.drain();
  SystemClock.now+=600;p.position+=600;ready(1650);TestEngine.p.handler.drain();
  check(!e.fading&&p.volume>0.99f&&e.effect.gain==-100f,"partial stream initially owns replacement output");
 }
 static void slowSourceRetargetingRetainsEffect()throws Exception{
  TestStreamingEngine.Buffer incomplete=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  startPlayback(e,p);
  DynamicsProcessing originalEffect=e.effect;
  int initialSeekCalls=p.seekCalls; // Initial cold alignment is also a native seek.
  p.asyncSeek=true;e.sourceSeekRequested();ready(22000);e.update(TestEngine.p.current);
  check(e.seeking&&p.volume==0f&&originalEffect.gain==0f&&!p.playing,
    "first user seek restores original and silences secondary");
  incomplete.waiting=true;
  SystemClock.now+=350;ready(22350);e.update(TestEngine.p.current);
  check(e.effect==originalEffect&&!originalEffect.released&&originalEffect.gain==0f,
    "RED 0.3.67: a stalled network read must not retire the full-gain source effect");

  // Source emits two more position discontinuities before the untagged ACK.
  SystemClock.now+=1293;e.sourceSeekRequested();ready(60000);e.update(TestEngine.p.current);
  SystemClock.now+=1136;e.sourceSeekRequested();ready(100000);e.update(TestEngine.p.current);
  SystemClock.now+=13;ready(100013);p.seek.onSeekComplete(p);
  check(p.seekCalls==initialSeekCalls+2&&e.seeking&&p.volume==0f&&e.effect==originalEffect,
    "2792ms ACK must target latest position: calls="+p.seekCalls+" seeking="+e.seeking+
       " effectRetained="+(e.effect==originalEffect)+" volume="+p.volume+
       " position="+p.position+" source="+TestEngine.p.current.position);
  SystemClock.now+=933;ready(100946);p.seek.onSeekComplete(p);
  check(p.seekCalls==initialSeekCalls+3&&e.seeking&&e.effect==originalEffect,
    "933ms residual correction stays off-output and keeps the same DSP session");
  incomplete.waiting=false;
  SystemClock.now+=17;ready(100963);p.seek.onSeekComplete(p);
  check(p.seekCalls==initialSeekCalls+3&&!e.seeking&&p.playing&&e.effect==originalEffect
      &&originalEffect.gain==0f&&p.volume==0f,
    "17ms final ACK starts only a muted clock-verification handover");
  SystemClock.now+=90;p.position+=90;ready(101053);TestEngine.p.handler.drain();
  check(e.effect==originalEffect&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT
      &&p.volume>0.99f&&originalEffect.gain==-100f,
    "one verified exclusive handover, without recreating the source effect");
  e.close();
 }
 static void realPauseAndNextOverrideSlowSeek()throws Exception{
  TestStreamingEngine.Buffer incomplete=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;startPlayback(e,p);
  p.asyncSeek=true;e.sourceSeekRequested();ready(50000);e.update(TestEngine.p.current);
  incomplete.waiting=true;SystemClock.now+=350;ready(50350);e.update(TestEngine.p.current);
  DynamicsProcessing retained=e.effect;
  TestEngine.p.current=TestEngine.source("1",50350,false);e.update(TestEngine.p.current);
  check(!p.playing&&p.volume==0f&&e.pausedAt>=0&&e.effect==retained,
    "genuine user pause must remain effective during stalled seek");
  MediaPlayer.OnSeekCompleteListener staleSeek=p.seek;
  // Yandex emits a position-discontinuity reason=SEEK when a real manual
  // Next changes the Media3 item index. Route that actual callback shape,
  // not a synthetic direct sourceBoundary() call.
  Media3SourceRouter router=new Media3SourceRouter(new SourceEventArbiter(),
   new Media3SourceRouter.Sink(){
    public void boundary(String nextAlias,String reason){e.sourceBoundary(reason);}
    public void seekRequested(){e.sourceSeekRequested();}
   });
  check(router.discontinuity("1","2","1","2",5,6,50350,0,0,false,true)
      ==SourceEventArbiter.Action.BOUNDARY,
    "Media3 manual Next changing item index must be a boundary during slow seek");
  staleSeek.onSeekComplete(p);
  check(p.released&&e.player==null&&e.effect==null&&retained.released,
    "real track boundary retires old in-flight decoder and effect before stale ACK");
  check(router.mediaItem("2","2","2",false,0)==SourceEventArbiter.Action.IGNORE,
    "follow-up Media3 item event cannot create a second boundary");
  SystemClock.now+=2000;TestEngine.p.handler.drain();
  check(e.player==null&&e.effect==null,"stale callbacks cannot revive output after Next");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  try{
  slowSourceRetargetingRetainsEffect();realPauseAndNextOverrideSlowSeek();
    System.out.println("PASS: "+checks+" HONOR 0.3.67 slow partial-stream multi-seek owner tests");
  } finally {
   if(TestEngine.e!=null&&!TestEngine.e.closed)TestEngine.e.close();
  }
 }
}
