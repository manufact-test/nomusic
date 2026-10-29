package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;
/** Sole classifier of asynchronous Media3 transport notifications.
 * Does not start/stop audio. ProbeService serializes each decision on its main handler
 * and sends accepted commands to ReplacementEngine's AudioOwnership gateway.
 */
final class SourceEventArbiter {
 enum Action { IGNORE, BOUNDARY, SEEK }
 Action mediaItem(String previousAlias,String liveAlias,String eventAlias,boolean repeat,long livePosition){
  boolean confirmedRepeat=repeat&&livePosition>=0&&livePosition<2000;
  return SourceTransitionGate.currentItemBoundary(previousAlias,liveAlias,eventAlias,confirmedRepeat)?Action.BOUNDARY:Action.IGNORE;
 }
 static boolean isBoundary(boolean automatic,int oldIndex,int nextIndex,String oldAlias,String nextAlias){
  return automatic||oldIndex!=nextIndex||(oldAlias!=null&&nextAlias!=null&&!Objects.equals(oldAlias,nextAlias));
 }
 Action discontinuity(String previousAlias,String liveAlias,String oldAlias,String eventAlias,
   int oldIndex,int nextIndex,long oldPosition,long newPosition,long livePosition,
   boolean automatic,boolean userSeek){
  if(isBoundary(automatic,oldIndex,nextIndex,oldAlias,eventAlias)){
   boolean repeated=Objects.equals(oldAlias,eventAlias)
     &&SourceTransitionGate.repeatAtBeginning(oldPosition,newPosition,livePosition);
   return SourceTransitionGate.currentItemBoundary(previousAlias,liveAlias,eventAlias,repeated)
     ?Action.BOUNDARY:Action.IGNORE;
  }
  // Matching timestamps do not authorize a stale track's seek.
  if(!userSeek||previousAlias==null||liveAlias==null||eventAlias==null
     ||!Objects.equals(previousAlias,liveAlias)
     ||!Objects.equals(eventAlias,liveAlias)
     ||(oldAlias!=null&&!Objects.equals(oldAlias,liveAlias)))return Action.IGNORE;
  return SourceTransitionGate.currentPositionSeek(livePosition,newPosition)
    ?Action.SEEK:Action.IGNORE;
 }
}
