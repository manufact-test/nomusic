package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;

/** Actual-engine replay of 0.3.71 seek residuals with a frozen stable clock baseline. */
public final class TestHonor071SeekResidual {
 static int checks;
 static TestStreamingEngine.Buffer activeBuffer;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static void start(ReplacementEngine e,MediaPlayer p){
  p.position+=50;SystemClock.now+=50;TestEngine.p.current=TestEngine.source("1",1050,true);e.update(TestEngine.p.current);
  TestEngine.p.handler.drain();
  p.position+=600;SystemClock.now+=600;TestEngine.p.current=TestEngine.source("1",1650,true);e.update(TestEngine.p.current);
  TestEngine.p.handler.drain();
  /* The first drain validates decoder advancement and starts the 160ms cold
     join. Advance that join explicitly before using this as a seek baseline. */
  if(e.fading){
   SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS;p.position+=ReplacementEngine.UNIFIED_JOIN_MS;
   TestEngine.p.current=TestEngine.source("1",p.position,true);e.update(TestEngine.p.current);
   TestEngine.p.handler.drain();
  }
  check(!e.fading&&p.volume>0.99f&&e.effect!=null&&e.effect.gain==-100f,
    "precondition: replacement owns output after verified initial join");
 }
 static void establishOffset(ReplacementEngine e,MediaPlayer p,long offset){
  for(int i=0;i<3;i++){
   SystemClock.now+=150;p.position+=150;
   TestEngine.p.current=TestEngine.source("1",p.position+offset,true);
   e.update(TestEngine.p.current);
  }
  check(e.seekAlignment.stableForTest()&&e.seekAlignment.stableOffsetForTest()==offset,
    "three advancing stable samples establish the transport offset "+offset+"ms");
 }
 static void stable206OffsetMakes283ResidualSafe()throws Exception{
  TestStreamingEngine.Buffer partial=TestStreamingEngine.start();activeBuffer=partial;
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;start(e,p);
  establishOffset(e,p,206);
  DynamicsProcessing original=e.effect;int before=p.seekCalls;
  p.asyncSeek=true;e.sourceSeekRequested();
  TestEngine.p.current=TestEngine.source("1",50000,true);e.update(TestEngine.p.current);
  check(e.seeking&&p.position==49794&&e.seekAlignment.baselineOffset()==206,
    "user seek preserves the previously stable 206ms transport relationship");
  SystemClock.now+=77;TestEngine.p.current=TestEngine.source("1",50077,true);p.seek.onSeekComplete(p);
  check(!e.seeking&&p.seekCalls==before+1&&e.fading&&e.audioOwner.handoverAwaitingClock()
      &&p.volume==0f&&original.gain==0f,
    "283ms raw residual is accepted as only 77ms beyond the stable baseline");
  SystemClock.now+=90;p.position+=90;TestEngine.p.current=TestEngine.source("1",50167,true);
  TestEngine.p.handler.drain();
  check(!e.fading&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT
      &&p.volume>0.99f&&original.gain==-100f&&e.seekAlignment.stableOffsetForTest()==283,
    "verified seek rejoins once and records its new steady transport offset");
  e.close();check(partial.closed&&e.effect==null,"cleanup retires partial stream and restores original");
 }
 static void new250msDeltaGetsSilentCorrection()throws Exception{
  TestStreamingEngine.Buffer partial=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;start(e,p);
  establishOffset(e,p,206);
  DynamicsProcessing original=e.effect;int before=p.seekCalls;
  p.asyncSeek=true;e.sourceSeekRequested();
  TestEngine.p.current=TestEngine.source("1",50000,true);e.update(TestEngine.p.current);
  SystemClock.now+=250;TestEngine.p.current=TestEngine.source("1",50250,true);p.seek.onSeekComplete(p);
  check(e.seeking&&p.seekCalls==before+2&&p.position==50044
      &&p.volume==0f&&original.gain==0f,
    "456ms raw residual adds 250ms beyond baseline and triggers one silent correction");
  SystemClock.now+=17;TestEngine.p.current=TestEngine.source("1",50267,true);p.seek.onSeekComplete(p);
  check(!e.seeking&&e.fading&&e.audioOwner.handoverAwaitingClock()
      &&p.playing&&p.volume==0f&&original.gain==0f,
    "fast correction ACK validates without releasing original audio early");
  SystemClock.now+=90;p.position+=90;TestEngine.p.current=TestEngine.source("1",50357,true);
  TestEngine.p.handler.drain();
  check(!e.fading&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT
      &&p.volume>0.99f&&original.gain==-100f,
    "only the corrected advancing decoder receives output ownership");
  e.close();check(partial.closed&&e.effect==null,"cleanup retires corrected partial stream");
 }
 static void noBaseline283ResidualCorrectsAndPauseNextWin()throws Exception{
  TestStreamingEngine.Buffer partial=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;start(e,p);
  DynamicsProcessing original=e.effect;int before=p.seekCalls;
  p.asyncSeek=true;e.sourceSeekRequested();
  TestEngine.p.current=TestEngine.source("1",70000,true);e.update(TestEngine.p.current);
  SystemClock.now+=311;TestEngine.p.current=TestEngine.source("1",70283,true);p.seek.onSeekComplete(p);
  check(e.seeking&&p.seekCalls==before+2&&p.position==70283
      &&p.volume==0f&&original.gain==0f,
    "without a stable baseline, 283ms residual is not accepted");
  SystemClock.now+=20;TestEngine.p.current=TestEngine.source("1",70303,true);p.seek.onSeekComplete(p);
  check(!e.seeking&&e.fading&&e.audioOwner.handoverAwaitingClock()&&p.volume==0f,
    "20ms final residual enters muted clock-validation gate");
  TestEngine.p.current=TestEngine.source("1",70303,false);e.update(TestEngine.p.current);
  check(!e.fading&&!p.playing&&e.pausedAt>=0&&p.volume==0f&&original.gain==0f,
    "genuine pause revokes the pending handover");
  MediaPlayer.OnSeekCompleteListener stale=p.seek;
  e.sourceBoundary("manual_next_during_residual_gate");stale.onSeekComplete(p);
  check(p.released&&e.player==null&&e.effect==null&&partial.closed,
    "Next retires the old decoder/effect and stale ACK cannot revive it");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  try{
  stable206OffsetMakes283ResidualSafe();
    new250msDeltaGetsSilentCorrection();
    noBaseline283ResidualCorrectsAndPauseNextWin();
    System.out.println("PASS: "+checks+" HONOR 0.3.71 baseline-aware seek and pause/Next checks");
  } finally {
   if(TestEngine.e!=null&&!TestEngine.e.closed)TestEngine.e.close();
   if(activeBuffer!=null&&!activeBuffer.closed)activeBuffer.close();
  }
 }
}
