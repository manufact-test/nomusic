package pro.celikom.nativeprobe.identitydiag;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.media.AudioManager;
import android.media.AudioAttributes;
import android.media.AudioPlaybackConfiguration;
import android.media.audiofx.AudioEffect;
import android.os.*;
import android.net.*;
import androidx.media3.common.*;
import androidx.media3.session.*;
import com.google.common.util.concurrent.ListenableFuture;
import java.io.*;
import java.util.*;
/** Current-player observation only. No notification, Accessibility, library or account access to Yandex. */
public class ProbeService extends Service {
 final String notificationRun=UUID.randomUUID().toString();String lastNotificationKey="";final SourceTransitionGate transitionGate=new SourceTransitionGate();final SourceSessionRecheck sessionRecheck=new SourceSessionRecheck();final SourceEventArbiter sourceArbiter=new SourceEventArbiter();final Media3SourceRouter media3Router=new Media3SourceRouter(sourceArbiter,new Media3SourceRouter.Sink(){public void boundary(String next,String reason){sourceBoundary(next,reason);}public void seekRequested(){if(replacement!=null)replacement.sourceSeekRequested();}});final SourceEventArbiter.LookaheadEvidence lookahead=new SourceEventArbiter.LookaheadEvidence();final SourceStateWatchdog stateWatchdog=new SourceStateWatchdog();final LegacySourcePositionPolicy legacyPositionPolicy=new LegacySourcePositionPolicy();android.media.browse.MediaBrowser legacyBrowser;android.media.session.MediaController legacyController;long lastLegacyDiagnosticAt=-1;boolean legacyPositionUnsafeLogged;boolean controllerSeen;long controllerGeneration,lastMediaEvent,lastHealth,endReachedAt=-1,sourceEventSequence,sourceItemGeneration;String sourceItemAlias;
 static ProbeService instance;final Handler handler=new Handler(Looper.getMainLooper());long serviceCreatedAt=-1,lastTickAt=-1,lastSampleAt=-1,lastHeartbeatAt=-1,lastNetworkAvailableAt=-1,lastNetworkLostAt=-1;int tickCount,sampleCount;
 volatile PlaybackSource current;AlbumProbe albumProbe;ReplacementEngine replacement;androidx.media3.session.MediaController controller;ListenableFuture<androidx.media3.session.MediaController> connecting,sourceProbe;PowerManager.WakeLock wake;boolean receiverRegistered,stopping,networkRegistered,networkSeen;ConnectivityManager connectivity;long lastWakeRenewal,lastState,lastConnectAttempt=-5000,nextConnectAllowedAt=-1,emptySince=-1,lastLookaheadPoll=-2000;int sourceProbeFailures;volatile String observedNextAlias,sourceTransitionExpectedAlias;String lastLookaheadSource,lastLookaheadCandidate,lastLookaheadSignature,lastLookaheadMetadataSignature;int lookaheadMetadataSamples,attempts;String lastStateKey="",connectionStatus="Подключаемся к Яндексу…",lastRoutes="";
 boolean alive(){return instance==this&&!stopping;}
 public void onCreate(){super.onCreate();LogStore.init(this);serviceCreatedAt=SystemClock.elapsedRealtime();}
 public IBinder onBind(Intent i){return null;}
 static final class NotificationContent {
  final NotificationState state;final NotificationTarget target;
  NotificationContent(NotificationState state,NotificationTarget target){this.state=state;this.target=target;}
  String fingerprint(){return state.fingerprint()+"|"+(target==null?"":target.fingerprint());}
 }
 NotificationContent notificationContent(){
  NativeApi api=NativeApi.get(this);AppPresentation.Input input=PlaybackUi.capture(this,api.signedIn(),replacement==null,"");PlaybackSource source=current;MobileActions.Target song=PlaybackUi.target(this);
  boolean lost=controllerSeen&&(controller==null||!controller.isConnected()),sessionLost=replacement!=null&&replacement.status.startsWith("Яндекс сменил");boolean hasReplacement=replacement!=null&&replacement.descriptor!=null&&replacement.descriptor.optBoolean("found");
  NotificationState state=NotificationState.of(input,source==null?"":source.title,source==null?"":source.artist,lost,sessionLost,song!=null,hasReplacement);
  NotificationTarget target=state.suggest&&song!=null?new NotificationTarget(notificationRun,song.id,song.key,api.accountGeneration):null;return new NotificationContent(state,target);
 }
 Intent notificationOpen(){return new Intent(this,RecorderActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);}
 Notification buildNotification(NotificationContent content){
  PendingIntent open=PendingIntent.getActivity(this,0,notificationOpen(),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
  PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,ProbeService.class).setAction("stop"),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
  Notification.Builder builder=new Notification.Builder(this,"diagnostic_v2").setSmallIcon(android.R.drawable.ic_media_play).setContentTitle(content.state.title).setContentText(content.state.text).setStyle(new Notification.BigTextStyle().bigText(content.state.text)).setSubText("CELIKOM").setShowWhen(false).setOnlyAlertOnce(true).setContentIntent(open).setOngoing(true).setVisibility(Notification.VISIBILITY_PRIVATE);
  if(content.target!=null){NotificationTarget t=content.target;Intent action=notificationOpen().setAction(NotificationTarget.ACTION).setData(new android.net.Uri.Builder().scheme("celikom").authority("suggest").appendPath(t.fingerprint()).build()).putExtra("notification_run",t.run).putExtra("notification_track",t.id).putExtra("notification_key",t.key).putExtra("notification_account",t.account);PendingIntent suggest=PendingIntent.getActivity(this,2,action,PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);builder.addAction(new Notification.Action.Builder(null,"Предложить песню",suggest).build());}
  builder.addAction(new Notification.Action.Builder(null,"Открыть CELIKOM",open).build());builder.addAction(new Notification.Action.Builder(null,"Стоп",stop).build());return builder.build();
 }
 Notification notification(){return buildNotification(notificationContent());}
 final Runnable notificationTick=new Runnable(){public void run(){if(!alive())return;try{NotificationContent content=notificationContent();String key=content.fingerprint();if(!key.equals(lastNotificationKey)){lastNotificationKey=key;getSystemService(NotificationManager.class).notify(220,buildNotification(content));}}catch(RuntimeException e){LogStore.error("notification_update",e);}handler.postDelayed(this,1000);}};
 public int onStartCommand(Intent i,int flags,int id){if(i!=null&&"stop".equals(i.getAction())){finish("user_stop");return START_NOT_STICKY;}if(alive()){if(LogStore.active){Map<String,Object> state=runtimeSnapshot("service_start_command_reused");state.put("startId",id);state.put("flags",flags);state.put("armExtra",i!=null&&i.getBooleanExtra("arm",false));LogStore.log("service_start_command",state);}if(i!=null&&i.getBooleanExtra("arm",false))beginTrial();return START_NOT_STICKY;}instance=this;
  try{NotificationManager nm=getSystemService(NotificationManager.class);nm.createNotificationChannel(new NotificationChannel("diagnostic_v2","Воспроизведение CELIKOM",NotificationManager.IMPORTANCE_LOW));if(Build.VERSION.SDK_INT>=34)startForeground(220,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);else startForeground(220,notification());LogStore.begin();try{Class<?> store=Class.forName("pro.celikom.nativeprobe.ProbeStore");store.getMethod("setEnabled",android.content.Context.class,boolean.class).invoke(store.getField("INSTANCE").get(null),this,true);}catch(Exception e){LogStore.log("native_audio_observation","Could not enable existing audio-session observation");}albumProbe=new AlbumProbe(this);replacement=new ReplacementEngine(this,true,true,false);replacement.adaptiveJoinExperiment=true;if(LogStore.active){Map<String,Object> state=runtimeSnapshot("service_start_command_created");state.put("startId",id);state.put("flags",flags);state.put("armExtra",i!=null&&i.getBooleanExtra("arm",false));LogStore.log("service_start_command",state);}
   File[] old=getCacheDir().listFiles((dir,name)->(name.startsWith("replacement-")||name.startsWith("buffered-"))&&name.endsWith(".audio"));if(old!=null)for(File f:old)f.delete();
   PowerManager pm=getSystemService(PowerManager.class);wake=pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"CELIKOM:playback");wake.setReferenceCounted(false);wake.acquire(90000);
   IntentFilter filter=new IntentFilter(AudioEffect.ACTION_OPEN_AUDIO_EFFECT_CONTROL_SESSION);filter.addAction(AudioEffect.ACTION_CLOSE_AUDIO_EFFECT_CONTROL_SESSION);filter.addAction(AudioManager.ACTION_AUDIO_BECOMING_NOISY);if(Build.VERSION.SDK_INT>=33)registerReceiver(audio,filter,Context.RECEIVER_EXPORTED);else registerReceiver(audio,filter);receiverRegistered=true;startPlaybackActivityObserver();
   PackageInfo p=getPackageManager().getPackageInfo(LogStore.PKG,0);LogStore.log("environment",LogStore.map("manufacturer",Build.MANUFACTURER,"model",Build.MODEL,"api",Build.VERSION.SDK_INT,"android",Build.VERSION.RELEASE,"yandexVersion",p.versionName,"yandexVersionCode",p.getLongVersionCode()));LogStore.log("build_policy",LogStore.map("notificationListener",false,"accessibility",false,"sms",false,"microphone",false,"accountPasswordsLogged",false,"replacementRequiresUserStart",true,"durationLimited",false,"apiOrigin",ApiContract.ORIGIN));
   connectivity=getSystemService(ConnectivityManager.class);try{connectivity.registerDefaultNetworkCallback(networkCallback);networkRegistered=true;}catch(RuntimeException e){LogStore.error("network_callback",e);}connect();handler.post(tick);handler.post(notificationTick);if(i!=null&&i.getBooleanExtra("arm",false))beginTrial();NativeApi.get(this).check((j,e)->{if(alive())LogStore.log("server_preflight",LogStore.map("ok",e==null,"errorCode",e,"signedIn",NativeApi.get(this).signedIn()));});
  }catch(Throwable e){LogStore.error("service_start",e);finish("start_failed");}return START_NOT_STICKY;
 }
 final ConnectivityManager.NetworkCallback networkCallback=new ConnectivityManager.NetworkCallback(){public void onAvailable(Network n){handler.post(()->{if(!alive())return;boolean retry=networkSeen;networkSeen=true;lastNetworkAvailableAt=SystemClock.elapsedRealtime();NetworkCapabilities caps=connectivity==null?null:connectivity.getNetworkCapabilities(n);LogStore.log("network_available",LogStore.map("retry",retry,"validated",caps!=null&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED),"wifi",caps!=null&&caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI),"cellular",caps!=null&&caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR),"vpn",caps!=null&&caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN)));if(retry){albumProbe.retryFailedAfterNetworkChange();if(replacement.player==null&&!replacement.preparing)replacement.suspend("network_available",0);}});}public void onLost(Network n){handler.post(()->{if(alive()){lastNetworkLostAt=SystemClock.elapsedRealtime();if(LogStore.active){Map<String,Object> state=runtimeSnapshot("network_lost");state.put("networkHandle",n.getNetworkHandle());LogStore.log("network_lost_state",state);}LogStore.log("network_lost","original remains available; replacement errors restore source and retry");}});}};
 final BroadcastReceiver audio=new BroadcastReceiver(){public void onReceive(Context c,Intent i){if(!alive()||replacement==null)return;String action=i.getAction();if(AudioManager.ACTION_AUDIO_BECOMING_NOISY.equals(action)){replacement.headphonesDisconnected();return;}if(!LogStore.PKG.equals(i.getStringExtra(AudioEffect.EXTRA_PACKAGE_NAME)))return;int session=i.getIntExtra(AudioEffect.EXTRA_AUDIO_SESSION,-1);boolean verifiedSender=verifiedSessionSender(this);
  boolean mustStop=YandexSessionSafety.shouldFailClosed(replacement.armed(),true,action,session,replacement.trustedSession);
  LogStore.log("audio_session_broadcast",LogStore.map("action",action,"sessionId",session,"trustedSessionId",replacement.trustedSession,
    "trustedForAttach",false,"senderUidVerified",verifiedSender,"failClosedSessionChange",mustStop));
  if(mustStop){
   /* On API 33 the sender UID cannot be verified: this broadcast can REVOKE a stale session,
      never AUTHORIZE a new one. Continuing replacement would layer it over new Yandex audio. */
   LogStore.log("replacement_yandex_session_stale_fail_closed",LogStore.map(
     "observedSessionId",session,"trustedSessionId",replacement.trustedSession,
     "senderUidVerified",verifiedSender,"newSessionTrusted",false,"audioCommandSent",true));
   replacement.stop("yandex_audio_session_changed");
  }else if(AudioEffect.ACTION_OPEN_AUDIO_EFFECT_CONTROL_SESSION.equals(action)){
   // A same-session OPEN is a non-authoritative Android 13 hint, not proof
   // that the Media3 controller or track changed. Test.40 probed a second
   // controller and could quarantine the real playback on probe failures.
   // Keep the live controller and replacement; Media3 callbacks and actual
   // disconnection remain the only source of reconnection decisions.
   LogStore.log("source_same_session_open_ignored",LogStore.map(
     "sessionId",session,"trustedSessionId",replacement.trustedSession,
     "controllerRetained",controller!=null&&controller.isConnected()));
  }}};
 void recheckQuietSourceController(int session){
  if(!alive()||replacement==null)return;
  PlaybackSource source=current;androidx.media3.session.MediaController stale=controller;
  long now=SystemClock.elapsedRealtime();
  boolean replacementAudible=replacement.armed()&&replacement.player!=null&&replacement.effect!=null;
  if(!sessionRecheck.probe(replacementAudible,stale!=null&&stale.isConnected(),
     source==null?null:source.alias,source==null?-1:source.position,
     session,replacement.trustedSession,lastMediaEvent<0?-1:now-lastMediaEvent,now))return;
  LogStore.log("source_controller_suspected_stale",LogStore.map(
    "reason","same_session_reopened_without_media3_events","suspectAlias",source.alias,
    "suspectPositionMs",source.position,"mediaEventAgeMs",now-lastMediaEvent,
    "sessionId",session,"unverifiedBroadcastOnlyRevokesAudio",true,
    "newSourceAuthorization",false));
  // The session OPEN is *unverified* on API 33. Test.39 discarded a healthy
  // read-only controller immediately; a failed reconnect then hid multiple
  // tracks for 40+ seconds. Verify with a second controller first, without
  // disturbing the working one or granting any new audio authorization.
  probeFreshSource(stale);
 }

 /** A second, short-lived read-only controller proves whether a quiet source
  * actually switched. Never release the live controller on a mere broadcast.
  * Failure quarantines replacement audio but leaves the original connected. */
 void probeFreshSource(androidx.media3.session.MediaController old){
  if(!alive()||old==null||controller!=old||!old.isConnected()||sourceProbe!=null)return;
  final long started=SystemClock.elapsedRealtime();
  try{
   SessionToken token=new SessionToken(this,new ComponentName(LogStore.PKG,
     "com.yandex.music.shared.media.session.session.Media3LibraryService"));
   final ListenableFuture<androidx.media3.session.MediaController> future=
     new androidx.media3.session.MediaController.Builder(this,token).buildAsync();
   sourceProbe=future;
   handler.postDelayed(()->{if(sourceProbe==future&&!future.isDone())future.cancel(false);},5000);
   future.addListener(()->{
    if(sourceProbe==future)sourceProbe=null;
    androidx.media3.session.MediaController fresh=null;
    try{
     fresh=future.get();
     if(!alive()||controller!=old)return;
     MediaItem item=fresh.getCurrentMediaItem();
     String freshAlias=item==null?null:item.mediaId;
     long freshPosition=item==null?-1:fresh.getCurrentPosition();
     boolean same=sessionRecheck.sameProgressOnFreshController(
       freshAlias,freshPosition,SystemClock.elapsedRealtime());
     LogStore.log("source_controller_probe_result",LogStore.map(
       "connected",true,"sameSource",same,"freshAlias",freshAlias,
       "elapsedMs",SystemClock.elapsedRealtime()-started,"audioCommandSent",false));
     sourceProbeFailures=0;
     if(same){sessionRecheck.clear();if(replacement!=null)replacement.update(current);return;}
     // Contradictory/empty fresh data: stop the old replacement before any
     // new controller is allowed to authorize another track.
     if(replacement!=null)replacement.suspend("source_controller_changed",1200);
     sessionRecheck.quarantine();current=null;lastStateKey="";
     stateWatchdog.reset();transitionGate.clear();controller=null;
     try{old.release();}catch(RuntimeException ignored){}
     nextConnectAllowedAt=-1;connect();
    }catch(Exception error){
     if(alive()&&controller==old){
      sourceProbeFailures++;
      sessionRecheck.quarantine();
      if(replacement!=null)replacement.suspend("source_probe_unavailable",1200);
      LogStore.log("source_controller_probe_result",LogStore.map(
        "connected",false,"type",error.getClass().getSimpleName(),
        "causeType",error.getCause()==null?"":error.getCause().getClass().getSimpleName(),
        "attempt",sourceProbeFailures,"oldControllerRetained",true));
      final long delay=Math.min(20000L,1500L*sourceProbeFailures);
      handler.postDelayed(()->{if(alive()&&controller==old&&sessionRecheck.awaitingFreshSource)
        probeFreshSource(old);},delay);
     }
    }finally{if(fresh!=null)try{fresh.release();}catch(RuntimeException ignored){}}
   },handler::post);
  }catch(RuntimeException error){
   sessionRecheck.quarantine();
   if(replacement!=null)replacement.suspend("source_probe_start_failed",1200);
   LogStore.log("source_controller_probe_result",LogStore.map(
     "connected",false,"type",error.getClass().getSimpleName(),"oldControllerRetained",true));
  }
 }
 /* Public API26 playback trace. Other applications are anonymized and cannot be identified.
   Counts are diagnostics only; never infer source seek/pause or issue audio commands. */
 AudioManager.AudioPlaybackCallback playbackActivityObserver;
 boolean playbackActivityRegistered;
 int lastPlatformMediaActive=-1,lastPlatformOtherActive=-1;
 void startPlaybackActivityObserver(){
  if(Build.VERSION.SDK_INT<26||playbackActivityRegistered)return;
  AudioManager manager=getSystemService(AudioManager.class);
  if(manager==null)return;
  playbackActivityObserver=new AudioManager.AudioPlaybackCallback(){
   @Override public void onPlaybackConfigChanged(List<AudioPlaybackConfiguration> configs){
    if(!alive()||!LogStore.active||configs==null)return;
    int media=0,other=0;
    for(AudioPlaybackConfiguration config:configs){
     if(config==null||config.getAudioAttributes()==null)continue;
     if(config.getAudioAttributes().getUsage()==AudioAttributes.USAGE_MEDIA)media++;else other++;
    }
    if(media==lastPlatformMediaActive&&other==lastPlatformOtherActive)return;
    lastPlatformMediaActive=media;lastPlatformOtherActive=other;
    PlaybackSource source=current;ReplacementEngine engine=replacement;
    boolean decoderPlaying=false;
    try{decoderPlaying=engine!=null&&engine.player!=null&&engine.player.isPlaying();}catch(RuntimeException ignored){}
    LogStore.log("platform_audio_activity_observed",LogStore.map(
     "activeMediaPlayers",media,"activeOtherPlayers",other,
     "sourceAlias",source==null?null:source.alias,
     "media3Playing",source!=null&&source.playing,"replacementDecoderPlaying",decoderPlaying,
     "identityAvailable",false,"positionAvailable",false,"sourceAppIdentified",false,
     "observationOnly",true,"audioCommandSent",false));
   }
  };
  try{manager.registerAudioPlaybackCallback(playbackActivityObserver,handler);playbackActivityRegistered=true;}
  catch(RuntimeException e){playbackActivityObserver=null;LogStore.log("platform_audio_activity_unavailable",LogStore.map("reason",e.getClass().getSimpleName()));}
 }
 void stopPlaybackActivityObserver(){
  if(!playbackActivityRegistered)return;
  playbackActivityRegistered=false;
  try{getSystemService(AudioManager.class).unregisterAudioPlaybackCallback(playbackActivityObserver);}
  catch(RuntimeException ignored){}
  playbackActivityObserver=null;
 }
 boolean screenInteractive(){PowerManager power=(PowerManager)getSystemService(POWER_SERVICE);return power!=null&&power.isInteractive();}
 boolean verifiedSessionSender(BroadcastReceiver receiver){
  // Package/session extras alone are not caller authentication. On older Android,
  // unverified broadcasts stay observations; effect control and verified panel remain authoritative.
  if(Build.VERSION.SDK_INT<34)return false;
  try{return receiver.getSentFromUid()==getPackageManager().getApplicationInfo(LogStore.PKG,0).uid;}catch(Exception ignored){return false;}
 }
 void connect(){if(!alive()||controller!=null||connecting!=null||SystemClock.elapsedRealtime()<nextConnectAllowedAt||SystemClock.elapsedRealtime()-lastConnectAttempt<1000)return;final long connectStartedAt=SystemClock.elapsedRealtime();lastConnectAttempt=connectStartedAt;final int connectAttempt=++attempts;final long connectGeneration=++controllerGeneration;if(LogStore.active)LogStore.log("media3_connect_attempt",LogStore.map("attempt",connectAttempt,"generation",connectGeneration,"lastMediaEventAgeMs",lastMediaEvent<=0?-1:connectStartedAt-lastMediaEvent,"replacementArmed",replacement!=null&&replacement.armed()));try{SessionToken token=new SessionToken(this,new ComponentName(LogStore.PKG,"com.yandex.music.shared.media.session.session.Media3LibraryService"));connecting=new androidx.media3.session.MediaController.Builder(this,token).setListener(new androidx.media3.session.MediaController.Listener(){public void onDisconnected(androidx.media3.session.MediaController c){if(controller==c){if(LogStore.active){Map<String,Object> state=runtimeSnapshot("media3_disconnected");state.put("connectAttempt",connectAttempt);LogStore.log("media3_disconnect_state",state);}controller=null;current=null;nextConnectAllowedAt=SystemClock.elapsedRealtime()+2000;connectionStatus="Соединение потеряно; переподключаемся…";replacement.update(null);LogStore.log("media3_disconnected","retry scheduled");handler.postDelayed(ProbeService.this::connect,2000);}}}).buildAsync();final ListenableFuture<androidx.media3.session.MediaController> future=connecting;handler.postDelayed(()->{if(connecting==future&&!future.isDone())future.cancel(false);},12000);future.addListener(()->{if(connecting==future)connecting=null;try{androidx.media3.session.MediaController c=future.get();if(!alive()||connectGeneration!=controllerGeneration){c.release();return;}controller=c;transitionGate.clear();lookahead.reset();lastLookaheadSource=null;lastLookaheadPoll=-2000;controllerSeen=true;lastMediaEvent=SystemClock.elapsedRealtime();if(LogStore.active)LogStore.log("media3_connect_result",LogStore.map("attempt",connectAttempt,"elapsedMs",lastMediaEvent-connectStartedAt,"connected",true,"generation",connectGeneration));attempts=0;nextConnectAllowedAt=-1;connectionStatus="Яндекс подключён";c.addListener(new Player.Listener(){public void onEvents(Player p,Player.Events e){if(!alive()||controller!=c)return;lastMediaEvent=SystemClock.elapsedRealtime();sample(true);}
    public void onTimelineChanged(Timeline timeline,int reason){if(!alive()||controller!=c)return;lastLookaheadPoll=-2000;long eventId=++sourceEventSequence;int currentIndex=-1,itemCount=-1;String liveAlias=null;try{currentIndex=c.getCurrentMediaItemIndex();itemCount=c.getMediaItemCount();MediaItem live=c.getCurrentMediaItem();liveAlias=live==null?null:live.mediaId;}catch(RuntimeException ignored){}LogStore.log("source_timeline_changed",LogStore.map("sourceEventId",eventId,"sourceItemGeneration",sourceItemGeneration,"reasonCode",reason,"reasonClass",SourceEventArbiter.classifyTimelineChange(reason),"windowCount",timeline==null?0:timeline.getWindowCount(),"currentIndex",currentIndex,"itemCount",itemCount,"liveAlias",liveAlias,"audioCommandSent",false));}
    public void onMediaItemTransition(MediaItem item,int reason){if(!alive()||controller!=c)return;long eventId=++sourceEventSequence;String next=item==null?null:item.mediaId;String live=null;try{MediaItem fresh=c.getCurrentMediaItem();live=fresh==null?null:fresh.mediaId;}catch(RuntimeException ignored){}String active=current==null?null:current.alias;long livePos=-1;int liveIndex=-1,itemCount=-1;try{livePos=c.getCurrentPosition();liveIndex=c.getCurrentMediaItemIndex();itemCount=c.getMediaItemCount();}catch(RuntimeException ignored){}String transitionClass=SourceEventArbiter.classifyMediaItemTransition(reason);SourceEventArbiter.Action action=media3Router.mediaItem(active,live,next,reason,livePos);LogStore.log("source_media_item_transition",LogStore.map("sourceEventId",eventId,"sourceItemGeneration",sourceItemGeneration,"reasonCode",reason,"transitionClass",transitionClass,"eventNextAlias",next,"liveAlias",live,"currentAlias",active,"livePositionMs",livePos,"liveIndex",liveIndex,"timelineItemCount",itemCount,"decision",action.name(),"manualNextButtonObserved",false,"manualNextAttribution","not_exposed_by_media3_listener","audioCommandSent",false));if(action!=SourceEventArbiter.Action.BOUNDARY)LogStore.log("source_boundary_ignored",LogStore.map("sourceEventId",eventId,"reason","stale_media_item_transition","eventNextAlias",next,"liveAlias",live,"currentAlias",active,"repeat",SourceEventArbiter.isRepeatTransition(reason),"transitionClass",transitionClass));}
    public void onPositionDiscontinuity(Player.PositionInfo oldPosition,Player.PositionInfo newPosition,int reason){if(!alive()||controller!=c)return;String oldAlias=oldPosition.mediaItem==null?null:oldPosition.mediaItem.mediaId,nextAlias=newPosition.mediaItem==null?null:newPosition.mediaItem.mediaId;boolean automatic=reason==Player.DISCONTINUITY_REASON_AUTO_TRANSITION,userSeek=reason==Player.DISCONTINUITY_REASON_SEEK;long eventId=++sourceEventSequence;String classification=SourceEventArbiter.classifyDiscontinuity(automatic,userSeek,oldPosition.mediaItemIndex,newPosition.mediaItemIndex,oldAlias,nextAlias);LogStore.log("source_discontinuity",LogStore.map("sourceEventId",eventId,"sourceItemGeneration",sourceItemGeneration,"reasonCode",reason,"classification",classification,"automaticTransition",automatic,"userSeek",userSeek,"itemIndexChanged",oldPosition.mediaItemIndex!=newPosition.mediaItemIndex,"aliasChanged",!Objects.equals(oldAlias,nextAlias),"manualNextButtonObserved",false,"manualNextAttribution","not_exposed_by_media3_listener","deviceInteractive",screenInteractive(),"oldPositionMs",oldPosition.positionMs,"newPositionMs",newPosition.positionMs,"oldAlias",oldAlias,"nextAlias",nextAlias,"oldIndex",oldPosition.mediaItemIndex,"nextIndex",newPosition.mediaItemIndex));
    String live=null;long livePosition=-1;
    try{if(c.isConnected()){MediaItem fresh=c.getCurrentMediaItem();live=fresh==null?null:fresh.mediaId;livePosition=c.getCurrentPosition();}}catch(RuntimeException ignored){}
    String active=current==null?null:current.alias;
    boolean boundary=SourceEventArbiter.isBoundary(reason==Player.DISCONTINUITY_REASON_AUTO_TRANSITION,oldPosition.mediaItemIndex,newPosition.mediaItemIndex,oldAlias,nextAlias);
    SourceEventArbiter.Action decision=media3Router.discontinuity(active,live,oldAlias,nextAlias,
      oldPosition.mediaItemIndex,newPosition.mediaItemIndex,oldPosition.positionMs,newPosition.positionMs,livePosition,
      reason==Player.DISCONTINUITY_REASON_AUTO_TRANSITION,reason==Player.DISCONTINUITY_REASON_SEEK);
    if(decision==SourceEventArbiter.Action.IGNORE){
      if(boundary)LogStore.log("source_boundary_ignored",LogStore.map("reason","stale_position_transition","oldAlias",oldAlias,"eventNextAlias",nextAlias,"liveAlias",live,"currentAlias",active));
      else if(reason==Player.DISCONTINUITY_REASON_SEEK)LogStore.log("source_seek_event_ignored",LogStore.map("reason","stale_or_unknown_controller_position","eventPositionMs",newPosition.positionMs,"controllerPositionMs",livePosition));
    }
    if(reason==Player.DISCONTINUITY_REASON_SEEK&&sessionRecheck.confirmFreshSeek(live,newPosition.positionMs,livePosition))
      LogStore.log("source_controller_freshness_confirmed",LogStore.map("reason","fresh_seek_event","alias",live,"audioCommandSent",false));
     }});LogStore.log("media3_connected","direct service; no notification access");connectLegacyPosition();sample(true);}catch(Exception e){if(alive()&&connectGeneration==controllerGeneration){connectionStatus="Ожидаем Яндекс Музыку";long retryMs=Math.min(20000,1000L*Math.max(1,connectAttempt));if(LogStore.active)LogStore.log("media3_connect_result",LogStore.map("attempt",connectAttempt,"elapsedMs",SystemClock.elapsedRealtime()-connectStartedAt,"connected",false,"errorType",e.getClass().getSimpleName(),"causeType",e.getCause()==null?"":e.getCause().getClass().getSimpleName(),"retryMs",retryMs));LogStore.log("media3_connection_failed",LogStore.map("attempt",connectAttempt,"type",e.getClass().getSimpleName()));nextConnectAllowedAt=SystemClock.elapsedRealtime()+retryMs;handler.postDelayed(this::connect,retryMs);}}},handler::post);}catch(RuntimeException e){connectionStatus="Яндекс ещё не доступен";if(LogStore.active)LogStore.log("media3_connect_result",LogStore.map("attempt",connectAttempt,"elapsedMs",SystemClock.elapsedRealtime()-connectStartedAt,"connected",false,"errorType",e.getClass().getSimpleName(),"retryMs",5000));nextConnectAllowedAt=SystemClock.elapsedRealtime()+5000;handler.postDelayed(this::connect,5000);}}
 final Runnable tick=new Runnable(){public void run(){if(!alive())return;long now=SystemClock.elapsedRealtime(),previousTick=lastTickAt;lastTickAt=now;tickCount++;if(LogStore.active&&(lastHeartbeatAt<0||now-lastHeartbeatAt>=15000)){lastHeartbeatAt=now;Map<String,Object> state=runtimeSnapshot("periodic_15s");state.put("previousTickGapMs",previousTick<0?-1:now-previousTick);LogStore.log("service_heartbeat",state);}if(wake!=null&&now-lastWakeRenewal>=60000){wake.acquire(90000);lastWakeRenewal=now;}NativeApi.get(ProbeService.this).refreshDiagnostics();sample(false);handler.postDelayed(this,250);}};
 Map<String,Object> runtimeSnapshot(String reason){
  long now=SystemClock.elapsedRealtime();ReplacementEngine e=replacement;PlaybackSource s=current;
  boolean controllerConnected=false,controllerPlaying=false;int controllerState=-1;long controllerPosition=-1;
  try{if(controller!=null&&controller.isConnected()){controllerConnected=true;controllerPlaying=controller.isPlaying();controllerState=controller.getPlaybackState();controllerPosition=controller.getCurrentPosition();}}catch(RuntimeException ignored){}
  boolean effectControl=false,effectEnabled=false,playerPlaying=false;int effectSession=-1,playerSession=-1;long playerPosition=-1;
  if(e!=null){
   try{if(e.effect!=null){effectSession=e.effect.getId();effectControl=e.effect.hasControl();effectEnabled=e.effect.getEnabled();}}catch(RuntimeException ignored){}
   try{if(e.player!=null){playerSession=e.player.getAudioSessionId();playerPlaying=e.player.isPlaying();playerPosition=e.player.getCurrentPosition();}}catch(RuntimeException ignored){}
  }
  return LogStore.map("reason",reason,"processId",android.os.Process.myPid(),"serviceInstance",notificationRun,
   "serviceAgeMs",serviceCreatedAt<0?-1:now-serviceCreatedAt,"tickAgeMs",lastTickAt<0?-1:now-lastTickAt,
   "sampleAgeMs",lastSampleAt<0?-1:now-lastSampleAt,"mediaEventAgeMs",lastMediaEvent<=0?-1:now-lastMediaEvent,
   "tickCount",tickCount,"sampleCount",sampleCount,"controllerConnected",controllerConnected,
   "controllerPlaybackState",controllerState,"controllerPlaying",controllerPlaying,"controllerPositionMs",controllerPosition,
   "sourceAlias",s==null?null:s.alias,"sourcePlaying",s!=null&&s.playing,"deviceInteractive",screenInteractive(),"sourceAgeMs",s==null?-1:now-s.observed,
   "sourcePositionMs",s==null?-1:s.position,"replacementArmed",e!=null&&e.armed(),"replacementStatus",e==null?"":e.status,
   "replacementTrackId",e==null?null:e.trackId,"replacementReady",e!=null&&e.ready,"replacementPreparing",e!=null&&e.preparing,
   "replacementOwnerState",e==null?"NONE":e.audioOwner.state().name(),"trustedSessionId",e==null?-1:e.trustedSession,
   "effectSessionId",effectSession,"effectHasControl",effectControl,"effectEnabled",effectEnabled,
   "playerSessionId",playerSession,"playerIsPlaying",playerPlaying,"playerPositionMs",playerPosition,
   "lookupRetryRemainingMs",e==null?-1:Math.max(0,e.nextLookup-now),"wakeLockHeld",wake!=null&&wake.isHeld(),
   "networkAvailableAgeMs",lastNetworkAvailableAt<0?-1:now-lastNetworkAvailableAt,
   "networkLostAgeMs",lastNetworkLostAt<0?-1:now-lastNetworkLostAt);
 }

 /* A read-only platform MediaBrowser companion to the Media3 controller.
    It never sends play, pause, seek or queue commands. */
 void connectLegacyPosition(){
  if(!alive()||legacyBrowser!=null)return;
  try{
   final android.media.browse.MediaBrowser browser=new android.media.browse.MediaBrowser(
    this,new ComponentName(LogStore.PKG,"com.yandex.music.shared.media.session.session.Media3LibraryService"),
    new android.media.browse.MediaBrowser.ConnectionCallback(){
     @Override public void onConnected(){
      if(!alive()||legacyBrowser==null||!legacyBrowser.isConnected())return;
      try{
       legacyController=new android.media.session.MediaController(ProbeService.this,legacyBrowser.getSessionToken());
       LogStore.log("legacy_position_source_connected",LogStore.map("passive",true,"transportCommandsSent",false));
      }catch(RuntimeException ex){legacyController=null;LogStore.log("legacy_position_source_unavailable",LogStore.map("stage","controller","type",ex.getClass().getSimpleName()));}
     }
     @Override public void onConnectionFailed(){legacyController=null;LogStore.log("legacy_position_source_unavailable",LogStore.map("stage","browser_connect","transportCommandsSent",false));}
     @Override public void onConnectionSuspended(){legacyController=null;LogStore.log("legacy_position_source_unavailable",LogStore.map("stage","browser_suspended","transportCommandsSent",false));}
    },null);
   legacyBrowser=browser;browser.connect();
  }catch(RuntimeException ex){legacyBrowser=null;legacyController=null;LogStore.log("legacy_position_source_unavailable",LogStore.map("stage","browser_create","type",ex.getClass().getSimpleName()));}
 }
 LegacySourcePositionPolicy.Decision legacyPosition(String alias,String title,String artist,long duration,long mediaPosition,boolean playing){
  final long now=SystemClock.elapsedRealtime();
  android.media.session.MediaController observer=legacyController;
  if(observer==null)return legacyPositionPolicy.unavailable(alias);
  try{
   android.media.MediaMetadata metadata=observer.getMetadata();
   android.media.session.PlaybackState state=observer.getPlaybackState();
   if(metadata==null||state==null)return legacyPositionPolicy.unavailable(alias);
   String platformTitle=metadata.getString(android.media.MediaMetadata.METADATA_KEY_TITLE);
   String platformArtist=metadata.getString(android.media.MediaMetadata.METADATA_KEY_ARTIST);
   long platformDuration=metadata.getLong(android.media.MediaMetadata.METADATA_KEY_DURATION);
   long platformAge=now-state.getLastPositionUpdateTime();
   long platformPosition=state.getPosition();
   boolean platformPlaying=state.getState()==android.media.session.PlaybackState.STATE_PLAYING;
   if(platformPosition>=0&&platformAge>=0&&platformAge<=30000&&platformPlaying){
    float speed=state.getPlaybackSpeed();
    if(Float.isFinite(speed)&&speed>0.5f&&speed<1.5f)
     platformPosition+=Math.round(platformAge*speed);
   }
   LegacySourcePositionPolicy.Decision decision=legacyPositionPolicy.reconcile(
    alias,title,artist,duration,mediaPosition,playing,
    platformTitle,platformArtist,platformDuration,platformPosition,platformAge,platformPlaying,now);
   if((decision.newRecovery||decision.failClosed||decision.candidate)&&
      (decision.newRecovery||lastLegacyDiagnosticAt<0||now-lastLegacyDiagnosticAt>=5000)){
    lastLegacyDiagnosticAt=now;
    LogStore.log(decision.newRecovery?"source_seek_platform_recovered":
      decision.failClosed?"source_seek_platform_fallback_lost":"source_seek_platform_disagreement",
      LogStore.map("alias",alias,"media3PositionMs",mediaPosition,"platformPositionMs",platformPosition,
       "platformStateAgeMs",platformAge,"sameTrack",LegacySourcePositionPolicy.sameTrack(
        title,artist,duration,platformTitle,platformArtist,platformDuration),
       "platformPlaying",platformPlaying,"transportCommandsSent",false,"passive",true));
   }
   return decision;
  }catch(RuntimeException ex){
   LogStore.log("legacy_position_source_unavailable",LogStore.map("stage","snapshot","type",ex.getClass().getSimpleName()));
   return legacyPositionPolicy.unavailable(alias);
  }
 }
 void disconnectLegacyPosition(){
  legacyController=null;
  if(legacyBrowser!=null)try{legacyBrowser.disconnect();}catch(RuntimeException ignored){}
  legacyBrowser=null;
 }

 /* Short post-prepare source polling avoids a full periodic-tick wait at the cold join.
    It never seeks, controls Yandex, or grants audio permission. */
 boolean fastJoinSampling;long fastJoinDeadlineMs;
 void requestFastJoinSamples(){
  if(!alive()||replacement==null||!replacement.armed())return;
  fastJoinDeadlineMs=SystemClock.elapsedRealtime()+FastJoinPollPolicy.BUDGET_MS;
  if(fastJoinSampling)return;
  fastJoinSampling=true;
  LogStore.log("replacement_fast_join_poll_started",LogStore.map("maxMs",FastJoinPollPolicy.BUDGET_MS,"stepMs",FastJoinPollPolicy.STEP_MS,"audioCommandSent",false));
  handler.postDelayed(new Runnable(){public void run(){
   ReplacementEngine engine=replacement;
   long now=SystemClock.elapsedRealtime();
   boolean eligible=engine!=null&&FastJoinPollPolicy.eligible(
    alive(),now,fastJoinDeadlineMs,engine.armed(),engine.player!=null,engine.ready,
    engine.effect!=null,engine.trustedSession>0,current!=null&&current.playing,
    current!=null&&Objects.equals(engine.identityKey,current.key));
   if(!eligible){fastJoinSampling=false;return;}
   sample(false);
   if(!alive()||replacement!=engine||engine.effect!=null){fastJoinSampling=false;return;}
   handler.postDelayed(this,FastJoinPollPolicy.STEP_MS);
  }},FastJoinPollPolicy.INITIAL_MS);
 }

 void sample(boolean event){if(!alive())return;lastSampleAt=SystemClock.elapsedRealtime();sampleCount++;String outputs=route();if(!outputs.equals(lastRoutes)){lastRoutes=outputs;LogStore.log("audio_outputs_changed",LogStore.map("availableOutputTypes",outputs,"activeSourceRouteKnown",false));}androidx.media3.session.MediaController c=controller;if(c==null||!c.isConnected()){if(c!=null){controller=null;c.release();}connect();current=null;if(replacement!=null)replacement.update(null);return;}try{MediaItem item=c.getCurrentMediaItem();if(item==null){current=null;replacement.update(null);long now=SystemClock.elapsedRealtime();if(emptySince<0)emptySince=now;if(now-emptySince>=5000){controller=null;c.release();emptySince=-1;connect();}return;}
   int nativeState=c.getPlaybackState();MediaMetadata m=item.mediaMetadata;String title=m.title==null?"":m.title.toString(),artist=m.artist==null?"":m.artist.toString(),cover=m.artworkUri==null?null:m.artworkUri.toString();long duration=c.getDuration();
   boolean usable=nativeState!=Player.STATE_ENDED&&nativeState!=Player.STATE_IDLE&&duration>0&&!title.trim().isEmpty();
   int gate=transitionGate.sample(usable?item.mediaId:null,SystemClock.elapsedRealtime());
   if(gate==SourceTransitionGate.WAIT){current=null;replacement.update(null);return;}
   if(gate==SourceTransitionGate.REFRESH){LogStore.log("source_controller_refresh",LogStore.map("reason","transition_alias_timeout","expectedAlias",transitionGate.expected,"actualAlias",item.mediaId,"nativeState",nativeState,"metadataUsable",usable));transitionGate.clear();replacement.sourceBoundary("transition_alias_timeout",item.mediaId);current=null;controller=null;c.release();connect();return;}
   if(nativeState==Player.STATE_ENDED||nativeState==Player.STATE_IDLE){if(current!=null||replacement.player!=null)sourceBoundary(null,"native_stopped");current=null;replacement.update(null);return;}
   long observedNow=SystemClock.elapsedRealtime();
   if(stateWatchdog.refresh(item.mediaId,nativeState,c.isPlaying(),observedNow-lastMediaEvent,observedNow)){
    LogStore.log("source_controller_refresh",LogStore.map("reason","quiet_buffering_snapshot","alias",item.mediaId,"nativeState",nativeState,"playWhenReady",c.getPlayWhenReady(),"suppressionReason",c.getPlaybackSuppressionReason(),"positionMs",c.getCurrentPosition(),"mediaEventAgeMs",observedNow-lastMediaEvent,"transportCommandSent",false));
    current=null;controller=null;stateWatchdog.reset();replacement.update(null);c.release();connect();return;
   }
   emptySince=-1;if(duration<=0||title.trim().isEmpty()){current=null;replacement.update(null);return;}long sampledPosition=c.getCurrentPosition();boolean fenced=sessionRecheck.awaitingFreshSource;if(!sessionRecheck.accept(item.mediaId,sampledPosition,observedNow)){current=null;replacement.update(null);return;}if(fenced)LogStore.log("source_controller_freshness_confirmed",LogStore.map("reason","new_controller_metadata","alias",item.mediaId,"positionMs",sampledPosition,"audioCommandSent",false));if(sourceItemAlias==null||(current==null&&!Objects.equals(sourceItemAlias,item.mediaId))){sourceItemGeneration++;sourceItemAlias=item.mediaId;}LegacySourcePositionPolicy.Decision legacy=legacyPosition(item.mediaId,title,artist,duration,sampledPosition,c.isPlaying());if(legacy.failClosed){if(!legacyPositionUnsafeLogged){legacyPositionUnsafeLogged=true;LogStore.log("source_seek_platform_fail_closed",LogStore.map("alias",item.mediaId,"originalRetained",true));}replacement.suspend("legacy_position_unverified",2000);replacement.update(null);return;}legacyPositionUnsafeLogged=false;if(legacy.newRecovery)replacement.sourceSeekRequested();PlaybackSource previous=current;current=new PlaybackSource(item.mediaId,title,artist,duration,cover,legacy.override?legacy.position:sampledPosition,c.isPlaying(),c.getDeviceInfo().playbackType==DeviceInfo.PLAYBACK_TYPE_LOCAL,c.getPlaybackParameters().speed,c.getPlayWhenReady(),nativeState==Player.STATE_BUFFERING);sourceTransitionExpectedAlias=null;if(previous!=null&&!previous.key.equals(current.key)){reportLookahead(current.alias,"sample_track_changed");replacement.sourceChanged(previous,current);}
   else if(previous!=null&&SourceTransitionGate.outgoingItemReset(previous.alias,current.alias,previous.position,previous.duration,current.position,previous.playing,current.playing,c.getPlayWhenReady(),nativeState==Player.STATE_BUFFERING))
      replacement.outgoingTrackReset(previous);
   albumProbe.observe(item.mediaId,title,artist,duration,cover);
   // Prioritize the audible song before speculative successor metadata.
   sampleLookahead(c,item);
   // Cached observations must still publish a decision when a previously seen song returns.
   albumProbe.publishCurrent();replacement.update(current);replacement.noteLookaheadCandidate(lookahead.next);
   long clock=SystemClock.elapsedRealtime();
   if(current.playing&&current.duration>0&&current.position>=current.duration){if(endReachedAt<0)endReachedAt=clock;if(clock-endReachedAt>=2000){LogStore.log("source_controller_refresh",LogStore.map("reason","item_stuck_at_end","alias",current.alias,"positionMs",current.position,"durationMs",current.duration));replacement.sourceBoundary("controller_stuck_at_end",null);current=null;controller=null;c.release();endReachedAt=-1;connect();return;}}else endReachedAt=-1;
   if(clock-lastHealth>=5000){lastHealth=clock;LogStore.log("playback_health",LogStore.map("alias",current.alias,"sourcePositionMs",current.position,"durationMs",current.duration,"sourcePlaying",current.playing,"nativeState",nativeState,"playWhenReady",c.getPlayWhenReady(),"suppressionReason",c.getPlaybackSuppressionReason(),"mediaEventAgeMs",clock-lastMediaEvent,"replacementReady",replacement.ready,"replacementPreparing",replacement.preparing,"replacementArmed",replacement.armed(),"trackId",replacement.trackId,"method",replacement.method));}
   String key=current.key+"|"+c.isPlaying()+"|"+c.getPlaybackState()+"|"+c.getPlaybackParameters().speed;if(!key.equals(lastStateKey)||SystemClock.elapsedRealtime()-lastState>=10000){lastStateKey=key;lastState=SystemClock.elapsedRealtime();LogStore.log("player_state",LogStore.map("mediaAlias",item.mediaId,"title",title,"artist",artist,"durationMs",duration,"albumId",current.albumId,"positionMs",current.position,"isPlaying",current.playing,"playbackState",c.getPlaybackState(),"playWhenReady",c.getPlayWhenReady(),"suppressionReason",c.getPlaybackSuppressionReason(),"speed",current.speed,"interactive",getSystemService(PowerManager.class).isInteractive(),"availableOutputTypes",route()));}
  }catch(RuntimeException e){current=null;replacement.suspend("source_sample_failed",2000);if(LogStore.active)LogStore.log("player_sample_failure",LogStore.map("type",e.getClass().getSimpleName(),"controllerPresent",controller!=null,"controllerConnected",controller!=null&&controller.isConnected(),"mediaEventAgeMs",lastMediaEvent<=0?-1:SystemClock.elapsedRealtime()-lastMediaEvent));LogStore.error("player_sample",e);}}
 void sourceBoundary(String nextAlias,String reason){if(!alive()||replacement==null)return;if(!transitionGate.begin(nextAlias,SystemClock.elapsedRealtime()))return;sourceTransitionExpectedAlias=nextAlias;lastMediaEvent=SystemClock.elapsedRealtime();replacement.sourceBoundary(reason,nextAlias);reportLookahead(nextAlias,reason);current=null;lastStateKey="";endReachedAt=-1;}
 void noteSourceBoundary(String nextAlias){sourceItemGeneration++;sourceItemAlias=nextAlias;}
 /* Read-only Media3 next-item feasibility. No audio, API or prefetch operations. */
 void sampleLookahead(androidx.media3.session.MediaController c,MediaItem item){
  long now=SystemClock.elapsedRealtime(),elapsed=now-lastLookaheadPoll;String active=item==null?null:item.mediaId;
  if(Objects.equals(lastLookaheadSource,active)&&elapsed<500)return;
  lastLookaheadSource=active;lastLookaheadPoll=now;
  boolean timeline=false,metadata=false,placeholder=true,strictAlbumMetadata=false,identityMetadata=false,stableFallback=false;
  String candidate=null,title="",artist="",cover=null,albumId=null,durationSource="unavailable",metadataSource="incomplete_identity_metadata";
  long metadataDuration=-1,windowDuration=-1,duration=-1;
  try{
   timeline=c!=null&&c.isConnected()&&c.isCommandAvailable(Player.COMMAND_GET_TIMELINE);
   if(timeline){
    int next=c.getNextMediaItemIndex(),count=c.getMediaItemCount();Timeline currentTimeline=c.getCurrentTimeline();
    if(next>=0&&next<count&&currentTimeline!=null&&next<currentTimeline.getWindowCount()){
     Timeline.Window window=new Timeline.Window();currentTimeline.getWindow(next,window);
     MediaItem future=window.mediaItem!=null?window.mediaItem:c.getMediaItemAt(next);
     if(future!=null){
      candidate=future.mediaId;MediaMetadata m=future.mediaMetadata;
      if(m!=null){title=m.title==null?"":m.title.toString();artist=m.artist==null?"":m.artist.toString();cover=m.artworkUri==null?null:m.artworkUri.toString();if(m.durationMs!=null)metadataDuration=m.durationMs;}
      placeholder=window.isPlaceholder;windowDuration=window.getDurationMs();
      if(metadataDuration>0){duration=metadataDuration;durationSource="media_metadata";}else if(windowDuration>0){duration=windowDuration;durationSource="timeline_window";}
      albumId=AlbumMatch.albumId(cover);
     }
    }
   }
  }catch(RuntimeException ignored){timeline=false;candidate=null;title="";artist="";cover=null;albumId=null;duration=-1;durationSource="unavailable";placeholder=true;metadataDuration=-1;windowDuration=-1;}
  identityMetadata=LookaheadPrefetchPolicy.identityMetadataAvailable(candidate,title,artist,duration);
  if(identityMetadata){
   String metadataKey=candidate+"|"+title+"|"+artist+"|"+albumId+"|"+duration+"|"+placeholder;
   if(metadataKey.equals(lastLookaheadMetadataSignature))lookaheadMetadataSamples=Math.min(lookaheadMetadataSamples+1,1000);
   else{lastLookaheadMetadataSignature=metadataKey;lookaheadMetadataSamples=1;}
  }else{lastLookaheadMetadataSignature="";lookaheadMetadataSamples=0;}
  strictAlbumMetadata=LookaheadPrefetchPolicy.metadataComplete(candidate,title,artist,albumId,duration,placeholder);
  stableFallback=LookaheadPrefetchPolicy.stableMetadataFallbackReady(candidate,title,artist,duration,lookaheadMetadataSamples);
  metadata=strictAlbumMetadata||stableFallback;
  if(strictAlbumMetadata)metadataSource="strict_album_metadata";
  else if(stableFallback)metadataSource=albumId==null?"stable_metadata_without_album_id":placeholder?"stable_placeholder_metadata":"stable_metadata_fallback";
  else if(identityMetadata)metadataSource="awaiting_stable_metadata";
  observedNextAlias=candidate;
  if(!Objects.equals(lastLookaheadCandidate,candidate)){lastLookaheadCandidate=candidate;lastLookaheadSignature="";}
  boolean changed=lookahead.observe(active,candidate,metadata,timeline,now);
  if(replacement!=null)replacement.noteLookaheadCandidate(candidate);
  if(changed)LogStore.log("source_next_readonly_observation",LogStore.map(
    "sourceEventSequence",sourceEventSequence,"sourceItemGeneration",sourceItemGeneration,
    "timelineAvailable",timeline,"candidateIdPresent",candidate!=null&&!candidate.isEmpty(),
    "candidateDistinct",candidate!=null&&!Objects.equals(active,candidate),
    "titlePresent",!title.trim().isEmpty(),"artistPresent",!artist.trim().isEmpty(),
    "albumIdPresent",albumId!=null,"metadataDurationPresent",metadataDuration>0,
    "windowDurationPresent",windowDuration>0,"durationSource",durationSource,
    "windowPlaceholder",placeholder,"identityMetadataAvailable",identityMetadata,
    "metadataStableSamples",lookaheadMetadataSamples,"metadataSource",metadataSource,
    "metadataComplete",metadata,"audioCommandSent",false,
    "prefetchStarted",replacement!=null&&replacement.lookaheadPrefetchStarted(candidate)));
  PlaybackSource source=current;long remaining=source==null?-1:Math.max(0,source.duration-source.position);
  boolean eligible=LookaheadPrefetchPolicy.mayResolve(replacement!=null&&replacement.armed(),
    NativeApi.get(this).signedIn(),source!=null&&source.playing,timeline,
    candidate!=null&&!candidate.isEmpty()&&!Objects.equals(active,candidate),metadata,remaining);
  if(eligible&&albumProbe!=null){
   String signature=candidate+"|"+title+"|"+artist+"|"+duration+"|"+cover;
   if(!signature.equals(lastLookaheadSignature)){lastLookaheadSignature=signature;albumProbe.observeLookahead(candidate,title,artist,duration,cover);}
  }else if(candidate==null)lastLookaheadSignature="";
 }
 void reportLookahead(String next,String reason){
  SourceEventArbiter.LookaheadEvidence.Verdict v=lookahead.boundary(next,SystemClock.elapsedRealtime());
  if(v.observed)LogStore.log("source_next_readonly_boundary",LogStore.map("sourceEventSequence",sourceEventSequence,"sourceItemGeneration",sourceItemGeneration,"reason",reason,"predicted",v.predicted,"matched",v.matched,"metadataComplete",v.complete,"leadMs",v.leadMs,"samples",v.samples,"authorizedForPrefetch",v.predicted&&v.matched&&v.complete&&v.leadMs>=LookaheadPrefetchPolicy.MIN_LEAD_MS,"prefetchStarted",replacement!=null&&replacement.lookaheadPrefetchStarted(next),"prefetchState",replacement==null?"none":replacement.lookaheadPrefetchState(next),"audioCommandSent",false));
}
 boolean lookaheadIsNext(String alias){
  if(!alive()||alias==null||alias.trim().isEmpty())return false;PlaybackSource source=current;
  return source!=null&&!Objects.equals(source.alias,alias)&&Objects.equals(observedNextAlias,alias)&&sourceTransitionExpectedAlias==null;
 }
 boolean lookaheadCandidateCurrent(String alias){
  if(alias==null||alias.trim().isEmpty())return false;PlaybackSource source=current;
  if(source!=null&&Objects.equals(source.alias,alias))return true;String expected=sourceTransitionExpectedAlias;
  if(expected!=null)return Objects.equals(expected,alias);
  return source!=null&&Objects.equals(observedNextAlias,alias);
 }

 String route(){try{android.media.AudioDeviceInfo[] a=getSystemService(AudioManager.class).getDevices(AudioManager.GET_DEVICES_OUTPUTS);List<Integer> types=new ArrayList<>();for(android.media.AudioDeviceInfo d:a)if(!types.contains(d.getType()))types.add(d.getType());return types.toString();}catch(RuntimeException e){return "unknown";}}
 void pauseForRouteLoss(){androidx.media3.session.MediaController c=controller;boolean sent=false;try{if(c!=null&&c.isConnected()&&c.isCommandAvailable(Player.COMMAND_PLAY_PAUSE)){c.pause();sent=true;}}catch(RuntimeException e){LogStore.error("route_pause_request",e);}LogStore.log("source_pause_requested",LogStore.map("reason","headphones_disconnected","sent",sent));sample(true);}
 void onIdentity(Map<String,Object> observation,Map<String,Object> decision){if(replacement==null)return;String key=PlaybackSource.key(String.valueOf(observation.get("mediaAlias")),observation.get("albumId"),String.valueOf(observation.get("title")),String.valueOf(observation.get("artist")),((Number)observation.get("durationMs")).longValue());if(Objects.equals(key,replacement.identityKey)&&Objects.equals(decision.get("candidateTrackId"),replacement.trackId)&&Objects.equals(String.valueOf(decision.get("method")),replacement.method))return;replacement.identity(observation,decision);}
 void beginTrial(){if(replacement==null)return;stopService(new Intent().setClassName(this,"pro.celikom.nativeprobe.AttenuationService"));if(Build.VERSION.SDK_INT>=34)try{startForeground(220,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE|ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK);}catch(RuntimeException e){replacement.status="Android не разрешил запустить воспроизведение";return;}replacement.arm();}
 static void refreshSessions(){ProbeService p=instance;if(p!=null)p.handler.post(p::sampleNow);}
 void sampleNow(){sample(true);}
 void finish(String reason){if(stopping)return;if(LogStore.active){Map<String,Object> state=runtimeSnapshot("service_finish_requested");state.put("finishReason",reason);LogStore.log("service_finish_requested",state);}stopping=true;if(sourceProbe!=null)sourceProbe.cancel(false);stopPlaybackActivityObserver();handler.removeCallbacksAndMessages(null);if(wake!=null&&wake.isHeld())wake.release();if(replacement!=null)replacement.close();if(albumProbe!=null)albumProbe.close();LogStore.end(reason);stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}
 public void onTaskRemoved(Intent root){if(LogStore.active){Map<String,Object> state=runtimeSnapshot("task_removed");LogStore.log("service_task_removed",state);}LogStore.log("task_removed","foreground playback retained until explicit Stop or Android service destruction");}
 public void onDestroy(){if(LogStore.active){Map<String,Object> state=runtimeSnapshot("service_destroying");LogStore.log("service_destroying",state);}stopping=true;stopPlaybackActivityObserver();if(replacement!=null)replacement.close();if(albumProbe!=null)albumProbe.close();LogStore.end("service_destroyed");if(networkRegistered)try{connectivity.unregisterNetworkCallback(networkCallback);}catch(RuntimeException ignored){}handler.removeCallbacksAndMessages(null);disconnectLegacyPosition();if(connecting!=null)connecting.cancel(false);if(controller!=null)controller.release();controller=null;current=null;if(receiverRegistered)try{unregisterReceiver(audio);}catch(RuntimeException ignored){}if(wake!=null&&wake.isHeld())wake.release();if(instance==this)instance=null;super.onDestroy();}
}
