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
  SystemClock.now+=ReplacementEngine.FADE_MS+50;
  TestEngine.p.current=TestEngine.source("1",1400,true);
  TestEngine.p.handler.drain();
  check(p.volume>0.99f&&e.originalMix==0f&&e.effect!=null,
    "setup must start with verified exclusive replacement output");
  p.position=1400;
  return p;
 }

 /* Actual 0.3.59 USER PAUSE 937ms, live resume position +126ms:
    retain the decoder and effect, but expose the re-seek and clock wait.
    This is a characterization replay, not acceptance of audible latency. */
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
  p.asyncSeek=true;
  sample(1526,true);
  check(e.player==p&&e.effect==effect&&!effect.released
    &&TestEngine.api.downloads==downloads,
    "resume must not create a decoder, effect or download");
  check(e.seeking&&p.seekCalls==before+1&&!p.playing
    &&e.originalMix==1f&&effect.gain==0f,
    "0.3.59 +126ms resume takes re-alignment with original restored");
  SystemClock.now+=18;
  sample(1544,true);
  p.seek.onSeekComplete(p);
  check(!e.seeking&&!e.fading&&p.playing&&p.volume>0.99f
    &&effect.gain==-100f,
    "after verified seek the existing decoder takes output in one owner turn");
  e.close();
 }

 /* The old 100ms fade to -100dB left both outputs inaudible.
    After repair a source is audible at every command checkpoint, and a
    prepared streaming decoder acquires output only after its clock advances. */
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
   quality(Math.max(originalLinear,p.volume)>=0.1,
     "RED 0.3.59: handover must not drive both command outputs below -20dB");
   check(p.volume==0f&&effect.gain==0f,
     "unverified streaming decoder cannot attenuate the live original");
  }
  p.position=1100;
  SystemClock.now+=25;
  TestEngine.p.current=TestEngine.source("1",1100,true);
  e.update(TestEngine.p.current);
  TestEngine.p.handler.drain();
  double originalLinear=Math.pow(10.0,effect.gain/20.0);
  quality(Math.max(originalLinear,p.volume)>=0.1,
    "RED 0.3.59: output must be granted without a scheduled near-silent phase");
  check(effect.gain==-100f&&p.volume>0.99f&&!e.fading,
    "validated streaming decoder receives full exclusive output in same owner turn");
  check(AudioOwnership.exclusive((float)originalLinear,p.volume),
    "neither pre-commit nor post-commit commands permit dual audible sessions");
  e.close();
 }

 /* Regression: on a long streaming seek, the native original is restored
    immediately. The monitor must close its old command gap at THAT command,
    not 551ms later when another secondary-volume call happens. */
 static void restoredSourceMustCloseGap()throws Exception{
  MediaPlayer p=exclusivelyAudibleReplacement();
  ReplacementEngine e=TestEngine.e;
  DynamicsProcessing effect=e.effect;
  p.asyncSeek=true;
  sample(60000,true);
  check(e.seeking&&!p.playing&&p.volume==0f
    &&e.originalMix==1f&&effect.gain==0f,
    "seek restores original source output with the same verified effect");
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
