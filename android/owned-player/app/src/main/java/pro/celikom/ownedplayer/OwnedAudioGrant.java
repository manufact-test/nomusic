package pro.celikom.ownedplayer;

import org.json.JSONObject;
import java.net.URI;

/** An API signed URL is not a bearer or entitlement; re-check both separately. */
public final class OwnedAudioGrant {
    public final String url;
    public final long expiresAtMs, durationMs, replacementId;
    private OwnedAudioGrant(String url,long expiry,long duration,long replacement){
        this.url=url;expiresAtMs=expiry;durationMs=duration;replacementId=replacement;
    }
    public static OwnedAudioGrant parse(JSONObject data,long nowMs)throws Exception{
        if(data==null || !data.optBoolean("found",false))
            throw new Exception("replacement_not_found");
        long id=data.optLong("replacement_id",-1);
        long expiry=data.optLong("expires_at",-1)*1000L;
        long duration=data.optLong("duration_ms",-1);
        if(id<=0 || data.optInt("version",-1)<1 ||
                duration<1000 || duration>86400000 ||
                expiry<=nowMs+5000 || expiry-nowMs>1800000)
            throw new Exception("invalid_grant");
        String mime=data.optString("mime_type","audio/mpeg");
        if(!"audio/mpeg".equals(mime)&&!"audio/mp4".equals(mime)&&
                !"audio/wav".equals(mime)&&!"audio/x-wav".equals(mime))
            throw new Exception("unsupported_audio");
        String candidate=data.optString("audio_url","");
        if(!OwnedPlaybackContract.validSignedAudioUrl(candidate,id,expiry,nowMs))
            throw new Exception("invalid_audio_url");
        URI resolved=new URI(OwnedPlaybackContract.ORIGIN).resolve(candidate);
        return new OwnedAudioGrant(resolved.toString(),expiry,duration,id);
    }
}
