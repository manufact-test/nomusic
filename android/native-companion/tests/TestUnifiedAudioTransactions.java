package pro.celikom.nativeprobe.identitydiag;
import java.io.File;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
/* Release gate: preparation is data-only; command ownership is single and revocable. */
public final class TestUnifiedAudioTransactions {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static void rejects(Runnable f,String why){boolean failed=false;try{f.run();}catch(IllegalStateException expected){failed=true;}check(failed,why);}
 public static void main(String[] args)throws Exception {
  AudioOwnership a=new AudioOwnership();a.track("one");a.preparing();
  AudioOwnership.Ticket data=a.ticket("one",2,11,3,120000);
  a.event(AudioOwnership.Event.PREPARE_READY);
  check(a.state()==AudioOwnership.State.PREPARING,"ready event cannot acquire audio");
  a.event(AudioOwnership.Event.SEEK);
  check(a.dataCurrent(data,2,"one",11,3,120000),"current audio data survives seek");
  check(!a.commandCurrent(data,2,"one",11,3,120000),"stale commands cannot survive seek");
  a.paused();a.event(AudioOwnership.Event.PAUSE);
  a.event(AudioOwnership.Event.PREPARE_READY);
  check(a.state()==AudioOwnership.State.PAUSED,"prepared file cannot exit pause");
  rejects(a::preparing,"paused output rejects background preparation");
  a.event(AudioOwnership.Event.BUFFERING);a.cancelPause();a.event(AudioOwnership.Event.RESUME);
  check(!a.commandCurrent(data,2,"one",11,3,120000),"buffer/resume revoke command");
  check(!a.dataCurrent(data,3,"one",11,3,120000),"account renewal revokes old data");
  check(!a.dataCurrent(data,2,"one",12,3,120000),"replacement mismatch rejects data");
  check(!a.dataCurrent(data,2,"one",11,4,120000),"version mismatch rejects data");
  check(!a.dataCurrent(data,2,"one",11,3,120010),"duration mismatch rejects data");
  DynamicsProcessing fx=new DynamicsProcessing(0,7,null);a.prepareSourceEffect(fx);
  a.grantReplacement(fx);
  rejects(a::preparing,"active replacement rejects background takeover");
  a.restoreSource(new MediaPlayer(),fx);a.retireDecoder();
  check(!a.dataCurrent(data,2,"one",11,3,120000),"decoder retirement revokes data lease");
  for(int i=0;i<10;i++){a.invalidate("skip");a.track("skip-"+i);a.preparing();
   AudioOwnership.Ticket old=a.ticket("skip-"+i,2,11,3,120000);
   a.event(AudioOwnership.Event.BOUNDARY);a.invalidate("next");
   check(!a.dataCurrent(old,2,"skip-"+i,11,3,120000),"ten rapid skips retire all callbacks");
  }
  a.track("repeat");a.preparing();AudioOwnership.Ticket repeat=a.ticket("repeat",2,11,3,120000);
  a.invalidate("same_song_repeat");a.track("repeat");
  check(!a.dataCurrent(repeat,2,"repeat",11,3,120000),"same media identity repeat has a new epoch");
  a.event(AudioOwnership.Event.ROUTE_LOSS);a.stopped();
  rejects(a::preparing,"stopped output cannot prepare");

  TestEngine.reset("ALBUM");TestEngine.e.arm();TestEngine.resolve();
  File f=File.createTempFile("transaction-paused",".audio");
  TestEngine.api.downloaded.done(f,null);MediaPlayer mp=TestEngine.e.player;
  TestEngine.p.current=TestEngine.source("1",1800,false);
  mp.prepared.onPrepared(mp);
  check(TestEngine.e.ready&&!mp.playing&&TestEngine.e.effect==null,
   "decoder ready while user paused must not start or mute native audio");
  check(TestEngine.e.audioOwner.state()==AudioOwnership.State.PAUSED,
   "source pause survives incoming prepared callback");
  TestEngine.e.stop("owner_logout");
  check(mp.released&&TestEngine.e.player==null&&TestEngine.e.effect==null,
   "stop releases prepared decoder without changing native playback");
  System.out.println("PASS unified Android audio transactions: "+checks+" checks");
 }
}
