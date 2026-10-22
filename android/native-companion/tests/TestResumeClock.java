package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
import android.media.MediaPlayer;

/** Real engine, delayed Android seek callback, and continuously advancing clocks. */
public class TestResumeClock {
 static int checks;
 static void check(boolean value,String reason){checks++;if(!value)throw new AssertionError(reason);}
 static void sample(long position,boolean playing){TestEngine.p.current=TestEngine.source("1",position,playing);TestEngine.e.update(TestEngine.p.current);}
 public static void main(String[] args)throws Exception {
  TestEngine.playing();ReplacementEngine e=TestEngine.e;MediaPlayer player=e.player;
  SystemClock.now+=ReplacementEngine.FADE_MS+20;sample(1160,true);TestEngine.p.handler.drain();
  int downloads=TestEngine.api.downloads,resolves=TestEngine.api.resolves;
  e.headphonesDisconnected();sample(1160,false);SystemClock.now+=400;
  player.asyncSeek=true;sample(60000,true);int primary=player.seekCalls;
  SystemClock.now+=551;sample(60551,true);player.seek.onSeekComplete(player);
  check(!player.playing,"551ms alignment error must be corrected before the replacement becomes audible");
  check(player.seekCalls==primary+1,"one bounded inaudible correction is submitted");
  SystemClock.now+=551;sample(61102,true);player.seek.onSeekComplete(player);
  check(player.playing&&!e.seeking,"corrected source and replacement resume together");
  int seeks=player.seekCalls;
  for(int i=1;i<=20;i++){
   SystemClock.now+=250;player.position+=250;sample(61102+i*250,true);TestEngine.p.handler.drain();
   check(player.playing&&player.seekCalls==seeks,"no audible post-resume reseek at tick "+i);
  }
  check(TestEngine.api.downloads==downloads&&TestEngine.api.resolves==resolves,"resume reuses the same prepared audio and authorization");
  e.close();

  TestEngine.playing();e=TestEngine.e;player=e.player;
  SystemClock.now+=ReplacementEngine.FADE_MS+20;sample(1160,true);TestEngine.p.handler.drain();
  int beforeRoute=player.seekCalls;player.position=1160;e.headphonesDisconnected();sample(1160,false);
  SystemClock.now+=1000;sample(1160,true);
  check(player.playing&&player.seekCalls==beforeRoute,"unchanged route-resume position reuses decoder without any seek");
  sample(1160,false);SystemClock.now+=400;sample(1160,false);TestEngine.p.handler.drain();sample(1160,true);
  check(player.playing&&player.seekCalls==beforeRoute,"ordinary pause-resume also avoids an unnecessary decoder seek");
  e.close();

  TestEngine.playing();e=TestEngine.e;player=e.player;
  // The native song has not ended. The last 100ms are still valid audio.
  SystemClock.now+=ReplacementEngine.FADE_MS+20;sample(119900,true);player.position=119900;
  // Complete a synchronous source seek at the tail, then continue normal play.
  e.update(TestEngine.p.current);
  check(e.player==player&&!player.released,"do not discard the last 150ms before the file or source ends");
  check(player.playing,"replacement tail keeps playing until completion or source track change");
  e.close();
  System.out.println("PASS: "+checks+" resume-clock and natural-tail checks");
 }
}
