package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import java.io.File;
import java.io.IOException;

/** Test.25 opt-in cold-start path. The approved full-file constructor is unchanged. */
public final class TestProgressiveCold {
 static int checks;
 static void check(boolean yes,String reason){checks++;if(!yes)throw new AssertionError(reason);}
 static final class Sparse extends BufferedAudio {
  Sparse()throws Exception{
   super(File.createTempFile("test25-cold-", ".audio"),()->{throw new IOException("no network in host fake");},
    ()->true,()->android.os.SystemClock.now,(name,bytes)->{});
   size=BLOCK*8;present.set(0);present.set(1);present.set(7);
  }
  public void prefetch(){}
 }
 static ReplacementEngine cold(boolean stream)throws Exception{
  TestEngine.reset("ALBUM",true);
  TestEngine.api.useStreaming=stream;
  ReplacementEngine old=TestEngine.e;
  old.close();
  TestEngine.e=new ReplacementEngine(TestEngine.p,true,true);
  TestEngine.e.coldJoinExclusiveExperiment=false;
  TestEngine.e.identity(LogStore.map("mediaAlias","1","albumId","42","title","Песня",
    "artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","7","method","ALBUM","editionConflict",false));
  TestEngine.e.arm();
  TestEngine.resolve();
  return TestEngine.e;
 }
 public static void main(String[] args)throws Exception{
  ReplacementEngine e=cold(true);
  check(e.progressiveColdAllowed&&e.preparing&&TestEngine.api.downloads==0
    &&TestEngine.api.streamed!=null,"eligible cold current starts sparse verification without a full-file download");
  Sparse ready=new Sparse();
  TestEngine.api.streamed.done(ready,null);
  check(e.player!=null&&e.streaming==ready&&e.audioFile==null
    &&TestEngine.api.downloads==0,"verified sparse blocks reach the one decoder before whole file downloads");
  MediaPlayer player=e.player;
  player.prepared.onPrepared(player);
  check(e.ready&&e.effect!=null,"native duration, account and audio-owner gates still protect progressive prepare");
  e.sourceBoundary("skip_during_sparse_stream");
  check(ready.closed&&player.released&&!ready.file.exists(),"Next revokes incomplete streaming file and player together");
  e.close();

  e=cold(false);
  check(e.preparing&&TestEngine.api.currentDownloads==1
    &&e.streamFallbackKey!=null&&e.streaming==null,"unavailable Range falls back to accepted full-file transfer exactly once");
  check(e.effect==null&&e.player==null,"failed sparse preflight never mutes the original");
  e.close();

  TestEngine.reset("ALBUM",true);
  check(!TestEngine.e.progressiveColdAllowed&&TestEngine.e.fullFileExperiment,
    "frozen local-file constructor remains the default for established audio regression tests");
  TestEngine.e.close();
  System.out.println("PASS: "+checks+" Test.25 progressive cold-start and rollback gates");
 }
}
