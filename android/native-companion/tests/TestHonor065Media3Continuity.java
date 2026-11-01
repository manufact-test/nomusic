package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;
import java.io.File;
import java.util.*;

/** Regression from HONOR 0.3.65: actual production Media3 routing decisions
 * followed by real ReplacementEngine commands. This is a host replay, not
 * hardware playback capture or an Android MediaController instrumentation test.
 */
public final class TestHonor065Media3Continuity {
 static int assertions,boundaries,seeks;
 static Media3SourceRouter router;
 static void check(boolean condition,String message){assertions++;if(!condition)throw new AssertionError(message);}
 static void installRouter(){
  router=new Media3SourceRouter(new SourceEventArbiter(),new Media3SourceRouter.Sink(){
   public void boundary(String alias,String reason){boundaries++;TestEngine.e.sourceBoundary(reason);}
   public void seekRequested(){seeks++;TestEngine.e.sourceSeekRequested();}
  });
 }
 static void source(String alias,long position){TestEngine.p.current=TestEngine.source(alias,position,true);}
 static void advance(String alias,long delta){
  MediaPlayer player=TestEngine.e.player;
  SystemClock.now+=delta;
  if(player!=null&&player.playing)player.position+=delta;
  source(alias,TestEngine.p.current.position+delta);
  TestEngine.p.handler.drain();
 }
 static void preparedSong(String alias)throws Exception{
  ReplacementEngine engine=TestEngine.e;
  source(alias,1000);
  engine.identity(LogStore.map("mediaAlias",alias,"albumId","42","title","Песня","artist","Артист","durationMs",120000L),
     LogStore.map("candidateTrackId",alias,"method","ALBUM"));
  TestEngine.resolve();
  File file=File.createTempFile("honor065-cached-",".audio");
  TestEngine.api.downloaded.done(file,null);
  engine.player.prepared.onPrepared(engine.player);
  advance(alias,600); // verify decoder movement and source/decoder clock alignment
  advance(alias,ReplacementEngine.UNIFIED_JOIN_MS+20); // complete the unchanged complementary entry
  check(engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT&&engine.player.volume>0.99f,
    "track "+alias+" prepared and joined before scrub sequence");
 }
 static void next(String oldAlias,String nextAlias,int oldIndex,boolean automatic)throws Exception{
  MediaPlayer former=TestEngine.e.player;
  SourceEventArbiter.Action decision=router.discontinuity(oldAlias,nextAlias,oldAlias,nextAlias,
    oldIndex,oldIndex+1,0,0,0,automatic,!automatic);
  check(decision==SourceEventArbiter.Action.BOUNDARY,
     "both Next-as-SEEK and automatic item-index transitions are true boundaries");
  check(former.released&&former.volume==0f&&TestEngine.e.player==null,
     "real routing retires the previous decoder before a new track");
  check(!TestEngine.e.sourceSeekedThisTrack&&!TestEngine.e.pendingStreamScrubJoin
      &&!TestEngine.e.explicitSourceSeek,"new track has no inherited scrub state");
  check(router.mediaItem(nextAlias,nextAlias,nextAlias,false,0)==SourceEventArbiter.Action.IGNORE,
      "follow-up onMediaItemTransition does not release the just-prepared successor");
  check(router.discontinuity(nextAlias,nextAlias,oldAlias,nextAlias,oldIndex,oldIndex+1,
      0,0,0,false,true)==SourceEventArbiter.Action.IGNORE,
      "delayed old-item Media3 discontinuity cannot re-release successor");
  preparedSong(nextAlias);
 }
 static void cachedScrub(String alias,int index,int sourceIndex){
  ReplacementEngine engine=TestEngine.e;
  MediaPlayer player=engine.player;
  long target=10000L+index*13700L;
  player.asyncSeek=true;
  SourceEventArbiter.Action action=router.discontinuity(alias,alias,alias,alias,
     sourceIndex,sourceIndex,TestEngine.p.current.position,target,target,false,true);
  check(action==SourceEventArbiter.Action.SEEK,"live same-item Media3 seek accepted "+alias+"/"+index);
  source(alias,target);
  engine.update(TestEngine.p.current);
  check(engine.seeking,"real engine starts seek on latest source position "+alias+"/"+index);
  // 0.3.65 fails here: both Yandex and CELIKOM are commanded silent while
  // the source is still playing, even with an entirely cached replacement.
  check(engine.effect==null||engine.effect.gain>-0.01f||player.volume>0.001f,
    "RED 0.3.65: cached finger seek must never command both sources silent "+alias+"/"+index);
  SystemClock.now+=55;
  source(alias,target+55);
  player.seek.onSeekComplete(player);
  SystemClock.now+=65;player.position+=65;source(alias,target+120);
  TestEngine.p.handler.drain();
  check(engine.player==player&&!player.released,"same decoder survives cached seek "+alias+"/"+index);
 }
 static void actualMedia3Chain()throws Exception{
  TestEngine.playing();installRouter();advance("1",600);
  check(TestEngine.e.audioOwner.state()==AudioOwnership.State.REPLACEMENT,"natural initial song joined");
  next("1","2",5,false); // manual Next emitted as reason SEEK, changing item index
  for(int i=0;i<6;i++)cachedScrub("2",i,6);
  next("2","3",6,true); // natural next item, then more scrubs
  for(int i=0;i<6;i++)cachedScrub("3",i,7);
  check(boundaries==2&&seeks==12,"exact Media3 event route counts, no duplicate boundaries");
  check(Collections.frequency(LogStore.events,"audio_command_anomaly")==0,
      "no >=40ms commanded gaps or overlaps across both cached seek sequences");
  TestEngine.e.close();
 }
 static void partiallyCachedScrubsNeverRestartColdDip()throws Exception{
  TestStreamingEngine.Buffer incomplete=TestStreamingEngine.start();
  ReplacementEngine engine=TestEngine.e;
  advance("1",600);
  advance("1",600); // first advancement validated the streaming clock and started the cold dip
  check(!incomplete.complete()&&engine.player.volume>0.99f,
    "stream remains incomplete after first join: volume="+engine.player.volume+
    " fading="+engine.fading+" state="+engine.audioOwner.state());
  MediaPlayer player=engine.player;player.asyncSeek=true;
  int before=Collections.frequency(LogStore.events,"replacement_exclusive_dip_start");
  for(int i=0;i<3;i++){
   engine.sourceSeekRequested();long target=24000+i*13000;
   source("1",target);engine.update(TestEngine.p.current);
   check(engine.seeking,"partial-stream seek must retain decoder");
   SystemClock.now+=60;source("1",target+60);player.seek.onSeekComplete(player);
   SystemClock.now+=60;player.position+=60;source("1",target+120);TestEngine.p.handler.drain();
   check(Collections.frequency(LogStore.events,"replacement_exclusive_dip_start")==before,
     "RED 0.3.65: repeated partial scrubs must not restart a 500ms cold dip");
  }
  check(Collections.frequency(LogStore.events,"replacement_exclusive_dip_start")==before,
      "only the initial cold entry is allowed to use the legacy dip");
  engine.close();
 }
 public static void main(String[] args)throws Exception{
  actualMedia3Chain();
  partiallyCachedScrubsNeverRestartColdDip();
  System.out.println("PASS: "+assertions+" HONOR 0.3.65 routed manual Next, automatic next, cached and streaming seek continuity checks");
 }
}
