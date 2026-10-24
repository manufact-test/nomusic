package pro.celikom.nativeprobe.identitydiag;
public class TestRequestPacing {
 static int checks;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 public static void main(String[] args){
  RequestBudget b=new RequestBudget();
  for(int i=0;i<24;i++)check(b.allow("album"+i,12150747L+i*4000),"24 new tracks are accepted");
  check(b.allow("current",12690418L),"recorded last song starts lookup instead of waiting for the old 12-minute boundary");
  check(!b.allow("other",12690419L),"rapid Next is paced");
  check(b.allow("other",12691918L),"current song can retry after 1.5 seconds without restart");
  check(!b.allow("other",12693418L),"same failed album keeps its 30-second cooldown");
  check(b.allow("other",12721918L),"failed album can retry automatically after cooldown");
  for(int i=0;i<300;i++)check(b.allow("long"+i,12800000L+i*2000),"long rapid listening never exhausts a cumulative song quota");
  check(b.recent.size()<=128,"history stays bounded");
  b.clearCooldowns();check(!b.allow("afterNetwork",13398001L),"network recovery does not bypass global pacing");
  check(b.allow("afterNetwork",13399500L),"network recovery remains automatic after short pacing delay");
  System.out.println("PASS: "+checks+" request pacing / recorded 0.3.31 quota regression checks");
 }
}
