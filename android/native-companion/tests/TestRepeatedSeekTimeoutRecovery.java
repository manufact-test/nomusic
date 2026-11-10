package pro.celikom.nativeprobe.identitydiag;

import android.os.SystemClock;
import android.media.MediaPlayer;
import org.json.JSONObject;
import java.io.File;

/**
 * Drives the ACTUAL Test.50 ReplacementEngine against existing fake Android
 * transport/MediaPlayer. This is NOT a recording of the owner's HONOR.
 */
public final class TestRepeatedSeekTimeoutRecovery {
 static int assertions;
 static void check(boolean ok,String msg){
  assertions++;
  if(!ok)throw new AssertionError(msg+" assertion="+assertions);
 }
 static void preparedReplacement()throws Exception{
  TestEngine.reset("ALBUM");
  TestEngine.e.arm();
  TestEngine.prepare();
  check(TestEngine.e.player!=null&&TestEngine.e.ready,
    "real engine fake current decoder is prepared before induced timeout");
 }
 static void exerciseRepeatAndRewind()throws Exception{
  preparedReplacement();
  ReplacementEngine e=TestEngine.e;
  String current=e.identityKey;
  check(current!=null&&e.armed(),"owner's automatic mode is active");
  MediaPlayer first=e.player;
  e.suspend("seek_timeout",e.retryDelay());
  check(first.released&&e.player==null&&e.effect==null,
    "one timeout releases secondary and restores original ownership");
  check(e.completedKey==null&&e.armed()&&!e.seekTimeoutBreaker.blocked(current),
    "first timeout retains legacy retry behavior and does NOT block this track");

  // First timeout retains Test.50's own retryDelay(), which may be
  // longer than a fixed 2s; wait for its actual deterministic deadline.
  SystemClock.now=Math.max(SystemClock.now+2000,e.nextLookup+100);
  TestEngine.p.current=TestEngine.source("1",1600,true);
  int beforeRetry=TestEngine.api.resolves;
  e.update(TestEngine.p.current);
  check(TestEngine.api.resolves==beforeRetry+1,
    "one timeout may create exactly one new authorized same-track resolve");
  TestEngine.api.resolved.done(TestEngine.found(),null);
  File audio=File.createTempFile("seek-failopen-model", ".audio");
  TestEngine.api.downloaded.done(audio,null);
  check(e.player!=null,"second candidate decoder exists only after normal authorization");
  // The problematic HONOR case is a native seek WITHOUT a completion ACK.
  // Fake MediaPlayer defaults to an immediate successful seek callback; turn
  // that off BEFORE onPrepared, otherwise the success legitimately clears
  // the first timeout streak and the test would be asserting a false bug.
  e.player.asyncSeek=true;
  e.player.prepared.onPrepared(e.player);
  check(e.ready&&e.player!=null,
    "second Test.50 attempt prepares but its decoder seek remains unacknowledged");

  MediaPlayer second=e.player;
  SystemClock.now+=1000;
  e.suspend("seek_timeout",e.retryDelay());
  check(second.released&&e.player==null&&e.effect==null,
    "second timeout releases decoder and source attenuation immediately");
  check(e.seekTimeoutBreaker.blocked(current)&&current.equals(e.completedKey),
    "second same-track timeout latches original through current source generation");
  check(e.audioOwner.state()==AudioOwnership.State.TRACK_UNSUPPORTED,
    "no output grant after repeated decoder timeout");
  check(e.completedReason!=null&&e.completedReason.contains("оригинал"),
    "show fail-open status instead of repeated loading");

  int afterLatch=TestEngine.api.resolves;
  TestEngine.p.current=TestEngine.source("1",100,true);
  e.update(TestEngine.p.current);
  check(TestEngine.api.resolves==afterLatch&&e.player==null
      &&e.seekTimeoutBreaker.blocked(current),
    "backward scrub cannot rearm a failed same-track decoder");

  e.sourceBoundary("manual_next","2");
  TestEngine.p.current=TestEngine.source("2",0,true);
  check(!e.seekTimeoutBreaker.blocked(current)&&e.completedKey==null,
    "only Next/real boundary resets timed-out source lease");
  e.identity(LogStore.map("mediaAlias","2","albumId","42",
       "title","Песня","artist","Артист","durationMs",120000L),
       LogStore.map("candidateTrackId","8","method","ALBUM"));
  check(TestEngine.api.resolves==afterLatch+1,
    "different song gets its own normal signed lookup");
  e.close();
 }
 static void noIdentityCannotLatch()throws Exception{
  preparedReplacement();
  ReplacementEngine e=TestEngine.e;
  e.sourceBoundary("identity_missing",null);
  check(e.identityKey==null,"not attached after boundary");
  e.suspend("seek_timeout",e.retryDelay());
  check(!e.seekTimeoutBreaker.blocked(null)&&e.completedKey==null,
    "late unidentified timeout cannot grant or block a live replacement");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  exerciseRepeatAndRewind();
  noIdentityCannotLatch();
  System.out.println("PASS: "+assertions+
    " engine-fake repeated-seek fallback and true Next isolation checks; no HONOR audio measured");
 }
}
