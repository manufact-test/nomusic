package pro.celikom.nativeprobe.identitydiag;

import java.io.File;
import java.io.IOException;
import android.os.SystemClock;
import org.json.JSONObject;

/** Test.35: one sparse source/validator set survives the NEXT -> CURRENT handoff. */
public final class Test35SingleFlight {
 static int assertions;
 static void check(boolean ok,String message){assertions++;if(!ok)throw new AssertionError(message);}

 static JSONObject descriptor(long replacementId)throws Exception{
  return new JSONObject().put("found",true).put("replacement_id",replacementId)
   .put("version",1).put("duration_ms",120000).put("mime_type","audio/mpeg");
 }
 static BufferedAudio source(boolean complete)throws Exception{
  File file=File.createTempFile("celikom-test35-single-flight-",".audio");
  BufferedAudio audio=new BufferedAudio(file,()->{throw new IOException("no_network_in_state_test");},
    ()->true,()->SystemClock.now,(name,bytes)->{});
  audio.size=BufferedAudio.BLOCK*8L;
  audio.present.set(0);audio.present.set(1);audio.present.set(7);
  if(complete)audio.present.set(0,8);
  else audio.holdPrefetchForSeek(); // deterministic: do not start background HTTP
  return audio;
 }
 static void begin()throws Exception{
  TestEngine.reset("ALBUM",true);
  TestEngine.e=new ReplacementEngine(TestEngine.p,true,true,true);
  TestEngine.api.signed=true;
  TestEngine.e.arm();
  TestEngine.p.lookaheadAlias="2";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  check(TestEngine.api.resolves==1&&TestEngine.e.player==null,
   "lookahead resolves quietly and never touches the source effect");
  TestEngine.api.resolveCallbacks.get(0).done(descriptor(1),null);
  check(TestEngine.api.lookaheadSparseRequests==1&&TestEngine.api.downloads==0
    &&"sparse_opening".equals(TestEngine.e.lookaheadPrefetchPhase),
   "Test.35 uses one prospective sparse transport, not full-file download");
 }
 static void current(JSONObject fresh)throws Exception{
  ReplacementEngine engine=TestEngine.e;
  engine.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  engine.identity(LogStore.map("mediaAlias","2","albumId","42","title","Песня",
   "artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM","editionConflict",false));
  engine.noteLookaheadCandidate(null);
  check(TestEngine.api.resolves==2,"live current track must independently resolve its edition");
  TestEngine.api.resolveCallbacks.get(1).done(fresh,null);
 }
 static void leasePromotion() {
  final boolean[] candidate={true},foreground={true};
  PromotableAudioLease lease=new PromotableAudioLease(()->candidate[0]);
  check(lease.getAsBoolean()&&!lease.promoted(),"speculative lease valid before takeover");
  lease.promote(()->foreground[0]);candidate[0]=false;
  check(lease.getAsBoolean()&&lease.promoted(),
   "completed takeover never inherits invalidated lookahead identity");
  foreground[0]=false;
  check(!lease.getAsBoolean(),"promoted source obeys current song cancellation");
  lease.revoke();foreground[0]=true;
  check(!lease.getAsBoolean(),"revoked lease cannot become valid again");
  boolean threw=false;try{lease.promote(()->true);}catch(IllegalStateException expected){threw=true;}
  check(threw,"a revoked source cannot be resurrected by a late callback");
 }
 static void oneVerifiedStreamIsAdopted()throws Exception{
  begin();
  BufferedAudio next=source(false);
  PromotableAudioLease lease=TestEngine.api.lookaheadSparseLeases.get(0);
  TestEngine.api.lookaheadSparseCallbacks.get(0).done(next,null);
  check(TestEngine.e.lookaheadSparse==next&&next.cachedBytes()==3L*BufferedAudio.BLOCK
    &&TestEngine.e.effect==null,"three previously verified blocks stay private and silent");
  current(descriptor(1));
  check(TestEngine.e.streaming==next&&TestEngine.e.player!=null
    &&TestEngine.e.lookaheadSparse==null&&TestEngine.e.lookaheadSparseLease==null
    &&TestEngine.api.foregroundSparseRequests==0&&TestEngine.api.downloads==0,
   "foreground decoder consumes EXACT same sparse source with no second request");
  check(lease.promoted()&&lease.getAsBoolean()&&!next.closed,
   "account and owner lease transfers atomically and preserves bytes");
  TestEngine.p.lookaheadAlias="3";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","3","durationMs",120000L),"9");
  check(lease.getAsBoolean()&&!next.closed,
   "the next speculative candidate cannot close the already adopted current stream");
  TestEngine.e.close();
  check(next.closed,"current decoder retires adopted stream normally on shutdown");
 }
 static void unreadySpeculationNeverBlocksCurrent()throws Exception{
  begin();
  PromotableAudioLease expired=TestEngine.api.lookaheadSparseLeases.get(0);
  NativeApi.StreamResult pending=TestEngine.api.lookaheadSparseCallbacks.get(0);
  TestEngine.api.useStreaming=true;
  current(descriptor(1));
  check(TestEngine.e.preparing&&TestEngine.api.foregroundSparseRequests==1
    &&TestEngine.api.downloads==0&&TestEngine.e.lookaheadSparse==null
    &&!expired.getAsBoolean(),
   "CURRENT gets immediate foreground Range with zero 1200ms wait or parallel full copy");
  BufferedAudio stale=source(false);pending.done(stale,null);
  check(stale.closed&&!stale.file.exists()&&TestEngine.e.player==null,
   "late speculative initialization cannot steal or leak current audio");
  BufferedAudio foreground=source(false);
  TestEngine.api.streamed.done(foreground,null);
  check(TestEngine.e.player!=null&&TestEngine.e.streaming==foreground,
   "foreground initialization can still join safely after speculative cancellation");
  TestEngine.e.close();
 }
 static void editionMismatchIsolated()throws Exception{
  begin();
  BufferedAudio wrong=source(false);
  PromotableAudioLease revoked=TestEngine.api.lookaheadSparseLeases.get(0);
  TestEngine.api.lookaheadSparseCallbacks.get(0).done(wrong,null);
  TestEngine.api.useStreaming=true;
  current(descriptor(2));
  check(wrong.closed&&!revoked.getAsBoolean()&&TestEngine.e.streaming==null
    &&TestEngine.api.foregroundSparseRequests==1&&TestEngine.api.downloads==0,
   "fresh replacement edition wins; mismatched speculative bytes never reach decoder");
  TestEngine.e.close();
 }
 static void completeSourceRetainsOriginalPrime()throws Exception{
  begin();
  BufferedAudio complete=source(true);
  File file=complete.file;
  TestEngine.api.lookaheadSparseCallbacks.get(0).done(complete,null);
  check(complete.closed&&file.exists()&&TestEngine.e.lookaheadSparse==null
    &&TestEngine.e.recentAudio.size()==1&&TestEngine.e.primedNext!=null
    &&TestEngine.api.downloads==0,
   "a fully verified stream becomes the same local-file/primed-decoder fast path as Test.33");
  current(descriptor(1));
  // Keep the frozen Test.33 150ms timeout for a primed decoder that has not
  // yet proved muted playback; this must not start another network request.
  SystemClock.now+=ReplacementEngine.PROMOTED_PRIME_READY_WAIT_MS+25;
  TestEngine.p.handler.drain();
  check(TestEngine.e.player!=null&&TestEngine.e.audioFromCache&&TestEngine.api.downloads==0,
   "fresh current resolve adopts complete prewarm without a second fetch");
  TestEngine.e.close();
 }
 static void repeatedQuickSkipFencesOldCallbacks()throws Exception{
  begin();
  NativeApi.StreamResult first=TestEngine.api.lookaheadSparseCallbacks.get(0);
  PromotableAudioLease old=TestEngine.api.lookaheadSparseLeases.get(0);
  TestEngine.p.lookaheadAlias="3";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","3","durationMs",120000L),"9");
  check(!old.getAsBoolean()&&TestEngine.api.resolves==2,
   "replacing the next candidate revokes only old speculative transport");
  BufferedAudio late=source(false);first.done(late,null);
  check(late.closed&&!late.file.exists()&&TestEngine.e.player==null,
   "late old NEXT callback cannot create a player or resurrect deleted source");
  TestEngine.e.close();
 }
 public static void main(String[] args)throws Exception{
  leasePromotion();oneVerifiedStreamIsAdopted();unreadySpeculationNeverBlocksCurrent();
  editionMismatchIsolated();completeSourceRetainsOriginalPrime();repeatedQuickSkipFencesOldCallbacks();
  System.out.println("PASS: "+assertions+" Test.35 single-flight sparse handoff assertions");
 }
}
