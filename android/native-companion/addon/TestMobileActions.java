package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.json.*;
public class TestMobileActions {
 static int checks;static void check(boolean value,String reason){checks++;if(!value)throw new AssertionError(reason);}
 interface Attempt{void run()throws Exception;}
 static void rejects(Attempt action)throws Exception{boolean rejected=false;try{action.run();}catch(Exception e){rejected=true;}check(rejected,"invalid input must be rejected");}
 public static void main(String[] args)throws Exception{
  String id="123456789",key=UUID.randomUUID().toString(),boundary="celikom-"+UUID.randomUUID();
  MobileActions.Target target=new MobileActions.Target(id,"current","Название\r\nInjected", "Исполнитель",180000);
  JSONObject fields=target.fields(key,true);check("1".equals(fields.getString("declaration")),"rights declaration uses server's existing value");check("180000".equals(fields.getString("duration_ms")),"duration is the pinned source duration");check(key.equals(fields.getString("request_id")),"retries retain idempotency key");check(!target.title.contains("\r")&&!target.title.contains("\n"),"song metadata cannot inject multipart headers");
  String body=new String(MobileActions.prefix(fields,boundary,"m4a"),StandardCharsets.UTF_8);check(body.contains("name=\"file\"; filename=\"version.m4a\""),"only a generic filename is transmitted");check(body.contains("Content-Type: audio/mp4\r\n\r\n"),"M4A keeps the existing server contract");check(body.contains("name=\"track_id\"\r\n\r\n"+id+"\r\n"),"exact identity is submitted");check(new String(MobileActions.suffix(boundary,true),StandardCharsets.UTF_8).equals("\r\n--"+boundary+"--\r\n"),"file multipart terminates correctly");
  JSONObject suggestion=target.fields(null,false);check(!suggestion.has("declaration")&&!suggestion.has("request_id"),"suggestion has no fake audio declaration");check(!new String(MobileActions.prefix(suggestion,boundary,null),StandardCharsets.UTF_8).contains("filename="),"suggestions contain no file part");
  check("mp3".equals(MobileActions.extension("Песня.MP3")),"case-insensitive MP3 selection");check("m4a".equals(MobileActions.extension("audio.m4a")),"AAC container selection");rejects(()->MobileActions.extension("song.wav"));rejects(()->MobileActions.extension("song.mp3.exe"));rejects(()->new MobileActions.Target("0","key","a","b",1000));rejects(()->new MobileActions.Target("1\r\n","key","a","b",1000));rejects(()->new MobileActions.Target("1","key","a","b",0));rejects(()->target.fields("bad",true));rejects(()->MobileActions.prefix(fields,"bad\r\nheader","mp3"));rejects(()->MobileActions.prefix(fields,boundary,"mp3\r\nheader"));
  String unicode=String.join("",Collections.nCopies(200,"😀я"));String safe=MobileActions.safe(unicode,240);check(safe.getBytes(StandardCharsets.UTF_8).length<=240,"server's metadata byte limit is respected");check(!safe.endsWith("\ud83d"),"truncation preserves code points");
  JSONObject general=MobileActions.support("Нужна помощь",key,null,null);check("general".equals(general.getString("kind"))&&!general.has("report"),"general support carries no diagnostics");JSONObject song=MobileActions.support("",key,target,"audio_issue");check("song".equals(song.getString("kind")),"song report kind matches desktop");check(id.equals(song.getJSONObject("report").getJSONObject("track").getString("id")),"song support pins exact track");check(song.getJSONObject("report").getJSONObject("diagnostics").has("trace"),"song support always contains bounded trace");
  SupportTrace.record("replacement_resolve",LogStore.map("trackId",id,"found",true));
  SupportTrace.record("replacement_recovery",LogStore.map("trackId",id,"reason","alignment_unstable","driftMs",123,"Authorization","SECRET"));
  SupportTrace.record("replacement_recovery",LogStore.map("trackId","1111111","reason","other_track"));
  JSONObject traced=MobileActions.support("",key,target,"audio_issue");
  String diagnostic=traced.getJSONObject("report").getJSONObject("diagnostics").toString();
  check(diagnostic.contains("alignment_unstable")&&!diagnostic.contains("SECRET")&&!diagnostic.contains("other_track"),"bounded support trace pins song and removes secret fields");
  SupportTrace.clear();
  check(MobileActions.support("",key,target,"audio_issue").getJSONObject("report").getJSONObject("diagnostics").getJSONArray("trace").length()==0,"logout clears support trace");rejects(()->MobileActions.support("",key,null,null));rejects(()->MobileActions.support("x",key,target,"unknown"));rejects(()->MobileActions.support("text","bad",null,null));
  RequestBudget budget=new RequestBudget();check(budget.allow("first",1000),"first request allowed");check(!budget.allow("burst",1001),"request bursts remain paced");check(budget.allow("next",2500),"new song allowed after pacing interval");check(!budget.allow("next",4000),"same album retries cool down");check(budget.allow("next",32500),"failed album retried after cooldown");for(int hour=1;hour<=24;hour++)check(budget.allow("hour-"+hour,hour*3600000L),"pacing works throughout a full day");
  Path directory=Files.createTempDirectory("celikom-journal-");File file=directory.resolve("report.txt").toFile();DiagnosticJournal journal=new DiagnosticJournal(file,128);journal.reset();
  for(int i=0;i<1000;i++)journal.append((String.format(Locale.ROOT,"%04d",i)+" · проверка\n").getBytes(StandardCharsets.UTF_8));
  check(journal.current.length()<=128&&journal.previous.length()<=128,"diagnostics remain bounded over many rotations");ByteArrayOutputStream bytes=new ByteArrayOutputStream();journal.copyTo(bytes);String snapshot=bytes.toString("UTF-8");check(snapshot.endsWith("0999 · проверка\n"),"export includes the latest event");String[] lines=snapshot.split("\n");int previous=-1;for(String line:lines){int n=Integer.parseInt(line.substring(0,4));check(n>previous,"rotated export retains chronological complete records");previous=n;}journal.append("1000 · дальше\n".getBytes(StandardCharsets.UTF_8));check(!snapshot.contains("1000"),"snapshot stays immutable while logging continues");journal.reset();check(file.length()==0&&!journal.previous.exists(),"fresh run removes both prior segments");Files.delete(file.toPath());Files.delete(directory);
  System.out.println("PASS: "+checks+" native contribution/support, rolling request budget and diagnostic rotation checks");
 }
}
