package pro.celikom.nativeprobe.identitydiag;
/** Replays sustained 0.3.51 clock divergence and Bluetooth correction policy. */
public final class TestClockSupervisor {
 static int checks;
 static void ok(boolean x,String why){checks++;if(!x)throw new AssertionError(why);}
 public static void main(String[] args){
  ClockSupervisor s=new ClockSupervisor();
  ok(s.assess(true,true,false,1160,1000)==ClockSupervisor.Decision.KEEP,"single high drift observation is not terminal");
  ok(s.assess(true,true,false,1156,2200)==ClockSupervisor.Decision.KEEP,"1.2s divergent clock not yet confirmed");
  ok(s.assess(true,true,false,1166,2501)==ClockSupervisor.Decision.RESTORE_SOURCE,"HONOR 1.16s steady discrepancy must restore native");
  s.reset();
  for(int i=0;i<50;i++)ok(s.assess(true,true,false,550,1000+250*i)==ClockSupervisor.Decision.KEEP,"550ms Bluetooth-offset baseline remains undisturbed");
  ok(s.assess(false,true,false,0,14000)==ClockSupervisor.Decision.SEEK,"first alignment is silent seek");
  ok(s.assess(true,true,true,3,14010)==ClockSupervisor.Decision.SEEK,"verified user seek always wins");
  s.reset();
  ok(s.assess(true,true,false,2600,16000)==ClockSupervisor.Decision.KEEP,"large clock jump is debounced");
  ok(s.assess(true,true,false,2700,17001)==ClockSupervisor.Decision.SEEK,"one bounded severe-stall correction before fail-open");
  s.onSeek();
  ok(s.assess(true,true,false,2600,18000)==ClockSupervisor.Decision.KEEP,"no instant repeat seek");
  ok(s.assess(true,true,false,2600,19501)==ClockSupervisor.Decision.RESTORE_SOURCE,"persistent stall cannot loop corrections");
  s.reset();
  ok(s.assess(true,false,false,3000,21000)==ClockSupervisor.Decision.KEEP,"pause does not count as drift");
  ok(s.assess(true,true,false,240,22000)==ClockSupervisor.Decision.KEEP,"normal small clock offset is harmless");
  System.out.println("PASS: "+checks+" unified clock supervisor decisions");
 }
}
