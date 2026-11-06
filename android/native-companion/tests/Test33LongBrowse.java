package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;
import java.io.File;
import org.json.JSONObject;

/** Replays HONOR Test.32's 7.06s 0ms same-item post-seek handover. */
public final class Test33LongBrowse {
 static int assertions;
 static void check(boolean condition,String message){
  assertions++;
  if(!condition)throw new AssertionError(message);
 }
 static void advance(MediaPlayer decoder,int ms){
  SystemClock.now+=ms;decoder.position+=ms;
  TestEngine.p.current=TestEngine.source("1",TestEngine.p.current.position+ms,true);
  TestEngine.p.handler.drain();
 }
 static void sameItemSeekStoppedDecoder()throws Exception{
  TestEngine.playing();
  ReplacementEngine engine=TestEngine.e;
  MediaPlayer decoder=engine.player;
  for(int i=0;i<12;i++)advance(decoder,20);
  check(engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
    "initial coherent blend must have settled");
  int downloads=TestEngine.api.downloads;

  // Exactly the case omitted from Test.32's noInstantRegrant(): the original
  // regained source ownership and the decoder was STOPPED by a same-item seek.
  engine.audioOwner.aligning();
  engine.setAuditedVolume(decoder,0f);
  engine.audioOwner.sourceGainDuringAlignment(engine.effect);
  engine.originalMix=1f;engine.aligned=true;engine.fading=false;
  engine.sourceSeekedThisTrack=true;
  engine.audioOwner.pauseDecoder(decoder);
  check(!decoder.playing&&engine.effect.gain==0f,
    "the seek left the original audible and the decoder paused");

  engine.update(TestEngine.p.current);
  check(decoder.playing&&engine.fading&&engine.originalMix==1f
    &&decoder.volume==0f&&engine.audioOwner.state()!=AudioOwnership.State.REPLACEMENT,
    "decoder restart must not bypass unified fade with exclusive_single_turn");
  for(int i=0;i<16;i++)advance(decoder,20);
  check(!engine.fading&&engine.originalMix==0f&&decoder.volume>0.99f
    &&engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
    "the same player completes one verified finite handover");
  check(TestEngine.api.downloads==downloads,
    "same-item seek never triggers a redundant download or new decoder");
  engine.close();
 }
 static void shuffledAlbumCacheRetention()throws Exception{
  TestEngine.reset("ALBUM");
  ReplacementEngine engine=TestEngine.e;
  File oldest=null,newest=null;
  for(int n=0;n<17;n++){
   File audio=File.createTempFile("celikom-test33-cache-", ".audio");
   if(n==0)oldest=audio;
   newest=audio;
   JSONObject descriptor=TestEngine.found().put("replacement_id",100+n);
   engine.cachePrefetchedAudio("track"+n,descriptor,audio);
   if(n==15)check(engine.recentAudio.size()==16&&oldest.exists(),
     "sixteen verified recent songs remain available under the unchanged byte ceiling");
  }
  check(engine.recentAudio.size()==16&&!oldest.exists()&&newest.exists(),
    "seventeenth song evicts only the oldest unprotected file");
  engine.close();
  check(!newest.exists(),"private cache is cleaned on shutdown");
 }
 public static void main(String[] args)throws Exception{
  sameItemSeekStoppedDecoder();shuffledAlbumCacheRetention();
  System.out.println("PASS: "+assertions+" Test.33 post-seek stopped-decoder handover assertions");
 }
}
