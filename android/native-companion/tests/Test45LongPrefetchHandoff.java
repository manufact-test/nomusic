package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;
import java.io.File;
import org.json.JSONObject;

/** Exact Test.44 HONOR 4–5-minute Next cases: no 1.2-second idle handoff. */
public final class Test45LongPrefetchHandoff {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static JSONObject descriptor(long duration)throws Exception{
  return new JSONObject().put("found",true).put("replacement_id",38)
    .put("version",1).put("duration_ms",duration).put("mime_type","audio/mpeg");
 }
 static PlaybackSource longSource(String alias){
  return new PlaybackSource(alias,"Песня","Артист",280000,
    "https://avatars.yandex.net/get-music-content/1/x.a.42-1/700x700",0,true,true,1f);
 }
 static void longCurrentFallsBackBeforeOldTimeout()throws Exception{
  TestEngine.reset("ALBUM",true);
  TestEngine.e.close();
  TestEngine.e=new ReplacementEngine(TestEngine.p,true,true);
  TestEngine.e.identity(LogStore.map("mediaAlias","1","albumId","42",
    "title","Песня","artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","7","method","ALBUM"));
  TestEngine.e.arm();
  TestEngine.p.lookaheadAlias="2";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",280000L),"8");
  check(TestEngine.api.resolves==2,"future long track starts a normal authenticated lookahead resolve");
  TestEngine.api.resolveCallbacks.get(1).done(descriptor(280000),null);
  check(TestEngine.api.lookaheadDownloads==1,"full-file speculative work begins before Next");
  // Test.45's 400ms branch applies after the 1.1s speculative queue grace.
  // Test.47 separately exercises Next *during* that grace.
  SystemClock.now+=LookaheadPrefetchPolicy.SPECULATIVE_QUEUE_YIELD_MS;
  TestEngine.e.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=longSource("2");
  TestEngine.p.lookaheadAlias=null;
  TestEngine.e.identity(LogStore.map("mediaAlias","2","albumId","42",
    "title","Песня","artist","Артист","durationMs",280000L),
    LogStore.map("candidateTrackId","8","method","ALBUM"));
  check(TestEngine.api.resolves==3,"promoted long track still requires a fresh current resolve");
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(280000),null);
  check(TestEngine.e.lookaheadPrefetchWait&&TestEngine.api.downloads==1,
    "current long song briefly gives the full-file prefetch its remaining chance");
  SystemClock.now+=399;TestEngine.p.handler.drain();
  check(TestEngine.e.lookaheadPrefetchWait&&TestEngine.api.downloads==1,
    "a still-valid lookahead may finish during its 400ms grace");
  SystemClock.now+=1;TestEngine.p.handler.drain();
  check(!TestEngine.e.lookaheadPrefetchWait&&TestEngine.api.downloads==2
      &&TestEngine.e.preparing&&TestEngine.e.effect==null,
    "stalled long full-file speculation yields to verified current sparse preparation at 400ms");
  check(!TestEngine.api.downloadValidity.get(0).getAsBoolean(),
    "cancelled speculative transfer cannot gain sound ownership later");
  File stale=File.createTempFile("celikom-test45-stale-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(stale,null);
  check(!stale.exists(),"a late full-file callback cannot overwrite the current decoder");
  TestEngine.e.close();
 }
 static void shortAndFrozenStayUnchanged(){
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,203700,"downloading")==1200,
    "HONOR 3:23 Pушка preserves the successfully completed 749ms promoted handoff");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,240000,"downloading")==400,
    "long current songs do not repeat an observed full 1200ms wait before sparse fallback");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,280000,"resolving")==1200,
    "a still-resolving lookahead keeps the existing short wait instead of premature cancellation");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(false,280000,"downloading")==10000,
    "frozen full-file release path remains unchanged");
 }
 public static void main(String[] args)throws Exception{
  shortAndFrozenStayUnchanged();
  longCurrentFallsBackBeforeOldTimeout();
  System.out.println("PASS: "+checks+" Test.45 HONOR long successor handoff guards");
 }
}
