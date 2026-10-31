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

  /* For a fast finger scrub keep the old source inaudible; for a stalled
     decoder restore Yandex after the strict bounded seek-hold deadline. */
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
     &&slow.effect==existingEffect&&existingEffect.gain==-100f&&slow.originalMix==0f,
     "short explicit scrub must not restore old original while decoder seeks");
  android.os.SystemClock.now+=ReplacementEngine.RETAINED_SEEK_JOIN_MS+1;
  TestEngine.p.handler.drain();
  check(slow.seeking&&!seekPlayer.playing&&seekPlayer.volume==0f
     &&slow.effect==existingEffect&&existingEffect.gain==0f&&slow.originalMix==1f,
     "slow seek restores source with same effect by bounded fallback deadline");
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
  accountEngine.accountLeaseCurrent();
  android.os.SystemClock.now+=40;TestEngine.p.handler.drain();
  check(accountPlayer.released&&accountEngine.effect==null&&!accountEngine.armed(),
    "direct account-change notification retires old output without a queued fade");
  accountEngine.close();


  /* Completion during play-intent buffering is not a confirmed end-of-song.
     It is particularly dangerous when Media3 still reports the old alias. */
  TestEngine.playing();
  ReplacementEngine bufferedEnd=TestEngine.e;
  MediaPlayer bufferedEndPlayer=bufferedEnd.player;
  TestEngine.p.current=TestEngine.buffering(3500);
  bufferedEnd.update(TestEngine.p.current);
  bufferedEndPlayer.completed.onCompletion(bufferedEndPlayer);
  check(bufferedEnd.player==bufferedEndPlayer&&!bufferedEndPlayer.released
      &&bufferedEnd.armed()&&bufferedEnd.completedKey==null,
      "transient buffering completion cannot finalize current song");
  android.os.SystemClock.now+=400;bufferedEnd.update(TestEngine.p.current);
  bufferedEndPlayer.completed.onCompletion(bufferedEndPlayer);
  check(bufferedEnd.player==bufferedEndPlayer&&bufferedEnd.audioOwner.state()==AudioOwnership.State.PAUSED,
      "held buffered decoder ignores completion and retains authorization");
  TestEngine.p.current=TestEngine.source("1",3500,true);bufferedEnd.update(TestEngine.p.current);
  check(bufferedEnd.player==bufferedEndPlayer&&!bufferedEndPlayer.released
      &&bufferedEnd.armed(),"same decoder resumes after buffered completion");
  MediaPlayer.OnCompletionListener obsoleteCompletion=bufferedEndPlayer.completed;
  bufferedEnd.sourceBoundary("confirmed_new_media");
  obsoleteCompletion.onCompletion(bufferedEndPlayer);
  check(bufferedEnd.player==null&&bufferedEnd.effect==null
      &&bufferedEndPlayer.released,"old MediaPlayer callback after boundary is inert");
  bufferedEnd.close();

  /* Only the audio authority may clear the initial decoder clock hold.
     A stale handover cannot grant output before native progress is verified. */
  AudioOwnership handover=new AudioOwnership();handover.track("handover");
  DynamicsProcessing handoverFx=new DynamicsProcessing(0,91,null);
  MediaPlayer handoverPlayer=new MediaPlayer();
  handover.prepareSourceEffect(handoverFx);handover.aligning();
  handover.event(AudioOwnership.Event.HANDOVER);
  handover.handoverWaitForClock(true);
  check(handover.handoverAwaitingClock(),"native clock gate acquired by owner");
  rejects(()->handover.grantReplacement(handoverFx),
    "handover cannot grant audible replacement before advancing decoder clock");
  handover.handoverClockValidated();
  handover.grantReplacement(handoverFx);
  check(handoverFx.gain==-100f&&!handover.handoverAwaitingClock(),
    "clock acknowledgement permits only exclusive native source grant");
  handover.restoreSource(handoverPlayer,handoverFx);
  handover.aligning();handover.event(AudioOwnership.Event.HANDOVER);
  handover.handoverWaitForClock(true);
  handover.hold(true);
  check(!handover.handoverAwaitingClock()&&handover.pauseMode()==AudioOwnership.PauseMode.BUFFERING,
    "buffering invalidates the old clock gate and its pending handover command");
  handover.source();handover.stopped();
  check(!handover.handoverAwaitingClock(),
    "retiring the audio owner drops any future clock-completion permission");

  /* Manual return must revoke old handover and refuse stale-account fade
     ticks even without an intervening Media3 onEvents update. */
  TestEngine.playing();ReplacementEngine returningEngine=TestEngine.e;
  MediaPlayer returningPlayer=returningEngine.player;
  android.os.SystemClock.now+=ReplacementEngine.FADE_MS+40;
  TestEngine.p.current=TestEngine.source("1",1400,true);
  TestEngine.p.handler.drain();
  check(returningPlayer.playing&&returningEngine.originalMix==0f,
    "return-account regression starts from exclusively audible replacement");
  long oldReturnEpoch=returningEngine.audioOwner.operationEpoch();
  returningEngine.returnOriginal();
  check(returningEngine.returning&&!returningEngine.armed()
     &&returningEngine.audioOwner.operationEpoch()!=oldReturnEpoch,
     "manual return starts a new owner epoch and revokes original handover");
  TestEngine.api.accountGeneration++;
  android.os.SystemClock.now+=60;TestEngine.p.handler.drain();
  check(returningPlayer.released&&returningEngine.player==null
     &&returningEngine.effect==null&&!returningEngine.returning,
     "old-account return tick cannot keep source muted or decoder alive");
  returningEngine.close();


  /* Prepared decoder callbacks are also asynchronous. Account rotation
     retires them before a Media3 playback state poll can intervene. */
  TestEngine.reset("ALBUM");TestEngine.e.arm();TestEngine.resolve();
  File accountReadyFile=File.createTempFile("prepared-account-rotated",".audio");
  TestEngine.api.downloaded.done(accountReadyFile,null);
  ReplacementEngine stalePreparedEngine=TestEngine.e;MediaPlayer stalePrepared=stalePreparedEngine.player;
  TestEngine.api.accountGeneration++;
  stalePrepared.prepared.onPrepared(stalePrepared);
  check(stalePrepared.released&&stalePreparedEngine.player==null
       &&!stalePreparedEngine.armed()&&stalePreparedEngine.effect==null,
       "onPrepared immediately retires decoder after account change");
  stalePreparedEngine.close();

  /* A native completion while a handover waits for the clock must not end
     the track, even if there is no native seek pending. */
  AudioOwnership waitingFinish=new AudioOwnership();waitingFinish.track("clock");
  waitingFinish.aligning();waitingFinish.event(AudioOwnership.Event.HANDOVER);
  waitingFinish.handoverWaitForClock(true);
  check(!waitingFinish.mayConsumeCompletion(new MediaPlayer()),
       "unverified decoder clock cannot count as complete replacement");
  waitingFinish.handoverClockValidated();
  check(waitingFinish.mayConsumeCompletion(new MediaPlayer()),
       "verified decoder clock permits normal end-of-track handling");
  waitingFinish.stopped();

  System.out.println("PASS unified Android audio transactions: "+checks+" checks");
 }
}
