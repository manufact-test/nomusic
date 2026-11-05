package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;

/** APK-default Test.39 contract, distinct from the accepted Test.38 replay. */
public final class Test39LateSourceEffectAttach {
 static int checks;
 static void check(boolean okay,String why){
  checks++;
  if(!okay)throw new AssertionError(why);
 }

 static MediaPlayer begin()throws Exception{
  TestEngine.reset("ALBUM",true);
  ReplacementEngine engine=TestEngine.e;
  check(!engine.lateSourceEffectAttachExperiment,"legacy replay explicitly selects Test.38");
  engine.lateSourceEffectAttachExperiment=true;
  engine.arm();
  MediaPlayer decoder=TestEngine.prepare();
  check(engine.localPrewarmWarmupPending&&decoder.isPlaying()
       &&decoder.volume==0f&&engine.effect==null&&engine.originalMix==1f,
       "APK experiment prewarms muted local decoder without constructing source effect");
  check(LogStore.events.contains("replacement_source_effect_deferred"),
       "real cold prewarm must log a deferred source attachment");
  return decoder;
 }

 static void attachOnlyAfterClockGate()throws Exception{
  LogStore.events.clear();
  int constructedBefore=DynamicsProcessing.constructionCount;
  MediaPlayer decoder=begin();
  ReplacementEngine engine=TestEngine.e;
  check(DynamicsProcessing.constructionCount==constructedBefore,
       "preparing a playable decoder must not construct DSP");
  TestCachedAudioRollback.advanceWarmup(decoder,10,20,8);
  check(engine.fading&&engine.audioOwner.handoverAwaitingClock()
    &&engine.effect==null&&decoder.volume==0f
    &&DynamicsProcessing.constructionCount==constructedBefore,
    "muted predictive alignment and seek ACK cannot touch source effect");
  TestCachedAudioRollback.advanceTogether(decoder,10,20);
  check(!engine.fading&&engine.effect!=null
    &&engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT
    &&decoder.volume>0.99f&&engine.effect.gain==-100f,
    "verified decoder advancement attaches once and finishes the same 160ms join");
  check(DynamicsProcessing.constructionCount==constructedBefore+1
    &&LogStore.events.contains("replacement_source_effect_attached_at_join")
    &&LogStore.events.contains("replacement_unified_join_start"),
    "exactly one new effect is created at the proven handover gate");
  engine.close();
 }

 static void cancelBeforeGateLeavesOriginalUntouched()throws Exception{
  int constructedBefore=DynamicsProcessing.constructionCount;
  MediaPlayer decoder=begin();
  ReplacementEngine engine=TestEngine.e;
  engine.sourceBoundary("owner_next","2");
  check(decoder.released&&engine.player==null&&engine.effect==null
    &&DynamicsProcessing.constructionCount==constructedBefore,
    "Next during silent prewarm releases decoder without ever enabling DSP");
  engine.close();
 }

 static void pauseBeforeGateMustNotCreateDSP()throws Exception{
  int constructedBefore=DynamicsProcessing.constructionCount;
  MediaPlayer decoder=begin();
  TestEngine.p.current=TestEngine.source("1",1000,false);
  TestEngine.e.update(TestEngine.p.current);
  check(!decoder.isPlaying()&&TestEngine.e.effect==null
    &&DynamicsProcessing.constructionCount==constructedBefore,
    "source pause during speculative warmup never opens the source DSP");
  TestEngine.e.close();
 }

 static void nextSongStartsWithFreshMutedDecoder()throws Exception{
  MediaPlayer first=begin();
  ReplacementEngine engine=TestEngine.e;
  TestCachedAudioRollback.advanceWarmup(first,10,20,8);
  TestCachedAudioRollback.advanceTogether(first,10,20);
  check(!engine.fading&&engine.effect!=null,
    "first song has exclusive source-effect lease before Next");
  DynamicsProcessing firstEffect=engine.effect;
  engine.sourceBoundary("manual_next","2");
  check(first.released&&firstEffect.released&&engine.effect==null,
    "switching songs retires old decoder and DSP without retaining a stale lease");

  TestEngine.p.current=TestEngine.source("2",1000,true);
  engine.identity(LogStore.map("mediaAlias","2","albumId","42",
    "title","Песня","artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","8","method","ALBUM","editionConflict",false));
  MediaPlayer second=TestEngine.prepare();
  check(second!=first&&second.isPlaying()&&second.volume==0f
    &&engine.effect==null&&engine.localPrewarmWarmupPending,
    "fresh next song warms silently without inherited DSP or previous audio");
  for(int i=0;i<10;i++){
   SystemClock.now+=20;
   if(i>=8)second.position+=20;
   TestEngine.p.current=TestEngine.source("2",TestEngine.p.current.position+20,true);
   TestEngine.p.handler.drain();
  }
  check(engine.fading&&engine.effect==null&&engine.audioOwner.handoverAwaitingClock(),
    "second song independently reaches clock gate with original still audible");
  for(int i=0;i<10;i++){
   SystemClock.now+=20;second.position+=20;
   TestEngine.p.current=TestEngine.source("2",TestEngine.p.current.position+20,true);
   TestEngine.p.handler.drain();
  }
  check(!engine.fading&&engine.effect!=null&&engine.effect!=firstEffect
    &&second.volume>0.99f&&engine.effect.gain==-100f,
    "second fresh song joins with exactly its own current decoder/effect");
  engine.close();
 }

 static void defaultProductModeIsExplicit()throws Exception{
  TestEngine.reset("ALBUM",true);
  ReplacementEngine productionDefault=new ReplacementEngine(TestEngine.p,true);
  check(productionDefault.lateSourceEffectAttachExperiment,
    "unconfigured app engine must actually enable Test.39 mode");
  productionDefault.close();
 }

 public static void main(String[] args)throws Exception{
  defaultProductModeIsExplicit();
  attachOnlyAfterClockGate();
  cancelBeforeGateLeavesOriginalUntouched();
  pauseBeforeGateMustNotCreateDSP();
  nextSongStartsWithFreshMutedDecoder();
  System.out.println("PASS: "+checks+" Test.39 production-default late DSP, gate, Next, pause and no-early-effect checks");
 }
}
