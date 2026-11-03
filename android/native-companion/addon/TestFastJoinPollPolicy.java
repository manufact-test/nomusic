package pro.celikom.nativeprobe.identitydiag;
public final class TestFastJoinPollPolicy {
 static int checks;
 static void check(boolean ok,String name){checks++;if(!ok)throw new AssertionError(name);}
 static boolean can(long now,long deadline,boolean playing,boolean effect,boolean identity,boolean armed){
  return FastJoinPollPolicy.eligible(true,now,deadline,armed,true,true,effect,true,playing,identity);
 }
 public static void main(String[] args){
  check(FastJoinPollPolicy.STEP_MS==30&&FastJoinPollPolicy.INITIAL_MS==15,
   "bounded fast sampling never relaxes the clock gate");
  check(can(110,1200,true,false,true,true),"fresh muted decoder gets prompt observer");
  check(can(1200,1200,true,false,true,true),"last sample before deadline allowed");
  check(!can(1201,1200,true,false,true,true),"deadline prevents long-term aggressive polling");
  check(!can(110,1200,false,false,true,true),"pause never forces join");
  check(!can(110,1200,true,true,true,true),"effect attachment ends fast polling");
  check(!can(110,1200,true,false,false,true),"old identity never resampled for replacement");
  check(!can(110,1200,true,false,true,false),"disarmed app never resampled");
  check(!FastJoinPollPolicy.eligible(true,110,1200,true,false,true,false,true,true,true),
   "no decoder means no fast probe");
  check(!FastJoinPollPolicy.eligible(true,110,1200,true,true,false,false,true,true,true),
   "decoder not ready means no fast probe");
  check(!FastJoinPollPolicy.eligible(true,110,1200,true,true,true,false,false,true,true),
   "untrusted session means no fast probe");
  check(!FastJoinPollPolicy.eligible(false,110,1200,true,true,true,false,true,true,true),
   "service must still be alive");
  System.out.println("PASS: "+checks+" bounded passive cold-join poll checks");
 }
}
