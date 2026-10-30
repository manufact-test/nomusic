package pro.celikom.nativeprobe.identitydiag;

/** Device-diagnostic invariants: commanded silence, not measured output. */
public final class TestAudioContinuityMonitor {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 public static void main(String[] args){
  AudioContinuityMonitor monitor=new AudioContinuityMonitor();
  check(monitor.observe(100,"track1","seek",true,true,false,0f)==null,"start commanded seek gap");
  check(monitor.observe(300,"track1","fade",true,true,true,0f)==null,"silent decoder does not end gap");
  AudioContinuityMonitor.Finding gap=monitor.observe(560,"track1","fade",true,true,true,0.05f);
  check(gap!=null&&"commanded_silence".equals(gap.kind)&&gap.durationMs==460,
      "0.46s commanded silence is reported exactly");
  check("seek".equals(gap.cause)&&"track1".equals(gap.trackId),"gap retains original reason and track");
  check(monitor.observe(600,"track1","fade",true,true,true,0.3f)==null,"no duplicate gap report");
  check(monitor.observe(700,"track1","handover",true,false,true,0.5f)!=null,
      "two simultaneous positive commands are explicitly flagged");
  check(monitor.observe(720,"track1","handover",true,false,true,0.6f)==null,
      "overlap warning is not repeated every volume tick");
  check(monitor.observe(750,"track1","restore",true,false,false,0f)==null,
      "no overlap after replacement stops");
  check(monitor.observe(1000,"track1","pause",false,true,false,0f)==null,
      "user pause is not misreported as commanded playback gap");
  check(monitor.observe(1010,"track1","seek",true,true,false,0f)==null,"new short gap starts");
  check(monitor.observe(1030,"track1","resume",true,true,true,0.3f)==null,
      "sub-40ms gap does not become a distracting alert");
  System.out.println("PASS: "+checks+" command-level continuity and overlap diagnostics");
 }
}
