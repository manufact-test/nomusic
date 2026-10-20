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
 volatile boolean revoking;static NativeApi singleton;final SecureSession session;final Context context;final ExecutorService work=Executors.newSingleThreadExecutor();final Handler main=new Handler(Looper.getMainLooper());
 static synchronized NativeApi get(Context c){if(singleton==null)singleton=new NativeApi(c);return singleton;}
 NativeApi(Context c){context=c.getApplicationContext();session=new SecureSession(c);}
 boolean signedIn(){return !revoking&&!session.read().optString("refresh_token").isEmpty();}
 void submit(String task,Callable<JSONObject> action,Result result){work.execute(()->{JSONObject j=null;String error=null;try{j=action.call();}catch(Exception e){error=e.getMessage();if(error==null||!error.matches("[a-z0-9_]{1,80}"))error="network_or_response_error";}final JSONObject out=j;final String fail=error;LogStore.log("backend_result",LogStore.map("operation",task,"ok",fail==null,"errorCode",fail));main.post(()->result.done(out,fail));});}
 JSONObject request(String path,JSONObject body,String access)throws Exception {
  HttpsURLConnection c=(HttpsURLConnection)new URL(ApiContract.ORIGIN+"/api/v1/"+path).openConnection();long start=SystemClock.elapsedRealtime();
  try{c.setConnectTimeout(7000);c.setReadTimeout(8000);c.setInstanceFollowRedirects(false);c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-store");if(access!=null&&!access.isEmpty())c.setRequestProperty("Authorization","Bearer "+access);
   if(body!=null){byte[] data=body.toString().getBytes(StandardCharsets.UTF_8);if(data.length>8192)throw new Exception("invalid_request");c.setRequestMethod("POST");c.setRequestProperty("Content-Type","application/json");c.setDoOutput(true);c.setFixedLengthStreamingMode(data.length);try(OutputStream out=c.getOutputStream()){out.write(data);}}
   int code=c.getResponseCode();if(code>=300&&code<400)throw new Exception("redirect_rejected");String type=c.getContentType();if(type==null||!type.toLowerCase().startsWith("application/json"))throw new Exception("invalid_api_response");InputStream stream=code>=200&&code<300?c.getInputStream():c.getErrorStream();JSONObject j;
   try(InputStream in=stream;ByteArrayOutputStream out=new ByteArrayOutputStream()){if(in==null)throw new Exception("empty_api_response");byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()+n>65536||SystemClock.elapsedRealtime()-start>18000)throw new Exception("response_limit");out.write(b,0,n);}j=new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));}
   LogStore.log("backend_http",LogStore.map("endpoint",path.split("\\?")[0],"httpCode",code,"elapsedMs",SystemClock.elapsedRealtime()-start));
   if(code<200||code>=300){String e=j.optString("error","api_http_error");throw new Exception(e.matches("[a-z0-9_]{1,80}")?e:"api_http_error");}return j;
  }finally{c.disconnect();}
 }
 String access()throws Exception {if(revoking)throw new Exception("login_required");JSONObject s=session.read();if(s.optString("refresh_token").isEmpty())throw new Exception("login_required");if(s.optLong("access_until_ms")<System.currentTimeMillis()+30000){try{s=request("auth/refresh",new JSONObject().put("refresh_token",s.getString("refresh_token")).put("installation_id",session.installation()),null);session.save(s);}catch(Exception e){if("invalid_session".equals(e.getMessage()))session.clear();throw e;}}return s.getString("access_token");}
 JSONObject authenticated(String path,JSONObject body)throws Exception{return request(path,body,access());}
 void login(String email,String password,Result r){submit("login",()->{JSONObject j=request("auth/login",new JSONObject().put("email",email.trim()).put("password",password).put("installation_id",session.installation()),null);if(j.has("access_token")){session.save(j);revoking=false;}return new JSONObject().put("verification_required",j.optBoolean("verification_required",false)).put("signedIn",j.has("access_token"));},r);}
 void verify(String email,String code,Result r){submit("verify_email",()->{JSONObject j=request("auth/verify-email",new JSONObject().put("email",email.trim()).put("code",code.trim()).put("installation_id",session.installation()),null);session.save(j);revoking=false;return new JSONObject().put("signedIn",true);},r);}
 void check(Result r){submit("server_check",()->{JSONObject c=request("config",null,null);ApiContract.config(c);JSONObject out=new JSONObject().put("server",true).put("signedIn",signedIn());if(signedIn())out.put("entitlement",authenticated("entitlement",null));return out;},r);}
 void activate(Result r){submit("activate",()->authenticated("auth/activate",new JSONObject()),r);}
 void logout(Result r){revoking=true;submit("logout",()->{try{JSONObject s=session.read();if(s.has("refresh_token"))request("auth/logout",new JSONObject().put("refresh_token",s.getString("refresh_token")).put("installation_id",session.installation()),null);}finally{session.clear();}return new JSONObject().put("ok",true);},r);}
 void resolve(String id,Result r){submit("resolve",()->{if(id==null||!id.matches("[1-9][0-9]{0,23}"))throw new Exception("invalid_track");ApiContract.config(request("config",null,null));JSONObject j=authenticated("resolve?audio_formats=mp3,m4a&service=yandex&track_id="+id,null);if(j.optBoolean("found"))ApiContract.audio(j,System.currentTimeMillis());return j;},r);}
 interface AudioResult{void done(File file,String error);}
 void download(JSONObject descriptor,java.util.function.BooleanSupplier valid,AudioResult r){work.execute(()->{File f=null;String error=null;HttpsURLConnection c=null;try{if(!valid.getAsBoolean())throw new Exception("cancelled");String url=ApiContract.audio(descriptor,System.currentTimeMillis());c=(HttpsURLConnection)new URL(url).openConnection();c.setConnectTimeout(7000);c.setReadTimeout(7000);c.setInstanceFollowRedirects(false);int status=c.getResponseCode();if(status!=200)throw new Exception("audio_access_failed");long size=c.getContentLengthLong();if(size>31457280)throw new Exception("audio_too_large");long start=SystemClock.elapsedRealtime();f=File.createTempFile("replacement-",".audio",context.getCacheDir());try(InputStream in=c.getInputStream();FileOutputStream out=new FileOutputStream(f)){byte[] b=new byte[32768];int n,total=0;while((n=in.read(b))!=-1){total+=n;if(total>31457280||SystemClock.elapsedRealtime()-start>30000||!valid.getAsBoolean())throw new Exception("download_cancelled_or_limited");out.write(b,0,n);}if(total==0||(size>=0&&total!=size))throw new Exception("incomplete_audio");}LogStore.log("replacement_download",LogStore.map("bytes",f.length(),"elapsedMs",SystemClock.elapsedRealtime()-start));}catch(Exception e){if(f!=null)f.delete();f=null;error="audio_download_failed";String reason=e.getMessage();LogStore.log("replacement_download_failure",LogStore.map("reasonCode",reason!=null&&reason.matches("[a-z0-9_]{1,80}")?reason:"transport_or_file_error","type",e.getClass().getSimpleName()));}finally{if(c!=null)c.disconnect();}final File out=f;final String fail=error;main.post(()->r.done(out,fail));});}
}
