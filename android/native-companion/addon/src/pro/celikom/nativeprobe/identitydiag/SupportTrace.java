package pro.celikom.nativeprobe.identitydiag;
import java.util.*;
import org.json.*;
/** Explicit song support reports only. Bounded codes, no private LogStore access. */
final class SupportTrace {
 private static final int LIMIT=160;
 private static final ArrayDeque<JSONObject> ring=new ArrayDeque<>();
 private static String currentTrack="";
 private static final Set<String> EVENTS=new HashSet<>(Arrays.asList(
   "backend_http","backend_result","replacement_resolve","replacement_stream_ready",
   "replacement_prepared","replacement_sync","replacement_seek_complete","replacement_warm_alignment",
   "replacement_decoder_advancing","replacement_transition_complete","replacement_recovery",
   "replacement_released","replacement_output_silenced","replacement_original_restored",
   "replacement_original_muted","replacement_stream_retry","replacement_stream_prefetch_wait",
   "source_discontinuity","album_resolution","playback_health"));
 private static final Set<String> NUMBERS=new HashSet<>(Arrays.asList(
   "elapsedMs","driftMs","residualMs","sourcePositionMs","cachedBytes",
   "correctionPass","pass","rampMs","retryMs","httpCode"));
 private static final Set<String> FLAGS=new HashSet<>(Arrays.asList(
   "gainZero","paused","found","replacementAudible","beforeTransportCleanup","ok"));
 private static final Set<String> CODES=new HashSet<>(Arrays.asList("reason","state","phase","result","errorCode","operation"));
 private static final Set<String> ENDPOINTS=new HashSet<>(Arrays.asList(
   "config","auth/me","entitlement","resolve","tracks/upload-status","tracks/version-status","rewards"));
 static synchronized void record(String event,Object source) {
  if(!(source instanceof Map))return;
  Map<?,?> data=(Map<?,?>)source;
  // Preserve real failure causes without widening the server's strict event whitelist.
  String impliedReason=null;
  switch(event){
   case "replacement_alignment_rejected": event="replacement_recovery";impliedReason="alignment_unstable";break;
   case "replacement_duration_mismatch":event="replacement_recovery";impliedReason="duration_mismatch";break;
   case "replacement_stream_failure": event="replacement_recovery";impliedReason="stream_failure";break;
   case "replacement_download_failure": event="replacement_recovery";impliedReason="download_failed";break;
   case "replacement_stream_fallback":event="replacement_recovery";break;
   case "replacement_failure":event="replacement_recovery";break;
   case "replacement_buffer_wait":event="replacement_stream_prefetch_wait";break;
   case "replacement_buffer_resumed":event="replacement_stream_ready";break;
   case "replacement_source_boundary":event="source_discontinuity";break;
   case "replacement_trial_stop":event="replacement_released";break;
  }
  if(!EVENTS.contains(event))return;
  Object rawTrack=data.get("trackId");
  String track=rawTrack instanceof String?(String)rawTrack:"";
  if(track.matches("[1-9][0-9]{0,23}"))currentTrack=track;
  else track=currentTrack;
  if(!track.matches("[1-9][0-9]{0,23}"))return;
  try {
   JSONObject row=new JSONObject().put("event",event).put("_at",System.nanoTime()/1000000L).put("_track",track);
   for(String k:NUMBERS){
    Object v=data.get(k);
    if(v instanceof Integer||v instanceof Long){
     long n=((Number)v).longValue();
     if(n>=((k.equals("driftMs")||k.equals("residualMs"))?-86400000:0)&&n<=86400000)row.put(k,n);
    }
   }
   for(String k:FLAGS){Object v=data.get(k);if(v instanceof Boolean)row.put(k,v);}
   for(String k:CODES){Object v=data.get(k);
    if(v instanceof String&&((String)v).matches("[a-zA-Z0-9_.:-]{1,64}"))row.put(k,v);
   }
   if(impliedReason!=null)row.put("reason",impliedReason);
   Object rawEndpoint=data.get("endpoint");
   String endpoint=rawEndpoint instanceof String?(String)rawEndpoint:"";
   if(ENDPOINTS.contains(endpoint))row.put("endpoint",endpoint);
   ring.addLast(row);while(ring.size()>LIMIT)ring.removeFirst();
  }catch(JSONException ignored){}
 }
 static synchronized JSONObject snapshot(String track){
  JSONObject result=new JSONObject();JSONArray arr=new JSONArray();long now=System.nanoTime()/1000000L;
  try {
   for(JSONObject stored:ring){
    if(!track.equals(stored.optString("_track")))continue;
    long age=Math.max(0,now-stored.optLong("_at"));if(age>180000)continue;
    JSONObject row=new JSONObject(stored.toString());row.remove("_track");row.remove("_at");row.put("ageMs",age);
    arr.put(row);
   }
   JSONArray bounded=new JSONArray();
   for(int i=Math.max(0,arr.length()-48);i<arr.length();i++)bounded.put(arr.getJSONObject(i));
   result.put("trace",bounded);
  }catch(JSONException ignored){}
  return result;
 }
 static synchronized void clear(){ring.clear();currentTrack="";}
}