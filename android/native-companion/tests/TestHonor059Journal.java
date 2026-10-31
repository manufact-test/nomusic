package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;

/* Sanitized deterministic replays from HONOR 0.3.59; no user diagnostics embedded. */
public final class TestHonor059Journal {
 static int checks;
 static final java.util.List<String> violations=new java.util.ArrayList<>();
 static void quality(boolean condition,String reason){
  checks++;
  if(!condition)violations.add(reason);
 }
 static void check(boolean condition,String reason){
  checks++;
  if(!condition)throw new AssertionError(reason);
 }
 static void sample(long position,boolean playing){
  TestEngine.p.current=TestEngine.source("1",position,playing);
  TestEngine.e.update(TestEngine.p.current);
 }
 static MediaPlayer exclusivelyAudibleReplacement()throws Exception{
  TestEngine.playing();
  ReplacementEngine e=TestEngine.e;
  MediaPlayer p=e.player;
  SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS+50;
  TestEngine.p.current=TestEngine.source("1",1400,true);
  TestEngine.p.handler.drain();
  check(p.volume>0.99f&&e.originalMix==0f&&e.effect!=null,
    "setup must start with verified exclusive replacement output");
  p.position=1400;
  return p;
 }

 /* Actual 0.3.59 USER PAUSE 937ms, live resume position +126ms:
    accepted behavior is to resume the retained decoder without a new seek.
    The old characterization expected the regression and must never return. */
 static void pauseResume126ms()throws Exception{
  MediaPlayer p=exclusivelyAudibleReplacement();
  ReplacementEngine e=TestEngine.e;
  DynamicsProcessing effect=e.effect;
  int before=p.seekCalls,downloads=TestEngine.api.downloads;
  sample(1400,false);
  check(e.pausedAt>=0&&!p.playing&&p.volume==0f
    &&e.audioOwner.pauseMode()==AudioOwnership.PauseMode.USER,
    "real user pause must hold the same prepared decoder");
  SystemClock.now+=937;
  sample(1526,true);
  check(e.player==p&&e.effect==effect&&!effect.released
    &&TestEngine.api.downloads==downloads,
    "resume must not create a decoder, effect or download");
  check(!e.seeking&&p.seekCalls==before&&p.playing
    &&e.originalMix==0f&&effect.gain==-100f&&p.volume>0.99f,
    "0.3.59 +126ms retained resume must not seek or hand over twice");
  e.close();
 }

 /* The single complementary entry may overlap only after validated decoder
    advancement. Commanded gains remain complementary; physical phase is
    not measured by this test. */
 static void fadeEnergyFloor()throws Exception{
  TestStreamingEngine.Buffer audio=TestStreamingEngine.start();
  ReplacementEngine e=TestEngine.e;
  MediaPlayer p=e.player;
  DynamicsProcessing effect=e.effect;
  check(audio!=null&&effect!=null&&p.volume==0f&&effect.gain==0f,
    "original must stay at full gain during streaming clock validation");
  for(int i=1;i<=3;i++){
   SystemClock.now+=25;
   TestEngine.p.current=TestEngine.source("1",1000+i*25,true);
   e.update(TestEngine.p.current);
   TestEngine.p.handler.drain();
   double originalLinear=Math.pow(10.0,effect.gain/20.0);
   quality(Math.max(originalLinear,p.volume)>=0.99,
     "unverified decoder must keep the original at full gain");
   check(p.volume==0f&&effect.gain==0f,
     "unverified streaming decoder cannot attenuate the live original");
  }
  p.position=1100;
  SystemClock.now+=25;
  TestEngine.p.current=TestEngine.source("1",1100,true);
  e.update(TestEngine.p.current);
  TestEngine.p.handler.drain();
  double originalLinear=Math.pow(10.0,effect.gain/20.0);
  quality(Math.max(originalLinear,p.volume)>=0.99,
    "clock gate must precede any intentional source dip");
  check(e.fading&&e.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND
      &&effect.gain==0f&&p.volume==0f,
    "verified decoder starts the one bounded join with source full");
  SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS/4;
  p.position+=ReplacementEngine.UNIFIED_JOIN_MS/4;
  sample(1100+ReplacementEngine.UNIFIED_JOIN_MS/4,true);TestEngine.p.handler.drain();
  originalLinear=Math.pow(10.0,effect.gain/20.0);
  quality(e.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND
      &&originalLinear>0.6&&originalLinear<0.9f&&p.volume>0.1f
      &&Math.abs(originalLinear+p.volume-1f)<0.02f,
    "first quarter keeps complementary commanded gains under an owner ticket");
  SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS/4;
  p.position+=ReplacementEngine.UNIFIED_JOIN_MS/4;
  sample(1100+ReplacementEngine.UNIFIED_JOIN_MS/2,true);TestEngine.p.handler.drain();
  check(p.volume>0.49f&&p.volume<0.51f&&e.originalMix>0.49f&&e.originalMix<0.51f,
    "unified midpoint never intentionally commands both channels to zero");
  SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS/4;
  p.position+=ReplacementEngine.UNIFIED_JOIN_MS/4;
  sample(1100+ReplacementEngine.UNIFIED_JOIN_MS*3/4,true);TestEngine.p.handler.drain();
  quality(p.volume>0.6f&&p.volume<0.9f&&e.originalMix>0.1f&&e.originalMix<0.4f,
    "third quarter uses complementary gains, not equal-power crossfade");
  SystemClock.now+=ReplacementEngine.UNIFIED_JOIN_MS/4+20;p.position+=ReplacementEngine.UNIFIED_JOIN_MS/4+20;
  sample(1100+ReplacementEngine.UNIFIED_JOIN_MS+20,true);TestEngine.p.handler.drain();
  check(effect.gain==-100f&&p.volume>0.99f&&!e.fading
      &&AudioOwnership.exclusive(e.originalMix,p.volume),
    "bounded unified entry ends in exclusive full-volume replacement");
  e.close();
 }

 /* Regression: 0.3.65 discovered that any muted-source seek hold can create
    an observable command gap. Source gain now returns during the seek itself. */
 static void restoredSourceMustCloseGap()throws Exception{
  MediaPlayer p=exclusivelyAudibleReplacement();
  ReplacementEngine e=TestEngine.e;
  DynamicsProcessing effect=e.effect;
  p.asyncSeek=true;
  sample(60000,true);
  check(e.seeking&&!p.playing&&p.volume==0f&&e.originalMix==1f&&effect.gain==0f,
    "cached scrub immediately retains audible native source ownership");
  SystemClock.now+=ReplacementEngine.RETAINED_SEEK_JOIN_MS+1;
  TestEngine.p.handler.drain();
  check(e.seeking&&!p.playing&&p.volume==0f
    &&e.originalMix==1f&&effect.gain==0f,
    "slow seek remains on original with same effect; no timed command-gap workaround");
  SystemClock.now+=551;
  AudioContinuityMonitor.Finding phantom=e.continuity.observe(
    SystemClock.now,"7","seek",true,false,false,0f);
  quality(phantom==null,
    "RED 0.3.59: restored original was omitted from continuity sampling; a phantom 551ms commanded-silence event is emitted");
  e.close();
 }

 public static void main(String[] args)throws Exception{
  pauseResume126ms();
  fadeEnergyFloor();
  restoredSourceMustCloseGap();
  if(!violations.isEmpty())throw new AssertionError(String.join(" | ",violations));
  System.out.println("PASS: "+checks+" HONOR 0.3.59 pause/seek diagnostic replay checks");
 }
}
