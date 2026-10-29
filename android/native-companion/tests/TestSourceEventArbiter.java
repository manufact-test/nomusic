package pro.celikom.nativeprobe.identitydiag;
/** The real HONOR 0.3.51 Media3 sequence: SEEK reason can also mean track
 * boundary when media item indices change; stale earlier transitions are ignored.
 */
public final class TestSourceEventArbiter {
 static int assertions;
 static void check(boolean result,String msg){assertions++;if(!result)throw new AssertionError(msg);}
 public static void main(String[] args){
  SourceEventArbiter arb=new SourceEventArbiter();
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
  check(arb.discontinuity("106","106","106","106",23,23,119500,0,40,true,false)==SourceEventArbiter.Action.BOUNDARY,
   "confirmed same-alias repeat at beginning is a boundary");
  check(arb.mediaItem("106","107","106",false,4000)==SourceEventArbiter.Action.IGNORE,
   "old event alias cannot stop a newer live track");
  check(arb.mediaItem("106","107","107",false,4000)==SourceEventArbiter.Action.BOUNDARY,
   "current media item transition is accepted");
  check(arb.discontinuity("106","106","105","106",22,23,0,0,0,false,true)==SourceEventArbiter.Action.IGNORE,
   "old replay is not a real seek on the current track");
  System.out.println("PASS: "+assertions+" actual HONOR Media3 event arbitration checks");
 }
}
