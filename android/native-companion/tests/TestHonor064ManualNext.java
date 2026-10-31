package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;

/** HONOR regression: manual Next -> partial HTTP stream -> user scrub.
 * 0.3.65 rejects both the 260ms muted-source hold and repeated 500ms dips. */
public final class TestHonor064ManualNext {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static void sample(String alias,long pos){TestEngine.p.current=TestEngine.source(alias,pos,true);}
 static void tick(String alias,MediaPlayer player,long ms,long pos){
  SystemClock.now+=ms;player.position+=ms;sample(alias,pos);TestEngine.p.handler.drain();
 }
 static TestStreamingEngine.Buffer newTrack(String alias,boolean manual)throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;
  MediaPlayer old=e.player;
  TestEngine.api.useStreaming=true;
  e.sourceBoundary(manual?"manual_next_button":"automatic_next");
  check(old.released&&old.volume==0f&&e.effect==null,
    "old track must be silenced before the next song can become audible");
  sample(alias,1000);
  e.identity(LogStore.map("mediaAlias",alias,"albumId","42","title","Песня","artist","Артист","durationMs",120000L),
      LogStore.map("candidateTrackId","8","method","ALBUM","editionConflict",false));
  TestEngine.resolve();
  TestStreamingEngine.Buffer buffer=new TestStreamingEngine.Buffer();
  TestEngine.api.streamed.done(buffer,null);
  e.player.prepared.onPrepared(e.player);
  check(e.player.playing&&e.player.volume==0f&&e.effect.gain==0f&&!buffer.complete(),
    "next song begins from incomplete streaming cache with original still audible");
  return buffer;
 }
 static void finishColdDip(String alias)throws Exception{
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  tick(alias,p,60,1060);
  check(e.fading&&e.effect.gain==0f&&p.volume==0f,
    "decoder must advance before the 500ms exclusive dip begins");
  tick(alias,p,125,1185);
  check(e.originalMix>0f&&e.originalMix<1f&&p.volume==0f,
    "quarter-wave dip commands only the original before the midpoint");
  tick(alias,p,125,1310);
  check(e.effect.gain==-100f&&p.volume==0f,
    "midpoint never overlaps the original and replacement waveforms");
  tick(alias,p,125,1435);
  check(e.effect.gain==-100f&&p.volume>0f&&p.volume<1f,
    "second dip half raises replacement without any Yandex overlap");
  tick(alias,p,130,1565);
  check(!e.fading&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT
      &&e.effect.gain==-100f&&p.volume==1f,
    "cold 500ms dip must complete on the single verified replacement");
 }
 static void manualNextAndRepeatedPartialScrubs()throws Exception{
  TestStreamingEngine.Buffer buffer=newTrack("2",true);
  finishColdDip("2");
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  DynamicsProcessing fx=e.effect;p.asyncSeek=true;
  int beforeResolves=TestEngine.api.resolves,beforeDownloads=TestEngine.api.downloads;
  long[] targets={60000,84000,30000};
  for(int i=0;i<targets.length;i++){
   long target=targets[i];int before=p.seekCalls;
   e.sourceSeekRequested();sample("2",target);e.update(TestEngine.p.current);
   check(e.seeking&&p.seekCalls==before+1&&!e.seekHoldActive
       &&!e.pendingStreamScrubJoin&&p.volume==0f
       &&fx.gain==0f&&e.originalMix==1f,
       "partial stream scrub "+i+" keeps native source audible without a new cold join");
   SystemClock.now+=310;sample("2",target+310);TestEngine.p.handler.drain();
   check(e.seeking&&p.volume==0f&&fx.gain==0f&&!e.seekHoldActive,
       "300ms HTTP seek must keep original audible without fallback owner swap "+i);
   p.seek.onSeekComplete(p);
   check(!e.seeking&&p.playing&&e.effect==fx&&e.player==p,
       "completed partial scrub retains decoder and effect, no re-download "+i);
   tick("2",p,60,target+370);
   check(!e.fading&&!e.pendingStreamScrubJoin&&p.volume==1f
       &&fx.gain==-100f&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
       "aligned partial scrub returns once without 500ms dip "+i);
  }
  check(TestEngine.api.downloads==beforeDownloads&&TestEngine.api.resolves==beforeResolves
      &&e.effect==fx&&!fx.released,
      "three manual-next scrubs cannot redo lookup, download or effect binding");
  // After the stream is entirely cached, source remains available during seek.
  buffer.present.set(1);
  check(buffer.complete(),"streaming fake must now represent a fully cached file");
  int before=p.seekCalls;
  e.sourceSeekRequested();sample("2",70000);e.update(TestEngine.p.current);
  check(!e.seekHoldActive&&p.seekCalls==before+1&&p.volume==0f
      &&fx.gain==0f&&e.originalMix==1f,
      "fully downloaded song never commands a muted-source seek gap");
  SystemClock.now+=65;sample("2",70065);p.seek.onSeekComplete(p);
  check(p.playing&&!e.seeking&&e.effect==fx&&fx.gain==0f,
      "fast completed seek stays on native output until decoder clock advances");
  tick("2",p,140,70205);
  check(p.volume==1f&&fx.gain==-100f&&!e.pendingStreamScrubJoin,
      "completed-cache fast scrub rejoins immediately without redundant dip");
  e.close();
 }
 static void autoNextAndCancelDuringDip()throws Exception{
  TestStreamingEngine.Buffer buffer=newTrack("3",false);
  finishColdDip("3");check(!buffer.complete(),"automatic next still plays a partial stream");
  TestEngine.e.close();
  newTrack("4",false);
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  tick("4",p,60,1060);tick("4",p,125,1185);
  check(e.fading&&e.originalMix>0f&&e.originalMix<1f&&p.volume==0f,
      "automatic next can be canceled during source-only down-half");
  e.sourceBoundary("next_during_exclusive_dip");
  SystemClock.now+=900;TestEngine.p.handler.drain();
  check(p.released&&e.player==null&&e.effect==null,
      "confirmed next cancels all delayed dip and scrub callbacks");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  manualNextAndRepeatedPartialScrubs();
  autoNextAndCancelDuringDip();
  System.out.println("PASS: "+checks+" HONOR manual Next, streaming/cached seeks, single cold dip and no repeated scrub dip");
 }
}
