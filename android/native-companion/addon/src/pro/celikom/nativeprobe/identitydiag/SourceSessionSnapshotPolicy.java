package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;
/* Read-only comparison of two independent Media3 controller snapshots.
   A disagreement is evidence to investigate, never authority to seek or pause. */
final class SourceSessionSnapshotPolicy {
 static final long POSITION_DISAGREEMENT_MS=1500;
 static final long DURATION_TOLERANCE_MS=1000;
 static final class Verdict {
  final boolean sameItem,validPosition,positionDisagrees,pauseDisagrees;
  final long positionDeltaMs;
  Verdict(boolean sameItem,boolean validPosition,long delta,boolean positionDisagrees,boolean pauseDisagrees){
   this.sameItem=sameItem;this.validPosition=validPosition;this.positionDeltaMs=delta;
   this.positionDisagrees=positionDisagrees;this.pauseDisagrees=pauseDisagrees;
  }
 }
 static Verdict compare(String primaryAlias,long primaryDuration,long primaryPosition,boolean primaryPlaying,
                         String directAlias,long directDuration,long directPosition,boolean directPlaying){
  boolean same=primaryAlias!=null&&Objects.equals(primaryAlias,directAlias)
   &&primaryDuration>0&&directDuration>0
   &&Math.abs(primaryDuration-directDuration)<=DURATION_TOLERANCE_MS;
  boolean valid=same&&primaryPosition>=0&&directPosition>=0
   &&primaryPosition<=primaryDuration+1000&&directPosition<=directDuration+1000;
  long delta=valid?directPosition-primaryPosition:0;
  return new Verdict(same,valid,delta,
   valid&&Math.abs(delta)>POSITION_DISAGREEMENT_MS,
   same&&primaryPlaying!=directPlaying);
 }
 private SourceSessionSnapshotPolicy(){}
}
