package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
import android.media.MediaPlayer;
import java.util.*;
public class TestHandoverClock {
 static int checks;
 static void check(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
 static void sample(long pos){TestEngine.p.current=TestEngine.source("1",pos,true);}
 static void recordedOffset(int drift)throws Exception{
  TestStreamingEngine.Buffer audio=TestStreamingEngine.start();ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;long source=1040L+drift;
  SystemClock.now+=40+drift;p.position+=40;sample(source);TestEngine.p.handler.drain();
  check(e.player==p&&!p.released&&p.seekCalls==(drift<=350?1:2),"recorded offset "+drift+"ms must not create unnecessary warm seeks");
  if(drift>350){SystemClock.now+=40;p.position+=40;source+=40;sample(source);TestEngine.p.handler.drain();}
  SystemClock.now+=ReplacementEngine.COLD_JOIN_DIP_MS/4;
  p.position+=ReplacementEngine.COLD_JOIN_DIP_MS/4;source+=ReplacementEngine.COLD_JOIN_DIP_MS/4;
  sample(source);TestEngine.p.handler.drain();
  double originalGain=Math.pow(10,e.effect.gain/20.0);
  check(e.audioOwner.state()==AudioOwnership.State.ALIGNING
      &&originalGain>0.1&&originalGain<1.0&&p.volume==0f,
      "recorded alignment ducks only the original after verified clock "+drift);
  SystemClock.now+=ReplacementEngine.COLD_JOIN_DIP_MS*3/4+40;
  p.position+=ReplacementEngine.COLD_JOIN_DIP_MS*3/4+40;
  source+=ReplacementEngine.COLD_JOIN_DIP_MS*3/4+40;
  sample(source);TestEngine.p.handler.drain();
  check(p.volume>0.99f&&e.effect.gain==-100f,
      "exclusive 500ms dip completes at replacement gain "+drift);
  SystemClock.now+=200;p.position+=200;source+=200;sample(source);TestEngine.p.handler.drain();int seeks=p.seekCalls;
  for(int i=0;i<8;i++){SystemClock.now+=250;p.position+=250;source+=250;sample(source);e.update(TestEngine.p.current);TestEngine.p.handler.drain();}
  check(e.player==p&&!p.released&&p.seekCalls==seeks&&TestEngine.api.resolves==1&&TestEngine.api.downloads==0,"recorded profile stays on same stream without repeated resolve/recovery "+drift);e.close();
 }
 static void coldJoinSoftEdgesAndCancellation()throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  check(e.fading&&p.volume==0f&&e.effect.gain==0f,
    "cold join starts with original still audible and silent replacement");
  SystemClock.now+=ReplacementEngine.COLD_JOIN_DIP_MS/4;
  sample(1000+ReplacementEngine.COLD_JOIN_DIP_MS/4);TestEngine.p.handler.drain();
  double originalGain=Math.pow(10,e.effect.gain/20.0);
  check(p.volume==0f&&e.effect.gain<0f&&e.effect.gain>-100f
      &&e.audioOwner.state()==AudioOwnership.State.ALIGNING
      &&originalGain>0.1&&originalGain<1f,
    "first quarter ducks source with replacement silent: no waveform clash");
  SystemClock.now+=ReplacementEngine.COLD_JOIN_DIP_MS/4;
  sample(1000+ReplacementEngine.COLD_JOIN_DIP_MS/2);TestEngine.p.handler.drain();
  check(p.volume==0f&&e.effect.gain==-100f&&e.fading,
    "midpoint has bounded intentional zero-overlap valley");
  SystemClock.now+=ReplacementEngine.COLD_JOIN_DIP_MS/4;
  sample(1000+ReplacementEngine.COLD_JOIN_DIP_MS*3/4);TestEngine.p.handler.drain();
  check(p.volume>0f&&p.volume<1f&&e.effect.gain==-100f&&e.fading,
    "third quarter raises only replacement, source fully attenuated");
  SystemClock.now+=ReplacementEngine.COLD_JOIN_DIP_MS/4+20;
  sample(1000+ReplacementEngine.COLD_JOIN_DIP_MS+20);
  TestEngine.p.handler.drain();
  check(p.volume==1f&&e.effect.gain==-100f&&!e.fading,
    "cold join finishes in exclusive decoder state");e.close();
  TestEngine.playing();e=TestEngine.e;p=e.player;
  SystemClock.now+=ReplacementEngine.COLD_JOIN_DIP_MS/4;
  sample(1000+ReplacementEngine.COLD_JOIN_DIP_MS/4);TestEngine.p.handler.drain();
  TestEngine.p.current=TestEngine.source("1",1080,false);e.update(TestEngine.p.current);
  check(!e.fading&&p.volume==0f&&e.effect!=null&&e.effect.gain==0f,
    "pause cancels partial dip and restores native gain");
  e.close();
  TestEngine.playing();e=TestEngine.e;p=e.player;
  SystemClock.now+=ReplacementEngine.COLD_JOIN_DIP_MS/4;
  sample(1000+ReplacementEngine.COLD_JOIN_DIP_MS/4);TestEngine.p.handler.drain();
  e.sourceBoundary("new_song_during_soft_join");SystemClock.now+=500;TestEngine.p.handler.drain();
  check(p.released&&p.volume==0f&&e.player==null&&e.effect==null,
    "new song cancels soft join without stale decoder or effect");e.close();
 }
 static void nearTerminalBlendTickMustNotTriggerRecovery()throws Exception{
  // Retain a direct regression for the legacy blending primitive even though
  // production now uses non-overlapping output for every cold handover.
  TestEngine.playing();ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;
  e.transition++;e.fading=false;e.audioOwner.handoverClockValidated();
  e.audioOwner.aligning();
  e.audioOwner.blendSameSong(p,e.effect,0.9999f,1f,e.identityKey,
      e.audioOwner.epoch(),e.audioOwner.operationEpoch());
  check(e.audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND,
    "HONOR 0.3.62: near-terminal legacy blend cannot prematurely revoke owner");
  e.audioOwner.blendSameSong(p,e.effect,1f,1f,e.identityKey,
      e.audioOwner.epoch(),e.audioOwner.operationEpoch());
  check(e.audioOwner.state()==AudioOwnership.State.REPLACEMENT,
    "HONOR 0.3.62: exact final blend tick still completes without recovery");
  e.close();
 }
 public static void main(String[] args)throws Exception{
  nearTerminalBlendTickMustNotTriggerRecovery();
  coldJoinSoftEdgesAndCancellation();
  for(int drift:new int[]{210,198,170,207,197,190,378,230,187})recordedOffset(drift);
  List<Map<String,Object>> rows=new ArrayList<>();rows.add(LogStore.map("catalogueTrackId","89285816","displayTitle","Он рядом","artist","Quest Pistols","durationMs",224520L));
  check("89285816".equals(AlbumMatch.match("Он рядом","Quest Pistols Show, Quest Pistols",224520,rows).get("catalogueTrackId")),"recorded duplicated artist display finds exact album track");
  check("NO_MATCH".equals(AlbumMatch.match("Он рядом","Quest Pistols, Another Artist",224520,rows).get("status")),"an unrecognised extra collaborator is not discarded");
  check("NO_MATCH".equals(AlbumMatch.match("Он рядом (Live)","Quest Pistols Show, Quest Pistols",224520,rows).get("status")),"edition title remains strict");
  check("NO_MATCH".equals(AlbumMatch.match("Он рядом","Quest Pistols Show, Quest Pistols",230000,rows).get("status")),"duration remains strict");
  rows.add(new LinkedHashMap<>(rows.get(0)));rows.get(1).put("catalogueTrackId","999");
  check("AMBIGUOUS".equals(AlbumMatch.match("Он рядом","Quest Pistols Show, Quest Pistols",224520,rows).get("status")),"two album candidates cannot pick an arbitrary edition");
  TestStreamingEngine.Buffer audio=TestStreamingEngine.start();ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;p.asyncSeek=true;
  SystemClock.now+=640;p.position+=40;sample(1640);TestEngine.p.handler.drain();
  check(p.volume==0f&&e.originalMix==1f,"decoder advancing 600ms late must not begin audible crossfade");
  check(p.playing&&p.seekCalls==2,"warm decoder aligns while running silently, avoiding another pause/start");
  SystemClock.now+=20;sample(1660);p.seek.onSeekComplete(p);
  SystemClock.now+=40;p.position+=40;sample(1700);TestEngine.p.handler.drain();
  check((p.volume==0f&&e.originalMix>0f)
     ||(e.audioOwner.state()==AudioOwnership.State.REPLACEMENT&&e.originalMix==0f),
     "aligned handover never commands two audible versions");
  SystemClock.now+=ReplacementEngine.COLD_JOIN_DIP_MS+40;
  p.position+=ReplacementEngine.COLD_JOIN_DIP_MS+40;
  sample(1700+ReplacementEngine.COLD_JOIN_DIP_MS+40);
  TestEngine.p.handler.drain();
  check(p.volume>0.99f&&e.originalMix==0f&&e.effect.gain==-100f,
      "aligned replacement has full output after the verified blend");
  int seeks=p.seekCalls;SystemClock.now+=200;p.position+=200;sample(2080);TestEngine.p.handler.drain();e.update(TestEngine.p.current);
  check(p.volume==1f&&e.originalMix==0f&&p.seekCalls==seeks,"completed aligned fade has no follow-up audible seek");e.close();
  audio=TestStreamingEngine.start();e=TestEngine.e;p=e.player;p.asyncSeek=true;SystemClock.now+=640;p.position+=40;sample(1640);TestEngine.p.handler.drain();
  e.sourceBoundary("next_during_warm_seek");p.seek=null;SystemClock.now+=1000;TestEngine.p.handler.drain();
  check(p.released&&e.player==null&&e.effect==null,"next song cancels pending warm alignment and fade");e.close();
  audio=TestStreamingEngine.start();e=TestEngine.e;p=e.player;p.asyncSeek=true;SystemClock.now+=640;p.position+=40;sample(1640);TestEngine.p.handler.drain();
  SystemClock.now+=600;sample(2240);p.seek.onSeekComplete(p);SystemClock.now+=40;p.position+=40;sample(2280);TestEngine.p.handler.drain();
  SystemClock.now+=600;sample(2880);p.seek.onSeekComplete(p);SystemClock.now+=40;p.position+=40;sample(2920);TestEngine.p.handler.drain();
  check(p.released&&p.volume==0f&&e.effect==null&&e.armed(),"repeated startup lag stays inaudible and terminates after bounded alignment attempts");e.close();
  audio=TestStreamingEngine.start();e=TestEngine.e;p=e.player;p.asyncSeek=true;SystemClock.now+=640;p.position+=40;sample(1640);TestEngine.p.handler.drain();MediaPlayer.OnSeekCompleteListener pending=p.seek;
  TestEngine.p.current=TestEngine.source("1",1640,false);e.update(TestEngine.p.current);pending.onSeekComplete(p);SystemClock.now+=400;TestEngine.p.current=TestEngine.source("1",1640,false);TestEngine.p.handler.drain();
  check(!p.playing&&p.volume==0f&&e.effect==null,"pause during warm seek cannot revive replacement or leave original muted");e.close();
  System.out.println("PASS: "+checks+" recorded artist-display and live-clock handover checks");
 }
}
