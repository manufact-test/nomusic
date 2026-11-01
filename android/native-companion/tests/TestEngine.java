package pro.celikom.nativeprobe.identitydiag;
import org.json.*;import java.util.*;import java.io.*;import android.os.SystemClock;import android.media.*;import android.media.audiofx.*;import pro.celikom.nativeprobe.AttenuationService;
/** Executes the actual ReplacementEngine with deterministic transport and audio adapters. */
public class TestEngine {
 static int tests;static ProbeService p;static ReplacementEngine e;static NativeApi api;
 static void ok(boolean b,String reason){tests++;if(!b)throw new AssertionError(reason);}
 static PlaybackSource source(String alias,long position,boolean playing){return new PlaybackSource(alias,"Песня","Артист",120000,"https://avatars.yandex.net/get-music-content/1/x.a.42-1/700x700",position,playing,true,1f);}
 static PlaybackSource buffering(long position){
  return new PlaybackSource("1","Песня","Артист",120000,
    "https://avatars.yandex.net/get-music-content/1/x.a.42-1/700x700",
    position,false,true,1f,true,true);
 }
 static void reset(String method){SystemClock.now=1000;AttenuationService.Companion.session=101;api=new NativeApi();NativeApi.api=api;p=new ProbeService();p.current=source("1",1000,true);e=new ReplacementEngine(p);e.identity(LogStore.map("mediaAlias","1","albumId","42","title","Песня","artist","Артист","durationMs",120000L),LogStore.map("candidateTrackId","7","method",method,"editionConflict",false));api.signed=true;}
 static JSONObject found()throws Exception{return new JSONObject().put("found",true).put("replacement_id",1).put("duration_ms",120000);}
 static void resolve()throws Exception{api.resolved.done(found(),null);}
 static void finishJoin(MediaPlayer player){if(player==null||!player.isPlaying()||!e.audioOwner.handoverAwaitingClock())return;String alias=p.current==null?"1":p.current.alias;long base=player.getCurrentPosition();SystemClock.now+=50;player.position=base+50;p.current=source(alias,base+50,true);p.handler.drain();SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS+20;player.position+=ReplacementEngine.UNIFIED_JOIN_MS+20;p.current=source(alias,player.getCurrentPosition(),true);p.handler.drain();}
 static MediaPlayer prepare()throws Exception{resolve();File f=File.createTempFile("engine-test", ".audio");api.downloaded.done(f,null);MediaPlayer player=e.player;player.prepared.onPrepared(player);finishJoin(player);return player;}
 static void playing()throws Exception{reset("ALBUM");e.arm();prepare();ok(e.player!=null&&e.player.isPlaying()&&e.effect!=null&&e.effect.getEnabled()&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT,"prepared replacement passes the decoder clock gate and starts with verified session");}
 public static void main(String[] args)throws Exception {
  reset("ALBUM");AttenuationService.Companion.session=null;e.arm();ok(e.armed()&&e.trustedSession<=0&&e.effect==null,"explicit activation waits for a verified session without muting");MediaPlayer waiting=prepare();ok(!waiting.playing&&e.effect==null,"waiting session cannot start prepared audio");AttenuationService.Companion.session=101;e.update(p.current);ok(waiting.playing&&e.effect!=null,"verified panel attachment resumes pending activation without another tap");
  reset("ALBUM");e.arm();ok(e.effect==null&&e.player==null,"server lookup cannot mute source");resolve();ok(e.preparing&&e.effect==null&&e.player==null,"download cannot mute source");File f=File.createTempFile("engine-test", ".audio");api.downloaded.done(f,null);ok(e.player!=null&&e.effect==null,"unprepared audio cannot mute source");e.player.duration=140000;e.player.prepared.onPrepared(e.player);ok(e.player==null&&e.effect==null&&!f.exists(),"wrong measured duration releases player and deletes audio");
  playing();MediaPlayer first=e.player;p.current=source("1",1000,false);e.update(p.current);ok(!first.playing&&e.effect!=null,"brief source pause keeps prepared audio and attenuation");p.current=source("1",1000,true);e.update(p.current);ok(first.playing&&e.effect!=null,"resume reattaches source effect and resumes replacement");p.current=source("1",60000,true);e.update(p.current);ok(first.position==60000&&first.playing&&e.effect!=null,"seek follows current source without fixed offset");
  p.current=source("2",0,true);e.update(p.current);ok(first.released&&e.player==null&&e.effect==null,"track change restores original");
  reset("ALBUM");e.arm();NativeApi.Result old=api.resolved;p.current=source("2",0,true);old.done(found(),null);ok(api.downloads==0&&e.effect==null,"old resolve callback cannot play for new track");
  ok(PlaybackDuration.safe(180880,180872)&&PlaybackDuration.safe(236090,236173),"matching audio durations keep playing");
  ok(PlaybackDuration.compatible(232450,231120,231096,true)&&
     PlaybackDuration.compatible(272700,272144,272118,true)&&
     PlaybackDuration.compatible(286730,286067,286067,true),
     "recorded 0.3.53 files pass a verified measured-duration tail check");
  ok(!PlaybackDuration.compatible(232450,231120,231096,false)&&
     !PlaybackDuration.compatible(120000,117000,117000,true),
     "unverified candidate or large edition difference cannot bypass safety");
  ok(PlaybackDuration.expectedTail(232450,231096,1354)&&
     !PlaybackDuration.expectedTail(232450,231096,4000),
     "bounded short outro is distinct from unexpected early decoder completion");
  ok(PlaybackDuration.safe(120000,120500)&&!PlaybackDuration.safe(120000,120501),"the tail guard has a deterministic 500ms limit");
  /* A strong album match can accept a bounded measured codec/outro tail. */
  reset("ALBUM");e.arm();api.resolved.done(new JSONObject().put("found",true).put("replacement_id",7).put("duration_ms",119418),null);
  ok(e.player==null&&e.preparing&&api.downloads==1&&e.effect==null,"582ms metadata discrepancy may be measured without muting the original");
  File measuredFile=File.createTempFile("engine-measured", ".audio");api.downloaded.done(measuredFile,null);
  e.player.duration=120000;e.player.prepared.onPrepared(e.player);
  ok(e.ready&&e.effect!=null,"correct 120000ms measured file plays despite misleading 119418ms server metadata");
  /* Admin-approved track IDs automatically accept bounded codec/outro tails. */
  for(int delta:new int[]{582,663}){
   reset("ALBUM");e.arm();int beforeResolve=api.resolves;
   api.resolved.done(new JSONObject().put("found",true).put("replacement_id",7).put("duration_ms",120000-delta),null);
   File candidateFile=File.createTempFile("engine-approved-tail", ".audio");api.downloaded.done(candidateFile,null);
   e.player.duration=120000-delta;e.player.prepared.onPrepared(e.player);
   ok(e.ready&&e.player!=null&&e.effect!=null&&api.resolves==beforeResolve,
      delta+"ms approved album tail starts automatically after the single live resolve");
  }
  /* A 1354ms measured tail is inside the existing bounded policy and must not
     create a confirmation prompt or a second server resolve. */
  reset("ALBUM");e.arm();int beforeApprovedResolve=api.resolves;
  api.resolved.done(new JSONObject().put("found",true).put("replacement_id",7).put("duration_ms",118646),null);
  File approvedTail=File.createTempFile("engine-approved-outro", ".audio");api.downloaded.done(approvedTail,null);
  e.player.duration=118646;e.player.prepared.onPrepared(e.player);
  ok(e.ready&&e.player!=null&&e.effect!=null&&api.resolves==beforeApprovedResolve,
     "approved 1354ms bounded tail starts automatically after one live resolve");
  MediaPlayer shortDecoder=e.player;p.current=source("1",118646,true);
  shortDecoder.completed.onCompletion(shortDecoder);
  ok(e.player==null&&e.effect==null&&e.completedReason==null,
     "approved expected short outro restores the original at the natural tail");
  reset("ALBUM");e.arm();api.resolved.done(new JSONObject().put("found",true).put("replacement_id",7).put("duration_ms",118000),null);
  ok(!e.preparing&&api.downloads==0&&e.effect==null,"metadata discrepancy beyond bounded probe never downloads or mutes");
  reset("ALBUM");e.arm();resolve();NativeApi.AudioResult oldDownload=api.downloaded;e.stop("owner_stop");File stale=File.createTempFile("engine-test", ".audio");oldDownload.done(stale,null);ok(!stale.exists()&&e.player==null,"late download after stop is discarded");
  playing();first=e.player;SystemClock.now+=13*60*1000;p.current=source("1",1000,true);e.update(p.current);ok(e.armed()&&!first.released&&e.effect!=null,"replacement remains enabled past the former twelve-minute limit");
  playing();first=e.player;e.update(null);ok(!first.playing&&e.effect==null&&!first.released,"brief lost source silences replacement and restores original while retaining decoder");SystemClock.now+=1600;e.update(null);ok(first.released&&e.effect==null,"sustained source loss releases retained decoder");
  playing();first=e.player;DynamicsProcessing effect=e.effect;effect.listener.onControlStatusChange(effect,false);ok(!e.armed()&&first.released&&e.effect==null,"effect control loss stops replacement");
  playing();first=e.player;first.error.onError(first,1,2);ok(e.armed()&&first.released&&e.effect==null,"media error restores original and retains automatic mode");
  reset("LEARNED_METADATA");e.arm();ok(api.resolves==1&&e.player==null&&e.effect==null,"unique learned track ID automatically starts its single live resolve without muting the original");prepare();ok(e.effect!=null,"approved learned-metadata replacement starts after server and file checks");e.close();ok(!e.armed()&&e.effect==null&&e.player==null,"service shutdown restores original");
  reset("NONE");e.identity(LogStore.map("mediaAlias","1","albumId","42","title","Песня","artist","Артист","durationMs",120000L),LogStore.map("candidateTrackId",null,"method","NONE"));e.arm();ok(api.resolves==0&&e.player==null,"stale or ambiguous identity hint without a unique current track ID never reaches the approved-replacement resolve");
  reset("ALBUM");e.arm();api.resolved.done(null,"access_denied");ok(e.player==null&&e.effect==null,"server entitlement denial keeps original");
  playing();first=e.player;SystemClock.now+=2000;e.update(p.current);ok(first.released&&e.effect==null,"stale source deadline restores original");
  // Preparation before enabling must be silent and reused at activation.
  reset("ALBUM");e.update(p.current);MediaPlayer warm=prepare();ok(e.ready&&!warm.playing&&e.effect==null,"preparation before arm never changes source audio");int requests=api.resolves;e.arm();ok(e.player==warm&&warm.playing&&api.resolves==requests,"arm reuses prepared audio without downloading again");finishJoin(warm);ok(warm.volume==1f&&e.effect.gain==-100f&&!e.fading,"ramp ends at replacement full volume and source muted after decoder motion");
  DynamicsProcessing sameEffect=e.effect;int attach= DynamicsProcessing.enabledCount;p.current=source("1",60000,true);e.update(p.current);ok(e.effect==sameEffect&&DynamicsProcessing.enabledCount==attach,"seeking does not release or reattach original attenuation");
  // An outstanding asynchronous seek is issued once; timeout restores the source.
  playing();warm=e.player;warm.asyncSeek=true;p.current=source("1",50000,true);e.update(p.current);int seeks=warm.seekCalls;e.update(p.current);ok(warm.seekCalls==seeks&&e.seeking,"pending seek is not repeatedly submitted");SystemClock.now+=2100;p.current=source("1",52100,true);e.update(p.current);ok(warm.released&&e.effect==null&&e.armed(),"seek timeout releases audio but retains automatic recovery");
  // Avoid a second correction for codec/position jitter right after starting.
  playing();warm=e.player;p.current=source("1",1404,true);int count=warm.seekCalls;e.update(p.current);ok(warm.seekCalls==count&&warm.playing,"404ms startup jitter does not cause another seek or source toggle");
  // A new exact-ID track is picked up without pressing arm again.
  playing();warm=e.player;long deadline=e.armedUntil;p.current=source("2",0,true);e.identity(LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),LogStore.map("candidateTrackId","8","method","ALBUM"));MediaPlayer next=prepare();ok(warm.released&&next.playing&&e.armedUntil==deadline,"automatic next track retains activation and deadline");
  // Network failure must retry after backoff without muting the source.
  reset("ALBUM");e.arm();api.resolved.done(null,"network_or_response_error");ok(e.effect==null&&e.armed()&&e.nextLookup>SystemClock.now,"network failure keeps original with automatic retry");int before=api.resolves;SystemClock.now=e.nextLookup;p.current=source("1",1000,true);e.update(p.current);ok(api.resolves==before+1,"network retry occurs without another activation");
  playing();e.suspend("source_disconnected",2000);ok(e.armed()&&e.effect==null,"media connection loss restores source while retaining activation");SystemClock.now+=2000;p.current=source("1",3000,true);e.update(p.current);next=prepare();ok(next.playing,"reconnection with same verified session resumes automatically");
  // Old download cannot change the pending state of a newer track.
  reset("ALBUM");e.arm();resolve();NativeApi.AudioResult previous=api.downloaded;p.current=source("2",0,true);e.identity(LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),LogStore.map("candidateTrackId","8","method","ALBUM"));resolve();File obsolete=File.createTempFile("engine-old", ".audio");previous.done(obsolete,null);ok(e.preparing&&!obsolete.exists(),"late cancelled download cannot clear new preparation state");
  // Old effect callbacks must not stop a new attachment.
  playing();DynamicsProcessing retired=e.effect;android.media.audiofx.AudioEffect.OnControlStatusChangeListener retiredListener=retired.listener;p.current=source("1",1000,false);e.update(p.current);SystemClock.now+=ReplacementEngine.PAUSE_GRACE_MS+20;p.current=source("1",1000,false);p.handler.drain();p.current=source("1",1000,true);e.update(p.current);retiredListener.onControlStatusChange(retired,false);ok(e.armed()&&e.effect!=null,"retired effect callback cannot stop new playback");
  playing();warm=e.player;e.stop("owner_return_original");SystemClock.now+=ReplacementEngine.FADE_MS+20;p.handler.drain();ok(warm.released&&e.effect==null&&!e.armed(),"queued ramp cannot restart audio after owner stop");
  playing();SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS+20;p.current=source("1",1160,true);p.handler.drain();sameEffect=e.effect;p.current=source("1",60000,true);e.update(p.current);ok(e.effect==sameEffect&&e.player!=null&&AudioOwnership.exclusive(e.originalMix,e.player.volume)
     &&((e.seeking&&e.effect.gain==0f&&e.player.volume==0f)
       ||(!e.seeking&&e.effect.gain==-100f&&e.player.volume>0.99f)),
     "synchronous seek safely commits replacement or retains audible original until alignment");
  playing();SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS+20;p.current=source("1",1160,true);p.handler.drain();warm=e.player;e.returnOriginal();ok(!e.armed()&&e.returning&&!warm.released,"manual return disables automatic mode and starts a bounded fade");SystemClock.now+=ReplacementEngine.FADE_MS+20;p.current=source("1",1320,true);p.handler.drain();ok(warm.released&&e.effect==null&&!e.returning,"manual return fade releases the player and original effect");
  // Phone report: seek -> transient false -> seek callback -> false ramp tick -> true.
  playing();SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS+20;p.current=source("1",1160,true);p.handler.drain();warm=e.player;sameEffect=e.effect;int downloads=api.downloads;int resolves=api.resolves;warm.asyncSeek=true;
  p.current=source("1",67670,true);e.update(p.current);
  SystemClock.now+=30;p.current=source("1",67664,false);e.update(p.current);warm.seek.onSeekComplete(warm);
  ok(!warm.playing&&e.player==warm&&e.ready,"seek completion while source paused must not start audio or discard decoder");
  SystemClock.now+=70;p.current=source("1",67664,false);p.handler.drain();
  ok(e.player==warm&&e.effect==sameEffect&&api.downloads==downloads&&api.resolves==resolves,"phone transient false cannot trigger fade recovery or re-download");
  p.current=source("1",67726,true);e.update(p.current);warm.seek.onSeekComplete(warm);
  ok(warm.playing&&e.effect==sameEffect,"phone seek resumes using the same player and original effect");
  /* A real Media3 pause snapshot must retain the prepared decoder after output grant. */
  playing();warm=e.player;SystemClock.now+=50;p.current=source("1",1050,false);e.update(p.current);p.handler.drain();
  ok(e.player==warm&&!warm.playing&&e.ready,"manual pause retains the decoder and silences replacement promptly");
  SystemClock.now+=ReplacementEngine.PAUSE_GRACE_MS+30;p.current=source("1",1050,false);p.handler.drain();
  ok(e.effect==null&&e.player==warm&&!warm.released,"sustained pause restores original effect but retains prepared decoder");
  p.current=source("1",1050,true);e.update(p.current);ok(warm.playing,"sustained pause resumes without network lookup");
  // Returning to the previous song requires live authorization, but not another audio download.
  playing();File retained=e.audioFile;warm=e.player;p.current=source("2",0,true);e.update(p.current);
  ok(retained.exists()&&e.recentAudio.size()==1,"track departure retains one bounded private audio file");
  p.current=source("1",0,true);e.identity(LogStore.map("mediaAlias","1","albumId","42","title","Песня","artist","Артист","durationMs",120000L),LogStore.map("candidateTrackId","7","method","ALBUM"));
  downloads=api.downloads;resolve();ok(api.downloads==downloads&&e.player!=null,"return uses cached audio only after a fresh successful resolve");e.player.prepared.onPrepared(e.player);ok(e.player.playing,"return starts without an unrelated user seek");e.stop("owner_stop");ok(!retained.exists()&&e.recentAudio.isEmpty(),"explicit stop removes retained audio");
  playing();retained=e.audioFile;p.current=source("2",0,true);e.update(p.current);p.current=source("1",0,true);e.update(p.current);downloads=api.downloads;api.resolved.done(found().put("version",2),null);
  ok(api.downloads==downloads+1,"changed replacement version cannot reuse old audio");e.stop("owner_stop");ok(!retained.exists(),"stop also deletes a superseded cached version");
  playing();retained=e.audioFile;p.current=source("2",0,true);e.update(p.current);p.current=source("1",0,true);e.update(p.current);api.resolved.done(null,"access_denied");
  ok(e.player==null&&e.effect==null&&!retained.exists(),"live entitlement denial discards cached audio and cannot play");
  // Rapid multiple seeks preserve one player even when callbacks interleave with temporary pauses.
  playing();warm=e.player;warm.asyncSeek=true;downloads=api.downloads;
  for(int n=0;n<10;n++){p.current=source("1",5000+n*7000,true);e.update(p.current);SystemClock.now+=20;p.current=source("1",5000+n*7000,false);e.update(p.current);warm.seek.onSeekComplete(warm);SystemClock.now+=30;p.handler.drain();p.current=source("1",5000+n*7000,true);e.update(p.current);warm.seek.onSeekComplete(warm);ok(e.player==warm&&warm.playing&&api.downloads==downloads,"rapid seek pulse retains player "+n);}
  e.stop("owner_stop");
  playing();e.stop("owner_return_original");int stoppedResolves=api.resolves;e.update(p.current);ok(api.resolves==stoppedResolves&&e.player==null,"manual return does not immediately pre-download the same file again");
  reset("ALBUM");p.current=null;AttenuationService.Companion.session=null;e.arm();ok(e.armed()&&e.effect==null,"can enable waiting mode before Yandex starts");p.current=source("1",1000,true);e.update(p.current);waiting=prepare();ok(!waiting.playing,"Yandex song alone cannot authorize source attenuation");AttenuationService.Companion.session=101;e.update(p.current);ok(waiting.playing,"late song and panel connection need no second activation");e.close();
  // Owner Bluetooth report: route loss must pause the source and retain activation.
  playing();SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS+20;p.current=source("1",1160,true);p.handler.drain();warm=e.player;sameEffect=e.effect;long routeDeadline=e.armedUntil;downloads=api.downloads;resolves=api.resolves;
  e.headphonesDisconnected();ok(p.pauseRequests==1&&e.waitingForRouteResume&&e.armedUntil==routeDeadline,"headphone loss requests source pause and retains automatic deadline");
  ok(!warm.playing&&e.player==warm&&e.effect==null&&sameEffect.released&&sameEffect.gain==0f,"route loss silences replacement and explicitly resets original gain before releasing effect");
  e.update(p.current);ok(!warm.playing&&e.waitingForRouteResume,"old playing snapshot cannot restart output after route loss");
  p.current=source("1",1160,false);e.update(p.current);ok(e.routePauseObserved&&!warm.playing,"source pause acknowledgement keeps replacement silent");
  SystemClock.now+=400;p.handler.drain();p.current=source("1",1160,true);e.update(p.current);ok(warm.playing&&!e.waitingForRouteResume&&e.effect!=null&&api.downloads==downloads&&api.resolves==resolves,"resume after route pause reuses prepared audio without re-arming or downloads");
  // Pending seek/ramp callbacks cannot make replacement audible on the speaker while waiting.
  playing();warm=e.player;warm.asyncSeek=true;p.current=source("1",50000,true);e.update(p.current);e.headphonesDisconnected();warm.seek.onSeekComplete(warm);SystemClock.now+=ReplacementEngine.FADE_MS+20;p.handler.drain();ok(!warm.playing&&e.effect==null&&e.waitingForRouteResume,"route loss during async seek cancels audible restart and queued fades");
  e.stop("owner_stop");p.current=source("1",50000,false);e.update(p.current);p.current=source("1",50000,true);e.update(p.current);ok(e.player==null&&!e.armed()&&!e.waitingForRouteResume,"explicit stop cancels route recovery");
  reset("ALBUM");e.arm();e.headphonesDisconnected();p.current=source("1",1000,false);e.update(p.current);waiting=prepare();ok(!waiting.playing&&e.effect==null,"download/prepare completed during route pause stays silent");p.current=source("1",1000,true);e.update(p.current);ok(waiting.playing,"source resume starts audio prepared during route pause");e.stop("yandex_audio_session_changed");ok(!e.armed()&&e.player==null,"session change still invalidates automatic route recovery");
  // Completed song is reusable after a live resolve; do not redownload on repeat.
  playing();retained=e.audioFile;e.suspend("replacement_end",30000);ok(retained.exists()&&e.recentAudio.size()==1,"natural end preserves validated file for a later repeat in this run");
  p.current=source("2",0,true);e.identity(LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),LogStore.map("candidateTrackId","8","method","ALBUM"));api.resolved.done(new JSONObject().put("found",false),null);
  p.current=source("1",0,true);e.identity(LogStore.map("mediaAlias","1","albumId","42","title","Песня","artist","Артист","durationMs",120000L),LogStore.map("candidateTrackId","7","method","ALBUM"));downloads=api.downloads;resolve();ok(api.downloads==downloads&&e.player!=null,"return after natural end uses file after fresh authorization");e.close();ok(!retained.exists(),"completed song cache deleted on shutdown");
  // The 0.3.54 HONOR trace shows playWhenReady=true while buffering during seeks.
   playing();warm=e.player;SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS+50;p.current=source("1",1160,true);p.handler.drain();
   p.current=buffering(1160);e.update(p.current);
   ok(warm.playing&&e.pausedAt<0&&e.sourceBufferSince>=0,
      "short play-intent buffering must not interrupt an audible decoder");
   SystemClock.now+=100;p.current=source("1",1260,true);e.update(p.current);
   ok(warm.playing&&e.sourceBufferSince<0,
      "short buffer recovery must avoid a redundant decoder restart");
   p.current=buffering(1260);e.update(p.current);
   SystemClock.now+=350;e.update(p.current);
   ok(!warm.playing&&e.player==warm&&e.pausedAt>=0,
      "longer buffering must hold the prepared decoder without releasing it");
   SystemClock.now+=950;p.handler.drain();
   ok(e.effect==null&&e.player==warm&&!warm.released,
      "long buffering must restore native gain within its bounded grace");
   p.current=source("1",1500,true);e.update(p.current);
   ok(e.player==warm&&api.downloads==1,
      "post-buffer resume must reuse its decoder rather than redownload audio");
   playing();warm=e.player;int prePauseSeeks=warm.seekCalls;
   p.current=source("1",1000,false);e.update(p.current);
   SystemClock.now+=ReplacementEngine.PAUSE_ALIGN_DELAY_MS+50;p.handler.drain();
   ok(warm.seekCalls==prePauseSeeks&&e.audioOwner.state()==AudioOwnership.State.PAUSED,
      "manual pause must not issue the old timed decoder prealignment seek");
   playing();warm=e.player;e.sourceSeekRequested();p.current=buffering(50000);e.update(p.current);
   ok(!warm.playing&&e.pausedAt>=0,
      "buffering after a user seek must immediately silence stale old-position audio");
   playing();warm=e.player;e.outgoingTrackReset(source("1",119000,true));
   ok(e.player==warm&&!warm.released,
      "speculative old-alias reset must retain decoder until confirmed boundary");
   p.current=source("2",0,true);e.update(p.current);
   ok(warm.released&&e.player==null,
      "confirmed next-track boundary must still release old decoder");
   System.out.println("PASS: "+tests+" actual-engine checks: prepare ordering, approved auto-start, pause/resume, seek, track change, late responses, stop, expiry, stale/disconnected source, effect loss, playback error and cleanup");
 }
}
