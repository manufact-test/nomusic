package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;

/* Durable, bounded and offline. No account/diagnostic grant is consulted. */
final class IncidentLog {
 static final long MAX_SEGMENT_BYTES=256*1024;
 private final DiagnosticJournal journal;
 IncidentLog(File file){this(file,MAX_SEGMENT_BYTES);}
 IncidentLog(File file,long limit){journal=new DiagnosticJournal(file,limit);}
 synchronized void record(String event,Object payload,long utcMs)throws IOException {
  Map<String,Object> safe=IncidentEvent.from(event,payload);
  if(safe==null)return;
  try{
   JSONObject row=new JSONObject();
   row.put("utc_ms",utcMs);
   row.put("event",event);
   row.put("data",new JSONObject(safe));
   journal.append((row.toString()+"\n").getBytes(StandardCharsets.UTF_8));
  }catch(JSONException e){throw new IOException("incident_encoding_failed",e);}
 }
 synchronized boolean hasReport(){return journal.current.length()>0||journal.previous.length()>0;}
 synchronized void snapshot(OutputStream out)throws IOException{
  out.write(("CELIKOM INCIDENT JOURNAL v1\n"+
   "Anonymous offline transport/process events. No tracks, account identifiers, "+
   "credentials, URLs or audio. Last two bounded segments; events are not a "+
   "continuous device availability monitor.\n\n").getBytes(StandardCharsets.UTF_8));
  journal.copyTo(out);
 }
}
