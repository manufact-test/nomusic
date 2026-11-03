package pro.celikom.nativeprobe.identitydiag;
/* Deterministic cases: seek never inferred from another song or unknown position. */
public final class TestSourceSessionSnapshotPolicy {
 static int checks;
 static void yes(boolean okay,String message){checks++;if(!okay)throw new AssertionError(message);}
 public static void main(String[] args){
  SourceSessionSnapshotPolicy.Verdict x=SourceSessionSnapshotPolicy.compare("447",219660,6000,true,"447",219660,135000,true);
  yes(x.sameItem&&x.validPosition&&x.positionDisagrees&&x.positionDeltaMs==129000,
   "direct session may expose a seek while primary stays on stale seconds");
  x=SourceSessionSnapshotPolicy.compare("430",232330,169454,true,"430",232330,169800,true);
  yes(x.sameItem&&!x.positionDisagrees,"late matching Media3 state stays inside jitter guard");
  x=SourceSessionSnapshotPolicy.compare("447",219660,6000,true,"430",232330,135000,false);
  yes(!x.sameItem&&!x.positionDisagrees&&!x.pauseDisagrees,"cross-track state cannot assert seek or pause");
  x=SourceSessionSnapshotPolicy.compare("447",219660,6000,true,"447",180000,135000,false);
  yes(!x.sameItem&&!x.positionDisagrees&&!x.pauseDisagrees,"edition-duration conflict fails closed");
  x=SourceSessionSnapshotPolicy.compare("447",219660,-1,true,"447",219660,135000,true);
  yes(!x.validPosition&&!x.positionDisagrees,"unknown position is not a recovered seek");
  x=SourceSessionSnapshotPolicy.compare("447",219660,50000,true,"447",219660,50050,false);
  yes(x.sameItem&&!x.positionDisagrees&&x.pauseDisagrees,"same-track pause disagreement is evidence only");
  x=SourceSessionSnapshotPolicy.compare("447",219660,50000,false,"447",219660,50050,false);
  yes(!x.pauseDisagrees,"same pause state does not yield a false conflict");
  x=SourceSessionSnapshotPolicy.compare("447",219660,219000,true,"447",219660,230000,true);
  yes(!x.validPosition&&!x.positionDisagrees,"invalid out-of-bounds position rejected");
  x=SourceSessionSnapshotPolicy.compare("447",219660,3000,true,"447",219660,4499,true);
  yes(!x.positionDisagrees,"bounded difference does not become a fake seek");
  x=SourceSessionSnapshotPolicy.compare("447",219660,3000,true,"447",219660,4501,true);
  yes(x.positionDisagrees,"large validated difference remains observable");
  System.out.println("PASS: "+checks+" secondary Media3 snapshot read-only safety checks");
 }
}
