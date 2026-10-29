package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;
/** Existing desktop contribution/support contracts, with immutable song targets. */
final class MobileActions {
 static final long MAX_AUDIO_BYTES=31457280;
 static final class Target {
  final String id,key,title,artist;final long duration;
  Target(String id,String key,String title,String artist,long duration)throws Exception{
   if(id==null||!id.matches("[1-9][0-9]{0,23}")||duration<1000||duration>86400000||key==null)throw new Exception("track_required");
   this.id=id;this.key=key;this.title=safe(title,240);this.artist=safe(artist,240);this.duration=duration;
  }
  JSONObject fields(String requestId,boolean upload)throws Exception{
   JSONObject j=new JSONObject().put("service","yandex").put("track_id",id).put("title",title).put("artist",artist).put("album","");
   if(upload){uuid(requestId);j.put("duration_ms",String.valueOf(duration)).put("request_id",requestId).put("declaration","1");}return j;
  }
 }
 static String safe(String value,int bytes){
  String s=value==null?"":value.replaceAll("[\\x00-\\x1f]"," ").trim();
  while(s.getBytes(StandardCharsets.UTF_8).length>bytes)s=s.substring(0,s.offsetByCodePoints(s.length(),-1));return s;
 }
 static void uuid(String value)throws Exception{if(value==null||!value.matches("[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}"))throw new Exception("invalid_request");}
 static String extension(String name)throws Exception{String s=name==null?"":name.toLowerCase(Locale.ROOT);if(s.endsWith(".mp3"))return "mp3";if(s.endsWith(".m4a"))return "m4a";throw new Exception("invalid_audio_file");}
 static byte[] prefix(JSONObject fields,String boundary,String extension)throws Exception{
  if(!boundary.matches("celikom-[a-f0-9-]{36}"))throw new Exception("invalid_request");
  ByteArrayOutputStream out=new ByteArrayOutputStream();Iterator<String> keys=fields.keys();
  while(keys.hasNext()){String key=keys.next();if(!Arrays.asList("service","track_id","title","artist","album","duration_ms","request_id","declaration").contains(key))throw new Exception("invalid_request");
   out.write(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+key+"\"\r\n\r\n"+fields.getString(key)+"\r\n").getBytes(StandardCharsets.UTF_8));}
  if(extension!=null){if(!Arrays.asList("mp3","m4a").contains(extension))throw new Exception("invalid_audio_file");out.write(("--"+boundary+"\r\nContent-Disposition: form-data; name=\"file\"; filename=\"version."+extension+"\"\r\nContent-Type: "+("mp3".equals(extension)?"audio/mpeg":"audio/mp4")+"\r\n\r\n").getBytes(StandardCharsets.UTF_8));}
  return out.toByteArray();
 }
 static byte[] suffix(String boundary,boolean file){return ((file?"\r\n":"")+"--"+boundary+"--\r\n").getBytes(StandardCharsets.UTF_8);}
 static JSONObject support(String message,String requestKey,Target target,String category)throws Exception{
  uuid(requestKey);String text=message==null?"":message.trim();if(text.length()>2000||text.getBytes(StandardCharsets.UTF_8).length>6000||text.matches("(?s).*[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f].*"))throw new Exception("invalid_message");
  if(target==null&&text.getBytes(StandardCharsets.UTF_8).length<3)throw new Exception("message_required");
  JSONObject j=new JSONObject().put("kind",target==null?"general":"song").put("message",text).put("request_key",requestKey);
  if(target!=null){
   if(!Arrays.asList("not_replacing","wrong_version","audio_issue","other").contains(category))throw new Exception("invalid_request");
   JSONObject diagnostics=SupportTrace.snapshot(target.id);
   j.put("report",new JSONObject().put("category",category).put("version",AppVersion.NAME)
    .put("track",new JSONObject().put("id",target.id).put("title",target.title).put("artist",target.artist).put("album",""))
    .put("diagnostics",diagnostics));
   // NativeApi rejects bodies over 8 KiB. Remove oldest trace entries, not the ticket.
   // Keep the freshest symptoms and the user's message even during a noisy failure.
   JSONArray trace=diagnostics.getJSONArray("trace");
   while(j.toString().getBytes(StandardCharsets.UTF_8).length>7500&&trace.length()>0){
    JSONArray newest=new JSONArray();for(int n=1;n<trace.length();n++)newest.put(trace.get(n));
    trace=newest;diagnostics.put("trace",trace);
   }
   if(j.toString().getBytes(StandardCharsets.UTF_8).length>8192)throw new Exception("invalid_request");
  }return j;
 }
}
