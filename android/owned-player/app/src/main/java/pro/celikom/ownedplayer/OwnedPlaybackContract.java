package pro.celikom.ownedplayer;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.HashMap;
import java.util.Map;

/** Pure-Java fail-closed source and entitlement gate. No vendor auth or playback. */
public final class OwnedPlaybackContract {
    public static final String ORIGIN = "https://darkred-camel-588676.hostingersite.com";
    private OwnedPlaybackContract() {}

    public static boolean validTrackId(String value) {
        return value != null && value.matches("[1-9][0-9]{0,19}");
    }

    public static boolean activeAccess(boolean explicitAllowed, long confirmedAtMs,
                                       long nowMs, long leaseMs) {
        return explicitAllowed && confirmedAtMs > 0 && nowMs >= confirmedAtMs
                && leaseMs > 0 && leaseMs <= 15000
                && nowMs - confirmedAtMs <= leaseMs;
    }

    public static boolean validSignedAudioUrl(String input,long replacementId,
                                               long expiresAtMs,long nowMs) {
        if(input == null || input.length() > 2048 || replacementId <= 0 ||
                expiresAtMs < nowMs + 5000 || expiresAtMs - nowMs > 1800000)
            return false;
        try {
            URI base = new URI(ORIGIN);
            URI url = base.resolve(input);
            if(!"https".equals(url.getScheme()) || url.getHost() == null ||
                    !base.getHost().equalsIgnoreCase(url.getHost()) ||
                    url.getPort() != -1 || url.getUserInfo() != null ||
                    url.getRawFragment() != null || url.getRawQuery() == null ||
                    !url.getRawPath().equals("/api/v1/audio/" + replacementId))
                return false;
            Map<String,String> query=new HashMap<>();
            for(String part:url.getRawQuery().split("&",-1)) {
                String[] kv=part.split("=", -1);
                if(kv.length!=2 || query.putIfAbsent(kv[0],kv[1])!=null)
                    return false;
            }
            if(!query.keySet().equals(java.util.Set.of("token","expires")) &&
                    !query.keySet().equals(java.util.Set.of("token","expires","sid")))
                return false;
            String token=query.get("token");
            String expiry=query.get("expires");
            return token != null && token.matches("[a-f0-9]{64}") &&
                    String.valueOf(expiresAtMs/1000).equals(expiry) &&
                    expiresAtMs%1000 == 0 &&
                    (!query.containsKey("sid") ||
                            query.get("sid").matches("[1-9][0-9]{0,17}"));
        } catch(URISyntaxException | IllegalArgumentException ex) {
            return false;
        }
    }
}
