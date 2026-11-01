package pro.celikom.nativeprobe.identitydiag;
import org.json.JSONObject;
import android.os.SystemClock;
import android.media.MediaPlayer;

/** Replays 0.3.51 HONOR failures, not synthetic successful-only paths. */
public final class TestRealFailures {
 static int checks;
 static void check(boolean value,String what){checks++;if(!value)throw new AssertionError(what);}
 static void sample(ReplacementEngine e,long position){
  TestEngine.p.current=TestEngine.source("1",position,true);
  e.update(TestEngine.p.current);
  TestEngine.p.handler.drain();
 }
 public static void main(String[] args)throws Exception {
  check(PlaybackDuration.compatible(221930,223399,223399,true),
      "recorded 1469ms measured edition can be a bounded verified outro");
  check(!PlaybackDuration.compatible(221930,223399,223399,false),
      "unverified 1469ms title-only match must not be forced on native playback");
  TestEngine.reset("ALBUM");
  ReplacementEngine e=TestEngine.e;e.arm();
  TestEngine.api.resolved.done(new JSONObject()
    .put("found",true).put("replacement_id",10).put("duration_ms",121469),null);
  check(e.player==null&&e.effect==null&&e.preparing,
      "the recorded 1469ms metadata difference can only begin an inaudible verification");
  java.io.File wrongFile=java.io.File.createTempFile("honor-wrong-edition", ".audio");
  TestEngine.api.downloaded.done(wrongFile,null);
  check(e.player!=null&&e.effect==null,"no original attenuation before measuring the replacement decoder");
  e.player.duration=121469;e.player.prepared.onPrepared(e.player);
  check(e.ready&&e.effect!=null&&e.player!=null,
      "recorded 1469ms approved album replacement starts automatically within the bounded tail policy");
  int lookups=TestEngine.api.resolves;
  SystemClock.now+=10000;sample(e,11000);
  check(TestEngine.api.resolves==lookups&&e.ready,
      "same accepted song must not repeatedly download while playing");
  TestEngine.p.current=TestEngine.source("2",0,true);
  e.identity(LogStore.map("mediaAlias","2","albumId","42",
     "title","Песня","artist","Артист","durationMs",120000L),
     LogStore.map("candidateTrackId","8","method","ALBUM"));
  check(e.completedKey==null&&TestEngine.api.resolves==lookups+1,
      "next native song automatically begins its own verified lookup, no rearm needed");
  e.close();

  DriftGuard guard=new DriftGuard();
  check(!guard.confirmed(true,true,1160,1000),"large clock drift requires confirmation");
  check(!guard.confirmed(true,true,1160,2200),"single 1.2s offset is not terminal");
  check(guard.confirmed(true,true,1160,2601),"sustained HONOR 1160ms divergence must fail open");
  guard.reset();
  check(!guard.confirmed(true,true,1160,4000),"reset invalidates stale evidence");
  check(!guard.confirmed(true,true,200,6200),"ordinary stable Bluetooth offset is allowed");
  check(!guard.confirmed(false,true,1100,9000),"unaligned seeks cannot trip the guard");
  check(!guard.confirmed(true,false,1100,9200),"paused/nonplaying source cannot trip guard");

  TestEngine.playing();e=TestEngine.e;
  MediaPlayer mp=e.player;
  SystemClock.now+=500;mp.position=1500;sample(e,1500);
  check(e.effect!=null&&!e.fading&&e.aligned,
      "drift test begins only after successful exclusive-audio handover");
  for(int i=0;i<9 && e.player!=null;i++){
   SystemClock.now+=300;
   long nativePosition=1800L+i*300;
   mp.position=nativePosition-1160;
   sample(e,nativePosition);
  }
  check(e.player==null&&e.effect==null&&e.armed()&&mp.released,
      "sustained drift restores original and releases unsafe decoder without stopping auto mode");
  check(e.status.contains("рассинхрон")&&e.completedKey!=null&&e.audioOwner.state()==AudioOwnership.State.TRACK_UNSUPPORTED,
      "unsafe drift reports specific reason and only blocks this track");
  e.close();

  TestEngine.playing();e=TestEngine.e;mp=e.player;
  SystemClock.now+=500;mp.position=1500;sample(e,1500);
  for(int i=0;i<12;i++){
   SystemClock.now+=300;
   long nativePosition=1800L+i*300;
   mp.position=nativePosition-240;
   sample(e,nativePosition);
  }
  check(e.player==mp&&!mp.released&&e.effect!=null,
      "normal 240ms hardware clock offset does not cause audible reattach or fail-open");
  e.close();
  System.out.println("PASS: "+checks+" real HONOR wrong-edition and persistent-drift fail-open checks");
 }
}
