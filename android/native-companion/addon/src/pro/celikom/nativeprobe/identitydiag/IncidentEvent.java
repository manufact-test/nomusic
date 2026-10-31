package pro.celikom.nativeprobe.identitydiag;
import java.util.*;

/* Narrow, anonymous event schema. Raw tracks, account data, URLs, messages and
   arbitrary exception text must never enter the always-available incident log. */
final class IncidentEvent {
 static Map<String,Object> from(String type,Object payload){
  if(!(payload instanceof Map))return null;
  Map<?,?> input=(Map<?,?>)payload;
  LinkedHashMap<String,Object> out=new LinkedHashMap<>();
  switch(type){
   case "app_open": code(out,input,"version");number(out,input,"androidApi");break;
   case "previous_process_exit":number(out,input,"reason");number(out,input,"status");break;
   case "backend_result":code(out,input,"operation");bool(out,input,"ok");code(out,input,"errorCode");break;
   case "backend_http":code(out,input,"endpoint");number(out,input,"httpCode");number(out,input,"elapsedMs");break;
   case "backend_transport_failure":
    code(out,input,"endpoint");code(out,input,"errorClass");code(out,input,"phase");
    number(out,input,"elapsedMs");bool(out,input,"vpn");bool(out,input,"internet");bool(out,input,"validated");break;
   case "network_state":
    bool(out,input,"active");bool(out,input,"internet");bool(out,input,"validated");
    bool(out,input,"vpn");bool(out,input,"wifi");bool(out,input,"cellular");break;
   case "network_available":bool(out,input,"retry");break;
   case "network_lost":break;
   case "server_preflight":bool(out,input,"ok");code(out,input,"errorCode");break;
   case "replacement_stream_failure":code(out,input,"type");number(out,input,"elapsedMs");break;
   case "replacement_download_failure":
    code(out,input,"reasonCode");code(out,input,"type");number(out,input,"elapsedMs");break;
   case "media3_connection_failed":number(out,input,"attempt");code(out,input,"type");break;
   case "probe_error":code(out,input,"channel");code(out,input,"class");break;
   case "replacement_trial_stop":code(out,input,"reason");break;
   case "run_end":code(out,input,"reason");break;
   default:return null;
  }
  return out;
 }
 static void code(Map<String,Object> out,Map<?,?> in,String key){
  Object raw=in.get(key);
  if(!(raw instanceof String))return;
  String value=(String)raw;
  if(value.matches("[A-Za-z0-9_./-]{1,64}")&&!value.contains(".."))out.put(key,value);
 }
 static void bool(Map<String,Object> out,Map<?,?> in,String key){
  Object raw=in.get(key);if(raw instanceof Boolean)out.put(key,raw);
 }
 static void number(Map<String,Object> out,Map<?,?> in,String key){
  Object raw=in.get(key);
  if(!(raw instanceof Number))return;
  long value=((Number)raw).longValue();
  if(value>=0&&value<=36000000)out.put(key,value);
 }
}
