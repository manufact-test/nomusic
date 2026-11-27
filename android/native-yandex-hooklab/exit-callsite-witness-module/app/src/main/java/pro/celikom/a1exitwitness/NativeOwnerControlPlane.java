package pro.celikom.a1exitwitness;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONObject;
import org.json.JSONException;
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
        "https://api.celikom.com";
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
                        || !enabled) {
                    NativeTrackIdBetaPolicy.mark(
                        NativeTrackIdBetaPolicy.Step.OWNER_PREFETCH_SUPERSEDED);
                    return;
                }
                JSONObject result=request(
                    "resolve?audio_formats=mp3,m4a&service=yandex&track_id="
                    +originalTrackId,null,access(owner));
                if(owner!=epoch.get() || latest!=latestPrefetch.get()
                        || !enabled) {
                    NativeTrackIdBetaPolicy.mark(
                        NativeTrackIdBetaPolicy.Step.OWNER_PREFETCH_SUPERSEDED);
                    return;
                }
                if(!approvedAudio(result))return;
                NativeGrantContract.Grant grant=readTrialGrant(originalTrackId,result);
                if(grant==null)return;
                // Server grant is never an original Yandex track/source proof.
                if(!validTrialGrant(originalTrackId,grant))return;
                if(!verifiedRange(grant.audioUrl,grant.mimeType))return;
                if(owner!=epoch.get() || latest!=latestPrefetch.get() || !enabled) {
                    NativeTrackIdBetaPolicy.mark(
                        NativeTrackIdBetaPolicy.Step.OWNER_PREFETCH_SUPERSEDED);
                    return;
                }
                warmGrant=new WarmGrant(owner,originalTrackId,grant,
                    System.currentTimeMillis());
            } catch(Exception failure) {
                markResolveFailure(failure);
            } finally {if(owner==epoch.get())warmingId=null;}
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
    // Only fixed outcome categories leave the owner control plane. Never
    // expose response text, credentials, token values, or exception messages.
    private static final class HttpRejected extends IOException {
        final int status;
        HttpRejected(int status) {super("http_rejected");this.status=status;}
    }
    private static final class SessionRequired extends IOException {
        SessionRequired() {super("login_required");}
    }
    private static boolean sessionRejected(Exception failure) {
        return failure instanceof SessionRequired
            || failure instanceof HttpRejected && ((HttpRejected)failure).status==401;
    }
    void start(Status callback) {
        action(callback,g->{
            if(!hasSession())return "login_required";
            JSONObject config;
            try {config=request("config",null,null);}
            catch(Exception failure) {return "config_failed";}
            if(config.optInt("api_version")!=1 || config.optBoolean("maintenance",true)
                    || config.optJSONObject("features")==null
                    || !config.getJSONObject("features").optBoolean("replacements")
                    || config.optJSONObject("incident")!=null
                        && config.optJSONObject("incident").optBoolean("active"))
                return "service_unavailable";
            String bearer;
            try {bearer=access(g);}
            catch(Exception failure) {
                return sessionRejected(failure)?"login_required":"refresh_failed";
            }
            JSONObject activated;
            try {activated=request("auth/activate",new JSONObject(),bearer);}
            catch(Exception failure) {
                return sessionRejected(failure)?"login_required":"activation_failed";
            }
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
        if(!refresh.matches("[a-f0-9]{64}"))throw new SessionRequired();
        if(stored.optLong("access_until_ms")<System.currentTimeMillis()+30000) {
            JSONObject newSession=request("auth/refresh",
                new JSONObject().put("refresh_token",refresh)
                    .put("installation_id",session.installation()),null);
            if(generation!=epoch.get())throw new IOException("owner_changed");
            session.save(newSession);
            stored=newSession;
        }
        String token=stored.optString("access_token");
        if(!token.matches("[a-f0-9]{64}"))throw new SessionRequired();
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
            if(status<200 || status>=300)throw new HttpRejected(status);
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
                && validTrialGrant(publisherTrackId,ready.grant)) {
            // Fast synchronous path: same signed, previously range-checked grant.
            offerExactBeta(generation,originalTrack,originalAlbum,originalSource,
                publisherTrackId,ready.grant);
            return;
        }
        network.execute(()->{
            if(!enabled || owner!=epoch.get() || bridge.generation()!=generation) {
                NativeTrackIdBetaPolicy.mark(
                    NativeTrackIdBetaPolicy.Step.OWNER_SOURCE_WINDOW_CLOSED);
                return;
            }
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
                        "resolve?audio_formats=mp3,m4a&service=yandex&track_id="
                            +publisherTrackId,null,access(owner));
                    if(!approvedAudio(response))return;
                    grant=readTrialGrant(publisherTrackId,response);
                    if(grant==null)return;
                }
                if(!validTrialGrant(publisherTrackId,grant))return;
                if(!verified && !verifiedRange(grant.audioUrl,grant.mimeType))return;
                if(!enabled || owner!=epoch.get()
                        || bridge.generation()!=generation) {
                    NativeTrackIdBetaPolicy.mark(
                        NativeTrackIdBetaPolicy.Step.OWNER_SOURCE_WINDOW_CLOSED);
                    return;
                }
                offerExactBeta(generation,originalTrack,originalAlbum,
                    originalSource,publisherTrackId,grant);
            } catch(Exception failure) {
                markResolveFailure(failure);
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
                        "resolve?audio_formats=mp3,m4a&service=yandex&track_id="
                        +originalTrackId,null,access(owner));
                    if(!approvedAudio(resolved))return;
                    grant=readGrant(resolved);
                }
                long now=System.currentTimeMillis();
                if(!NativeGrantContract.isAcceptable(grant,originalTrackId,
                        originalAlbumId,originalEditionId,originalDurationMs,ORIGIN,now)
                        || !prewarmed && !verifyAudioRange(grant.audioUrl,grant.mimeType))return;
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
    private static boolean approvedAudio(JSONObject response) {
        boolean found=response.optBoolean("found");
        boolean legacy=NativeTrackIdBetaPolicy.legacyAuthenticatedPositiveResolve(
            found,response.has("approved"),response.has("entitled"),
            response.optString("audio_url",""));
        boolean approved=response.optBoolean("approved",legacy);
        boolean entitled=response.optBoolean("entitled",legacy);
        String mime=response.optString("mime_type","");
        boolean supportedMime="audio/mpeg".equals(mime) || "audio/mp4".equals(mime);
        if(!found)NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_NOT_FOUND);
        else if(!approved)NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_NOT_APPROVED_FLAG);
        else if(!entitled)NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_NOT_ENTITLED);
        else if(!supportedMime)NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_UNSUPPORTED_MIME);
        else if("audio/mpeg".equals(mime))NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_MPEG);
        else NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_MP4);
        boolean ok=found && approved && entitled && supportedMime;
        NativeTrackIdBetaPolicy.mark(ok ? NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_APPROVED
            : NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_NOT_APPROVED);
        return ok;
    }
    private static boolean validTrialGrant(String id,NativeGrantContract.Grant grant) {
        boolean ok=NativeTrackIdBetaPolicy.signedTrialGrant(
            id,grant,ORIGIN,System.currentTimeMillis())!=null;
        if(ok)NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.OWNER_SIGNED_GRANT_VALID);
        else NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.OWNER_RESPONSE_INVALID);
        return ok;
    }
    private static boolean verifiedRange(String url,String mimeType) {
        boolean ok=verifyAudioRange(url,mimeType);
        NativeTrackIdBetaPolicy.mark(ok ? NativeTrackIdBetaPolicy.Step.OWNER_AUDIO_RANGE_VALID
            : NativeTrackIdBetaPolicy.Step.OWNER_AUDIO_RANGE_REJECTED);
        if(ok) {
            NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.SIGNED_AUDIO_READY);
            if("audio/mpeg".equals(mimeType))
                NativeTrackIdBetaPolicy.mark(NativeTrackIdBetaPolicy.Step.SIGNED_MPEG_READY);
        }
        return ok;
    }
    private void offerExactBeta(long generation,Object originalTrack,Object originalAlbum,
            Object originalSource,String publisherTrackId,NativeGrantContract.Grant grant) {
        if(!bridge.offerLimitedBetaSignedAudio(generation,originalTrack,
                originalAlbum,originalSource,publisherTrackId,grant,ORIGIN))
            NativeTrackIdBetaPolicy.mark(
                NativeTrackIdBetaPolicy.Step.OWNER_OFFER_REJECTED);
    }
    private static void markResolveFailure(Exception failure) {
        NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.OWNER_NETWORK_OR_RESPONSE_ERROR);
        // Only bounded failure categories, never exception messages / URLs.
        NativeTrackIdBetaPolicy.mark(failure instanceof JSONException
            ?NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_JSON_INVALID
            :failure instanceof IOException
                ?NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_TRANSPORT_ERROR
                :NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_CONSTRUCTION_ERROR);
    }
    private static NativeGrantContract.Grant readTrialGrant(
            String requestedTrackId,JSONObject response) throws JSONException {
        java.util.Map<String,Object> fields=new java.util.HashMap<>();
        java.util.Iterator<String> keys=response.keys();
        while(keys.hasNext()) {
            String key=keys.next();
            Object value=response.get(key);
            fields.put(key,value==JSONObject.NULL?null:value);
        }
        NativeGrantContract.Grant grant=NativeTrackIdBetaPolicy.parseTrialResolve(
            requestedTrackId,fields,ORIGIN);
        if(grant==null)NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.OWNER_RESOLVE_JSON_INVALID);
        else if(!response.has("track_id"))NativeTrackIdBetaPolicy.mark(
            NativeTrackIdBetaPolicy.Step.OWNER_LEGACY_REQUEST_BOUND);
        return grant;
    }
    private static NativeGrantContract.Grant readGrant(JSONObject resolved)
            throws Exception {
        // Never fabricate approval from an explicit false/null response.
        // In deployed v1, both fields are absent and the authenticated
        // session-bound signed ticket is the equivalent positive evidence.
        boolean legacy=NativeTrackIdBetaPolicy.legacyAuthenticatedPositiveResolve(
            resolved.optBoolean("found"),resolved.has("approved"),
            resolved.has("entitled"),resolved.optString("audio_url",""));
        boolean approved=legacy || resolved.getBoolean("approved");
        boolean entitled=legacy || resolved.getBoolean("entitled");
        URI url=new URI(ORIGIN).resolve(resolved.getString("audio_url"));
        return new NativeGrantContract.Grant(
            resolved.getString("track_id"),resolved.optString("album_id",""),
            resolved.optString("edition_id",""),resolved.getLong("duration_ms"),
            resolved.getLong("version"),approved,
            entitled,url.toString(),
            Math.multiplyExact(resolved.getLong("expires_at"),1000),
            resolved.getString("mime_type"));
    }
    private static boolean verifyAudioRange(String url,String mimeType) {
        if(!"audio/mpeg".equals(mimeType) && !"audio/mp4".equals(mimeType))return false;
        HttpsURLConnection c=null;
        try {
            c=(HttpsURLConnection)new URL(url).openConnection();
            c.setConnectTimeout(2200); c.setReadTimeout(2200);
            c.setInstanceFollowRedirects(false); c.setUseCaches(false);
            c.setRequestProperty("Range","bytes=0-4095");
            c.setRequestProperty("Accept","audio/mpeg, audio/mp4");
            if(c.getResponseCode()!=206 || !mimeType.equals(c.getContentType()))return false;
            String range=c.getHeaderField("Content-Range");
            if(range==null || !range.matches("bytes 0-[0-9]+/[1-9][0-9]*"))return false;
            try(InputStream in=c.getInputStream()) {
                byte[] head=new byte[12]; int got=0;
                while(got<head.length) {int n=in.read(head,got,head.length-got);if(n<0)return false;got+=n;}
                if("audio/mpeg".equals(mimeType))
                    return head[0]=='I' && head[1]=='D' && head[2]=='3'
                        || (head[0]&255)==255 && ((head[1]&255)&224)==224;
                return head[4]=='f' && head[5]=='t' && head[6]=='y' && head[7]=='p';
            }
        } catch(Exception ignored) {return false;}
        finally {if(c!=null)c.disconnect();}
    }
}
