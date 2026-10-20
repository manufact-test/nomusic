package pro.celikom.nativeprobe.identitydiag;
import android.media.*;
import android.media.audiofx.*;
import android.os.*;
import android.content.Context;
import org.json.*;
import java.io.*;
import java.util.*;
/** Owner-enabled automatic replacement within the foreground diagnostic run. */
final class ReplacementEngine {
 static final long RUN_MS=720000, PREPARED_MS=60000, SEEK_TIMEOUT_MS=2000, FADE_MS=140, PAUSE_GRACE_MS=350;
 final ProbeService owner; final NativeApi api;
 String status="Замена выключена",identityKey,trackId,method="NONE",lookupKey;
 JSONObject descriptor; long descriptorUntil,nextLookup,armedUntil,preparedAt,seekStarted,fadeStarted,transition,settleUntil,pausedAt=-1;
 volatile long generation; int trustedSession=-1,failures,seekCorrections;
 MediaPlayer player; DynamicsProcessing effect; LoudnessEnhancer loudness; File audioFile;
 float originalMix=1f; boolean ready,closed,preparing,seeking,fading,aligned,returning,preloadAllowed=true,waitingForRouteResume,routePauseObserved,resumePositionRetained; String lastSync="";
 final Set<String> confirmed=new HashSet<>();
 // Private, bounded to this foreground run. Every reuse requires a new live resolve.
 static final long CACHE_BYTES=62914560;
 final LinkedHashMap<String,File> recentAudio=new LinkedHashMap<>();
 String audioKey(JSONObject j){return trackId+"|"+j.optLong("replacement_id")+"|"+j.optLong("version")+"|"+j.optLong("duration_ms")+"|"+j.optString("mime_type","audio/mpeg");}
 void clearAudioCache(){for(File f:recentAudio.values())f.delete();recentAudio.clear();}
 void rememberAudio(){if(audioFile==null||descriptor==null||!ready||!api.signedIn())return;String key=audioKey(descriptor);File old=recentAudio.remove(key);if(old!=null&&!old.equals(audioFile))old.delete();recentAudio.put(key,audioFile);audioFile=null;long size=0;for(File f:recentAudio.values())size+=f.length();Iterator<File> it=recentAudio.values().iterator();while(it.hasNext()&&(recentAudio.size()>3||size>CACHE_BYTES)){File f=it.next();size-=f.length();f.delete();it.remove();}}

 ReplacementEngine(ProbeService owner){this.owner=owner;api=NativeApi.get(owner);}
 static Integer verifiedSession(Context c){try{Class<?> store=Class.forName("pro.celikom.nativeprobe.ProbeStore");Object instance=store.getField("INSTANCE").get(null);if(!Boolean.TRUE.equals(store.getMethod("enabled",Context.class).invoke(instance,c)))return null;JSONObject report=(JSONObject)store.getMethod("report",Context.class).invoke(instance,c);Class<?> cls=Class.forName("pro.celikom.nativeprobe.AttenuationService");Object companion=cls.getField("Companion").get(null);return (Integer)companion.getClass().getMethod("verifiedSession",JSONObject.class,long.class).invoke(companion,report,System.currentTimeMillis());}catch(Exception e){return null;}}
 void arm(){if(closed)return;if(returning)stop("rearm_during_return");if(!api.signedIn()){status="Сначала войди в свой аккаунт CELIKOM";return;}
  Integer session=verifiedSession(owner);
  if(session!=null&&session>0){if(trustedSession>0&&trustedSession!=session){generation++;preparing=false;release("session_rearmed");descriptor=null;lookupKey=null;}trustedSession=session;}
  preloadAllowed=true;armedUntil=SystemClock.elapsedRealtime()+RUN_MS;
  status=trustedSession>0?"Автозамена включена до конца общей проверки":"Автозамена ожидает подключения: открой эквалайзер Яндекса → CELIKOM один раз";
  LogStore.log("replacement_trial_start",LogStore.map("durationMs",RUN_MS,"verifiedAudioSession",trustedSession,"waitingForVerifiedSession",trustedSession<=0,"automaticNextTracks",true,"preparedBeforeArm",ready));update(owner.current);
 }
 void attachPendingSession(){if(!armed()||trustedSession>0)return;Integer session=verifiedSession(owner);if(session!=null&&session>0){trustedSession=session;status="Подключение получено; автозамена включена";LogStore.log("replacement_session_attached",LogStore.map("sessionId",session,"source","verified_yandex_panel"));}}
 void headphonesDisconnected(){
  if(!armed()&&!returning&&effect==null)return;
  if(returning){stop("headphones_disconnected_during_return");return;}
  resumePositionRetained=player!=null&&ready&&aligned&&!seeking;waitingForRouteResume=true;routePauseObserved=false;transition++;fading=false;aligned=false;pausedAt=-1;
  try{if(player!=null&&ready){player.setVolume(0,0);if(player.isPlaying())player.pause();}}catch(RuntimeException ex){suspend("route_pause_failed",0);}
  unmute();
  status="Наушники отключены. Пауза; нажми ▶ в Яндексе, чтобы продолжить с автозаменой";
  LogStore.log("replacement_route_pause",LogStore.map("automaticModeRetained",armed(),"preparedAudioRetained",ready,"sessionId",trustedSession));
  owner.pauseForRouteLoss();
 }
 String confirmationKey(){PlaybackSource s=owner.current;return s==null?"":s.albumId+"|"+s.title+"|"+s.artist+"|"+s.duration+"|"+trackId;}
 void confirm(){if(identityKey!=null&&trackId!=null){confirmed.add(confirmationKey());LogStore.log("metadata_candidate_confirmed",LogStore.map("trackId",trackId,"identityKey",identityKey));lookupKey=null;nextLookup=0;update(owner.current);}}
 void identity(Map<String,Object> o,Map<String,Object> decision){String key=PlaybackSource.key(String.valueOf(o.get("mediaAlias")),o.get("albumId"),String.valueOf(o.get("title")),String.valueOf(o.get("artist")),((Number)o.get("durationMs")).longValue());PlaybackSource s=owner.current;if(s==null||!s.key.equals(key))return;String id=(String)decision.get("candidateTrackId");String nextMethod=String.valueOf(decision.get("method"));if(!Objects.equals(identityKey,key)||!Objects.equals(trackId,id)){generation++;preparing=false;release("identity_changed");nextLookup=0;failures=0;descriptor=null;lookupKey=null;}identityKey=key;trackId=id;method=nextMethod;if(id==null){status="Песня пока не определена однозначно; играет оригинал";return;}update(s);}
 boolean current(String key){PlaybackSource s=owner.current;return !closed&&owner.alive()&&s!=null&&ApiContract.current(key,s.key,SystemClock.elapsedRealtime()-s.observed,s.connected);}
 boolean armed(){return armedUntil>SystemClock.elapsedRealtime();}
 long position(PlaybackSource s){long extra=s.playing?Math.max(0,SystemClock.elapsedRealtime()-s.observed):0;return Math.min(s.duration,Math.max(0,s.position+extra));}
 void update(PlaybackSource s){if(closed||returning)return;attachPendingSession();if(armedUntil!=0&&!armed()){stop("run_limit");return;}
  if(s==null||!s.connected||SystemClock.elapsedRealtime()-s.observed>1500){if(player!=null||preparing||lookupKey!=null)suspend("source_unavailable",1000);status="Ожидаем подключение к Яндексу; играет оригинал";return;}
  if(waitingForRouteResume){if(!s.playing){routePauseObserved=true;status="Наушники отключены. Нажми ▶ в Яндексе для продолжения";return;}if(!routePauseObserved){status="Ждём паузу Яндекса после отключения наушников";return;}waitingForRouteResume=false;pausedAt=-1;aligned=false;LogStore.log("replacement_route_resume",LogStore.map("sessionId",trustedSession,"sourcePlaying",true));}
  if(!s.key.equals(identityKey)){if(player!=null||preparing){generation++;preparing=false;release("track_changed");descriptor=null;lookupKey=null;}return;}
  if(trackId==null||(!armed()&&!preloadAllowed))return;
  if(!api.signedIn()){clearAudioCache();if(player!=null||preparing)suspend("login_required",0);status="ID найден; войди в CELIKOM для проверки замены";return;}
  if(!"ALBUM".equals(method)&&!confirmed.contains(confirmationKey())){status="Резерв нашёл песню. Подтверди найденную версию; пока играет оригинал";return;}
  if(!Float.isFinite(s.speed)||Math.abs(s.speed-1f)>0.01f){if(player!=null||preparing)suspend("unsupported_speed",1000);status="Для замены нужна скорость 1×; играет оригинал";return;}
  long clock=SystemClock.elapsedRealtime();
  if(ready&&!armed()&&clock-preparedAt>PREPARED_MS){generation++;release("prepared_expired");descriptor=null;lookupKey=null;}
  if(!identityKey.equals(lookupKey)){if(clock<nextLookup)return;lookupKey=identityKey;final String key=identityKey,id=trackId;final long g=generation;status="Проверяем замену на сервере…";api.resolve(id,(j,error)->{if(closed||g!=generation||!current(key))return;if(error!=null){LogStore.log("replacement_resolve",LogStore.map("trackId",id,"errorCode",error));boolean denied=Arrays.asList("invalid_session","access_denied","login_required","unauthorized","trial_not_activated").contains(error);if(denied)clearAudioCache();if(!denied){lookupKey=null;nextLookup=SystemClock.elapsedRealtime()+retryDelay();}status="Сервер: "+message(error)+"; играет оригинал";return;}descriptor=j;descriptorUntil=SystemClock.elapsedRealtime()+15000;boolean found=j.optBoolean("found",false);status=found?"Замена найдена; готовим заранее":"В каталоге CELIKOM этой замены нет; играет оригинал";LogStore.log("replacement_resolve",LogStore.map("trackId",id,"found",found,"replacementId",j.optLong("replacement_id"),"durationMs",j.optLong("duration_ms")));if(found)prepare(key,j,g);});return;}
  if(descriptor!=null&&descriptor.optBoolean("found")&&player==null&&!preparing){if(clock>descriptorUntil){lookupKey=null;descriptor=null;return;}prepare(identityKey,descriptor,generation);}
  if(player==null||!ready||!armed())return;
  if(trustedSession<=0){status="Автозамена ожидает подключения: открой эквалайзер Яндекса → CELIKOM один раз";return;}
  try{
   if(!s.playing){pauseSource(s);return;}
   pausedAt=-1;
   if(seeking){if(clock-seekStarted>SEEK_TIMEOUT_MS)suspend("seek_timeout",retryDelay());return;}
   long target=position(s);if(target>=player.getDuration()){if(!player.isPlaying())suspend("replacement_end",30000);return;}
   long drift=target-player.getCurrentPosition();
   // A retained paused decoder already at the native position needs no seek.
   if(!aligned&&resumePositionRetained&&Math.abs(drift)<=350){aligned=true;resumePositionRetained=false;LogStore.log("replacement_resume_aligned",LogStore.map("trackId",trackId,"driftMs",drift,"seekSkipped",true));}
   if(!aligned||Math.abs(drift)>1500||(clock>=settleUntil&&Math.abs(drift)>500)){seek(s,target,drift);return;}
   if(effect==null&&!mute())return;
   if(!effect.hasControl()||!effect.getEnabled()){stop("effect_control_lost");return;}
   if(!player.isPlaying()){player.setVolume(0,0);player.start();fade();}
   else if(!fading)applyVolume(1f);
   status="Играет замена · автопереход включён";logSync("playing",s,drift);
  }catch(RuntimeException e){suspend("playback_exception",retryDelay());status="Ошибка звука — оригинал восстановлен; повторим автоматически";LogStore.log("replacement_failure",LogStore.map("reason","playback_exception","type",e.getClass().getSimpleName()));}
 }
 void sourceChanged(PlaybackSource previous,PlaybackSource next){
  long ownPosition=-1,ownDuration=-1;
  try{if(player!=null&&ready){ownPosition=player.getCurrentPosition();ownDuration=player.getDuration();}}catch(RuntimeException ignored){}
  LogStore.log("source_track_transition",LogStore.map("previousTrackId",trackId,"previousAlias",previous.alias,"nextAlias",next.alias,"previousDurationMs",previous.duration,"previousProjectedPositionMs",position(previous),"remainingSourceMs",Math.max(0,previous.duration-position(previous)),"replacementPositionMs",ownPosition,"replacementDurationMs",ownDuration,"replacementReady",ready,"followsNativeTrackChange",true));
 }
 void pauseSource(PlaybackSource s){
  if(player==null)return;
  if(pausedAt<0){resumePositionRetained=ready&&aligned&&!seeking;pausedAt=SystemClock.elapsedRealtime();transition++;fading=false;aligned=false;player.setVolume(0,0);if(player.isPlaying())player.pause();final MediaPlayer p=player;final long token=transition;
   owner.handler.postDelayed(()->{if(player==p&&token==transition&&current(identityKey)&&!owner.current.playing)unmute();},PAUSE_GRACE_MS);
  }
  if(SystemClock.elapsedRealtime()-pausedAt>=PAUSE_GRACE_MS)unmute();
  status="Пауза — аудио сохранено для продолжения";logSync("paused",s,0);
 }
 long retryDelay(){failures++;return Math.min(30000,5000L*(1L<<Math.min(3,failures-1)));}
 void seek(PlaybackSource s,long target,long drift){seek(s,target,drift,false);}
 void seek(PlaybackSource s,long target,long drift,boolean correction){resumePositionRetained=false;seekCorrections=correction?1:0;seeking=true;aligned=true;seekStarted=SystemClock.elapsedRealtime();transition++;fading=false;player.setVolume(0,0);if(player.isPlaying())player.pause();status="Синхронизация позиции…";LogStore.log("replacement_sync",LogStore.map("state","seek","trackId",trackId,"sourcePositionMs",target,"driftMs",drift,"originalStillMuted",effect!=null,"inaudibleCorrection",correction));final MediaPlayer p=player;final long t=transition;p.seekTo(target,MediaPlayer.SEEK_CLOSEST);owner.handler.postDelayed(()->{if(player==p&&seeking&&transition==t)suspend("seek_timeout",retryDelay());},SEEK_TIMEOUT_MS);}
 void prepare(String key,JSONObject j,long g){if(preparing||!current(key)||!api.signedIn())return;PlaybackSource s=owner.current;if(Math.abs(s.duration-j.optLong("duration_ms"))>5000){status="Длительности различаются — играет оригинал";descriptor=null;return;}preparing=true;status="Готовим аудио заранее; оригинал продолжает играть";
  File cached=recentAudio.remove(audioKey(j));
  if(cached!=null&&cached.isFile()){LogStore.log("replacement_audio_reused",LogStore.map("trackId",trackId,"liveResolveRequired",true));acceptAudio(key,j,g,cached,null);return;}
  api.download(j,()->!closed&&g==generation&&api.signedIn()&&current(key),(file,error)->acceptAudio(key,j,g,file,error));
 }
 void acceptAudio(String key,JSONObject j,long g,File file,String error){if(g!=generation||closed){if(file!=null)file.delete();return;}preparing=false;if(file==null){suspend("download_failed",retryDelay());status="Сеть недоступна; играет оригинал, повторим автоматически";return;}if(!current(key)||!api.signedIn()){file.delete();suspend("download_source_changed",1000);return;}
   try{audioFile=file;player=new MediaPlayer();final MediaPlayer p=player;p.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());p.setVolume(0,0);p.setDataSource(file.getAbsolutePath());p.setOnErrorListener((mp,what,extra)->{if(mp==player){suspend("media_player_error",retryDelay());LogStore.log("replacement_failure",LogStore.map("reason","media_player_error","what",what,"extra",extra));}return true;});p.setOnCompletionListener(mp->{if(mp==player)suspend("replacement_completed",30000);});p.setOnPreparedListener(mp->{if(mp!=player)return;if(g!=generation||!current(key)){suspend("prepared_stale",1000);return;}PlaybackSource now=owner.current;if(!ApiContract.durations(now.duration,j.optLong("duration_ms"),mp.getDuration())||(trustedSession>0&&mp.getAudioSessionId()==trustedSession)){suspend("duration_or_session_invalid",30000);status="Проверка аудио не пройдена; играет оригинал";return;}ready=true;failures=0;preparedAt=SystemClock.elapsedRealtime();status=armed()?"Аудио готово; синхронизируем":"Аудио готово заранее; можно включать автозамену";LogStore.log("replacement_prepared",LogStore.map("trackId",trackId,"measuredDurationMs",mp.getDuration(),"sourceDurationMs",now.duration,"separateAudioSession",true,"beforeArm",!armed()));update(now);});p.setOnSeekCompleteListener(mp->completeSeek(mp,key));p.prepareAsync();final MediaPlayer preparingPlayer=p;owner.handler.postDelayed(()->{if(player==preparingPlayer&&!ready)suspend("prepare_timeout",retryDelay());},10000);
   }catch(Exception e){suspend("prepare_failed",retryDelay());status="Не удалось подготовить аудио; играет оригинал";}
 }
 void completeSeek(MediaPlayer mp,String key){
  if(mp!=player||!seeking)return;
  seeking=false;
  long clock=SystemClock.elapsedRealtime(),elapsed=clock-seekStarted;
  if(!ready||!armed()||!current(key))return;
  PlaybackSource now=owner.current;
  long target=position(now),residual=target-mp.getCurrentPosition();
  LogStore.log("replacement_seek_complete",LogStore.map("elapsedMs",elapsed,"trackId",trackId,"residualMs",residual,"correctionPass",seekCorrections));
  // Android seeks to the requested position but reports completion later. A
  // slow seek or codec rounding must be corrected before the fade becomes
  // audible, rather than causing another stop/seek shortly after playback.
  // One bounded measured correction; never chase callbacks in an endless loop.
  if(!waitingForRouteResume&&now.playing&&!mp.isPlaying()&&seekCorrections==0
    &&Math.abs(residual)>500&&Math.abs(residual)<=1500){
   long compensated=Math.max(0,Math.min(mp.getDuration()-1,target+residual));
   if(compensated<mp.getDuration()-150){seek(now,compensated,residual,true);return;}
  }
  settleUntil=clock+1200;
  update(now);
 }
 boolean mute(){try{if(trustedSession<=0||player==null||player.getAudioSessionId()==trustedSession)throw new IllegalStateException();DynamicsProcessing candidate=new DynamicsProcessing(0,trustedSession,null);effect=candidate;candidate.setControlStatusListener((e,control)->{if(!control)owner.handler.post(()->{if(effect==candidate)stop("effect_control_lost");});});if(!candidate.hasControl())throw new IllegalStateException();originalMix=1f;candidate.setInputGainAllChannelsTo(0f);if(candidate.setEnabled(true)!=AudioEffect.SUCCESS)throw new IllegalStateException();LogStore.log("replacement_original_muted",LogStore.map("sessionId",trustedSession,"globalVolumeChanged",false,"rampMs",FADE_MS));return true;}catch(RuntimeException e){stop("cannot_mute_original");status="Телефон не разрешил приглушить Яндекс; замена остановлена";return false;}}
 void fade(){final long token=++transition;final MediaPlayer p=player;final DynamicsProcessing fx=effect;final float initialOriginal=originalMix;fadeStarted=SystemClock.elapsedRealtime();fading=true;Runnable ramp=new Runnable(){public void run(){if(closed||token!=transition||p!=player||fx!=effect||!armed())return;try{if(!current(identityKey)){suspend("fade_source_unavailable",1000);return;}if(!owner.current.playing){pauseSource(owner.current);return;}float mix=Math.min(1f,(SystemClock.elapsedRealtime()-fadeStarted)/(float)FADE_MS);originalMix=initialOriginal*(1f-mix);fx.setInputGainAllChannelsTo(originalMix<=0.001f?-100f:(float)(20*Math.log10(originalMix)));applyVolume(mix);if(mix<1f)owner.handler.postDelayed(this,20);else{fading=false;LogStore.log("replacement_transition_complete",LogStore.map("trackId",trackId,"rampMs",SystemClock.elapsedRealtime()-fadeStarted));}}catch(RuntimeException e){suspend("fade_failed",retryDelay());}}};ramp.run();}
 void applyVolume(float mix){double gain=descriptor==null?0:descriptor.optDouble("gain_db",0);float volume=mix*(float)Math.min(1,Math.pow(10,Math.min(0,gain)/20));player.setVolume(volume,volume);if(gain>0&&loudness==null)try{loudness=new LoudnessEnhancer(player.getAudioSessionId());loudness.setTargetGain((int)Math.round(gain*100));loudness.setEnabled(true);}catch(RuntimeException ignored){LogStore.log("replacement_gain","positive gain unavailable");}}
 void unmute(){if(effect!=null){DynamicsProcessing fx=effect;effect=null;boolean gainReset=false,disabled=false,released=false;try{fx.setControlStatusListener(null);}catch(RuntimeException ignored){}try{fx.setInputGainAllChannelsTo(0f);gainReset=true;}catch(RuntimeException ignored){}try{disabled=fx.setEnabled(false)==AudioEffect.SUCCESS;}catch(RuntimeException ignored){}try{fx.release();released=true;}catch(RuntimeException ignored){}originalMix=1f;LogStore.log("replacement_original_restored",LogStore.map("reason","effect_released","gainReset",gainReset,"disabled",disabled,"released",released,"hardwareAudibilityVerified",false));}}
 void release(String reason){if("identity_changed".equals(reason)||"track_changed".equals(reason)||"replacement_end".equals(reason)||"replacement_completed".equals(reason))rememberAudio();returning=false;pausedAt=-1;boolean had=player!=null||effect!=null;transition++;ready=false;seeking=false;fading=false;aligned=false;resumePositionRetained=false;if(player!=null){try{player.setOnErrorListener(null);player.setOnPreparedListener(null);player.setOnCompletionListener(null);player.setOnSeekCompleteListener(null);player.release();}catch(RuntimeException ignored){}player=null;}if(loudness!=null){try{loudness.release();}catch(RuntimeException ignored){}loudness=null;}unmute();if(audioFile!=null){audioFile.delete();audioFile=null;}if(had)LogStore.log("replacement_released",LogStore.map("reason",reason));}
 void suspend(String reason,long delay){generation++;preparing=false;release(reason);descriptor=null;lookupKey=null;nextLookup=SystemClock.elapsedRealtime()+delay;LogStore.log("replacement_recovery",LogStore.map("reason",reason,"automaticModeRetained",armed(),"retryMs",delay));}
 void returnOriginal(){
  if(player==null||effect==null||!ready||!current(identityKey)||!owner.current.playing){stop("owner_return_original");return;}
  preloadAllowed=false;armedUntil=0;returning=true;fading=false;seeking=false;final long token=++transition;final MediaPlayer p=player;final DynamicsProcessing fx=effect;final long start=SystemClock.elapsedRealtime();final float initialOriginal=originalMix;
  status="Плавно возвращаем оригинал…";
  Runnable ramp=new Runnable(){public void run(){if(token!=transition||p!=player||fx!=effect)return;try{if(!current(identityKey)||!owner.current.playing){stop("return_source_changed");return;}float mix=Math.min(1f,(SystemClock.elapsedRealtime()-start)/(float)FADE_MS);originalMix=initialOriginal+(1f-initialOriginal)*mix;fx.setInputGainAllChannelsTo(originalMix<=0.001f?-100f:(float)(20*Math.log10(originalMix)));applyVolume(1f-mix);if(mix<1f)owner.handler.postDelayed(this,20);else stop("owner_return_original");}catch(RuntimeException ex){stop("return_failed");}}};ramp.run();
 }
 void stop(String reason){waitingForRouteResume=false;routePauseObserved=false;preloadAllowed=false;clearAudioCache();returning=false;armedUntil=0;trustedSession=-1;generation++;preparing=false;release(reason);descriptor=null;lookupKey=null;nextLookup=0;status="Замена выключена; играет оригинал";if("yandex_audio_session_changed".equals(reason)||"effect_control_lost".equals(reason))status="Яндекс сменил аудиосессию. Открой его эквалайзер → CELIKOM и снова включи автозамену";else if("headphones_disconnected".equals(reason))status="Наушники отключены. Оригинал восстановлен; подключи их и снова включи автозамену";LogStore.log("replacement_trial_stop",LogStore.map("reason",reason));}
 void close(){closed=true;stop("service_stopped");}
 void logSync(String state,PlaybackSource s,long drift){String key=state+"|"+s.key;if(!key.equals(lastSync)||Math.abs(drift)>350){lastSync=key;LogStore.log("replacement_sync",LogStore.map("state",state,"trackId",trackId,"sourcePositionMs",position(s),"driftMs",drift));}}
 static String message(String code){switch(code){case "login_required":case "invalid_session":return "нужно войти в CELIKOM";case "access_denied":case "trial_not_activated":return "нет активного доступа CELIKOM";case "invalid_credentials":return "неверная почта или пароль";case "rate_limited":return "слишком много запросов — попробуй позже";default:return code;}}
}
