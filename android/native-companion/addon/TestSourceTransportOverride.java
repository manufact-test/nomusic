package pro.celikom.nativeprobe.identitydiag;

public class TestSourceTransportOverride {
 static int checks;
 static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
 static PlaybackSource source(long position,boolean playing,boolean wants,boolean buffering){
  return new PlaybackSource("113","Нас не понимают вообще","Космонавты, RASKOL",232330,null,
    position,playing,true,1.0f,wants,buffering,1000L);
 }
 public static void main(String[] args){
  SourceTransportOverride override=new SourceTransportOverride();
  PlaybackSource live=source(153000,true,true,false);long pauseTime=live.observed;
  PlaybackSource paused=source(153000,false,false,false);
  check(override.accept(live,paused,153000,pauseTime),"same-alias fresh paused snapshot is accepted");
  check(override.active(),"pause override remains active while primary controller is stale");
  PlaybackSource effective=override.apply(live,pauseTime+1000);
  check(!effective.playing&&!effective.wantsToPlay&&!effective.buffering,"stale playing controller is presented to engine as paused");
  check(effective.position==153000,"paused position is frozen at fresh snapshot");
  PlaybackSource primaryPaused=source(153000,false,false,false);
  check(override.apply(primaryPaused,pauseTime+1200)==primaryPaused&&!override.active(),"override clears when primary controller catches up");

  live=source(42000,true,true,false);long seekTime=live.observed;
  PlaybackSource sought=source(153676,true,true,false);
  check(override.accept(live,sought,153676,seekTime),"fresh same-track seek target is accepted");
  effective=override.apply(live,seekTime+1000);
  check(effective.position>=154676,"fresh seek position advances from its own clock");
  check(!override.accept(live,source(42000,true,true,false),153676,seekTime+1000),"stale position cannot confirm a different seek target");
  check(override.active(),"rejected stale seek does not discard the last confirmed snapshot");

  PlaybackSource other= new PlaybackSource("114","Other","Artist",200000,null,5000,true,true,1f,true,false,1000L);
  check(override.apply(other,seekTime+1500)==other&&!override.active(),"track boundary clears prior transport override");
  PlaybackSource buffering=source(153676,false,true,true);
  check(override.accept(source(153676,true,true,false),buffering,-1,buffering.observed),"fresh buffering state is accepted distinctly from pause");
  effective=override.apply(source(153676,true,true,false),buffering.observed+100);
  check(!effective.playing&&effective.wantsToPlay&&effective.buffering,"buffering override preserves play intent without claiming user pause");
  System.out.println("PASS: "+checks+" fresh transport override, seek confirmation and source-boundary cases");
 }
}
