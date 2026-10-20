package pro.celikom.nativeprobe.identitydiag;
import java.nio.file.*;import java.util.*;import java.io.*;import org.json.*;import android.os.SystemClock;import android.media.MediaPlayer;import pro.celikom.nativeprobe.AttenuationService;
/** Replay only exported player state/seek timing; no real Android hardware or network. */
public class TestPhoneReplay {
 static ProbeService p;static ReplacementEngine e;static NativeApi api;static String alias="24";static long duration=180880,pos=62521;static boolean playing=true;static int resolves,downloads,seekCalls;static MediaPlayer prepared,seekPlayer;static long resolveAt,downloadAt,prepareAt,seekAt;static List<File> files=new ArrayList<>();
 static PlaybackSource source(){return new PlaybackSource(alias,alias.equals("24")?"Ау":"Поводы",alias.equals("24")?"10AGE, Ramil'":"WHITE GALLOWS, Real Girl",duration,alias.equals("24")?"https://avatars.yandex.net/get-music-content/1/x.a.38902809-1/700x700":"https://avatars.yandex.net/get-music-content/1/x.a.27161331-1/700x700",pos,playing,true,1f);}
 static void sample(){p.current=source();e.identity(LogStore.map("mediaAlias",alias,"title",p.current.title,"artist",p.current.artist,"albumId",p.current.albumId,"durationMs",duration),LogStore.map("candidateTrackId",alias.equals("24")?"144530503":"116855180","method","ALBUM"));e.update(p.current);}
 static void step(long target)throws Exception{while(SystemClock.now<target){long delta=Math.min(10,target-SystemClock.now);SystemClock.now+=delta;if(playing)pos+=delta;if(e.player!=null&&e.player.playing)e.player.position+=delta;sample();p.handler.drain();
  if(api.resolves>resolves){resolves=api.resolves;resolveAt=SystemClock.now+100;}
  if(resolveAt>0&&SystemClock.now>=resolveAt){resolveAt=0;api.resolved.done(new JSONObject().put("found",alias.equals("24")).put("replacement_id",1).put("version",1).put("duration_ms",180872),null);}
  if(api.downloads>downloads){downloads=api.downloads;downloadAt=SystemClock.now+300;}
  if(downloadAt>0&&SystemClock.now>=downloadAt){downloadAt=0;File f=File.createTempFile("phone-replay", ".audio");files.add(f);api.downloaded.done(f,null);}
  if(e.player!=null&&e.player!=prepared){prepared=e.player;prepared.duration=(int)duration;prepared.asyncSeek=true;prepareAt=SystemClock.now+60;}
  if(prepareAt>0&&SystemClock.now>=prepareAt){prepareAt=0;if(prepared!=null&&!prepared.released)prepared.prepared.onPrepared(prepared);}
  if(e.player!=seekPlayer){seekPlayer=e.player;seekCalls=0;seekAt=0;}
  if(seekPlayer!=null&&seekPlayer.seekCalls>seekCalls){seekCalls=seekPlayer.seekCalls;seekAt=SystemClock.now+20;}
  if(seekAt>0&&SystemClock.now>=seekAt){seekAt=0;if(seekPlayer!=null&&!seekPlayer.released)seekPlayer.seek.onSeekComplete(seekPlayer);}
 }}
 public static void main(String[] args)throws Exception{SystemClock.now=1000;api=new NativeApi();api.signed=true;NativeApi.api=api;p=new ProbeService();e=new ReplacementEngine(p);AttenuationService.Companion.session=45609;sample();e.arm();int states=0;
  try{for(String row:Files.readAllLines(Paths.get(args[0]))){if(row.startsWith("#")||row.isEmpty())continue;String[] a=row.split("\t");step(1000+Long.parseLong(a[0]));alias=a[1];duration=Long.parseLong(a[2]);pos=Long.parseLong(a[3]);playing=Boolean.parseBoolean(a[4]);sample();states++;}
   step(SystemClock.now+500);long recoveries=LogStore.events.stream().filter(x->x.equals("replacement_recovery")).count();if(recoveries!=0||api.downloads!=1||!e.armed()||e.player==null||!e.player.playing)throw new AssertionError("replay: recoveries="+recoveries+" downloads="+api.downloads+" status="+e.status);System.out.println("PASS: phone timeline replay, "+states+" source events; zero destructive recoveries; one download; return to Ау reused after live resolve");
  }finally{e.close();for(File f:files)if(f.exists())throw new AssertionError("audio not deleted after run");}
 }
}
