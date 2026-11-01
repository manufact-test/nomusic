package pro.celikom.nativeprobe.identitydiag;
import android.media.*;
import android.media.audiofx.*;
import android.os.*;
import android.content.Context;
import org.json.*;
import java.io.*;
import java.util.*;
/** User-enabled automatic replacement within the foreground service lifetime. */
final class ReplacementEngine {
  static final long PREPARED_MS=60000, SEEK_TIMEOUT_MS=2000, HANDOVER_DRIFT_MS=350, STREAM_SEEK_TIMEOUT_MS=12000, FADE_MS=360,
  STRICT_STREAM_JOIN_DRIFT_MS=100, STRICT_JOIN_BUDGET_MS=3000, WARM_CALLBACK_LEAD_MS=70, PAUSE_GRACE_MS=30000, PAUSE_RESUME_FADE_MS=180, PAUSE_ALIGN_DELAY_MS=160, PAUSE_ALIGN_TOLERANCE_MS=85, UNIFIED_JOIN_MS=160, RETAINED_SEEK_JOIN_MS=260;
 final ProbeService owner; final NativeApi api;
 String status="Замена выключена",identityKey,trackId,method="NONE",lookupKey;
 JSONObject descriptor; long descriptorUntil,nextLookup,armedUntil,preparedAt,seekStarted,seekBudget=SEEK_TIMEOUT_MS,fadeStarted,transition,pausedAt=-1;
 long pauseRestoreDelayMs=PAUSE_GRACE_MS,sourceBufferSince=-1;
 final AudioOwnership audioOwner=new AudioOwnership();
 AudioOwnership.Ticket prepareTicket;
 long authorizationAccount=-1;
 final AudioContinuityMonitor continuity=new AudioContinuityMonitor();float commandedReplacementVolume;
 volatile long generation; int trustedSession=-1,failures,seekCorrections;
 final BufferRecoveryGate bufferGate=new BufferRecoveryGate();BufferedAudio streaming;boolean bufferWaiting;String streamFallbackKey;
 MediaPlayer player; DynamicsProcessing effect; LoudnessEnhancer loudness; File audioFile;
 float originalMix=1f; boolean ready,closed,preparing,seeking,fading,aligned,returning,preloadAllowed=true,waitingForRouteResume,routePauseObserved,resumePositionRetained,resumeFadePending,seekHoldActive,sourceSeekedThisTrack,pendingStreamScrubJoin,streamSeekWaitLogged,durationConfirmationRequired; String lastSync="";
 final ClockSupervisor clockSupervisor=new ClockSupervisor();PlaybackSource previousSource;boolean explicitSourceSeek;long unavailableSince=-1,lastSyncAt=-1,lastLoggedDrift;String completedKey,completedReason;long completedPosition,resumeDrift;
 final Set<String> confirmed=new HashSet<>();
 // Private, bounded to this foreground run. Every reuse requires a new live resolve.
 static final long CACHE_BYTES=62914560;
 final LinkedHashMap<String,File> recentAudio=new LinkedHashMap<>();
 String audioKey(JSONObject j){return trackId+"|"+j.optLong("replacement_id")+"|"+j.optLong("version")+"|"+j.optLong("duration_ms")+"|"+j.optString("mime_type","audio/mpeg");}
 /* 0.3.74 HONOR: 24 WARM callbacks took 40..155ms, but reusing an old
    ALIGNMENT ACK predicted up to 250ms and drove the decoder 177ms AHEAD.
    An ALIGNMENT HTTP-range latency is not a WARM latency estimator. Keep
    one conservative lead close to the observed 60..80ms warm median.
    Transport times cannot establish PCM phase or speaker presentation. */
 static long predictedWarmLeadMs(){return WARM_CALLBACK_LEAD_MS;}
 static long predictedWarmTargetMs(long sourceMs,long durationMs){
  return Math.max(0,Math.min(Math.max(0,durationMs-151),sourceMs+WARM_CALLBACK_LEAD_MS));
 }
 void skipUnstableJoin(String reason,long drift,int attempts){
  final String key=identityKey;
  final long sourceMs=owner.current==null?0:position(owner.current);
  LogStore.log("replacement_join_guard_fallback",LogStore.map(
    "reason",reason,"projectedDriftMs",drift,"warmCorrections",attempts,
    "originalRetained",true,"sourcePcmMeasured",false,"phaseVerified",false));
  suspend(reason,30000);
  completedKey=key;completedPosition=sourceMs;
  completedReason="Синхронизация неустойчива — играет оригинал до следующей песни";
  audioOwner.unsupported(reason);status=completedReason;
 }
 void clearAudioCache(){for(File f:recentAudio.values())f.delete();recentAudio.clear();}
 void rememberAudio(){if(streaming!=null&&audioFile==null)audioFile=streaming.retainComplete();if(audioFile==null||descriptor==null||!ready||!api.signedIn())return;String key=audioKey(descriptor);File old=recentAudio.remove(key);if(old!=null&&!old.equals(audioFile))old.delete();recentAudio.put(key,audioFile);audioFile=null;long size=0;for(File f:recentAudio.values())size+=f.length();Iterator<File> it=recentAudio.values().iterator();while(it.hasNext()&&(recentAudio.size()>3||size>CACHE_BYTES)){File f=it.next();size-=f.length();f.delete();it.remove();}}

 ReplacementEngine(ProbeService owner){this.owner=owner;api=NativeApi.get(owner);}
 static Integer verifiedSession(Context c){try{Class<?> store=Class.forName("pro.celikom.nativeprobe.ProbeStore");Object instance=store.getField("INSTANCE").get(null);if(!Boolean.TRUE.equals(store.getMethod("enabled",Context.class).invoke(instance,c)))return null;JSONObject report=(JSONObject)store.getMethod("report",Context.class).invoke(instance,c);Class<?> cls=Class.forName("pro.celikom.nativeprobe.AttenuationService");Object companion=cls.getField("Companion").get(null);return (Integer)companion.getClass().getMethod("verifiedSession",JSONObject.class,long.class).invoke(companion,report,System.currentTimeMillis());}catch(Exception e){return null;}}
 void arm(){if(closed)return;if(returning)stop("rearm_during_return");if(authorizationAccount>=0&&authorizationAccount!=api.accountGeneration)stop("account_changed");if(!api.signedIn()){status="Сначала войди в свой аккаунт CELIKOM";return;}
  authorizationAccount=api.accountGeneration;audioOwner.activate();if(identityKey!=null)audioOwner.track(identityKey);Integer session=verifiedSession(owner);
  if(session!=null&&session>0){if(trustedSession>0&&trustedSession!=session){generation++;preparing=false;release("session_rearmed");descriptor=null;lookupKey=null;}trustedSession=session;}
  preloadAllowed=true;armedUntil=Long.MAX_VALUE;
  status=trustedSession>0?"Автозамена включена":"Открой эквалайзер Яндекс Музыки и выбери CELIKOM";
  LogStore.log("replacement_trial_start",LogStore.map("durationLimited",false,"verifiedAudioSession",trustedSession,"waitingForVerifiedSession",trustedSession<=0,"automaticNextTracks",true,"preparedBeforeArm",ready));update(owner.current);
 }
 void attachPendingSession(){if(!armed()||trustedSession>0)return;Integer session=verifiedSession(owner);if(session!=null&&session>0){trustedSession=session;status="Подключение получено; автозамена включена";LogStore.log("replacement_session_attached",LogStore.map("sessionId",session,"source","verified_yandex_panel"));}}
 void headphonesDisconnected(){
  if(!armed()&&!returning&&effect==null)return;
  if(returning){stop("headphones_disconnected_during_return");return;}
  resumePositionRetained=player!=null&&ready&&aligned&&!seeking;waitingForRouteResume=true;routePauseObserved=false;transition++;fading=false;aligned=false;pausedAt=-1;audioOwner.event(AudioOwnership.Event.ROUTE_LOSS);
  try{if(player!=null&&ready){setAuditedVolume(player,0f);audioOwner.pauseDecoder(player);}}catch(RuntimeException ex){suspend("route_pause_failed",0);}
  unmute();
  status="Наушники отключены. Пауза; нажми ▶ в Яндексе, чтобы продолжить с автозаменой";
  LogStore.log("replacement_route_pause",LogStore.map("automaticModeRetained",armed(),"preparedAudioRetained",ready,"sessionId",trustedSession));
  owner.pauseForRouteLoss();
 }
 /* Album/title/artist matching is a strong candidate, not proof of the exact
    source edit. Only explicit owner confirmation may use the extended tail. */
 boolean verifiedDurationIdentity(){return confirmed.contains(confirmationKey());}
 String confirmationKey(){PlaybackSource s=owner.current;return s==null?"":s.albumId+"|"+s.title+"|"+s.artist+"|"+s.duration+"|"+trackId;}
 void confirm(){if(identityKey!=null&&trackId!=null){confirmed.add(confirmationKey());durationConfirmationRequired=false;completedKey=null;completedReason=null;LogStore.log("metadata_candidate_confirmed",LogStore.map("trackId",trackId,"identityKey",identityKey));lookupKey=null;descriptor=null;nextLookup=0;update(owner.current);}}
 void identity(Map<String,Object> o,Map<String,Object> decision){String key=PlaybackSource.key(String.valueOf(o.get("mediaAlias")),o.get("albumId"),String.valueOf(o.get("title")),String.valueOf(o.get("artist")),((Number)o.get("durationMs")).longValue());PlaybackSource s=owner.current;if(s==null||!s.key.equals(key))return;String id=(String)decision.get("candidateTrackId");String nextMethod=String.valueOf(decision.get("method"));if(!Objects.equals(identityKey,key)||!Objects.equals(trackId,id)){completedKey=null;completedReason=null;clockSupervisor.reset();generation++;preparing=false;release("identity_changed");audioOwner.track(key);sourceSeekedThisTrack=false;nextLookup=0;failures=0;descriptor=null;lookupKey=null;}identityKey=key;trackId=id;method=nextMethod;if(id==null){status="Песня пока не определена однозначно; играет оригинал";return;}update(s);}
 boolean current(String key){PlaybackSource s=owner.current;return !closed&&owner.alive()&&s!=null&&ApiContract.current(key,s.key,SystemClock.elapsedRealtime()-s.observed,s.connected);}
 /* Transport data belongs to a verified track/account generation, not to a
    transient Media3 connection snapshot. Source output still requires current(). */
 boolean transportLeaseCurrent(String key,long g,long account){return !closed&&owner.alive()&&g==generation&&account==api.accountGeneration&&api.signedIn()&&Objects.equals(identityKey,key);}
 boolean armed(){return !closed&&armedUntil!=0;}
 long position(PlaybackSource s){long extra=s.playing?Math.max(0,SystemClock.elapsedRealtime()-s.observed):0;return Math.min(s.duration,Math.max(0,s.position+extra));}
 /* An account switch revokes queued decoder callbacks before the next
    timeline tick. Never grant old-account audio after sign-in changes. */
 boolean accountLeaseCurrent(){
  if(authorizationAccount<0||authorizationAccount==api.accountGeneration)return true;
  stop("account_generation_changed");return false;
 }
 void update(PlaybackSource s){if(closed||returning)return;
  if(!accountLeaseCurrent())return;
  attachPendingSession();
  if(s!=null&&(!s.connected||SystemClock.elapsedRealtime()-s.observed>1500)){if(player!=null||preparing||lookupKey!=null)suspend("source_unavailable",1000);status="Ожидаем подключение к Яндексу; играет оригинал";return;}
  if(s==null){
   long now=SystemClock.elapsedRealtime();if(unavailableSince<0){unavailableSince=now;transition++;fading=false;seeking=false;resumePositionRetained=ready&&aligned;aligned=false;try{if(player!=null&&ready){setAuditedVolume(player,0f);audioOwner.pauseDecoder(player);}}catch(RuntimeException ignored){}unmute();LogStore.log("replacement_source_wait",LogStore.map("decoderRetained",player!=null&&ready,"graceMs",1500));}
    if(streaming!=null)streaming.releasePrefetchAfterSeek();
    if(now-unavailableSince>=1500&&(player!=null||preparing||lookupKey!=null))suspend("source_unavailable",1000);status="Ожидаем подключение к Яндексу; играет оригинал";return;
  }
  unavailableSince=-1;
  boolean sourceJump=explicitSourceSeek;PlaybackSource previous=previousSource;previousSource=s;
  if(previous!=null&&previous.key.equals(s.key)&&previous.playing&&s.playing&&s!=previous&&s.observed>=previous.observed&&Math.abs(s.position-(previous.position+s.observed-previous.observed))>900)sourceJump=true;
  if(sourceJump){explicitSourceSeek=true;sourceSeekedThisTrack=true;}
  if(completedKey!=null&&completedKey.equals(s.key)){
   if(s.playing&&s.position<completedPosition-1500){completedKey=null;completedReason=null;lookupKey=null;descriptor=null;nextLookup=0;LogStore.log("replacement_repeat_detected",LogStore.map("sourcePositionMs",s.position));}
   else{status=completedReason==null?"Ожидаем следующую песню; играет оригинал":completedReason;return;}
  }
  if(durationConfirmationRequired&&!confirmed.contains(confirmationKey())){
   status="Длительность версии отличается. Подтвердите найденную песню; пока играет оригинал";return;
  }
  if(waitingForRouteResume){if(!s.playing){routePauseObserved=true;status="Наушники отключены. Нажми ▶ в Яндексе для продолжения";return;}if(!routePauseObserved){status="Ждём паузу Яндекса после отключения наушников";return;}waitingForRouteResume=false;pausedAt=-1;aligned=false;LogStore.log("replacement_route_resume",LogStore.map("sessionId",trustedSession,"sourcePlaying",true));}
  if(!s.key.equals(identityKey)){if(player!=null||preparing){generation++;preparing=false;release("track_changed");descriptor=null;lookupKey=null;}return;}
  if(trackId==null||(!armed()&&!preloadAllowed))return;
  if(!api.signedIn()){clearAudioCache();if(player!=null||preparing)suspend("login_required",0);status="ID найден; войди в CELIKOM для проверки замены";return;}
  if(!"ALBUM".equals(method)&&!confirmed.contains(confirmationKey())){status="Резерв нашёл песню. Подтверди найденную версию; пока играет оригинал";return;}
  if(!Float.isFinite(s.speed)||Math.abs(s.speed-1f)>0.01f){if(player!=null||preparing)suspend("unsupported_speed",1000);status="Для замены нужна скорость 1×; играет оригинал";return;}
  long clock=SystemClock.elapsedRealtime();
  if(ready&&!armed()&&clock-preparedAt>PREPARED_MS){generation++;release("prepared_expired");descriptor=null;lookupKey=null;}
  if(!identityKey.equals(lookupKey)){if(clock<nextLookup)return;lookupKey=identityKey;if(authorizationAccount<0)authorizationAccount=api.accountGeneration;final String key=identityKey,id=trackId;final long g=generation,account=api.accountGeneration;status="Проверяем замену на сервере…";api.resolve(id,()->!closed&&g==generation&&account==api.accountGeneration&&api.signedIn()&&current(key),(j,error)->{if(closed||g!=generation||account!=api.accountGeneration)return;if(!current(key)){if(Objects.equals(lookupKey,key)){lookupKey=null;descriptor=null;nextLookup=SystemClock.elapsedRealtime()+1000;status="Ожидаем актуальное состояние Яндекс Музыки";LogStore.log("replacement_lookup_deferred",LogStore.map("reason","source_not_current","retryMs",1000));}return;}if(error!=null){LogStore.log("replacement_resolve",LogStore.map("trackId",id,"errorCode",error));boolean denied=Arrays.asList("invalid_session","access_denied","login_required","unauthorized","trial_not_activated").contains(error);if(denied)clearAudioCache();if(!denied){lookupKey=null;nextLookup=SystemClock.elapsedRealtime()+retryDelay();}status="Сервер: "+message(error)+"; играет оригинал";return;}descriptor=j;descriptorUntil=SystemClock.elapsedRealtime()+15000;boolean found=j.optBoolean("found",false);status=found?"Замена найдена; готовим заранее":"В каталоге CELIKOM этой замены нет; играет оригинал";LogStore.log("replacement_resolve",LogStore.map("trackId",id,"found",found,"replacementId",j.optLong("replacement_id"),"durationMs",j.optLong("duration_ms")));if(found)prepare(key,j,g);});return;}
  if(descriptor!=null&&descriptor.optBoolean("found")&&player==null&&!preparing){if(clock>descriptorUntil){lookupKey=null;descriptor=null;return;}prepare(identityKey,descriptor,generation);}
  if(player==null||!ready||!armed())return;
  if(trustedSession<=0){status="Автозамена ожидает подключения: открой эквалайзер Яндекса → CELIKOM один раз";return;}
  try{
   if(!s.playing){
    clockSupervisor.reset();
    if(s.buffering&&s.wantsToPlay)bufferSource(s,sourceJump);
    else{sourceBufferSince=-1;pauseSource(s,false);}
    return;
   }
   if(sourceBufferSince>=0){
    LogStore.log("replacement_source_buffer_resumed",LogStore.map("trackId",trackId,"bufferMs",clock-sourceBufferSince,"decoderRetained",player!=null&&ready));
    sourceBufferSince=-1;
   }
   boolean resumed=pausedAt>=0;long pausedDuration=resumed?Math.max(0,clock-pausedAt):0;
   if(resumed){audioOwner.event(AudioOwnership.Event.RESUME);audioOwner.cancelPause();resumeFadePending=true;LogStore.log("replacement_resume_fast",LogStore.map("retainedOriginalEffect",effect!=null,"pauseDurationMs",pausedDuration));}
   pausedAt=-1;
   if(streaming!=null&&streaming.closed){suspend("stream_interrupted",1000);return;}
   boolean waiting=streaming!=null&&streaming.stalled();
   /* During a slow sparse HTTP read, seek() has ALREADY silenced and paused
      the replacement and restored the verified source effect to 0dB. Do not
      unmute() here: releasing/recreating that effect for every long range
      request adds an unnecessary second audio-ownership transition to one
      finger scrub. Keep it attached at unity gain until the final ACK (or a
      real pause, route loss, track boundary, effect loss or seek timeout).
      This does not make the HTTP seek faster; it removes a proven redundant
      DSP detach/reattach on the path recorded by HONOR 0.3.67. */
   if(waiting&&audioOwner.seekInFlight(player))audioOwner.noteSeekRangeWait(player);
   if(waiting&&seeking&&!streamSeekWaitLogged){
    streamSeekWaitLogged=true;
    LogStore.log("replacement_stream_seek_data_wait",LogStore.map(
      "trackId",trackId,"cachedBytes",streaming.cachedBytes(),
      "sourceEffectRetained",effect!=null&&originalMix>=0.999f,
      "replacementSilent",commandedReplacementVolume<=0.001f,
      "seekInFlight",audioOwner.seekInFlight(player)));
   }
   if(streaming!=null&&bufferGate.recover(waiting,aligned&&!bufferWaiting,seeking,player.getCurrentPosition(),clock)){
     if(!bufferWaiting){bufferWaiting=true;transition++;fading=false;aligned=false;seeking=false;resumePositionRetained=false;setAuditedVolume(player,0f);audioOwner.pauseDecoder(player);streaming.releasePrefetchAfterSeek();unmute();LogStore.log("replacement_buffer_wait",LogStore.map("trackId",trackId,"cachedBytes",streaming.cachedBytes()));}
    status="Связь замедлилась; играет оригинал, подгружаем замену";return;
   }
   if(bufferWaiting){if(waiting)return;bufferGate.reset();bufferWaiting=false;aligned=false;LogStore.log("replacement_buffer_resumed",LogStore.map("trackId",trackId));}
   /* After a canceled warm seek, do not start another decoder seek until the
      untagged completion arrives or the retained decoder times out safely. */
   if(audioOwner.seekInFlight(player)&&!seeking){
    /* Explicit user seek wins over a pending warm-alignment fade. Do not
       let a stale warm callback resume the old fade at the new source position. */
    if(sourceJump&&fading){seek(s,position(s),0);return;}
    if(audioOwner.seekExpired(player,clock,streaming!=null&&!streaming.complete()?STREAM_SEEK_TIMEOUT_MS:SEEK_TIMEOUT_MS))
     suspend("seek_timeout",retryDelay());
    else status="Ожидаем предыдущую перемотку; играет оригинал";
    return;
   }
   if(seeking){if(clock-seekStarted>seekBudget)suspend("seek_timeout",retryDelay());return;}
   long target=position(s);if(target>=s.duration){suspend("source_end",30000);return;}if(target>=player.getDuration()){
     if(PlaybackDuration.boundedTail(s.duration,player.getDuration()))
      LogStore.log("replacement_expected_tail",LogStore.map("trackId",trackId,"sourceDurationMs",s.duration,"measuredDurationMs",player.getDuration(),"action","handoff_to_original_before_next_track"));
     suspend("replacement_end",30000);return;}
   long drift=target-player.getCurrentPosition();
   boolean retainedPosition=resumePositionRetained&&!sourceJump&&!waitingForRouteResume;
   boolean retainedPauseResume=resumed&&retainedPosition&&effect!=null;
   if(fading&&audioOwner.handoverAwaitingClock()&&!sourceJump)return;
   // A retained paused decoder already at the native position needs no seek.
   if(!aligned&&retainedPosition&&Math.abs(drift)<=HANDOVER_DRIFT_MS){aligned=true;resumePositionRetained=false;LogStore.log("replacement_resume_aligned",LogStore.map("trackId",trackId,"driftMs",drift,"seekSkipped",true));}
   /* Source position is authoritative after a pause: resync off-output if necessary. */
   if(resumed&&pausedDuration>=PAUSE_ALIGN_DELAY_MS&&effect!=null&&Math.abs(drift)>(retainedPauseResume?HANDOVER_DRIFT_MS:PAUSE_ALIGN_TOLERANCE_MS)){seek(s,target,drift);return;}
   ClockSupervisor.Decision clockDecision=clockSupervisor.assess(aligned,!seeking&&!audioOwner.handoverAwaitingClock(),sourceJump,drift,clock);
   if(clockDecision==ClockSupervisor.Decision.RESTORE_SOURCE){
    String key=identityKey;LogStore.log("replacement_drift_unstable",LogStore.map("trackId",trackId,"sourcePositionMs",target,"driftMs",drift,"fallback","original_until_next_track","clockSupervisor","confirmed"));
    suspend("drift_unstable",30000);completedKey=key;completedPosition=target;completedReason="Большой рассинхрон замены — играет оригинал до следующей песни";audioOwner.unsupported("drift_unstable");status=completedReason;ownerEvent("drift_unsupported");return;
   }
   if(clockDecision==ClockSupervisor.Decision.SEEK){seek(s,target,drift);return;}
   boolean seamlessResume=retainedPauseResume&&originalMix<=0.001f&&Math.abs(drift)<=HANDOVER_DRIFT_MS;
   boolean newlyAttached=effect==null;
   if(newlyAttached&&!mute())return;
   if(!effect.hasControl()||!effect.getEnabled()){stop("effect_control_lost");return;}
    if(!player.isPlaying()){if(seamlessResume){audioOwner.grantReplacement(effect);originalMix=0f;applyVolume(1f);}else setAuditedVolume(player,0f);audioOwner.startDecoder(player,effect,identityKey,audioOwner.epoch());try{LogStore.log("audio_decoder_start",LogStore.map("trackId",trackId,"decoderPositionMs",player.getCurrentPosition(),"sourcePositionMs",position(s),"reusePreparedDecoder",true,"seekPending",seeking,"sourceMutedCommand",effect!=null&&originalMix<=0.001f));}catch(RuntimeException ignored){}traceAudioCommands();if(seamlessResume){fading=false;resumeFadePending=false;audioOwner.replacement();LogStore.log("replacement_resume_seamless",LogStore.map("trackId",trackId,"driftMs",drift,"sourcePositionMs",target,"retainedEffect",true));}else fade(newlyAttached||pendingStreamScrubJoin);}
    else if(newlyAttached){setAuditedVolume(player,0f);fade(true);}
   else if(!fading){if(pendingStreamScrubJoin&&originalMix>0.001f){setAuditedVolume(player,0f);fade(true);}else{audioOwner.grantReplacement(effect);originalMix=0f;applyVolume(1f);}}
   status="Играет замена · автопереход включён";logSync("playing",s,drift);
  }catch(RuntimeException e){suspend("playback_exception",retryDelay());status="Ошибка звука — оригинал восстановлен; повторим автоматически";LogStore.log("replacement_failure",LogStore.map("reason","playback_exception","type",e.getClass().getSimpleName()));}
 }
 /** A 0ms BUFFERING frame can precede the confirmed next MediaItem by a few ms.
  * Do not tear down the current decoder on this speculative old-alias reset.
  * sourceBoundary() still retires it immediately when the new alias is confirmed. */
 void outgoingTrackReset(PlaybackSource previous){
  if(player==null&&effect==null)return;
  long projected=position(previous);
  LogStore.log("replacement_outgoing_candidate",LogStore.map("trackId",trackId,
    "previousAlias",previous.alias,"remainingMs",Math.max(0,previous.duration-projected),
    "retainedUntilConfirmedBoundary",true));
 }
 void sourceSeekRequested(){if(armed()){explicitSourceSeek=true;sourceSeekedThisTrack=true;}}
 void sourceBoundary(String reason){
  if(closed)return;durationConfirmationRequired=false;sourceBufferSince=-1;generation++;preparing=false;release("track_changed");audioOwner.event(AudioOwnership.Event.BOUNDARY);audioOwner.invalidate(reason);identityKey=null;trackId=null;method="NONE";completedReason=null;clockSupervisor.reset();descriptor=null;lookupKey=null;nextLookup=0;failures=0;previousSource=null;completedKey=null;explicitSourceSeek=false;sourceSeekedThisTrack=false;unavailableSince=-1;status="Определяем новую песню; играет оригинал";ownerEvent("source_boundary");LogStore.log("replacement_source_boundary",LogStore.map("reason",reason,"originalRestoredBeforeLookup",true));
 }
 void sourceChanged(PlaybackSource previous,PlaybackSource next){
  long ownPosition=-1,ownDuration=-1;
  try{if(player!=null&&ready){ownPosition=player.getCurrentPosition();ownDuration=player.getDuration();}}catch(RuntimeException ignored){}
  LogStore.log("source_track_transition",LogStore.map("previousTrackId",trackId,"previousAlias",previous.alias,"nextAlias",next.alias,"previousDurationMs",previous.duration,"previousProjectedPositionMs",position(previous),"remainingSourceMs",Math.max(0,previous.duration-position(previous)),"replacementPositionMs",ownPosition,"replacementDurationMs",ownDuration,"replacementReady",ready,"followsNativeTrackChange",true));
  if(identityKey!=null||player!=null||preparing)sourceBoundary("sample_track_changed");
 }
 /** Media3 buffering with playWhenReady=true is not a user pause.
  * A tiny stall may be absorbed by an already audible replacement. A seek or
  * longer stall silences it without throwing away the prepared decoder.
  * Never play through a user seek or a pending handover. */
 void bufferSource(PlaybackSource s,boolean sourceJump){
  long now=SystemClock.elapsedRealtime();
  boolean firstBuffer=sourceBufferSince<0;
  if(sourceBufferSince<0){
   sourceBufferSince=now;
   LogStore.log("replacement_source_buffer",LogStore.map("trackId",trackId,
     "sourcePositionMs",s.position,"sourceJump",sourceJump,
     "decoderPlaying",player!=null&&ready&&player.isPlaying(),
     "userPause",false));
  }
  /* Media3 commonly enters BUFFERING for 15–70ms during an explicit seek.
     AudioOwnership already owns that in-flight decoder seek and has made the
     replacement silent while restoring native source gain. Do not turn the
     same transport operation into a second PAUSED/BUFFERING transaction:
     it revokes the seek's output lease and forces a second handover. If
     buffering outlasts native seek completion, the next update falls through
     to normal BUFFERING handling. */
  if(seeking&&audioOwner.seekInFlight(player)){
   status="Перематываем — ожидаем позицию источника";
   return;
  }
  /* An onEvents(BUFFERING) snapshot may arrive *after* the native decoder's
     seek callback has already started its muted clock-validation handover.
     In that state the original still has full gain, the replacement is
     silent, and the output ticket is valid. A new PAUSED transaction would
     revoke that ticket and require another decoder start/clock handover for
     a single user seek (observed repeatedly on HONOR 0.3.66). Keep the
     existing handover alive across a transient source buffer instead.
     The pre-existing short-buffer bound still transfers longer stalls to
     the ordinary pause/recovery path. An unprocessed user seek never enters
     this branch, so old-position replacement audio cannot leak through. */
  boolean mutedHandover=fading&&audioOwner.handoverAwaitingClock()
    &&audioOwner.state()==AudioOwnership.State.ALIGNING
    &&commandedReplacementVolume<=0.001f&&originalMix>=0.999f;
  boolean retainedAudible=!fading&&!audioOwner.handoverAwaitingClock()
    &&commandedReplacementVolume>0.001f;
  if(!sourceJump&&!explicitSourceSeek&&!seeking
    &&effect!=null&&ready&&player!=null&&player.isPlaying()
    &&(retainedAudible||mutedHandover)&&now-sourceBufferSince<300){
   if(mutedHandover&&firstBuffer)LogStore.log("replacement_muted_handover_buffer_hold",
     LogStore.map("trackId",trackId,"sourcePositionMs",s.position,
       "originalAudible",true,"replacementSilent",true,"handoverTicketRetained",true));
   status=mutedHandover?"Яндекс буферизует — ждём подтверждения позиции":"Яндекс буферизует — сохраняем текущий звук";
   return;
  }
  pauseSource(s,true);
 }
 void pauseSource(PlaybackSource s){pauseSource(s,false);}
 void pauseSource(PlaybackSource s,boolean buffering){
  if(player==null)return;
   if(streaming!=null)streaming.releasePrefetchAfterSeek();
  /* Changing USER_PAUSE <-> BUFFERING invalidates the old timer and delay. */
  boolean pauseCauseChanged=pausedAt>=0&&audioOwner.pauseMode()!=AudioOwnership.PauseMode.NONE
      &&audioOwner.pauseMode()!=(buffering?AudioOwnership.PauseMode.BUFFERING:AudioOwnership.PauseMode.USER);
  if(pausedAt<0||pauseCauseChanged){
   if(pauseCauseChanged)LogStore.log("replacement_pause_cause_changed",
       LogStore.map("trackId",trackId,"toBuffering",buffering,"decoderRetained",ready));
   bufferGate.reset();
   resumeDrift=position(s)-player.getCurrentPosition();
   resumePositionRetained=ready&&aligned&&!seeking;
   pauseRestoreDelayMs=seeking||audioOwner.handoverAwaitingClock()?350:buffering?900:PAUSE_GRACE_MS;
   pausedAt=SystemClock.elapsedRealtime();
   transition++;fading=false;aligned=false;
   setAuditedVolume(player,0f);
   audioOwner.pauseDecoder(player);
   /* A pause must silence the secondary and restore any partial source gain. */
   if(effect!=null&&originalMix>0.001f
      &&(audioOwner.state()==AudioOwnership.State.ALIGNING
          ||audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND)){
    audioOwner.aligning();audioOwner.sourceGainDuringAlignment(effect);
    originalMix=1f;traceAudioCommands();
   }
   audioOwner.hold(buffering);
   final MediaPlayer p=player;final DynamicsProcessing fx=effect;
   final long token=transition,epoch=audioOwner.epoch();final String key=identityKey;
   final long lease=audioOwner.pauseLease();
   // Do not seek a paused decoder on a 160ms timer. The old code changed its
   // owner state from PAUSED to ALIGNING and invalidated its restore lease;
   // correct alignment against the live position only when playback resumes.
   owner.handler.postDelayed(()->{
    if(player==p&&effect==fx&&token==transition&&audioOwner.current(epoch,key)
      &&audioOwner.validPause(lease)&&pausedAt>=0&&!seeking&&current(identityKey)
      &&owner.current!=null&&!owner.current.playing)unmute();
   },pauseRestoreDelayMs);
  }
  if(SystemClock.elapsedRealtime()-pausedAt>=pauseRestoreDelayMs)unmute();
  status=buffering?"Яндекс буферизует — ожидаем продолжения":"Пауза — аудио сохранено для продолжения";
  ownerEvent(buffering?"source_buffering":"paused");
  logSync(buffering?"buffering":"paused",s,0);
 }
 long retryDelay(){failures++;return Math.min(30000,5000L*(1L<<Math.min(3,failures-1)));}
 void seek(PlaybackSource s,long target,long drift){seek(s,target,drift,false);}
 void seek(PlaybackSource s,long target,long drift,boolean correction){
   if(streaming!=null)streaming.holdPrefetchForSeek();
  if(audioOwner.seekInFlight(player)){
   /* Last desired source position wins. The decoder keeps its one outstanding
      untagged seek; the source is audible while that position settles. */
   audioOwner.event(AudioOwnership.Event.SEEK);transition++;fading=false;
   seeking=false;aligned=false;resumePositionRetained=false;
   setAuditedVolume(player,0f);audioOwner.pauseDecoder(player);
   audioOwner.aligning();
   if(effect!=null){audioOwner.sourceGainDuringAlignment(effect);originalMix=1f;traceAudioCommands();}
   seekHoldActive=false;pendingStreamScrubJoin=false;
   status="Ожидаем последнюю позицию перемотки; играет оригинал";return;
  }
  /* A seek is not a cold attachment. Do not silence BOTH sessions during a
     cached decoder seek and do not repeatedly start the 500ms cold-entry dip
     on an incomplete HTTP stream. Keep the original audible and retain the
     same effect/decoder until the most recent target's clock is verified. */
  pendingStreamScrubJoin=false;seekHoldActive=false;
  clockSupervisor.onSeek();audioOwner.event(AudioOwnership.Event.SEEK);audioOwner.aligning();explicitSourceSeek=false;resumePositionRetained=false;seekCorrections=correction?seekCorrections+1:0;seeking=true;streamSeekWaitLogged=false;aligned=true;seekStarted=SystemClock.elapsedRealtime();seekBudget=streaming!=null&&!streaming.complete()?STREAM_SEEK_TIMEOUT_MS:SEEK_TIMEOUT_MS;transition++;fading=false;setAuditedVolume(player,0f);audioOwner.pauseDecoder(player);
  if(effect!=null){audioOwner.sourceGainDuringAlignment(effect);originalMix=1f;traceAudioCommands();}
  status="Синхронизация позиции; оригинал звучит…";ownerEvent("seek");LogStore.log("replacement_sync",LogStore.map("state","seek","trackId",trackId,"sourcePositionMs",target,"driftMs",drift,"originalStillMuted",false,"originalRestoredDuringSeek",true,"inaudibleCorrection",correction));final MediaPlayer p=player;final long t=transition,epoch=audioOwner.epoch();final String key=identityKey;
  long sourceAtSubmit=position(s),decoderAtSubmit=player.getCurrentPosition();
  audioOwner.issueSeek(p,target,key,epoch,AudioOwnership.SeekKind.ALIGNMENT,seekStarted,
    sourceAtSubmit,s.position,s.observed,decoderAtSubmit);owner.handler.postDelayed(()->{if(player==p&&seeking&&transition==t&&audioOwner.current(epoch,key))suspend("seek_timeout",retryDelay());},seekBudget);}
 void prepare(String key,JSONObject j,long g){if(preparing||!current(key)||!api.signedIn())return;PlaybackSource s=owner.current;if(!PlaybackDuration.metadataProbeAllowed(s.duration,j.optLong("duration_ms"))){LogStore.log("replacement_duration_mismatch",LogStore.map("trackId",trackId,"sourceDurationMs",s.duration,"replacementDurationMs",j.optLong("duration_ms")));completedKey=key;completedPosition=position(s);completedReason="Версия замены не совпадает по длительности — пропускаем эту песню, играет оригинал";audioOwner.unsupported("duration_mismatch");status=completedReason;LogStore.log("replacement_track_skipped",LogStore.map("reason","duration_mismatch","trackId",trackId,"sourceDurationMs",s.duration,"replacementDurationMs",j.optLong("duration_ms"),"action","original_until_next_track"));descriptor=null;return;}if(!PlaybackDuration.safe(s.duration,j.optLong("duration_ms"))){
   LogStore.log("replacement_duration_probe",LogStore.map("trackId",trackId,"sourceDurationMs",s.duration,"reportedDurationMs",j.optLong("duration_ms"),"policy","verify_measured_file_before_any_audio"));
  }audioOwner.preparing();prepareTicket=audioOwner.ticket(key,api.accountGeneration,j.optLong("replacement_id"),j.optLong("version"),j.optLong("duration_ms"));preparing=true;status="Готовим аудио заранее; оригинал продолжает играть";
  File cached=recentAudio.remove(audioKey(j));
  if(cached!=null&&cached.isFile()){LogStore.log("replacement_audio_reused",LogStore.map("trackId",trackId,"liveResolveRequired",true));acceptAudio(key,j,g,cached,null);return;}
  if(key.equals(streamFallbackKey)){downloadFull(key,j,g);return;}
  status="Подготавливаем начало песни; играет оригинал";
  final long account=api.accountGeneration;
  api.stream(j,()->transportLeaseCurrent(key,g,account),(source,error)->{
   if(g!=generation||closed||!current(key)||!api.signedIn()){if(source!=null)source.close();if(g==generation&&!closed)suspend("stream_source_changed",1000);return;}
   if(source==null){streamFallbackKey=key;LogStore.log("replacement_stream_fallback",LogStore.map("reason","range_unavailable"));downloadFull(key,j,g);return;}
   acceptAudio(key,j,g,null,source,null);
  });
 }
 void downloadFull(String key,JSONObject j,long g){final long account=api.accountGeneration;api.download(j,()->transportLeaseCurrent(key,g,account),(file,error)->acceptAudio(key,j,g,file,error));}
 void acceptAudio(String key,JSONObject j,long g,File file,String error){acceptAudio(key,j,g,file,null,error);}
 void acceptAudio(String key,JSONObject j,long g,File file,BufferedAudio source,String error){if(g!=generation||closed||!audioOwner.dataCurrent(prepareTicket,api.accountGeneration,key,j.optLong("replacement_id"),j.optLong("version"),j.optLong("duration_ms"))){if(file!=null)file.delete();if(source!=null)source.close();return;}preparing=false;if(file==null&&source==null){suspend("download_failed",retryDelay());status="Сеть недоступна; играет оригинал, повторим автоматически";return;}if(!current(key)||!api.signedIn()){if(file!=null)file.delete();if(source!=null)source.close();suspend("download_source_changed",1000);return;}
   try{audioFile=file;streaming=source;bufferWaiting=false;player=new MediaPlayer();final MediaPlayer p=player;final long ownerTicket=audioOwner.epoch();final AudioOwnership.Ticket dataTicket=prepareTicket;p.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());setAuditedVolume(p,0f);if(source==null)p.setDataSource(file.getAbsolutePath());else p.setDataSource(new StreamingAudio(source));p.setOnErrorListener((mp,what,extra)->{if(mp==player&&g==generation&&audioOwner.current(ownerTicket,key)&&accountLeaseCurrent()){suspend("media_player_error",retryDelay());LogStore.log("replacement_failure",LogStore.map("reason","media_player_error","what",what,"extra",extra));}return true;});p.setOnCompletionListener(mp->{
    if(mp!=player||g!=generation||!audioOwner.current(ownerTicket,key)||!accountLeaseCurrent())return;
    /* Completion is untagged: an old-position callback during a seek or a
       paused/buffered/route-lost hold must not mark the song complete. */
    if(!ready||!armed()||returning||pausedAt>=0||waitingForRouteResume
        ||!audioOwner.mayConsumeCompletion(mp)||!current(key)){
     LogStore.log("replacement_completion_deferred",LogStore.map(
       "seekInFlight",audioOwner.seekInFlight(mp),"sourceHeld",pausedAt>=0,
       "routeLost",waitingForRouteResume,"ownerState",audioOwner.state().name()));
     return;
    }
    PlaybackSource nativeNow=owner.current;
    if(nativeNow==null||!nativeNow.playing||!key.equals(nativeNow.key))return;
    if(nativeNow!=null&&key.equals(nativeNow.key)&&nativeNow.playing&&
      PlaybackDuration.expectedTail(nativeNow.duration,mp.getDuration(),nativeNow.duration-position(nativeNow))){
     LogStore.log("replacement_expected_tail",LogStore.map("trackId",trackId,"sourceRemainingMs",nativeNow.duration-position(nativeNow),"measuredDurationMs",mp.getDuration(),"action","original_for_short_outro"));
     suspend("replacement_completed",30000);
    }else if(nativeNow!=null&&key.equals(nativeNow.key)&&nativeNow.playing&&nativeNow.duration-position(nativeNow)>750){
     long remaining=nativeNow.duration-position(nativeNow);
     LogStore.log("replacement_early_completion",LogStore.map("trackId",trackId,"sourceRemainingMs",remaining,"ownerEpoch",audioOwner.epoch(),"action","original_until_next_track"));
     suspend("replacement_early_completion",30000);
     completedKey=key;completedPosition=position(nativeNow);
     completedReason="Замена закончилась раньше оригинала — играет оригинал до следующей песни";
     audioOwner.unsupported("replacement_early_completion");status=completedReason;ownerEvent("early_completion");
    }else suspend("replacement_completed",30000);
   });p.setOnPreparedListener(mp->{if(mp!=player||g!=generation||!audioOwner.current(ownerTicket,key)||!accountLeaseCurrent()||!audioOwner.dataCurrent(dataTicket,api.accountGeneration,key,j.optLong("replacement_id"),j.optLong("version"),j.optLong("duration_ms")))return;audioOwner.event(AudioOwnership.Event.PREPARE_READY);if(!current(key)){suspend("prepared_stale",1000);return;}PlaybackSource now=owner.current;if(!ApiContract.durations(now.duration,j.optLong("duration_ms"),mp.getDuration())||
     !PlaybackDuration.compatible(now.duration,j.optLong("duration_ms"),mp.getDuration(),verifiedDurationIdentity())||
     (trustedSession>0&&mp.getAudioSessionId()==trustedSession)){
    if(!PlaybackDuration.compatible(now.duration,j.optLong("duration_ms"),mp.getDuration(),verifiedDurationIdentity())){LogStore.log("replacement_duration_mismatch",LogStore.map("trackId",trackId,"sourceDurationMs",now.duration,"reportedDurationMs",j.optLong("duration_ms"),"replacementDurationMs",mp.getDuration(),"stage","measured_file"));completedKey=identityKey;completedPosition=position(now);completedReason="Эту замену нельзя воспроизвести безопасно; играет оригинал";}
    suspend("duration_or_session_invalid",30000);if(completedReason!=null){audioOwner.unsupported("measured_duration_mismatch");status=completedReason;}else status="Проверка аудио не пройдена; играет оригинал";return;}
   if(!PlaybackDuration.safe(now.duration,mp.getDuration()))
    LogStore.log("replacement_bounded_tail_accepted",LogStore.map("trackId",trackId,"sourceDurationMs",now.duration,"measuredDurationMs",mp.getDuration(),"reportedDurationMs",j.optLong("duration_ms"),"identityMethod",method,"originalRetainedUntilBoundary",true));
   if(!PlaybackDuration.safe(now.duration,j.optLong("duration_ms")))
    LogStore.log("replacement_duration_probe_verified",LogStore.map("trackId",trackId,"sourceDurationMs",now.duration,"reportedDurationMs",j.optLong("duration_ms"),"measuredDurationMs",mp.getDuration()));
   ready=true;failures=0;preparedAt=SystemClock.elapsedRealtime();status=armed()?"Аудио готово; синхронизируем":"Аудио готово заранее; можно включать автозамену";LogStore.log("replacement_prepared",LogStore.map("trackId",trackId,"measuredDurationMs",mp.getDuration(),"sourceDurationMs",now.duration,"separateAudioSession",true,"beforeArm",!armed()));update(now);});p.setOnSeekCompleteListener(mp->completeSeek(mp,key));p.prepareAsync();if(source!=null)source.prefetch();final MediaPlayer preparingPlayer=p;owner.handler.postDelayed(()->{if(player==preparingPlayer&&!ready)suspend("prepare_timeout",retryDelay());},10000);
   }catch(Exception e){suspend("prepare_failed",retryDelay());status="Не удалось подготовить аудио; играет оригинал";}
 }
 void completeSeek(MediaPlayer mp,String key){
  if(mp!=player||!Objects.equals(identityKey,key)||!accountLeaseCurrent())return;
  AudioOwnership.SeekAck ack=audioOwner.acceptSeekCompletion(mp);
  if(ack==null)return; // repeated/retired callback
  /* Snapshot BOTH ALIGNMENT and WARM ACKs. This is transport data, not PCM. */
  final long ackClock=SystemClock.elapsedRealtime();
  final PlaybackSource sourceAtAck=owner.current;
  final long projectedAtAck=sourceAtAck==null?-1:position(sourceAtAck);
  final long decoderAtAck=mp.getCurrentPosition();
  Map<String,Object> ackFields=LogStore.map(
    "seekSeq",ack.sequence,"kind",ack.kind.name(),
    "requestedPositionMs",ack.targetMs,
    "sourceProjectedMs",projectedAtAck,"decoderPositionMs",decoderAtAck,
    "rawResidualMs",sourceAtAck==null?null:Long.valueOf(projectedAtAck-decoderAtAck),
    "rawResidualSemantics","source transport minus decoder cursor at ACK; includes source advance during asynchronous seek",
    "correctionPass",ack.kind==AudioOwnership.SeekKind.ALIGNMENT?seekCorrections:-1,
    "rangeWaitObserved",ack.rangeWaitObserved,
    "staleOperation",ack.operationEpoch!=audioOwner.operationEpoch(),
    "sourcePcmMeasured",false,"phaseVerified",false,"hardwareOutputMeasured",false,"transportOnly",true);
  ackFields.putAll(SeekTimingEvidence.atAck(ack,ackClock,projectedAtAck,decoderAtAck,
      sourceAtAck==null?-1:sourceAtAck.observed));
  LogStore.log("replacement_seek_ack",ackFields);
    if(ack.operationEpoch!=audioOwner.operationEpoch()){
   /* A pause revoked output permission, not necessarily the decoder position.
      Reuse a verified final alignment without granting an old audible command.
      A new source position or route loss must never reuse the canceled result. */
   PlaybackSource sourceNow=owner.current;
   boolean positionStillValid=ack.kind==AudioOwnership.SeekKind.ALIGNMENT
      &&!waitingForRouteResume&&sourceNow!=null&&current(key)
      &&Math.abs(position(sourceNow)-mp.getCurrentPosition())<=PAUSE_ALIGN_TOLERANCE_MS;
   seeking=false;aligned=positionStillValid;
   resumePositionRetained=positionStillValid;
   if(!waitingForRouteResume&&sourceNow!=null&&sourceNow.playing)update(sourceNow);
   return;
  }
  if(ack.kind==AudioOwnership.SeekKind.WARM){
   
   return;
  }
  if(!seeking)return;
  seeking=false;
  long clock=SystemClock.elapsedRealtime(),elapsed=clock-seekStarted;
  if(!ready||!armed()||!current(key))return;
  PlaybackSource now=owner.current;
  long target=position(now),decoderAtComplete=mp.getCurrentPosition(),residual=target-decoderAtComplete;
  LogStore.log("replacement_seek_complete",LogStore.map(
    "elapsedMs",elapsed,"trackId",trackId,"residualMs",residual,
    "sourceProjectedAtCompleteMs",target,"decoderPositionAtCompleteMs",decoderAtComplete,
    "residualSemantics","source transport minus decoder cursor at callback; not output presentation",
    "sourceSnapshotAgeAtCompleteMs",Math.max(0,clock-now.observed),
    "correctionPass",seekCorrections,"sourcePcmMeasured",false,"phaseVerified",false));
  /* A second streaming seek can also wait for data. Never publish that stale
     alignment and then correct it audibly after handover. Allow two measured
     corrections, then keep the original if the decoder cannot settle. */
  if(streaming!=null&&!waitingForRouteResume&&now.playing&&!mp.isPlaying()
    &&Math.abs(residual)>HANDOVER_DRIFT_MS){
   if(seekCorrections>=2||target>=mp.getDuration()-150){
    LogStore.log("replacement_alignment_rejected",LogStore.map("trackId",trackId,"residualMs",residual,"correctionPass",seekCorrections));suspend("alignment_unstable",retryDelay());return;
   }
   seek(now,Math.max(0,Math.min(mp.getDuration()-1,target)),residual,true);return;
  }
  /* Preserve the accepted local-file compensation; no network wait is involved. */
  if(streaming==null&&!waitingForRouteResume&&now.playing&&!mp.isPlaying()&&seekCorrections==0
    &&Math.abs(residual)>500&&Math.abs(residual)<=1500){
   long compensated=Math.max(0,Math.min(mp.getDuration()-1,target+residual));
   if(compensated<mp.getDuration()-150){seek(now,compensated,residual,true);return;}
  }
  // A transient non-playing snapshot during an in-flight seek can clear
  // 'aligned'. Accept the completed position if within the existing
  // handover drift budget, rather than launching a second redundant seek.
  if(Math.abs(residual)<=HANDOVER_DRIFT_MS){
   aligned=true;
   if(!now.playing)resumePositionRetained=true;
  }
  update(now);
 }
 boolean mute(){try{if(trustedSession<=0||player==null||player.getAudioSessionId()==trustedSession)throw new IllegalStateException();DynamicsProcessing candidate=new DynamicsProcessing(0,trustedSession,null);effect=candidate;candidate.setControlStatusListener((e,control)->{if(!control)owner.handler.post(()->{if(effect==candidate)stop("effect_control_lost");});});if(!candidate.hasControl())throw new IllegalStateException();originalMix=1f;audioOwner.prepareSourceEffect(candidate);LogStore.log("replacement_original_muted",LogStore.map("sessionId",trustedSession,"globalVolumeChanged",false,"rampMs",resumeFadePending?PAUSE_RESUME_FADE_MS:FADE_MS));return true;}catch(RuntimeException e){stop("cannot_mute_original");status="Телефон не разрешил приглушить Яндекс; замена остановлена";return false;}}
  void fade(boolean coherentEntry){
  final long token=++transition;final MediaPlayer p=player;final DynamicsProcessing fx=effect;
  final long ownerEpoch=audioOwner.epoch();final String ownerKey=identityKey;
   if(streaming!=null)streaming.holdPrefetchForSeek();
  audioOwner.aligning();
  audioOwner.event(AudioOwnership.Event.HANDOVER);
  final AudioOwnership.Ticket handoverTicket=audioOwner.ticket(ownerKey,api.accountGeneration,descriptor==null?0:descriptor.optLong("replacement_id"),descriptor==null?0:descriptor.optLong("version"),descriptor==null?0:descriptor.optLong("duration_ms"));
   /* The original stays audible during native decoder startup and clock
      alignment. Once validated, a new attachment uses the SAME complementary
      linear entry tested on HONOR; a retained seek uses exclusive single-turn.
      Sample phase of two Android output sessions is NOT measurable here:
      the linear entry is a listening compromise, never acoustic proof. */
  resumeFadePending=false;
  final boolean alignLive=streaming!=null;
  final long[] baseline={p.getCurrentPosition()},phaseStarted={SystemClock.elapsedRealtime()};
  final int[] corrections={0};final long[] softStarted={-1};
  /* Passive cold join drift summary: projected transport clocks only. */
  final long[] coldClock={Long.MAX_VALUE,Long.MIN_VALUE,0,-1,-1};
  final boolean[] outputPreLogged={false},outputMidLogged={false},outputPostLogged={false};
  final long coldStarted=SystemClock.elapsedRealtime();
  if(originalMix<=0.001f&&!seekHoldActive){
   setAuditedVolume(p,0f);
   audioOwner.sourceGainDuringAlignment(fx);originalMix=1f;traceAudioCommands();
  }
  fadeStarted=SystemClock.elapsedRealtime();fading=true;audioOwner.handoverWaitForClock(alignLive);
  Runnable ramp=new Runnable(){public void run(){
   if(closed||token!=transition||p!=player||fx!=effect||!armed()||!accountLeaseCurrent()
      ||!audioOwner.current(ownerEpoch,ownerKey)||!audioOwner.commandCurrent(handoverTicket,api.accountGeneration,ownerKey,descriptor==null?0:descriptor.optLong("replacement_id"),descriptor==null?0:descriptor.optLong("version"),descriptor==null?0:descriptor.optLong("duration_ms")))return;
   try{
    if(!current(identityKey)){suspend("fade_source_unavailable",1000);return;}
    if(!owner.current.playing){
     if(owner.current.buffering&&owner.current.wantsToPlay)bufferSource(owner.current,false);
     else pauseSource(owner.current,false);
     /* The held muted decoder still owns this callback. Without a new tick,
        update() would see handoverAwaitingClock and wait forever. */
     if(token==transition&&fading&&audioOwner.handoverAwaitingClock())
      owner.handler.postDelayed(this,20);
     return;
    }
    if(audioOwner.handoverAwaitingClock()){
     long now=SystemClock.elapsedRealtime(),position=p.getCurrentPosition();
     if(now-coldStarted>=STRICT_JOIN_BUDGET_MS){
      skipUnstableJoin("join_gate_deadline",position(owner.current)-position,corrections[0]);return;
     }
     if(audioOwner.seekInFlight(p)||position-baseline[0]<40){
      if(now-phaseStarted[0]>=2000){
       skipUnstableJoin("decoder_start_timeout",position(owner.current)-position,corrections[0]);return;
      }
      owner.handler.postDelayed(this,20);return;
     }
     long target=position(owner.current),drift=target-position;
     if(Math.abs(drift)>STRICT_STREAM_JOIN_DRIFT_MS){
      if(corrections[0]>=2||target>=p.getDuration()-150){
       skipUnstableJoin("join_alignment_unstable",drift,corrections[0]);return;
      }
      long lead=predictedWarmLeadMs();
      long warmTarget=predictedWarmTargetMs(target,p.getDuration());
      corrections[0]++;baseline[0]=warmTarget;phaseStarted[0]=now;
      LogStore.log("replacement_warm_alignment",LogStore.map(
        "trackId",trackId,"driftMs",drift,"pass",corrections[0],
        "sourceProjectedAtRequestMs",target,"sourceSnapshotPositionMs",owner.current.position,
        "sourceSnapshotAgeAtRequestMs",Math.max(0,now-owner.current.observed),
        "decoderPositionBeforeSeekMs",position,
        "seekTargetMs",warmTarget,"predictedLeadMs",lead,
        "thresholdMs",STRICT_STREAM_JOIN_DRIFT_MS,"predictor","warm_callback_fixed_70ms","replacementAudible",false,
        "measurementClass","transport_timeline_only"));
      /* One muted decoder seek; original remains fully audible. */
      PlaybackSource sourceAtSubmit=owner.current;
      audioOwner.issueSeek(p,warmTarget,ownerKey,ownerEpoch,AudioOwnership.SeekKind.WARM,now,
        position(sourceAtSubmit),sourceAtSubmit.position,sourceAtSubmit.observed,p.getCurrentPosition());
      owner.handler.postDelayed(this,20);return;
     }
     audioOwner.handoverClockValidated();fadeStarted=now;
     LogStore.log("replacement_join_guard_verified",LogStore.map(
       "driftMs",drift,"thresholdMs",STRICT_STREAM_JOIN_DRIFT_MS,
       "sourceProjectedPositionMs",target,"sourceSnapshotPositionMs",owner.current.position,
       "sourceSnapshotAgeMs",Math.max(0,now-owner.current.observed),
       "decoderPositionMs",position,
       "corrections",corrections[0],"originalAudibleUntilGate",true,
       "phaseVerified",false,"sourcePcmMeasured",false,"hardwareOutputMeasured",false,
       "measurementClass","transport_timeline_only"));
     LogStore.log("replacement_decoder_advancing",LogStore.map(
       "trackId",trackId,"driftMs",drift,"corrections",corrections[0],
       "waitMs",now-phaseStarted[0]));
    }
     if(!outputPreLogged[0]){
      logOutputClockSample(p,owner.current,coherentEntry?"pre_blend":"pre_exclusive_grant");
      outputPreLogged[0]=true;
     }
     /* The same bounded ticket and audio owner fence protect both paths.
        No equal-power gain law: two correlated sessions at 0.5/0.5 can
        interfere, but an equal-power 0.707/0.707 could also add +3dB. */
     if(coherentEntry){
     if(softStarted[0]<0){
      softStarted[0]=SystemClock.elapsedRealtime();
       LogStore.log("replacement_unified_join_start",LogStore.map("trackId",trackId,
         "durationMs",UNIFIED_JOIN_MS,"gainLaw","complementary_linear",
         "sourcePcmMeasured",false,"phaseVerified",false,"oneMode",true));
     }
     long elapsed=Math.max(0,SystemClock.elapsedRealtime()-softStarted[0]);
     if(!outputMidLogged[0]&&elapsed>=UNIFIED_JOIN_MS/2){
      logOutputClockSample(p,owner.current,"blend_midpoint");outputMidLogged[0]=true;
     }
     long sourceProjected=position(owner.current),decoderProjected=p.getCurrentPosition();
     long transportDrift=sourceProjected-decoderProjected;
     coldClock[0]=Math.min(coldClock[0],transportDrift);
     coldClock[1]=Math.max(coldClock[1],transportDrift);
     if(coldClock[2]++==0){coldClock[3]=sourceProjected;coldClock[4]=decoderProjected;}
      float mix=TransitionMix.progress(elapsed,UNIFIED_JOIN_MS);
     float gain=(float)Math.min(1,Math.pow(10,Math.min(0,descriptor==null?0:descriptor.optDouble("gain_db",0))/20));
     float volume=audioOwner.blendSameSong(p,fx,mix,Math.max(0.00001f,gain),ownerKey,ownerEpoch,handoverTicket.operationEpoch);
     originalMix=1f-mix;commandedReplacementVolume=volume;traceAudioCommands();
      if(elapsed<UNIFIED_JOIN_MS){owner.handler.postDelayed(this,20);return;}
     applyVolume(1f);
    }else{
     audioOwner.grantReplacement(fx);originalMix=0f;applyVolume(1f);
    }
    if(!outputPostLogged[0]){
     logOutputClockSample(p,owner.current,coherentEntry?"post_blend":"post_exclusive_grant");
     outputPostLogged[0]=true;
    }
    fading=false;audioOwner.replacement();seekHoldActive=false;pendingStreamScrubJoin=false;ownerEvent("exclusive_handover");
     if(streaming!=null)streaming.releasePrefetchAfterSeek();
    if(coherentEntry&&coldClock[2]>0)LogStore.log("replacement_join_transport_summary",LogStore.map(
      "joinMode","unified_complementary_linear","transportOnly",true,
      "elapsedFromJoinStartMs",SystemClock.elapsedRealtime()-coldStarted,
      "commandedJoinMs",UNIFIED_JOIN_MS,"samples",coldClock[2],
      "sourceStartMs",coldClock[3],"decoderStartMs",coldClock[4],
      "sourceEndMs",position(owner.current),"decoderEndMs",p.getCurrentPosition(),
      "minDriftMs",coldClock[0],"maxDriftMs",coldClock[1],
      "sourcePcmMeasured",false,"phaseVerified",false));
    LogStore.log("replacement_transition_complete",LogStore.map(
       "trackId",trackId,"rampMs",coherentEntry?UNIFIED_JOIN_MS:0,
       "joinMode",coherentEntry?"unified_complementary_linear":"exclusive_single_turn",
      "commandDelayMs",SystemClock.elapsedRealtime()-fadeStarted));
   }catch(RuntimeException e){suspend("fade_failed",retryDelay());}
  }};ramp.run();
 }
 void logOutputClockSample(MediaPlayer p,PlaybackSource source,String stage){
  LogStore.log("replacement_output_clock_sample",OutputClockEvidence.capture(p,source,stage));
 }
 /* These are our own output commands, NOT an acoustic or Bluetooth measurement. */
 void setAuditedVolume(MediaPlayer p,float volume){
  audioOwner.volume(p,volume,effect);
  if(p==player){commandedReplacementVolume=volume;traceAudioCommands();}
 }
 void traceAudioCommands(){
  try{
   PlaybackSource source=owner.current;
   boolean playing=source!=null&&source.playing;
   boolean muted=effect!=null&&originalMix<=0.001f;
   boolean decoder=player!=null&&ready&&player.isPlaying();
   String cause=seeking?"seek":pausedAt>=0?"source_pause":bufferWaiting?"buffer_wait":
                returning?"manual_return":fading?"handover":"transport";
   AudioContinuityMonitor.Finding finding=continuity.observe(SystemClock.elapsedRealtime(),
     trackId,cause,playing,muted,decoder,commandedReplacementVolume,audioOwner.state());
   if(finding!=null)LogStore.log("audio_command_anomaly",LogStore.map(
     "kind",finding.kind,"classification",finding.classification,
     "expectedByOwnerState",finding.expectedByOwnerState,
     "trackId",finding.trackId,"cause",finding.cause,
     "durationMs",finding.durationMs,"transition",transition,
     "sourcePlaying",playing,"sourceMutedCommand",muted,
     "decoderPlaying",decoder,"replacementVolumeCommand",commandedReplacementVolume,
     "seekPending",seeking,"ownerState",audioOwner.state().name(),
     "hardwareOutputMeasured",false));
  }catch(RuntimeException ignored){} /* Telemetry cannot break playback. */
 }
 void applyVolume(float mix){double gain=descriptor==null?0:descriptor.optDouble("gain_db",0);float volume=mix*(float)Math.min(1,Math.pow(10,Math.min(0,gain)/20));setAuditedVolume(player,volume);if(gain>0&&loudness==null)try{loudness=new LoudnessEnhancer(player.getAudioSessionId());loudness.setTargetGain((int)Math.round(gain*100));loudness.setEnabled(true);}catch(RuntimeException ignored){LogStore.log("replacement_gain","positive gain unavailable");}}
 void unmute(){unmute(player);}
 void unmute(MediaPlayer secondary){seekHoldActive=false;if(effect!=null){DynamicsProcessing fx=effect;effect=null;AudioOwnership.RestoreResult r=audioOwner.restoreSource(secondary,fx);commandedReplacementVolume=0f;originalMix=1f;LogStore.log("replacement_original_restored",LogStore.map("reason","effect_released","gainReset",r.gainReset,"disabled",r.disabled,"released",r.released,"hardwareAudibilityVerified",false));ownerEvent("source_restored");traceAudioCommands();}}
 /* Invalidate ramps and silence output before cache, network or diagnostic cleanup.
    HttpURLConnection.disconnect and effect release may block on the old route. */
 MediaPlayer silenceBeforeCleanup(){transition++;fading=false;MediaPlayer old=player;player=null;if(old!=null){boolean zero=false,paused=false;try{setAuditedVolume(old,0f);zero=true;}catch(RuntimeException ignored){}try{audioOwner.pauseDecoder(old);paused=!old.isPlaying();}catch(RuntimeException ignored){}LogStore.log("replacement_output_silenced",LogStore.map("trackId",trackId,"gainZero",zero,"paused",paused,"beforeTransportCleanup",true));}unmute(old);return old;}
 void release(String reason){
  sourceBufferSince=-1;audioOwner.cancelPause();
  boolean had=player!=null||effect!=null;MediaPlayer old=silenceBeforeCleanup();
  if("identity_changed".equals(reason)||"track_changed".equals(reason)||"replacement_end".equals(reason)||"replacement_completed".equals(reason)||"source_end".equals(reason)||"source_unavailable".equals(reason)||"source_disconnected".equals(reason))rememberAudio();
  /* Detach a completed file before MediaPlayer.release closes its MediaDataSource. */
  if(old!=null){try{old.setOnErrorListener(null);old.setOnPreparedListener(null);old.setOnCompletionListener(null);old.setOnSeekCompleteListener(null);}catch(RuntimeException ignored){}try{old.release();}catch(RuntimeException ignored){}}
  returning=false;pausedAt=-1;resumeFadePending=false;seekHoldActive=false;pendingStreamScrubJoin=false;audioOwner.source();audioOwner.retireDecoder();prepareTicket=null;bufferGate.reset();bufferWaiting=false;if(streaming!=null){streaming.close();streaming=null;}ready=false;seeking=false;fading=false;aligned=false;resumePositionRetained=false;
  if(loudness!=null){try{loudness.release();}catch(RuntimeException ignored){}loudness=null;}if(audioFile!=null){audioFile.delete();audioFile=null;}if(had)LogStore.log("replacement_released",LogStore.map("reason",reason));
 }
 void suspend(String reason,long delay){if(streaming!=null&&Arrays.asList("prepare_timeout","prepare_failed","duration_or_session_invalid","seek_timeout","media_player_error","decoder_start_timeout").contains(reason)){streamFallbackKey=identityKey;delay=1000;LogStore.log("replacement_stream_fallback",LogStore.map("reason",reason));}if("replacement_completed".equals(reason)||"replacement_end".equals(reason)||"source_end".equals(reason)){completedKey=identityKey;completedPosition=owner.current==null?0:position(owner.current);}generation++;preparing=false;release(reason);descriptor=null;lookupKey=null;nextLookup=SystemClock.elapsedRealtime()+delay;audioOwner.recovering(reason);ownerEvent("recovery");LogStore.log("replacement_recovery",LogStore.map("reason",reason,"automaticModeRetained",armed(),"retryMs",delay));}
 void returnOriginal(){
  if(!accountLeaseCurrent())return;
  if(player==null||effect==null||!ready||!current(identityKey)||!owner.current.playing
     ||seeking||audioOwner.seekInFlight(player)||originalMix>0.001f){
    /* No return animation may grant audible replacement during a seek. */
    stop("owner_return_original");return;
   }
  /* A manual return is a first-class owner transition: it invalidates
     previous handover command tickets, including their scheduled ramp ticks. */
  audioOwner.event(AudioOwnership.Event.RETURN);
  final AudioOwnership.Ticket returnTicket=audioOwner.ticket(identityKey,api.accountGeneration,
     descriptor==null?0:descriptor.optLong("replacement_id"),
     descriptor==null?0:descriptor.optLong("version"),
     descriptor==null?0:descriptor.optLong("duration_ms"));
  preloadAllowed=false;armedUntil=0;returning=true;fading=false;seeking=false;final long token=++transition;final MediaPlayer p=player;final DynamicsProcessing fx=effect;final long start=SystemClock.elapsedRealtime();status="Возвращаем оригинал без наложения звука…";
  Runnable ramp=new Runnable(){public void run(){if(token!=transition||p!=player||fx!=effect||!accountLeaseCurrent())return;
     if(!audioOwner.commandCurrent(returnTicket,api.accountGeneration,identityKey,
         descriptor==null?0:descriptor.optLong("replacement_id"),
         descriptor==null?0:descriptor.optLong("version"),
         descriptor==null?0:descriptor.optLong("duration_ms")))return;
     try{if(!current(identityKey)||!owner.current.playing){stop("return_source_changed");return;}float mix=TransitionMix.progress(SystemClock.elapsedRealtime()-start,FADE_MS);if(mix<1f){audioOwner.grantReplacement(fx);originalMix=0f;applyVolume(1f-mix);owner.handler.postDelayed(this,20);}else{applyVolume(0);stop("owner_return_original");}}catch(RuntimeException ex){stop("return_failed");}}};ramp.run();
 }
 void stop(String reason){previousSource=null;completedKey=null;completedReason=null;durationConfirmationRequired=false;clockSupervisor.reset();explicitSourceSeek=false;unavailableSince=-1;waitingForRouteResume=false;routePauseObserved=false;preloadAllowed=false;clearAudioCache();returning=false;armedUntil=0;trustedSession=-1;generation++;preparing=false;release(reason);descriptor=null;lookupKey=null;nextLookup=0;status="Замена выключена; играет оригинал";authorizationAccount=-1;audioOwner.event(AudioOwnership.Event.STOP);audioOwner.stopped();ownerEvent("stopped");if("yandex_audio_session_changed".equals(reason)||"effect_control_lost".equals(reason))status="Яндекс сменил аудиосессию. Открой его эквалайзер → CELIKOM и снова включи автозамену";else if("headphones_disconnected".equals(reason))status="Наушники отключены. Оригинал восстановлен; подключи их и снова включи автозамену";LogStore.log("replacement_trial_stop",LogStore.map("reason",reason));}
 void close(){closed=true;stop("service_stopped");}
 void ownerEvent(String event){LogStore.log("audio_owner_state",LogStore.map("event",event,"state",audioOwner.state().name(),"ownerGeneration",audioOwner.epoch(),"ownerReason",audioOwner.reason(),"trackId",trackId,"identityKey",identityKey,"replacementVolume",commandedReplacementVolume,"sourceMutedCommand",effect!=null&&originalMix<=0.001f,"hardwareOutputMeasured",false));}
 void logSync(String state,PlaybackSource s,long drift){String key=state+"|"+s.key;long now=SystemClock.elapsedRealtime();if(!key.equals(lastSync)||lastSyncAt<0||now-lastSyncAt>=10000||Math.abs(drift-lastLoggedDrift)>=500){lastSync=key;lastSyncAt=now;lastLoggedDrift=drift;LogStore.log("replacement_sync",LogStore.map("state",state,"trackId",trackId,"sourcePositionMs",position(s),"driftMs",drift));}}

 static String message(String code){switch(code){case "login_required":case "invalid_session":return "нужно войти в CELIKOM";case "access_denied":case "trial_not_activated":return "нет активного доступа CELIKOM";case "invalid_credentials":return "неверная почта или пароль";case "rate_limited":return "слишком много запросов — попробуй позже";default:return code;}}
}
