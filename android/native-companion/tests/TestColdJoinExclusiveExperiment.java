package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;

/** Narrow A/B replay for the prewarmed local-file cold/new-track handover only. */
public final class TestColdJoinExclusiveExperiment {
  static int checks;

  static void check(boolean okay,String why){
    checks++;
    if(!okay)throw new AssertionError(why);
  }

  static MediaPlayer begin(boolean exclusive)throws Exception{
    TestEngine.reset("ALBUM",true);
    ReplacementEngine engine=TestEngine.e;
    engine.coldJoinExclusiveExperiment=exclusive;
    engine.arm();
    MediaPlayer decoder=TestEngine.prepare();

    check(engine.fullFileExperiment&&"full_download_file".equals(engine.audioSourceKind),
        "experiment must use the accepted full-local-file source");
    check(decoder.playing&&engine.localPrewarmWarmupPending
            &&decoder.volume==0f&&engine.effect!=null&&engine.effect.gain==0f
            &&engine.originalMix==1f,
        "both variants start with muted decoder and original audible");

    // Match the existing 0.3.85 local decoder prewarm/alignment path exactly.
    TestCachedAudioRollback.advanceWarmup(decoder,10,20,8);
    check(engine.fading&&engine.audioOwner.handoverAwaitingClock()
            &&decoder.volume==0f&&engine.effect.gain==0f
            &&engine.originalMix==1f&&decoder.seekCalls==1,
        "both variants reach the same pre-handover clock gate after one muted alignment seek");
    return decoder;
  }

  static void advanceAndAssert(MediaPlayer decoder,boolean exclusive){
    ReplacementEngine engine=TestEngine.e;
    for(int i=0;i<10;i++){
      SystemClock.now+=20;
      decoder.position+=20;
      TestEngine.p.current=TestEngine.source("1",
          TestEngine.p.current.position+20,true);
      TestEngine.p.handler.drain();

      if(exclusive){
        check(AudioOwnership.exclusive(engine.originalMix,decoder.volume),
            "exclusive experiment never commands both sessions audible at once");
      }else if(engine.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND){
        check(engine.fading&&Math.abs(engine.originalMix+decoder.volume-1f)<0.02f,
            "baseline variant retains the existing complementary-linear gain law");
      }else{
        check(AudioOwnership.exclusive(engine.originalMix,decoder.volume),
            "baseline is exclusive outside its existing blend interval");
      }
    }
    check(!engine.fading&&engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT
            &&decoder.volume>0.99f&&engine.effect.gain==-100f,
        "both variants finish with the replacement as sole commanded output");
  }

  static void legacyBaselineRemainsAvailableToHostReplay()throws Exception{
    LogStore.events.clear();
    MediaPlayer decoder=begin(false);
    advanceAndAssert(decoder,false);
    check(LogStore.events.contains("replacement_unified_join_start")
            &&LogStore.events.contains("replacement_join_transport_summary")
            &&!LogStore.events.contains("replacement_cold_join_experiment_start"),
        "test-only baseline still exercises the unchanged 160ms complementary join");
    TestEngine.e.close();
  }

  static void exclusiveColdJoinUsesTheSameGateWithoutOverlap()throws Exception{
    LogStore.events.clear();
    MediaPlayer decoder=begin(true);
    advanceAndAssert(decoder,true);
    check(LogStore.events.contains("replacement_cold_join_experiment_start")
            &&!LogStore.events.contains("replacement_unified_join_start")
            &&!LogStore.events.contains("replacement_join_transport_summary"),
        "experiment replaces only the cold-join blend, not the prewarm or clock gate");
    TestEngine.e.close();
  }

  static void productionConstructorSelectsExperimentWithoutAnAppToggle(){
    TestEngine.reset("ALBUM",true);
    ReplacementEngine production=new ReplacementEngine(TestEngine.p);
    check(production.coldJoinExclusiveExperiment,
        "production constructor selects the isolated exclusive cold-join candidate");
    check(!TestEngine.e.coldJoinExclusiveExperiment,
        "test-only constructor keeps legacy baseline injection for regression replay");
    production.close();
    TestEngine.e.close();
  }

  public static void main(String[] args)throws Exception{
    legacyBaselineRemainsAvailableToHostReplay();
    exclusiveColdJoinUsesTheSameGateWithoutOverlap();
    productionConstructorSelectsExperimentWithoutAnAppToggle();
    System.out.println("PASS: "+checks
        +" cold-join baseline/exclusive handover, same-gate and no-overlap checks");
  }
}
