package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import java.io.File;
import org.json.JSONObject;

/** Exercises next-track prefetch promotion into the live track without duplicate downloads. */
public final class TestLookaheadPrefetchHandoff {
 static int checks;
 static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
 static JSONObject descriptor(long replacementId)throws Exception{
  return new JSONObject().put("found",true).put("replacement_id",replacementId)
    .put("version",1).put("duration_ms",120000).put("mime_type","audio/mpeg");
 }
 static void beginLookahead()throws Exception{
  TestEngine.reset("ALBUM",true);
  TestEngine.api.signed=true;
  TestEngine.e.arm();
  TestEngine.p.lookaheadAlias="2";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  check(TestEngine.api.resolves==2&&TestEngine.e.player==null&&TestEngine.e.effect==null,
    "lookahead starts a second resolve without creating a decoder or touching audio ownership");
  check(TestEngine.api.resolveValidity.get(1).getAsBoolean(),
    "next-item resolve remains valid while the same item is still in the timeline");
  TestEngine.api.resolveCallbacks.get(1).done(descriptor(1),null);
  check(TestEngine.api.downloads==1&&TestEngine.e.player==null&&TestEngine.e.effect==null,
    "prefetch downloads the full file only; original remains the sole audible source");
 }
 static void promoteCurrent(JSONObject fresh,boolean expectPrefetchWait)throws Exception{
  TestEngine.e.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  TestEngine.e.identity(
    LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","8","method","ALBUM","editionConflict",false));
  TestEngine.e.noteLookaheadCandidate(null);
  check(TestEngine.e.lookaheadPrefetchPromoted,
    "the lookahead lease is promoted when the candidate becomes the current track");
  check(TestEngine.api.resolves==3,
    "the boundary still performs a fresh live resolve before any cached audio is consumed");
  TestEngine.api.resolveCallbacks.get(2).done(fresh,null);
  if(expectPrefetchWait)check(TestEngine.e.preparing&&TestEngine.e.player==null&&TestEngine.api.downloads==1,
    "current preparation waits for the matching in-flight prefetch instead of downloading twice");
  else check(TestEngine.e.preparing&&TestEngine.api.downloads==2,
    "a mismatched fresh resolve immediately uses its own full download");
 }
 static void matchingPrefetchIsConsumed()throws Exception{
  File file=File.createTempFile("celikom-lookahead-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  ReplacementEngine engine=TestEngine.e;
  MediaPlayer player=engine.player;
  check(player!=null&&engine.audioFromCache&&engine.audioFile==file,
    "the promoted prefetch file is consumed by the freshly resolved current track");
  check(TestEngine.api.downloads==1,
    "one lookahead download is reused; no second full-file download is issued");
  player.prepared.onPrepared(player);
  check(engine.localPrewarmWarmupPending&&engine.effect!=null,
    "the existing muted local decoder prewarm starts after cache adoption");
  engine.close();
 }
 static void mismatchedFreshResolveFallsBack()throws Exception{
  beginLookahead();promoteCurrent(descriptor(2),false);
  check(TestEngine.api.downloads==2&&TestEngine.e.preparing,
    "a fresh resolve key mismatch falls back to its own full download");
  check(!TestEngine.api.downloadValidity.get(0).getAsBoolean(),
    "mismatched prefetch lease is cancelled before its late file can be consumed");
  File stale=File.createTempFile("celikom-lookahead-stale-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(stale,null);
  check(!stale.exists(),"a late mismatched prefetch file is deleted");
  TestEngine.e.close();
 }
 static void latePrefetchCanStartAfterBoundary()throws Exception{
  TestEngine.reset("ALBUM",true);
  TestEngine.api.signed=true;
  TestEngine.e.arm();
  TestEngine.e.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  check(TestEngine.api.resolves==2&&TestEngine.e.player==null,
    "a uniquely identified next item may begin prefetch even if its album response arrives after the boundary");
  TestEngine.e.identity(
    LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","8","method","ALBUM","editionConflict",false));
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  check(TestEngine.e.preparing&&TestEngine.api.downloads==0,
    "the current item waits while the late lookahead resolve is still in flight");
  TestEngine.api.resolveCallbacks.get(1).done(descriptor(1),null);
  check(TestEngine.api.downloads==1,
    "the late lookahead response continues directly into one full-file download");
  File file=File.createTempFile("celikom-lookahead-late-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  check(TestEngine.e.player!=null&&TestEngine.e.audioFromCache&&TestEngine.e.audioFile==file,
    "late prefetch completion is adopted by the current track without a duplicate download");
  TestEngine.e.close();
 }
 static void newNextCandidateCannotStealCurrentDownload()throws Exception{
  beginLookahead();promoteCurrent(descriptor(1),true);
  TestEngine.p.lookaheadAlias="3";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","3","durationMs",120000L),"9");
  check(TestEngine.api.downloads==1&&TestEngine.api.resolves==3
      &&"2".equals(TestEngine.e.lookaheadPrefetchAlias)&&TestEngine.e.lookaheadPrefetchWait,
    "a new next-track candidate cannot cancel an in-flight current-track handoff");
  File current=File.createTempFile("celikom-current-handoff-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(current,null);
  check(TestEngine.e.player!=null&&TestEngine.e.audioFile==current
      &&TestEngine.e.audioFromCache&&!TestEngine.e.lookaheadPrefetchWait,
    "the promoted current song still consumes its original download");
  android.os.SystemClock.now+=1000;TestEngine.p.handler.drain();
  check(TestEngine.api.resolves==4&&"3".equals(TestEngine.e.lookaheadPrefetchAlias),
    "the next track begins prefetch after the current handoff is secure");
  check(TestEngine.api.downloads==1,
    "no duplicate current-track file download was started");
  TestEngine.e.close();
 }
 static void cancelledCurrentWaitMustFallBack()throws Exception{
  beginLookahead();promoteCurrent(descriptor(1),true);
  TestEngine.e.invalidateLookaheadPrefetch("simulated_conflicting_candidate");
  check(TestEngine.api.downloads==2&&TestEngine.e.preparing
      &&!TestEngine.e.lookaheadPrefetchWait&&TestEngine.e.effect==null,
    "invalidating a promoted wait starts the verified current full-file fallback");
  check(!TestEngine.api.downloadValidity.get(0).getAsBoolean(),
    "cancelled prefetch cannot replace the freshly resolved fallback");
  File stale=File.createTempFile("celikom-stale-wait-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(stale,null);
  check(!stale.exists(),"a late cancelled prefetch is discarded");
  File current=File.createTempFile("celikom-fallback-current-",".audio");
  TestEngine.api.downloadCallbacks.get(1).done(current,null);
  check(TestEngine.e.player!=null&&TestEngine.e.audioFile==current,
    "the current decoder prepares after the cancellation fallback");
  TestEngine.e.close();
 }
 static void currentWaitHasTimeout()throws Exception{
  beginLookahead();promoteCurrent(descriptor(1),true);
  android.os.SystemClock.now+=10001;TestEngine.p.handler.drain();
  check(TestEngine.api.downloads==2&&TestEngine.e.preparing
      &&!TestEngine.e.lookaheadPrefetchWait,
    "a hung promoted prefetch falls back after a bounded current wait");
  File current=File.createTempFile("celikom-timeout-current-",".audio");
  TestEngine.api.downloadCallbacks.get(1).done(current,null);
  check(TestEngine.e.player!=null&&TestEngine.e.audioFile==current,
    "timeout fallback can still prepare the current replacement");
  TestEngine.e.close();
 }
 public static void main(String[] args)throws Exception{
  beginLookahead();promoteCurrent(descriptor(1),true);matchingPrefetchIsConsumed();
  mismatchedFreshResolveFallsBack();latePrefetchCanStartAfterBoundary();
  newNextCandidateCannotStealCurrentDownload();cancelledCurrentWaitMustFallBack();
  currentWaitHasTimeout();
  System.out.println("PASS: "+checks+" lookahead promotion, fresh-resolve, cache handoff and mismatch checks");
 }
}
