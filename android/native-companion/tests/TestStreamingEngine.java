package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
import android.media.MediaPlayer;
import java.io.*;
public class TestStreamingEngine {
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static class Buffer extends BufferedAudio {
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
  // Actual report: first range seek spent 179ms waiting for data, next seek is cached.
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;e=TestEngine.e;e.arm();TestEngine.resolve();audio=new Buffer();TestEngine.api.streamed.done(audio,null);player=e.player;player.asyncSeek=true;player.prepared.onPrepared(player);long initialPosition=player.position;
  SystemClock.now+=179;TestEngine.p.current=TestEngine.source("1",initialPosition+179,true);player.seek.onSeekComplete(player);check(player.seekCalls==2&&!player.playing&&e.effect==null,"179ms stream-seek residual is corrected while original still plays");check(player.position==initialPosition+179,"cached correction uses current source, not extrapolated old network latency");
  SystemClock.now+=8;TestEngine.p.current=TestEngine.source("1",initialPosition+187,true);player.seek.onSeekComplete(player);check(player.playing&&Math.abs(e.position(TestEngine.p.current)-player.position)<=10,"cached seek joins within ten milliseconds in recorded-delay replay");
  SystemClock.now+=90;TestEngine.p.current=TestEngine.source("1",initialPosition+277,true);TestEngine.p.handler.drain();check(player.volume>0&&player.volume<0.3f&&e.originalMix>0.7f,"first quarter of transition eases in instead of jumping to full volume");
  e.sourceBoundary("rapid_next");SystemClock.now+=500;TestEngine.p.handler.drain();check(player.released&&e.effect==null&&e.player==null,"queued longer fade cannot leak the old song over a new track");e.close();
  TestEngine.reset("ALBUM");e=TestEngine.e;e.arm();java.util.function.BooleanSupplier lookup=TestEngine.api.resolveValid;check(lookup.getAsBoolean(),"active lookup is current");e.sourceBoundary("skip_in_flight");check(!lookup.getAsBoolean(),"skipping a song invalidates queued and active lookup transport");e.close();
  // Report 17:58:55: decoder asks for data while playback can still advance.
  audio=start();e=TestEngine.e;player=e.player;int seekCount=player.seekCalls;audio.waiting=true;
  for(int i=1;i<=12;i++){SystemClock.now+=250;player.position+=250;TestEngine.p.current=TestEngine.source("1",1000+i*250,true);e.update(TestEngine.p.current);check(player.playing&&e.effect!=null&&!e.bufferWaiting&&player.seekCalls==seekCount,"read-ahead wait cannot create original/replacement oscillation at tick "+i);}
  audio.waiting=false;e.close();
  audio=start();e=TestEngine.e;player=e.player;player.asyncSeek=true;TestEngine.p.current=TestEngine.source("1",30000,true);e.update(TestEngine.p.current);seekCount=player.seekCalls;audio.waiting=true;SystemClock.now+=300;TestEngine.p.current=TestEngine.source("1",30300,true);e.update(TestEngine.p.current);check(e.seeking&&player.seekCalls==seekCount&&e.effect==null,"waiting seek restores original without cancelling/reissuing seek");audio.waiting=false;player.position=30300;player.seek.onSeekComplete(player);check(player.playing&&e.effect!=null,"one completed buffered seek resumes automatically");e.close();
  System.out.println("PASS: "+checks+" actual engine progressive playback, buffering recovery, fallback and cancellation checks");
 }
}
