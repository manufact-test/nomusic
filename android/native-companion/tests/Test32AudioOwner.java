package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;

/** Test.31 HONOR failures: sparse first grant and zero-ramp regrant. */
public final class Test32AudioOwner {
 static int checks;
 static void check(boolean yes,String why){checks++;if(!yes)throw new AssertionError(why);}
 static void tick(MediaPlayer player,int ms){
  SystemClock.now+=ms;player.position+=ms;
  TestEngine.p.current=TestEngine.source("1",TestEngine.p.current.position+ms,true);
  TestEngine.p.handler.drain();
 }
 static void sparseRunway()throws Exception{
  TestEngine.reset("ALBUM");TestEngine.api.useStreaming=true;
  TestEngine.e.arm();TestEngine.resolve();
  TestStreamingEngine.Buffer incomplete=new TestStreamingEngine.Buffer();
  incomplete.runwayReady=false;
  TestEngine.api.streamed.done(incomplete,null);
  ReplacementEngine engine=TestEngine.e;MediaPlayer decoder=engine.player;
  decoder.prepared.onPrepared(decoder);
  for(int i=0;i<15;i++)tick(decoder,40);
  check(engine.effect!=null&&engine.originalMix==1f&&decoder.volume==0f
      &&!engine.audioOwner.state().equals(AudioOwnership.State.REPLACEMENT),
      "single verified sparse block cannot receive audible ownership");
  check(engine.player==decoder&&decoder.playing&&engine.fading,
      "original remains audible while the same decoder and prefetch prepare runway");
  incomplete.runwayReady=true;
  for(int i=0;i<14;i++)tick(decoder,40);
  check(engine.player==decoder&&engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT
      &&engine.originalMix==0f&&decoder.volume>0.99f,
      "only verified contiguous future runway authorizes the same decoder");
  // HONOR «Толер»: the first joined sparse stream later blocked, and Test.31
  // re-entered the same underbuffered decoder. A confirmed post-grant stall
  // must instead fail open and take the proven full-file retry on this track.
  incomplete.waiting=true;
  SystemClock.now+=350;
  TestEngine.p.current=TestEngine.source("1",TestEngine.p.current.position+350,true);
  engine.update(TestEngine.p.current);
  SystemClock.now+=600;
  TestEngine.p.current=TestEngine.source("1",TestEngine.p.current.position+600,true);
  engine.update(TestEngine.p.current);
  check(engine.player==null&&engine.effect==null&&engine.armed()
      &&engine.streamFallbackKey!=null,
      "post-grant sparse starvation restores original without same-stream oscillation");
  SystemClock.now=engine.nextLookup;
  TestEngine.p.current=TestEngine.source("1",TestEngine.p.current.position,true);
  engine.update(TestEngine.p.current);TestEngine.resolve();
  check(TestEngine.api.downloads==1&&engine.preparing,
      "stream starvation retries only the validated full-file path");
  engine.close();
 }
 static void noInstantRegrant()throws Exception{
  TestEngine.playing();ReplacementEngine engine=TestEngine.e;
  MediaPlayer decoder=engine.player;
  for(int i=0;i<10;i++)tick(decoder,20);
  check(engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
    "warm track owns sound before simulated post-seek restore");
  // Model a legitimate BUFFERING/seek state after source gain has returned.
  // Test.31 used to call grantReplacement() immediately from update().
  engine.audioOwner.aligning();engine.setAuditedVolume(decoder,0f);
  engine.audioOwner.sourceGainDuringAlignment(engine.effect);
  engine.originalMix=1f;engine.aligned=true;engine.fading=false;
  engine.update(TestEngine.p.current);
  check(engine.fading&&decoder.volume==0f&&engine.originalMix==1f,
    "audible original must NEVER become 100%-replacement in one update tick");
  for(int i=0;i<14;i++)tick(decoder,20);
  check(engine.audioOwner.state()==AudioOwnership.State.REPLACEMENT
      &&decoder.volume>0.99f&&engine.originalMix==0f,
      "regrant uses one finite ticketed clock-gated transfer");
  engine.close();
 }
 public static void main(String[] args)throws Exception{
  sparseRunway();noInstantRegrant();
  System.out.println("PASS: "+checks+" Test.32 sparse and zero-ramp source regrant regressions");
 }
}
