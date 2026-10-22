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
  audio.waiting=true;SystemClock.now+=300;TestEngine.p.current=TestEngine.source("1",1300,true);e.update(TestEngine.p.current);check(e.effect==null&&!player.playing&&e.bufferWaiting&&e.armed(),"buffer wait restores original and retains automatic mode");audio.waiting=false;SystemClock.now+=500;TestEngine.p.current=TestEngine.source("1",1800,true);e.update(TestEngine.p.current);check(player.playing&&e.effect!=null&&!e.bufferWaiting,"buffer resume aligns current source before restoring replacement");e.sourceBoundary("test_switch");check(audio.closed&&player.released&&e.effect==null&&!audio.file.exists(),"track boundary cancels partial reader and cannot cache incomplete audio");e.close();
  audio=start();e=TestEngine.e;player=e.player;player.error.onError(player,1,2);check(e.armed()&&e.effect==null&&audio.closed&&e.streamFallbackKey!=null,"codec error restores original and selects full-file fallback");SystemClock.now=e.nextLookup;TestEngine.p.current=TestEngine.source("1",2000,true);e.update(TestEngine.p.current);TestEngine.resolve();check(TestEngine.api.downloads==1&&e.preparing,"unsupported streaming retries full download automatically");e.close();
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;e=TestEngine.e;e.arm();TestEngine.resolve();NativeApi.StreamResult old=TestEngine.api.streamed;e.stop("owner_stop");audio=new Buffer();old.done(audio,null);check(audio.closed&&e.player==null&&!e.armed(),"late stream callback after Stop cannot revive playback");
  audio=start();e=TestEngine.e;audio.close();TestEngine.p.current=TestEngine.source("1",1200,true);e.update(TestEngine.p.current);check(e.player==null&&e.effect==null&&e.armed(),"cancelled stream cannot report playing or retain original attenuation");e.close();
  System.out.println("PASS: "+checks+" actual engine progressive playback, buffering recovery, fallback and cancellation checks");
 }
}
