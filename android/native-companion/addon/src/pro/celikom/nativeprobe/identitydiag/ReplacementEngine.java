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
 static final long PREPARED_MS=60000, SEEK_TIMEOUT_MS=2000, HANDOVER_DRIFT_MS=350, STREAM_SEEK_TIMEOUT_MS=12000, FADE_MS=360, PAUSE_GRACE_MS=30000, PAUSE_RESUME_FADE_MS=180, PAUSE_ALIGN_DELAY_MS=160, PAUSE_ALIGN_TOLERANCE_MS=85, NEW_TRACK_JOIN_MS=60;
 final ProbeService owner; final NativeApi api;
 String status="Замена выключена",identityKey,trackId,method="NONE",lookupKey;
 JSONObject descriptor; long descriptorUntil,nextLookup,armedUntil,preparedAt,seekStarted,seekBudget=SEEK_TIMEOUT_MS,fadeStarted,transition,pausedAt=-1;
 long warmSeekTransition=-1;boolean handoverPending;long pauseRestoreDelayMs=PAUSE_GRACE_MS;
 final AudioOwnership audioOwner=new AudioOwnership();
 final AudioContinuityMonitor continuity=new AudioContinuityMonitor();float commandedReplacementVolume;
 volatile long generation; int trustedSession=-1,failures,seekCorrections;
 final BufferRecoveryGate bufferGate=new BufferRecoveryGate();BufferedAudio streaming;boolean bufferWaiting;String streamFallbackKey;
 MediaPlayer player; DynamicsProcessing effect; LoudnessEnhancer loudness; File audioFile;
 float originalMix=1f; boolean ready,closed,preparing,seeking,fading,aligned,returning,preloadAllowed=true,waitingForRouteResume,routePauseObserved,resumePositionRetained,resumeFadePending; String lastSync="";
 final SyncPolicy syncPolicy=new SyncPolicy();PlaybackSource previousSource;boolean explicitSourceSeek;long unavailableSince=-1,lastSyncAt=-1,lastLoggedDrift;String completedKey;long completedPosition,resumeDrift;
 final Set<String> confirmed=new HashSet<>();
 // Private, bounded to this foreground run. Every reuse requires a new live resolve.
 static final long CACHE_BYTES=62914560;
 final LinkedHashMap<String,File> recentAudio=new LinkedHashMap<>();
 String audioKey(JSONObject j){return trackId+"|"+j.optLong("replacement_id")+"|"+j.optLong("version")+"|"+j.optLong("duration_ms")+"|"+j.optString("mime_type","audio/mpeg");}
 void clearAudioCache(){for(File f:recentAudio.values())f.delete();recentAudio.clear();}
 void rememberAudio(){if(streaming!=null&&audioFile==null)audioFile=streaming.retainComplete();if(audioFile==null||descriptor==null||!ready||!api.signedIn())return;String key=audioKey(descriptor);File old=recentAudio.remove(key);if(old!=null&&!old.equals(audioFile))old.delete();recentAudio.put(key,audioFile);audioFile=null;long size=0;for(File f:recentAudio.values())size+=f.length();Iterator<File> it=recentAudio.values().iterator();while(it.hasNext()&&(recentAudio.size()>3||size>CACHE_BYTES)){File f=it.next();size-=f.length();f.delete();it.remove();}}

 ReplacementEngine(ProbeService owner){this.owner=owner;api=NativeApi.get(owner);}
 static Integer verifiedSession(Context c){try{Class<?> store=Class.forName("pro.celikom.nativeprobe.ProbeStore");Object instance=store.getField("INSTANCE").get(null);if(!Boolean.TRUE.equals(store.getMethod("enabled",Context.class).invoke(instance,c)))return null;JSONObject report=(JSONObject)store.getMethod("report",Context.class).invoke(instance,c);Class<?> cls=Class.forName("pro.celikom.nativeprobe.AttenuationService");Object companion=cls.getField("Companion").get(null);return (Integer)companion.getClass().getMethod("verifiedSession",JSONObject.class,long.class).invoke(companion,report,System.currentTimeMillis());}catch(Exception e){return null;}}
 void arm(){if(closed)return;if(returning)stop("rearm_during_return");if(!api.signedIn()){status="Сначала войди в свой аккаунт CELIKOM";return;}
  Integer session=verifiedSession(owner);
  if(session!=null&&session>0){if(trustedSession>0&&trustedSession!=session){generation++;preparing=false;release("session_rearmed");descriptor=null;lookupKey=null;}trustedSession=session;}
  preloadAllowed=true;armedUntil=Long.MAX_VALUE;
  status=trustedSession>0?"Автозамена включена":"Открой эквалайзер Яндекс Музыки и выбери CELIKOM";
  LogStore.log("replacement_trial_start",LogStore.map("durationLimited",false,"verifiedAudioSession",trustedSession,"waitingForVerifiedSession",trustedSession<=0,"automaticNextTracks",true,"preparedBeforeArm",ready));update(owner.current);
 }
 void attachPendingSession(){if(!armed()||trustedSession>0)return;Integer session=verifiedSession(owner);if(session!=null&&session>0){trustedSession=session;status="Подключение получено; автозамена включена";LogStore.log("replacement_session_attached",LogStore.map("sessionId",session,"source","verified_yandex_panel"));}}
 void headphonesDisconnected(){
  if(!armed()&&!returning&&effect==null)return;
  if(returning){stop("headphones_disconnected_during_return");return;}
  resumePositionRetained=player!=null&&ready&&aligned&&!seeking;waitingForRouteResume=true;routePauseObserved=false;transition++;fading=false;handoverPending=false;warmSeekTransition=-1;aligned=false;pausedAt=-1;
  try{if(player!=null&&ready){setAuditedVolume(player,0f);if(player.isPlaying())player.pause();}}catch(RuntimeException ex){suspend("route_pause_failed",0);}
  unmute();
  status="Наушники отключены. Пауза; нажми ▶ в Яндексе, чтобы продолжить с автозаменой";
  LogStore.log("replacement_route_pause",LogStore.map("automaticModeRetained",armed(),"preparedAudioRetained",ready,"sessionId",trustedSession));
  owner.pauseForRouteLoss();
 }
 String confirmationKey(){PlaybackSource s=owner.current;return s==null?"":s.albumId+"|"+s.title+"|"+s.artist+"|"+s.duration+"|"+trackId;}
 void confirm(){if(identityKey!=null&&trackId!=null){confirmed.add(confirmationKey());LogStore.log("metadata_candidate_confirmed",LogStore.map("trackId",trackId,"identityKey",identityKey));lookupKey=null;nextLookup=0;update(owner.current);}}
 void identity(Map<String,Object> o,Map<String,Object> decision){String key=PlaybackSource.key(String.valueOf(o.get("mediaAlias")),o.get("albumId"),String.valueOf(o.get("title")),String.valueOf(o.get("artist")),((Number)o.get("durationMs")).longValue());PlaybackSource s=owner.current;if(s==null||!s.key.equals(key))return;String id=(String)decision.get("candidateTrackId");String nextMethod=String.valueOf(decision.get("method"));if(!Objects.equals(identityKey,key)||!Objects.equals(trackId,id)){completedKey=null;generation++;preparing=false;release("identity_changed");nextLookup=0;failures=0;descriptor=null;lookupKey=null;}identityKey=key;trackId=id;method=nextMethod;if(id==null){status="Песня пока не определена однозначно; играет оригинал";return;}update(s);}
 boolean current(String key){PlaybackSource s=owner.current;return !closed&&owner.alive()&&s!=null&&ApiContract.current(key,s.key,SystemClock.elapsedRealtime()-s.observed,s.connected);}
 boolean armed(){return !closed&&armedUntil!=0;}
 long position(PlaybackSource s){long extra=s.playing?Math.max(0,SystemClock.elapsedRealtime()-s.observed):0;return Math.min(s.duration,Math.max(0,s.position+extra));}
 void update(PlaybackSource s){if(closed||returning)return;attachPendingSession();
  if(s!=null&&(!s.connected||SystemClock.elapsedRealtime()-s.observed>1500)){if(player!=null||preparing||lookupKey!=null)suspend("source_unavailable",1000);status="Ожидаем подключение к Яндексу; играет оригинал";return;}
  if(s==null){
   long now=SystemClock.elapsedRealtime();if(unavailableSince<0){unavailableSince=now;transition++;fading=false;handoverPending=false;warmSeekTransition=-1;seeking=false;resumePositionRetained=ready&&aligned;aligned=false;syncPolicy.reset();try{if(player!=null&&ready){setAuditedVolume(player,0f);if(player.isPlaying())player.pause();}}catch(RuntimeException ignored){}unmute();LogStore.log("replacement_source_wait",LogStore.map("decoderRetained",player!=null&&ready,"graceMs",1500));}
   if(now-unavailableSince>=1500&&(player!=null||preparing||lookupKey!=null))suspend("source_unavailable",1000);status="Ожидаем подключение к Яндексу; играет оригинал";return;
  }
  unavailableSince=-1;
  boolean sourceJump=explicitSourceSeek;PlaybackSource previous=previousSource;previousSource=s;
  if(previous!=null&&previous.key.equals(s.key)&&previous.playing&&s.playing&&s!=previous&&s.observed>=previous.observed&&Math.abs(s.position-(previous.position+s.observed-previous.observed))>900)sourceJump=true;
  if(completedKey!=null&&completedKey.equals(s.key)){
   if(s.playing&&s.position<completedPosition-1500){completedKey=null;lookupKey=null;descriptor=null;nextLookup=0;LogStore.log("replacement_repeat_detected",LogStore.map("sourcePositionMs",s.position));}
   else{status="Ожидаем следующую песню; играет оригинал";return;}
  }
  if(waitingForRouteResume){if(!s.playing){routePauseObserved=true;status="Наушники отключены. Нажми ▶ в Яндексе для продолжения";return;}if(!routePauseObserved){status="Ждём паузу Яндекса после отключения наушников";return;}waitingForRouteResume=false;pausedAt=-1;aligned=false;LogStore.log("replacement_route_resume",LogStore.map("sessionId",trustedSession,"sourcePlaying",true));}
  if(!s.key.equals(identityKey)){if(player!=null||preparing){generation++;preparing=false;release("track_changed");descriptor=null;lookupKey=null;}return;}
  if(trackId==null||(!armed()&&!preloadAllowed))return;
  if(!api.signedIn()){clearAudioCache();if(player!=null||preparing)suspend("login_required",0);status="ID найден; войди в CELIKOM для проверки замены";return;}
  if(!"ALBUM".equals(method)&&!confirmed.contains(confirmationKey())){status="Резерв нашёл песню. Подтверди найденную версию; пока играет оригинал";return;}
  if(!Float.isFinite(s.speed)||Math.abs(s.speed-1f)>0.01f){if(player!=null||preparing)suspend("unsupported_speed",1000);status="Для замены нужна скорость 1×; играет оригинал";return;}
  long clock=SystemClock.elapsedRealtime();
  if(ready&&!armed()&&clock-preparedAt>PREPARED_MS){generation++;release("prepared_expired");descriptor=null;lookupKey=null;}
  if(!identityKey.equals(lookupKey)){if(clock<nextLookup)return;lookupKey=identityKey;final String key=identityKey,id=trackId;final long g=generation;status="Проверяем замену на сервере…";api.resolve(id,()->!closed&&g==generation&&api.signedIn()&&current(key),(j,error)->{if(closed||g!=generation)return;if(!current(key)){if(Objects.equals(lookupKey,key)){lookupKey=null;descriptor=null;nextLookup=SystemClock.elapsedRealtime()+1000;status="Ожидаем актуальное состояние Яндекс Музыки";LogStore.log("replacement_lookup_deferred",LogStore.map("reason","source_not_current","retryMs",1000));}return;}if(error!=null){LogStore.log("replacement_resolve",LogStore.map("trackId",id,"errorCode",error));boolean denied=Arrays.asList("invalid_session","access_denied","login_required","unauthorized","trial_not_activated").contains(error);if(denied)clearAudioCache();if(!denied){lookupKey=null;nextLookup=SystemClock.elapsedRealtime()+retryDelay();}status="Сервер: "+message(error)+"; играет оригинал";return;}descriptor=j;descriptorUntil=SystemClock.elapsedRealtime()+15000;boolean found=j.optBoolean("found",false);status=found?"Замена найдена; готовим заранее":"В каталоге CELIKOM этой замены нет; играет оригинал";LogStore.log("replacement_resolve",LogStore.map("trackId",id,"found",found,"replacementId",j.optLong("replacement_id"),"durationMs",j.optLong("duration_ms")));if(found)prepare(key,j,g);});return;}
  if(descriptor!=null&&descriptor.optBoolean("found")&&player==null&&!preparing){if(clock>descriptorUntil){lookupKey=null;descriptor=null;return;}prepare(identityKey,descriptor,generation);}
  if(player==null||!ready||!armed())return;
  if(trustedSession<=0){status="Автозамена ожидает подключения: открой эквалайзер Яндекса → CELIKOM один раз";return;}
  try{
   if(!s.playing){pauseSource(s);return;}
   boolean resumed=pausedAt>=0;long pausedDuration=resumed?Math.max(0,clock-pausedAt):0;
   if(resumed){audioOwner.cancelPause();resumeFadePending=true;LogStore.log("replacement_resume_fast",LogStore.map("retainedOriginalEffect",effect!=null,"pauseDurationMs",pausedDuration));}
   pausedAt=-1;
   if(streaming!=null&&streaming.closed){suspend("stream_interrupted",1000);return;}
   boolean waiting=streaming!=null&&streaming.stalled();
   // While a seek is waiting, restore the original without cancelling/repeating that seek.
   if(waiting&&seeking&&effect!=null){setAuditedVolume(player,0f);if(player.isPlaying())player.pause();unmute();}
   if(streaming!=null&&bufferGate.recover(waiting,aligned&&!bufferWaiting,seeking,player.getCurrentPosition(),clock)){
    if(!bufferWaiting){bufferWaiting=true;transition++;fading=false;handoverPending=false;warmSeekTransition=-1;aligned=false;seeking=false;resumePositionRetained=false;setAuditedVolume(player,0f);if(player.isPlaying())player.pause();unmute();LogStore.log("replacement_buffer_wait",LogStore.map("trackId",trackId,"cachedBytes",streaming.cachedBytes()));}
    status="Связь замедлилась; играет оригинал, подгружаем замену";return;
   }
   if(bufferWaiting){if(waiting)return;bufferGate.reset();bufferWaiting=false;aligned=false;LogStore.log("replacement_buffer_resumed",LogStore.map("trackId",trackId));}
   if(seeking){if(clock-seekStarted>seekBudget)suspend("seek_timeout",retryDelay());return;}
   long target=position(s);if(target>=s.duration){suspend("source_end",30000);return;}if(target>=player.getDuration()){suspend("replacement_end",30000);return;}
   long drift=target-player.getCurrentPosition();
   if(fading&&handoverPending&&!sourceJump)return;
   // A retained paused decoder already at the native position needs no seek.
   if(!aligned&&resumePositionRetained&&!sourceJump&&Math.abs(drift)<=PAUSE_ALIGN_TOLERANCE_MS){aligned=true;resumePositionRetained=false;LogStore.log("replacement_resume_aligned",LogStore.map("trackId",trackId,"driftMs",drift,"seekSkipped",true));}
   /* Source position is authoritative after a pause: resync off-output if necessary. */
   if(resumed&&pausedDuration>=PAUSE_ALIGN_DELAY_MS&&effect!=null&&Math.abs(drift)>PAUSE_ALIGN_TOLERANCE_MS){seek(s,target,drift);return;}
   if(syncPolicy.correct(aligned,drift,sourceJump,clock)){seek(s,target,drift);return;}
   boolean seamlessResume=resumed&&effect!=null&&originalMix<=0.001f&&!sourceJump&&Math.abs(drift)<=PAUSE_ALIGN_TOLERANCE_MS;
   boolean newlyAttached=effect==null;
   if(newlyAttached&&!mute())return;
   if(!effect.hasControl()||!effect.getEnabled()){stop("effect_control_lost");return;}
   if(!player.isPlaying()){if(seamlessResume){audioOwner.grantReplacement(effect);originalMix=0f;applyVolume(1f);}else setAuditedVolume(player,0f);player.start();try{LogStore.log("audio_decoder_start",LogStore.map("trackId",trackId,"decoderPositionMs",player.getCurrentPosition(),"sourcePositionMs",position(s),"reusePreparedDecoder",true,"seekPending",seeking,"sourceMutedCommand",effect!=null&&originalMix<=0.001f));}catch(RuntimeException ignored){}traceAudioCommands();if(seamlessResume){fading=false;resumeFadePending=false;audioOwner.replacement();LogStore.log("replacement_resume_seamless",LogStore.map("trackId",trackId,"driftMs",drift,"sourcePositionMs",target,"retainedEffect",true));}else fade();}
   else if(newlyAttached){setAuditedVolume(player,0f);fade();}
   else if(!fading){audioOwner.grantReplacement(effect);originalMix=0f;applyVolume(1f);}
   status="Играет замена · автопереход включён";logSync("playing",s,drift);
  }catch(RuntimeException e){suspend("playback_exception",retryDelay());status="Ошибка звука — оригинал восстановлен; повторим автоматически";LogStore.log("replacement_failure",LogStore.map("reason","playback_exception","type",e.getClass().getSimpleName()));}
 }
 void outgoingTrackReset(PlaybackSource previous){
  if(player==null&&effect==null)return;
  long projected=position(previous);
  LogStore.log("replacement_outgoing_reset",LogStore.map("trackId",trackId,"previousAlias",previous.alias,"previousPositionMs",projected,"previousDurationMs",previous.duration,"remainingMs",Math.max(0,previous.duration-projected),"oldDecoderPlaying",player!=null&&player.isPlaying(),"oldOriginalMuted",effect!=null&&originalMix<=0.001f));
  suspend("source_end",30000);
 }
 void sourceSeekRequested(){if(armed())explicitSourceSeek=true;}
 void sourceBoundary(String reason){
  if(closed)return;generation++;preparing=false;release("track_changed");identityKey=null;trackId=null;method="NONE";descriptor=null;lookupKey=null;nextLookup=0;failures=0;previousSource=null;completedKey=null;explicitSourceSeek=false;unavailableSince=-1;syncPolicy.reset();status="Определяем новую песню; играет оригинал";LogStore.log("replacement_source_boundary",LogStore.map("reason",reason,"originalRestoredBeforeLookup",true));
 }
 void sourceChanged(PlaybackSource previous,PlaybackSource next){
  long ownPosition=-1,ownDuration=-1;
  try{if(player!=null&&ready){ownPosition=player.getCurrentPosition();ownDuration=player.getDuration();}}catch(RuntimeException ignored){}
  LogStore.log("source_track_transition",LogStore.map("previousTrackId",trackId,"previousAlias",previous.alias,"nextAlias",next.alias,"previousDurationMs",previous.duration,"previousProjectedPositionMs",position(previous),"remainingSourceMs",Math.max(0,previous.duration-position(previous)),"replacementPositionMs",ownPosition,"replacementDurationMs",ownDuration,"replacementReady",ready,"followsNativeTrackChange",true));
  if(identityKey!=null||player!=null||preparing)sourceBoundary("sample_track_changed");
 }
 void pauseSource(PlaybackSource s){
  if(player==null)return;
  if(pausedAt<0){bufferGate.reset();resumeDrift=position(s)-player.getCurrentPosition();resumePositionRetained=ready&&aligned&&!seeking;pauseRestoreDelayMs=seeking||handoverPending?350:PAUSE_GRACE_MS;pausedAt=SystemClock.elapsedRealtime();transition++;fading=false;handoverPending=false;warmSeekTransition=-1;aligned=false;setAuditedVolume(player,0f);if(player.isPlaying())player.pause();audioOwner.paused();final MediaPlayer p=player;final DynamicsProcessing fx=effect;final long token=transition;final long lease=audioOwner.pauseLease();
   owner.handler.postDelayed(()->{if(player!=p||token!=transition||pausedAt<0||seeking||!current(identityKey)||owner.current==null||owner.current.playing||!ready||!armed()||effect!=fx)return;try{long nativePosition=position(owner.current),delta=nativePosition-p.getCurrentPosition();if(Math.abs(delta)>PAUSE_ALIGN_TOLERANCE_MS){LogStore.log("replacement_pause_prealign",LogStore.map("trackId",trackId,"driftMs",delta,"pauseAgeMs",SystemClock.elapsedRealtime()-pausedAt));seek(owner.current,nativePosition,delta);}}catch(RuntimeException ex){LogStore.log("replacement_pause_prealign_failed",LogStore.map("type",ex.getClass().getSimpleName()));}},PAUSE_ALIGN_DELAY_MS);
   owner.handler.postDelayed(()->{if(player==p&&effect==fx&&token==transition&&audioOwner.validPause(lease)&&pausedAt>=0&&!seeking&&current(identityKey)&&owner.current!=null&&!owner.current.playing)unmute();},pauseRestoreDelayMs);
  }
  if(SystemClock.elapsedRealtime()-pausedAt>=pauseRestoreDelayMs)unmute();
  status="Пауза — аудио сохранено для продолжения";logSync("paused",s,0);
 }
 long retryDelay(){failures++;return Math.min(30000,5000L*(1L<<Math.min(3,failures-1)));}
 void seek(PlaybackSource s,long target,long drift){seek(s,target,drift,false);}
 void seek(PlaybackSource s,long target,long drift,boolean correction){audioOwner.aligning();explicitSourceSeek=false;syncPolicy.reset();resumePositionRetained=false;seekCorrections=correction?seekCorrections+1:0;seeking=true;aligned=true;seekStarted=SystemClock.elapsedRealtime();seekBudget=streaming!=null&&!streaming.complete()?STREAM_SEEK_TIMEOUT_MS:SEEK_TIMEOUT_MS;transition++;fading=false;handoverPending=false;warmSeekTransition=-1;setAuditedVolume(player,0f);if(player.isPlaying())player.pause();status="Синхронизация позиции…";LogStore.log("replacement_sync",LogStore.map("state","seek","trackId",trackId,"sourcePositionMs",target,"driftMs",drift,"originalStillMuted",effect!=null,"inaudibleCorrection",correction));final MediaPlayer p=player;final long t=transition;p.seekTo(target,MediaPlayer.SEEK_CLOSEST);owner.handler.postDelayed(()->{if(player==p&&seeking&&transition==t)suspend("seek_timeout",retryDelay());},seekBudget);}
 void prepare(String key,JSONObject j,long g){if(preparing||!current(key)||!api.signedIn())return;PlaybackSource s=owner.current;if(!PlaybackDuration.safe(s.duration,j.optLong("duration_ms"))){LogStore.log("replacement_duration_mismatch",LogStore.map("trackId",trackId,"sourceDurationMs",s.duration,"replacementDurationMs",j.optLong("duration_ms")));status="Версия заметно короче или длиннее — играет оригинал";descriptor=null;return;}preparing=true;status="Готовим аудио заранее; оригинал продолжает играть";
  File cached=recentAudio.remove(audioKey(j));
  if(cached!=null&&cached.isFile()){LogStore.log("replacement_audio_reused",LogStore.map("trackId",trackId,"liveResolveRequired",true));acceptAudio(key,j,g,cached,null);return;}
  if(key.equals(streamFallbackKey)){downloadFull(key,j,g);return;}
  status="Подготавливаем начало песни; играет оригинал";
  api.stream(j,()->!closed&&g==generation&&api.signedIn()&&current(key),(source,error)->{
   if(g!=generation||closed||!current(key)||!api.signedIn()){if(source!=null)source.close();if(g==generation&&!closed)suspend("stream_source_changed",1000);return;}
   if(source==null){streamFallbackKey=key;LogStore.log("replacement_stream_fallback",LogStore.map("reason","range_unavailable"));downloadFull(key,j,g);return;}
   acceptAudio(key,j,g,null,source,null);
  });
 }
 void downloadFull(String key,JSONObject j,long g){api.download(j,()->!closed&&g==generation&&api.signedIn()&&current(key),(file,error)->acceptAudio(key,j,g,file,error));}
 void acceptAudio(String key,JSONObject j,long g,File file,String error){acceptAudio(key,j,g,file,null,error);}
 void acceptAudio(String key,JSONObject j,long g,File file,BufferedAudio source,String error){if(g!=generation||closed){if(file!=null)file.delete();if(source!=null)source.close();return;}preparing=false;if(file==null&&source==null){suspend("download_failed",retryDelay());status="Сеть недоступна; играет оригинал, повторим автоматически";return;}if(!current(key)||!api.signedIn()){if(file!=null)file.delete();if(source!=null)source.close();suspend("download_source_changed",1000);return;}
   try{audioFile=file;streaming=source;bufferWaiting=false;player=new MediaPlayer();final MediaPlayer p=player;p.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());setAuditedVolume(p,0f);if(source==null)p.setDataSource(file.getAbsolutePath());else p.setDataSource(new StreamingAudio(source));p.setOnErrorListener((mp,what,extra)->{if(mp==player){suspend("media_player_error",retryDelay());LogStore.log("replacement_failure",LogStore.map("reason","media_player_error","what",what,"extra",extra));}return true;});p.setOnCompletionListener(mp->{if(mp==player)suspend("replacement_completed",30000);});p.setOnPreparedListener(mp->{if(mp!=player)return;if(g!=generation||!current(key)){suspend("prepared_stale",1000);return;}PlaybackSource now=owner.current;if(!ApiContract.durations(now.duration,j.optLong("duration_ms"),mp.getDuration())||!PlaybackDuration.safe(now.duration,mp.getDuration())||(trustedSession>0&&mp.getAudioSessionId()==trustedSession)){if(!PlaybackDuration.safe(now.duration,mp.getDuration())){LogStore.log("replacement_duration_mismatch",LogStore.map("trackId",trackId,"sourceDurationMs",now.duration,"replacementDurationMs",mp.getDuration()));completedKey=identityKey;completedPosition=position(now);}
    suspend("duration_or_session_invalid",30000);status="Проверка аудио не пройдена; играет оригинал";return;}ready=true;failures=0;preparedAt=SystemClock.elapsedRealtime();status=armed()?"Аудио готово; синхронизируем":"Аудио готово заранее; можно включать автозамену";LogStore.log("replacement_prepared",LogStore.map("trackId",trackId,"measuredDurationMs",mp.getDuration(),"sourceDurationMs",now.duration,"separateAudioSession",true,"beforeArm",!armed()));update(now);});p.setOnSeekCompleteListener(mp->completeSeek(mp,key));p.prepareAsync();if(source!=null)source.prefetch();final MediaPlayer preparingPlayer=p;owner.handler.postDelayed(()->{if(player==preparingPlayer&&!ready)suspend("prepare_timeout",retryDelay());},10000);
   }catch(Exception e){suspend("prepare_failed",retryDelay());status="Не удалось подготовить аудио; играет оригинал";}
 }
 void completeSeek(MediaPlayer mp,String key){
  if(mp!=player)return;
  if(warmSeekTransition==transition){warmSeekTransition=-1;return;}
  if(!seeking)return;
  seeking=false;
  long clock=SystemClock.elapsedRealtime(),elapsed=clock-seekStarted;
  if(!ready||!armed()||!current(key))return;
  PlaybackSource now=owner.current;
  long target=position(now),residual=target-mp.getCurrentPosition();
  LogStore.log("replacement_seek_complete",LogStore.map("elapsedMs",elapsed,"trackId",trackId,"residualMs",residual,"correctionPass",seekCorrections));
  /* A second streaming seek can also wait for data. Never publish that stale
     alignment and then correct it audibly after handover. Allow two measured
     corrections, then keep the original if the decoder cannot settle. */
  if(streaming!=null&&!waitingForRouteResume&&now.playing&&!mp.isPlaying()
    &&Math.abs(residual)>(seekCorrections==0?80:HANDOVER_DRIFT_MS)){
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
 boolean mute(){try{if(trustedSession<=0||player==null||player.getAudioSessionId()==trustedSession)throw new IllegalStateException();DynamicsProcessing candidate=new DynamicsProcessing(0,trustedSession,null);effect=candidate;candidate.setControlStatusListener((e,control)->{if(!control)owner.handler.post(()->{if(effect==candidate)stop("effect_control_lost");});});if(!candidate.hasControl())throw new IllegalStateException();originalMix=1f;audioOwner.preparing();candidate.setInputGainAllChannelsTo(0f);if(candidate.setEnabled(true)!=AudioEffect.SUCCESS)throw new IllegalStateException();LogStore.log("replacement_original_muted",LogStore.map("sessionId",trustedSession,"globalVolumeChanged",false,"rampMs",resumeFadePending?PAUSE_RESUME_FADE_MS:FADE_MS));return true;}catch(RuntimeException e){stop("cannot_mute_original");status="Телефон не разрешил приглушить Яндекс; замена остановлена";return false;}}
 void fade(){
  final long token=++transition;final MediaPlayer p=player;final DynamicsProcessing fx=effect;final float initialOriginal=originalMix;
  final boolean shortResume=resumeFadePending;
  audioOwner.aligning();
  final long rampDuration=shortResume?PAUSE_RESUME_FADE_MS:(initialOriginal<=0.001f?80:NEW_TRACK_JOIN_MS);resumeFadePending=false;
  // When attenuation stays attached through a short pause, validate decoder's advancing clock before raising replacement volume.
  final boolean alignLive=streaming!=null&&(initialOriginal>0.001f||shortResume);
  final long[] baseline={p.getCurrentPosition()},phaseStarted={SystemClock.elapsedRealtime()};final int[] corrections={0};
  fadeStarted=SystemClock.elapsedRealtime();fading=true;handoverPending=alignLive;warmSeekTransition=-1;
  Runnable ramp=new Runnable(){public void run(){
   if(closed||token!=transition||p!=player||fx!=effect||!armed())return;
   try{
    if(!current(identityKey)){suspend("fade_source_unavailable",1000);return;}
    if(!owner.current.playing){pauseSource(owner.current);return;}
    if(handoverPending){
     long now=SystemClock.elapsedRealtime(),position=p.getCurrentPosition();
     if(warmSeekTransition==token||position-baseline[0]<40){
      if(now-phaseStarted[0]>=2000){suspend("decoder_start_timeout",1000);return;}
      owner.handler.postDelayed(this,20);return;
     }
     long target=position(owner.current),drift=target-position;
     if(Math.abs(drift)>HANDOVER_DRIFT_MS){
      if(corrections[0]>=2||target>=p.getDuration()-150){suspend("alignment_unstable",retryDelay());return;}
      corrections[0]++;baseline[0]=target;phaseStarted[0]=now;warmSeekTransition=token;
      LogStore.log("replacement_warm_alignment",LogStore.map("trackId",trackId,"driftMs",drift,"pass",corrections[0],"replacementAudible",false));
      /* Seek the running muted decoder. A pause/start would recreate its startup lag. */
      p.seekTo(Math.max(0,target),MediaPlayer.SEEK_CLOSEST);owner.handler.postDelayed(this,20);return;
     }
     handoverPending=false;fadeStarted=now;
     LogStore.log("replacement_decoder_advancing",LogStore.map("trackId",trackId,"driftMs",drift,"corrections",corrections[0],"waitMs",now-phaseStarted[0]));
    }
    float mix=TransitionMix.progress(SystemClock.elapsedRealtime()-fadeStarted,rampDuration);
    // Break-before-make: an original and its replacement must NEVER be audible together.
    // Wait for decoder progress/alignment first; then mute native source completely,
    // and only afterwards raise replacement. Do not reintroduce a crossfade here.
    if(mix>0){audioOwner.grantReplacement(fx);originalMix=0f;}
    applyVolume(mix);
    if(mix<1f)owner.handler.postDelayed(this,20);else{fading=false;handoverPending=false;warmSeekTransition=-1;audioOwner.replacement();LogStore.log("replacement_transition_complete",LogStore.map("trackId",trackId,"rampMs",SystemClock.elapsedRealtime()-fadeStarted));}
   }catch(RuntimeException e){suspend("fade_failed",retryDelay());}
  }};ramp.run();
 }
 /* These are our own output commands, NOT an acoustic or Bluetooth measurement. */
 void setAuditedVolume(MediaPlayer p,float volume){
  p.setVolume(volume,volume);
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
     trackId,cause,playing,muted,decoder,commandedReplacementVolume);
   if(finding!=null)LogStore.log("audio_command_anomaly",LogStore.map(
     "kind",finding.kind,"trackId",finding.trackId,"cause",finding.cause,
     "durationMs",finding.durationMs,"transition",transition,
     "sourcePlaying",playing,"sourceMutedCommand",muted,
     "decoderPlaying",decoder,"replacementVolumeCommand",commandedReplacementVolume,
     "seekPending",seeking,"ownerState",audioOwner.state().name(),
     "hardwareOutputMeasured",false));
  }catch(RuntimeException ignored){} /* Telemetry cannot break playback. */
 }
 void applyVolume(float mix){double gain=descriptor==null?0:descriptor.optDouble("gain_db",0);float volume=mix*(float)Math.min(1,Math.pow(10,Math.min(0,gain)/20));setAuditedVolume(player,volume);if(gain>0&&loudness==null)try{loudness=new LoudnessEnhancer(player.getAudioSessionId());loudness.setTargetGain((int)Math.round(gain*100));loudness.setEnabled(true);}catch(RuntimeException ignored){LogStore.log("replacement_gain","positive gain unavailable");}}
 void unmute(){if(effect!=null){audioOwner.silenceReplacement(player);commandedReplacementVolume=0f;DynamicsProcessing fx=effect;effect=null;boolean gainReset=false,disabled=false,released=false;try{fx.setControlStatusListener(null);}catch(RuntimeException ignored){}try{fx.setInputGainAllChannelsTo(0f);gainReset=true;}catch(RuntimeException ignored){}try{disabled=fx.setEnabled(false)==AudioEffect.SUCCESS;}catch(RuntimeException ignored){}try{fx.release();released=true;}catch(RuntimeException ignored){}originalMix=1f;audioOwner.source();LogStore.log("replacement_original_restored",LogStore.map("reason","effect_released","gainReset",gainReset,"disabled",disabled,"released",released,"hardwareAudibilityVerified",false));traceAudioCommands();}}
 /* Invalidate ramps and silence output before cache, network or diagnostic cleanup.
    HttpURLConnection.disconnect and effect release may block on the old route. */
 MediaPlayer silenceBeforeCleanup(){transition++;fading=false;handoverPending=false;warmSeekTransition=-1;MediaPlayer old=player;player=null;if(old!=null){boolean zero=false,paused=false;try{setAuditedVolume(old,0f);zero=true;}catch(RuntimeException ignored){}try{if(old.isPlaying())old.pause();paused=!old.isPlaying();}catch(RuntimeException ignored){}LogStore.log("replacement_output_silenced",LogStore.map("trackId",trackId,"gainZero",zero,"paused",paused,"beforeTransportCleanup",true));}unmute();return old;}
 void release(String reason){
  audioOwner.cancelPause();
  boolean had=player!=null||effect!=null;MediaPlayer old=silenceBeforeCleanup();
  if("identity_changed".equals(reason)||"track_changed".equals(reason)||"replacement_end".equals(reason)||"replacement_completed".equals(reason)||"source_end".equals(reason)||"source_unavailable".equals(reason)||"source_disconnected".equals(reason))rememberAudio();
  /* Detach a completed file before MediaPlayer.release closes its MediaDataSource. */
  if(old!=null){try{old.setOnErrorListener(null);old.setOnPreparedListener(null);old.setOnCompletionListener(null);old.setOnSeekCompleteListener(null);}catch(RuntimeException ignored){}try{old.release();}catch(RuntimeException ignored){}}
  returning=false;pausedAt=-1;resumeFadePending=false;audioOwner.source();bufferGate.reset();bufferWaiting=false;if(streaming!=null){streaming.close();streaming=null;}ready=false;seeking=false;fading=false;handoverPending=false;warmSeekTransition=-1;aligned=false;resumePositionRetained=false;
  if(loudness!=null){try{loudness.release();}catch(RuntimeException ignored){}loudness=null;}if(audioFile!=null){audioFile.delete();audioFile=null;}if(had)LogStore.log("replacement_released",LogStore.map("reason",reason));
 }
 void suspend(String reason,long delay){if(streaming!=null&&Arrays.asList("prepare_timeout","prepare_failed","duration_or_session_invalid","seek_timeout","media_player_error","decoder_start_timeout").contains(reason)){streamFallbackKey=identityKey;delay=1000;LogStore.log("replacement_stream_fallback",LogStore.map("reason",reason));}if("replacement_completed".equals(reason)||"replacement_end".equals(reason)||"source_end".equals(reason)){completedKey=identityKey;completedPosition=owner.current==null?0:position(owner.current);}generation++;preparing=false;release(reason);descriptor=null;lookupKey=null;nextLookup=SystemClock.elapsedRealtime()+delay;LogStore.log("replacement_recovery",LogStore.map("reason",reason,"automaticModeRetained",armed(),"retryMs",delay));}
 void returnOriginal(){
  if(player==null||effect==null||!ready||!current(identityKey)||!owner.current.playing){stop("owner_return_original");return;}
  preloadAllowed=false;armedUntil=0;returning=true;fading=false;handoverPending=false;warmSeekTransition=-1;seeking=false;final long token=++transition;final MediaPlayer p=player;final DynamicsProcessing fx=effect;final long start=SystemClock.elapsedRealtime();status="Возвращаем оригинал без наложения звука…";
  Runnable ramp=new Runnable(){public void run(){if(token!=transition||p!=player||fx!=effect)return;try{if(!current(identityKey)||!owner.current.playing){stop("return_source_changed");return;}float mix=TransitionMix.progress(SystemClock.elapsedRealtime()-start,FADE_MS);if(mix<1f){audioOwner.grantReplacement(fx);originalMix=0f;applyVolume(1f-mix);owner.handler.postDelayed(this,20);}else{applyVolume(0);stop("owner_return_original");}}catch(RuntimeException ex){stop("return_failed");}}};ramp.run();
 }
 void stop(String reason){previousSource=null;completedKey=null;explicitSourceSeek=false;unavailableSince=-1;syncPolicy.reset();waitingForRouteResume=false;routePauseObserved=false;preloadAllowed=false;clearAudioCache();returning=false;armedUntil=0;trustedSession=-1;generation++;preparing=false;release(reason);descriptor=null;lookupKey=null;nextLookup=0;status="Замена выключена; играет оригинал";if("yandex_audio_session_changed".equals(reason)||"effect_control_lost".equals(reason))status="Яндекс сменил аудиосессию. Открой его эквалайзер → CELIKOM и снова включи автозамену";else if("headphones_disconnected".equals(reason))status="Наушники отключены. Оригинал восстановлен; подключи их и снова включи автозамену";LogStore.log("replacement_trial_stop",LogStore.map("reason",reason));}
 void close(){closed=true;stop("service_stopped");}
 void logSync(String state,PlaybackSource s,long drift){String key=state+"|"+s.key;long now=SystemClock.elapsedRealtime();if(!key.equals(lastSync)||lastSyncAt<0||now-lastSyncAt>=10000||Math.abs(drift-lastLoggedDrift)>=500){lastSync=key;lastSyncAt=now;lastLoggedDrift=drift;LogStore.log("replacement_sync",LogStore.map("state",state,"trackId",trackId,"sourcePositionMs",position(s),"driftMs",drift));}}

 static String message(String code){switch(code){case "login_required":case "invalid_session":return "нужно войти в CELIKOM";case "access_denied":case "trial_not_activated":return "нет активного доступа CELIKOM";case "invalid_credentials":return "неверная почта или пароль";case "rate_limited":return "слишком много запросов — попробуй позже";default:return code;}}
}
