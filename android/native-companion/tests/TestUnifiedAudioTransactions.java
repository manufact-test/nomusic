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

  /* Native original gains are restored before an asynchronous seek rather than
     leaving both the original and decoder silenced through a network stall. */
  TestEngine.playing();
  ReplacementEngine slow=TestEngine.e;MediaPlayer seekPlayer=slow.player;
  android.media.audiofx.DynamicsProcessing existingEffect=slow.effect;
  android.os.SystemClock.now+=ReplacementEngine.FADE_MS+50;
  TestEngine.p.current=TestEngine.source("1",1400,true);TestEngine.p.handler.drain();
  check(seekPlayer.volume>0.99f&&existingEffect.gain==-100f,
    "replacement was exclusively audible before seeking");
  seekPlayer.asyncSeek=true;
  TestEngine.p.current=TestEngine.source("1",60000,true);
  slow.update(TestEngine.p.current);
  check(slow.seeking&&!seekPlayer.playing&&seekPlayer.volume==0f
     &&slow.effect==existingEffect&&existingEffect.gain==0f&&slow.originalMix==1f,
     "slow seek must restore source with same attached effect before decoder alignment");
  slow.returnOriginal();
  check(slow.effect==null&&slow.player==null&&!slow.armed(),
     "manual return during seek cannot promote the muted decoder to audible output");
  slow.close();

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

  /* Explicit owner pause cause replaces older delayed restores. */
  AudioOwnership modes=new AudioOwnership();modes.track("m");
  modes.hold(false);long userLease=modes.pauseLease();
  check(modes.pauseMode()==AudioOwnership.PauseMode.USER,"user pause is classified by owner");
  modes.hold(true);
  check(modes.pauseMode()==AudioOwnership.PauseMode.BUFFERING&&!modes.validPause(userLease),
    "buffering invalidates user-pause timer lease");
  modes.cancelPause();
  check(modes.pauseMode()==AudioOwnership.PauseMode.NONE,"resume clears cause");
  modes.hold(true);modes.source();
  check(modes.pauseMode()==AudioOwnership.PauseMode.NONE,"restoring source clears cause");

  /* Real buffering -> pause: the short timer must not cut a new manual pause. */
  TestEngine.playing();ReplacementEngine switcher=TestEngine.e;
  MediaPlayer retained=switcher.player;
  TestEngine.p.current=TestEngine.buffering(2000);switcher.update(TestEngine.p.current);
  android.os.SystemClock.now+=350;switcher.update(TestEngine.p.current);
  check(switcher.pausedAt>=0&&switcher.audioOwner.pauseMode()==AudioOwnership.PauseMode.BUFFERING,
    "buffering holds existing decoder");
  android.os.SystemClock.now+=100;TestEngine.p.current=TestEngine.source("1",2000,false);
  switcher.update(TestEngine.p.current);
  check(switcher.pauseRestoreDelayMs==ReplacementEngine.PAUSE_GRACE_MS
    &&switcher.audioOwner.pauseMode()==AudioOwnership.PauseMode.USER
    &&switcher.player==retained,"new manual pause supersedes buffering timer");
  android.os.SystemClock.now+=1200;TestEngine.p.handler.drain();
  check(switcher.effect!=null&&!retained.playing,
    "expired old buffering timer cannot restore original during a new user pause");
  switcher.close();

  /* Real pause -> buffering: stale 30s timer must not delay native recovery. */
  TestEngine.playing();switcher=TestEngine.e;retained=switcher.player;
  TestEngine.p.current=TestEngine.source("1",2100,false);
  switcher.update(TestEngine.p.current);
  check(switcher.audioOwner.pauseMode()==AudioOwnership.PauseMode.USER,"native pause observed");
  android.os.SystemClock.now+=100;TestEngine.p.current=TestEngine.buffering(2100);
  switcher.update(TestEngine.p.current);
  check(switcher.pauseRestoreDelayMs==900
    &&switcher.audioOwner.pauseMode()==AudioOwnership.PauseMode.BUFFERING
    &&switcher.player==retained,"buffering gains its own short lease and grace");
  android.os.SystemClock.now+=1000;TestEngine.p.handler.drain();
  check(switcher.effect==null&&!retained.released&&!retained.playing,
    "short buffering grace restores native gain and retains current decoder");
  TestEngine.p.current=TestEngine.source("1",2100,true);switcher.update(TestEngine.p.current);
  check(switcher.player==retained&&switcher.armed(),
    "buffer recovery reuses authorized decoder without another download");
  switcher.close();


  /* Preparation completes while Media3 has play intent but is buffering.
     Data readiness cannot start the muted replacement or seize source effect. */
  TestEngine.reset("ALBUM");TestEngine.e.arm();TestEngine.resolve();
  File bufferedFile=File.createTempFile("ready-while-buffered",".audio");
  TestEngine.api.downloaded.done(bufferedFile,null);
  MediaPlayer bufferedPlayer=TestEngine.e.player;
  TestEngine.p.current=TestEngine.buffering(3500);
  bufferedPlayer.prepared.onPrepared(bufferedPlayer);
  check(TestEngine.e.ready&&!bufferedPlayer.playing&&TestEngine.e.effect==null
      &&TestEngine.e.audioOwner.pauseMode()==AudioOwnership.PauseMode.BUFFERING,
      "buffered prepared callback stages data only; native output remains authoritative");
  int downloadedBefore=TestEngine.api.downloads;
  TestEngine.p.current=TestEngine.source("1",3500,true);
  TestEngine.e.update(TestEngine.p.current);
  check(bufferedPlayer.playing&&TestEngine.e.player==bufferedPlayer
      &&TestEngine.api.downloads==downloadedBefore,
      "prepared buffered decoder starts only on a live playing source without download");
  TestEngine.e.sourceBoundary("buffered_new_track");
  check(bufferedPlayer.released&&TestEngine.e.player==null&&TestEngine.e.effect==null,
      "boundary retires buffered decoder and its future callbacks");
  TestEngine.p.handler.drain();
  check(TestEngine.e.player==null,"old buffered timers cannot reanimate next-song audio");
  TestEngine.e.close();

  /* Even if the effect is valid, the sole owner rejects positive decoder gain
     until the native seek acknowledgement has been consumed. */
  AudioOwnership guarded=new AudioOwnership();guarded.track("guard");
  android.media.audiofx.DynamicsProcessing guardedEffect=new android.media.audiofx.DynamicsProcessing(0,83,null);
  MediaPlayer guardedPlayer=new MediaPlayer();guardedPlayer.asyncSeek=true;
  guarded.prepareSourceEffect(guardedEffect);guarded.aligning();
  guarded.volume(guardedPlayer,0f,guardedEffect);
  check(guarded.issueSeek(guardedPlayer,4000,"guard",guarded.epoch(),
     AudioOwnership.SeekKind.WARM,android.os.SystemClock.now),"guarded warm seek issued");
  rejects(()->guarded.grantReplacement(guardedEffect),
     "in-flight native seek cannot acquire audible output lease");
  guarded.acceptSeekCompletion(guardedPlayer);
  guarded.grantReplacement(guardedEffect);
  guarded.volume(guardedPlayer,1f,guardedEffect);
  check(guardedPlayer.volume==1f&&guardedEffect.gain==-100f,
     "only acknowledged decoder may acquire verified exclusive output");
  guarded.restoreSource(guardedPlayer,guardedEffect);


  /* A stale decoder completion is not a signal that the CURRENT track ended
     while a native seek or user pause has revoked audio permission. */
  TestEngine.playing();ReplacementEngine endEngine=TestEngine.e;
  MediaPlayer ending=endEngine.player;ending.asyncSeek=true;
  TestEngine.p.current=TestEngine.source("1",60000,true);
  endEngine.update(TestEngine.p.current);
  check(endEngine.seeking&&endEngine.audioOwner.seekInFlight(ending),
    "real decoder has an outstanding seek for stale completion test");
  ending.completed.onCompletion(ending);
  check(endEngine.player==ending&&!ending.released&&endEngine.completedKey==null
      &&endEngine.seeking,"completion from pre-seek decoder position is ignored");
  ending.seek.onSeekComplete(ending);
  check(endEngine.player==ending&&endEngine.armed(),
    "valid current seek still resumes after obsolete completion");
  endEngine.close();

  TestEngine.playing();endEngine=TestEngine.e;ending=endEngine.player;
  TestEngine.p.current=TestEngine.source("1",5000,false);
  endEngine.update(TestEngine.p.current);
  ending.completed.onCompletion(ending);
  check(endEngine.player==ending&&!ending.released&&endEngine.ready
      &&endEngine.audioOwner.pauseMode()==AudioOwnership.PauseMode.USER,
    "completion received during manual pause cannot discard reusable decoder");
  TestEngine.p.current=TestEngine.source("1",5000,true);
  endEngine.update(TestEngine.p.current);
  check(endEngine.player==ending&&ending.playing,
    "resumed playback reuses the decoder after ignored paused completion");
  endEngine.close();

  TestEngine.playing();endEngine=TestEngine.e;ending=endEngine.player;
  endEngine.headphonesDisconnected();
  ending.completed.onCompletion(ending);
  check(endEngine.player==ending&&endEngine.waitingForRouteResume
     &&endEngine.armed(),"route loss completion cannot terminate authorized decoder");
  endEngine.close();

  /* Normal replacement completion must still restore source, not be
     accidentally hidden by the new callback gate. */
  TestEngine.playing();endEngine=TestEngine.e;ending=endEngine.player;
  ending.completed.onCompletion(ending);
  check(endEngine.player==null&&endEngine.effect==null&&endEngine.armed(),
    "valid current decoder completion continues to use normal source recovery");
  endEngine.close();


  /* Account generation may rotate before the next Media3 update. Every
     callback that could affect output must immediately revoke old audio. */
  TestEngine.playing();ReplacementEngine accountEngine=TestEngine.e;
  MediaPlayer accountPlayer=accountEngine.player;accountPlayer.asyncSeek=true;
  TestEngine.p.current=TestEngine.source("1",60000,true);
  accountEngine.update(TestEngine.p.current);
  check(accountEngine.seeking&&accountEngine.audioOwner.seekInFlight(accountPlayer),
    "account rotation test starts with pending seek");
  TestEngine.api.accountGeneration++;
  accountPlayer.seek.onSeekComplete(accountPlayer);
  check(accountPlayer.released&&accountEngine.player==null&&!accountEngine.armed()
      &&accountEngine.effect==null,"old-account seek callback immediately revokes old output");
  accountEngine.close();

  TestEngine.playing();accountEngine=TestEngine.e;accountPlayer=accountEngine.player;
  TestEngine.api.accountGeneration++;
  accountPlayer.completed.onCompletion(accountPlayer);
  check(accountPlayer.released&&accountEngine.player==null&&!accountEngine.armed(),
    "old-account media completion cannot grant a new account its decoder");
  accountEngine.close();

  TestEngine.playing();accountEngine=TestEngine.e;accountPlayer=accountEngine.player;
  TestEngine.api.accountGeneration++;
  accountPlayer.error.onError(accountPlayer,1,1);
  check(accountPlayer.released&&accountEngine.player==null&&!accountEngine.armed(),
    "old-account media error stops rather than retrying authorized audio");
  accountEngine.close();

  TestEngine.playing();accountEngine=TestEngine.e;accountPlayer=accountEngine.player;
  TestEngine.api.accountGeneration++;
  android.os.SystemClock.now+=40;TestEngine.p.handler.drain();
  check(accountPlayer.released&&accountEngine.effect==null&&!accountEngine.armed(),
    "queued handover detects account rotation before promoting replacement gain");
  accountEngine.close();

  System.out.println("PASS unified Android audio transactions: "+checks+" checks");
 }
}
