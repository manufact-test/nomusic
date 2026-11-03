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
  check(TestEngine.api.downloads==1&&TestEngine.api.lookaheadDownloads==1&&TestEngine.api.currentDownloads==0&&TestEngine.e.player==null&&TestEngine.e.effect==null,
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
  check(TestEngine.api.downloads==2&&TestEngine.api.lookaheadDownloads==1&&TestEngine.api.currentDownloads==1&&TestEngine.e.preparing,
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
  android.os.SystemClock.now+=10001;
  // The real service samples the live Media3 item every 250 ms.
  TestEngine.p.current=TestEngine.source("2",11000,true);
  TestEngine.p.handler.drain();
  check(TestEngine.api.downloads==2&&TestEngine.e.preparing
      &&!TestEngine.e.lookaheadPrefetchWait,
    "a hung promoted prefetch falls back after a bounded current wait");
  File current=File.createTempFile("celikom-timeout-current-",".audio");
  TestEngine.api.downloadCallbacks.get(1).done(current,null);
  check(TestEngine.e.player!=null&&TestEngine.e.audioFile==current,
    "timeout fallback can still prepare the current replacement");
  TestEngine.e.close();
 }
 static void readyPrimedDecoderIsAdoptedOnlyAfterFreshResolve()throws Exception{
  beginLookahead();
  File file=File.createTempFile("celikom-prime-next-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  ReplacementEngine.NextDecoderPrime speculative=TestEngine.e.primedNext;
  check(speculative!=null&&TestEngine.e.player==null&&TestEngine.e.effect==null,
   "next audio is primed silently without gaining source-effect ownership");
  MediaPlayer future=speculative.player;
  future.prepared.onPrepared(future);
  check(future.isPlaying()&&future.volume==0f&&TestEngine.e.effect==null,
   "the next decoder starts at zero volume while current source remains untouched");
  future.position=45;android.os.SystemClock.now+=50;TestEngine.p.handler.drain();
  check(speculative.ready&&!future.isPlaying()&&future.seekCalls==1&&future.volume==0f,
   "the primed decoder proves muted motion, pauses and returns to position zero");
  TestEngine.e.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  TestEngine.e.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM","editionConflict",false));
  TestEngine.e.noteLookaheadCandidate(null);
  check(TestEngine.api.resolves==3,"a primed decoder never replaces the fresh live resolve");
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  check(TestEngine.e.player==future&&TestEngine.e.ready&&TestEngine.e.audioFromCache
    &&TestEngine.e.localPrewarmAttempted&&TestEngine.e.effect!=null
    &&TestEngine.api.downloads==1,
   "only the fresh current resolve may adopt a prepared decoder and full-file cache");
  TestEngine.e.close();
 }
 static void stalledPrimedDecoderExpiresWithoutBlockingCurrent()throws Exception{
  beginLookahead();
  File file=File.createTempFile("celikom-prime-timeout-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  ReplacementEngine.NextDecoderPrime speculative=TestEngine.e.primedNext;
  check(speculative!=null,"a silent next decoder was allocated");
  android.os.SystemClock.now+=ReplacementEngine.NEXT_DECODER_PRIME_TIMEOUT_MS+1;
  TestEngine.p.handler.drain();
  check(speculative.player.released&&TestEngine.e.primedNext==null
      &&TestEngine.e.player==null&&TestEngine.e.effect==null,
   "a stalled speculative decoder releases without changing source audio ownership");
  TestEngine.e.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  TestEngine.e.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  check(TestEngine.e.player!=null&&!TestEngine.e.ready&&TestEngine.e.audioFromCache
       &&TestEngine.api.downloads==1,
   "even if speculative decoder timed out, the full cached file uses normal playback preparation");
  TestEngine.e.close();
 }
 static void primedDecoderKeyMismatchCannotPlay()throws Exception{
  beginLookahead();
  File file=File.createTempFile("celikom-prime-mismatch-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  ReplacementEngine.NextDecoderPrime speculative=TestEngine.e.primedNext;
  check(speculative!=null,"the speculative decoder starts before mismatch");
  promoteCurrent(descriptor(2),false);
  check(speculative.player.released&&TestEngine.e.player==null
     &&TestEngine.api.downloads==2&&TestEngine.e.primedNext==null
     &&TestEngine.e.effect==null,
    "a different live audio key discards the silent decoder and uses fresh download");
  TestEngine.e.close();
 }

 static void unrelatedCurrentSongCannotDiscardPrimedSuccessor()throws Exception{
  beginLookahead();
  File file=File.createTempFile("celikom-prime-unrelated-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  ReplacementEngine engine=TestEngine.e;
  ReplacementEngine.NextDecoderPrime candidate=engine.primedNext;
  check(candidate!=null,"future decoder exists before current preparation");
  MediaPlayer future=candidate.player;
  future.prepared.onPrepared(future);
  future.position=45;android.os.SystemClock.now+=50;TestEngine.p.handler.drain();
  check(candidate.ready,"future decoder completed muted priming");
  MediaPlayer wrong=engine.takePrimedNext("1",engine.audioKeyFor("7",descriptor(1)),file);
  check(wrong==null&&engine.primedNext==candidate&&!future.released,
   "preparing current item must preserve a different primed next-item decoder");
  engine.close();
 }
 static void promotedPrimeWaitsForFreshResolveBeforeNextCandidate()throws Exception{
  beginLookahead();
  File file=File.createTempFile("celikom-prime-promoted-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  ReplacementEngine engine=TestEngine.e;
  ReplacementEngine.NextDecoderPrime candidate=engine.primedNext;
  MediaPlayer future=candidate.player;
  future.prepared.onPrepared(future);
  future.position=45;android.os.SystemClock.now+=50;TestEngine.p.handler.drain();
  check(candidate.ready,"current-track candidate has a ready muted decoder");
  engine.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  engine.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  engine.noteLookaheadCandidate(null);
  TestEngine.p.lookaheadAlias="3";
  engine.prefetchLookahead(LogStore.map("mediaAlias","3","durationMs",120000L),"9");
  check(engine.primedNext==candidate&&!future.released
    &&"2".equals(engine.lookaheadPrefetchAlias)&&TestEngine.api.resolves==3,
   "new successor cannot delete promoted current prime while fresh resolve is pending");
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  check(engine.player==future&&engine.ready&&engine.primedNext==null,
   "fresh current resolve adopts the original primed decoder without recreation");
  android.os.SystemClock.now+=250;TestEngine.p.handler.drain();
  check(TestEngine.api.resolves==4&&"3".equals(engine.lookaheadPrefetchAlias),
   "next candidate still starts promptly after protected current adoption");
  engine.close();
 }
 static void promotedPrimePreparedAfterBoundary()throws Exception{
  beginLookahead();
  File file=File.createTempFile("celikom-prime-current-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  ReplacementEngine engine=TestEngine.e;
  ReplacementEngine.NextDecoderPrime candidate=engine.primedNext;
  MediaPlayer future=candidate.player;
  engine.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  engine.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  engine.noteLookaheadCandidate(null);
  future.prepared.onPrepared(future);
  check(engine.primedNext==candidate&&!future.released&&future.isPlaying()
      &&future.volume==0f&&engine.effect==null,
   "a promoted prime still finishes silent preparation when its song becomes current");
  future.position=45;android.os.SystemClock.now+=50;TestEngine.p.handler.drain();
  check(candidate.ready&&!future.isPlaying(),
   "promoted live prime completes the muted motion and rewind");
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  check(engine.player==future&&engine.ready&&TestEngine.api.downloads==1,
   "fresh resolve adopts the prime completed after the boundary");
  engine.close();
 }
 static void freshResolveWaitsBrieflyForPromotedPrime()throws Exception{
  beginLookahead();
  File file=File.createTempFile("celikom-prime-live-wait-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  ReplacementEngine engine=TestEngine.e;
  ReplacementEngine.NextDecoderPrime candidate=engine.primedNext;
  MediaPlayer future=candidate.player;
  engine.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  engine.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  engine.noteLookaheadCandidate(null);
  future.prepared.onPrepared(future);
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  check(engine.player==null&&engine.primedNext==candidate
      &&TestEngine.api.downloads==1&&engine.effect==null,
   "fresh live resolve briefly waits for the in-progress matching muted prime");
  future.position=45;android.os.SystemClock.now+=60;TestEngine.p.handler.drain();
  check(engine.player==future&&engine.ready&&engine.primedNext==null
      &&TestEngine.api.downloads==1,
   "brief wait adopts the same decoder after a post-boundary priming ACK");
  engine.close();
 }
 static void stalledPromotedPrimeFallsBackAfterBoundedWait()throws Exception{
  beginLookahead();
  File file=File.createTempFile("celikom-prime-live-expire-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(file,null);
  ReplacementEngine engine=TestEngine.e;
  ReplacementEngine.NextDecoderPrime candidate=engine.primedNext;
  MediaPlayer future=candidate.player;
  engine.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  engine.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  engine.noteLookaheadCandidate(null);
  future.prepared.onPrepared(future);
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  android.os.SystemClock.now+=ReplacementEngine.PROMOTED_PRIME_READY_WAIT_MS+25;
  TestEngine.p.handler.drain();
  check(engine.player!=null&&engine.player!=future&&!engine.ready
      &&future.released&&engine.primedNext==null&&TestEngine.api.downloads==1,
   "a stalled promoted prime falls back to a new decoder after bounded grace");
  engine.close();
 }

 static void cachedCurrentPrimeBeforeFreshResolve()throws Exception{
  TestEngine.reset("ALBUM",true);TestEngine.api.signed=true;TestEngine.e.arm();
  ReplacementEngine engine=TestEngine.e;
  File file=File.createTempFile("celikom-current-cache-", ".audio");
  String audioKey=engine.audioKeyFor("8",descriptor(1));
  engine.recentAudio.put(audioKey,file);
  engine.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",1000,true);
  engine.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  ReplacementEngine.NextDecoderPrime candidate=engine.primedNext;
  check(candidate!=null&&candidate.currentCache
    &&candidate.player.volume==0f&&engine.player==null&&engine.effect==null,
    "a repeat in the private cache can silently prepare its current decoder while live resolve is pending");
  check(TestEngine.api.resolves==2&&TestEngine.api.downloads==0,
    "current cached prime does not skip fresh authorization or start a download");
  MediaPlayer muted=candidate.player;muted.prepared.onPrepared(muted);
  check(muted.playing&&muted.volume==0f&&engine.effect==null,
    "the speculative decoder starts muted without touching the source");
  muted.position=45;android.os.SystemClock.now+=55;TestEngine.p.handler.drain();
  check(candidate.ready&&!muted.playing&&muted.position==0,
    "muted current prime becomes ready and rewinds before any fresh replacement grant");
  TestEngine.api.resolveCallbacks.get(1).done(descriptor(1),null);
  check(engine.player==muted&&engine.ready&&engine.primedNext==null
     &&engine.audioFromCache&&engine.effect!=null&&TestEngine.api.downloads==0,
    "a matching live descriptor adopts the primed cached decoder, with the original seek path intact");
  engine.close();
 }
 static void cachedCurrentPrimeRejectedOnLiveEditionMismatch()throws Exception{
  TestEngine.reset("ALBUM",true);TestEngine.api.signed=true;TestEngine.e.arm();
  ReplacementEngine engine=TestEngine.e;
  File file=File.createTempFile("celikom-current-edition-", ".audio");
  engine.recentAudio.put(engine.audioKeyFor("8",descriptor(1)),file);
  engine.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  engine.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  MediaPlayer stale=engine.primedNext.player;
  stale.prepared.onPrepared(stale);stale.position=45;
  android.os.SystemClock.now+=50;TestEngine.p.handler.drain();
  TestEngine.api.resolveCallbacks.get(1).done(descriptor(2),null);
  check(stale.released&&engine.primedNext==null&&engine.player==null
    &&TestEngine.api.downloads==1&&engine.effect==null,
    "stale cached replacement is rejected after a new authorized edition arrives");
  engine.close();
 }
 static void currentPrimeRevokedOnBoundaryBeforeResolve()throws Exception{
  TestEngine.reset("ALBUM",true);TestEngine.api.signed=true;TestEngine.e.arm();
  ReplacementEngine engine=TestEngine.e;
  File file=File.createTempFile("celikom-current-boundary-", ".audio");
  engine.recentAudio.put(engine.audioKeyFor("8",descriptor(1)),file);
  engine.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  engine.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  MediaPlayer stale=engine.primedNext.player;
  engine.sourceBoundary("manual_next","3");
  check(stale.released&&engine.primedNext==null
    &&engine.player==null&&engine.effect==null,
    "leaving a current song revokes its silent prime before any fresh resolve can authorize it");
  engine.close();
 }

 static void repeatedCurrentWaitIsSingleFlight()throws Exception{
  TestEngine.reset("ALBUM",true);TestEngine.api.signed=true;TestEngine.e.arm();
  ReplacementEngine engine=TestEngine.e;
  File file=File.createTempFile("celikom-current-single-flight-", ".audio");
  engine.recentAudio.put(engine.audioKeyFor("8",descriptor(1)),file);
  engine.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  engine.identity(
   LogStore.map("mediaAlias","2","albumId","42","title","Песня","artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM"));
  check(engine.primedNext!=null&&!engine.primedNext.ready,
    "cached decoder is priming when the current resolve starts");
  TestEngine.api.resolveCallbacks.get(1).done(descriptor(1),null);
  check(engine.primeReadyWaitInFlight&&engine.player==null&&TestEngine.api.downloads==0,
    "only one bounded wait is opened for this unfinished prime");
  long waitToken=engine.primeReadyWaitToken;
  for(int i=0;i<35;i++)engine.update(TestEngine.p.current);
  check(engine.primeReadyWaitToken==waitToken&&engine.primeReadyWaitInFlight,
    "rapid source samples reuse the same wait without scheduling other callbacks");
  android.os.SystemClock.now+=ReplacementEngine.PROMOTED_PRIME_READY_WAIT_MS+40;
  TestEngine.p.handler.drain();
  check(engine.player!=null&&engine.audioFile==file
     &&TestEngine.api.downloads==0&&!engine.primeReadyWaitInFlight,
    "a stalled speculative prime falls back to one cached decoder, never a duplicate download");
  engine.close();
  check(!file.exists(),"single-flight fallback does not leak the cached file");
 }
 public static void main(String[] args)throws Exception{
  beginLookahead();promoteCurrent(descriptor(1),true);matchingPrefetchIsConsumed();
  mismatchedFreshResolveFallsBack();latePrefetchCanStartAfterBoundary();
  newNextCandidateCannotStealCurrentDownload();cancelledCurrentWaitMustFallBack();
  currentWaitHasTimeout();readyPrimedDecoderIsAdoptedOnlyAfterFreshResolve();
  unrelatedCurrentSongCannotDiscardPrimedSuccessor();
  promotedPrimeWaitsForFreshResolveBeforeNextCandidate();
  primedDecoderKeyMismatchCannotPlay();stalledPrimedDecoderExpiresWithoutBlockingCurrent();
  promotedPrimePreparedAfterBoundary();freshResolveWaitsBrieflyForPromotedPrime();
  stalledPromotedPrimeFallsBackAfterBoundedWait();
  cachedCurrentPrimeBeforeFreshResolve();cachedCurrentPrimeRejectedOnLiveEditionMismatch();
  currentPrimeRevokedOnBoundaryBeforeResolve();repeatedCurrentWaitIsSingleFlight();
  System.out.println("PASS: "+checks+" lookahead promotion, fresh-resolve, cache handoff and mismatch checks");
 }
}
