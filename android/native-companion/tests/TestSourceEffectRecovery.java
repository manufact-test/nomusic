package pro.celikom.nativeprobe.identitydiag;
import java.io.File;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;

/** Test.19: DSP failures restore the original and defer a single retry until a new track. */
public final class TestSourceEffectRecovery {
 static int checks;
 static void check(boolean value,String message){
  checks++;if(!value)throw new AssertionError(message);
 }
 static void exercise(String failure)throws Exception{
  TestEngine.reset("ALBUM");
  ReplacementEngine e=TestEngine.e;
  e.arm();
  if("create".equals(failure))DynamicsProcessing.failNextCreate=true;
  else if("control".equals(failure))DynamicsProcessing.denyNextControl=true;
  else if("enable".equals(failure))DynamicsProcessing.failNextEnable=true;
  else throw new AssertionError("invalid test mode");
  MediaPlayer failed=TestEngine.prepare();
  check(failed.released&&!failed.isPlaying(),
   failure+": decoder is retired before source-only playback");
  check(e.effect==null&&e.player==null&&!e.ready,
   failure+": failed effect is cleaned up");
  check(e.armed()&&e.trustedSession==101,
   failure+": verified owner activation remains armed");
  check(e.audioOwner.state()==AudioOwnership.State.RECOVERING,
   failure+": one owner is in recoverable original-only state");
  check(e.completedKey!=null&&e.completedReason!=null,
   failure+": failed track is deferred");
  int resolves=TestEngine.api.resolves;
  for(int i=0;i<5;i++){
   TestEngine.p.current=TestEngine.source("1",1000+i*250,true);
   e.update(TestEngine.p.current);
   TestEngine.p.handler.drain();
  }
  check(TestEngine.api.resolves==resolves&&e.effect==null,
   failure+": no same-track retry storm or audio overlap");
  TestEngine.p.current=TestEngine.source("2",1000,true);
  e.identity(LogStore.map(
   "mediaAlias","2","albumId","42","title","Песня",
   "artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  check(TestEngine.api.resolves==resolves+1,
   failure+": next song automatically re-resolves without manual rearm");
  TestEngine.api.resolved.done(TestEngine.found(),null);
  File file=File.createTempFile("test19-effect-recovered", ".audio");
  TestEngine.api.downloaded.done(file,null);
  MediaPlayer next=e.player;
  check(next!=null,failure+": next track gets fresh decoder");
  next.prepared.onPrepared(next);
  check(e.armed()&&e.effect!=null&&e.effect.hasControl()
       &&e.effect.getEnabled(),
   failure+": next track can attach new effect after transient failure");
  check(e.originalMix>=0.999f&&e.commandedReplacementVolume<=0.001f,
   failure+": source remains audible while decoder prewarms muted");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  exercise("create");
  exercise("control");
  exercise("enable");
  TestEngine.reset("ALBUM");
  ReplacementEngine e=TestEngine.e;e.arm();
  MediaPlayer player=TestEngine.prepare();
  check(player!=null&&e.effect!=null,"preflight fixture ready");
  e.unmute();
  e.trustedSession=0;
  check(!e.mute()&&!e.armed()&&e.effect==null,
   "invalid verified session still requires manual rearm");
  check(e.player==null,
   "fatal unverified session retires own decoder and restores original");
  e.close();
  System.out.println("PASS: Test19 next-track DSP recovery "+checks+" checks");
 }
}
