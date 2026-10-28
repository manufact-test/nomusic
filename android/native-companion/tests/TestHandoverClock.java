package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
import android.media.MediaPlayer;
import java.util.*;
public class TestHandoverClock {
 static int checks;
 static void check(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
 static void sample(long pos){TestEngine.p.current=TestEngine.source("1",pos,true);}
 public static void main(String[] args)throws Exception{
  List<Map<String,Object>> rows=new ArrayList<>();rows.add(LogStore.map("catalogueTrackId","89285816","displayTitle","Он рядом","artist","Quest Pistols","durationMs",224520L));
  check("89285816".equals(AlbumMatch.match("Он рядом","Quest Pistols Show, Quest Pistols",224520,rows).get("catalogueTrackId")),"recorded duplicated artist display finds exact album track");
  check("NO_MATCH".equals(AlbumMatch.match("Он рядом","Quest Pistols, Another Artist",224520,rows).get("status")),"an unrecognised extra collaborator is not discarded");
  check("NO_MATCH".equals(AlbumMatch.match("Он рядом (Live)","Quest Pistols Show, Quest Pistols",224520,rows).get("status")),"edition title remains strict");
  check("NO_MATCH".equals(AlbumMatch.match("Он рядом","Quest Pistols Show, Quest Pistols",230000,rows).get("status")),"duration remains strict");
  rows.add(new LinkedHashMap<>(rows.get(0)));rows.get(1).put("catalogueTrackId","999");
  check("AMBIGUOUS".equals(AlbumMatch.match("Он рядом","Quest Pistols Show, Quest Pistols",224520,rows).get("status")),"two album candidates cannot pick an arbitrary edition");
  TestStreamingEngine.Buffer audio=TestStreamingEngine.start();ReplacementEngine e=TestEngine.e;MediaPlayer p=e.player;p.asyncSeek=true;
  SystemClock.now+=240;p.position+=40;sample(1240);TestEngine.p.handler.drain();
  check(p.volume==0f&&e.originalMix==1f,"decoder advancing 200ms late must not begin audible crossfade");
  check(p.playing&&p.seekCalls==2,"warm decoder aligns while running silently, avoiding another pause/start");
  SystemClock.now+=20;sample(1260);p.seek.onSeekComplete(p);
  SystemClock.now+=40;p.position+=40;sample(1300);TestEngine.p.handler.drain();
  check(p.volume==0f&&e.originalMix==1f,"aligned handover starts at zero replacement gain");
  SystemClock.now+=180;p.position+=180;sample(1480);TestEngine.p.handler.drain();
  check(p.volume>0.45f&&p.volume<0.55f&&e.originalMix>0.45f,"aligned midpoint uses complementary gradual gains");
  int seeks=p.seekCalls;SystemClock.now+=200;p.position+=200;sample(1680);TestEngine.p.handler.drain();e.update(TestEngine.p.current);
  check(p.volume==1f&&e.originalMix==0f&&p.seekCalls==seeks,"completed aligned fade has no follow-up audible seek");e.close();
  audio=TestStreamingEngine.start();e=TestEngine.e;p=e.player;p.asyncSeek=true;SystemClock.now+=240;p.position+=40;sample(1240);TestEngine.p.handler.drain();
  e.sourceBoundary("next_during_warm_seek");p.seek=null;SystemClock.now+=1000;TestEngine.p.handler.drain();
  check(p.released&&e.player==null&&e.effect==null,"next song cancels pending warm alignment and fade");e.close();
  audio=TestStreamingEngine.start();e=TestEngine.e;p=e.player;p.asyncSeek=true;SystemClock.now+=240;p.position+=40;sample(1240);TestEngine.p.handler.drain();
  SystemClock.now+=200;sample(1440);p.seek.onSeekComplete(p);SystemClock.now+=40;p.position+=40;sample(1480);TestEngine.p.handler.drain();
  SystemClock.now+=200;sample(1680);p.seek.onSeekComplete(p);SystemClock.now+=40;p.position+=40;sample(1720);TestEngine.p.handler.drain();
  check(p.released&&p.volume==0f&&e.effect==null&&e.armed(),"repeated startup lag stays inaudible and terminates after bounded alignment attempts");e.close();
  audio=TestStreamingEngine.start();e=TestEngine.e;p=e.player;p.asyncSeek=true;SystemClock.now+=240;p.position+=40;sample(1240);TestEngine.p.handler.drain();MediaPlayer.OnSeekCompleteListener pending=p.seek;
  TestEngine.p.current=TestEngine.source("1",1240,false);e.update(TestEngine.p.current);pending.onSeekComplete(p);SystemClock.now+=400;TestEngine.p.current=TestEngine.source("1",1240,false);TestEngine.p.handler.drain();
  check(!p.playing&&p.volume==0f&&e.effect==null,"pause during warm seek cannot revive replacement or leave original muted");e.close();
  System.out.println("PASS: "+checks+" recorded artist-display and live-clock handover checks");
 }
}
