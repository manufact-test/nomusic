package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;
/** A live Media3 current-item change takes precedence over a delayed
 * discontinuity callback that still describes the outgoing item. */
final class SourceTimelineBoundaryPolicy {
 static boolean confirmedItemChange(String previousAlias,String liveAlias,
   boolean sourceConnected,boolean currentItemHasIdentity){
  return sourceConnected&&currentItemHasIdentity
    &&previousAlias!=null&&!previousAlias.isEmpty()
    &&liveAlias!=null&&!liveAlias.isEmpty()
    &&!Objects.equals(previousAlias,liveAlias);
 }
}
