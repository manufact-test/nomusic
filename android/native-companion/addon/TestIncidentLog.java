package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/* The always-available incident path must remain anonymous, bounded and
   readable after a process restart, without any server/account permission. */
public final class TestIncidentLog {
 static void check(boolean good,String reason){if(!good)throw new AssertionError(reason);}
 static Map<String,Object> fields(Object... values){
  Map<String,Object> out=new LinkedHashMap<>();
  for(int i=0;i+1<values.length;i+=2)out.put((String)values[i],values[i+1]);
  return out;
 }
 static String snapshot(IncidentLog log)throws Exception{
  ByteArrayOutputStream out=new ByteArrayOutputStream();log.snapshot(out);
  return new String(out.toByteArray(),StandardCharsets.UTF_8);
 }
 public static void main(String[] args)throws Exception{
  Path temp=Files.createTempDirectory("celikom-incident-test-");
  try{
   File file=temp.resolve("incident.txt").toFile();
   IncidentLog first=new IncidentLog(file,600);
   first.record("app_open",fields("version","0.3.61","androidApi",33),1000);
   first.record("backend_transport_failure",fields(
    "endpoint","resolve","errorClass","SocketTimeoutException","phase","before_http",
    "elapsedMs",9604,"vpn",true,"internet",true,
    "access_token","TOP_SECRET","email","private@example.test",
    "title","Secret Song","trackId","12345","message","Bearer TOP_SECRET"),2000);
   first.record("player_state",fields("title","Secret Song"),2500);
   String saved=snapshot(first);
   check(saved.contains("backend_transport_failure"),"transport failure must be saved");
   check(saved.contains("SocketTimeoutException"),"exception category must survive");
   check(saved.contains("\"vpn\":true"),"VPN context must survive");
   check(!saved.contains("TOP_SECRET")&&!saved.contains("private@example.test")
    &&!saved.contains("Secret Song")&&!saved.contains("12345"),"sensitive fields must be excluded");
   check(!saved.contains("player_state"),"raw playback data must be excluded");
   IncidentLog reopened=new IncidentLog(file,600);
   check(snapshot(reopened).contains("backend_transport_failure"),
    "records must survive process recreation without authorization");
   for(int i=0;i<30;i++)reopened.record("backend_result",fields(
    "operation","resolve","ok",false,"errorCode","timeout"),3000+i);
   String rotated=snapshot(new IncidentLog(file,600));
   check(rotated.contains("\"utc_ms\":3029"),"latest incident must survive bounded rotation");
   check(rotated.length()<2000,"two short journal segments must bound retention");
   check(!rotated.contains("TOP_SECRET"),"rotation must not expose tokens");
   reopened.record("previous_process_exit",fields("reason",6,"status",137),5000);
   check(snapshot(new IncidentLog(file,600)).contains("previous_process_exit"),
    "Android process-exit reason must be preserved for next launch");
   check(IncidentEvent.from("backend_result",fields("operation","resolve",
    "errorCode","Bearer secret","ok",false)).containsKey("errorCode")==false,
    "untrusted error text must be filtered");
   System.out.println("PASS TestIncidentLog: persisted offline, bounded, redacted, exit history");
  }finally{
   try(java.util.stream.Stream<Path> files=Files.walk(temp)){
    files.sorted(Comparator.reverseOrder()).forEach(p->{try{Files.deleteIfExists(p);}catch(IOException ignored){}});
   }
  }
 }
}
