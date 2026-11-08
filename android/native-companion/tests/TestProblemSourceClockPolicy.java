package pro.celikom.nativeprobe.identitydiag;
public final class TestProblemSourceClockPolicy {
 static int checks;
 static void check(boolean cond,String why){checks++;if(!cond)throw new AssertionError(why);}
 public static void main(String[] args){
  ProblemSourceClockPolicy p=new ProblemSourceClockPolicy();
  check(!p.observe("626",110904,215000,true,true,1000),"first sample");
  for(int t=1250;t<4000;t+=250)
   check(!p.observe("626",110904+(t-1000),215000,true,true,t),"healthy moving source");
  check(!p.observe("626",110904,215000,false,true,4000),"paused reset");
  check(!p.observe("626",110904,215000,true,true,4500),"start stalled clock observation");
  check(!p.observe("626",110905,215000,true,true,6300),"wait for two seconds");
  check(p.observe("626",110904,215000,true,true,6701),"frozen READY clock is detected");
  check(!p.observe("626",110904,215000,true,true,9000),"report only once");
  check(!p.observe("626",111230,215000,true,true,9250),"renewed motion resets stale state");
  check(!p.observe("626",111230,215000,true,false,12000),"buffering is not a frozen clock");
  check(!p.observe("626",213950,215000,true,true,13000),"near end ignored");
  check(!p.observe("other",10,215000,true,true,14000),"new track reset");
  check(!p.observe(null,10,215000,true,true,15000),"missing track reset");
  System.out.println("PASS: "+checks+" guarded source clock stall policy checks");
 }
}
