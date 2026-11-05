package pro.celikom.nativeprobe.identitydiag;

import android.os.SystemClock;
import java.io.*;
import java.net.*;
import java.util.Arrays;
import org.json.JSONObject;

/** Test.36: content-verified transfer takeover, never a blind timer increase. */
public final class Test36TransferTakeover {
 static int checks;
 static void check(boolean value,String reason){checks++;if(!value)throw new AssertionError(reason);}
 static JSONObject descriptor(long edition)throws Exception{return new JSONObject()
  .put("found",true).put("replacement_id",edition).put("version",1)
  .put("duration_ms",120000).put("mime_type","audio/mpeg");}
 static ReplacementEngine begin(boolean optIn)throws Exception{
  TestEngine.reset("ALBUM",true);
  TestEngine.e.close();
  ReplacementEngine e=new ReplacementEngine(TestEngine.p,true,true,optIn);
  TestEngine.e=e;e.identity(LogStore.map("mediaAlias","1","albumId","42","title","Песня",
   "artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","7","method","ALBUM","editionConflict",false));
  e.arm();TestEngine.p.lookaheadAlias="2";
  e.prefetchLookahead(LogStore.map("mediaAlias","2","durationMs",120000L),"8");
  TestEngine.api.resolveCallbacks.get(1).done(descriptor(1),null);
  check(TestEngine.api.lookaheadDownloads==1,"one speculative full-file download scheduled");
  e.sourceBoundary("sample_track_changed","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  TestEngine.p.lookaheadAlias=null;
  e.identity(LogStore.map("mediaAlias","2","albumId","42","title","Песня",
   "artist","Артист","durationMs",120000L),
   LogStore.map("candidateTrackId","8","method","ALBUM","editionConflict",false));
  e.noteLookaheadCandidate(null);
  check(TestEngine.api.resolves==3,"current still resolves live edition before takeover");
  return e;
 }
 static void testTransferPolicy(){
  LookaheadTransferState t=new LookaheadTransferState();t.progress(9000000,11000000,1200);
  check(!t.finishInsteadOfRestart(1300,100),"no takeover without edition verification");
  t.promote();
  check(t.finishInsteadOfRestart(1300,100),"recent 82% full-file transfer may continue");
  check(!t.finishInsteadOfRestart(1700,100),"stalled transfer may not extend wait");
  t.progress(1000000,11000000,1700);
  check(!t.finishInsteadOfRestart(1700,100),"small transfer may not delay sparse fallback");
  t.progress(10000000,11000000,2500);
  check(t.finishInsteadOfRestart(2500,100),"almost completed file within extension ceiling");
  check(!t.finishInsteadOfRestart(2700,100),"extension has an absolute deadline");
  t.progress(11000000,11000000,2550);
  check(!t.finishInsteadOfRestart(2550,100),"completed transfer never asks to wait more");
  LookaheadTransferState unknown=new LookaheadTransferState();unknown.promote();unknown.progress(2000000,-1,1000);
  check(!unknown.finishInsteadOfRestart(1200,0),"unknown content length cannot prolong handoff");
 }
 static void testReuseInsteadOfRestart()throws Exception{
  ReplacementEngine e=begin(true);
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  LookaheadTransferState transfer=e.lookaheadTransfer;
  check(e.lookaheadPrefetchWait&&transfer.foreground(),"matching live edition promotes running full transfer");
  transfer.progress(8600000,11000000,SystemClock.now);
  SystemClock.now+=1200;
  transfer.progress(8700000,11000000,SystemClock.now);
  TestEngine.p.handler.drain();
  check(e.lookaheadPrefetchWait&&TestEngine.api.downloads==1,
   "the former 1.2s cancellation reuses 8.7MB instead of restarting transport");
  SystemClock.now+=100;
  transfer.progress(10500000,11000000,SystemClock.now);
  TestEngine.p.handler.drain();
  check(e.lookaheadPrefetchWait&&TestEngine.api.downloads==1,"progress extends bounded same-file takeover");
  File whole=File.createTempFile("test36-current-",".audio");
  TestEngine.api.downloadCallbacks.get(0).done(whole,null);
  check(e.player!=null&&e.audioFile==whole&&e.audioFromCache&&TestEngine.api.downloads==1,
   "one full original transfer is adopted, without second sparse stream or download");
  check(e.originalMix>=0.999f,"no premature source mute during promotion");
  e.close();
 }
 static void testStallAndWrongEdition()throws Exception{
  ReplacementEngine e=begin(true);
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  LookaheadTransferState transfer=e.lookaheadTransfer;
  transfer.progress(8000000,11000000,SystemClock.now);
  SystemClock.now+=1200;
  TestEngine.p.handler.drain();
  check(!e.lookaheadPrefetchWait&&TestEngine.api.currentDownloads==1,
   "stalled transfer falls back at original 1.2s budget");
  check(!TestEngine.api.downloadValidity.get(0).getAsBoolean(),
   "fallback revokes old transfer lease, preventing stale completion");
  e.close();

  e=begin(true);
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(2),null);
  check(TestEngine.api.currentDownloads==1&&TestEngine.api.lookaheadDownloads==1,
   "mismatched edition falls back immediately");
  check(e.lookaheadTransfer==null||!e.lookaheadTransfer.foreground(),
   "a wrong edition is never promoted to foreground");
  e.close();

  e=begin(false);
  TestEngine.api.resolveCallbacks.get(2).done(descriptor(1),null);
  check(e.lookaheadTransfer==null&&e.lookaheadPrefetchWait,
   "accepted Test.33 constructor remains a separate untouched code path");
  e.close();
 }
 static void testRealTransferProgress()throws Exception{
  byte[] payload=new byte[1500000];Arrays.fill(payload,(byte)87);
  File target=File.createTempFile("celikom-test36-copy-",".audio");
  final int[] progress={0};final long[] finalSize={-1};
  try{
   AudioTransfer.copy(target,()->new HttpURLConnection(new URL("https://example.invalid")){
    public void connect(){}public void disconnect(){}public boolean usingProxy(){return false;}
    public int getResponseCode(){return 200;}
    public long getContentLengthLong(){return payload.length;}
    public String getHeaderField(String name){return "ETag".equals(name)?"\"test36\"":null;}
    public InputStream getInputStream(){return new ByteArrayInputStream(payload);}
   },()->true,()->false,SystemClock::elapsedRealtime,(attempt,bytes,reason)->{},
    (bytes,total,now)->{progress[0]++;finalSize[0]=bytes;check(total==payload.length,"known content-length verified");});
   check(target.length()==payload.length&&finalSize[0]==payload.length&&progress[0]>2,
    "real bounded transfer publishes byte progress and completes identical file");
  }finally{target.delete();}
 }
 public static void main(String[] args)throws Exception{
  testTransferPolicy();testReuseInsteadOfRestart();testStallAndWrongEdition();testRealTransferProgress();
  System.out.println("PASS: "+checks+" Test.36 validated in-flight transfer takeover assertions");
 }
}
