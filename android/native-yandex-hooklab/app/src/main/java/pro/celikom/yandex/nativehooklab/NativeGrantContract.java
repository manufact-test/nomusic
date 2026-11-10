package pro.celikom.yandex.nativehooklab;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Android-side, pure Java parity with the Windows W15 signed-source contract.
 * No network request, credential, URL rewrite, native decoder, or logging.
 * Exact token and session verification is STILL done by the CELIKOM server.
 *
 * An approved response passing this STRUCTURAL gate does NOT prove that
 * native Android Yandex can decode or play it.
 */
public final class NativeGrantContract {
    private static final Pattern TRACK = Pattern.compile("[1-9][0-9]{0,23}");
    private static final Pattern RESOURCE_PATH = Pattern.compile("/api/v1/audio/[1-9][0-9]{0,17}");
    private static final Pattern TOKEN = Pattern.compile("[a-f0-9]{64}");
    private static final Pattern EXPIRES = Pattern.compile("[0-9]{9,12}");
    private static final Pattern SID = Pattern.compile("[1-9][0-9]{0,17}");
    private static final long MIN_TTL_MS = 5000L;
    private static final long MAX_TTL_MS = 30 * 60 * 1000L;

    private NativeGrantContract() {}

    /** From a previously authorized CELIKOM bridge, never from Yandex data. */
    public static final class Grant {
        public final String trackId;
        public final boolean approved;
        public final boolean entitled;
        public final String audioUrl;
        public final long expiresAtMs;
        public final String mimeType;

        public Grant(String trackId, boolean approved, boolean entitled,
                     String audioUrl, long expiresAtMs, String mimeType) {
            this.trackId = trackId;
            this.approved = approved;
            this.entitled = entitled;
            this.audioUrl = audioUrl;
            this.expiresAtMs = expiresAtMs;
            this.mimeType = mimeType;
        }
    }

    public static boolean isExactTrackId(String id) {
        return id != null && TRACK.matcher(id).matches();
    }

    /** No parsed URL, sensitive query, token or secret leaves the caller. */
    public static boolean isAcceptable(Grant grant, String requestedTrackId,
                                        String allowedOrigin, long nowMs) {
        if (grant == null || !isExactTrackId(requestedTrackId)
                || !requestedTrackId.equals(grant.trackId)
                || !grant.approved || !grant.entitled || nowMs < 0
                || grant.audioUrl == null || allowedOrigin == null
                || !("audio/mpeg".equals(grant.mimeType)
                    || "audio/mp4".equals(grant.mimeType))
                || grant.expiresAtMs < nowMs + MIN_TTL_MS
                || grant.expiresAtMs - nowMs > MAX_TTL_MS
                || grant.audioUrl.length() > 2048
                || allowedOrigin.length() > 512) return false;

        try {
            URI expected = new URI(allowedOrigin);
            URI signed = new URI(grant.audioUrl);
            if (!"https".equalsIgnoreCase(expected.getScheme())
                    || !"https".equalsIgnoreCase(signed.getScheme())
                    || expected.getHost() == null || signed.getHost() == null
                    || !expected.getHost().equalsIgnoreCase(signed.getHost())
                    || effectivePort(expected) != effectivePort(signed)
                    || expected.getRawUserInfo() != null
                    || signed.getRawUserInfo() != null
                    || expected.getRawQuery() != null
                    || expected.getRawFragment() != null
                    || signed.getRawFragment() != null
                    || !(expected.getRawPath().isEmpty()
                         || "/".equals(expected.getRawPath()))
                    || !RESOURCE_PATH.matcher(signed.getRawPath()).matches()) {
                return false;
            }
            String rawQuery = signed.getRawQuery();
            if (rawQuery == null || rawQuery.length() > 512) return false;
            Set<String> keys = new HashSet<>();
            String signedExpiry = null;
            boolean validToken = false;
            for (String item : rawQuery.split("&", -1)) {
                int equalAt = item.indexOf('=');
                if (equalAt <= 0 || equalAt != item.lastIndexOf('=')) return false;
                String key = item.substring(0, equalAt);
                String val = item.substring(equalAt + 1);
                if (!keys.add(key)) return false;
                switch (key) {
                    case "token":
                        if (!TOKEN.matcher(val).matches()) return false;
                        validToken = true;
                        break;
                    case "expires":
                        if (!EXPIRES.matcher(val).matches()) return false;
                        signedExpiry = val;
                        break;
                    case "sid":
                        if (!SID.matcher(val).matches()) return false;
                        break;
                    default:
                        // Reject unknown fields and the desktop-only query guard.
                        return false;
                }
            }
            if (!validToken || signedExpiry == null) return false;
            long unixSeconds = Long.parseLong(signedExpiry);
            return unixSeconds * 1000L == grant.expiresAtMs;
        } catch (URISyntaxException | ArithmeticException | NumberFormatException e) {
            return false;
        }
    }

    private static int effectivePort(URI uri) {
        return uri.getPort() == -1 ? 443 : uri.getPort();
    }
}
