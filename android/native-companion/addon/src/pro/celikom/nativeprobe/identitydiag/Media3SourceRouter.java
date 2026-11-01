package pro.celikom.nativeprobe.identitydiag;

/** Production Media3 callback dispatcher, shared with host replay tests.
 * The caller supplies the controller's live alias and position: callbacks may
 * describe an already superseded item, or a SEEK may cross a media-item index.
 */
final class Media3SourceRouter {
 interface Sink {
  void boundary(String nextAlias,String reason);
  void seekRequested();
 }
 private final SourceEventArbiter arbiter;
 private final Sink sink;
 Media3SourceRouter(SourceEventArbiter arbiter,Sink sink){this.arbiter=arbiter;this.sink=sink;}

 SourceEventArbiter.Action mediaItem(String active,String live,String next,boolean repeat,long livePosition){
  SourceEventArbiter.Action action=arbiter.mediaItem(active,live,next,repeat,livePosition);
  if(action==SourceEventArbiter.Action.BOUNDARY)sink.boundary(next,"media_item_transition");
  return action;
 }
 SourceEventArbiter.Action mediaItem(String active,String live,String next,int transitionReason,long livePosition){
  return mediaItem(active,live,next,SourceEventArbiter.isRepeatTransition(transitionReason),livePosition);
 }

 SourceEventArbiter.Action discontinuity(String active,String live,String oldAlias,String nextAlias,
    int oldIndex,int nextIndex,long oldPosition,long nextPosition,long livePosition,
    boolean automatic,boolean userSeek){
  SourceEventArbiter.Action action=arbiter.discontinuity(active,live,oldAlias,nextAlias,
    oldIndex,nextIndex,oldPosition,nextPosition,livePosition,automatic,userSeek);
  if(action==SourceEventArbiter.Action.BOUNDARY)sink.boundary(nextAlias,"position_transition");
  else if(action==SourceEventArbiter.Action.SEEK)sink.seekRequested();
  return action;
 }
}
