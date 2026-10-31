package pro.celikom.nativeprobe.identitydiag;
import android.app.ActivityManager;
import android.app.ApplicationExitInfo;
import android.content.Context;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Build;
import android.os.SystemClock;
import java.io.*;
import java.util.*;

/* Separate from full owner-only diagnostics and the playback service.
   A failed server check must never prevent writing or exporting this log. */
final class IncidentJournal {
 private static IncidentLog log;
 private IncidentJournal(){}
 static synchronized void init(Context context){
  if(log!=null)return;
  Context app=context.getApplicationContext();
  log=new IncidentLog(new File(app.getFilesDir(),"incident-journal-v1.txt"));
  record("app_open",LogStore.map("version",AppVersion.NAME,"androidApi",Build.VERSION.SDK_INT));
  recordPreviousExit(app);
 }
 static synchronized void record(String event,Object payload){
  if(log==null)return;
  try{log.record(event,payload,System.currentTimeMillis());}catch(Exception ignored){
   /* Never affect audio, authentication or UI when local storage is unavailable. */
  }
 }
 static synchronized boolean hasReport(){return log!=null&&log.hasReport();}
 static synchronized void snapshot(File destination)throws IOException{
  if(log==null)throw new IOException("incident_not_initialized");
  try(OutputStream out=new FileOutputStream(destination)){log.snapshot(out);}
 }
 static void transportFailure(Context context,String endpoint,Throwable failure,long elapsedMs,boolean receivedHttp){
  String safeEndpoint=endpoint==null?"unknown":endpoint.split("\\?")[0];
  Map<String,Object> data=LogStore.map("endpoint",safeEndpoint,
   "errorClass",failure.getClass().getSimpleName(),
   "phase",receivedHttp?"after_http":"before_http",
   "elapsedMs",elapsedMs);
  try{
   ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
   Network network=manager==null?null:manager.getActiveNetwork();
   NetworkCapabilities capabilities=manager==null||network==null?null:manager.getNetworkCapabilities(network);
   if(capabilities!=null){
    data.put("vpn",capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN));
    data.put("internet",capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET));
    data.put("validated",capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED));
   }
  }catch(RuntimeException ignored){}
  record("backend_transport_failure",data);
 }
 private static void recordPreviousExit(Context context){
  if(Build.VERSION.SDK_INT<30)return;
  try{
   ActivityManager manager=context.getSystemService(ActivityManager.class);
   if(manager==null)return;
   SharedPreferences pref=context.getSharedPreferences("incident-exit-v1",0);
   long last=pref.getLong("last-time",0),newest=last;
   for(ApplicationExitInfo info:manager.getHistoricalProcessExitReasons(null,0,8)){
    if(!context.getApplicationInfo().processName.equals(info.getProcessName()))continue;
    long timestamp=info.getTimestamp();
    if(timestamp<=last||timestamp>System.currentTimeMillis())continue;
    record("previous_process_exit",LogStore.map("reason",info.getReason(),"status",info.getStatus()));
    newest=Math.max(newest,timestamp);
   }
   if(newest!=last)pref.edit().putLong("last-time",newest).apply();
  }catch(RuntimeException ignored){}
 }
}
