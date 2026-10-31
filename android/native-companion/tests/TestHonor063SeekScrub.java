package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;
import android.os.SystemClock;
import android.media.audiofx.DynamicsProcessing;

/** Replay of 26 scrubs in the 0.3.63 HONOR journal: avoid two audible owner
 * swaps on every short user seek, while long decoder stalls fail open. */
public final class TestHonor063SeekScrub {
 static int checks;
 static void check(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
 static ReplacementEngine ready()throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;
  SystemClock.now+=100;e.player.position+=100;
  TestEngine.p.current=TestEngine.source("1",1100,true);TestEngine.p.handler.drain();
  check(e.audioOwner.state()==AudioOwnership.State.REPLACEMENT
      &&e.effect.gain==-100f&&e.player.volume>0.99f,
      "precondition: verified same-song join already completed");
  return e;
 }
 static void fastScrubNeverPlaysOldYandexAudio()throws Exception{
  ReplacementEngine e=ready();MediaPlayer p=e.player;DynamicsProcessing fx=e.effect;
  p.asyncSeek=true;int initialSeeks=p.seekCalls;
  e.sourceSeekRequested();TestEngine.p.current=TestEngine.source("1",60000,true);e.update(TestEngine.p.current);
  check(e.seeking&&p.seekCalls==initialSeeks+1&&!p.playing&&p.volume==0f
      &&fx.gain==-100f&&e.originalMix==0f,
      "RED 0.3.63: fast scrubbing must not audibly restore the old Yandex source position");
  SystemClock.now+=65;TestEngine.p.current=TestEngine.source("1",60065,true);
  p.seek.onSeekComplete(p);
  check(!e.seeking&&p.playing&&e.effect==fx&&fx.gain==-100f,
      "new-position decoder startup must retain sole muted source owner");
  SystemClock.now+=140;p.position+=140;TestEngine.p.current=TestEngine.source("1",60205,true);
  TestEngine.p.handler.drain();
  check(e.audioOwner.state()==AudioOwnership.State.REPLACEMENT
      &&p.volume>0.99f&&fx.gain==-100f&&e.effect==fx
      &&p.seekCalls==initialSeeks+1&&!p.released,
      "fast scrub returns to replacement without original/replacement reattachment");
  SystemClock.now+=300;TestEngine.p.handler.drain();
  check(fx.gain==-100f&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
      "expired fallback timer cannot unmute Yandex after successful handover");
  e.close();
 }
 static void slowScrubRestoresOriginalAndKeepsDecoder()throws Exception{
  ReplacementEngine e=ready();MediaPlayer p=e.player;DynamicsProcessing fx=e.effect;
  p.asyncSeek=true;e.sourceSeekRequested();TestEngine.p.current=TestEngine.source("1",60000,true);e.update(TestEngine.p.current);
  SystemClock.now+=ReplacementEngine.RETAINED_SEEK_JOIN_MS+20;
  TestEngine.p.current=TestEngine.source("1",60000+ReplacementEngine.RETAINED_SEEK_JOIN_MS+20,true);
  TestEngine.p.handler.drain();
  check(e.effect==fx&&!fx.released&&fx.gain==0f&&p.volume==0f&&!p.playing&&e.seeking,
      "long decoder seek restores audible Yandex through retained effect at bounded deadline");
  p.seek.onSeekComplete(p);
  check(!e.seeking&&p.playing&&e.effect==fx,
      "slow seek completion retains prepared decoder instead of starting fresh download");
  SystemClock.now+=150;p.position+=150;TestEngine.p.current=TestEngine.source("1",60350,true);
  TestEngine.p.handler.drain();
  check(fx.gain==-100f&&p.volume>0.99f,
      "after a slow seek fallback, only verified decoder can take ownership again");
  e.close();
 }
 static void supersededScrubNeverLeaksStaleAudio()throws Exception{
  ReplacementEngine e=ready();MediaPlayer p=e.player;p.asyncSeek=true;
  e.sourceSeekRequested();TestEngine.p.current=TestEngine.source("1",35000,true);e.update(TestEngine.p.current);
  e.sourceSeekRequested();TestEngine.p.current=TestEngine.source("1",70000,true);e.update(TestEngine.p.current);
  check(p.seekCalls==2&&!p.playing&&p.volume==0f&&e.effect.gain==-100f,
      "second drag must serialize an in-flight seek without surfacing old source audio");
  p.seek.onSeekComplete(p);
  check(p.seekCalls==3&&!p.playing&&e.effect.gain==-100f,
      "old completion cannot grant sound and only latest target is sought");
  p.seek.onSeekComplete(p);
  SystemClock.now+=130;p.position+=130;
  TestEngine.p.current=TestEngine.source("1",70130,true);TestEngine.p.handler.drain();
  check(e.player==p&&!p.released&&p.volume>0.99f&&e.effect.gain==-100f,
      "latest seek, same decoder and exclusive CELIKOM output survive cancellation");
  e.close();
 }
 static void stalledYandexBufferingCannotLeaveSourceSilenced()throws Exception{
  ReplacementEngine e=ready();MediaPlayer p=e.player;p.asyncSeek=true;
  e.sourceSeekRequested();TestEngine.p.current=TestEngine.source("1",79000,true);e.update(TestEngine.p.current);
  SystemClock.now+=40;TestEngine.p.current=TestEngine.buffering(79000);e.update(TestEngine.p.current);
  check(e.seeking&&e.effect!=null&&e.effect.gain==-100f,
      "transient Yandex BUFFERING during decoder seek cannot force a second audio owner");
  p.seek.onSeekComplete(p);
  check(!e.seeking&&e.pausedAt>=0&&!p.playing,
      "after native completion a still-buffering Yandex player stays safely held");
  SystemClock.now+=ReplacementEngine.RETAINED_SEEK_JOIN_MS;
  TestEngine.p.handler.drain();
  check(e.effect==null&&e.originalMix==1f&&!p.playing&&e.player==p,
      "stalled Yandex buffering must restore native gain and retain decoder by bounded fallback");
  TestEngine.p.current=TestEngine.source("1",79250,true);e.update(TestEngine.p.current);
  check(p.playing&&e.effect!=null&&e.player==p,
      "Yandex buffering recovery reuses decoder without new download");
  e.close();
 }
 static void trackBoundaryCancelsScrubTimer()throws Exception{
  ReplacementEngine e=ready();MediaPlayer p=e.player;p.asyncSeek=true;
  e.sourceSeekRequested();TestEngine.p.current=TestEngine.source("1",60000,true);e.update(TestEngine.p.current);
  e.sourceBoundary("new_track_while_scrubbing");
  SystemClock.now+=ReplacementEngine.RETAINED_SEEK_JOIN_MS+100;
  TestEngine.p.handler.drain();
  check(p.released&&e.player==null&&e.effect==null&&!e.seekHoldActive,
      "next track cancels delayed original-gain restoration and decoder ownership");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  fastScrubNeverPlaysOldYandexAudio();
  slowScrubRestoresOriginalAndKeepsDecoder();
  supersededScrubNeverLeaksStaleAudio();
  stalledYandexBufferingCannotLeaveSourceSilenced();
  trackBoundaryCancelsScrubTimer();
  System.out.println("PASS: "+checks+" HONOR 0.3.63 real-engine scrub owner and bounded slow-seek gates");
 }
}
