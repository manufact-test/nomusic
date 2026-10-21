package pro.celikom.nativeprobe.identitydiag;
import android.app.PendingIntent;
import android.content.*;
import android.graphics.Bitmap;
import android.graphics.drawable.Icon;
import android.net.Uri;
import android.os.*;
import org.json.*;
import java.io.*;
import java.lang.reflect.Array;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;
public final class LogStore {
 static Context context; static File file; static DiagnosticJournal journal;static DiagnosticArchive archive; static boolean active; static long start; static int events; static String failure="";
 static final LinkedHashMap<String,Integer> counts=new LinkedHashMap<>();
 static final String PKG="ru.yandex.music"; static final int MAX=8*1024*1024;
 static synchronized void init(Context c){context=c.getApplicationContext();file=new File(c.getFilesDir(),"combined-identity-v1.txt");journal=new DiagnosticJournal(file,MAX);archive=new DiagnosticArchive(file);}
 static synchronized void begin(){active=true;events=0;counts.clear();start=SystemClock.elapsedRealtime();try{if(archive!=null)archive.remember(journal);}catch(IOException ignored){}try{journal.reset();failure="";}catch(Exception e){failure="Не удалось начать запись диагностики";active=false;return;}force("run_start",map("version",AppVersion.NAME,"utc",new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX",Locale.ROOT).format(new Date()),"privacy","Local player state; public Yandex album lookup; CELIKOM account/API only after user action. No passwords, tokens, audio or bitmap pixels in the report","durationLimited",false,"journalSegmentBytes",MAX));}
 static synchronized void log(String type,Object data){if(active)force(type,data);}
 static synchronized void force(String type,Object data){if(journal==null)return;try{JSONObject row=new JSONObject();row.put("elapsed_ms",start==0?0:SystemClock.elapsedRealtime()-start);row.put("event",type);row.put("data",json(data,0));journal.append((row.toString()+"\n").getBytes(StandardCharsets.UTF_8));events++;counts.put(type,counts.containsKey(type)?counts.get(type)+1:1);}catch(Throwable e){failure="Запись диагностики недоступна; воспроизведение продолжается";active=false;}}
 static synchronized boolean hasReport(){return journal!=null&&(journal.current.length()>0||journal.previous.length()>0||archive!=null&&archive.available());}
 static synchronized void snapshot(File destination)throws IOException{try(OutputStream out=new FileOutputStream(destination)){out.write(("CELIKOM COMBINED "+AppVersion.NAME+"\nCurrent and two previous runs; no credentials or audio bytes. Older segments may be rotated.\n\n").getBytes(StandardCharsets.UTF_8));if(archive!=null)archive.copyTo(out);if(journal!=null)journal.copyTo(out);}}
 static synchronized void end(String reason){if(active)force("run_end",map("reason",reason,"counts",new LinkedHashMap<>(counts)));active=false;}
 static Map<String,Object> map(Object...v){Map<String,Object> m=new LinkedHashMap<>();for(int i=0;i+1<v.length;i+=2)m.put(String.valueOf(v[i]),v[i+1]);return m;}
 static String clean(String s){if(s==null)return null;s=s.replaceAll("(?i)(Bearer\\s+)[A-Za-z0-9._~+/=-]+","$1[REDACTED]");s=s.replaceAll("(?i)((?:access_token|oauth_token|refresh_token|authorization|password|cookie|sessionid|secret|sign|signature|token)=)[^&#\\s]+","$1[REDACTED]");return s.length()>12000?s.substring(0,12000)+"[TRUNCATED]":s;}
 static boolean secret(String k){String s=k.toLowerCase(Locale.ROOT);return s.matches(".*(?:password|authorization|cookie|oauth|access.?token|refresh.?token|secret|account.?name|email|phone).*") && !s.contains("media_session");}
 static Object json(Object v,int d){if(v==null)return JSONObject.NULL;if(d>7)return "[DEPTH_LIMIT]";try{
  if(v instanceof Bundle){Bundle b=(Bundle)v;JSONObject j=new JSONObject();ArrayList<String> keys=new ArrayList<>(b.keySet());Collections.sort(keys);int n=0;for(String k:keys){if(++n>160){j.put("_truncated",true);break;}try{j.put(k,secret(k)?"[REDACTED]":json(b.get(k),d+1));}catch(Throwable e){j.put(k,"[UNREADABLE "+e.getClass().getSimpleName()+"]");}}return j;}
  if(v instanceof Map){JSONObject j=new JSONObject();for(Object k:((Map<?,?>)v).keySet())j.put(String.valueOf(k),secret(String.valueOf(k))?"[REDACTED]":json(((Map<?,?>)v).get(k),d+1));return j;}
  if(v instanceof Bitmap){Bitmap b=(Bitmap)v;return new JSONObject(map("type","Bitmap","width",b.getWidth(),"height",b.getHeight(),"pixels","not collected"));}
  if(v instanceof Icon){Icon i=(Icon)v;Map<String,Object> m=map("type","Icon","iconType",i.getType());if(i.getType()==Icon.TYPE_URI||i.getType()==Icon.TYPE_URI_ADAPTIVE_BITMAP)m.put("uri",i.getUri());if(i.getType()==Icon.TYPE_RESOURCE){m.put("resPackage",i.getResPackage());m.put("resId",i.getResId());}return json(m,d+1);}
  if(v instanceof PendingIntent){PendingIntent p=(PendingIntent)v;return json(map("type","PendingIntent","creatorPackage",p.getCreatorPackage(),"creatorUid",p.getCreatorUid(),"intentContents","not exposed by public API"),d+1);}
  if(v instanceof byte[])return "[byte array length="+((byte[])v).length+"]";
  if(v instanceof Iterable){JSONArray a=new JSONArray();int i=0;for(Object x:(Iterable<?>)v){if(i++>=80){a.put("[TRUNCATED]");break;}a.put(json(x,d+1));}return a;}
  if(v.getClass().isArray()){JSONArray a=new JSONArray();for(int i=0;i<Math.min(Array.getLength(v),80);i++)a.put(json(Array.get(v,i),d+1));return a;}
  if(v instanceof Number||v instanceof Boolean)return v;
  return clean(String.valueOf(v));
 }catch(Throwable e){return "[SERIALIZE_ERROR "+e.getClass().getSimpleName()+"]";}}
 static synchronized String status(){return (active?"Запись идёт":"Запись остановлена")+" · событий: "+events+"\nРазмер TXT: "+(file==null?0:file.length()/1024)+" КБ"+(failure.isEmpty()?"":"\n"+failure);}
 static void error(String channel,Throwable e){log("probe_error",map("channel",channel,"class",e.getClass().getName(),"message",e.getMessage()));}
}
