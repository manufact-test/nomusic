package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;
/** Blocking audio lifecycle replay; add real Android verification before any release. */
public final class TestAudioLifecycle {
 static int count;
 static void ok(boolean condition,String label){count++;if(!condition)throw new AssertionError(label);}
 public static void main(String[] args)throws Exception {
  AudioOwnership a=new AudioOwnership();a.track("105");long epoch=a.epoch();
  a.preparing();ok(a.current(epoch,"105"),"track generation starts preparation");
  MediaPlayer mp=new MediaPlayer();
  boolean rejected=false;try{a.volume(mp,0.5f,null);}catch(IllegalStateException expected){rejected=true;}
  ok(rejected&&mp.volume==0f,"secondary cannot play before source is muted");
  DynamicsProcessing fx=new DynamicsProcessing(0,101,null);a.prepareSourceEffect(fx);
  rejected=false;try{a.grantReplacement(fx);}catch(IllegalStateException expected){rejected=true;}
  ok(rejected,"prepare alone cannot grant audible output");
  a.aligning();a.grantReplacement(fx);a.volume(mp,0.75f,fx);
  ok(mp.volume==0.75f&&fx.gain==-100f&&a.state()==AudioOwnership.State.REPLACEMENT,"exclusive grant");
  a.paused();long lease=a.pauseLease();a.cancelPause();
  ok(!a.validPause(lease),"resume cancels stale pause timer");
  rejected=false;try{a.volume(mp,1f,fx);}catch(IllegalStateException expected){rejected=true;}
  ok(rejected,"old grant cannot raise output while seeking");
  a.grantReplacement(fx);a.volume(mp,1f,fx);mp.start();
  a.silenceReplacement(mp);ok(mp.volume==0f&&!mp.playing,"secondary silenced before source restoration");
  fx.setInputGainAllChannelsTo(0f);a.source();
  a.track("106");ok(!a.current(epoch,"105"),"old alias rejected by generation");
  a.unsupported("duration_mismatch");ok(a.state()==AudioOwnership.State.TRACK_UNSUPPORTED,"mismatch is terminal per track");
  a.track("107");ok(a.state()==AudioOwnership.State.SOURCE_ONLY,"new track unblocks replacement");
  a.recovering("drift_unstable");ok(a.state()==AudioOwnership.State.RECOVERING,"drift recovery is observable");
  MediaPlayer ordered=new MediaPlayer();
  DynamicsProcessing orderedEffect=new DynamicsProcessing(0,101,null){
   @Override public void setInputGainAllChannelsTo(float gain){
    if(gain==0f&&(ordered.volume>0.001f||ordered.playing))
     throw new AssertionError("native gain was restored before secondary was silenced");
    super.setInputGainAllChannelsTo(gain);
   }
  };
  AudioOwnership sequence=new AudioOwnership();sequence.track("ordered");sequence.aligning();
  sequence.prepareSourceEffect(orderedEffect);sequence.aligning();sequence.grantReplacement(orderedEffect);
  sequence.volume(ordered,0.8f,orderedEffect);sequence.startDecoder(ordered,orderedEffect,"ordered",sequence.epoch());
  AudioOwnership.RestoreResult outcome=sequence.restoreSource(ordered,orderedEffect);
  ok(outcome.gainReset&&outcome.disabled&&outcome.released,"source restoration closes audio effect");
  ok(ordered.volume==0f&&!ordered.playing&&orderedEffect.gain==0f,"restoration always mutes secondary first");
  a.stopped();ok(a.state()==AudioOwnership.State.STOPPED,"Stop revokes output");
  a.track("108");ok(a.state()==AudioOwnership.State.STOPPED&&!a.current(a.epoch(),"108"),"new observation cannot rearm Stop");
  a.activate();ok(a.current(a.epoch(),"108")&&a.state()==AudioOwnership.State.SOURCE_ONLY,"user arm explicitly reopens transport");
  TestEngine.playing();ReplacementEngine e=TestEngine.e;MediaPlayer old=e.player;
  long oldEpoch=e.audioOwner.epoch();e.sourceBoundary("confirmed_next_track");
  ok(!e.audioOwner.current(oldEpoch,"1")&&old.released&&old.volume==0f&&e.effect==null,
    "real boundary invalidates old output before restoration");e.close();
  TestEngine.playing();e=TestEngine.e;MediaPlayer shortPlayer=e.player;
  TestEngine.p.current=TestEngine.source("1",35000,true);shortPlayer.completed.onCompletion(shortPlayer);
  ok(shortPlayer.released&&e.effect==null,"early decoder completion restores original");
  ok(e.completedReason!=null&&e.completedReason.contains("раньше"),"early decoder ending has clear track reason");
  e.close();
  TestEngine.playing();e=TestEngine.e;
  String sameKey=e.identityKey;long previousGeneration=e.audioOwner.epoch();
  e.stop("owner_stop");
  ok(e.audioOwner.state()==AudioOwnership.State.STOPPED,"explicit Stop revokes audio");
  e.arm();
  ok(e.audioOwner.current(e.audioOwner.epoch(),sameKey)&&e.audioOwner.epoch()!=previousGeneration,
     "rearming same current song restores identity lease without stale callbacks");
  MediaPlayer restarted=TestEngine.prepare();
  ok(restarted.isPlaying()&&e.effect!=null,"Stop and Start on the same song can play without reselecting a track");
  e.close();
  System.out.println("PASS: "+count+" lifecycle state and real-engine failure gates");
 }
}
