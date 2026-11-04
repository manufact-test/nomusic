package pro.celikom.nativeprobe.identitydiag;

import android.os.SystemClock;
import java.io.File;
import java.io.ByteArrayInputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import org.json.JSONObject;

/**
 * Replays HONOR Test.33's Johnyboy handoff: 8.59/11.45 MiB were discarded
 * at the 1.2 second current-track timeout even while the file was advancing.
 */
public final class Test34PromotedHandoff {
 static int checks;
 static void check(boolean ok,String message){checks++;if(!ok)throw new AssertionError(message);}
 static JSONObject audio()throws Exception{return new JSONObject()
  .put("found",true).put("replacement_id",34).put("version",1)
  .put("duration_ms",120000).put("mime_type","audio/mpeg");}

 static void begin()throws Exception{
  TestEngine.reset("ALBUM",true);
  TestEngine.e=new ReplacementEngine(TestEngine.p,true,true);
  TestEngine.e.identity(LogStore.map("mediaAlias","1","albumId","42","title","Песня",
    "artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","7","method","ALBUM"));
  TestEngine.e.arm();
  TestEngine.p.lookaheadAlias="2";
  TestEngine.e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  check(TestEngine.api.resolves==2,"one current and one lookahead resolve");
  TestEngine.api.resolveCallbacks.get(1).done(audio(),null);
  check(TestEngine.api.lookaheadDownloads==1&&TestEngine.api.currentDownloads==0,
   "a single speculative full-file transfer started without source muting");
  TestEngine.e.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  TestEngine.e.identity(LogStore.map("mediaAlias","2","albumId","42","title","Песня",
    "artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","8","method","ALBUM"));
  TestEngine.e.noteLookaheadCandidate(null);
  TestEngine.api.resolveCallbacks.get(2).done(audio(),null);
  check(TestEngine.e.lookaheadPrefetchWait&&TestEngine.api.currentDownloads==0
    &&TestEngine.e.effect==null,"fresh resolve promotes matching inflight audio safely");
 }
 static void progressAt(long afterWaitStarted,long bytes,long total){
  SystemClock.now+=afterWaitStarted;
  TestEngine.p.current=TestEngine.source("2",afterWaitStarted,true);
  TestEngine.api.downloadCallbacks.get(0).progress(bytes,total,SystemClock.now);
 }
 static void nearCompleteFileIsNotThrownAway()throws Exception{
  begin();
  long full=11446773;
  progressAt(100,700000,full);
  progressAt(1100,8592404,full);
  TestEngine.p.handler.drain();
  check(TestEngine.e.lookaheadPrefetchWait&&TestEngine.api.currentDownloads==0,
    "75 percent completed Johnyboy transfer earns evidence-based short grace");
  progressAt(300,10100000,full);
  TestEngine.p.handler.drain();
  check(TestEngine.e.lookaheadPrefetchWait&&TestEngine.api.currentDownloads==0,
    "advancing close-to-complete download is not canceled at the next poll");
  File complete=File.createTempFile("celikom-test34-near-", ".audio");
  TestEngine.api.downloadCallbacks.get(0).done(complete,null);
  check(TestEngine.e.player!=null&&TestEngine.e.audioFromCache&&TestEngine.e.audioFile==complete
    &&TestEngine.api.downloads==1&&TestEngine.e.effect==null,
    "one completed file is consumed after live resolve without duplicate network work or premature mute");
  TestEngine.e.close();
 }
 static void poorProgressKeepsOriginalFastFallback()throws Exception{
  begin();long full=11446773;
  progressAt(100,300000,full);
  progressAt(1100,1600000,full);
  TestEngine.p.handler.drain();
  check(!TestEngine.e.lookaheadPrefetchWait&&TestEngine.api.lookaheadDownloads==1
    &&TestEngine.api.currentDownloads==1&&TestEngine.e.effect==null,
    "slow cold prefetch falls back at original 1200ms without speculative extra delay");
  check(!TestEngine.api.downloadValidity.get(0).getAsBoolean(),
    "superseded transport cannot inject its old candidate");
  File stale=File.createTempFile("celikom-test34-stale-", ".audio");
  TestEngine.api.downloadCallbacks.get(0).done(stale,null);
  check(!stale.exists(),"late canceled full file is deleted");
  TestEngine.e.close();
 }
 static void stalledNearCompleteMustYield()throws Exception{
  begin();long full=11446773;
  progressAt(100,700000,full);
  progressAt(1100,8592404,full);
  TestEngine.p.handler.drain();
  check(TestEngine.e.lookaheadPrefetchWait,"recent 75 percent progress earns bounded grace");
  SystemClock.now+=400;
  TestEngine.p.current=TestEngine.source("2",1600,true);
  TestEngine.p.handler.drain();
  check(!TestEngine.e.lookaheadPrefetchWait&&TestEngine.api.currentDownloads==1,
    "a formerly fast download that stopped advancing yields to foreground");
  TestEngine.e.close();
 }
 static void extraGraceIsAlwaysBounded()throws Exception{
  begin();long full=11446773;
  progressAt(100,700000,full);
  for(int n=0;n<25;n++){
   progressAt(100,8000000+n*100000,full);
   TestEngine.p.handler.drain();
  }
  check(!TestEngine.e.lookaheadPrefetchWait&&TestEngine.api.currentDownloads==1,
    "even with continuing progress, the extra grace never runs beyond its fixed bound");
  TestEngine.e.close();
 }
 static void policyRejectsMissingOrNonCurrentProgress(){
  LookaheadHandoffProgress progress=new LookaheadHandoffProgress();
  check(!progress.worthWaiting(2200,1000),"unknown content length cannot extend a current wait");
  progress.update(5000000,0,2100);
  check(!progress.worthWaiting(2200,1000),"invalid content length is ignored");
  progress.update(9000000,11446773,1200);
  check(!progress.worthWaiting(2200,1000),"an old progress reading cannot extend the wait");
  progress.update(9700000,11446773,2150);
  check(progress.worthWaiting(2200,1000),"recent verified bytes can extend current wait");
  check(!progress.worthWaiting(3101,1000),"absolute maximum wait is enforced");
 }
 static void actualTransferReportsVerifiedBytes()throws Exception{
  File file=File.createTempFile("celikom-test34-transfer-", ".audio");
  final byte[] payload=new byte[1024*1024+17];
  final AtomicInteger reports=new AtomicInteger();
  final AtomicLong largest=new AtomicLong();
  try{
   AudioTransfer.copy(file,()->new HttpURLConnection(new URL("http://example.invalid/never-contacted")){
    @Override public void connect(){}
    @Override public void disconnect(){}
    @Override public boolean usingProxy(){return false;}
    @Override public int getResponseCode(){return 200;}
    @Override public long getContentLengthLong(){return payload.length;}
    @Override public String getHeaderField(String key){return "ETag".equals(key)?"\"stable-test\"":null;}
    @Override public ByteArrayInputStream getInputStream(){return new ByteArrayInputStream(payload);}
   },()->true,()->false,SystemClock::elapsedRealtime,(attempt,bytes,reason)->{
    throw new AssertionError("complete transfer should not retry");
   },(bytes,expected,at)->{
    check(expected==payload.length&&bytes<=expected,"transport reports only verified bounded length");
    reports.incrementAndGet();largest.set(Math.max(largest.get(),bytes));
   });
   check(file.length()==payload.length&&largest.get()==payload.length&&reports.get()>1,
    "real full-file copy emits fresh total and chunk progress, not just a final completion event");
  }finally{file.delete();}
 }
 public static void main(String[] args)throws Exception{
  nearCompleteFileIsNotThrownAway();poorProgressKeepsOriginalFastFallback();
  stalledNearCompleteMustYield();extraGraceIsAlwaysBounded();policyRejectsMissingOrNonCurrentProgress();
  actualTransferReportsVerifiedBytes();
  System.out.println("PASS: "+checks+" Test.34 promoted inflight-progress and safe fallback assertions");
 }
}
