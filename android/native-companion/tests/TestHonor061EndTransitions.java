package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;

/* Recorded HONOR 0.3.61: near-tail Media3 SEEK boundaries must be observational
   until the new alias is confirmed. Preserve the audio path accepted by user. */
public final class TestHonor061EndTransitions {
 static int checks;
 static void ok(boolean valid,String why){checks++;if(!valid)throw new AssertionError(why);}

 static void earlyNextCandidateIsReadOnly()throws Exception {
  /* Remaining native Yandex timer at outgoing reset: 6.677, 3.620,
     5.892 and 6.777 seconds. Not proof of natural-song completion. */
  for(int remaining:new int[]{6677,3620,5892,6777}){
   TestEngine.playing();
   ReplacementEngine e=TestEngine.e;
   MediaPlayer old=e.player;
   DynamicsProcessing fx=e.effect;
   old.position=120000-remaining;
   TestEngine.p.current=TestEngine.source("1",120000-remaining,true);
   e.update(TestEngine.p.current);
   int seeks=old.seekCalls,downloads=TestEngine.api.downloads;
   e.outgoingTrackReset(TestEngine.p.current);
   ok(e.player==old&&!old.released&&e.effect==fx&&old.seekCalls==seeks
       &&TestEngine.api.downloads==downloads,
       "0.3.61 near-tail candidate must not cancel/reseek old decoder at remaining "+remaining);
   ok(e.armed()&&e.identityKey!=null,
       "source candidate alone cannot advance/retire the current identity");
   e.sourceBoundary("confirmed_new_alias");
   ok(old.released&&!old.playing&&old.volume==0f&&e.effect==null&&e.player==null,
       "confirmed new identity silences old decoder before source restoration");
   ok(e.identityKey==null&&e.trackId==null,
       "next song must reestablish a verified identity before playback");
   e.close();
  }
 }
 static void actualEndOnlyAfterNativeDuration()throws Exception {
  TestEngine.playing();
  ReplacementEngine e=TestEngine.e;
  MediaPlayer old=e.player;
  old.position=119999;
  TestEngine.p.current=TestEngine.source("1",119999,true);
  e.update(TestEngine.p.current);
  ok(e.player==old&&!old.released,
      "one millisecond remaining cannot be treated as source end");
  TestEngine.p.current=TestEngine.source("1",120000,true);
  e.update(TestEngine.p.current);
  ok(old.released&&!old.playing&&old.volume==0f&&e.effect==null,
      "verified native source end restores original and retires decoder");
  ok(e.completedKey!=null&&e.armed(),
      "natural end waits for confirmed following song, retaining automatic mode");
  e.close();
 }
 public static void main(String[] args)throws Exception {
  earlyNextCandidateIsReadOnly();
  actualEndOnlyAfterNativeDuration();
  System.out.println("PASS: "+checks+" HONOR 0.3.61 near-tail/confirmed-boundary and native-end acceptance gates");
 }
}
