package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
import android.media.MediaPlayer;
import org.json.*;
/** Virtual elapsed time exercises the real engine, not physical Android scheduling. */
public class TestLongRun {
 static int checks;static void check(boolean value,String reason){checks++;if(!value)throw new AssertionError(reason);}
 public static void main(String[] args)throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;long enabled=e.armedUntil;
  for(int song=1;song<=300;song++){
   SystemClock.now+=180000;
   TestEngine.p.current=TestEngine.source(String.valueOf(song+1),1000,true);
   e.identity(LogStore.map("mediaAlias",String.valueOf(song+1),"albumId","42","title","Песня","artist","Артист","durationMs",120000L),LogStore.map("candidateTrackId",String.valueOf(song+7),"method","ALBUM"));
   MediaPlayer player=TestEngine.prepare();
   check(e.armed()&&e.armedUntil==enabled&&player.playing,"automatic activation survives song "+song);
   check(e.recentAudio.size()<=3,"private audio cache remains bounded at song "+song);
  }
  check(SystemClock.now>12*3600000L,"simulation crosses twelve hours of elapsed time");
  e.stop("user_stop");check(!e.armed()&&e.player==null&&e.effect==null&&e.recentAudio.isEmpty(),"explicit Stop still releases everything after long playback");
  e.arm();check(e.armed(),"owner can explicitly restart after Stop");e.close();check(!e.armed()&&e.player==null,"service shutdown always cancels activation");
  System.out.println("PASS: "+checks+" actual-engine long-run checks, 300 song changes and 15 virtual hours; physical scheduling unverified");
 }
}
