package pro.celikom.nativeprobe.identitydiag;
import android.content.Context;
import android.os.*;
import org.json.*;
import javax.net.ssl.HttpsURLConnection;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
/** One serialized transport for refresh rotation; no embedded user/API credentials. */
final class NativeApi {
 interface Result {void done(JSONObject result,String error);}
 volatile boolean revoking;volatile long accountGeneration;static NativeApi singleton;final SecureSession session;final Context context;final ExecutorService work=Executors.newSingleThreadExecutor();final ExecutorService audioWork=Executors.newSingleThreadExecutor();final ExecutorService contributions=Executors.newSingleThreadExecutor();final Handler main=new Handler(Looper.getMainLooper());
 static synchronized NativeApi get(Context c){if(singleton==null)singleton=new NativeApi(c);return singleton;}
 NativeApi(Context c){context=c.getApplicationContext();session=new SecureSession(c);}
 boolean signedIn(){return !revoking&&!session.read().optString("refresh_token").isEmpty();}
 void submit(String task,Callable<JSONObject> action,Result result){work.execute(()->{JSONObject j=null;String error=null;try{j=action.call();}catch(Exception e){error=e.getMessage();if(error==null||!error.matches("[a-z0-9_]{1,80}"))error="network_or_response_error";}final JSONObject out=j;final String fail=error;LogStore.log("backend_result",LogStore.map("operation",task,"ok",fail==null,"errorCode",fail));main.post(()->result.done(out,fail));});}
 JSONObject request(String path,JSONObject body,String access)throws Exception {return request(path,body,access,null);}
 JSONObject request(String path,JSONObject body,String access,java.util.function.BooleanSupplier valid)throws Exception {
  HttpsURLConnection c=(HttpsURLConnection)new URL(ApiContract.ORIGIN+"/api/v1/"+path).openConnection();long start=SystemClock.elapsedRealtime();
  try(ReadFence fence=new ReadFence(c,valid)){fence.check();c.setConnectTimeout(7000);c.setReadTimeout(8000);c.setInstanceFollowRedirects(false);c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-store");if(access!=null&&!access.isEmpty())c.setRequestProperty("Authorization","Bearer "+access);
   if(body!=null){byte[] data=body.toString().getBytes(StandardCharsets.UTF_8);if(data.length>8192)throw new Exception("invalid_request");c.setRequestMethod("POST");c.setRequestProperty("Content-Type","application/json");c.setDoOutput(true);c.setFixedLengthStreamingMode(data.length);try(OutputStream out=c.getOutputStream()){out.write(data);}}
   int code=c.getResponseCode();if(code>=300&&code<400)throw new Exception("redirect_rejected");String type=c.getContentType();if(type==null||!type.toLowerCase().startsWith("application/json"))throw new Exception("invalid_api_response");InputStream stream=code>=200&&code<300?c.getInputStream():c.getErrorStream();JSONObject j;
   try(InputStream in=stream;ByteArrayOutputStream out=new ByteArrayOutputStream()){if(in==null)throw new Exception("empty_api_response");byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){fence.check();if(out.size()+n>65536||SystemClock.elapsedRealtime()-start>18000)throw new Exception("response_limit");out.write(b,0,n);}j=new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));}
   fence.check();LogStore.log("backend_http",LogStore.map("endpoint",path.split("\\?")[0],"httpCode",code,"elapsedMs",SystemClock.elapsedRealtime()-start));
   if(code<200||code>=300){String e=j.optString("error","api_http_error");throw new Exception(e.matches("[a-z0-9_]{1,80}")?e:"api_http_error");}return j;
  }finally{c.disconnect();}
 }
 String access()throws Exception {if(revoking)throw new Exception("login_required");JSONObject s=session.read();if(s.optString("refresh_token").isEmpty())throw new Exception("login_required");if(s.optLong("access_until_ms")<System.currentTimeMillis()+30000){try{s=request("auth/refresh",new JSONObject().put("refresh_token",s.getString("refresh_token")).put("installation_id",session.installation()),null);session.save(s);}catch(Exception e){if("invalid_session".equals(e.getMessage()))session.clear();throw e;}}return s.getString("access_token");}
 JSONObject authenticated(String path,JSONObject body)throws Exception{return request(path,body,access());}
 void login(String email,String password,Result r){submit("login",()->{JSONObject j=request("auth/login",new JSONObject().put("email",email.trim()).put("password",password).put("installation_id",session.installation()),null);if(j.has("access_token")){session.save(j);accountGeneration++;revoking=false;}return new JSONObject().put("verification_required",j.optBoolean("verification_required",false)).put("signedIn",j.has("access_token"));},r);}
 void verify(String email,String code,Result r){submit("verify_email",()->{JSONObject j=request("auth/verify-email",new JSONObject().put("email",email.trim()).put("code",code.trim()).put("installation_id",session.installation()),null);session.save(j);accountGeneration++;revoking=false;return new JSONObject().put("signedIn",true);},r);}
 void check(Result r){submit("server_check",()->{JSONObject c=request("config",null,null);ApiContract.config(c);JSONObject out=new JSONObject().put("server",true).put("signedIn",signedIn());if(signedIn())out.put("entitlement",authenticated("entitlement",null));return out;},r);}
 void startAccess(Result r){final long generation=accountGeneration;submit("start_access",()->{if(generation!=accountGeneration)throw new Exception("login_required");ApiContract.config(request("config",null,null));JSONObject j=authenticated("auth/activate",new JSONObject());JSONObject entitlement=j.optJSONObject("entitlement");if(entitlement==null||!(entitlement.opt("allowed") instanceof Boolean))throw new Exception("invalid_api_response");return entitlement;},r);}
 void logout(Result r){revoking=true;accountGeneration++;submit("logout",()->{try{JSONObject s=session.read();if(s.has("refresh_token"))request("auth/logout",new JSONObject().put("refresh_token",s.getString("refresh_token")).put("installation_id",session.installation()),null);}finally{session.clear();}return new JSONObject().put("ok",true);},r);}
 void support(JSONObject body,Result r){final long generation=accountGeneration;submit("support",()->{if(generation!=accountGeneration)throw new Exception("login_required");return authenticated("support",body);},r);}
 void presence(String id,Result r){submit("track_status",()->authenticated("tracks/upload-status?service=yandex&track_id="+id,null),r);}
 interface Progress {void update(int percent);}
 void contribute(MobileActions.Target target,File file,String extension,String requestId,Progress progress,Result result){
  final long generation=accountGeneration;
  // Token refresh stays serialized with playback. The file transfer has a separate
  // worker so a slow upload cannot block resolving/downloading the next song.
  work.execute(()->{try{if(generation!=accountGeneration)throw new Exception("login_required");String token=access();contributions.execute(()->{
   JSONObject response=null;String error=null;HttpsURLConnection c=null;
   try{
    if(revoking||generation!=accountGeneration)throw new Exception("login_required");
    boolean upload=file!=null;long size=upload?file.length():0;if(upload&&(size<1024||size>MobileActions.MAX_AUDIO_BYTES))throw new Exception("invalid_audio_file");
    String boundary="celikom-"+java.util.UUID.randomUUID();byte[] first=MobileActions.prefix(target.fields(requestId,upload),boundary,upload?extension:null),last=MobileActions.suffix(boundary,upload);
    c=(HttpsURLConnection)new URL(ApiContract.ORIGIN+"/api/v1/"+(upload?"uploads":"track-requests")).openConnection();c.setConnectTimeout(7000);c.setReadTimeout(15000);c.setInstanceFollowRedirects(false);c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("Authorization","Bearer "+token);c.setRequestProperty("Accept","application/json");c.setRequestProperty("Content-Type","multipart/form-data; boundary="+boundary);c.setRequestProperty("Cache-Control","no-store");if(upload)c.setRequestProperty("X-Celikom-Upload-Attempt",requestId);c.setFixedLengthStreamingMode(first.length+size+last.length);
    final HttpsURLConnection connection=c;final long started=SystemClock.elapsedRealtime();java.util.concurrent.ScheduledExecutorService timer=Executors.newSingleThreadScheduledExecutor();java.util.concurrent.ScheduledFuture<?> deadline=timer.schedule(connection::disconnect,60,TimeUnit.SECONDS);
    try{
     try(OutputStream out=c.getOutputStream()){
      out.write(first);if(upload)try(InputStream in=new FileInputStream(file)){byte[] b=new byte[32768];int n,lastPercent=-1;long sent=0;while((n=in.read(b))!=-1){if(revoking||generation!=accountGeneration||SystemClock.elapsedRealtime()-started>60000)throw new Exception("upload_interrupted");sent+=n;if(sent>size)throw new Exception("invalid_audio_file");out.write(b,0,n);int percent=(int)(sent*100/size);if(percent!=lastPercent){lastPercent=percent;main.post(()->progress.update(percent));}}if(sent!=size)throw new Exception("invalid_audio_file");}out.write(last);
     }
     int code=c.getResponseCode();if(code>=300&&code<400)throw new Exception("redirect_rejected");String type=c.getContentType();if(type==null||!type.toLowerCase(java.util.Locale.ROOT).startsWith("application/json"))throw new Exception("invalid_api_response");
     try(InputStream in=code>=200&&code<300?c.getInputStream():c.getErrorStream();ByteArrayOutputStream bytes=new ByteArrayOutputStream()){
      if(in==null)throw new Exception("empty_api_response");byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(bytes.size()+n>65536)throw new Exception("response_limit");bytes.write(b,0,n);}response=new JSONObject(new String(bytes.toByteArray(),StandardCharsets.UTF_8));}
     if(code<200||code>=300)throw new Exception(response.optString("error","api_http_error"));
    }finally{deadline.cancel(false);timer.shutdownNow();}
   }catch(Exception e){String message=e.getMessage();error=message!=null&&message.matches("[a-z0-9_]{1,80}")?message:"network_or_response_error";}
   finally{if(c!=null)c.disconnect();}
   final JSONObject out=response;final String fail=error;LogStore.log("backend_result",LogStore.map("operation",file==null?"track_request":"upload","ok",fail==null,"errorCode",fail));main.post(()->result.done(out,fail));
  });}catch(Exception e){main.post(()->result.done(null,"login_required"));}});
 }
 void resolve(String id,Result r){resolve(id,()->true,r);}
 void resolve(String id,java.util.function.BooleanSupplier current,Result result){final long account=accountGeneration;java.util.function.BooleanSupplier valid=()->!revoking&&account==accountGeneration&&current.getAsBoolean();
  submit("resolve",()->{if(!valid.getAsBoolean())throw new Exception("lookup_cancelled");if(id==null||!id.matches("[1-9][0-9]{0,23}"))throw new Exception("invalid_track");ApiContract.config(request("config",null,null,valid));if(!valid.getAsBoolean())throw new Exception("lookup_cancelled");
   // Refresh token rotation remains serialized and must finish even if the song changes.
   String token=access();if(!valid.getAsBoolean())throw new Exception("lookup_cancelled");JSONObject j=request("resolve?audio_formats=mp3,m4a&service=yandex&track_id="+id,null,token,valid);if(j.optBoolean("found"))ApiContract.audio(j,System.currentTimeMillis());return j;},result);
 }
 interface StreamResult {void done(BufferedAudio source,String error);}
 void stream(JSONObject descriptor,java.util.function.BooleanSupplier valid,StreamResult result){final long account=accountGeneration;audioWork.execute(()->{BufferedAudio source=null;String error=null;long start=SystemClock.elapsedRealtime();try{
  java.util.function.BooleanSupplier allowed=()->!revoking&&account==accountGeneration&&valid.getAsBoolean();
  if(!allowed.getAsBoolean())throw new Exception("audio_cancelled");
  File file=File.createTempFile("buffered-",".audio",context.getCacheDir());
  source=new BufferedAudio(file,()->(HttpsURLConnection)new URL(ApiContract.audio(descriptor,System.currentTimeMillis())).openConnection(),allowed,SystemClock::elapsedRealtime,(name,bytes)->LogStore.log(name,LogStore.map("cachedBytes",bytes,"elapsedMs",SystemClock.elapsedRealtime()-start)));
  source.initialize();if(!allowed.getAsBoolean())throw new Exception("audio_cancelled");
 }catch(Exception e){if(source!=null)source.close();source=null;error="audio_stream_unavailable";LogStore.log("replacement_stream_failure",LogStore.map("type",e.getClass().getSimpleName(),"elapsedMs",SystemClock.elapsedRealtime()-start));}
 final BufferedAudio out=source;final String fail=error;main.post(()->result.done(out,fail));});}
 interface AudioResult{void done(File file,String error);}
 void download(JSONObject descriptor,java.util.function.BooleanSupplier valid,AudioResult r){final long account=accountGeneration;audioWork.execute(()->{File file=null;String error=null;long started=SystemClock.elapsedRealtime();java.util.function.BooleanSupplier allowed=()->!revoking&&account==accountGeneration&&valid.getAsBoolean();try{
  if(!allowed.getAsBoolean())throw new Exception("download_cancelled");
  file=File.createTempFile("replacement-",".audio",context.getCacheDir());
  AudioTransfer.copy(file,()->(HttpsURLConnection)new URL(ApiContract.audio(descriptor,System.currentTimeMillis())).openConnection(),allowed,SystemClock::elapsedRealtime,(attempt,bytes,reason)->LogStore.log("replacement_download_retry",LogStore.map("attempt",attempt,"retainedBytes",bytes,"reasonCode",reason)));
  LogStore.log("replacement_download",LogStore.map("bytes",file.length(),"elapsedMs",SystemClock.elapsedRealtime()-started));
 }catch(Exception e){long bytes=file==null?0:file.length();if(file!=null)file.delete();file=null;error="audio_download_failed";String reason=e.getMessage();LogStore.log("replacement_download_failure",LogStore.map("reasonCode",reason!=null&&reason.matches("[a-z0-9_]{1,80}")?reason:"transport_or_file_error","type",e.getClass().getSimpleName(),"receivedBytes",bytes,"elapsedMs",SystemClock.elapsedRealtime()-started));}
 final File out=file;final String fail=error;main.post(()->r.done(out,fail));});}
}
