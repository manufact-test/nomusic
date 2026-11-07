package pro.celikom.nativeprobe.identitydiag;

public class TestSourceActivityProbePolicy {
 static int checks;
 static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
 public static void main(String[] args){
  SourceActivityProbePolicy p=new SourceActivityProbePolicy();
  check(p.sample("113",true,true,false,true,true,2,false,0)==SourceActivityProbePolicy.Action.NONE,"two active media players is normal source+replacement playback");
  check(p.sample("113",true,true,false,true,true,1,false,100)==SourceActivityProbePolicy.Action.NONE,"one-player dip begins debounce");
  check(p.sample("113",true,true,false,true,true,1,false,599)==SourceActivityProbePolicy.Action.NONE,"transient dip shorter than 500ms is ignored");
  check(p.sample("113",true,true,false,true,true,1,false,600)==SourceActivityProbePolicy.Action.PROBE_PAUSE,"stable source-player disappearance requests a read-only pause probe");
  p.probeCompleted(true,600);
  check(p.sample("113",true,true,false,false,false,1,true,700)==SourceActivityProbePolicy.Action.NONE,"confirmed pause is held while only replacement remains");
  check(p.sample("113",true,true,false,false,false,2,true,800)==SourceActivityProbePolicy.Action.NONE,"resume player-count increase is debounced");
  check(p.sample("113",true,true,false,false,false,2,true,1300)==SourceActivityProbePolicy.Action.PROBE_RESUME,"stable source-player return requests a fresh resume snapshot");
  p.probeCompleted(false,1300);
  check(p.sample("113",true,true,false,true,true,2,false,1400)==SourceActivityProbePolicy.Action.NONE,"normal playback after fresh resume does not probe");
  check(p.sample("113",true,true,false,true,true,1,false,1500)==SourceActivityProbePolicy.Action.NONE,"new pause dip starts a new candidate");
  check(p.sample("113",true,true,false,true,true,1,false,2000)==SourceActivityProbePolicy.Action.PROBE_PAUSE,"a later independent pause may be checked again");
  check(p.sample("113",true,true,true,true,true,1,false,3000)==SourceActivityProbePolicy.Action.NONE,"buffering is not classified as user pause");
  check(p.sample("113",true,true,false,true,false,1,false,4000)==SourceActivityProbePolicy.Action.NONE,"inaudible replacement does not create pause probe");
  check(p.sample("114",true,true,false,true,true,1,false,5000)==SourceActivityProbePolicy.Action.NONE,"new alias resets old candidate");
  System.out.println("PASS: "+checks+" source activity pause/resume probe cases");
 }
}
