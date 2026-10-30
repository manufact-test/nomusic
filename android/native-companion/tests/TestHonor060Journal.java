package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;
import android.os.SystemClock;

/* 0.3.60 HONOR failures: these are user-perceived latency acceptance gates.
   A working owner state is insufficient if it repeats needless seeks. */
public final class TestHonor060Journal {
 static int checks;
 static void ok(boolean condition,String message){
  checks++;if(!condition)throw new AssertionError(message);
 }
 static void pauseRetainsDecoder()throws Exception{
  /* Actual 0.3.60 paused resume: 126/132/238/299ms drift,
     while the verified native session/track/effect never changed. */
  for(int drift:new int[]{126,132,238,299}){
   TestEngine.playing();ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
   int calls=p.seekCalls;int downloads=TestEngine.api.downloads;
   TestEngine.p.current=TestEngine.source("1",1000,false);e.update(TestEngine.p.current);
   ok(e.pausedAt>=0&&!p.playing&&e.effect!=null,"user pause retains prepared audio");
   SystemClock.now+=937;
   TestEngine.p.current=TestEngine.source("1",1000+drift,true);e.update(TestEngine.p.current);
   ok(e.player==p&&e.effect!=null&&TestEngine.api.downloads==downloads,
      "pause must not rebuild decoder/effect or download");
   ok(p.seekCalls==calls&&!e.seeking,
      "RED 0.3.60: retained same-track resume <=350ms must not re-seek");
   ok(p.playing&&p.volume>0.99f&&e.originalMix==0f,
      "RED 0.3.60: verified retained decoder resumes without a new original/secondary handover");
   e.close();
  }
 }
 static void noUnnecessaryStreamingCorrection()throws Exception{
  /* Actual 0.3.60 initial seek residual 204ms: another seek was
     issued despite the existing 350ms handover drift budget. */
  TestStreamingEngine.Buffer data=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  p.asyncSeek=true;TestEngine.p.current=TestEngine.source("1",30000,true);e.update(TestEngine.p.current);
  int calls=p.seekCalls;ok(e.seeking,"streaming seeks are asynchronous");
  SystemClock.now+=204;TestEngine.p.current=TestEngine.source("1",30204,true);
  p.seek.onSeekComplete(p);
  ok(p.seekCalls==calls&&!e.seeking,
     "RED 0.3.60: 204ms residual inside handover clock budget does not justify another seek");
  ok(e.player==p&&!data.closed,"a single seek retains streaming decoder and data");
  e.close();
 }
 static void briefSourceReconnectKeepsTransportLease()throws Exception{
  /* Actual 0.3.60 at 15.913s source refresh -> stream_interrupted ->
     1.7s re-resolution and a 5.37s new-track handover. */
  TestStreamingEngine.Buffer data=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;
  java.util.function.BooleanSupplier lease=TestEngine.api.streamValid;
  ok(lease!=null&&lease.getAsBoolean(),"stream data lease is live");
  TestEngine.p.current=null;e.update(null);
  ok(!data.closed&&e.player!=null,"short source outage retains prepared reader");
  ok(lease.getAsBoolean(),
    "RED 0.3.60: transient null Media3 snapshot must not cancel same-account/same-track cached audio");
  TestEngine.p.current=TestEngine.source("1",1200,true);e.update(TestEngine.p.current);
  ok(lease.getAsBoolean(),"same track return retains source data lease");
  e.sourceBoundary("verified_next");
  ok(!lease.getAsBoolean(),"confirmed next track immediately revokes old data lease");
  e.close();
  data=TestStreamingEngine.start();e=TestEngine.e;lease=TestEngine.api.streamValid;
  TestEngine.api.accountGeneration++;
  ok(!lease.getAsBoolean(),"account change immediately cancels old stream data lease");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  pauseRetainsDecoder();noUnnecessaryStreamingCorrection();
  briefSourceReconnectKeepsTransportLease();
  System.out.println("PASS: "+checks+" HONOR 0.3.60 end-to-end pause/seek/source-refresh regression checks");
 }
}
