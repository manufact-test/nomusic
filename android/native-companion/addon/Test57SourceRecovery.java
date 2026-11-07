package pro.celikom.nativeprobe.identitydiag;
public final class Test57SourceRecovery {
 static int count;
 static void ok(boolean x,String label){count++;if(!x)throw new AssertionError(label);}
 public static void main(String[]args){
  StalledStartRecoveryPolicy p=new StalledStartRecoveryPolicy();
  ok(!p.shouldRecover("129",true,true,false,0,100,10000),"first buffering sample no nudge");
  ok(!p.shouldRecover("129",true,true,false,0,2300,12200),"normal 2s buffering ignored");
  ok(!p.shouldRecover("129",true,true,false,0,3400,13990),"just below time threshold");
  ok(p.shouldRecover("129",true,true,false,0,4400,14400),"Test55 Dym >4s at position0 one authorized attempt");
  ok(!p.shouldRecover("129",true,true,false,0,9000,20000),"never loop same item after attempt");
  ok(!p.shouldRecover("129",false,true,true,5000,1000,21000),"native ready does not nudge");
  ok(!p.shouldRecover("129",true,true,false,0,10000,30000),"one attempt persists across temporary READY");
  p.clear();ok(!p.shouldRecover("129",true,true,false,0,200,31000),"new generation resets timer");
  ok(!p.shouldRecover("129",true,false,false,0,8000,40000),"user-requested pause cannot trigger recovery");
  ok(!p.shouldRecover("129",true,true,false,1800,8000,42000),"mid-song buffering does not reset user seek");
  ok(!p.shouldRecover("129",true,true,false,0,100,45000),"recent Yandex event prevents nudge");
  p.clear();p.shouldRecover("Good",true,true,false,0,200,1000);
  ok(!p.shouldRecover("Good",false,true,true,300,300,1200),"healthy songs immediately READY");
  ok(!p.shouldRecover("Good",true,true,false,0,100,1300),"short second normal buffer never eligible");
  ok(p.shouldRecover("Good",true,true,false,0,6000,6000),"strictly eligible only after long stall");
  ok(!p.shouldRecover("Other",true,true,false,0,100,8000),"new item has independent observation");
  ok(SourceTimelineBoundaryPolicy.confirmedItemChange("67","129",true,true),
   "RASKOL -> Dym live current item wins over stale SAME_ITEM_SEEK 107ms later");
  ok(!SourceTimelineBoundaryPolicy.confirmedItemChange("67","67",true,true),
   "same-item RASKOL seek never mistaken for new item");
  ok(!SourceTimelineBoundaryPolicy.confirmedItemChange("67","129",false,true),
   "no boundary from disconnected controller");
  ok(!SourceTimelineBoundaryPolicy.confirmedItemChange(null,"129",true,true),
   "startup does not invent outgoing track");
  ok(!SourceTimelineBoundaryPolicy.confirmedItemChange("67","129",true,false),
   "no boundary from an unusable media item");
  ok(!SourceTimelineBoundaryPolicy.confirmedItemChange("67",null,true,true),
   "null live alias is not a confirmed different track");
  System.out.println("PASS: "+count+" Test57 source recovery and transition regression cases");
 }
}
