package pro.celikom.nativeprobe.identitydiag;

/** Test.55: owner HONOR recordings plus Test.53 false-positive replay. */
public final class TestSourceActivityPauseFallback {
 static int assertions;
 static void check(boolean ok,String reason){assertions++;if(!ok)throw new AssertionError(reason);}
 static SourceActivityPauseFallback.Snapshot tick(SourceActivityPauseFallback p,
   String alias,long now,long sourcePosition,boolean exclusive,long mediaAge){
  return p.sample(alias,true,true,false,exclusive,sourcePosition,232330,1f,mediaAge,now);
 }
 public static void main(String[] args){
  SourceActivityPauseFallback p=new SourceActivityPauseFallback();
  check(tick(p,"RASKOL",10000,50000,false,3500).mode==SourceActivityPauseFallback.Mode.LIVE,"initial sample live");
  p.activity(2,"RASKOL",50500,10500);
  p.activity(1,"RASKOL",51000,11000);
  check(!tick(p,"RASKOL",11449,51449,true,4500).override(),"normal transient drop below threshold");
  check(tick(p,"RASKOL",11899,51899,true,4500).mode==SourceActivityPauseFallback.Mode.LIVE,"899ms not yet paused");
  SourceActivityPauseFallback.Snapshot s=tick(p,"RASKOL",11900,51900,true,4500);
  check(s.mode==SourceActivityPauseFallback.Mode.PAUSED&&s.justPaused&&s.positionMs==51000,"sustained UI pause freezes original position");
  check(tick(p,"RASKOL",17000,57000,false,8200).positionMs==51000,"native clock advances but replacement stays paused");
  p.activity(0,"RASKOL",51000,17100);
  check(tick(p,"RASKOL",17200,57500,false,9000).mode==SourceActivityPauseFallback.Mode.PAUSED,"zero players means still paused");
  p.activity(1,"RASKOL",51000,18000);
  s=tick(p,"RASKOL",18500,59000,false,10300);
  check(s.mode==SourceActivityPauseFallback.Mode.RESUMED_CLOCK&&s.positionMs==51500,"source resumes from frozen audible position, not stale Media3 clock");
  check(tick(p,"RASKOL",20000,60000,false,11700).positionMs==53000,"virtual playback position moves at source speed");
  p.activity(2,"RASKOL",53000,20010);
  check(tick(p,"Next",20100,0,false,0).mode==SourceActivityPauseFallback.Mode.LIVE,"real item transition discards any offset");
  p.activity(2,"Next",1500,22000);p.activity(1,"Next",1800,22300);
  check(tick(p,"Next",22500,2000,true,3500).mode==SourceActivityPauseFallback.Mode.LIVE,"Test.53 200ms false quarantine stays live");
  check(tick(p,"Other",22530,0,true,0).mode==SourceActivityPauseFallback.Mode.LIVE,"next item never inherits a candidate");
  // Test.50 stable songs: 22-450ms drop, always no intervention.
  for(int ms: new int[]{10,80,140,250,330,450}){
   p.reset();tick(p,"Good",1000,10000,false,1500);p.activity(2,"Good",10000,1000);
   p.activity(1,"Good",10250,1250);
   check(!tick(p,"Good",1250+ms,10250+ms,true,1500).override(),"no false positive on "+ms+"ms normal drop");
   p.activity(2,"Good",10250+ms,1250+ms);
  }
  p.reset();tick(p,"Seek",1000,10000,false,4500);p.activity(2,"Seek",10000,1000);
  p.activity(1,"Seek",10300,1500);
  check(!tick(p,"Seek",2600,11400,false,4500).override(),"not yet exclusive means cannot pause");
  check(tick(p,"Seek",2600,11400,true,100).mode==SourceActivityPauseFallback.Mode.LIVE,"fresh Media3 event inhibits inferred pause");
  s=tick(p,"Seek",2700,11500,true,1400);
  check(s.mode==SourceActivityPauseFallback.Mode.PAUSED,"valid steady source finally permits pause");
  p.sourceSeek();
  check(tick(p,"Seek",2800,145000,true,1500).mode==SourceActivityPauseFallback.Mode.LIVE,"confirmed seek invalidates virtual clock");
  p.reset();tick(p,"Buffering",1000,0,false,10000);p.activity(2,"Buffering",0,1000);
  p.activity(1,"Buffering",0,1300);
  check(p.sample("Buffering",true,true,true,true,0,232330,1f,10000,5000).mode==SourceActivityPauseFallback.Mode.LIVE,"buffering must never pretend to be user pause");
  System.out.println("PASS: "+assertions+" Test.55 pause and normal transition playback activity checks");
 }
}
