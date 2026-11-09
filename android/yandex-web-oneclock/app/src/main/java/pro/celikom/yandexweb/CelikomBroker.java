package pro.celikom.yandexweb;

import android.content.Context;
import android.media.MediaMetadataRetriever;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONObject;

import javax.net.ssl.HttpsURLConnection;
import java.io.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/**
 * CELIKOM-only broker. No Yandex cookies/credentials/tokens are read here.
 * All API authorization is native + encrypted at rest, never reachable from page JS.
 */
final class CelikomBroker {
    interface Listener {
        void status(String safeText);
        void ready(String trackId,String albumId,long durationMs);
    }
    static final class Asset {
        final String id, albumId;
        final long durationMs;
        final File file;
        Asset(String id,String albumId,long durationMs,File file) {
            this.id=id;this.albumId=albumId;this.durationMs=durationMs;this.file=file;
        }
    }
    private final SecureSession session;
    private final Context context;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ThreadPoolExecutor io = new ThreadPoolExecutor(1,1,0,
        TimeUnit.MILLISECONDS,new LinkedBlockingQueue<>(8));
    private final Map<String, Asset> ready = new ConcurrentHashMap<>();
    private final Set<String> pending = ConcurrentHashMap.newKeySet();
    private final Listener listener;
    private final File cacheDir;
    private volatile boolean enabled = false;
    private volatile int generation = 0;

    CelikomBroker(Context ctx,Listener callback) {
        context=ctx.getApplicationContext();
        session=new SecureSession(context);
        cacheDir=new File(context.getCacheDir(),"oneclock-approved");
        if(!cacheDir.exists()&&!cacheDir.mkdirs())throw new IllegalStateException("cache unavailable");
        listener=callback;
    }
    void setEnabled(boolean value) { enabled=value; if(value) report("Подмена включена: только готовые версии"); }
    boolean isEnabled() {return enabled;}
    boolean signedIn() {return !session.read().optString("refresh_token","").isEmpty();}
    private void report(String status) { main.post(()->listener.status(status)); }
    private void sendReady(Asset a) { main.post(()->listener.ready(a.id,a.albumId,a.durationMs)); }

    void login(String email,String password) {
        if(email==null||password==null||email.trim().isEmpty()||password.isEmpty()) {
            report("Введите почту и пароль CELIKOM"); return;
        }
        final String mail=email.trim();
        schedule(()->{
            try {
                JSONObject payload=new JSONObject()
                    .put("email",mail).put("password",password).put("installation_id",session.installation());
                JSONObject result=request("auth/login",payload,null);
                if(result.optBoolean("verification_required",false)) {
                    report("Требуется код подтверждения CELIKOM");return;
                }
                session.save(result);
                int revision=++generation;
                if(revision==generation) {
                    ready.clear();
                    report("CELIKOM: вход выполнен");
                }
            }catch(Exception e){report("Вход CELIKOM не выполнен");}
        });
    }

    void verify(String email,String code) {
        if(email==null||code==null||code.trim().isEmpty()) {report("Введите код");return;}
        schedule(()->{
            try {
                JSONObject result=request("auth/verify-email",new JSONObject()
                    .put("email",email.trim()).put("code",code.trim())
                    .put("installation_id",session.installation()),null);
                session.save(result);++generation;
                report("CELIKOM: вход подтверждён");
            } catch(Exception e){report("Код CELIKOM не подтверждён");}
        });
    }

    void logout() {
        enabled=false;
        ++generation;
        ready.clear();
        pending.clear();
        session.clear();
        report("CELIKOM: выход выполнен");
        schedule(()->{
            File[] files=cacheDir.listFiles();
            if(files!=null) for(File f:files) if(f.isFile()) f.delete();
        });
    }

    void prefetch(String id,String albumId,long sourceDurationMs) {
        if(!enabled||!signedIn()||!numeric(id)||!numeric(albumId)||
            sourceDurationMs<=0||sourceDurationMs>86400000) return;
        String key=id+":"+albumId;
        Asset asset=ready.get(key);
        if(asset!=null&&asset.file.isFile()&&Math.abs(asset.durationMs-sourceDurationMs)<=1500) {
            sendReady(asset);return;
        }
        if(!pending.add(key))return;
        final int lease=generation;
        schedule(()->{
            try {
                if(!enabled||lease!=generation) return;
                String access=access();
                JSONObject grant=request("auth/activate",new JSONObject(),access)
                    .optJSONObject("entitlement");
                if(grant==null||!grant.optBoolean("allowed",false)) {
                    report("CELIKOM: подписка или пробный период не активны");return;
                }
                JSONObject data=request("resolve?audio_formats=mp3&service=yandex&track_id="+id,null,access);
                if(!data.optBoolean("found",false))return;
                if(!"audio/mpeg".equals(data.optString("mime_type","audio/mpeg")))return;
                String signed=ApiContract.audio(data,System.currentTimeMillis());
                long descriptorMs=ApiContract.integer(data,"duration_ms");
                if(Math.abs(descriptorMs-sourceDurationMs)>1500)return;
                File tmp=File.createTempFile("dl-",".part",cacheDir);
                try {
                    final String media=signed;
                    AudioTransfer.copy(tmp,()->{
                        HttpsURLConnection c=(HttpsURLConnection)new URL(media).openConnection();
                        c.setInstanceFollowRedirects(false);
                        return c;
                    },()->enabled&&lease==generation,System::currentTimeMillis,
                    (attempt,bytes,reason)->{});
                    if(!enabled||lease!=generation) return;
                    if(tmp.length()<1024||tmp.length()>AudioTransfer.MAX_BYTES)return;
                    MediaMetadataRetriever retriever=new MediaMetadataRetriever();
                    long measuredMs;
                    try {
                        retriever.setDataSource(tmp.getAbsolutePath());
                        String value=retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION);
                        measuredMs=value==null?0:Long.parseLong(value);
                    }finally {try{retriever.release();}catch(IOException ignored){}}
                    if(!ApiContract.durations(sourceDurationMs,descriptorMs,measuredMs))return;
                    File destination=new File(cacheDir,"track-"+id+"-"+albumId+".mp3");
                    if(!tmp.renameTo(destination))return;
                    if(!enabled||lease!=generation) {destination.delete();return;}
                    Asset next=new Asset(id,albumId,measuredMs,destination);
                    ready.put(key,next);
                    trimCache();
                    sendReady(next);
                }finally{tmp.delete();}
            }catch(Exception e){report("CELIKOM: загрузка версии не удалась");}
            finally{pending.remove(key);}
        });
    }
    Asset asset(String id,String albumId) {
        if(!numeric(id)||!numeric(albumId))return null;
        Asset a=ready.get(id+":"+albumId);
        return a!=null&&a.file.isFile()?a:null;
    }
    void announceReady() {
        for(Asset a:ready.values())if(a.file.isFile())sendReady(a);
    }

    void discardAll() {
        ready.clear();
        pending.clear();
        ++generation;
    }
    private void trimCache() {
        File[] files=cacheDir.listFiles(File::isFile);
        if(files==null)return;
        Arrays.sort(files,Comparator.comparingLong(File::lastModified));
        long total=0;
        for(File f:files)total+=f.length();
        for(File f:files){
            if(total<=64L*1024*1024)break;
            if(!f.getName().startsWith("track-"))continue;
            long bytes=f.length();
            if(f.delete())total-=bytes;
        }
        ready.entrySet().removeIf(e->!e.getValue().file.isFile());
    }
    private void schedule(Runnable task) {
        try {io.execute(task);}catch(RejectedExecutionException ignored){report("CELIKOM занят: пропуск запроса");}
    }
    private static boolean numeric(String id) {return id!=null&&id.matches("[1-9][0-9]{0,23}");}

    private synchronized String access() throws Exception {
        JSONObject s=session.read();
        if(s.optString("refresh_token").isEmpty())throw new IOException("login_required");
        if(s.optLong("access_until_ms")<System.currentTimeMillis()+30000){
            JSONObject updated=request("auth/refresh",new JSONObject()
                .put("refresh_token",s.getString("refresh_token"))
                .put("installation_id",session.installation()),null);
            session.save(updated);
            s=updated;
        }
        return s.getString("access_token");
    }

    private static JSONObject request(String path, JSONObject body, String access) throws Exception {
        if(path==null||!path.matches("[a-z0-9_/?=,&.-]{1,180}"))throw new IOException("invalid_path");
        HttpsURLConnection c=(HttpsURLConnection)new URL(ApiContract.ORIGIN+"/api/v1/"+path).openConnection();
        try {
            c.setConnectTimeout(7000);
            c.setReadTimeout(9000);
            c.setInstanceFollowRedirects(false);
            c.setRequestProperty("Accept","application/json");
            c.setRequestProperty("Cache-Control","no-store");
            if(access!=null)c.setRequestProperty("Authorization","Bearer "+access);
            if(body!=null){
                byte[] data=body.toString().getBytes(StandardCharsets.UTF_8);
                if(data.length>8192)throw new IOException("payload_too_large");
                c.setRequestMethod("POST");
                c.setDoOutput(true);
                c.setRequestProperty("Content-Type","application/json");
                c.setFixedLengthStreamingMode(data.length);
                try(OutputStream out=c.getOutputStream()){out.write(data);}
            }
            int code=c.getResponseCode();
            if(code>=300&&code<400)throw new IOException("redirect_rejected");
            String type=c.getContentType();
            if(type==null||!type.startsWith("application/json"))throw new IOException("invalid_mime");
            try(InputStream in=code>=200&&code<300?c.getInputStream():c.getErrorStream()){
                if(in==null)throw new IOException("empty_response");
                ByteArrayOutputStream out=new ByteArrayOutputStream();
                byte[] buffer=new byte[4096];int n;
                while((n=in.read(buffer))!=-1) {
                    if(out.size()+n>65536)throw new IOException("response_large");
                    out.write(buffer,0,n);
                }
                JSONObject response=new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));
                if(code<200||code>=300)throw new IOException("api_error");
                return response;
            }
        }finally{c.disconnect();}
    }
}
