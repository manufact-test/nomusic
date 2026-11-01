package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;
import java.io.File;

/** Isolated A/B source-path experiment: live Android uses full local files. */
public final class TestFullFileSeekExperiment {
 static int checks;
 static void check(boolean okay,String why){checks++;if(!okay)throw new AssertionError(why);}

 static void fullFileLoadsWithoutStreamAndSeeksLocally()throws Exception{
  TestEngine.reset("ALBUM",true);
  ReplacementEngine engine=TestEngine.e;
  check(engine.fullFileExperiment,"the installed candidate selects full-file playback");
  engine.arm();
  check(engine.player==null&&engine.effect==null&&TestEngine.api.resolves==1,
    "a fresh authenticated resolve still precedes every replacement");
  TestEngine.resolve();
  check(TestEngine.api.downloads==1&&TestEngine.api.streamed==null
      &&TestEngine.api.valid.getAsBoolean()&&engine.preparing,
    "the candidate requests one bounded full download, never a range stream");
  File file=File.createTempFile("celikom-full-experiment-",".audio");
  TestEngine.api.downloaded.done(file,null);
  MediaPlayer decoder=engine.player;
  check(decoder!=null&&engine.audioFile==file
      &&decoder.dataSource==null&&engine.streaming==null
      &&"full_download_file".equals(engine.audioSourceKind),
    "MediaPlayer receives the private local file, not a MediaDataSource");
  decoder.prepared.onPrepared(decoder);
  check(engine.localPrewarmWarmupPending&&decoder.volume==0f&&engine.effect!=null
      &&engine.effect.gain==0f&&engine.originalMix==1f,
    "download and decoder startup do not silence the original");

  TestCachedAudioRollback.advanceWarmup(decoder,10,20,8);
  TestCachedAudioRollback.advanceTogether(decoder,10,20);
  check(engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT
      &&decoder.volume>0.99f&&engine.effect.gain==-100f,
    "the existing original-to-replacement handover works for a full local file");

  int originalDownloads=TestEngine.api.downloads;
  int originalSeeks=decoder.seekCalls;
  decoder.asyncSeek=true;
  engine.sourceSeekRequested();
  TestEngine.p.current=TestEngine.source("1",42000,true);
  engine.update(TestEngine.p.current);
  check(engine.seeking&&decoder.seekCalls==originalSeeks+1
      &&decoder.volume==0f&&engine.effect.gain==0f,
    "finger seek uses the same decoder and retains original output");
  SystemClock.now+=60;
  TestEngine.p.current=TestEngine.source("1",42060,true);
  decoder.seek.onSeekComplete(decoder);
  check(!engine.seeking&&decoder.playing&&engine.player==decoder,
    "a local seek ACK resumes the retained decoder");
  TestCachedAudioRollback.advanceTogether(decoder,8,250);
  check(TestEngine.api.downloads==originalDownloads&&TestEngine.api.streamed==null
      &&decoder.seekCalls==originalSeeks+1,
    "manual seek does not issue new network work or redundant correction");

  TestEngine.p.current=TestEngine.source("1",44000,false);
  engine.update(TestEngine.p.current);
  check(!decoder.playing&&engine.effect!=null,
    "Pause retains the existing decoder/effect without new transport");
  TestEngine.p.current=TestEngine.source("1",44000,true);
  engine.update(TestEngine.p.current);
  check(decoder.playing&&engine.player==decoder,
    "Resume uses the same prepared local file");

  engine.sourceBoundary("manual_next");
  check(decoder.released&&engine.player==null&&engine.effect==null
      &&engine.recentAudio.containsValue(file)&&file.exists(),
    "Next restores the original and retains only a bounded private cache file");
  engine.stop("owner_stop");
  check(!file.exists()&&engine.recentAudio.isEmpty(),
    "Stop removes the temporary file and cannot retain a playback lease");
 }

 static void deadlineFailureAndCancellationRemainFailOpen()throws Exception{
  TestEngine.reset("ALBUM",true);
  ReplacementEngine engine=TestEngine.e;
  engine.arm();TestEngine.resolve();
  check(TestEngine.api.valid.getAsBoolean(),"new source has a valid download lease");
  SystemClock.now+=ReplacementEngine.FULL_FILE_EXPERIMENT_BUDGET_MS+1;
  check(!TestEngine.api.valid.getAsBoolean(),
    "experimental full download expires after the declared 20-second budget");
  TestEngine.api.downloaded.done(null,"audio_download_failed");
  check(engine.player==null&&engine.effect==null&&engine.armed(),
    "download timeout leaves the original audible and automatic mode enabled");

  TestEngine.reset("ALBUM",true);
  engine=TestEngine.e;
  engine.arm();TestEngine.resolve();
  NativeApi.AudioResult pending=TestEngine.api.downloaded;
  engine.stop("owner_stop");
  File stale=File.createTempFile("celikom-stale-experiment-",".audio");
  pending.done(stale,null);
  check(!stale.exists()&&engine.player==null&&engine.effect==null,
    "a late result after Stop is deleted before it can be played");
 }

 public static void main(String[] args)throws Exception{
  fullFileLoadsWithoutStreamAndSeeksLocally();
  deadlineFailureAndCancellationRemainFailOpen();
  System.out.println("PASS: "+checks+" full-file source-path, seek, pause, Next, timeout and cancellation checks");
 }
}
