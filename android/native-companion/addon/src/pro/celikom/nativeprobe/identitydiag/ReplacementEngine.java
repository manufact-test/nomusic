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
 static final long HOT_CACHED_SEEK_TIMEOUT_MS=700;
 static final long STREAM_RUNWAY_WAIT_MS=12000;
 static final long FULL_FILE_EXPERIMENT_BUDGET_MS=20000;
 final ProbeService owner; final NativeApi api;
 final boolean fullFileExperiment;
 // Explicit experimental opt-in only for the isolated CELIKOM Test service.
 // Existing two-argument local-file callers keep their frozen semantics.
 final boolean progressiveColdAllowed;
 // Test.31: use the SAME 160ms complementary crossfade in the actual APK and
 // host replay. Test.28's 32ms source duck followed by 48ms decoder rise
 // intentionally created a near-silent gap at EVERY fresh song attachment.
 // Keep the rejected exclusive mode only as an explicit diagnostic A/B case.
 boolean coldJoinExclusiveExperiment=false;
 // Test.39 experiment: original DSP remains entirely untouched until the
 // silent replacement decoder has passed the existing clock/runway gate.
 // Deliberately not enabled in stable/accepted builds.
 boolean lateSourceEffectAttachExperiment=true;
 // Test.42 is enabled only by the isolated CELIKOM Test service. The accepted
 // host replay and stable 0.3.85 never enter this experimental gain policy.
 boolean adaptiveJoinExperiment=false;
 // Test.40 production-only: require several stable silent decoder clock
 // samples before first handover. Two-argument Test.39 replay stays unchanged.
 final boolean conservativeColdJoinExperiment;
 String status="Замена выключена",identityKey,trackId,method="NONE",lookupKey;
 JSONObject descriptor; long descriptorUntil,nextLookup,preparedAt,seekStarted,seekBudget=SEEK_TIMEOUT_MS,fadeStarted,transition,pausedAt=-1;volatile long armedUntil;
 long pauseRestoreDelayMs=PAUSE_GRACE_MS,sourceBufferSince=-1,decoderInstanceSequence,decoderInstanceId;String audioSourceKind="unknown";
 final AudioOwnership audioOwner=new AudioOwnership();
 AudioOwnership.Ticket prepareTicket;
 long authorizationAccount=-1;
 final AudioContinuityMonitor continuity=new AudioContinuityMonitor();float commandedReplacementVolume;
 volatile long generation; int trustedSession=-1,failures,seekCorrections;
 final BufferRecoveryGate bufferGate=new BufferRecoveryGate();BufferedAudio streaming;boolean bufferWaiting;String streamFallbackKey;
 MediaPlayer player; DynamicsProcessing effect; LoudnessEnhancer loudness; File audioFile;
 float originalMix=1f; boolean ready,preparing,seeking,fading,aligned,returning,preloadAllowed=true,waitingForRouteResume,routePauseObserved,resumePositionRetained,resumeFadePending,seekHoldActive,sourceSeekedThisTrack,pendingStreamScrubJoin,streamSeekWaitLogged,seekRetargetPending;volatile boolean closed; boolean audioFromCache,localPrewarmAttempted,localPrewarmWarmupPending,localPrewarmAlignmentPending,localPrewarmJoinPending,deferredEffectPending; long localPrewarmWarmupStartedAt,localPrewarmWarmupPosition; String lastSync="",coldEnvelopeOwnerKey;
 // Verified local fast seeks stay inside the already-audible decoder, without
 // a second source/DSP handover. Unlike the rejected Test.65 delayed mute,
 // this path NEVER pauses or mutes either session during its fast seek.
 boolean hotCachedSeek,hotCachedSeekPending,hotCachedSeekPaused;long hotCachedSeekStarted,hotCachedSeekTarget,hotCachedSeekSequence,hotCachedSeekEpoch;int hotCachedSeekCorrections;
 final ClockSupervisor clockSupervisor=new ClockSupervisor();PlaybackSource previousSource;boolean explicitSourceSeek;long unavailableSince=-1,lastSyncAt=-1,lastLoggedDrift;String completedKey,completedReason;long completedPosition,resumeDrift;
 String joinRetryKey;int joinRetryAttempts;boolean joinRetryPreferBaseline,joinLoudnessUnavailable;
 // Private, bounded to this foreground run. Every reuse requires a new live resolve.
 /* Bounded in-session warm cache covers playlist reorder and rapid repeat selections. */
 static final long CACHE_BYTES=RecentAudioCachePolicy.MAX_BYTES;
 final LinkedHashMap<String,File> recentAudio=new LinkedHashMap<>();
 final LinkedHashSet<String> failedPrimeKeys=new LinkedHashSet<>();
 volatile long lookaheadPrefetchGeneration,lookaheadPrefetchAccount=-1,lookaheadPrefetchStartedAt;
 volatile String lookaheadPrefetchAlias,lookaheadPrefetchTrackId,lookaheadPrefetchPhase="none";
 String lookaheadPrefetchResolvedAudioKey;JSONObject lookaheadPrefetchCurrentDescriptor;boolean lookaheadPrefetchPromoted,lookaheadPrefetchWait;
 // A primed next decoder remains muted and never owns the source effect.
 // Live playback still requires a fresh current-track resolve and measured duration.
 static final long NEXT_DECODER_PRIME_TIMEOUT_MS=1800, PROMOTED_PRIME_GRACE_MS=800, PROMOTED_PRIME_READY_WAIT_MS=150, CACHED_CURRENT_PRIME_READY_WAIT_MS=340;
 static final class NextDecoderPrime {
  final String alias,trackId,audioKey;final long account;final File file;final MediaPlayer player;
  final long startedAt;final boolean currentCache;long motionOrigin;boolean ready;
  NextDecoderPrime(String alias,String trackId,String audioKey,long account,File file,MediaPlayer player,boolean currentCache){
   this.alias=alias;this.trackId=trackId;this.audioKey=audioKey;this.account=account;
   this.file=file;this.player=player;this.currentCache=currentCache;this.startedAt=SystemClock.elapsedRealtime();
  }
 }
 NextDecoderPrime primedNext;boolean lastPrimeWasCurrentCache,primeReadyWaitInFlight;long primeReadyWaitToken;
 long lookaheadPromotedAtMs;
 boolean primingNextCurrent(NextDecoderPrime c){
  PlaybackSource current=owner.current;
  boolean currentWarm=c.currentCache&&current!=null
   &&Objects.equals(current.alias,c.alias)&&Objects.equals(trackId,c.trackId)
   &&Objects.equals(identityKey,current.key);
  boolean promotedCurrent=!c.currentCache&&current!=null&&Objects.equals(current.alias,c.alias)
   &&lookaheadPrefetchPromoted
   &&(trackId==null||Objects.equals(trackId,c.trackId))
   &&(identityKey==null||Objects.equals(identityKey,current.key));
  boolean expectedNext=!c.currentCache
   &&(current==null||!Objects.equals(current.alias,c.alias))
   &&owner.lookaheadCandidateCurrent(c.alias);
  return primedNext==c&&!closed&&armed()&&api.signedIn()
   &&c.account==api.accountGeneration
   &&(currentWarm||(!c.currentCache
    &&Objects.equals(lookaheadPrefetchAlias,c.alias)
    &&Objects.equals(lookaheadPrefetchTrackId,c.trackId)
    &&(promotedCurrent||expectedNext)));
 }
 void discardPrimedNext(String reason){
  NextDecoderPrime old=primedNext;if(old==null)return;primedNext=null;
  if(Arrays.asList("prime_timeout","motion_timeout","decoder_start_error","warmup_error",
    "measured_duration_mismatch","source_session_collision","player_error").contains(reason)){
   failedPrimeKeys.add(old.audioKey);
   if(failedPrimeKeys.size()>16)failedPrimeKeys.remove(failedPrimeKeys.iterator().next());
  }
  try{old.player.setOnPreparedListener(null);old.player.setOnSeekCompleteListener(null);
    old.player.setOnErrorListener(null);old.player.setOnCompletionListener(null);
    audioOwner.discardSpeculativeNext(old.player);
  }catch(RuntimeException ignored){}
  LogStore.log(old.currentCache?"replacement_cached_current_prime_discarded":"replacement_lookahead_decoder_prime_discarded",LogStore.map(
    "mediaAlias",old.alias,"reason",reason,"sourceMuted",false));
 }
 void pollPrimedNext(NextDecoderPrime c){
  if(!primingNextCurrent(c)){if(primedNext==c)discardPrimedNext("candidate_changed");return;}
  MediaPlayer p=c.player;
  try{
   long elapsed=SystemClock.elapsedRealtime()-c.startedAt;
   if(p.getCurrentPosition()-c.motionOrigin>=40){
    audioOwner.pauseSpeculativeNext(p);p.setOnSeekCompleteListener(mp->{
     if(mp!=p||!primingNextCurrent(c)){if(primedNext==c)discardPrimedNext("seek_stale");return;}
     c.ready=true;
     LogStore.log(c.currentCache?"replacement_cached_current_prime_ready":"replacement_lookahead_decoder_prime_ready",LogStore.map(
      "mediaAlias",c.alias,"trackId",c.trackId,"elapsedMs",
      SystemClock.elapsedRealtime()-c.startedAt,"sourceMuted",false));
    });
    audioOwner.seekSpeculativeNextZero(p);return;
   }
   if(elapsed>=NEXT_DECODER_PRIME_TIMEOUT_MS){discardPrimedNext("motion_timeout");return;}
   owner.handler.postDelayed(()->pollPrimedNext(c),20);
  }catch(RuntimeException e){discardPrimedNext("warmup_error");}
 }
 void primeNextDecoder(String alias,String id,JSONObject j,File file,long account){
  primeDecoder(alias,id,audioKeyFor(id,j),j.optLong("duration_ms"),file,account,false);
 }
 void primeCachedCurrentDecoder(PlaybackSource source,String id){
  if(source==null||!armed()||!api.signedIn()||player!=null||preparing||primedNext!=null)return;
  ArrayList<Map.Entry<String,File>> entries=new ArrayList<>(recentAudio.entrySet());
  for(int i=entries.size()-1;i>=0;i--){
   Map.Entry<String,File> entry=entries.get(i);String key=entry.getKey();
   String[] parts=key.split("\\|",5);
   if(parts.length!=5||!id.equals(parts[0])||failedPrimeKeys.contains(key))continue;
   long duration;
   try{duration=Long.parseLong(parts[3]);}catch(NumberFormatException bad){continue;}
   if(!PlaybackDuration.metadataProbeAllowed(source.duration,duration))continue;
   File file=entry.getValue();if(file==null||!file.isFile())continue;
   primeDecoder(source.alias,id,key,duration,file,api.accountGeneration,true);
   return;
  }
 }
 void primeDecoder(String alias,String id,String key,long duration,File file,long account,boolean currentCache){
  if(closed||!armed()||!api.signedIn()||file==null||!file.isFile()
   ||owner.current==null)return;
  boolean eligible=currentCache?Objects.equals(owner.current.alias,alias)
    &&Objects.equals(trackId,id)&&Objects.equals(identityKey,owner.current.key)
    :owner.lookaheadCandidateCurrent(alias)&&!Objects.equals(owner.current.alias,alias);
  if(!eligible||failedPrimeKeys.contains(key))return;
  /* Keep the existing lookahead lease if the current song is not its candidate.
     Both paths stay silent until a matching fresh current resolve arrives. */
  if(currentCache&&primedNext!=null)return;
  if(!currentCache&&primedNext!=null&&primedNext.currentCache
    &&Objects.equals(primedNext.alias,owner.current.alias))return;
  discardPrimedNext("new_candidate");
  MediaPlayer p=null;
  try{
   p=new MediaPlayer();
   p.setAudioAttributes(new AudioAttributes.Builder()
    .setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
   audioOwner.silenceFutureDecoder(p);p.setDataSource(file.getAbsolutePath());
   NextDecoderPrime c=new NextDecoderPrime(alias,id,key,account,file,p,currentCache);
   primedNext=c;final MediaPlayer future=p;
   p.setOnErrorListener((mp,what,extra)->{
    if(primedNext==c)discardPrimedNext("player_error");return true;
   });
   p.setOnPreparedListener(mp->{
    if(mp!=future||!primingNextCurrent(c)){
     if(primedNext==c)discardPrimedNext("prepared_stale");return;
    }
    try{
     if(!PlaybackDuration.metadataProbeAllowed(duration,mp.getDuration())){
      discardPrimedNext("measured_duration_mismatch");return;
     }
     if(trustedSession>0&&mp.getAudioSessionId()==trustedSession){
      discardPrimedNext("source_session_collision");return;
     }
     c.motionOrigin=mp.getCurrentPosition();
     audioOwner.startSpeculativeNext(mp);
     LogStore.log(currentCache?"replacement_cached_current_prime_start":"replacement_lookahead_decoder_prime_start",LogStore.map(
      "mediaAlias",alias,"trackId",id,"sourceMuted",false,"replacementVolumeCommand",0f));
     owner.handler.postDelayed(()->pollPrimedNext(c),20);
    }catch(RuntimeException e){discardPrimedNext("decoder_start_error");}
   });p.prepareAsync();
   owner.handler.postDelayed(()->{
    if(primedNext==c&&!c.ready
       &&SystemClock.elapsedRealtime()-c.startedAt>=NEXT_DECODER_PRIME_TIMEOUT_MS)
     discardPrimedNext("prime_timeout");
   },NEXT_DECODER_PRIME_TIMEOUT_MS);
  }catch(Exception e){
   if(primedNext!=null&&primedNext.player==p)discardPrimedNext("setup_failed");
   else if(p!=null)audioOwner.discardSpeculativeNext(p);
  }
 }
 MediaPlayer takePrimedNext(String alias,String key,File file){
  NextDecoderPrime c=primedNext;if(c==null)return null;
  /* Preparing an unrelated current song must not destroy its already primed successor. */
  if(!Objects.equals(c.alias,alias))return null;
  if(!c.ready||!Objects.equals(c.audioKey,key)
   ||c.account!=api.accountGeneration||!c.file.equals(file)){
   discardPrimedNext("not_ready_or_live_key_mismatch");return null;
  }
  primedNext=null;lastPrimeWasCurrentCache=c.currentCache;
  try{c.player.setOnPreparedListener(null);c.player.setOnErrorListener(null);
   c.player.setOnSeekCompleteListener(null);c.player.setOnCompletionListener(null);
   audioOwner.adoptSpeculativeNext(c.player);
  }catch(RuntimeException e){
   audioOwner.discardSpeculativeNext(c.player);lastPrimeWasCurrentCache=false;return null;
  }
  return c.player;
 }
 String audioKey(JSONObject j){return trackId+"|"+j.optLong("replacement_id")+"|"+j.optLong("version")+"|"+j.optLong("duration_ms")+"|"+j.optString("mime_type","audio/mpeg");}
 String audioKeyFor(String id,JSONObject j){return id+"|"+j.optLong("replacement_id")+"|"+j.optLong("version")+"|"+j.optLong("duration_ms")+"|"+j.optString("mime_type","audio/mpeg");}
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
  if(adaptiveJoinExperiment&&key!=null&&current(key)&&armed()
      &&owner.current!=null&&sourceMs+4000<owner.current.duration){
   if(!Objects.equals(joinRetryKey,key)){joinRetryKey=key;joinRetryAttempts=0;}
   long retry=JoinTransitionPolicy.retryMs(++joinRetryAttempts);
   LogStore.log("replacement_join_guard_fallback",LogStore.map(
     "reason",reason,"projectedDriftMs",drift,"warmCorrections",attempts,
     "originalRetained",true,"retrySameTrack",true,"retryAttempt",joinRetryAttempts,
     "retryMs",retry,"sourcePcmMeasured",false,"phaseVerified",false));
   suspend(reason,retry);
   completedKey=null;completedReason=null;
   status="Синхронизация неустойчива — повторяем на этой песне; играет оригинал";
   return;
  }
  LogStore.log("replacement_join_guard_fallback",LogStore.map(
    "reason",reason,"projectedDriftMs",drift,"warmCorrections",attempts,
    "originalRetained",true,"sourcePcmMeasured",false,"phaseVerified",false));
  suspend(reason,30000);
  completedKey=key;completedPosition=sourceMs;
  completedReason="Синхронизация неустойчива — играет оригинал до следующей песни";
  audioOwner.unsupported(reason);status=completedReason;
 }
 /** Test.42's fade exception was discarded, then retried only after 5s.
  * Keep the original audible, retry this still-current song with a bounded
  * backoff, and use the older 160ms entry instead of repeating a failed fade. */
 void recoverFailedJoin(RuntimeException error,String stage,long duration,float lastMix){
  final String key=identityKey;
  final PlaybackSource source=owner.current;
  final long sourceMs=source==null?0:position(source);
  final boolean sameTrack=adaptiveJoinExperiment&&key!=null&&current(key)&&armed()
    &&source!=null&&sourceMs+4000<source.duration;
  final String detail=error instanceof IllegalStateException || error instanceof IllegalArgumentException
    ?error.getMessage():null;
  LogStore.log("replacement_join_exception",LogStore.map(
    "reason","fade_failed","type",error.getClass().getSimpleName(),"detail",detail,
    "stage",stage,"requestedDurationMs",duration,"lastCommandedMix",lastMix,
    "ownerState",audioOwner.state().name(),"retrySameTrack",sameTrack,
    "sourcePcmMeasured",false,"hardwareOutputMeasured",false));
  if(sameTrack){
   if(!Objects.equals(joinRetryKey,key)){joinRetryKey=key;joinRetryAttempts=0;}
   joinRetryPreferBaseline=true;
   long retry=JoinTransitionPolicy.retryMs(++joinRetryAttempts);
   LogStore.log("replacement_join_guard_fallback",LogStore.map(
     "reason","fade_failed","originalRetained",true,"retrySameTrack",true,
     "retryAttempt",joinRetryAttempts,"retryMs",retry,
     "nextJoinDurationMs",UNIFIED_JOIN_MS,"fallbackFromDurationMs",duration));
   suspend("fade_failed",retry);
   completedKey=null;completedReason=null;
   status="Ошибка перехода — повторяем на этой песне; играет оригинал";
   return;
  }
  suspend("fade_failed",retryDelay());
 }
 void clearAudioCache(){for(File f:recentAudio.values())f.delete();recentAudio.clear();failedPrimeKeys.clear();}
 void trimRecentAudio(File keep){
  long size=0;for(File f:recentAudio.values())size+=f.length();
  Iterator<Map.Entry<String,File>> it=recentAudio.entrySet().iterator();
  while(it.hasNext()&&RecentAudioCachePolicy.shouldTrim(recentAudio.size(),size)){
   Map.Entry<String,File> entry=it.next();File f=entry.getValue();
   /* Never delete a freshly cached file or the still-primed decoder's local source. */
   if(f.equals(keep)||(primedNext!=null&&f.equals(primedNext.file)))continue;
   String reason=RecentAudioCachePolicy.pressure(recentAudio.size(),size);long bytes=f.length();
   it.remove();size-=bytes;f.delete();
   LogStore.log("replacement_audio_cache_evicted",LogStore.map(
    "reason",reason,"bytes",bytes,"remainingEntries",recentAudio.size(),"remainingBytes",size,
    "primeProtected",primedNext!=null));
  }
 }
 void rememberAudio(){if(streaming!=null&&audioFile==null)audioFile=streaming.retainComplete();if(audioFile==null||descriptor==null||!ready||!api.signedIn())return;String key=audioKey(descriptor);File old=recentAudio.remove(key);if(old!=null&&!old.equals(audioFile))old.delete();recentAudio.put(key,audioFile);File kept=audioFile;audioFile=null;trimRecentAudio(kept);}
 /* A fully downloaded file survives a fast Next while its decoder is preparing.
    Reuse still requires a fresh resolve and measured duration verification. */
 void retainInterruptedCompleteFile(String reason){
  if(ready||audioFile==null||!audioFile.isFile()||descriptor==null||!api.signedIn()
   ||streaming!=null||!fullFileExperiment
   ||!("track_changed".equals(reason)||"identity_changed".equals(reason)))return;
  File retained=audioFile;
  cachePrefetchedAudio(trackId,descriptor,retained);
  audioFile=null;
  LogStore.log("replacement_interrupted_file_retained",LogStore.map(
   "trackId",trackId,"reason",reason,"bytes",retained.length(),
   "freshResolveRequired",true,"decoderValidated",false));
 }
 void noteLookaheadCandidate(String candidateAlias){
  if(lookaheadPrefetchAlias==null)return;PlaybackSource source=owner.current;
  if(source!=null&&Objects.equals(source.alias,lookaheadPrefetchAlias)){
   if(Objects.equals(identityKey,source.key)&&!Objects.equals(trackId,lookaheadPrefetchTrackId)){invalidateLookaheadPrefetch("current_identity_mismatch");return;}
   if(!lookaheadPrefetchPromoted)lookaheadPromotedAtMs=SystemClock.elapsedRealtime();
   lookaheadPrefetchPromoted=true;
   if("ready".equals(lookaheadPrefetchPhase)){lookaheadPrefetchPhase="cached";LogStore.log("replacement_lookahead_prefetch_promoted",LogStore.map("mediaAlias",lookaheadPrefetchAlias,"trackId",lookaheadPrefetchTrackId,"cacheRetained",true));}
   else LogStore.log("replacement_lookahead_prefetch_promoted_inflight",LogStore.map("mediaAlias",lookaheadPrefetchAlias,"trackId",lookaheadPrefetchTrackId,"phase",lookaheadPrefetchPhase));
   return;
  }
  if(!Objects.equals(candidateAlias,lookaheadPrefetchAlias)&&!owner.lookaheadCandidateCurrent(lookaheadPrefetchAlias))invalidateLookaheadPrefetch("next_item_changed");
 }
 void clearLookaheadPrefetchState(){
  lookaheadPrefetchGeneration++;lookaheadPrefetchAlias=null;lookaheadPrefetchTrackId=null;lookaheadPrefetchAccount=-1;
  lookaheadPrefetchPhase="none";lookaheadPrefetchResolvedAudioKey=null;lookaheadPrefetchCurrentDescriptor=null;
  lookaheadPrefetchPromoted=false;lookaheadPrefetchWait=false;lookaheadPromotedAtMs=0;
 }
 void finishLookaheadPrefetch(String reason){
  if(!"cache_consumed".equals(reason)&&primedNext!=null&&!primedNext.currentCache)discardPrimedNext("prefetch_finished_"+reason);
  if(lookaheadPrefetchAlias!=null)LogStore.log("replacement_lookahead_prefetch_finished",LogStore.map("mediaAlias",lookaheadPrefetchAlias,"trackId",lookaheadPrefetchTrackId,"reason",reason));
  clearLookaheadPrefetchState();
 }
 void invalidateLookaheadPrefetch(String reason){
  if(lookaheadPrefetchAlias==null)return;
  // An in-flight download may already be the CURRENT track's only prepare path.
  // Never discard its fresh-resolved descriptor and strand preparing=true.
  if(lookaheadPrefetchWait&&lookaheadPrefetchCurrentDescriptor!=null){
   fallbackPromotedLookaheadPrefetch("invalidated_"+reason);
   return;
  }
  LogStore.log("replacement_lookahead_prefetch_cancelled",LogStore.map("mediaAlias",lookaheadPrefetchAlias,"trackId",lookaheadPrefetchTrackId,"phase",lookaheadPrefetchPhase,"reason",reason));
  if(primedNext!=null&&!primedNext.currentCache)discardPrimedNext("prefetch_invalidated_"+reason);
  clearLookaheadPrefetchState();
 }
 boolean lookaheadPrefetchStarted(String alias){return Objects.equals(lookaheadPrefetchAlias,alias)&&("resolving".equals(lookaheadPrefetchPhase)||"downloading".equals(lookaheadPrefetchPhase)||"ready".equals(lookaheadPrefetchPhase)||"cached".equals(lookaheadPrefetchPhase));}
 String lookaheadPrefetchState(String alias){return Objects.equals(lookaheadPrefetchAlias,alias)?lookaheadPrefetchPhase:"none";}
 boolean lookaheadPrefetchCurrent(long token,long account,String alias,String id){
  if(closed||token!=lookaheadPrefetchGeneration||account!=api.accountGeneration||!api.signedIn()||!armed()||!Objects.equals(lookaheadPrefetchAlias,alias)||!Objects.equals(lookaheadPrefetchTrackId,id))return false;
  PlaybackSource source=owner.current;
  if(source!=null&&Objects.equals(source.alias,alias)&&Objects.equals(identityKey,source.key)&&!Objects.equals(trackId,id))return false;
  return owner.lookaheadCandidateCurrent(alias);
 }
 boolean waitForLookaheadPrefetch(String key,JSONObject fresh,long g){
  PlaybackSource source=owner.current;
  if(!lookaheadPrefetchPromoted||source==null||!Objects.equals(source.alias,lookaheadPrefetchAlias)
      ||!Objects.equals(identityKey,key)||!Objects.equals(trackId,lookaheadPrefetchTrackId)
      ||lookaheadPrefetchAccount!=api.accountGeneration||!armed()
      ||(!"resolving".equals(lookaheadPrefetchPhase)&&!"downloading".equals(lookaheadPrefetchPhase))
      ||g!=generation||!current(key)
      ||!PlaybackDuration.metadataProbeAllowed(source.duration,fresh.optLong("duration_ms")))return false;
  String freshKey=audioKeyFor(trackId,fresh);
  if(lookaheadPrefetchResolvedAudioKey!=null&&!freshKey.equals(lookaheadPrefetchResolvedAudioKey)){
   LogStore.log("replacement_lookahead_prefetch_key_mismatch",LogStore.map(
     "mediaAlias",lookaheadPrefetchAlias,"trackId",trackId,"freshResolveKeyMatches",false,
     "action","cancel_prefetch_use_fresh_download"));
   invalidateLookaheadPrefetch("fresh_resolve_key_mismatch");return false;
  }
  audioOwner.preparing();
  prepareTicket=audioOwner.ticket(key,api.accountGeneration,fresh.optLong("replacement_id"),
    fresh.optLong("version"),fresh.optLong("duration_ms"));
  preparing=true;audioFromCache=false;status="Готовим замену заранее; оригинал продолжает играть";
  lookaheadPrefetchCurrentDescriptor=fresh;lookaheadPrefetchWait=true;
  // A stalled prefetch must not leave the current song in PREPARING indefinitely.
  // The frozen local-file experiment keeps its exact original 10s policy;
  // only the Test.25 opt-in yields early to verified sparse preparation.
  final long handoffWaitMs=progressiveColdAllowed?1200:10000;
  final String waitAlias=source.alias;
  owner.handler.postDelayed(()->{
   if(!closed&&g==generation&&lookaheadPrefetchWait
      &&Objects.equals(waitAlias,lookaheadPrefetchAlias)&&Objects.equals(identityKey,key)&&current(key))
    fallbackPromotedLookaheadPrefetch("current_handoff_timeout");
  },handoffWaitMs);
  LogStore.log("replacement_lookahead_prefetch_current_wait",LogStore.map(
    "mediaAlias",lookaheadPrefetchAlias,"trackId",trackId,"phase",lookaheadPrefetchPhase,
    "freshResolveRequired",true,"audioKeyMatches",lookaheadPrefetchResolvedAudioKey==null?"pending":true,
    "originalRemainsAudible",true,"waitBudgetMs",handoffWaitMs));
  return true;
 }
 void prepareWithLookaheadPrefetch(String key,JSONObject fresh,long g){
  if(preparing||!current(key)||!api.signedIn())return;
  // A fresh current resolve is the final authority: revoke any speculative
  // decoder from a different replacement edition before another download.
  NextDecoderPrime speculative=primedNext;
  if(speculative!=null&&owner.current!=null
   &&Objects.equals(owner.current.alias,speculative.alias)
   &&!Objects.equals(audioKeyFor(trackId,fresh),speculative.audioKey))
   discardPrimedNext("fresh_current_audio_key_mismatch");
  if(waitForLookaheadPrefetch(key,fresh,g))return;
  if(waitForPromotedPrimeReady(key,fresh,g))return;
  prepare(key,fresh,g);
 }
 boolean waitForPromotedPrimeReady(String key,JSONObject fresh,long g){
  NextDecoderPrime c=primedNext;
  PlaybackSource source=owner.current;
  if(c==null||c.ready||source==null
      ||!Objects.equals(c.alias,source.alias)
      ||!Objects.equals(c.trackId,trackId)
      ||!Objects.equals(c.audioKey,audioKeyFor(trackId,fresh))
      ||c.account!=api.accountGeneration
      ||!c.file.equals(recentAudio.get(c.audioKey))
      ||!primingNextCurrent(c))return false;
  /* One in-flight wait per current decoder: repeated source samples must not
     queue duplicate prepare/download callbacks after a single fresh resolve. */
  if(primeReadyWaitInFlight)return true;
  primeReadyWaitInFlight=true;
  final long waitToken=++primeReadyWaitToken;
  final long started=SystemClock.elapsedRealtime();
  final long waitBudgetMs=c.currentCache?CACHED_CURRENT_PRIME_READY_WAIT_MS:PROMOTED_PRIME_READY_WAIT_MS;
  LogStore.log(c.currentCache?"replacement_cached_current_prime_live_wait":"replacement_lookahead_decoder_prime_live_wait",LogStore.map(
    "mediaAlias",c.alias,"trackId",c.trackId,"waitBudgetMs",waitBudgetMs,
    "freshResolveVerified",true,"sourceMuted",false));
  owner.handler.postDelayed(new Runnable(){public void run(){
    if(waitToken!=primeReadyWaitToken)return;
    if(g!=generation||!current(key)||!api.signedIn()||preparing||player!=null){
     primeReadyWaitInFlight=false;return;
    }
    if(primedNext==c&&!c.ready
       &&SystemClock.elapsedRealtime()-started<waitBudgetMs){
      owner.handler.postDelayed(this,20);return;
    }
    primeReadyWaitInFlight=false;
    LogStore.log(c.currentCache?"replacement_cached_current_prime_live_wait_done":"replacement_lookahead_decoder_prime_live_wait_done",LogStore.map(
      "mediaAlias",c.alias,"ready",primedNext==c&&c.ready,
      "elapsedMs",SystemClock.elapsedRealtime()-started));
    prepare(key,fresh,g);
  }},20);
  return true;
 }
 void fallbackPromotedLookaheadPrefetch(String reason){
  if(!lookaheadPrefetchWait||lookaheadPrefetchCurrentDescriptor==null)return;
  JSONObject fresh=lookaheadPrefetchCurrentDescriptor;String key=identityKey;long g=generation;String alias=lookaheadPrefetchAlias;
  lookaheadPrefetchWait=false;lookaheadPrefetchCurrentDescriptor=null;lookaheadPrefetchPromoted=false;
  LogStore.log("replacement_lookahead_prefetch_current_fallback",LogStore.map("mediaAlias",alias,"trackId",trackId,"reason",reason,"action",progressiveColdAllowed?"fresh_verified_sparse_start":"fresh_descriptor_full_download"));
  invalidateLookaheadPrefetch(reason);
  if(preparing&&g==generation&&current(key)){
   if(progressiveColdAllowed){preparing=false;prepare(key,fresh,g);}
   else downloadFull(key,fresh,g);
  }
 }
 void resumePromotedLookaheadPrefetch(){
  if(!lookaheadPrefetchWait||lookaheadPrefetchCurrentDescriptor==null)return;PlaybackSource source=owner.current;
  if(source==null||!Objects.equals(source.alias,lookaheadPrefetchAlias)||!Objects.equals(identityKey,source.key)||!Objects.equals(trackId,lookaheadPrefetchTrackId))return;
  JSONObject fresh=lookaheadPrefetchCurrentDescriptor;String expected=audioKeyFor(trackId,fresh);
  if(!Objects.equals(expected,lookaheadPrefetchResolvedAudioKey)){fallbackPromotedLookaheadPrefetch("resolved_key_mismatch");return;}
  String key=identityKey;long g=generation;lookaheadPrefetchWait=false;lookaheadPrefetchCurrentDescriptor=null;
  LogStore.log("replacement_lookahead_prefetch_current_ready",LogStore.map("mediaAlias",source.alias,"trackId",trackId,"audioKeyMatches",true,"cacheReady",true,"sourceItemGeneration",owner.sourceItemGeneration));
  preparing=false;prepare(key,fresh,g);
 }
 void prefetchLookahead(Map<String,Object> observation,String id){
  if(closed||!armed()||!preloadAllowed||!api.signedIn()||observation==null)return;
  String alias=String.valueOf(observation.get("mediaAlias"));PlaybackSource source=owner.current;
  // A late album/lookahead callback can refer to the song that is ALREADY
  // current after a manual Next. In progressive mode its verified sparse
  // current-track preparation is faster than starting a speculative FULL-file
  // download, waiting 1200ms, cancelling it and then preparing from scratch.
  // Preserve the frozen full-file prefetch/handoff behavior and all real NEXT
  // candidates (whose aliases differ from the live source).
  if(progressiveColdAllowed&&source!=null&&Objects.equals(source.alias,alias)){
   LogStore.log("replacement_lookahead_prefetch_skipped",LogStore.map(
     "mediaAlias",alias,"trackIdPresent",id!=null,"reason","already_current_progressive_prepare",
     "currentTrackUsesFreshResolve",true,"audioCommandSent",false));
   return;
  }
  long duration=observation.get("durationMs") instanceof Number?((Number)observation.get("durationMs")).longValue():-1;
  long remaining=source==null?-1:Math.max(0,source.duration-position(source));
  boolean unique=id!=null&&id.matches("[1-9][0-9]{0,23}");
  boolean eligible=LookaheadPrefetchPolicy.mayPrefetch(armed(),api.signedIn(),source!=null&&source.playing,owner.lookaheadCandidateCurrent(alias),unique,remaining);
  if(!eligible){LogStore.log("replacement_lookahead_prefetch_skipped",LogStore.map("mediaAlias",alias,"trackIdPresent",unique,"sourcePlaying",source!=null&&source.playing,"remainingMs",remaining,"candidateCurrent",owner.lookaheadCandidateCurrent(alias),"reason","prefetch_gate"));return;}
  if(Objects.equals(lookaheadPrefetchAlias,alias)&&Objects.equals(lookaheadPrefetchTrackId,id)&&lookaheadPrefetchAccount==api.accountGeneration&&("resolving".equals(lookaheadPrefetchPhase)||"downloading".equals(lookaheadPrefetchPhase)||"ready".equals(lookaheadPrefetchPhase)||"cached".equals(lookaheadPrefetchPhase)))return;
  if(lookaheadPrefetchWait&&lookaheadPrefetchCurrentDescriptor!=null){
   // One prefetch slot: let the promoted current file finish before reserving
   // it for a further next song. Re-check identity after a short delay.
   LogStore.log("replacement_lookahead_prefetch_deferred",LogStore.map(
     "mediaAlias",alias,"currentAlias",lookaheadPrefetchAlias,
     "reason","current_track_handoff_inflight","audioCommandSent",false));
   final Map<String,Object> retryObservation=new LinkedHashMap<>(observation);
   owner.handler.postDelayed(()->{
    if(!closed&&owner.lookaheadIsNext(alias))prefetchLookahead(retryObservation,id);
   },1000);
   return;
  }
  /* Keep a promoted ready decoder alive briefly for the fresh current-track resolve.
     A new successor is retried shortly; the bound prevents starving rapid Next. */
  if(lookaheadPrefetchPromoted&&"cached".equals(lookaheadPrefetchPhase)
   &&source!=null&&Objects.equals(source.alias,lookaheadPrefetchAlias)
   &&primedNext!=null&&primedNext.ready
   &&Objects.equals(primedNext.alias,source.alias)
   &&Objects.equals(primedNext.trackId,lookaheadPrefetchTrackId)
   &&SystemClock.elapsedRealtime()-lookaheadPromotedAtMs<PROMOTED_PRIME_GRACE_MS){
   LogStore.log("replacement_lookahead_prefetch_deferred",LogStore.map(
    "mediaAlias",alias,"currentAlias",source.alias,
    "reason","promoted_primed_decoder_current_handoff","audioCommandSent",false));
   final Map<String,Object> retryObservation=new LinkedHashMap<>(observation);
   owner.handler.postDelayed(()->{
    if(!closed&&owner.lookaheadIsNext(alias))prefetchLookahead(retryObservation,id);
   },200);
   return;
  }
  invalidateLookaheadPrefetch("new_next_item");
  final long token=++lookaheadPrefetchGeneration,account=api.accountGeneration,start=SystemClock.elapsedRealtime();
  lookaheadPrefetchAlias=alias;lookaheadPrefetchTrackId=id;lookaheadPrefetchAccount=account;lookaheadPrefetchStartedAt=start;lookaheadPrefetchPhase="resolving";
  lookaheadPrefetchResolvedAudioKey=null;lookaheadPrefetchCurrentDescriptor=null;lookaheadPrefetchPromoted=false;lookaheadPrefetchWait=false;
  LogStore.log("replacement_lookahead_prefetch_start",LogStore.map("mediaAlias",alias,"trackId",id,"sourceDurationMs",duration,"remainingMs",remaining,"sourceItemGeneration",owner.sourceItemGeneration,"sourceEventSequence",owner.sourceEventSequence,"audioCommandSent",false));
  api.resolve(id,()->lookaheadPrefetchCurrent(token,account,alias,id),(j,error)->{
   if(!lookaheadPrefetchCurrent(token,account,alias,id)){LogStore.log("replacement_lookahead_prefetch_stale",LogStore.map("mediaAlias",alias,"stage","resolve"));return;}
   if(error!=null){lookaheadPrefetchPhase="failed";LogStore.log("replacement_lookahead_prefetch_failure",LogStore.map("mediaAlias",alias,"stage","resolve","errorCode",error));fallbackPromotedLookaheadPrefetch("resolve_failed");return;}
   if(j==null||!j.optBoolean("found",false)){lookaheadPrefetchPhase="not_found";LogStore.log("replacement_lookahead_prefetch_not_found",LogStore.map("mediaAlias",alias,"trackId",id));fallbackPromotedLookaheadPrefetch("not_found");return;}
   long replacementDuration=j.optLong("duration_ms");
   if(!PlaybackDuration.metadataProbeAllowed(duration,replacementDuration)){lookaheadPrefetchPhase="duration_rejected";LogStore.log("replacement_lookahead_prefetch_rejected",LogStore.map("mediaAlias",alias,"sourceDurationMs",duration,"replacementDurationMs",replacementDuration));fallbackPromotedLookaheadPrefetch("duration_rejected");return;}
   lookaheadPrefetchResolvedAudioKey=audioKeyFor(id,j);
   if(lookaheadPrefetchWait&&lookaheadPrefetchCurrentDescriptor!=null&&!lookaheadPrefetchResolvedAudioKey.equals(audioKeyFor(id,lookaheadPrefetchCurrentDescriptor))){fallbackPromotedLookaheadPrefetch("fresh_resolve_key_mismatch");return;}
   /* A fresh entitlement/edition resolve may reuse an already complete local file.
      Re-downloading the same next song competes with the current serial audio lane. */
   File alreadyCached=recentAudio.get(lookaheadPrefetchResolvedAudioKey);
   if(alreadyCached!=null&&!alreadyCached.isFile()){recentAudio.remove(lookaheadPrefetchResolvedAudioKey);alreadyCached=null;}
   if(alreadyCached!=null){
    lookaheadPrefetchPhase="ready";
    primeNextDecoder(alias,id,j,alreadyCached,account);
    LogStore.log("replacement_lookahead_cache_reused",LogStore.map(
     "mediaAlias",alias,"trackId",id,"freshResolveRequired",true,
     "audioKeyMatches",true,"bytes",alreadyCached.length(),"newDownload",false));
    resumePromotedLookaheadPrefetch();
    return;
   }
   lookaheadPrefetchPhase="downloading";
   api.downloadLookahead(j,()->lookaheadPrefetchCurrent(token,account,alias,id),(file,downloadError)->{
    if(!lookaheadPrefetchCurrent(token,account,alias,id)){if(file!=null)file.delete();LogStore.log("replacement_lookahead_prefetch_stale",LogStore.map("mediaAlias",alias,"stage","download","fileDeleted",file!=null));return;}
    if(file==null){lookaheadPrefetchPhase="failed";LogStore.log("replacement_lookahead_prefetch_failure",LogStore.map("mediaAlias",alias,"stage","download","errorCode",downloadError));fallbackPromotedLookaheadPrefetch("download_failed");return;}
    cachePrefetchedAudio(id,j,file);lookaheadPrefetchPhase="ready";primeNextDecoder(alias,id,j,file,account);
    LogStore.log("replacement_lookahead_prefetch_ready",LogStore.map("mediaAlias",alias,"trackId",id,"bytes",file.length(),"elapsedMs",SystemClock.elapsedRealtime()-start,"remainingMsAtStart",remaining,"audioCommandSent",false));
    resumePromotedLookaheadPrefetch();
   });
  });
 }
 void cachePrefetchedAudio(String id,JSONObject j,File file){
  if(file==null||!file.isFile())return;String key=audioKeyFor(id,j);File old=recentAudio.remove(key);if(old!=null&&!old.equals(file))old.delete();recentAudio.put(key,file);
  trimRecentAudio(file);
 }


 // Keep the frozen local-file default for regression callers. The isolated
 // Test.25 service opts into progressive cold preparation explicitly.
 ReplacementEngine(ProbeService owner){this(owner,true);}
 ReplacementEngine(ProbeService owner,boolean fullFileExperiment){this(owner,fullFileExperiment,false);}
 ReplacementEngine(ProbeService owner,boolean fullFileExperiment,boolean progressiveColdAllowed){this(owner,fullFileExperiment,progressiveColdAllowed,false);}
 ReplacementEngine(ProbeService owner,boolean fullFileExperiment,boolean progressiveColdAllowed,boolean conservativeColdJoinExperiment){this.owner=owner;api=NativeApi.get(owner);this.fullFileExperiment=fullFileExperiment;this.progressiveColdAllowed=progressiveColdAllowed;this.conservativeColdJoinExperiment=conservativeColdJoinExperiment;}
 AudioOwnership.SeekContext seekContext(){return new AudioOwnership.SeekContext(
  owner.sourceEventSequence,owner.sourceItemGeneration,generation,decoderInstanceId,
  audioOwner.epoch(),audioOwner.operationEpoch(),audioSourceKind,localPrewarmAttempted);}
 Map<String,Object> traceFields(){return LogStore.map(
  "sourceEventSequence",owner.sourceEventSequence,"sourceItemGeneration",owner.sourceItemGeneration,
  "replacementGeneration",generation,"decoderInstanceId",decoderInstanceId,
  "audioSourceKind",audioSourceKind,"localPrewarmAttempted",localPrewarmAttempted,
  "ownerGeneration",audioOwner.epoch(),"ownerOperationEpoch",audioOwner.operationEpoch());}
 void logTrace(String event,Map<String,Object> fields){
  Map<String,Object> trace=traceFields();
  for(Map.Entry<String,Object> entry:trace.entrySet())if(!fields.containsKey(entry.getKey()))fields.put(entry.getKey(),entry.getValue());
  LogStore.log(event,fields);
 }
 static Integer verifiedSession(Context c){try{Class<?> store=Class.forName("pro.celikom.nativeprobe.ProbeStore");Object instance=store.getField("INSTANCE").get(null);if(!Boolean.TRUE.equals(store.getMethod("enabled",Context.class).invoke(instance,c)))return null;JSONObject report=(JSONObject)store.getMethod("report",Context.class).invoke(instance,c);Class<?> cls=Class.forName("pro.celikom.nativeprobe.AttenuationService");Object companion=cls.getField("Companion").get(null);return (Integer)companion.getClass().getMethod("verifiedSession",JSONObject.class,long.class).invoke(companion,report,System.currentTimeMillis());}catch(Exception e){return null;}}
 void arm(){if(closed)return;if(returning)stop("rearm_during_return");if(authorizationAccount>=0&&authorizationAccount!=api.accountGeneration)stop("account_changed");if(!api.signedIn()){status="Сначала войди в свой аккаунт CELIKOM";return;}
  authorizationAccount=api.accountGeneration;audioOwner.activate();if(identityKey!=null)audioOwner.track(identityKey);Integer session=verifiedSession(owner);
  if(session!=null&&session>0){if(trustedSession>0&&trustedSession!=session){generation++;preparing=false;release("session_rearmed");descriptor=null;lookupKey=null;}trustedSession=session;}
  preloadAllowed=true;armedUntil=Long.MAX_VALUE;
  status=trustedSession>0?"Автозамена включена":"Открой эквалайзер Яндекс Музыки и выбери CELIKOM";
  LogStore.log("replacement_arm_state",owner.runtimeSnapshot("replacement_armed"));LogStore.log("replacement_trial_start",LogStore.map("durationLimited",false,"verifiedAudioSession",trustedSession,"waitingForVerifiedSession",trustedSession<=0,"automaticNextTracks",true,"preparedBeforeArm",ready));update(owner.current);
 }
 void attachPendingSession(){if(!armed()||trustedSession>0)return;Integer session=verifiedSession(owner);if(session!=null&&session>0){trustedSession=session;status="Подключение получено; автозамена включена";LogStore.log("replacement_session_attached",LogStore.map("sessionId",session,"source","verified_yandex_panel"));}}
 void headphonesDisconnected(){
  if(!armed()&&!returning&&effect==null)return;
  boolean interruptedLocalPrewarm=localPrewarmWarmupPending||localPrewarmAlignmentPending;
  if(interruptedLocalPrewarm)localPrewarmAttempted=false;
  localPrewarmWarmupPending=false;localPrewarmAlignmentPending=false;localPrewarmJoinPending=false;
  if(returning){stop("headphones_disconnected_during_return");return;}
  resumePositionRetained=player!=null&&ready&&aligned&&!seeking;waitingForRouteResume=true;routePauseObserved=false;transition++;fading=false;aligned=false;pausedAt=-1;audioOwner.event(AudioOwnership.Event.ROUTE_LOSS);
  try{if(player!=null&&ready){setAuditedVolume(player,0f);audioOwner.pauseDecoder(player);}}catch(RuntimeException ex){suspend("route_pause_failed",0);}
  unmute();
  status="Наушники отключены. Пауза; нажми ▶ в Яндексе, чтобы продолжить с автозаменой";
  LogStore.log("replacement_route_pause",LogStore.map("automaticModeRetained",armed(),"preparedAudioRetained",ready,"sessionId",trustedSession));
  owner.pauseForRouteLoss();
 }
 /* A unique catalogue track ID is a candidate for a live server resolve.
    The backend's approved replacement response authorizes playback; the
    bounded measured-duration check remains an independent safety gate. */
 boolean verifiedDurationIdentity(){return trackId!=null&& !"NONE".equals(method);}
 void identity(Map<String,Object> o,Map<String,Object> decision){String key=PlaybackSource.key(String.valueOf(o.get("mediaAlias")),o.get("albumId"),String.valueOf(o.get("title")),String.valueOf(o.get("artist")),((Number)o.get("durationMs")).longValue());PlaybackSource s=owner.current;if(s==null||!s.key.equals(key))return;String id=(String)decision.get("candidateTrackId");String nextMethod=String.valueOf(decision.get("method"));if(!Objects.equals(identityKey,key)||!Objects.equals(trackId,id)){completedKey=null;completedReason=null;joinRetryKey=null;joinRetryAttempts=0;clockSupervisor.reset();generation++;preparing=false;release("identity_changed");audioOwner.track(key);sourceSeekedThisTrack=false;nextLookup=0;failures=0;descriptor=null;lookupKey=null;}identityKey=key;trackId=id;method=nextMethod;if(lookaheadPrefetchAlias!=null&&Objects.equals(s.alias,lookaheadPrefetchAlias)){if(id!=null&&Objects.equals(id,lookaheadPrefetchTrackId)){if(!lookaheadPrefetchPromoted)lookaheadPromotedAtMs=SystemClock.elapsedRealtime();lookaheadPrefetchPromoted=true;}else invalidateLookaheadPrefetch("current_identity_mismatch");}if(id==null){status="Песня пока не определена однозначно; играет оригинал";return;}primeCachedCurrentDecoder(s,id);update(s);}
 boolean current(String key){PlaybackSource s=owner.current;return !closed&&owner.alive()&&s!=null&&ApiContract.current(key,s.key,SystemClock.elapsedRealtime()-s.observed,s.connected);}
 /* Transport data belongs to a verified track/account generation, not to a
    transient Media3 connection snapshot. Source output still requires current(). */
 boolean transportLeaseCurrent(String key,long g,long account){return !closed&&owner.alive()&&g==generation&&account==api.accountGeneration&&api.signedIn()&&Objects.equals(identityKey,key);}
 boolean armed(){return !closed&&armedUntil!=0;}
 long position(PlaybackSource s){long extra=s.playing?Math.max(0,SystemClock.elapsedRealtime()-s.observed):0;return Math.min(s.duration,Math.max(0,s.position+extra));}
 void prewarmLocalFileForInitialAlignment(PlaybackSource s,boolean resumed,boolean sourceJump){
  if(localPrewarmAttempted||localPrewarmWarmupPending||localPrewarmAlignmentPending||localPrewarmJoinPending
     ||streaming!=null||audioFile==null||player==null||!ready
     ||!armed()||trustedSession<=0||s==null||!s.playing||player.isPlaying()
     ||resumePositionRetained||waitingForRouteResume||sourceJump
     ||explicitSourceSeek||seeking||aligned||fading||audioOwner.handoverAwaitingClock())return;
  boolean defer=lateSourceEffectAttachExperiment&&!resumed&&!sourceJump
    &&effect==null&&!routePauseObserved&&!resumePositionRetained
    &&!sourceSeekedThisTrack&&!pendingStreamScrubJoin;
  if(!defer&&!mute())return;
  localPrewarmAttempted=true;localPrewarmWarmupPending=true;
  localPrewarmWarmupStartedAt=SystemClock.elapsedRealtime();
  localPrewarmWarmupPosition=player.getCurrentPosition();
  setAuditedVolume(player,0f);
  if(defer){
   audioOwner.startMutedDecoderBeforeEffect(player,identityKey,audioOwner.epoch());
   deferredEffectPending=true;
   LogStore.log("replacement_source_effect_deferred",LogStore.map(
     "trackId",trackId,"sourceSessionId",trustedSession,
     "phase","local_decoder_prewarm","originalUntouched",true));
  }else audioOwner.startDecoder(player,effect,identityKey,audioOwner.epoch());
  traceAudioCommands();
  logTrace("replacement_local_decoder_prewarm_start",LogStore.map(
    "trackId",trackId,"sourceKind",audioSourceKind,"cacheHit",audioFromCache,
    "decoderRecreated",true,"decoderPositionMs",localPrewarmWarmupPosition,
    "sourcePositionMs",position(s),"replacementMuted",commandedReplacementVolume<=0.001f,
    "originalAudible",originalMix>=0.999f,"prewarmBeforeAlignmentSeek",true));
 }
 boolean awaitLocalPrewarmMotion(PlaybackSource s,boolean resumed,boolean sourceJump){
  if(!localPrewarmWarmupPending)return false;
  if(sourceJump||explicitSourceSeek||waitingForRouteResume||s==null||!s.playing){
   localPrewarmWarmupPending=false;
   return false;
  }
  long now=SystemClock.elapsedRealtime(),decoderPosition=player==null?localPrewarmWarmupPosition:player.getCurrentPosition();
  long moved=decoderPosition-localPrewarmWarmupPosition;
  if(moved>=40){
   localPrewarmWarmupPending=false;localPrewarmAlignmentPending=true;
   logTrace("replacement_local_decoder_prewarm_motion",LogStore.map(
     "trackId",trackId,"movedMs",moved,"waitMs",now-localPrewarmWarmupStartedAt,
     "sourcePositionMs",position(s),"decoderPositionMs",decoderPosition,
     "originalAudible",originalMix>=0.999f,"replacementMuted",commandedReplacementVolume<=0.001f));
   return false;
  }
  if(now-localPrewarmWarmupStartedAt>=SEEK_TIMEOUT_MS){
   localPrewarmWarmupPending=false;
   skipUnstableJoin("local_decoder_prewarm_timeout",position(s)-decoderPosition,0);
   return true;
  }
  final MediaPlayer expected=player;final long epoch=generation;final String key=identityKey;
  owner.handler.postDelayed(()->{if(player==expected&&generation==epoch&&current(key)&&localPrewarmWarmupPending)update(owner.current);},20);
  return true;
 }
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
   if(hotCachedSeek){suspend("hot_cached_seek_source_lost",1000);return;}
   long now=SystemClock.elapsedRealtime();if(unavailableSince<0){unavailableSince=now;transition++;fading=false;seeking=false;resumePositionRetained=ready&&aligned;aligned=false;try{if(player!=null&&ready){setAuditedVolume(player,0f);audioOwner.pauseDecoder(player);}}catch(RuntimeException ignored){}unmute();LogStore.log("replacement_source_wait",LogStore.map("decoderRetained",player!=null&&ready,"graceMs",1500));}
    if(streaming!=null)streaming.releasePrefetchAfterSeek();
    if(now-unavailableSince>=1500&&(player!=null||preparing||lookupKey!=null))suspend("source_unavailable",1000);status="Ожидаем подключение к Яндексу; играет оригинал";return;
  }
  unavailableSince=-1;
  boolean sourceJump=explicitSourceSeek;PlaybackSource previous=previousSource;previousSource=s;
  if(previous!=null&&previous.key.equals(s.key)&&previous.playing&&s.playing&&s!=previous&&s.observed>=previous.observed&&Math.abs(s.position-(previous.position+s.observed-previous.observed))>900)sourceJump=true;
  if(sourceJump){explicitSourceSeek=true;sourceSeekedThisTrack=true;}
  if(sourceJump&&seeking&&audioOwner.seekInFlight(player))
   supersedePendingAlignmentForSourceSeek("source_position_jump");
  if(completedKey!=null&&completedKey.equals(s.key)){
   if(s.playing&&s.position<completedPosition-1500){completedKey=null;completedReason=null;lookupKey=null;descriptor=null;nextLookup=0;LogStore.log("replacement_repeat_detected",LogStore.map("sourcePositionMs",s.position));}
   else{status=completedReason==null?"Ожидаем следующую песню; играет оригинал":completedReason;return;}
  }
  if(waitingForRouteResume){if(!s.playing){routePauseObserved=true;status="Наушники отключены. Нажми ▶ в Яндексе для продолжения";return;}if(!routePauseObserved){status="Ждём паузу Яндекса после отключения наушников";return;}waitingForRouteResume=false;pausedAt=-1;aligned=false;LogStore.log("replacement_route_resume",LogStore.map("sessionId",trustedSession,"sourcePlaying",true));}
  if(!s.key.equals(identityKey)){if(player!=null||preparing){generation++;preparing=false;release("track_changed");descriptor=null;lookupKey=null;}return;}
  if(trackId==null||"NONE".equals(method)||(!armed()&&!preloadAllowed))return;
  if(!api.signedIn()){clearAudioCache();if(player!=null||preparing)suspend("login_required",0);status="ID найден; войди в CELIKOM для проверки замены";return;}
  if(!Float.isFinite(s.speed)||Math.abs(s.speed-1f)>0.01f){if(player!=null||preparing)suspend("unsupported_speed",1000);status="Для замены нужна скорость 1×; играет оригинал";return;}
  long clock=SystemClock.elapsedRealtime();
  if(ready&&!armed()&&clock-preparedAt>PREPARED_MS){generation++;release("prepared_expired");descriptor=null;lookupKey=null;}
  if(!identityKey.equals(lookupKey)){if(clock<nextLookup)return;lookupKey=identityKey;if(authorizationAccount<0)authorizationAccount=api.accountGeneration;final String key=identityKey,id=trackId;final long g=generation,account=api.accountGeneration;status="Проверяем замену на сервере…";api.resolve(id,()->!closed&&g==generation&&account==api.accountGeneration&&api.signedIn()&&current(key),(j,error)->{if(closed||g!=generation||account!=api.accountGeneration)return;if(!current(key)){if(Objects.equals(lookupKey,key)){lookupKey=null;descriptor=null;nextLookup=SystemClock.elapsedRealtime()+1000;status="Ожидаем актуальное состояние Яндекс Музыки";LogStore.log("replacement_lookup_deferred",LogStore.map("reason","source_not_current","retryMs",1000));}return;}if(error!=null){LogStore.log("replacement_resolve",LogStore.map("trackId",id,"errorCode",error));boolean denied=Arrays.asList("invalid_session","access_denied","login_required","unauthorized","trial_not_activated").contains(error);if(denied)clearAudioCache();if(!denied){lookupKey=null;nextLookup=SystemClock.elapsedRealtime()+retryDelay();}status="Сервер: "+message(error)+"; играет оригинал";return;}descriptor=j;descriptorUntil=SystemClock.elapsedRealtime()+15000;boolean found=j.optBoolean("found",false);status=found?"Замена найдена; готовим заранее":"В каталоге CELIKOM этой замены нет; играет оригинал";LogStore.log("replacement_resolve",LogStore.map("trackId",id,"found",found,"replacementId",j.optLong("replacement_id"),"durationMs",j.optLong("duration_ms")));if(found)prepareWithLookaheadPrefetch(key,j,g);});return;}
  if(descriptor!=null&&descriptor.optBoolean("found")&&player==null&&!preparing){if(clock>descriptorUntil){lookupKey=null;descriptor=null;return;}prepareWithLookaheadPrefetch(identityKey,descriptor,generation);}
  if(player==null||!ready||!armed())return;
  if(trustedSession<=0){status="Автозамена ожидает подключения: открой эквалайзер Яндекса → CELIKOM один раз";return;}
  try{
   if(!s.playing){
    if(hotCachedSeek){
     // HONOR emits a transient !playing sample in the middle of a scrub.
     // Immediately pause/silence the decoder, but retain the *same* player
     // until its untagged seek callback drains. Retiring on this sample made
     // every otherwise-fast scrub pay for a complete decoder reconnection.
     hotCachedSeekPaused=true;
     pauseSource(s,s.buffering&&s.wantsToPlay);return;
    }
    // Pause clears transient drift evidence without re-arming a consumed
    // one-per-song correction allowance. Track/Stop still perform full reset.
    clockSupervisor.onSeek();
    if(s.buffering&&s.wantsToPlay)bufferSource(s,sourceJump);
    else{sourceBufferSince=-1;pauseSource(s,false);}
    return;
   }
   if(sourceBufferSince>=0){
    logTrace("replacement_source_buffer_resumed",LogStore.map("trackId",trackId,"bufferMs",clock-sourceBufferSince,"decoderRetained",player!=null&&ready));
    sourceBufferSince=-1;
   }
   boolean resumed=pausedAt>=0;long pausedDuration=resumed?Math.max(0,clock-pausedAt):0;
   if(resumed){audioOwner.event(AudioOwnership.Event.RESUME);audioOwner.cancelPause();resumeFadePending=true;LogStore.log("replacement_resume_fast",LogStore.map("retainedOriginalEffect",effect!=null,"pauseDurationMs",pausedDuration));}
   pausedAt=-1;
   if(streaming!=null&&streaming.closed){suspend("stream_interrupted",1000);return;}
   if(hotCachedSeek){
    if(sourceJump)hotCachedSeekPending=true;
    status="Перематываем готовую версию внутри проигрывателя CELIKOM";
    return;
   }
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
    logTrace("replacement_stream_seek_data_wait",LogStore.map(
      "trackId",trackId,"cachedBytes",streaming.cachedBytes(),
      "sourceEffectRetained",effect!=null&&originalMix>=0.999f,
      "replacementSilent",commandedReplacementVolume<=0.001f,
      "seekInFlight",audioOwner.seekInFlight(player),"seekSeq",audioOwner.inFlightSequence(player),
      "seekKind",audioOwner.inFlightKind(player),"seekTargetMs",audioOwner.inFlightTargetMs(player),
      "seekElapsedMs",audioOwner.inFlightElapsedMs(player,clock)));
   }
   if(streaming!=null&&bufferGate.recover(waiting,aligned&&!bufferWaiting,seeking,player.getCurrentPosition(),clock)){
    // Once a sparse decoder has actually owned the sound, a stalled stream
    // is not eligible for another speculative immediate re-grant. Fetch a
    // verified full file on the next attempt with the original audible.
    if(originalMix<=0.001f&&audioOwner.state()==AudioOwnership.State.REPLACEMENT){
     LogStore.log("replacement_stream_starvation",LogStore.map("trackId",trackId,
       "cachedBytes",streaming.cachedBytes(),"action","full_file_retry_no_sparse_rejoin"));
     streamFallbackKey=identityKey;suspend("stream_starved_after_grant",1000);return;
    }
    if(!bufferWaiting){
     bufferWaiting=true;transition++;fading=false;aligned=false;seeking=false;
     resumePositionRetained=false;setAuditedVolume(player,0f);
     audioOwner.pauseDecoder(player);streaming.releasePrefetchAfterSeek();unmute();
     LogStore.log("replacement_buffer_wait",LogStore.map("trackId",trackId,
       "cachedBytes",streaming.cachedBytes(),"originalAudible",true));
    }
    status="Готовим непрерывный буфер; играет оригинал";return;
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
   if(sourceJump&&eligibleHotCachedSeek(s,target)){
    hotCachedSeekCorrections=0;
    startHotCachedSeek(s,target);
    return;
   }
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
   prewarmLocalFileForInitialAlignment(s,resumed,sourceJump);
   if(awaitLocalPrewarmMotion(s,resumed,sourceJump))return;
   if(clockDecision==ClockSupervisor.Decision.SEEK){
    long seekTarget=target;
    /* Only the first muted cold join predicts callback advance; user seeking stays frozen. */
    if(localPrewarmAlignmentPending&&!explicitSourceSeek&&!sourceJump
      &&streaming==null&&target<s.duration-500){
     seekTarget=predictedWarmTargetMs(target,player.getDuration());
     LogStore.log("replacement_cold_alignment_lead",LogStore.map(
      "trackId",trackId,"sourcePositionMs",target,"targetMs",seekTarget,
      "leadMs",seekTarget-target,"sourcePcmMeasured",false));
    }
    seek(s,seekTarget,drift);return;
   }
  if(localPrewarmAlignmentPending){
   localPrewarmAlignmentPending=false;localPrewarmJoinPending=true;
   logTrace("replacement_local_decoder_prewarm_aligned",LogStore.map("trackId",trackId,"sourcePositionMs",target,"decoderPositionMs",player.getCurrentPosition(),"seekSkipped",true,"originalAudible",originalMix>=0.999f));
  }
   boolean seamlessResume=retainedPauseResume&&originalMix<=0.001f&&Math.abs(drift)<=HANDOVER_DRIFT_MS;
   boolean newlyAttached=effect==null;
   boolean lateColdAttach=lateSourceEffectAttachExperiment&&newlyAttached
     &&(deferredEffectPending||!player.isPlaying())&&!seamlessResume&&!resumed&&!resumeFadePending
     &&!routePauseObserved&&!resumePositionRetained&&!sourceSeekedThisTrack
     &&!pendingStreamScrubJoin&&!bufferWaiting&&(streaming==null||conservativeColdJoinExperiment)&&trustedSession>0
     &&player.getAudioSessionId()!=trustedSession;
   if(newlyAttached&&!lateColdAttach&&!mute())return;
   if(effect!=null&&(!effect.hasControl()||!effect.getEnabled())){stop("effect_control_lost");return;}
    if(!player.isPlaying()){
     boolean prewarmedJoin=localPrewarmJoinPending;
     if(seamlessResume){audioOwner.grantReplacement(effect);originalMix=0f;applyVolume(1f);}else setAuditedVolume(player,0f);
     if(lateColdAttach){
      audioOwner.startMutedDecoderBeforeEffect(player,identityKey,audioOwner.epoch());
      logTrace("replacement_source_effect_deferred",LogStore.map(
        "trackId",trackId,"sourceSessionId",trustedSession,
        "sourceUntouched",true,"decoderMuted",true));
     }else audioOwner.startDecoder(player,effect,identityKey,audioOwner.epoch());
     try{logTrace("audio_decoder_start",LogStore.map("trackId",trackId,"decoderPositionMs",player.getCurrentPosition(),"sourcePositionMs",position(s),"reusePreparedDecoder",true,"seekPending",seeking,"sourceMutedCommand",effect!=null&&originalMix<=0.001f,"prewarmedLocalFile",localPrewarmAttempted));}catch(RuntimeException ignored){}
     traceAudioCommands();
     if(seamlessResume){fading=false;resumeFadePending=false;audioOwner.replacement();LogStore.log("replacement_resume_seamless",LogStore.map("trackId",trackId,"driftMs",drift,"sourcePositionMs",target,"retainedEffect",true));}
     else if(prewarmedJoin){localPrewarmJoinPending=false;startPrewarmedColdJoin();}
     /* HONOR Test.32: SAME_ITEM_SEEK-to-zero restarted a stopped decoder and
        used an audible 0ms exclusive_single_turn. Treat confirmed beginning
        replay as a new entry, including with a retained effect. Do NOT alter
        mid-song sparse finger-scrub callback timing or ordinary pause-resume:
        they have separate owner-accepted regression contracts. */
     else {
      boolean replayFromBeginning=sourceSeekedThisTrack&&target<=1500;
      fade((newlyAttached||pendingStreamScrubJoin||replayFromBeginning)
        &&!(newlyAttached&&coldJoinExclusiveExperiment&&!sourceSeekedThisTrack),
        lateColdAttach||streaming!=null);
     }
    }
    else if(newlyAttached){setAuditedVolume(player,0f);
     if(localPrewarmJoinPending){localPrewarmJoinPending=false;startPrewarmedColdJoin();}
     else fade(!(coldJoinExclusiveExperiment&&!sourceSeekedThisTrack),lateColdAttach||streaming!=null);}
    else if(localPrewarmJoinPending&&!fading){localPrewarmJoinPending=false;startPrewarmedColdJoin();}
    else if(!fading){
     if(originalMix>0.001f){
      // Test.31's exclusive_single_turn branch granted 100% volume after a
      // transient BUFFERING/seek while the original was audible. Every such
      // transfer now passes the same clock + runway + owner-ticket gate.
      setAuditedVolume(player,0f);fade(true,true);
     }else{
      // No transfer: retain the already-exclusive replacement owner.
      audioOwner.grantReplacement(effect);originalMix=0f;applyVolume(1f);
     }
    }
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
 void sourceSeekRequested(){
  if(!armed())return;
  explicitSourceSeek=true;sourceSeekedThisTrack=true;
  supersedePendingAlignmentForSourceSeek("media3_seek_discontinuity");
 }
 /* MediaPlayer seek callbacks have no request ID. If the source moves again
    during an ALIGNMENT seek, revoke that ticket immediately but keep its one
    native seek in flight. Its callback must drain before the latest target is
    submitted; issuing concurrent seekTo calls would make callbacks ambiguous. */
 void supersedePendingAlignmentForSourceSeek(String reason){
  if(!seeking||seekRetargetPending||player==null||!audioOwner.seekInFlight(player))return;
  long sequence=audioOwner.inFlightSequence(player);
  long oldTarget=audioOwner.inFlightTargetMs(player);
  long operationBefore=audioOwner.operationEpoch();
  audioOwner.event(AudioOwnership.Event.SEEK);
  audioOwner.aligning();
  seekRetargetPending=true;
  localPrewarmWarmupPending=false;localPrewarmAlignmentPending=false;localPrewarmJoinPending=false;
  seekHoldActive=false;pendingStreamScrubJoin=false;
  aligned=false;resumePositionRetained=false;fading=false;
  setAuditedVolume(player,0f);
  if(player.isPlaying())audioOwner.pauseDecoder(player);
  if(effect!=null&&originalMix<0.999f){
   audioOwner.sourceGainDuringAlignment(effect);originalMix=1f;traceAudioCommands();
  }
  logTrace("replacement_seek_superseded",LogStore.map(
    "reason",reason,"seekSeq",sequence,"oldTargetMs",oldTarget,
    "sourceEventSequence",owner.sourceEventSequence,
    "sourcePositionMs",owner.current==null?null:Long.valueOf(position(owner.current)),
    "operationEpochBefore",operationBefore,"operationEpochAfter",audioOwner.operationEpoch(),
    "singleFlightRetained",audioOwner.seekInFlight(player),
    "replacementMuted",commandedReplacementVolume<=0.001f,
    "sourceEffectRetained",effect!=null&&effect.hasControl()));
 }
 void sourceBoundary(String reason){sourceBoundary(reason,null);}
 void sourceBoundary(String reason,String nextAlias){
  if(closed)return;if(primedNext!=null&&primedNext.currentCache)discardPrimedNext("current_source_boundary");owner.noteSourceBoundary(nextAlias);sourceBufferSince=-1;generation++;preparing=false;
  Map<String,Object> boundaryContext=traceFields();
  release("track_changed");audioOwner.event(AudioOwnership.Event.BOUNDARY);audioOwner.invalidate(reason);
  identityKey=null;trackId=null;method="NONE";completedReason=null;clockSupervisor.reset();descriptor=null;lookupKey=null;nextLookup=0;failures=0;previousSource=null;completedKey=null;explicitSourceSeek=false;sourceSeekedThisTrack=false;unavailableSince=-1;status="Определяем новую песню; играет оригинал";ownerEvent("source_boundary");
  Map<String,Object> fields=LogStore.map("reason",reason,"originalRestoredBeforeLookup",true);
  fields.putAll(boundaryContext);fields.put("sourceItemGeneration",owner.sourceItemGeneration);fields.put("replacementGeneration",generation);
  LogStore.log("replacement_source_boundary",fields);
 }
 void sourceChanged(PlaybackSource previous,PlaybackSource next){
  long ownPosition=-1,ownDuration=-1;
  try{if(player!=null&&ready){ownPosition=player.getCurrentPosition();ownDuration=player.getDuration();}}catch(RuntimeException ignored){}
  LogStore.log("source_track_transition",LogStore.map("previousTrackId",trackId,"previousAlias",previous.alias,"nextAlias",next.alias,"previousDurationMs",previous.duration,"previousProjectedPositionMs",position(previous),"remainingSourceMs",Math.max(0,previous.duration-position(previous)),"replacementPositionMs",ownPosition,"replacementDurationMs",ownDuration,"replacementReady",ready,"followsNativeTrackChange",true,"sourceEventSequence",owner.sourceEventSequence,"sourceItemGeneration",owner.sourceItemGeneration));
  if(identityKey!=null||player!=null||preparing)sourceBoundary("sample_track_changed",next.alias);
  else owner.noteSourceBoundary(next.alias);
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
  boolean interruptedLocalPrewarm=localPrewarmWarmupPending||localPrewarmAlignmentPending;
  if(interruptedLocalPrewarm)localPrewarmAttempted=false;
  if(interruptedLocalPrewarm||localPrewarmJoinPending){localPrewarmWarmupPending=false;localPrewarmAlignmentPending=false;localPrewarmJoinPending=false;}
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
 /** The Test.29 "Дым" trace proved verified decoder seeks of 51–72ms still
  * performed two DSP/output ownership changes. A fully cached local seek can
  * instead stay in the already exclusive player. No muted-source timer:
  * source AND replacement retain their pre-seek gains while MediaPlayer seeks. */
 boolean eligibleHotCachedSeek(PlaybackSource s,long target){
  return s!=null&&target>=0&&target<s.duration&&ready&&armed()
   &&player!=null&&player.isPlaying()&&!seeking&&!fading&&!hotCachedSeek
   &&!audioOwner.seekInFlight(player)&&effect!=null&&effect.hasControl()&&effect.getEnabled()
   &&audioOwner.state()==AudioOwnership.State.REPLACEMENT
   &&originalMix<=0.001f&&commandedReplacementVolume>0.001f
   &&(streaming==null||streaming.hasVerifiedSeekNeighborhood(target,s.duration));
 }
 void startHotCachedSeek(PlaybackSource source,long target){
  if(hotCachedSeek)return;
  final MediaPlayer p=player;final String key=identityKey;
  clockSupervisor.onSeek();audioOwner.event(AudioOwnership.Event.SEEK);
  hotCachedSeek=true;hotCachedSeekPending=false;hotCachedSeekPaused=false;hotCachedSeekTarget=target;
  hotCachedSeekStarted=SystemClock.elapsedRealtime();hotCachedSeekEpoch=audioOwner.operationEpoch();
  final long seq=++hotCachedSeekSequence,epoch=hotCachedSeekEpoch;
  aligned=true;explicitSourceSeek=false;sourceSeekedThisTrack=true;
  logTrace("replacement_hot_cached_seek_request",LogStore.map(
   "trackId",trackId,"targetMs",target,"sourcePositionMs",position(source),
   "verifiedCache",true,"sourceGainChanged",false,"replacementGainChanged",false,
   "singleAudibleOwner",true,"sequence",seq,"audioSourceKind",audioSourceKind));
  // Preserve the owner-approved completeSeek() method byte-for-byte. Route
  // only this isolated experiment's callbacks through its own handler.
  p.setOnSeekCompleteListener(mp->{if(hotCachedSeek)completeHotCachedSeek(mp,key);else completeSeek(mp,key);});
  try{audioOwner.seekAudibleCached(p,target,key,audioOwner.epoch(),effect);}
  catch(RuntimeException ex){hotCachedSeek=false;suspend("hot_cached_seek_rejected",retryDelay());return;}
  owner.handler.postDelayed(()->{
   if(hotCachedSeek&&player==p&&seq==hotCachedSeekSequence&&epoch==hotCachedSeekEpoch
      &&(audioOwner.operationEpoch()==epoch||hotCachedSeekPaused)&&current(key)){
    logTrace("replacement_hot_cached_seek_timeout",LogStore.map(
     "trackId",trackId,"targetMs",target,"elapsedMs",SystemClock.elapsedRealtime()-hotCachedSeekStarted,
     "action","retire_untagged_decoder_restore_source"));
    hotCachedSeek=false;
    // Reusing this MediaPlayer would risk an old untagged callback being
    // mistaken for the next seek. Fail open through source, then recreate it.
    suspend("hot_cached_seek_timeout",retryDelay());
   }
  },HOT_CACHED_SEEK_TIMEOUT_MS);
 }
 void seek(PlaybackSource s,long target,long drift){seek(s,target,drift,false);}
 void seek(PlaybackSource s,long target,long drift,boolean correction){
   if(streaming!=null)streaming.holdPrefetchForSeek();
  boolean keepLocalPrewarmRunning=localPrewarmAlignmentPending&&!correction&&!explicitSourceSeek&&!audioOwner.seekInFlight(player);
  if(localPrewarmWarmupPending&&!keepLocalPrewarmRunning)localPrewarmWarmupPending=false;
  if(localPrewarmAlignmentPending&&!keepLocalPrewarmRunning){localPrewarmAlignmentPending=false;localPrewarmJoinPending=false;}
  if(audioOwner.seekInFlight(player)){
   seekRetargetPending=false;localPrewarmAlignmentPending=false;localPrewarmJoinPending=false;
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
  clockSupervisor.onSeek();audioOwner.event(AudioOwnership.Event.SEEK);audioOwner.aligning();explicitSourceSeek=false;resumePositionRetained=false;seekCorrections=correction?seekCorrections+1:0;seeking=true;seekRetargetPending=false;streamSeekWaitLogged=false;aligned=true;seekStarted=SystemClock.elapsedRealtime();seekBudget=streaming!=null&&!streaming.complete()?STREAM_SEEK_TIMEOUT_MS:SEEK_TIMEOUT_MS;transition++;fading=false;setAuditedVolume(player,0f);
  if(!keepLocalPrewarmRunning)audioOwner.pauseDecoder(player);
  else logTrace("replacement_local_decoder_prewarm_seek",LogStore.map("trackId",trackId,"decoderStillRunningMuted",player.isPlaying(),"targetMs",target));
  if(effect!=null){audioOwner.sourceGainDuringAlignment(effect);originalMix=1f;traceAudioCommands();}
  status="Синхронизация позиции; оригинал звучит…";ownerEvent("seek");logTrace("replacement_sync",LogStore.map("state","seek","trackId",trackId,"sourcePositionMs",target,"driftMs",drift,"originalStillMuted",false,"originalRestoredDuringSeek",true,"inaudibleCorrection",correction));final MediaPlayer p=player;final long t=transition,epoch=audioOwner.epoch();final String key=identityKey;
  long sourceAtSubmit=position(s),decoderAtSubmit=player.getCurrentPosition();
  audioOwner.issueSeek(p,target,key,epoch,AudioOwnership.SeekKind.ALIGNMENT,seekStarted,
    sourceAtSubmit,s.position,s.observed,decoderAtSubmit,seekContext());owner.handler.postDelayed(()->{if(player==p&&seeking&&transition==t&&audioOwner.current(epoch,key))suspend("seek_timeout",retryDelay());},seekBudget);}
 void prepare(String key,JSONObject j,long g){if(preparing||player!=null||!current(key)||!api.signedIn())return;PlaybackSource s=owner.current;if(!PlaybackDuration.metadataProbeAllowed(s.duration,j.optLong("duration_ms"))){LogStore.log("replacement_duration_mismatch",LogStore.map("trackId",trackId,"sourceDurationMs",s.duration,"replacementDurationMs",j.optLong("duration_ms")));completedKey=key;completedPosition=position(s);completedReason="Версия замены не совпадает по длительности — пропускаем эту песню, играет оригинал";audioOwner.unsupported("duration_mismatch");status=completedReason;LogStore.log("replacement_track_skipped",LogStore.map("reason","duration_mismatch","trackId",trackId,"sourceDurationMs",s.duration,"replacementDurationMs",j.optLong("duration_ms"),"action","original_until_next_track"));descriptor=null;return;}if(!PlaybackDuration.safe(s.duration,j.optLong("duration_ms"))){
   LogStore.log("replacement_duration_probe",LogStore.map("trackId",trackId,"sourceDurationMs",s.duration,"reportedDurationMs",j.optLong("duration_ms"),"policy","verify_measured_file_before_any_audio"));
  }audioOwner.preparing();prepareTicket=audioOwner.ticket(key,api.accountGeneration,j.optLong("replacement_id"),j.optLong("version"),j.optLong("duration_ms"));preparing=true;status="Готовим аудио заранее; оригинал продолжает играть";
  audioFromCache=false;
  File cached=recentAudio.remove(audioKey(j));
  if(cached!=null&&cached.isFile()){audioFromCache=true;if(Objects.equals(lookaheadPrefetchTrackId,trackId)&&Objects.equals(lookaheadPrefetchAlias,owner.current.alias))finishLookaheadPrefetch("cache_consumed");LogStore.log("replacement_audio_reused",LogStore.map("trackId",trackId,"liveResolveRequired",true,"cacheHit",true,"decoderRecreated",true,"sourceKind","local_cache_file","sourceItemGeneration",owner.sourceItemGeneration,"sourceEventSequence",owner.sourceEventSequence));acceptAudio(key,j,g,cached,null);return;}
  if(fullFileExperiment&&progressiveColdAllowed&&!key.equals(streamFallbackKey)){
   LogStore.log("replacement_progressive_cold_start",LogStore.map("trackId",trackId,
     "policy","validated_range_before_full_file","startupBudgetMs",1800,
     "originalRemainsAudible",true,"owner", "foreground_single_decoder"));
   startVerifiedProgressive(key,j,g);return;
  }
  if(fullFileExperiment){
   logTrace("replacement_full_file_experiment_start",LogStore.map(
     "trackId",trackId,"sourceKind","full_download_file",
     "streamingSkipped",true,"downloadBudgetMs",FULL_FILE_EXPERIMENT_BUDGET_MS,
     "originalRemainsAudible",true));
   downloadFull(key,j,g);return;
  }
  if(key.equals(streamFallbackKey)){downloadFull(key,j,g);return;}
  status="Подготавливаем начало песни; играет оригинал";
  final long account=api.accountGeneration;
  api.stream(j,()->transportLeaseCurrent(key,g,account),(source,error)->{
   if(g!=generation||closed||!current(key)||!api.signedIn()){if(source!=null)source.close();if(g==generation&&!closed)suspend("stream_source_changed",1000);return;}
   if(source==null){streamFallbackKey=key;LogStore.log("replacement_stream_fallback",LogStore.map("reason","range_unavailable"));downloadFull(key,j,g);return;}
   acceptAudio(key,j,g,null,source,null);
  });
 }
 void downloadFull(String key,JSONObject j,long g){audioFromCache=false;final long account=api.accountGeneration,start=SystemClock.elapsedRealtime();api.download(j,()->transportLeaseCurrent(key,g,account)&&(!fullFileExperiment||SystemClock.elapsedRealtime()-start<FULL_FILE_EXPERIMENT_BUDGET_MS),(file,error)->acceptAudio(key,j,g,file,error));}
 void startVerifiedProgressive(String key,JSONObject j,long g){
  final long account=api.accountGeneration;
  PlaybackSource observed=owner.current;
  final long sourcePositionMs=observed==null?-1:position(observed),sourceDurationMs=observed==null?-1:observed.duration;
  status="Подключаем замену по проверенным частям файла; играет оригинал";
  api.stream(j,()->transportLeaseCurrent(key,g,account),sourcePositionMs,sourceDurationMs,(source,error)->{
   if(g!=generation||closed||!current(key)||!api.signedIn()){
    if(source!=null)source.close();return;
   }
   if(source==null){
    streamFallbackKey=key;
    LogStore.log("replacement_progressive_cold_fallback",LogStore.map(
      "trackId",trackId,"reason",error==null?"range_unavailable":error,
      "action","accepted_full_file_download"));
    downloadFull(key,j,g);return;
   }
   LogStore.log("replacement_progressive_cold_ready",LogStore.map("trackId",trackId,
     "cachedBytes",source.cachedBytes(),"verifiedRange",true,"decoderSource","private_sparse_file"));
   acceptAudio(key,j,g,null,source,null);
  });
 }
 void acceptAudio(String key,JSONObject j,long g,File file,String error){acceptAudio(key,j,g,file,null,error);}
 void acceptAudio(String key,JSONObject j,long g,File file,BufferedAudio source,String error){if(g!=generation||closed||!audioOwner.dataCurrent(prepareTicket,api.accountGeneration,key,j.optLong("replacement_id"),j.optLong("version"),j.optLong("duration_ms"))){if(file!=null)file.delete();if(source!=null)source.close();return;}preparing=false;if(file==null&&source==null){suspend("download_failed",retryDelay());status="Сеть недоступна; играет оригинал, повторим автоматически";return;}if(!current(key)||!api.signedIn()){if(file!=null)file.delete();if(source!=null)source.close();suspend("download_source_changed",1000);return;}
   try{if(source!=null)audioFromCache=false;audioFile=file;streaming=source;audioSourceKind=source!=null?"stream":audioFromCache?"local_cache_file":"full_download_file";localPrewarmAttempted=false;localPrewarmAlignmentPending=false;localPrewarmJoinPending=false;bufferWaiting=false;
    lastPrimeWasCurrentCache=false;
    final MediaPlayer primed=source==null&&file!=null?takePrimedNext(owner.current.alias,audioKeyFor(trackId,j),file):null;
    final boolean decoderPrimed=primed!=null;
    player=decoderPrimed?primed:new MediaPlayer();decoderInstanceId=++decoderInstanceSequence;final MediaPlayer p=player;final long ownerTicket=audioOwner.epoch();final AudioOwnership.Ticket dataTicket=prepareTicket;p.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());setAuditedVolume(p,0f);if(!decoderPrimed){if(source==null)p.setDataSource(file.getAbsolutePath());else p.setDataSource(new StreamingAudio(source));}p.setOnErrorListener((mp,what,extra)->{if(mp==player&&g==generation&&audioOwner.current(ownerTicket,key)&&accountLeaseCurrent()){suspend("media_player_error",retryDelay());LogStore.log("replacement_failure",LogStore.map("reason","media_player_error","what",what,"extra",extra));}return true;});p.setOnCompletionListener(mp->{
    if(mp!=player||g!=generation||!audioOwner.current(ownerTicket,key)||!accountLeaseCurrent())return;
    if(localPrewarmWarmupPending||localPrewarmAlignmentPending||localPrewarmJoinPending){
     LogStore.log("replacement_completion_before_local_join",LogStore.map(
       "trackId",trackId,"cacheHit",audioFromCache,"decoderPositionMs",mp.getCurrentPosition(),
       "originalAudible",originalMix>=0.999f,"action","keep_original"));
     suspend("replacement_completed",30000);
     return;
    }
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
   });final MediaPlayer.OnPreparedListener livePrepared=mp->{if(mp!=player||g!=generation||!audioOwner.current(ownerTicket,key)||!accountLeaseCurrent()||!audioOwner.dataCurrent(dataTicket,api.accountGeneration,key,j.optLong("replacement_id"),j.optLong("version"),j.optLong("duration_ms")))return;audioOwner.event(AudioOwnership.Event.PREPARE_READY);if(!current(key)){suspend("prepared_stale",1000);return;}PlaybackSource now=owner.current;boolean durationCompatible=PlaybackDuration.compatible(now.duration,j.optLong("duration_ms"),mp.getDuration(),verifiedDurationIdentity());
   if(!ApiContract.durations(now.duration,j.optLong("duration_ms"),mp.getDuration())||
     !durationCompatible||
     (trustedSession>0&&mp.getAudioSessionId()==trustedSession)){
    if(!durationCompatible){
     LogStore.log("replacement_duration_mismatch",LogStore.map("trackId",trackId,"sourceDurationMs",now.duration,"reportedDurationMs",j.optLong("duration_ms"),"replacementDurationMs",mp.getDuration(),"stage","measured_file"));
     completedKey=identityKey;completedPosition=position(now);completedReason="Эту замену нельзя воспроизводить безопасно; играет оригинал";
    }
    suspend("duration_or_session_invalid",30000);if(completedReason!=null){audioOwner.unsupported("measured_duration_mismatch");status=completedReason;}else status="Проверка аудио не пройдена; играет оригинал";return;}
   if(!PlaybackDuration.safe(now.duration,mp.getDuration()))
    LogStore.log("replacement_bounded_tail_accepted",LogStore.map("trackId",trackId,"sourceDurationMs",now.duration,"measuredDurationMs",mp.getDuration(),"reportedDurationMs",j.optLong("duration_ms"),"identityMethod",method,"originalRetainedUntilBoundary",true));
   if(!PlaybackDuration.safe(now.duration,j.optLong("duration_ms")))
    LogStore.log("replacement_duration_probe_verified",LogStore.map("trackId",trackId,"sourceDurationMs",now.duration,"reportedDurationMs",j.optLong("duration_ms"),"measuredDurationMs",mp.getDuration()));
   ready=true;failures=0;preparedAt=SystemClock.elapsedRealtime();
    if(decoderPrimed){localPrewarmAttempted=true;localPrewarmAlignmentPending=true;
     logTrace(lastPrimeWasCurrentCache?"replacement_cached_current_prime_adopted":"replacement_lookahead_decoder_prime_adopted",LogStore.map(
      "trackId",trackId,"sourceItemGeneration",owner.sourceItemGeneration,
      "freshResolveRequired",true,"measuredDurationVerified",true,"audioKeyMatches",true));
    }
    status=armed()?"Аудио готово; синхронизируем":"Аудио готово заранее; можно включать автозамену";logTrace("replacement_prepared",LogStore.map("trackId",trackId,"measuredDurationMs",mp.getDuration(),"sourceDurationMs",now.duration,"separateAudioSession",true,"beforeArm",!armed()));owner.requestFastJoinSamples();update(now);};p.setOnPreparedListener(livePrepared);p.setOnSeekCompleteListener(mp->completeSeek(mp,key));
    if(decoderPrimed)livePrepared.onPrepared(p);else p.prepareAsync();if(source!=null)source.prefetch();final MediaPlayer preparingPlayer=p;owner.handler.postDelayed(()->{if(player==preparingPlayer&&!ready)suspend("prepare_timeout",retryDelay());},10000);
   }catch(Exception e){suspend("prepare_failed",retryDelay());status="Не удалось подготовить аудио; играет оригинал";}
 }
 void completeHotCachedSeek(MediaPlayer mp,String key){
  if(mp!=player||!Objects.equals(identityKey,key)||!accountLeaseCurrent())return;
  if(hotCachedSeek){
   long elapsed=SystemClock.elapsedRealtime()-hotCachedSeekStarted;
   PlaybackSource now=owner.current;
   long actual=mp.getCurrentPosition();
   long desired=now==null?-1:position(now);
   long difference=desired-actual;
   boolean pending=hotCachedSeekPending;
   boolean interruptedByPause=hotCachedSeekPaused;
   hotCachedSeek=false;hotCachedSeekPending=false;hotCachedSeekPaused=false;
   logTrace("replacement_hot_cached_seek_ack",LogStore.map(
    "trackId",trackId,"requestedPositionMs",hotCachedSeekTarget,
    "sourceProjectedMs",desired,"decoderPositionMs",actual,"residualMs",difference,
    "callbackElapsedMs",elapsed,"sourceGainChanged",false,"replacementGainChanged",false,
    "singleAudibleOwner",true,"pendingRetarget",pending,"correctionPass",hotCachedSeekCorrections));
   if(!ready||!armed()||now==null||!current(key)
      ||(!interruptedByPause&&audioOwner.operationEpoch()!=hotCachedSeekEpoch)){
    suspend("hot_cached_seek_stale",1000);return;
   }
   if(interruptedByPause){
    // The source pause changed the owner epoch deliberately. Its in-flight
    // native callback is now drained. Never resume audio from the callback:
    // re-align normally only after the source reports actual playback again.
    aligned=false;resumePositionRetained=false;
    if(!now.playing){
     status="Пауза во время перемотки — аудио сохранено";
     logTrace("replacement_hot_cached_seek_pause_drained",LogStore.map(
      "trackId",trackId,"callbackElapsedMs",elapsed,"decoderRetained",true));
     return;
    }
    if(Math.abs(difference)<=HANDOVER_DRIFT_MS&&effect!=null
       &&effect.hasControl()&&effect.getEnabled()&&originalMix<=0.001f
       &&audioOwner.state()==AudioOwnership.State.ALIGNING){
     // A short false/true Media3 pulse did not invalidate native alignment.
     // Reuse the owner-approved seamless-resume grant: one decoder, no second
     // native seek, and no original-to-replacement gain reversal.
     audioOwner.grantReplacement(effect);originalMix=0f;
     applyVolume(1f);
     audioOwner.startDecoder(mp,effect,identityKey,audioOwner.epoch());
     audioOwner.replacement();resumeFadePending=false;aligned=true;
     explicitSourceSeek=false;previousSource=now;
     logTrace("replacement_hot_cached_seek_resume_aligned",LogStore.map(
      "trackId",trackId,"residualMs",difference,"reseek",false,
      "decoderRetained",true,"sourceGainChanged",false));
     return;
    }
    seek(now,desired,difference,true);return;
   }
   if(!now.playing){pauseSource(now,false);return;}
   if(pending||Math.abs(difference)>HANDOVER_DRIFT_MS){
    if(hotCachedSeekCorrections<1&&eligibleHotCachedSeek(now,desired)){
     hotCachedSeekCorrections++;
     startHotCachedSeek(now,desired);return;
    }
    // Do not retry an audible seek against speculative or missing bytes.
    // Its last callback has drained, so the ordinary serialized silent seek
    // can safely restore original audio while waiting for the network.
    seek(now,desired,difference,true);return;
   }
   explicitSourceSeek=false;previousSource=now;aligned=true;
   status="Играет замена · быстрая перемотка без переподключения";
   logTrace("replacement_hot_cached_seek_complete",LogStore.map(
    "trackId",trackId,"elapsedMs",elapsed,"sourceGainChanged",false,
    "replacementGainChanged",false,"sourcePcmMeasured",false,
    "hardwareOutputMeasured",false));
   return;
  }
 }
 void completeSeek(MediaPlayer mp,String key){
  if(mp!=player||!Objects.equals(identityKey,key)||!accountLeaseCurrent())return;
  AudioOwnership.SeekAck ack=audioOwner.acceptSeekCompletion(mp);
  if(ack==null)return; // repeated/retired callback
  seekRetargetPending=false;
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
  if(ack.context!=null)ackFields.putAll(ack.context.fields());
  LogStore.log("replacement_seek_ack",ackFields);
    if(ack.operationEpoch!=audioOwner.operationEpoch()){
   if(localPrewarmWarmupPending||localPrewarmAlignmentPending){localPrewarmWarmupPending=false;localPrewarmAlignmentPending=false;localPrewarmJoinPending=false;}
   /* A pause revoked output permission, not necessarily the decoder position.
      Reuse a verified final alignment without granting an old audible command.
      A new source position or route loss must never reuse the canceled result. */
   PlaybackSource sourceNow=owner.current;
   boolean positionStillValid=ack.kind==AudioOwnership.SeekKind.ALIGNMENT
      &&!waitingForRouteResume&&sourceNow!=null&&current(key)
      &&Math.abs(position(sourceNow)-mp.getCurrentPosition())<=PAUSE_ALIGN_TOLERANCE_MS;
   seeking=false;aligned=positionStillValid;
   resumePositionRetained=positionStillValid;
   if(positionStillValid){explicitSourceSeek=false;previousSource=sourceNow;}
   if(!waitingForRouteResume&&sourceNow!=null&&sourceNow.playing)update(sourceNow);
   return;
  }
  if(ack.kind==AudioOwnership.SeekKind.ALIGNMENT&&localPrewarmAlignmentPending){
   localPrewarmAlignmentPending=false;localPrewarmJoinPending=true;
   LogStore.log("replacement_local_decoder_prewarm_aligned",LogStore.map("trackId",trackId,"sourcePositionMs",projectedAtAck,"decoderPositionMs",decoderAtAck,"seekCallbackElapsedMs",ackClock-ack.submittedAt,"originalAudible",originalMix>=0.999f));
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
  Map<String,Object> completeFields=LogStore.map(
    "elapsedMs",elapsed,"trackId",trackId,"seekSeq",ack.sequence,"seekKind",ack.kind.name(),
    "requestedPositionMs",ack.targetMs,"rangeWaitObserved",ack.rangeWaitObserved,"residualMs",residual,
    "sourceProjectedAtCompleteMs",target,"decoderPositionAtCompleteMs",decoderAtComplete,
    "residualSemantics","source transport minus decoder cursor at callback; not output presentation",
    "sourceSnapshotAgeAtCompleteMs",Math.max(0,clock-now.observed),
    "correctionPass",seekCorrections,"sourcePcmMeasured",false,"phaseVerified",false);
  if(ack.context!=null)completeFields.putAll(ack.context.fields());
  LogStore.log("replacement_seek_complete",completeFields);
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
 boolean mute(){try{if(trustedSession<=0||player==null||player.getAudioSessionId()==trustedSession)throw new IllegalStateException();DynamicsProcessing candidate=new DynamicsProcessing(0,trustedSession,null);effect=candidate;candidate.setControlStatusListener((e,control)->owner.handler.post(()->{if(effect!=candidate)return;Map<String,Object> state=owner.runtimeSnapshot("audio_effect_control_status");state.put("controlGranted",control);LogStore.log("audio_effect_control_status",state);if(!control)stop("effect_control_lost");}));if(!candidate.hasControl())throw new IllegalStateException();originalMix=1f;audioOwner.prepareSourceEffect(candidate);deferredEffectPending=false;LogStore.log("replacement_original_muted",LogStore.map("sessionId",trustedSession,"globalVolumeChanged",false,"rampMs",resumeFadePending?PAUSE_RESUME_FADE_MS:FADE_MS));return true;}catch(RuntimeException e){stop("cannot_mute_original");status="Телефон не разрешил приглушить Яндекс; замена остановлена";return false;}}
  void startPrewarmedColdJoin(){
   if(coldJoinExclusiveExperiment){
    logTrace("replacement_cold_join_experiment_start",LogStore.map(
      "trackId",trackId,"mode","exclusive_after_existing_clock_gate",
      "baselineMode","unified_complementary_linear",
      "sourcePcmMeasured",false,"phaseVerified",false));
    fade(false,true);
   }else fade(true,true);
  }
  void fade(boolean coherentEntry){fade(coherentEntry,streaming!=null);}
 static boolean exclusiveColdEnvelope(boolean coherentEntry,boolean requireClockGate,
                                      boolean enabled,boolean seekedCurrentTrack){
  // The same streaming decoder is re-entered after every finger seek. That
  // must NOT turn a post-seek handover into another first-cold 32/48ms duck.
  return !coherentEntry&&requireClockGate&&enabled&&!seekedCurrentTrack;
 }
 void fade(boolean coherentEntry,boolean requireClockGate){
  final long token=++transition;final MediaPlayer p=player;
  final DynamicsProcessing[] fxRef={effect};
  final boolean sourceEffectDeferred=fxRef[0]==null;
  final boolean conservativeCold=conservativeColdJoinExperiment&&sourceEffectDeferred
    &&!sourceSeekedThisTrack&&!pendingStreamScrubJoin&&!explicitSourceSeek
    &&!resumePositionRetained&&!waitingForRouteResume;
  final JoinStabilityWindow stableClock=new JoinStabilityWindow();
  final long[] firstEligibleClock={-1};
  final long[] adaptiveDuration={UNIFIED_JOIN_MS};final float[] adaptiveMix={0f};
  final String[] fadeStage={"clock_gate"};
  final long ownerEpoch=audioOwner.epoch();final String ownerKey=identityKey;
  // A completed seek releases foreground priority. Holding background
  // prefetch through a clock-gated join exhausted the initial 128KiB prefix.
  if(streaming!=null){streaming.releasePrefetchAfterSeek();streaming.prefetch();}
  audioOwner.aligning();
  audioOwner.event(AudioOwnership.Event.HANDOVER);
  final AudioOwnership.Ticket handoverTicket=audioOwner.ticket(ownerKey,api.accountGeneration,descriptor==null?0:descriptor.optLong("replacement_id"),descriptor==null?0:descriptor.optLong("version"),descriptor==null?0:descriptor.optLong("duration_ms"));
   /* The original stays audible during native decoder startup and clock
      alignment. The isolated prewarmed cold-join experiment may use an exclusive
      single-turn grant after this same clock gate; the legacy baseline retains
      its complementary-linear entry. Transport clocks do not measure PCM phase. */
  resumeFadePending=false;
  final boolean alignLive=requireClockGate||sourceEffectDeferred;
  final long[] baseline={p.getCurrentPosition()},phaseStarted={SystemClock.elapsedRealtime()};
  final int[] corrections={0};final long[] softStarted={-1};
  /* Exclusive cold joins previously switched unity source -> unity decoder in
     one handler tick. That is click-prone even when transport clocks agree:
     they do not prove matching PCM phase. Keep the two audible sessions strictly
     disjoint; shape only the very first cold handover, never a finger seek. */
  final long[] exclusiveDuckStarted={-1},exclusiveRiseStarted={-1};
  final boolean shapeExclusiveCold=exclusiveColdEnvelope(coherentEntry,requireClockGate,
       coldJoinExclusiveExperiment&&!Objects.equals(coldEnvelopeOwnerKey,ownerKey),sourceSeekedThisTrack);
  /* Passive cold join drift summary: projected transport clocks only. */
  final long[] coldClock={Long.MAX_VALUE,Long.MIN_VALUE,0,-1,-1};
  final boolean[] outputPreLogged={false},outputMidLogged={false},outputPostLogged={false},runwayWaitLogged={false};
  final long coldStarted=SystemClock.elapsedRealtime();
  if(originalMix<=0.001f&&!seekHoldActive){
   setAuditedVolume(p,0f);
   audioOwner.sourceGainDuringAlignment(fxRef[0]);originalMix=1f;traceAudioCommands();
  }
  fadeStarted=SystemClock.elapsedRealtime();fading=true;audioOwner.handoverWaitForClock(alignLive);
  Runnable ramp=new Runnable(){public void run(){
   if(closed||token!=transition||p!=player||fxRef[0]!=effect||!armed()||!accountLeaseCurrent()
      ||!audioOwner.current(ownerEpoch,ownerKey)||!audioOwner.commandCurrent(handoverTicket,api.accountGeneration,ownerKey,descriptor==null?0:descriptor.optLong("replacement_id"),descriptor==null?0:descriptor.optLong("version"),descriptor==null?0:descriptor.optLong("duration_ms")))return;
   try{
    fadeStage[0]="clock_gate";
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
     if(now-coldStarted>=(streaming!=null?STREAM_RUNWAY_WAIT_MS:STRICT_JOIN_BUDGET_MS)){
      if(streaming!=null){
       LogStore.log("replacement_stream_runway_timeout",LogStore.map("trackId",trackId,
         "cachedBytes",streaming.cachedBytes(),"originalAudible",true,
         "action","full_file_retry"));
       streamFallbackKey=identityKey;suspend("stream_runway_timeout",1000);return;
      }
      skipUnstableJoin("join_gate_deadline",position(owner.current)-position,corrections[0]);return;
     }
     if(audioOwner.seekInFlight(p)||position-baseline[0]<40){
      if(now-phaseStarted[0]>=2000){
       skipUnstableJoin("decoder_start_timeout",position(owner.current)-position,corrections[0]);return;
      }
      owner.handler.postDelayed(this,20);return;
     }
     long target=position(owner.current),drift=target-position;
     if(streaming!=null&&!streaming.hasPlayableRunway(target,owner.current.duration)){
      if(!runwayWaitLogged[0]){
       runwayWaitLogged[0]=true;
       LogStore.log("replacement_stream_runway_wait",LogStore.map("trackId",trackId,
         "cachedBytes",streaming.cachedBytes(),"contiguousAheadBytes",
         streaming.contiguousAhead(target,owner.current.duration),"requiredBytes",
         streaming.runwayTargetBytes(target,owner.current.duration),
         "originalAudible",true,"decoderMuted",true));
      }
      status="Готовим непрерывный буфер; играет оригинал";
      owner.handler.postDelayed(this,40);return;
     }
     if(Math.abs(drift)>(conservativeCold?JoinStabilityWindow.MAX_DRIFT_MS:STRICT_STREAM_JOIN_DRIFT_MS)){
      if(corrections[0]>=2||target>=p.getDuration()-150){
       skipUnstableJoin("join_alignment_unstable",drift,corrections[0]);return;
      }
      stableClock.reset();firstEligibleClock[0]=-1;
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
        position(sourceAtSubmit),sourceAtSubmit.position,sourceAtSubmit.observed,p.getCurrentPosition(),seekContext());
      owner.handler.postDelayed(this,20);return;
     }
     if(conservativeCold){
      if(firstEligibleClock[0]<0)firstEligibleClock[0]=now;
      JoinStabilityWindow.Decision decision=stableClock.observe(now,drift,
        firstEligibleClock[0],streaming!=null?JoinStabilityWindow.STREAM_DEADLINE_MS:
          JoinStabilityWindow.LOCAL_DEADLINE_MS);
      if(decision==JoinStabilityWindow.Decision.UNSAFE){
       skipUnstableJoin("cold_clock_not_stable",drift,corrections[0]);return;
      }
      if(decision==JoinStabilityWindow.Decision.WAIT){
       owner.handler.postDelayed(this,20);return;
      }
      LogStore.log("replacement_cold_clock_window_verified",LogStore.map(
       "trackId",trackId,"samples",stableClock.samples,
       "observationMs",now-stableClock.started,"minDriftMs",stableClock.min,
       "maxDriftMs",stableClock.max,"originalAudible",true,
       "sourcePcmMeasured",false,"phaseVerified",false));
     }
     audioOwner.handoverClockValidated();fadeStarted=now;
     logTrace("replacement_join_guard_verified",LogStore.map(
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
     // Attach the native source effect at 0dB only AFTER all cold-start
     // checks pass. A stale controller, failed seek or buffer timeout never
     // touches Yandex's audio processing. The verified effect remains the
     // required guard before any secondary volume may become nonzero.
     if(sourceEffectDeferred&&fxRef[0]==null){
      fadeStage[0]="source_effect_attach";
      if(!mute())return;
      fxRef[0]=effect;
      LogStore.log("replacement_source_effect_attached_at_join",LogStore.map(
        "trackId",trackId,"sessionId",trustedSession,
        "sourcePcmMeasured",false,"sourceGainDb",0,
        "decoderAlreadyAdvancingMuted",p.isPlaying()));
     }
     final DynamicsProcessing fx=fxRef[0];
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
      if(adaptiveJoinExperiment){
       long entryDrift=position(owner.current)-p.getCurrentPosition();
       adaptiveDuration[0]=JoinTransitionPolicy.durationMs(entryDrift,
         Math.max(0,softStarted[0]-owner.current.observed),
         joinRetryPreferBaseline&&Objects.equals(joinRetryKey,ownerKey));
      }
       logTrace("replacement_unified_join_start",LogStore.map("trackId",trackId,
         "durationMs",adaptiveDuration[0],"gainLaw","complementary_linear",
         "adaptive",adaptiveJoinExperiment,
         "baselineRetry",adaptiveJoinExperiment&&joinRetryPreferBaseline&&Objects.equals(joinRetryKey,ownerKey),
         "sourcePcmMeasured",false,"phaseVerified",false,"oneMode",true));
     }
     long elapsed=Math.max(0,SystemClock.elapsedRealtime()-softStarted[0]);
     if(!outputMidLogged[0]&&elapsed>=adaptiveDuration[0]/2){
      logOutputClockSample(p,owner.current,"blend_midpoint");outputMidLogged[0]=true;
     }
     long sourceProjected=position(owner.current),decoderProjected=p.getCurrentPosition();
     long transportDrift=sourceProjected-decoderProjected;
     coldClock[0]=Math.min(coldClock[0],transportDrift);
     coldClock[1]=Math.max(coldClock[1],transportDrift);
     if(coldClock[2]++==0){coldClock[3]=sourceProjected;coldClock[4]=decoderProjected;}
      float mix=adaptiveJoinExperiment
       ?JoinTransitionPolicy.boundedMix(elapsed,adaptiveDuration[0],adaptiveMix[0])
       :TransitionMix.progress(elapsed,UNIFIED_JOIN_MS);
     adaptiveMix[0]=mix;
     float gain=(float)Math.min(1,Math.pow(10,Math.min(0,descriptor==null?0:descriptor.optDouble("gain_db",0))/20));
     fadeStage[0]="positive_gain_ramp";
     if(adaptiveJoinExperiment)rampPositiveGain(p,mix);
     fadeStage[0]="same_song_mix";
     float volume=audioOwner.blendSameSong(p,fx,mix,Math.max(0.00001f,gain),ownerKey,ownerEpoch,handoverTicket.operationEpoch);
     originalMix=1f-mix;commandedReplacementVolume=volume;traceAudioCommands();
      // blendSameSong grants REPLACEMENT only at the exact 1.0 endpoint.
      // Test.43 proved that >=0.999 could reach this path at 0.99902/0.99975,
      // when the source still owns a tiny fraction and audioOwner.volume(1)
      // correctly throws "secondary gain without exclusive owner". Complete
      // the bounded remaining step before issuing any exclusive gain command.
      if(!JoinTransitionPolicy.exclusiveGainReady(mix)){owner.handler.postDelayed(this,20);return;}
     fadeStage[0]="final_decoder_gain";
     applyVolume(1f);
    }else if(shapeExclusiveCold){
     long now=SystemClock.elapsedRealtime();
     if(exclusiveDuckStarted[0]<0){
       coldEnvelopeOwnerKey=ownerKey;
      exclusiveDuckStarted[0]=now;
      LogStore.log("replacement_exclusive_soft_join_start",LogStore.map(
       "trackId",trackId,"sourceDuckMs",32,"decoderRiseMs",48,
       "sourcePcmMeasured",false,"phaseVerified",false,"nonOverlapping",true));
     }
     if(exclusiveRiseStarted[0]<0){
      float progress=TransitionMix.progress(now-exclusiveDuckStarted[0],32);
      audioOwner.duckSourceForExclusiveJoin(p,fx,progress,ownerKey,ownerEpoch,handoverTicket.operationEpoch);
      originalMix=1f-progress;traceAudioCommands();
      if(progress<1f){owner.handler.postDelayed(this,10);return;}
      audioOwner.grantReplacement(fx);originalMix=0f;applyVolume(0f);
      exclusiveRiseStarted[0]=now;
      owner.handler.postDelayed(this,10);return;
     }
     float progress=TransitionMix.progress(now-exclusiveRiseStarted[0],48);
     applyVolume(progress);
     if(progress<1f){owner.handler.postDelayed(this,10);return;}
    }else{
     audioOwner.grantReplacement(fx);originalMix=0f;applyVolume(1f);
    }
    fadeStage[0]="post_join_clock_sample";
    if(!outputPostLogged[0]){
     logOutputClockSample(p,owner.current,coherentEntry?"post_blend":"post_exclusive_grant");
     outputPostLogged[0]=true;
    }
    if(adaptiveJoinExperiment){joinRetryKey=null;joinRetryAttempts=0;joinRetryPreferBaseline=false;}
    fadeStage[0]="owner_completion";
    fading=false;audioOwner.replacement();seekHoldActive=false;pendingStreamScrubJoin=false;ownerEvent("exclusive_handover");
     if(streaming!=null)streaming.releasePrefetchAfterSeek();
    if(coherentEntry&&coldClock[2]>0)LogStore.log("replacement_join_transport_summary",LogStore.map(
      "joinMode","unified_complementary_linear","transportOnly",true,
      "elapsedFromJoinStartMs",SystemClock.elapsedRealtime()-coldStarted,
      "commandedJoinMs",adaptiveDuration[0],"adaptive",adaptiveJoinExperiment,"samples",coldClock[2],
      "sourceStartMs",coldClock[3],"decoderStartMs",coldClock[4],
      "sourceEndMs",position(owner.current),"decoderEndMs",p.getCurrentPosition(),
      "minDriftMs",coldClock[0],"maxDriftMs",coldClock[1],
      "sourcePcmMeasured",false,"phaseVerified",false));
    logTrace("replacement_transition_complete",LogStore.map(
       "trackId",trackId,"rampMs",coherentEntry?adaptiveDuration[0]:shapeExclusiveCold?80:0,
       "joinMode",coherentEntry?"unified_complementary_linear":shapeExclusiveCold?"exclusive_duck_then_rise":"exclusive_single_turn",
      "commandDelayMs",SystemClock.elapsedRealtime()-fadeStarted));
   }catch(RuntimeException e){recoverFailedJoin(e,fadeStage[0],adaptiveDuration[0],adaptiveMix[0]);}
  }};ramp.run();
 }
 /** Existing gain_db above zero used to switch LoudnessEnhancer on only when
  * the fade ended, producing an instantaneous level jump for boosted tracks.
  * Test.42 warms the replacement effect at 0dB while the decoder is muted,
  * then moves its gain along with the bounded output fade. */
 void rampPositiveGain(MediaPlayer p,float mix){
  double db=descriptor==null?0:descriptor.optDouble("gain_db",0);
  if(!(db>0)||!Double.isFinite(db)||joinLoudnessUnavailable)return;
  try{
   if(loudness==null){
    loudness=new LoudnessEnhancer(p.getAudioSessionId());
    loudness.setTargetGain(0);loudness.setEnabled(true);
   }
   loudness.setTargetGain((int)Math.round(Math.min(30,db)*100*mix));
  }catch(RuntimeException ex){
   joinLoudnessUnavailable=true;
   LogStore.log("replacement_gain",LogStore.map("reason","join_loudness_ramp_unavailable"));
  }
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
 void unmute(MediaPlayer secondary){seekHoldActive=false;deferredEffectPending=false;if(effect!=null){DynamicsProcessing fx=effect;effect=null;AudioOwnership.RestoreResult r=audioOwner.restoreSource(secondary,fx);commandedReplacementVolume=0f;originalMix=1f;LogStore.log("replacement_original_restored",LogStore.map("reason","effect_released","gainReset",r.gainReset,"disabled",r.disabled,"released",r.released,"hardwareAudibilityVerified",false));ownerEvent("source_restored");traceAudioCommands();}}
 /* Invalidate ramps and silence output before cache, network or diagnostic cleanup.
    HttpURLConnection.disconnect and effect release may block on the old route. */
 MediaPlayer silenceBeforeCleanup(){transition++;fading=false;MediaPlayer old=player;player=null;if(old!=null){boolean zero=false,paused=false;try{setAuditedVolume(old,0f);zero=true;}catch(RuntimeException ignored){}try{audioOwner.pauseDecoder(old);paused=!old.isPlaying();}catch(RuntimeException ignored){}LogStore.log("replacement_output_silenced",LogStore.map("trackId",trackId,"gainZero",zero,"paused",paused,"beforeTransportCleanup",true));}unmute(old);return old;}
 void release(String reason){
  primeReadyWaitInFlight=false;primeReadyWaitToken++;sourceBufferSince=-1;audioOwner.cancelPause();
  localPrewarmAttempted=false;localPrewarmWarmupPending=false;localPrewarmAlignmentPending=false;localPrewarmJoinPending=false;localPrewarmWarmupStartedAt=0;localPrewarmWarmupPosition=0;audioFromCache=false;
  boolean had=player!=null||effect!=null;MediaPlayer old=silenceBeforeCleanup();
  if("identity_changed".equals(reason)||"track_changed".equals(reason)||"replacement_end".equals(reason)||"replacement_completed".equals(reason)||"source_end".equals(reason)||"source_unavailable".equals(reason)||"source_disconnected".equals(reason)||"fade_failed".equals(reason))rememberAudio();
  retainInterruptedCompleteFile(reason);
  /* Detach a completed file before MediaPlayer.release closes its MediaDataSource. */
  if(old!=null){try{old.setOnErrorListener(null);old.setOnPreparedListener(null);old.setOnCompletionListener(null);old.setOnSeekCompleteListener(null);}catch(RuntimeException ignored){}try{old.release();}catch(RuntimeException ignored){}}
  returning=false;pausedAt=-1;resumeFadePending=false;seekHoldActive=false;pendingStreamScrubJoin=false;
  hotCachedSeek=false;hotCachedSeekPending=false;hotCachedSeekPaused=false;hotCachedSeekSequence++;
  audioOwner.source();audioOwner.retireDecoder();prepareTicket=null;bufferGate.reset();bufferWaiting=false;if(streaming!=null){streaming.close();streaming=null;}ready=false;seeking=false;seekRetargetPending=false;fading=false;aligned=false;resumePositionRetained=false;
  if(loudness!=null){try{loudness.release();}catch(RuntimeException ignored){}loudness=null;}joinLoudnessUnavailable=false;if(audioFile!=null){audioFile.delete();audioFile=null;}if(had)LogStore.log("replacement_released",LogStore.map("reason",reason));
 }
 void suspend(String reason,long delay){if(streaming!=null&&Arrays.asList("prepare_timeout","prepare_failed","duration_or_session_invalid","seek_timeout","media_player_error","decoder_start_timeout").contains(reason)){streamFallbackKey=identityKey;delay=1000;LogStore.log("replacement_stream_fallback",LogStore.map("reason",reason));}if("replacement_completed".equals(reason)||"replacement_end".equals(reason)||"source_end".equals(reason)){completedKey=identityKey;completedPosition=owner.current==null?0:position(owner.current);}Map<String,Object> recovery=owner.runtimeSnapshot("replacement_recovery_"+reason);generation++;preparing=false;release(reason);descriptor=null;lookupKey=null;nextLookup=SystemClock.elapsedRealtime()+delay;audioOwner.recovering(reason);ownerEvent("recovery");recovery.put("reason",reason);recovery.put("automaticModeRetained",armed());recovery.put("retryMs",delay);recovery.put("retryAtElapsedMs",nextLookup);recovery.put("failureCount",failures);recovery.put("postReleaseReady",ready);recovery.put("postReleasePreparing",preparing);LogStore.log("replacement_recovery",recovery);}
 void returnOriginal(){
  if(!accountLeaseCurrent())return;
  if(player==null||effect==null||!ready||!current(identityKey)||!owner.current.playing
     ||seeking||hotCachedSeek||audioOwner.seekInFlight(player)||originalMix>0.001f){
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
 void stop(String reason){discardPrimedNext("replacement_stop");invalidateLookaheadPrefetch("replacement_stop_"+reason);Map<String,Object> stopState=owner.runtimeSnapshot("replacement_stop_"+reason);stopState.put("stopReason",reason);LogStore.log("replacement_stop_state",stopState);previousSource=null;completedKey=null;completedReason=null;clockSupervisor.reset();explicitSourceSeek=false;unavailableSince=-1;waitingForRouteResume=false;routePauseObserved=false;preloadAllowed=false;clearAudioCache();returning=false;armedUntil=0;trustedSession=-1;generation++;preparing=false;release(reason);descriptor=null;lookupKey=null;nextLookup=0;status="Замена выключена; играет оригинал";authorizationAccount=-1;audioOwner.event(AudioOwnership.Event.STOP);audioOwner.stopped();ownerEvent("stopped");if("yandex_audio_session_changed".equals(reason)||"effect_control_lost".equals(reason))status="Яндекс сменил аудиосессию. Открой его эквалайзер → CELIKOM и снова включи автозамену";else if("headphones_disconnected".equals(reason))status="Наушники отключены. Оригинал восстановлен; подключи их и снова включи автозамену";LogStore.log("replacement_trial_stop",LogStore.map("reason",reason));}
 void close(){closed=true;stop("service_stopped");}
 void ownerEvent(String event){LogStore.log("audio_owner_state",LogStore.map("event",event,"state",audioOwner.state().name(),"ownerGeneration",audioOwner.epoch(),"ownerReason",audioOwner.reason(),"trackId",trackId,"identityKey",identityKey,"replacementVolume",commandedReplacementVolume,"sourceMutedCommand",effect!=null&&originalMix<=0.001f,"hardwareOutputMeasured",false));}
 void logSync(String state,PlaybackSource s,long drift){String key=state+"|"+s.key;long now=SystemClock.elapsedRealtime();if(!key.equals(lastSync)||lastSyncAt<0||now-lastSyncAt>=10000||Math.abs(drift-lastLoggedDrift)>=500){lastSync=key;lastSyncAt=now;lastLoggedDrift=drift;LogStore.log("replacement_sync",LogStore.map("state",state,"trackId",trackId,"sourcePositionMs",position(s),"driftMs",drift));}}

 static String message(String code){switch(code){case "login_required":case "invalid_session":return "нужно войти в CELIKOM";case "access_denied":case "trial_not_activated":return "нет активного доступа CELIKOM";case "invalid_credentials":return "неверная почта или пароль";case "rate_limited":return "слишком много запросов — попробуй позже";default:return code;}}
}
