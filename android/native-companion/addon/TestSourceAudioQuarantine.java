package pro.celikom.nativeprobe.identitydiag;

public class TestSourceAudioQuarantine {
 static int checks;
 static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
 public static void main(String[] args){
  SourceAudioQuarantine q=new SourceAudioQuarantine();
  check(!q.trigger(true,true,true,true,"264",2361,2361,900,1,85,105631),"same-session OPEN immediately after a real Media3 transition must be ignored");
  check(!q.trigger(true,true,true,true,"264",2361,2361,4800,2,85,105631),"normal two-player playback cannot prove a hidden restart");
  check(!q.trigger(true,true,true,true,"264",2361,2361,4800,1,900,105631),"old count-one dip is not a recent audio restart");
  check(!q.trigger(true,true,false,true,"264",2361,2361,4800,1,85,105631),"inactive decoder cannot trigger quarantine");
  check(!q.trigger(true,true,true,true,"264",2361,9876,4800,1,85,105631),"different session not treated as a same-session hint");
  check(!q.trigger(true,true,true,true,"264",2361,2361,4800,1,-1,105631),"no activity callback means no guess");
  check(q.trigger(true,true,true,true,"264",2361,2361,4800,1,85,105631),"Test52 recorded post-transition unreported OPEN must fail open");
  check(q.active()&&"264".equals(q.alias()),"source alias is quarantined after unverified restart");
  check(!q.allow("264"),"repeated stale source polls cannot reauthorize old replacement");
  check(!q.allow(null),"missing item cannot reauthorize old replacement");
  check(!q.trigger(true,true,true,true,"264",2361,2361,16000,1,80,116880),"repeated OPEN remains fenced");
  check(q.allow("258"),"new confirmed Media3 item lifts the fence");
  check(!q.active(),"fence clears on a different live alias");
  check(q.allow("258"),"normal replacement allowed after confirmed source change");
  q.trigger(true,true,true,true,"207",2361,2361,4800,1,80,70000);
  q.clear();check(!q.active()&&q.allow("207"),"explicit service stop clears the fence");
  System.out.println("PASS: "+checks+" stale Media3/audio-session fail-open regression cases");
 }
}
