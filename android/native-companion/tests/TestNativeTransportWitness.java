package pro.celikom.nativeprobe.identitydiag;
final class TestNativeTransportWitness {
 static void yes(boolean b,String why){if(!b)throw new AssertionError(why);}
 static NativeTransportWitness.Verdict step(NativeTransportWitness w,String alias,String id,
   boolean same,int legacyState,long legacyAge,boolean media3Playing,long eventAge,long now){
  return w.observe(alias,id,same,legacyState,80000,legacyAge,80500,media3Playing,
       media3Playing,3,eventAge,now);
 }
 public static void main(String[] a){
  NativeTransportWitness w=new NativeTransportWitness();
  yes(!NativeTransportWitness.watched("85025192"),"control not watched");
  yes(!NativeTransportWitness.watched("78608850"),"control not watched");
  yes(NativeTransportWitness.watched("42884423"),"RASKOL");
  yes(NativeTransportWitness.watched("39949113"),"Dym");
  yes(!w.noteUnavailable("722","85025192"),"control no secondary observer");
  yes(w.noteUnavailable("722","42884423"),"RASKOL secondary source absence");
  yes(!w.noteUnavailable("722","42884423"),"no repeated absence spam");
  yes(w.noteUnavailable("785","39949113"),"Dym can report absence separately");
  yes(!step(w,"722","85025192",true,2,10,true,1000,1000).restore,"control cannot fall back");
  yes(!step(w,"722","42884423",false,2,10,true,1000,1050).restore,"unmatched metadata");
  yes(!step(w,"722","42884423",true,2,3000,true,1000,1400).restore,"stale legacy");
  yes(!step(w,"722","42884423",true,2,10,true,100,1500).restore,"new Media3 event");
  yes(!step(w,"722","42884423",true,3,10,true,800,1900).restore,"playing agrees");
  w.noteSeek("722","42884423",81218,2000);
  NativeTransportWitness.Verdict early=step(w,"722","42884423",true,3,30,true,1200,2320);
  yes(early.report&&"post_seek_early".equals(early.stage),"seek trace early");
  yes(early.freshAfterSeek,"fresh timestamp after seek");
  NativeTransportWitness.Verdict late=step(w,"722","42884423",true,3,2000,true,2200,3500);
  yes(late.report&&"post_seek_late".equals(late.stage),"seek trace late");
  yes(!late.freshState,"stale timestamp not presentation proof");
  yes(!step(w,"722","42884423",true,2,100,true,1000,4000).restore,"need two samples");
  yes(!step(w,"722","42884423",true,2,100,true,1000,4200).restore,"bounded confirmation");
  yes(step(w,"722","42884423",true,2,100,true,1000,4350).restore,"fresh matching pause disagreement fail closed");
  yes(w.quarantined("722","42884423"),"quarantine lasts for song");
  yes(!w.quarantined("785","39949113"),"next song not affected");
  yes(!step(w,"785","39949113",true,3,10,true,800,5000).restore,"next normal");
  yes(!w.quarantined("785","39949113"),"track boundary clears quarantine");
  yes(!step(w,"785","39949113",true,2,10,false,1200,5300).restore,"both paused safe");
  yes(!step(w,"785","39949113",true,2,10,true,1200,5600).restore,"initial disagreement");
  yes(step(w,"785","39949113",true,2,10,true,1200,5950).restore,"Dym fail closed");
  System.out.println("PASS TestNativeTransportWitness");
 }
}
