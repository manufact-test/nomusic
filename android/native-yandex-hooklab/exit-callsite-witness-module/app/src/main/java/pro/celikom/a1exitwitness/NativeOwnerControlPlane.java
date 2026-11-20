package pro.celikom.a1exitwitness;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONObject;
import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.IOException;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicLong;
import javax.net.ssl.HttpsURLConnection;

/**
 * CELIKOM owner account and signed-grant control plane INSIDE the independent
 * CELIKOM Yandex clone. No vendor credentials, no second audio player.
 *
 * Uses existing CELIKOM server contracts and clone-private AndroidKeyStore.
 * Work stays off the main thread. Every Next/Stop invalidates pending results.
 * A signed URL is never an original Yandex album/edition proof: those must
 * arrive independently from the same original source BEFORE native prepare.
 */
final class NativeOwnerControlPlane {
    interface Status { void done(String code); }
    private static final String ORIGIN =
        "https://darkred-camel-588676.hostingersite.com";
    private final NativeOwnerSession session;
    private final NativeEarlySourceLifecycleBridge bridge;
    private final ExecutorService network=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private final AtomicLong epoch=new AtomicLong();
    private final AtomicLong latestPrefetch=new AtomicLong();
    private volatile boolean enabled;
    private static final class WarmGrant {
        final long owner,atMs;
        final String track;
        final NativeGrantContract.Grant grant;
        WarmGrant(long owner,String track,NativeGrantContract.Grant grant,long atMs) {
            this.owner=owner;this.track=track;this.grant=grant;this.atMs=atMs;
        }
    }
    // One short-lived, owner-session-only speculative result. This is NEVER
    // native source identity and can never bypass exact original album/edition.
    private volatile WarmGrant warmGrant;
    private volatile String warmingId;
    void warmFromPublisherTrackId(String originalTrackId) {
        if(!enabled || !NativeTrackIdBetaPolicy.allows(originalTrackId))return;
        final long owner=epoch.get();
        WarmGrant current=warmGrant;
        if(current!=null && current.owner==owner
                && current.track.equals(originalTrackId)
                && System.currentTimeMillis()-current.atMs<30000)return;
        if(originalTrackId.equals(warmingId))return;
        warmingId=originalTrackId;
        NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.PREFETCH_STARTED);
        final long latest=latestPrefetch.incrementAndGet();
        network.execute(()->{
            try {
                if(owner!=epoch.get() || latest!=latestPrefetch.get()
                        || !enabled)return;
                JSONObject result=request(
                    "resolve?audio_formats=mp3&service=yandex&track_id="
                    +originalTrackId,null,access(owner));
                if(owner!=epoch.get() || latest!=latestPrefetch.get()
                        || !enabled)return;
                if(result.optBoolean("found") && result.optBoolean("approved")
                        && result.optBoolean("entitled")
                        && "audio/mpeg".equals(result.optString("mime_type"))) {
                    NativeGrantContract.Grant grant=readGrant(result);
                    // This preflight checks only CELIKOM-issued signed audio,
                    // NEVER the identity of the currently playing Yandex source.
                    if(NativeTrackIdBetaPolicy.signedTrialGrant(
                            originalTrackId,grant,ORIGIN,System.currentTimeMillis())
                            !=null
                            && verifyMpegRange(grant.audioUrl)
                            && owner==epoch.get() && latest==latestPrefetch.get())
                        {
                            warmGrant=new WarmGrant(owner,originalTrackId,grant,
                                System.currentTimeMillis());
                            NativeTrackIdBetaPolicy.mark(
                                NativeTrackIdBetaPolicy.Step.SIGNED_MPEG_READY);
                        }
                }
            } catch(Exception ignored) { }
            finally {if(owner==epoch.get())warmingId=null;}
        });
    }
    NativeOwnerControlPlane(Context context,NativeEarlySourceLifecycleBridge bridge) {
        if(context==null || bridge==null)throw new IllegalArgumentException("OWNER_REQUIRED");
        this.session=new NativeOwnerSession(context);
        this.bridge=bridge;
    }
    boolean hasSession() {
        return !session.read().optString("refresh_token").isEmpty();
    }
    boolean enabled() {return enabled;}
    private void reply(Status callback,String code,long generation) {
        if(callback==null)return;
        main.post(()->{if(epoch.get()==generation)callback.done(code);});
    }
    private void action(Status callback,OwnerOperation operation) {
        final long generation=epoch.incrementAndGet();
        network.execute(()->{
            String result;
            try { result=operation.run(generation); }
            catch(Exception failure) {result="network_or_auth_error";}
            reply(callback,result,generation);
        });
    }
    interface OwnerOperation {String run(long generation) throws Exception;}
    void login(String email,String password,Status callback) {
        if(email==null || password==null || email.trim().isEmpty()
                || password.isEmpty()) {if(callback!=null)callback.done("login_required");return;}
        // An explicit owner login invalidates any earlier audio permission.
        stop();
        action(callback,g->{
            JSONObject body=new JSONObject().put("email",email.trim())
                .put("password",password).put("installation_id",session.installation());
            JSONObject response=request("auth/login",body,null);
            if(g!=epoch.get())return "cancelled";
            if(!response.optString("access_token").isEmpty()) {
                session.save(response);
                return "signed_in";
            }
            return response.optBoolean("verification_required")
                ?"verification_required":"login_required";
        });
    }
    void verify(String email,String code,Status callback) {
        if(email==null || email.trim().isEmpty() || code==null || code.trim().isEmpty())
            {if(callback!=null)callback.done("verification_required");return;}
        stop();
        action(callback,g->{
            JSONObject response=request("auth/verify-email",
                new JSONObject().put("email",email.trim()).put("code",code.trim())
                    .put("installation_id",session.installation()),null);
            if(g!=epoch.get())return "cancelled";
            session.save(response);
            return "signed_in";
        });
    }
    void start(Status callback) {
        action(callback,g->{
            if(!hasSession())return "login_required";
            JSONObject config=request("config",null,null);
            if(config.optInt("api_version")!=1 || config.optBoolean("maintenance",true)
                    || config.optJSONObject("features")==null
                    || !config.getJSONObject("features").optBoolean("replacements")
                    || config.optJSONObject("incident")!=null
                        && config.optJSONObject("incident").optBoolean("active"))
                return "service_unavailable";
            String bearer=access(g);
            JSONObject activated=request("auth/activate",new JSONObject(),bearer);
            JSONObject entitlement=activated.optJSONObject("entitlement");
            if(entitlement==null || !entitlement.optBoolean("allowed"))
                return "not_entitled";
            // The owner lifecycle is activated only after a current authorized
            // server response, never merely because a token was saved locally.
            main.post(()->{
                if(g==epoch.get() && !enabled) {
                    bridge.startForAuthenticatedOwner();
                    enabled=true;
                    NativeTrackIdBetaPolicy.mark(
                        NativeTrackIdBetaPolicy.Step.OWNER_ENABLED);
                }
            });
            return "enabled";
        });
    }
    void stop() {
        epoch.incrementAndGet();
        warmGrant=null;
        warmingId=null;
        latestPrefetch.incrementAndGet();
        enabled=false;
        bridge.stopForAuthenticatedOwner();
        // Current native decoder/source is not rewritten mid-song.
    }
    private String access(long generation) throws Exception {
        if(generation!=epoch.get())throw new IOException("owner_changed");
        JSONObject stored=session.read();
        String refresh=stored.optString("refresh_token");
        if(!refresh.matches("[a-f0-9]{64}"))throw new IOException("login_required");
        if(stored.optLong("access_until_ms")<System.currentTimeMillis()+30000) {
            JSONObject newSession=request("auth/refresh",
                new JSONObject().put("refresh_token",refresh)
                    .put("installation_id",session.installation()),null);
            if(generation!=epoch.get())throw new IOException("owner_changed");
            session.save(newSession);
            stored=newSession;
        }
        String token=stored.optString("access_token");
        if(!token.matches("[a-f0-9]{64}"))throw new IOException("login_required");
        return token;
    }
    private JSONObject request(String path,JSONObject body,String bearer) throws Exception {
        HttpsURLConnection c=(HttpsURLConnection)new URL(
            ORIGIN+"/api/v1/"+path).openConnection();
        try {
            c.setConnectTimeout(3000);
            c.setReadTimeout(3500);
            c.setInstanceFollowRedirects(false);
            c.setUseCaches(false);
            c.setRequestProperty("Accept","application/json");
            c.setRequestProperty("Cache-Control","no-store");
            if(bearer!=null)c.setRequestProperty("Authorization","Bearer "+bearer);
            if(body!=null) {
                byte[] payload=body.toString().getBytes(StandardCharsets.UTF_8);
                if(payload.length>8192)throw new IOException("request_too_large");
                c.setRequestMethod("POST");
                c.setDoOutput(true);
                c.setRequestProperty("Content-Type","application/json");
                c.setFixedLengthStreamingMode(payload.length);
                try(java.io.OutputStream out=c.getOutputStream()){out.write(payload);}
            }
            int status=c.getResponseCode();
            if(status<200 || status>=300)throw new IOException("http_rejected");
            String mime=c.getContentType();
            if(mime==null || !mime.toLowerCase(java.util.Locale.ROOT)
                    .startsWith("application/json"))throw new IOException("not_json");
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            try(InputStream in=c.getInputStream()) {
                byte[] part=new byte[2048];
                int n;
                while((n=in.read(part))!=-1){
                    if(bytes.size()+n>65536)throw new IOException("response_too_large");
                    bytes.write(part,0,n);
                }
            }
            return new JSONObject(new String(bytes.toByteArray(),StandardCharsets.UTF_8));
        } finally {c.disconnect();}
    }
    /**
     * Explicit owner-only trackId BETA for the IDs allowlisted by
     * NativeTrackIdBetaPolicy. The signed ID is already bound to THIS original Track/Album/source Java object lineage.
     * CELIKOM server album/edition are not publisher identity evidence.
     */
    void requestForTrackIdBeta(long generation,Object originalTrack,
            Object originalAlbum,Object originalSource,String publisherTrackId) {
        if(!enabled || !NativeTrackIdBetaPolicy.allows(publisherTrackId))return;
        NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_REQUEST);
        final long owner=epoch.get();
        WarmGrant ready=warmGrant;
        long now=System.currentTimeMillis();
        if(ready!=null && ready.owner==owner
                && publisherTrackId.equals(ready.track)
                && now>=ready.atMs && now-ready.atMs<30000
                && NativeTrackIdBetaPolicy.signedTrialGrant(
                    publisherTrackId,ready.grant,ORIGIN,now)!=null) {
            // Fast synchronous path: network, HTTP206 and MPEG sync were
            // verified already by the separate background prefetch lane.
            bridge.offerLimitedBetaSignedAudio(generation,originalTrack,
                originalAlbum,originalSource,publisherTrackId,ready.grant,ORIGIN);
            return;
        }
        network.execute(()->{
            if(!enabled || owner!=epoch.get() || bridge.generation()!=generation)
                return;
            try {
                WarmGrant warmed=warmGrant;
                NativeGrantContract.Grant grant;
                boolean verified=warmed!=null && warmed.owner==owner
                    && publisherTrackId.equals(warmed.track)
                    && System.currentTimeMillis()>=warmed.atMs
                    && System.currentTimeMillis()-warmed.atMs<30000;
                if(verified) {
                    grant=warmed.grant;
                } else {
                    JSONObject response=request(
                        "resolve?audio_formats=mp3&service=yandex&track_id="
                            +publisherTrackId,null,access(owner));
                    if(!response.optBoolean("found")
                            || !response.optBoolean("approved")
                            || !response.optBoolean("entitled")
                            || !"audio/mpeg".equals(response.optString("mime_type")))
                        return;
                    grant=readGrant(response);
                }
                if(NativeTrackIdBetaPolicy.signedTrialGrant(
                        publisherTrackId,grant,ORIGIN,System.currentTimeMillis())
                        ==null || !verified && !verifyMpegRange(grant.audioUrl))
                    return;
                if(!enabled || owner!=epoch.get()
                        || bridge.generation()!=generation)return;
                bridge.offerLimitedBetaSignedAudio(generation,originalTrack,
                    originalAlbum,originalSource,publisherTrackId,grant,ORIGIN);
            } catch(Exception ignored) {
                // No delayed fallback can replace an already prepared track.
            }
        });
    }

    /**
     * Only the EXISTING certified triple/source caller may invoke this method.
     * An arbitrary server album/edition never certifies the Yandex source.
     */
    void requestForCertifiedSource(long generation,Object originalTrack,
            Object originalAlbum,Object originalSource,String originalTrackId,
            String originalAlbumId,String originalEditionId,long originalDurationMs) {
        if(!enabled || !NativeGrantContract.isExactTrackId(originalTrackId)
                || originalAlbumId==null || originalEditionId==null
                || originalDurationMs<=0)return;
        final long owner=epoch.get();
        network.execute(()->{
            try {
                if(!enabled || owner!=epoch.get()
                        || bridge.generation()!=generation)return;
                WarmGrant preflight=warmGrant;
                boolean prewarmed=preflight!=null && preflight.owner==owner
                    && preflight.track.equals(originalTrackId)
                    && System.currentTimeMillis()-preflight.atMs<30000;
                NativeGrantContract.Grant grant;
                if(prewarmed) {
                    grant=preflight.grant;
                } else {
                    JSONObject resolved=request(
                        "resolve?audio_formats=mp3&service=yandex&track_id="
                        +originalTrackId,null,access(owner));
                    if(!resolved.optBoolean("found")
                            || !resolved.optBoolean("approved")
                            || !resolved.optBoolean("entitled")
                            || !"audio/mpeg".equals(resolved.optString("mime_type")))
                        return;
                    grant=readGrant(resolved);
                }
                long now=System.currentTimeMillis();
                if(!NativeGrantContract.isAcceptable(grant,originalTrackId,
                        originalAlbumId,originalEditionId,originalDurationMs,ORIGIN,now)
                        || !prewarmed && !verifyMpegRange(grant.audioUrl))return;
                if(!enabled || owner!=epoch.get() || bridge.generation()!=generation
                        || !bridge.isSuccessfulOriginalSource(generation,originalTrack,
                            originalAlbum,originalSource))return;
                NativeSourceGate.Candidate candidate=new NativeSourceGate.Candidate(
                    originalTrackId,originalAlbumId,originalEditionId,
                    true,true,true,true,true,true);
                bridge.offerAuthenticatedApprovedAudio(generation,originalTrack,
                    originalAlbum,originalSource,candidate,grant,ORIGIN,
                    originalDurationMs);
            } catch(Exception ignored) {
                // Any failure => original. Never log signed URL or credentials.
            }
        });
    }
    private static NativeGrantContract.Grant readGrant(JSONObject resolved)
            throws Exception {
        URI url=new URI(ORIGIN).resolve(resolved.getString("audio_url"));
        return new NativeGrantContract.Grant(
            resolved.getString("track_id"),resolved.optString("album_id",""),
            resolved.optString("edition_id",""),resolved.getLong("duration_ms"),
            resolved.getLong("version"),resolved.getBoolean("approved"),
            resolved.getBoolean("entitled"),url.toString(),
            Math.multiplyExact(resolved.getLong("expires_at"),1000),
            resolved.getString("mime_type"));
    }
    private static boolean verifyMpegRange(String url) {
        HttpsURLConnection c=null;
        try {
            c=(HttpsURLConnection)new URL(url).openConnection();
            c.setConnectTimeout(2200);
            c.setReadTimeout(2200);
            c.setInstanceFollowRedirects(false);
            c.setUseCaches(false);
            c.setRequestProperty("Range","bytes=0-4095");
            c.setRequestProperty("Accept","audio/mpeg");
            if(c.getResponseCode()!=206 || !"audio/mpeg".equals(c.getContentType()))
                return false;
            String range=c.getHeaderField("Content-Range");
            if(range==null || !range.matches("bytes 0-[0-9]+/[1-9][0-9]*"))
                return false;
            try(InputStream in=c.getInputStream()) {
                byte[] head=new byte[3];
                int got=0;
                while(got<3) {
                    int n=in.read(head,got,3-got);
                    if(n<0)return false;
                    got+=n;
                }
                return head[0]=='I' && head[1]=='D' && head[2]=='3'
                    || (head[0]&255)==255 && ((head[1]&255)&224)==224;
            }
        } catch(Exception ignored) {return false;}
        finally {if(c!=null)c.disconnect();}
    }
}
