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
  /* Account changes cannot inherit a previous user's resolve, decoder or entitlement. */
  TestEngine.playing();
  ReplacementEngine active=TestEngine.e;MediaPlayer old=active.player;
  TestEngine.api.accountGeneration++;
  active.update(TestEngine.p.current);
  check(old.released&&active.effect==null&&active.player==null&&!active.armed(),
    "account rotation restores original and revokes the old decoder");
  TestEngine.reset("ALBUM");TestEngine.e.arm();TestEngine.resolve();
  NativeApi.AudioResult pending=TestEngine.api.downloaded;
  TestEngine.api.accountGeneration++;
  File stale=File.createTempFile("account-stale",".audio");pending.done(stale,null);
  check(!stale.exists()&&TestEngine.e.player==null,
    "download from previous account can never attach a decoder");
  TestEngine.e.update(TestEngine.p.current);
  check(!TestEngine.e.armed()&&!TestEngine.e.preparing,
    "account rollover clears an otherwise stuck preparation");

  /* One native callback has no request ID. Do not submit a second seek until
     the first has truly acknowledged; its stale output epoch never becomes new. */
  AudioOwnership single=new AudioOwnership();single.track("single");single.aligning();
  MediaPlayer silent=new MediaPlayer();silent.asyncSeek=true;
  long sourceEpoch=single.epoch();
  check(single.issueSeek(silent,3000,"single",sourceEpoch,AudioOwnership.SeekKind.WARM,1000),
    "first native seek accepted");
  single.event(AudioOwnership.Event.PAUSE);
  check(!single.issueSeek(silent,60000,"single",sourceEpoch,AudioOwnership.SeekKind.ALIGNMENT,1100)
       &&silent.seekCalls==1,"canceled warm seek must serialize before new seek");
  AudioOwnership.SeekAck staleAck=single.acceptSeekCompletion(silent);
  check(staleAck.kind==AudioOwnership.SeekKind.WARM
       &&staleAck.operationEpoch!=single.operationEpoch(),
       "old native callback cannot carry current audio command permission");
  check(single.issueSeek(silent,60000,"single",sourceEpoch,AudioOwnership.SeekKind.ALIGNMENT,1200)
       &&silent.seekCalls==2,"new seek starts only after old callback consumed");
  check(single.acceptSeekCompletion(silent).kind==AudioOwnership.SeekKind.ALIGNMENT,
    "second completion belongs exclusively to new seek");
  check(single.acceptSeekCompletion(silent)==null,"duplicated completion is ignored");
  single.retireDecoder();

  /* Real streaming decoder: user seeks while a warm seek is still in flight.
     The old fade is canceled and original audio restored immediately. */
  TestStreamingEngine.Buffer buffering=TestStreamingEngine.start();
  ReplacementEngine engine=TestEngine.e;MediaPlayer nativePlayer=engine.player;
  nativePlayer.asyncSeek=true;android.os.SystemClock.now+=640;nativePlayer.position+=40;
  TestEngine.p.current=TestEngine.source("1",1640,true);
  TestEngine.p.handler.drain();
  check(engine.audioOwner.seekInFlight(nativePlayer)&&nativePlayer.seekCalls==2,
    "warm alignment owns one pending native seek");
  engine.sourceSeekRequested();
  TestEngine.p.current=TestEngine.source("1",60000,true);engine.update(TestEngine.p.current);
  check(nativePlayer.seekCalls==2&&!nativePlayer.playing
      &&engine.effect==null&&nativePlayer.volume==0f,
      "explicit seek cancels fade, restores original and defers native seek");
  nativePlayer.seek.onSeekComplete(nativePlayer);
  check(nativePlayer.seekCalls==3&&engine.seeking&&!nativePlayer.playing,
      "old warm callback permits a new native seek but cannot authorize output");
  nativePlayer.seek.onSeekComplete(nativePlayer);
  check(nativePlayer.playing&&engine.player==nativePlayer&&engine.effect!=null,
      "new seek completes with retained decoder and verified exclusive handover");
  engine.close();

  /* Warm seek canceled by a genuine pause must not be mistaken for resume seek. */
  buffering=TestStreamingEngine.start();engine=TestEngine.e;nativePlayer=engine.player;
  nativePlayer.asyncSeek=true;android.os.SystemClock.now+=640;nativePlayer.position+=40;
  TestEngine.p.current=TestEngine.source("1",1640,true);TestEngine.p.handler.drain();
  check(engine.audioOwner.seekInFlight(nativePlayer),"warm native seek pending before pause");
  TestEngine.p.current=TestEngine.source("1",1640,false);engine.update(TestEngine.p.current);
  TestEngine.p.current=TestEngine.source("1",60000,true);engine.update(TestEngine.p.current);
  check(nativePlayer.seekCalls==2&&!nativePlayer.playing,
      "resume must not overlap the canceled native warm seek");
  nativePlayer.seek.onSeekComplete(nativePlayer);
  check(nativePlayer.seekCalls==3&&engine.seeking&&!nativePlayer.playing,
      "canceled warm completion triggers latest source alignment only");
  nativePlayer.seek.onSeekComplete(nativePlayer);
  check(engine.player==nativePlayer&&nativePlayer.playing,
      "post-pause alignment returns to the live song without new decoder");
  engine.close();
  System.out.println("PASS unified Android audio transactions: "+checks+" checks");
 }
}
