package pro.celikom.nativeprobe.identitydiag;
/** The real HONOR 0.3.51 Media3 sequence: SEEK reason can also mean track
 * boundary when media item indices change; stale earlier transitions are ignored.
 */
public final class TestSourceEventArbiter {
 static int assertions;
 static void check(boolean result,String msg){assertions++;if(!result)throw new AssertionError(msg);}
 public static void main(String[] args){
  SourceEventArbiter arb=new SourceEventArbiter();
  check("SAME_ITEM_SEEK".equals(SourceEventArbiter.classifyDiscontinuity(false,true,23,23,"21","21")),
    "same-index SEEK is a same-item seek, not a track boundary");
  check("SEEK_TO_OTHER_ITEM".equals(SourceEventArbiter.classifyDiscontinuity(false,true,23,24,"21","22")),
    "SEEK plus media-item index change is a seek to another item");
  check("AUTOMATIC_BOUNDARY".equals(SourceEventArbiter.classifyDiscontinuity(true,false,23,24,"21","22")),
    "automatic transition remains distinct from a seek");
  check("ITEM_BOUNDARY_UNCLASSIFIED".equals(SourceEventArbiter.classifyDiscontinuity(false,false,23,24,"21","22")),
    "item boundary without a seek/automatic reason remains unclassified");
  check("REPEAT".equals(SourceEventArbiter.classifyMediaItemTransition(0)),
    "Media3 transition reason 0 is repeat");
  check("AUTO".equals(SourceEventArbiter.classifyMediaItemTransition(1)),
    "Media3 transition reason 1 is automatic");
  check("SEEK_TO_OTHER_ITEM".equals(SourceEventArbiter.classifyMediaItemTransition(2)),
    "Media3 transition reason 2 is a seek to another item");
  check("PLAYLIST_CHANGED".equals(SourceEventArbiter.classifyMediaItemTransition(3)),
    "Media3 transition reason 3 is playlist mutation, not proof of manual Next");
  check("PLAYLIST_CHANGED".equals(SourceEventArbiter.classifyTimelineChange(0)),
    "Media3 timeline reason 0 is playlist changed");
  check("SOURCE_UPDATE".equals(SourceEventArbiter.classifyTimelineChange(1)),
    "Media3 timeline reason 1 is source update");

  check(arb.discontinuity("105","105","104","105",21,22,0,0,73000,false,true)==SourceEventArbiter.Action.IGNORE,
   "0.3.51 stale 104->105 replay while 105 is already active must be ignored");
  for(int current=105;current<109;current++){
   String old=Integer.toString(current),next=Integer.toString(current+1);
   check(arb.discontinuity(old,next,old,next,current-83,current-82,0,0,0,false,true)==SourceEventArbiter.Action.BOUNDARY,
     "0.3.51 item-index change is a boundary even when Media3 declares seek "+old);
   check(arb.mediaItem(next,next,next,false,0)==SourceEventArbiter.Action.IGNORE,
     "follow-up stale media item callback cannot double-stop replacement "+next);
  }
  check(arb.discontinuity("106","106","106","106",23,23,3648,61334,101197,false,true)==SourceEventArbiter.Action.IGNORE,
   "stale 3648->61334 seek cannot override live 101197ms position");
  check(arb.discontinuity("106","106","106","106",23,23,101000,101150,101151,false,true)==SourceEventArbiter.Action.SEEK,
   "fresh same-item seek must reach replacement alignment");
  check(arb.discontinuity("107","107","106","106",24,24,8100,9200,9201,false,true)==SourceEventArbiter.Action.IGNORE,
   "coincident timestamp from old song must never seek current decoder");
  check(arb.discontinuity("106","107","107","107",24,24,8100,9200,9201,false,true)==SourceEventArbiter.Action.IGNORE,
   "stale previous alias cannot authorize seek on current song");
  check(arb.discontinuity("107","107","106","107",24,24,8100,9200,9201,false,true)==SourceEventArbiter.Action.IGNORE,
   "mixed old and new position aliases cannot authorize seek");
  check(arb.discontinuity("107","107",null,"107",24,24,8100,9200,9201,false,true)==SourceEventArbiter.Action.SEEK,
   "live seek with missing old position alias remains valid");
  check(arb.discontinuity("106","106","106","106",23,23,119500,0,40,true,false)==SourceEventArbiter.Action.BOUNDARY,
   "confirmed same-alias repeat at beginning is a boundary");
  check(arb.mediaItem("106","107","106",false,4000)==SourceEventArbiter.Action.IGNORE,
   "old event alias cannot stop a newer live track");
  check(arb.mediaItem("106","107","107",false,4000)==SourceEventArbiter.Action.BOUNDARY,
   "current media item transition is accepted");
  check(arb.discontinuity("106","106","105","106",22,23,0,0,0,false,true)==SourceEventArbiter.Action.IGNORE,
   "old replay is not a real seek on the current track");
  SourceEventArbiter.LookaheadEvidence next=new SourceEventArbiter.LookaheadEvidence();
   check(next.observe("a",null,false,false,1000),"unknown timeline recorded");
   check(next.observe("a","b",false,true,1400),"new future candidate observed");
   check(!next.observe("a","b",false,true,1500),"unchanged candidate is not re-logged");
   SourceEventArbiter.LookaheadEvidence.Verdict wrong=next.boundary("c",1700);
   check(wrong.predicted&&!wrong.matched&&!wrong.complete&&wrong.leadMs==300,
     "unreliable lookahead cannot be used to prefetch");
   next.observe("c","d",true,true,2000);
   SourceEventArbiter.LookaheadEvidence.Verdict right=next.boundary("d",3500);
   check(right.observed&&right.predicted&&right.matched&&right.complete&&right.leadMs==1500,
     "confirmed candidate yields read-only timing, not ownership");
   check(!next.boundary("d",3600).observed,"duplicate boundary ignored");
   next.observe("same","same",true,true,4000);
   check(!next.boundary("same",4200).predicted,"same song is not future candidate");
   next.observe("x","y",true,true,4500);next.reset();
   check(!next.boundary("y",4600).observed,"reconnect revokes observed candidate");
   Media3SourceRouter reasonRouter=new Media3SourceRouter(arb,new Media3SourceRouter.Sink(){
   public void boundary(String next,String reason){}
   public void seekRequested(){}
  });
  check(reasonRouter.mediaItem("108","109","109",2,0)==SourceEventArbiter.Action.BOUNDARY,
    "reason-aware router still accepts a current SEEK-to-next-item boundary");
  System.out.println("PASS: "+assertions+" actual HONOR Media3 event arbitration checks");
 }
}
