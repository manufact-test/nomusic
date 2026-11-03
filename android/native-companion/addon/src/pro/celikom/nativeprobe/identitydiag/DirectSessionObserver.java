package pro.celikom.nativeprobe.identitydiag;
import android.content.*;
import android.os.SystemClock;
import androidx.media3.common.MediaItem;
import androidx.media3.session.MediaController;
import androidx.media3.session.SessionToken;
import com.google.common.util.concurrent.ListenableFuture;
import java.util.*;

/* Opt-in diagnostic scope: the two owner-reported Yandex tracks.
   The independent controller never issues any transport or player command. */
final class DirectSessionObserver {
 final ProbeService owner;
 final LinkedHashSet<String> attempted=new LinkedHashSet<>();
 MediaController independent;
 ListenableFuture<MediaController> connecting;
 String alias;
 long startedAt,lastReportedAt,firstEligibleAt;String firstEligibleAlias;
 boolean servicesLogged;
 DirectSessionObserver(ProbeService owner){this.owner=owner;}
 void close(){
  MediaController old=independent;independent=null;
  ListenableFuture<MediaController> pending=connecting;connecting=null;
  alias=null;
  if(old!=null)old.release();
  if(pending!=null)MediaController.releaseFuture(pending);
 }
 void observe(MediaController primary,MediaItem current,String trackId){
  if(current==null||primary==null||!primary.isConnected()){close();return;}
  String liveAlias=current.mediaId;
  if(alias!=null&&(!Objects.equals(alias,liveAlias)||owner.controller!=primary))close();
  if(!"39949113".equals(trackId)&&!"42884423".equals(trackId))return;
  long now=SystemClock.elapsedRealtime();
  if(!Objects.equals(firstEligibleAlias,liveAlias)){firstEligibleAlias=liveAlias;firstEligibleAt=now;}
  /* Diagnostic binder/service discovery must not contend with a new song's first chord. */
  if(now-firstEligibleAt<4000)return;
  if(independent==null&&connecting==null&&!attempted.contains(liveAlias))begin(primary,liveAlias,trackId,now);
  if(independent==null||now-lastReportedAt<500)return;
  if(now-startedAt>75000){close();return;}
  lastReportedAt=now;
  try{
   if(!independent.isConnected()){close();return;}
   MediaItem other=independent.getCurrentMediaItem();
   long mainPosition=primary.getCurrentPosition(),secondPosition=independent.getCurrentPosition();
   boolean mainPlaying=primary.isPlaying(),secondPlaying=independent.isPlaying();
   SourceSessionSnapshotPolicy.Verdict diff=SourceSessionSnapshotPolicy.compare(
    liveAlias,primary.getDuration(),mainPosition,mainPlaying,
    other==null?null:other.mediaId,independent.getDuration(),secondPosition,secondPlaying);
   LogStore.log("source_direct_session_comparison",LogStore.map(
    "trackId",trackId,"sourceAlias",liveAlias,"sameItem",diff.sameItem,
    "validPosition",diff.validPosition,"positionDeltaMs",diff.positionDeltaMs,
    "positionDisagrees",diff.positionDisagrees,"pauseDisagrees",diff.pauseDisagrees,
    "mainPositionMs",mainPosition,"directPositionMs",secondPosition,
    "mainPlaying",mainPlaying,"directPlaying",secondPlaying,
    "mainMediaEventAgeMs",Math.max(0,now-owner.lastMediaEvent),
    "action","diagnostic_only_no_seek_or_pause","transportCommandsSent",false));
  }catch(RuntimeException e){
   LogStore.log("source_direct_session_unavailable",LogStore.map(
    "reason","snapshot_failed","exceptionType",e.getClass().getSimpleName(),"transportCommandsSent",false));
   close();
  }
 }
 void begin(MediaController primary,String liveAlias,String trackId,long now){
  attempted.add(liveAlias);
  if(attempted.size()>12)attempted.remove(attempted.iterator().next());
  alias=liveAlias;startedAt=now;lastReportedAt=0;
  try{
   if(!servicesLogged){
    servicesLogged=true;
    try{
     for(SessionToken available:SessionToken.getAllServiceTokens(owner))
      if(LogStore.PKG.equals(available.getPackageName()))
       LogStore.log("source_public_media_service",LogStore.map(
        "serviceName",available.getServiceName(),"tokenType",available.getType(),
        "transportCommandsSent",false));
    }catch(RuntimeException e){
     LogStore.log("source_public_media_service_unavailable",LogStore.map(
      "exceptionType",e.getClass().getSimpleName(),"transportCommandsSent",false));
    }
   }
   SessionToken token=primary.getConnectedToken();
   if(token==null||token.getType()!=SessionToken.TYPE_SESSION
    ||!LogStore.PKG.equals(token.getPackageName())){
    LogStore.log("source_direct_session_unavailable",LogStore.map(
     "trackId",trackId,"reason","no_direct_same_package_token","transportCommandsSent",false));
    close();return;
   }
   LogStore.log("source_direct_session_connect",LogStore.map(
    "trackId",trackId,"tokenType",token.getType(),"samePackage",true,"transportCommandsSent",false));
   connecting=new MediaController.Builder(owner,token).setListener(new MediaController.Listener(){
    public void onDisconnected(MediaController controller){
     if(independent==controller){
      LogStore.log("source_direct_session_disconnected",LogStore.map("transportCommandsSent",false));
      close();
     }
    }
   }).buildAsync();
   final ListenableFuture<MediaController> future=connecting;
   owner.handler.postDelayed(()->{
    if(connecting==future&&!future.isDone()){
     LogStore.log("source_direct_session_unavailable",LogStore.map(
      "reason","connect_timeout","transportCommandsSent",false));
     close();
    }
   },8000);
   future.addListener(()->{
    if(connecting==future)connecting=null;
    try{
     MediaController connected=future.get();
     if(!owner.alive()||!Objects.equals(alias,liveAlias)||owner.controller!=primary){
      connected.release();return;
     }
     independent=connected;
     SessionToken connectedToken=connected.getConnectedToken();
     LogStore.log("source_direct_session_connected",LogStore.map(
      "trackId",trackId,"tokenType",connectedToken==null?-1:connectedToken.getType(),
      "transportCommandsSent",false));
    }catch(Exception e){
     if(owner.alive())LogStore.log("source_direct_session_unavailable",LogStore.map(
      "reason","connect_failed","exceptionType",e.getClass().getSimpleName(),"transportCommandsSent",false));
    }
   },owner.handler::post);
  }catch(RuntimeException e){
   LogStore.log("source_direct_session_unavailable",LogStore.map(
    "reason","connect_exception","exceptionType",e.getClass().getSimpleName(),"transportCommandsSent",false));
   close();
  }
 }
}
