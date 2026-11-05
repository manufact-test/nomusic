package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;

/** Test.40 guards the cold audio join and preserves a connected source. */
public final class Test40ConservativeJoin {
 static int assertions;
 static void check(boolean b,String message){assertions++;if(!b)throw new AssertionError(message);}

 static void probeDoesNotDiscardLiveMedia3(){
  SourceSessionRecheck guard=new SourceSessionRecheck();
  check(guard.probe(true,true,"old",35000,929,929,4500,10000),
    "same-session hint may start an independent, read-only probe");
  check(!guard.awaitingFreshSource,
    "unverified hint alone must not quarantine a working controller");
  check(guard.sameProgressOnFreshController("old",35080,10080),
    "fresh second controller with progressing same item cancels false alarm");
  check(!guard.sameProgressOnFreshController("new",20,10080),
    "new item is an actual source boundary");
  guard.clear();
  check(!guard.probe(true,true,"old",35000,929,929,4500,10090),
    "same-session repeated hints must not cause a reconnect storm");
  check(guard.probe(true,true,"old",45000,929,929,15000,25000),
    "later independent hint may be checked");
  guard.quarantine();
  check(!guard.accept("old",45200,25100),
    "failed fresh probe cannot authorize stale replacement audio");
  check(guard.accept("new",50,25300),
    "freshly confirmed next song lifts the safe fence");
 }

 static void transportWindow(){
  JoinStabilityWindow gate=new JoinStabilityWindow();
  check(gate.observe(1000,22,1000,1400)==JoinStabilityWindow.Decision.WAIT,
    "first sample cannot authorize a join");
  check(gate.observe(1040,23,1000,1400)==JoinStabilityWindow.Decision.WAIT,
    "clock needs a time window");
  check(gate.observe(1080,26,1000,1400)==JoinStabilityWindow.Decision.WAIT,
    "three samples still lack the whole window");
  check(gate.observe(1120,28,1000,1400)==JoinStabilityWindow.Decision.READY,
    "four coherent clock samples permit a bounded join");
  gate.reset();
  check(gate.observe(2000,27,2000,1400)==JoinStabilityWindow.Decision.WAIT,
    "new item resets clock statistics");
  check(gate.observe(2060,57,2000,1400)==JoinStabilityWindow.Decision.WAIT,
    "30ms growth breaks confidence before any gain is granted");
  check(gate.observe(2120,86,2000,1400)==JoinStabilityWindow.Decision.WAIT,
    "Test.39-style drift reaching 86ms cannot be blended");
  check(gate.observe(3400,44,2000,1400)==JoinStabilityWindow.Decision.UNSAFE,
    "bounded gate keeps the original instead of an audible rough switch");
 }

 static void productionScope(){
  TestEngine.reset("ALBUM",true);
  check(!TestEngine.e.conservativeColdJoinExperiment,
    "two-argument accepted host replay remains unchanged");
  ReplacementEngine production=new ReplacementEngine(TestEngine.p,true,true,true);
  check(production.conservativeColdJoinExperiment&&production.lateSourceEffectAttachExperiment,
    "only the isolated progressive Test.40 service enables new source gate");
  production.close();TestEngine.e.close();
 }

 static void actualDecoderColdJoin()throws Exception{
  TestEngine.reset("ALBUM",true);
  TestEngine.e.close();
  TestEngine.e=new ReplacementEngine(TestEngine.p,true,true,true);
  ReplacementEngine engine=TestEngine.e;
  engine.identity(LogStore.map("mediaAlias","1","albumId","42",
    "title","Песня","artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","7","method","ALBUM","editionConflict",false));
  engine.arm();
  MediaPlayer decoder=TestEngine.prepare();
  check(decoder.isPlaying()&&engine.effect==null&&decoder.volume==0f,
    "Test.40 production starts its local decoder silently without source DSP");
  TestCachedAudioRollback.advanceWarmup(decoder,10,20,8);
  check(engine.fading&&engine.effect==null,
    "warmup and seek ACK remain inaudible and do not attach DSP early");
  // Simulate the real decoder clock settling after the predicted 70ms warm
  // seek lead. The uncompensated fake remains 70ms ahead and is rejected.
  decoder.position-=70;
  TestCachedAudioRollback.advanceTogether(decoder,12,20);
  check(engine.fading&&engine.effect!=null,
    "several stable clock readings eventually authorize the real DSP handover");
  TestCachedAudioRollback.advanceTogether(decoder,12,20);
  check(!engine.fading&&decoder.volume>0.99f
    &&engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
    "real decoder completes a single guarded 160ms handover");
  engine.close();
 }

 public static void main(String[]args)throws Exception{probeDoesNotDiscardLiveMedia3();transportWindow();productionScope();actualDecoderColdJoin();
  System.out.println("PASS: "+assertions+" Test.40 source probe + conservative join checks");}
}
