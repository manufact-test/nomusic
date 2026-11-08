package pro.celikom.nativeprobe.identitydiag;

import android.app.Service;
import android.content.ComponentName;
import android.media.MediaMetadata;
import android.media.session.MediaController;
import android.media.session.MediaSessionManager;
import android.media.session.PlaybackState;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.service.notification.NotificationListenerService;

import java.util.List;
import java.util.Objects;

import androidx.media3.common.MediaItem;
import androidx.media3.common.Player;

/**
 * Test.74: explicitly enabled, READ-ONLY independent framework MediaSession
 * witness for exactly ru.yandex.music. Android's Notification Access setting
 * is required; this class NEVER reads notification content, and has NO
 * onNotificationPosted/onNotificationRemoved override or transport commands.
 *
 * Diagnostic only: NO result from here can authorize, pause, seek, change
 * volume, or select a CELIKOM replacement.
 */
public final class YandexSessionWitnessService extends NotificationListenerService {
 static volatile YandexSessionWitnessService live;
 static volatile MediaController yandex;
 static volatile int yandexSessionCount;
 private static long lastSampleAt;
 private final Handler main=new Handler(Looper.getMainLooper());
 private MediaSessionManager sessions;
 private MediaController subscribed;
 private int generation;
 private final MediaSessionManager.OnActiveSessionsChangedListener changed = list -> main.post(()->bind(list));
 private final MediaController.Callback callback=new MediaController.Callback(){
  @Override public void onPlaybackStateChanged(PlaybackState state){
   if(LogStore.active)LogStore.log("yandex_witness_playback_callback",LogStore.map(
    "generation",generation,"state",state==null?-1:state.getState(),
    "rawPositionMs",state==null?-1:state.getPosition(),
    "lastUpdateElapsedMs",state==null?-1:state.getLastPositionUpdateTime(),
    "observerOnly",true,"audioCommandSent",false));
  }
  @Override public void onMetadataChanged(MediaMetadata md){
   if(LogStore.active)LogStore.log("yandex_witness_metadata_callback",LogStore.map(
     "generation",generation,
     "title",md==null?null:md.getString(MediaMetadata.METADATA_KEY_TITLE),
     "artist",md==null?null:md.getString(MediaMetadata.METADATA_KEY_ARTIST),
     "durationMs",md==null?-1:md.getLong(MediaMetadata.METADATA_KEY_DURATION),
     "observerOnly",true,"audioCommandSent",false));
  }
  @Override public void onSessionDestroyed(){
   if(LogStore.active)LogStore.log("yandex_witness_session_destroyed",LogStore.map(
    "generation",generation,"observerOnly",true));
   main.post(()->refresh());
  }
 };
 @Override public void onListenerConnected(){
  super.onListenerConnected();
  live=this;
  try{
   sessions=(MediaSessionManager)getSystemService(Service.MEDIA_SESSION_SERVICE);
   if(sessions==null)throw new IllegalStateException("media_session_manager_unavailable");
   ComponentName component=new ComponentName(this,YandexSessionWitnessService.class);
   sessions.addOnActiveSessionsChangedListener(changed,component,main);
   refresh();
   if(LogStore.active)LogStore.log("yandex_witness_permission",LogStore.map(
     "enabled",true,"scope","Yandex media session only; no notification text",
     "observerOnly",true,"audioCommandSent",false));
  }catch(SecurityException | IllegalStateException e){
   if(LogStore.active)LogStore.log("yandex_witness_unavailable",LogStore.map(
     "reason",e.getClass().getSimpleName(),"observerOnly",true));
   detach();
  }
 }
 @Override public void onListenerDisconnected(){detach();super.onListenerDisconnected();}
 @Override public void onDestroy(){detach();super.onDestroy();}
 private void refresh(){
  try{
   if(live!=this||sessions==null)return;
   bind(sessions.getActiveSessions(new ComponentName(this,YandexSessionWitnessService.class)));
  }catch(SecurityException e){
   if(LogStore.active)LogStore.log("yandex_witness_unavailable",LogStore.map(
      "reason","permission_revoked","observerOnly",true));
   bind(null);
  }
 }
 private void bind(List<MediaController> list){
  if(live!=this)return;
  MediaController next=null;int count=0;
  if(list!=null)for(MediaController c:list){
   if(c!=null && Objects.equals(c.getPackageName(),LogStore.PKG)){
    count++;
    if(next==null)next=c;
   }
  }
  yandexSessionCount=count;
  if(next==subscribed)return;
  if(subscribed!=null)try{subscribed.unregisterCallback(callback);}catch(RuntimeException ignored){}
  subscribed=next;yandex=next;generation++;
  if(next!=null)next.registerCallback(callback,main);
  if(LogStore.active)LogStore.log("yandex_witness_session_selected",LogStore.map(
    "generation",generation,"yandexSessions",count,"available",next!=null,
    "selection","top-priority Yandex only; other packages ignored",
    "observerOnly",true,"audioCommandSent",false));
 }
 private void detach(){
  if(live!=this)return;
  if(sessions!=null)try{sessions.removeOnActiveSessionsChangedListener(changed);}catch(RuntimeException ignored){}
  if(subscribed!=null)try{subscribed.unregisterCallback(callback);}catch(RuntimeException ignored){}
  subscribed=null;sessions=null;yandex=null;yandexSessionCount=0;live=null;generation++;
 }
 private static Object boolExtra(Bundle extras,String name){
  if(extras==null||!extras.containsKey(name))return null;
  Object value=extras.get(name);
  return value instanceof Boolean?value:null;
 }
 private static boolean same(String a,String b){
  return a!=null&&b!=null&&!a.trim().isEmpty()&&a.trim().equalsIgnoreCase(b.trim());
 }
 /**
  * Passive comparison: called only AFTER the ordinary Test.73 playback
  * observer/update, never supplying values back to ReplacementEngine.
  */
 static void sample(androidx.media3.session.MediaController remote,PlaybackSource source){
  if(!LogStore.active||source==null)return;
  long now=SystemClock.elapsedRealtime();
  if(now-lastSampleAt<500)return;
  lastSampleAt=now;
  YandexSessionWitnessService service=live;
  MediaController platform=yandex;
  long remotePos=source.position;
  if(service==null||platform==null){
   LogStore.log("yandex_witness_sample",LogStore.map(
    "enabled",service!=null,"available",platform!=null,
    "yandexSessions",yandexSessionCount,
    "alias",source.alias,"title",source.title,
    "remoteMedia3Playing",source.playing,"remoteMedia3PositionMs",remotePos,
    "observerOnly",true,"audioCommandSent",false));
   return;
  }
  try{
   PlaybackState state=platform.getPlaybackState();
   MediaMetadata metadata=platform.getMetadata();
   long raw=state==null?-1:state.getPosition();
   long age=state==null?-1:now-state.getLastPositionUpdateTime();
   long projected=raw;
   if(state!=null&&state.getState()==PlaybackState.STATE_PLAYING&&age>=0&&age<=20000
      &&state.getPlaybackSpeed()>0&&state.getPlaybackSpeed()<3)
    projected=raw+Math.round(age*state.getPlaybackSpeed());
   String name=metadata==null?null:metadata.getString(MediaMetadata.METADATA_KEY_TITLE);
   String artist=metadata==null?null:metadata.getString(MediaMetadata.METADATA_KEY_ARTIST);
   long duration=metadata==null?-1:metadata.getLong(MediaMetadata.METADATA_KEY_DURATION);
   MediaItem current=remote==null?null:remote.getCurrentMediaItem();
   Bundle extras=current==null?null:current.mediaMetadata.extras;
   Object seekable=boolExtra(extras,"com.yandex.music.media.metadata.seekable");
   Object dynamic=boolExtra(extras,"com.yandex.music.media.metadata.dynamic");
   Object liveFlag=boolExtra(extras,"com.yandex.music.media.metadata.live");
   LogStore.log("yandex_witness_sample",LogStore.map(
     "enabled",true,"available",true,"yandexSessions",yandexSessionCount,
     "alias",source.alias,"title",source.title,"artist",source.artist,
     "remoteMedia3Playing",source.playing,
     "remoteMedia3PositionMs",remotePos,
     "remoteMedia3WantsToPlay",source.wantsToPlay,
     "remoteSeekCommandAvailable",remote!=null&&remote.isCommandAvailable(Player.COMMAND_SEEK_IN_CURRENT_MEDIA_ITEM),
     "remotePauseCommandAvailable",remote!=null&&remote.isCommandAvailable(Player.COMMAND_PLAY_PAUSE),
     "metadataSeekable",seekable,"metadataDynamic",dynamic,"metadataLive",liveFlag,
     "witnessTitle",name,"witnessArtist",artist,"witnessDurationMs",duration,
     "witnessTitleMatches",same(source.title,name),
     "witnessState",state==null?-1:state.getState(),
     "witnessPlaying",state!=null&&state.getState()==PlaybackState.STATE_PLAYING,
     "witnessRawPositionMs",raw,"witnessProjectedPositionMs",projected,
     "witnessStateAgeMs",age,
     "observerOnly",true,"audioCommandSent",false));
  }catch(RuntimeException e){
   LogStore.log("yandex_witness_unavailable",LogStore.map(
     "reason",e.getClass().getSimpleName(),"observerOnly",true,"audioCommandSent",false));
  }
 }
}
