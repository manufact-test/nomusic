package pro.celikom.nativeprobe.identitydiag;
/** Replays sustained 0.3.51 clock divergence and Bluetooth correction policy. */
public final class TestClockSupervisor {
 static int checks;
 static void ok(boolean x,String why){checks++;if(!x)throw new AssertionError(why);}
 public static void main(String[] args){
  ClockSupervisor s=new ClockSupervisor();
  ok(s.assess(true,true,false,1160,1000)==ClockSupervisor.Decision.KEEP,"single high drift observation is not terminal");
  ok(s.assess(true,true,false,1156,1500)==ClockSupervisor.Decision.KEEP,"short medium divergence is observed without recovery churn");
  ok(s.assess(true,true,false,1166,1751)==ClockSupervisor.Decision.SEEK,"sustained 1.16s discrepancy gets one silent resync before permanent fallback");
  s.onSeek();
  ok(s.assess(true,true,false,1140,1800)==ClockSupervisor.Decision.KEEP,"medium correction resets observation window");
  ok(s.assess(true,true,false,1180,3299)==ClockSupervisor.Decision.KEEP,"no repeat correction before fallback threshold");
  ok(s.assess(true,true,false,1160,3301)==ClockSupervisor.Decision.RESTORE_SOURCE,"failed moderate correction restores native rather than looping");
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
  s.reset();
  ok(s.assess(true,true,false,950,24000)==ClockSupervisor.Decision.KEEP,"transient moderate drift alone cannot trigger seek");
  ok(s.assess(true,true,false,500,24500)==ClockSupervisor.Decision.KEEP,"normal timing clears transient warning");
  ok(s.assess(true,true,false,920,24700)==ClockSupervisor.Decision.KEEP,"moderate timer restarts after low drift");
  ok(s.assess(true,true,false,920,25451)==ClockSupervisor.Decision.SEEK,"new sustained moderate drift can be corrected once");
  s.onSeek();
  ok(s.assess(true,true,false,300,25600)==ClockSupervisor.Decision.KEEP,"healthy post-seek sample does not rearm correction budget");
  ok(s.assess(true,true,false,1000,26000)==ClockSupervisor.Decision.KEEP,"drift after prior correction observed");
  ok(s.assess(true,true,false,1000,27501)==ClockSupervisor.Decision.RESTORE_SOURCE,"one correction per track even after one healthy sample");
  System.out.println("PASS: "+checks+" unified clock supervisor decisions");
 }
}
