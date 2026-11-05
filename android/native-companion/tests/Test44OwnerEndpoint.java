package pro.celikom.nativeprobe.identitydiag;

import java.util.Map;

/** Regressions grounded in the two fresh HONOR Test.43 runs (22:53 and 22:55). */
public final class Test44OwnerEndpoint {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}

 static void cappedFadeCannotClaimExclusiveOwnership(){
  // Test.43 actual final_decoder_gain exceptions reported 0.9997536 and
  // 0.9990203. Both exceed the former 0.999 shortcut but keep the original
  // source at a small nonzero gain in SAME_SONG_BLEND.
  float near=JoinTransitionPolicy.boundedMix(220,220,0.8397536f);
  check(near>0.999f&&near<1f,"replay the near-terminal capped fade value");
  check(!JoinTransitionPolicy.exclusiveGainReady(near),
    "only exact full mixer ownership may issue an exclusive gain command");
  check(!JoinTransitionPolicy.exclusiveGainReady(0.9990203f),
    "second HONOR exception remains a blend, not REPLACEMENT");
  float endpoint=JoinTransitionPolicy.boundedMix(240,220,near);
  check(endpoint==1f&&JoinTransitionPolicy.exclusiveGainReady(endpoint),
    "one bounded additional handler tick finishes the mixer without fallback");
 }

 static void lateCurrentAliasMustNotStartSpeculativeFullDownload(){
  TestEngine.reset("ALBUM",true);
  TestEngine.e.close();
  TestEngine.e=new ReplacementEngine(TestEngine.p,true,true);
  TestEngine.e.identity(LogStore.map("mediaAlias","1","albumId","42",
    "title","Песня","artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","7","method","ALBUM","editionConflict",false));
  TestEngine.e.arm();
  check(TestEngine.e.progressiveColdAllowed,
    "only Test opt-in progressive current-track preparation is affected");
  int before=TestEngine.api.resolves;
  Map<String,Object> alreadyCurrent=LogStore.map("mediaAlias","1","durationMs",120000L);
  TestEngine.e.prefetchLookahead(alreadyCurrent,"7");
  check(TestEngine.api.resolves==before&&TestEngine.e.lookaheadPrefetchAlias==null,
    "after manual Next the current song never starts a redundant full-file prefetch");
  TestEngine.p.lookaheadAlias="2";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  check(TestEngine.api.resolves==before+1&&"2".equals(TestEngine.e.lookaheadPrefetchAlias),
    "a genuinely NEXT song still gets the existing lookahead prefetch");
  TestEngine.e.close();
 }

 public static void main(String[] args){
  cappedFadeCannotClaimExclusiveOwnership();
  lateCurrentAliasMustNotStartSpeculativeFullDownload();
  System.out.println("PASS: "+checks+" Test.44 exact owner endpoint and late-current prefetch guards");
 }
}
