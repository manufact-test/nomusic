package pro.celikom.ownedplayer;

import android.content.Context;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Existing first-party CELIKOM server API. No unauthorized third-party APIs.
 * All requests serialized to protect refresh token rotation.
 */
final class OwnedApiClient {
    private static OwnedApiClient instance;
    static synchronized OwnedApiClient get(Context context){
        if(instance==null)instance=new OwnedApiClient(context);
        return instance;
    }
    final OwnedSessionStore store;
    private OwnedApiClient(Context context){
        store=new OwnedSessionStore(context);
    }
    synchronized boolean signedIn(){return store.current()!=null;}
    synchronized long accountEpoch(){return store.epoch();}
    private JSONObject fetch(String route,JSONObject body,String token,int maxBytes)throws Exception {
        if(!route.matches("[a-z0-9_/-]+([?][a-z0-9_=&-]+)?"))
            throw new Exception("unsafe_route");
        HttpURLConnection c=(HttpURLConnection)new URL(
                OwnedPlaybackContract.ORIGIN+"/api/v1/"+route).openConnection();
        try {
            c.setConnectTimeout(7000);c.setReadTimeout(8000);
            c.setInstanceFollowRedirects(false);
            c.setRequestProperty("Accept","application/json");
            c.setRequestProperty("Cache-Control","no-store");
            c.setRequestProperty("X-Celikom-Platform","android");
            c.setRequestProperty("X-Celikom-App-Version","0.1.0");
            if(token!=null)c.setRequestProperty("Authorization","Bearer "+token);
            if(body!=null){
                byte[] bytes=body.toString().getBytes(StandardCharsets.UTF_8);
                if(bytes.length>8192)throw new Exception("request_too_large");
                c.setRequestMethod("POST");c.setDoOutput(true);
                c.setRequestProperty("Content-Type","application/json");
                c.setFixedLengthStreamingMode(bytes.length);
                try(OutputStream out=c.getOutputStream()){out.write(bytes);}
            }
            int status=c.getResponseCode();
            if(status>=300&&status<400)throw new Exception("redirect_rejected");
            if(status==401)throw new Exception("unauthorized");
            if(status<200||status>=300)throw new Exception("request_failed");
            String type=c.getContentType();
            if(type==null||!type.toLowerCase(java.util.Locale.ROOT).startsWith("application/json"))
                throw new Exception("response_type");
            try(InputStream input=c.getInputStream();
                ByteArrayOutputStream output=new ByteArrayOutputStream()){
                byte[] buffer=new byte[4096];int n;
                while((n=input.read(buffer))!=-1){
                    if(output.size()+n>maxBytes)throw new Exception("response_too_large");
                    output.write(buffer,0,n);
                }
                return new JSONObject(output.toString(StandardCharsets.UTF_8));
            }
        } finally {c.disconnect();}
    }
    private String token()throws Exception{
        JSONObject session=store.current();
        if(session==null)throw new Exception("login_required");
        if(session.optLong("_access_until_ms")<System.currentTimeMillis()+30000){
            try {
                JSONObject refresh=fetch("auth/refresh",new JSONObject()
                    .put("refresh_token",session.getString("refresh_token"))
                    .put("installation_id",store.installation()),null,65536);
                store.save(refresh,false);
                session=store.current();
            }catch(Exception ex){
                store.clear();
                throw new Exception("session_expired");
            }
        }
        return session.getString("access_token");
    }
    synchronized JSONObject authenticated(String route,JSONObject body,int limit)throws Exception{
        String access=token();
        try {
            return fetch(route,body,access,limit);
        } catch(Exception ex) {
            if(!"unauthorized".equals(ex.getMessage()))throw ex;
            JSONObject previous=store.current();
            if(previous==null)throw new Exception("login_required");
            try {
                JSONObject next=fetch("auth/refresh",new JSONObject()
                    .put("refresh_token",previous.getString("refresh_token"))
                    .put("installation_id",store.installation()),null,65536);
                store.save(next,false);
                return fetch(route,body,store.current().getString("access_token"),limit);
            }catch(Exception fail){
                store.clear();
                throw new Exception("session_expired");
            }
        }
    }
    synchronized JSONObject login(String email,String password)throws Exception {
        if(store.current()!=null)store.clear();
        JSONObject result=fetch("auth/login",new JSONObject()
            .put("email",email.trim()).put("password",password)
            .put("installation_id",store.installation()),null,65536);
        if(result.optBoolean("verification_required"))return result;
        store.save(result,true);
        return result;
    }
    synchronized void verify(String email,String code)throws Exception{
        JSONObject result=fetch("auth/verify-email",new JSONObject()
            .put("email",email.trim()).put("code",code.trim())
            .put("installation_id",store.installation()),null,65536);
        store.save(result,true);
    }
    synchronized void logout(){
        JSONObject session=store.current();
        // Invalidate current account immediately; remote logout is best-effort.
        store.clear();
        if(session!=null)try{
            fetch("auth/logout",new JSONObject()
                .put("refresh_token",session.optString("refresh_token"))
                .put("installation_id",store.installation()),
                session.optString("access_token"),65536);
        }catch(Exception ignored){}
    }
    synchronized void healthy()throws Exception{
        JSONObject j=fetch("config",null,null,65536);
        if(j.optInt("api_version",-1)!=1||j.optBoolean("maintenance",true)||
                j.optJSONObject("features")==null||
                !j.getJSONObject("features").optBoolean("replacements",false)||
                (j.optJSONObject("incident")!=null&&j.getJSONObject("incident").optBoolean("active",false)))
            throw new Exception("service_unavailable");
    }
    synchronized boolean entitled()throws Exception{
        JSONObject result=authenticated("entitlement",null,65536);
        if(!(result.opt("allowed") instanceof Boolean))throw new Exception("bad_entitlement");
        return result.optBoolean("allowed",false);
    }
    synchronized boolean activate()throws Exception{
        JSONObject j=authenticated("auth/activate",new JSONObject(),65536);
        JSONObject entitlement=j.optJSONObject("entitlement");
        if(entitlement==null || !(entitlement.opt("allowed") instanceof Boolean))
            throw new Exception("bad_activation");
        return entitlement.optBoolean("allowed");
    }
    synchronized OwnedCatalogue catalogue()throws Exception{
        JSONObject j=authenticated("replacement-catalog",null,2_000_000);
        return OwnedCatalogue.parse(j,System.currentTimeMillis());
    }
    synchronized OwnedAudioGrant grant(String trackId)throws Exception{
        if(!OwnedPlaybackContract.validTrackId(trackId))throw new Exception("invalid_track_id");
        JSONObject j=authenticated("resolve?service=yandex&track_id="+trackId,null,65536);
        return OwnedAudioGrant.parse(j,System.currentTimeMillis());
    }
}
