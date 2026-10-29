package pro.celikom.nativeprobe.identitydiag;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
/** Replays sanitized 0.3.51 observed clock samples (not a fake success trace).
 * Host tests observe decoder commands, not actual Bluetooth acoustic output.
 */
public final class TestHonor051Journal {
 static int checks;
 static void check(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
 public static void main(String[] args)throws Exception {
  if(args.length!=1)throw new IllegalArgumentException("sanitized HONOR journal fixture required");
  Map<String,ClockSupervisor> clocks=new HashMap<>();
  Set<String> restored=new HashSet<>();
  Map<String,Long> restoredAt=new HashMap<>();
  int retainedNativeSamples=0;
  for(String line:Files.readAllLines(Paths.get(args[0]))){
   if(line.trim().isEmpty()||line.startsWith("#"))continue;
   String[] row=line.split("\\s+");
   if(row.length!=5)throw new AssertionError("Malformed sanitized journal row");
   String segment=row[0],mode=row[4];
   long when=Long.parseLong(row[1]),position=Long.parseLong(row[2]),drift=Long.parseLong(row[3]);
   check(position>=0&&Math.abs(drift)<10000,"journal includes bounded clock sample");
   ClockSupervisor guard=clocks.computeIfAbsent(segment,k->new ClockSupervisor());
   if(restored.contains(segment)){retainedNativeSamples++;continue;}
   ClockSupervisor.Decision decision;
   if("paused".equals(mode))decision=guard.assess(true,false,false,drift,when);
   else if("seek".equals(mode)){decision=guard.assess(false,true,false,drift,when);guard.onSeek();}
   else if("playing".equals(mode))decision=guard.assess(true,true,false,drift,when);
   else throw new AssertionError("unknown telemetry mode");
   if("seek".equals(mode))check(decision==ClockSupervisor.Decision.SEEK,"explicit alignment remains available");
   if("paused".equals(mode))check(decision==ClockSupervisor.Decision.KEEP,"pause cannot look like clock drift");
   if(decision==ClockSupervisor.Decision.RESTORE_SOURCE){
    check(segment.equals("B"),"only sustained 1.16s deviation must be rejected");
    restored.add(segment);restoredAt.put(segment,when);
   }else if("playing".equals(mode))check(decision==ClockSupervisor.Decision.KEEP,"good original/BT clock needs no automatic seek");
  }
  check(restored.size()==1&&restored.contains("B"),"persistent HONOR offset must fall back only on affected track");
  check(restoredAt.get("B")<=177730L,"1.16s drift is restored by the next recorded diagnostic sample");
  check(retainedNativeSamples>=8,"subsequent bad-track samples cannot start extra decoder corrections");
  check(!restored.contains("A")&&!restored.contains("C")&&!restored.contains("D"),"normal 240ms/90ms/200ms offsets retained");
  check(!PlaybackDuration.safe(221930,223399),"recorded 1469ms edition mismatch must reject before decoding");
  check(PlaybackDuration.safe(120000,120500),"duration policy remains strict but not over-restrictive");
  System.out.println("PASS: "+checks+" recorded HONOR 0.3.51 clock and wrong-edition replay checks");
 }
}
