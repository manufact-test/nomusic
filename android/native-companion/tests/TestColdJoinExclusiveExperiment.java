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
    check(LogStore.events.contains("replacement_cold_alignment_lead"),
        "only muted cold attachment applies the bounded predictive alignment lead");
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
            &&LogStore.events.contains("replacement_exclusive_soft_join_start")
            &&!LogStore.events.contains("replacement_unified_join_start")
            &&!LogStore.events.contains("replacement_join_transport_summary"),
        "bounded non-overlap source-duck/decoder-rise replaces only the cold-join blend");
    TestEngine.e.close();
  }

  static void pauseWhileSourceIsDuckingRestoresSource()throws Exception{
    LogStore.events.clear();
    MediaPlayer decoder=begin(true);
    ReplacementEngine engine=TestEngine.e;
    // Complete the transport-only gate and enter the first muted source ramp.
    for(int i=0;i<6&&!LogStore.events.contains("replacement_exclusive_soft_join_start");i++){
      SystemClock.now+=20;
      decoder.position+=20;
      TestEngine.p.current=TestEngine.source("1",TestEngine.p.current.position+20,true);
      TestEngine.p.handler.drain();
    }
    check(LogStore.events.contains("replacement_exclusive_soft_join_start")
            &&decoder.volume==0f&&engine.originalMix>0f,
        "cold envelope begins with inaudible replacement");
    SystemClock.now+=10;
    decoder.position+=10;
    TestEngine.p.current=TestEngine.source("1",TestEngine.p.current.position+10,true);
    TestEngine.p.handler.drain();
    check(engine.originalMix>0f&&engine.originalMix<1f&&decoder.volume==0f,
        "source is partly ducked and replacement is still silent");
    PlaybackSource paused=TestEngine.source("1",TestEngine.p.current.position,false);
    TestEngine.p.current=paused;
    engine.update(paused);
    check(decoder.volume==0f&&engine.effect.gain==0f
            &&engine.audioOwner.state()==AudioOwnership.State.PAUSED,
        "source pause during exclusive envelope restores native gain and silences decoder");
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

  static void fingerSeekCannotBecomeAnotherColdJoin(){
    TestEngine.reset("ALBUM");
    ReplacementEngine engine=TestEngine.e;
    engine.coldJoinExclusiveExperiment=true;
    engine.arm();
    check(ReplacementEngine.exclusiveColdEnvelope(false,true,true,false),
        "first cold streaming join retains the owner-selected exclusive envelope");
    engine.sourceSeekRequested();
    check(engine.sourceSeekedThisTrack,
        "observed Media3 finger seek tags the current source even before decoder ACK");
    check(!ReplacementEngine.exclusiveColdEnvelope(false,true,
        engine.coldJoinExclusiveExperiment,engine.sourceSeekedThisTrack)
        &&!ReplacementEngine.exclusiveColdEnvelope(true,true,true,false)
        &&!ReplacementEngine.exclusiveColdEnvelope(false,false,true,false),
        "a seek, coherent resume or unvalidated clock must not replay the first-cold duck");
    engine.coldEnvelopeOwnerKey=engine.identityKey;
    check(!ReplacementEngine.exclusiveColdEnvelope(false,true,
        engine.coldJoinExclusiveExperiment
            &&!engine.identityKey.equals(engine.coldEnvelopeOwnerKey),false),
        "even a later source-buffer recovery on the same item cannot start another first-cold duck");
    engine.close();
  }

  public static void main(String[] args)throws Exception{
    legacyBaselineRemainsAvailableToHostReplay();
    exclusiveColdJoinUsesTheSameGateWithoutOverlap();
    pauseWhileSourceIsDuckingRestoresSource();
    fingerSeekCannotBecomeAnotherColdJoin();
    productionConstructorSelectsExperimentWithoutAnAppToggle();
    System.out.println("PASS: "+checks
        +" cold-join baseline/exclusive handover, same-gate and no-overlap checks");
  }
}
