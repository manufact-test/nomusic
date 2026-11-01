package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;
/** Sole classifier of asynchronous Media3 transport notifications.
 * Does not start/stop audio. ProbeService serializes each decision on its main handler
 * and sends accepted commands to ReplacementEngine's AudioOwnership gateway.
 */
final class SourceEventArbiter {
 enum Action { IGNORE, BOUNDARY, SEEK }
 /* Media3 1.8.x Player reason values. These labels describe controller
    notifications, not a physical UI button press. */
 static boolean isRepeatTransition(int reason){return reason==0;}
 static String classifyMediaItemTransition(int reason){
  switch(reason){
   case 0:return "REPEAT";
   case 1:return "AUTO";
   case 2:return "SEEK_TO_OTHER_ITEM";
   case 3:return "PLAYLIST_CHANGED";
   default:return "UNKNOWN";
  }
 }
 static String classifyTimelineChange(int reason){
  switch(reason){
   case 0:return "PLAYLIST_CHANGED";
   case 1:return "SOURCE_UPDATE";
   default:return "UNKNOWN";
  }
 }
 static String classifyDiscontinuity(boolean automatic,boolean userSeek,int oldIndex,int nextIndex,
                                     String oldAlias,String nextAlias){
  boolean itemChanged=oldIndex!=nextIndex
    ||(oldAlias!=null&&nextAlias!=null&&!Objects.equals(oldAlias,nextAlias));
  if(automatic)return "AUTOMATIC_BOUNDARY";
  if(userSeek&&itemChanged)return "SEEK_TO_OTHER_ITEM";
  if(userSeek)return "SAME_ITEM_SEEK";
  if(itemChanged)return "ITEM_BOUNDARY_UNCLASSIFIED";
  return "POSITION_CHANGE_UNCLASSIFIED";
 }
 /* Read-only probe. Candidate strings stay in memory, never enter diagnostics. */
 static final class LookaheadEvidence {
  String source,next;boolean complete,timeline;long firstSeen=-1;int samples;
  void reset(){source=null;next=null;complete=false;timeline=false;firstSeen=-1;samples=0;}
  boolean observe(String active,String candidate,boolean complete,boolean timeline,long time){
   String valid=active!=null&&candidate!=null&&!candidate.isEmpty()&&!Objects.equals(active,candidate)?candidate:null;
   boolean changed=!Objects.equals(source,active)||!Objects.equals(next,valid)
      ||this.complete!=complete||this.timeline!=timeline;
   if(changed){source=active;next=valid;this.complete=valid!=null&&complete;this.timeline=timeline;
    firstSeen=valid==null?-1:time;samples=0;}
   samples++;return changed;
  }
  static final class Verdict {
   final boolean observed,predicted,matched,complete;final long leadMs;final int samples;
   Verdict(boolean observed,boolean predicted,boolean matched,boolean complete,long leadMs,int samples){
    this.observed=observed;this.predicted=predicted;this.matched=matched;
    this.complete=complete;this.leadMs=leadMs;this.samples=samples;
   }
  }
  Verdict boundary(String actual,long time){
   boolean seen=source!=null,predicted=next!=null;
   Verdict result=new Verdict(seen,predicted,predicted&&actual!=null
    &&!Objects.equals(source,actual)&&Objects.equals(next,actual),complete,
    predicted&&firstSeen>=0?Math.max(0,time-firstSeen):0,samples);
   reset();return result;
  }
 }
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
