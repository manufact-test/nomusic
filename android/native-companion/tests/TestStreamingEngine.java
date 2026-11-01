package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
import android.media.MediaPlayer;
import java.io.*;
public class TestStreamingEngine {
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static class Buffer extends BufferedAudio {
  Runnable beforeClose;public void close(){if(beforeClose!=null){Runnable r=beforeClose;beforeClose=null;r.run();}super.close();}
  boolean waiting;Buffer()throws Exception{super(File.createTempFile("celikom-stream-engine-",".test"),()->{throw new IOException("unused fake transport");},()->true,()->SystemClock.now,(n,b)->{});size=BLOCK*2;present.set(0);}
  public void prefetch(){}boolean stalled(){return waiting;}
 }
 static Buffer start()throws Exception{TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;TestEngine.e.arm();TestEngine.resolve();Buffer audio=new Buffer();TestEngine.api.streamed.done(audio,null);TestEngine.e.player.prepared.onPrepared(TestEngine.e.player);return audio;}
 public static void main(String[] args)throws Exception{
  Buffer audio=start();ReplacementEngine e=TestEngine.e;MediaPlayer player=e.player;check(player.playing&&!audio.complete()&&TestEngine.api.downloads==0,"actual engine plays from partial buffer without full download");
  audio.waiting=true;SystemClock.now+=300;TestEngine.p.current=TestEngine.source("1",1300,true);e.update(TestEngine.p.current);check(player.playing&&e.effect!=null,"a pending decoder read alone cannot interrupt playback");SystemClock.now+=500;TestEngine.p.current=TestEngine.source("1",1800,true);e.update(TestEngine.p.current);check(e.effect==null&&!player.playing&&e.bufferWaiting&&e.armed(),"buffer wait restores original and retains automatic mode");audio.waiting=false;SystemClock.now+=500;TestEngine.p.current=TestEngine.source("1",1800,true);e.update(TestEngine.p.current);check(player.playing&&e.effect!=null&&!e.bufferWaiting,"buffer resume aligns current source before restoring replacement");e.sourceBoundary("test_switch");check(audio.closed&&player.released&&e.effect==null&&!audio.file.exists(),"track boundary cancels partial reader and cannot cache incomplete audio");e.close();
  audio=start();e=TestEngine.e;player=e.player;player.error.onError(player,1,2);check(e.armed()&&e.effect==null&&audio.closed&&e.streamFallbackKey!=null,"codec error restores original and selects full-file fallback");SystemClock.now=e.nextLookup;TestEngine.p.current=TestEngine.source("1",2000,true);e.update(TestEngine.p.current);TestEngine.resolve();check(TestEngine.api.downloads==1&&e.preparing,"unsupported streaming retries full download automatically");e.close();
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;e=TestEngine.e;e.arm();TestEngine.resolve();NativeApi.StreamResult old=TestEngine.api.streamed;e.stop("owner_stop");audio=new Buffer();old.done(audio,null);check(audio.closed&&e.player==null&&!e.armed(),"late stream callback after Stop cannot revive playback");
  audio=start();e=TestEngine.e;audio.close();TestEngine.p.current=TestEngine.source("1",1200,true);e.update(TestEngine.p.current);check(e.player==null&&e.effect==null&&e.armed(),"cancelled stream cannot report playing or retain original attenuation");e.close();
  /* HONOR 0.3.73: 179ms seek ACK may still become a 187ms decoder-clock
     gap. The stricter gate must keep original audible, predict the WARM
     callback latency and verify advancement before permitting a blend. */
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;e=TestEngine.e;e.arm();TestEngine.resolve();audio=new Buffer();TestEngine.api.streamed.done(audio,null);player=e.player;player.asyncSeek=true;player.prepared.onPrepared(player);long initialPosition=player.position;
  SystemClock.now+=179;TestEngine.p.current=TestEngine.source("1",initialPosition+179,true);player.seek.onSeekComplete(player);check(player.seekCalls==1&&!e.seeking&&player.playing&&e.effect!=null,"179ms stream-seek residual must not trigger another seek");check(player.volume==0f&&e.effect.gain==0f,"source stays audible until advancing replacement clock is verified");
  SystemClock.now+=8;TestEngine.p.current=TestEngine.source("1",initialPosition+187,true);e.update(TestEngine.p.current);check(player.seekCalls==1&&player.playing,"cached decoder remains active without a second seek");
  SystemClock.now+=90;player.position+=90;TestEngine.p.handler.drain();
  check(player.seekCalls==2&&e.audioOwner.seekInFlight(player)
      &&player.volume==0f&&e.effect.gain==0f,
      "187ms projected stream drift requires one muted warm correction");
  // Android's warm callback is asynchronous: source advances while the same
  // verified original effect remains at full gain.
  SystemClock.now+=150;
  TestEngine.p.current=TestEngine.source("1",initialPosition+427,true);
  player.seek.onSeekComplete(player);
  check(player.volume==0f&&e.effect.gain==0f&&!e.audioOwner.seekInFlight(player),
      "warm ACK alone must never make replacement audible");
  SystemClock.now+=50;player.position+=50;
  TestEngine.p.current=TestEngine.source("1",initialPosition+477,true);
  TestEngine.p.handler.drain();
  check(e.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND,
      "corrected projected clock enters the one existing blend");
  SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS/4;
  player.position+=ReplacementEngine.UNIFIED_JOIN_MS/4;
  TestEngine.p.current=TestEngine.source("1",initialPosition+517,true);
  TestEngine.p.handler.drain();
  double sourceGain=Math.pow(10,e.effect.gain/20.0);
  check(e.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND
      &&sourceGain>0.6&&sourceGain<0.9f&&player.volume>0.1f&&player.volume<0.4f,
      "strictly verified streaming clock starts the same complementary entry");
  SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS+60;
  player.position+=ReplacementEngine.UNIFIED_JOIN_MS+60;
  TestEngine.p.current=TestEngine.source("1",initialPosition+737,true);
  TestEngine.p.handler.drain();check(player.volume>0.99f&&e.originalMix==0f&&e.effect.gain==-100f,
      "bounded correction completes original single-mode join: volume="+player.volume+" source="+e.originalMix+" gain="+e.effect.gain+" state="+e.audioOwner.state()+" fading="+e.fading);
  e.sourceBoundary("rapid_next");SystemClock.now+=500;TestEngine.p.handler.drain();check(player.released&&e.effect==null&&e.player==null,"queued longer fade cannot leak the old song over a new track");e.close();
  TestEngine.reset("ALBUM");e=TestEngine.e;e.arm();java.util.function.BooleanSupplier lookup=TestEngine.api.resolveValid;check(lookup.getAsBoolean(),"active lookup is current");e.sourceBoundary("skip_in_flight");check(!lookup.getAsBoolean(),"skipping a song invalidates queued and active lookup transport");e.close();
  // Report 17:58:55: decoder asks for data while playback can still advance.
  audio=start();e=TestEngine.e;player=e.player;int seekCount=player.seekCalls;audio.waiting=true;
  for(int i=1;i<=12;i++){SystemClock.now+=250;player.position+=250;TestEngine.p.current=TestEngine.source("1",1000+i*250,true);e.update(TestEngine.p.current);check(player.playing&&e.effect!=null&&!e.bufferWaiting&&player.seekCalls==seekCount,"read-ahead wait cannot create original/replacement oscillation at tick "+i);}
  audio.waiting=false;e.close();
  audio=start();e=TestEngine.e;player=e.player;player.asyncSeek=true;TestEngine.p.current=TestEngine.source("1",30000,true);e.update(TestEngine.p.current);seekCount=player.seekCalls;audio.waiting=true;SystemClock.now+=300;TestEngine.p.current=TestEngine.source("1",30300,true);e.update(TestEngine.p.current);check(e.seeking&&player.seekCalls==seekCount&&e.effect!=null&&e.effect.gain==0f,"waiting seek preserves full-gain original and its effect without cancelling/reissuing seek");audio.waiting=false;player.position=30300;player.seek.onSeekComplete(player);check(player.playing&&e.effect!=null,"one completed buffered seek resumes automatically");e.close();
  // isPlaying is true before a streaming decoder necessarily advances its clock.
  audio=start();e=TestEngine.e;player=e.player;SystemClock.now+=400;TestEngine.p.current=TestEngine.source("1",1400,true);TestEngine.p.handler.drain();check(e.originalMix==1f&&player.volume==0f,"frozen startup decoder never fades out original");player.position+=50;SystemClock.now+=50;TestEngine.p.current=TestEngine.source("1",1450,true);TestEngine.p.handler.drain();SystemClock.now+=200;player.position+=200;TestEngine.p.current=TestEngine.source("1",1650,true);TestEngine.p.handler.drain();SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS/4;player.position+=ReplacementEngine.UNIFIED_JOIN_MS/4;TestEngine.p.current=TestEngine.source("1",1650+ReplacementEngine.UNIFIED_JOIN_MS/4,true);TestEngine.p.handler.drain();check(e.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND
     &&Math.pow(10,e.effect.gain/20.0)>0.001&&player.volume>0f&&player.volume<1f,
     "decoder clock confirmation permits only bounded, ticketed linear entry");SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS;player.position+=ReplacementEngine.UNIFIED_JOIN_MS;TestEngine.p.current=TestEngine.source("1",1650+ReplacementEngine.UNIFIED_JOIN_MS/4+ReplacementEngine.UNIFIED_JOIN_MS,true);TestEngine.p.handler.drain();check(e.originalMix==0f&&player.volume>0.99f,"completed unified join grants replacement only");e.close();
  audio=start();e=TestEngine.e;player=e.player;SystemClock.now+=2100;TestEngine.p.current=TestEngine.source("1",3100,true);TestEngine.p.handler.drain();check(e.effect==null&&player.released&&e.armed()&&e.streamFallbackKey!=null,"frozen startup times out to original and full-file recovery");e.close();
  // 2026-10-28 Монпасье: a 2s seek timeout discarded a partial stream,
  // then downloaded all 9.5MB for 52.9s. Preserve the in-flight seek instead.
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;e=TestEngine.e;e.arm();TestEngine.resolve();audio=new Buffer();TestEngine.api.streamed.done(audio,null);player=e.player;player.asyncSeek=true;player.prepared.onPrepared(player);long requested=player.position;int issued=player.seekCalls;
  SystemClock.now+=2500;TestEngine.p.current=TestEngine.source("1",requested+2500,true);e.update(TestEngine.p.current);TestEngine.p.handler.drain();check(e.player==player&&e.seeking&&!audio.closed&&player.seekCalls==issued&&TestEngine.api.downloads==0&&e.effect==null,"recorded 2.5s data wait keeps original and existing stream, without full download or repeated seek");
  SystemClock.now+=500;TestEngine.p.current=TestEngine.source("1",requested+3000,true);player.seek.onSeekComplete(player);check(player.seekCalls==issued+1&&e.effect==null&&player.position==requested+3000,"3s network wait gets one current-position correction while inaudible");
  SystemClock.now+=20;TestEngine.p.current=TestEngine.source("1",requested+3020,true);player.seek.onSeekComplete(player);check(player.playing&&e.player==player&&TestEngine.api.downloads==0,"cached correction resumes same stream without restarting download");e.close();
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;e=TestEngine.e;e.arm();TestEngine.resolve();audio=new Buffer();TestEngine.api.streamed.done(audio,null);player=e.player;player.asyncSeek=true;player.prepared.onPrepared(player);SystemClock.now+=12001;TestEngine.p.current=TestEngine.source("1",13001,true);TestEngine.p.handler.drain();check(player.released&&audio.closed&&e.effect==null&&e.armed(),"a genuinely stuck partial seek still has a bounded timeout and restores original");e.close();
  // Cancellation can wait inside disconnect/stream cleanup. Old output must
  // already be inaudible before entering that potentially blocking work.
  audio=start();e=TestEngine.e;player=e.player;final MediaPlayer retiring=player;final ReplacementEngine engine=e;final boolean[] safe={false};
  Buffer checking=audio;checking.beforeClose=()->{safe[0]=retiring.volume==0f&&!retiring.playing&&retiring.released&&engine.player==null&&engine.effect==null;};e.sourceBoundary("recorded_papirosy_next");check(safe[0],"track boundary silences old player and restores original BEFORE stream cancellation");e.close();
  audio=start();e=TestEngine.e;audio.present.set(1);try(java.io.RandomAccessFile output=new java.io.RandomAccessFile(audio.file,"rw")){output.setLength(audio.size);}java.io.File retained=audio.file;e.sourceBoundary("completed_stream_boundary");check(audio.closed&&retained.exists()&&e.recentAudio.containsValue(retained),"real MediaDataSource-close semantics preserve completed audio before releasing decoder");e.close();check(!retained.exists(),"Stop still deletes retained private audio");
  /* Report 20:13: Было давно: 3400ms initial seek + 1784ms correction.
     Previously the second residual became audible, then caused another seek. */
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;e=TestEngine.e;e.arm();TestEngine.resolve();audio=new Buffer();TestEngine.api.streamed.done(audio,null);player=e.player;player.asyncSeek=true;player.prepared.onPrepared(player);requested=player.position;
  SystemClock.now+=3400;TestEngine.p.current=TestEngine.source("1",requested+3400,true);player.seek.onSeekComplete(player);
  SystemClock.now+=1784;TestEngine.p.current=TestEngine.source("1",requested+5184,true);player.seek.onSeekComplete(player);check(!player.playing&&e.effect==null&&e.seeking&&player.seekCalls==3,"recorded second slow correction cannot expose 1784ms-late replacement");
  SystemClock.now+=53;TestEngine.p.current=TestEngine.source("1",requested+5237,true);player.seek.onSeekComplete(player);check(player.playing&&player.seekCalls==3,"cached final correction starts aligned within 53ms");
  for(int i=1;i<=8;i++){SystemClock.now+=250;player.position+=250;TestEngine.p.current=TestEngine.source("1",requested+5237+i*250,true);e.update(TestEngine.p.current);TestEngine.p.handler.drain();check(player.seekCalls==3&&player.playing,"aligned report replay cannot create an audible follow-up seek at tick "+i);}e.close();
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;e=TestEngine.e;e.arm();TestEngine.resolve();audio=new Buffer();TestEngine.api.streamed.done(audio,null);player=e.player;player.asyncSeek=true;player.prepared.onPrepared(player);requested=player.position;
  for(int i=1;i<=3;i++){SystemClock.now+=1800;TestEngine.p.current=TestEngine.source("1",requested+i*1800,true);player.seek.onSeekComplete(player);}
  check(player.released&&e.effect==null&&e.armed()&&player.seekCalls==3,"unsteady alignment has a bounded silent retry count and keeps original available");e.close();
  System.out.println("PASS: "+checks+" actual engine progressive playback, buffering recovery, fallback and cancellation checks");
 }
}
