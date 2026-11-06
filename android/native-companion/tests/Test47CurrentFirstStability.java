package pro.celikom.nativeprobe.identitydiag;

import android.os.SystemClock;
import java.io.File;
import org.json.JSONObject;

/** HONOR Test.46 queue-grace Next and current-first prefetch regressions. */
public final class Test47CurrentFirstStability {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static JSONObject descriptor()throws Exception{
  return new JSONObject().put("found",true).put("replacement_id",1)
    .put("version",1).put("duration_ms",120000).put("mime_type","audio/mpeg");
 }
 static void start(){
  TestEngine.reset("ALBUM",true);
  TestEngine.e.close();
  TestEngine.e=new ReplacementEngine(TestEngine.p,true,true);
  TestEngine.e.identity(
    LogStore.map("mediaAlias","1","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","7","method","ALBUM"));
  TestEngine.api.signed=true;
  TestEngine.e.arm();
 }
 static void queueGraceManualNext()throws Exception{
  start();
  TestEngine.p.lookaheadAlias="2";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  check(TestEngine.api.resolves==2,"unique lookahead obtains its independent server resolve");
  TestEngine.api.resolveCallbacks.get(1).done(descriptor(),null);
  check(TestEngine.e.lookaheadPrefetchQueuedAtMs==SystemClock.now
    &&TestEngine.api.lookaheadDownloads==1,
    "full-file speculative transfer is queued but has not had its 1100ms grace");
  TestEngine.e.sourceBoundary("manual_next","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  TestEngine.e.identity(
    LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","8","method","ALBUM"));
  check(TestEngine.api.resolves==3,"fresh current resolve is mandatory even with lookahead");
  TestEngine.e.noteLookaheadCandidate(null);
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(),null);
  check(!TestEngine.e.lookaheadPrefetchWait
    &&TestEngine.e.lookaheadPrefetchAlias==null
    &&TestEngine.api.currentDownloads==1
    &&TestEngine.e.preparing&&TestEngine.e.effect==null,
    "rapid manual Next starts the verified foreground fallback without waiting 1200ms");
  check(!TestEngine.api.downloadValidity.get(0).getAsBoolean(),
    "obsolete lookahead cannot authorize playback after current promotion");
  File stale=File.createTempFile("celikom-test47-stale-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(stale,null);
  check(!stale.exists(),"late speculative download cannot overwrite current audio");
  File current=File.createTempFile("celikom-test47-current-",".audio");
  TestEngine.api.downloadCallbacks.get(1).done(current,null);
  check(TestEngine.e.player!=null&&TestEngine.e.effect==null,
    "only freshly resolved foreground file may prepare and it starts silent");
  TestEngine.e.close();
 }
 static void currentPreparationWinsSpeculation()throws Exception{
  start();
  TestEngine.api.resolveCallbacks.get(0).done(descriptor(),null);
  check(TestEngine.e.preparing&&!TestEngine.e.ready,
    "current song is still preparing its verified cold decoder");
  TestEngine.p.lookaheadAlias="2";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  check(TestEngine.api.resolves==1&&TestEngine.e.lookaheadPrefetchAlias==null,
    "speculative full-file work cannot contend while audible current is preparing");
  File current=File.createTempFile("celikom-test47-first-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(current,null);
  TestEngine.e.player.prepared.onPrepared(TestEngine.e.player);
  check(TestEngine.e.ready,"current decoder becomes ready normally");
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  check(TestEngine.api.resolves==2&&"2".equals(TestEngine.e.lookaheadPrefetchAlias),
    "safe next-item prefetch still starts once current decoder is ready");
  TestEngine.e.close();
 }
 static void repeatedPromotionDoesNotFloodJournal()throws Exception{
  start();
  TestEngine.p.lookaheadAlias="2";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  TestEngine.e.sourceBoundary("manual_next","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  TestEngine.e.identity(
    LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","8","method","ALBUM"));
  int before=LogStore.events.size();
  for(int i=0;i<30;i++)TestEngine.e.noteLookaheadCandidate(null);
  long promoted=LogStore.events.subList(before,LogStore.events.size()).stream()
    .filter("replacement_lookahead_prefetch_promoted_inflight"::equals).count();
  check(promoted<=1,"periodic samples do not fill long-session journal with duplicate promotion events");
  TestEngine.e.close();
 }
 public static void main(String[] args)throws Exception{
  queueGraceManualNext();
  currentPreparationWinsSpeculation();
  repeatedPromotionDoesNotFloodJournal();
  System.out.println("PASS: "+checks+" Test.47 current-first queue, cache and session guards");
 }
}
