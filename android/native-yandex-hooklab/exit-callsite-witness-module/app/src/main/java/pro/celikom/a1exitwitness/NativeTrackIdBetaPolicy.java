package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import java.util.concurrent.atomic.AtomicIntegerArray;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.HashSet;
import java.util.Set;
import java.util.Map;

/**
 * OWNER-APPROVED LIMITED TRIAL ONLY: the original publisher's trackId and
 * exact same original Track/Album/source object lineage are the sole source
 * identities. Neither the CELIKOM server album/edition nor these synthetic
 * gate tags are evidence of a publisher album/edition. Never enable globally.
 */
final class NativeTrackIdBetaPolicy {
    private static final String RASKOL="42884423";
    private static final String LESHA_SVIK="39949113";
    // Issuer Yandex Music 10AGE & Ramil' — «Ау», owner confirmed in
    // October CELIKOM library: 144530503 (not album track 38436680).
    static final String RAMIL_AU="144530503";
    static final String BETA_ALBUM="CELIKOM_BETA_ALBUM_UNVERIFIED";
    static final String BETA_EDITION="CELIKOM_BETA_EDITION_UNVERIFIED";
    /** Privacy-safe event counters; NEVER record IDs, signed URLs or tokens. */
    enum Step {
        ISSUER_PROXY_HOOK_REGISTERED, ISSUER_PROXY_CREATED, ISSUER_METHOD_SELECTED,
        ISSUER_HANDLER_INVOKE, ISSUER_TRACK_SCOPE_MISSING,
        ISSUER_HANDLER_ARGS_PRESENT, ISSUER_HANDLER_ARGS_MISSING,
        ISSUER_PROCESSING_EXCEPTION,
        ISSUER_VALUE_NULL, ISSUER_VALUE_NONNUMERIC,
        ISSUER_VALUE_TARGET_ALLOWLISTED, ISSUER_VALUE_KNOWN_OTHER_VERSION,
        ISSUER_VALUE_OTHER_NUMERIC, ISSUER_VALUE_SCOPE_PRESENT,
        ISSUER_VALUE_SCOPE_ABSENT,
        ISSUER_ASYNC_ID_OBSERVED, ISSUER_ASYNC_CREATOR_BOUND,
        ISSUER_ASYNC_CREATOR_STALE,
        ISSUER_TRACKID, ORIGINAL_CREATOR_KEY_CONFIRMED,
        EXACT_BETA_CREATOR, ORIGINAL_SETTER, OWNER_ENABLED,
        PREFETCH_STARTED, SIGNED_MPEG_READY, OWNER_RESOLVE_REQUEST,
        OWNER_RESOLVE_APPROVED, OWNER_RESOLVE_NOT_APPROVED,
        OWNER_RESOLVE_NOT_FOUND, OWNER_RESOLVE_NOT_APPROVED_FLAG,
        OWNER_RESOLVE_NOT_ENTITLED, OWNER_RESOLVE_UNSUPPORTED_MIME,
        OWNER_RESOLVE_MPEG, OWNER_RESOLVE_MP4, SIGNED_AUDIO_READY,
        OWNER_RESPONSE_INVALID, OWNER_SIGNED_GRANT_VALID,
        OWNER_AUDIO_RANGE_VALID, OWNER_AUDIO_RANGE_REJECTED,
        OWNER_PREFETCH_SUPERSEDED, OWNER_SOURCE_WINDOW_CLOSED,
        OWNER_OFFER_REJECTED, OWNER_NETWORK_OR_RESPONSE_ERROR,
        OWNER_RESOLVE_JSON_INVALID, OWNER_RESOLVE_TRANSPORT_ERROR,
        OWNER_RESOLVE_CONSTRUCTION_ERROR, OWNER_LEGACY_REQUEST_BOUND,
        GRANT_ADMITTED, EXACT_PREPARE, DECISION_ALTERNATE,
        DATASOURCE_ARMED, AUDIO_OPEN, AUDIO_READ
    }
    private static final AtomicIntegerArray counts=
        new AtomicIntegerArray(Step.values().length);
    private static final Object PROXY_SHAPE_LOCK = new Object();
    private static final java.util.ArrayList<String> proxyShapeDetails =
        new java.util.ArrayList<>();
    private static final int MAX_PROXY_SHAPE_DETAILS = 64;

    static void mark(Step step) {if(step!=null)counts.incrementAndGet(step.ordinal());}

    /**
     * Retain bounded, non-secret reflection metadata even when the proxy is
     * created before Application.onCreate opens the local diagnostic file.
     * Only class/interface/method/annotation metadata is accepted here.
     */
    static void recordProxyShape(String category, String detail) {
        if (category == null || detail == null) return;
        String safeCategory = safeShapeToken(category);
        String safeDetail = safeShapeToken(detail);
        synchronized (PROXY_SHAPE_LOCK) {
            if (proxyShapeDetails.size() >= MAX_PROXY_SHAPE_DETAILS) return;
            proxyShapeDetails.add(
                "event=AUDIO_ISSUER_PROXY_SHAPE;origin=" + safeCategory
                + ";error=" + safeDetail + ";thread=OTHER");
        }
    }

    static String[] proxyShapeSummary() {
        synchronized (PROXY_SHAPE_LOCK) {
            return proxyShapeDetails.toArray(new String[0]);
        }
    }

    private static String safeShapeToken(String value) {
        String clean = value.toUpperCase(java.util.Locale.ROOT)
            .replaceAll("[^A-Z0-9_.$#():<>]", "_");
        if (clean.length() > 96) clean = clean.substring(0, 96);
        return clean.isEmpty() ? "UNKNOWN" : clean;
    }
    static String replacementStatus() {
        if(counts.get(Step.AUDIO_READ.ordinal())>0)return "BETA_EXO_AUDIO_READ";
        if(counts.get(Step.DATASOURCE_ARMED.ordinal())>0)return "BETA_SOURCE_ARMED";
        return "BETA_NO_ALTERNATE_AUDIO_PROOF";
    }
    static String[] diagnosticSummary() {
        Step[] steps=Step.values();
        String[] lines=new String[steps.length];
        for(int i=0;i<steps.length;i++) {
            int n=counts.get(i);
            String bucket=n==0?"NONE":n==1?"ONE":n<10?"FEW":"MANY";
            lines[i]="event=AUDIO_TRACKID_BETA;origin="+steps[i].name()
                +";error="+bucket+";thread=OTHER";
        }
        return lines;
    }
    private NativeTrackIdBetaPolicy(){}
    static boolean allows(String publisherTrackId) {
        return RASKOL.equals(publisherTrackId)
            || LESHA_SVIK.equals(publisherTrackId)
            || RAMIL_AU.equals(publisherTrackId);
    }

    /**
     * The deployed CELIKOM resolve v1 returns no approved/entitled booleans.
     * Its positive result is produced only by an approved, active catalogue
     * lookup AFTER the authenticated account/entitlement gate. A missing
     * boolean is acceptable only for THAT legacy shape, with a session-bound
     * signed audio ticket. Explicit false, partial schemas and test-token
     * responses without sid remain rejected. NativeGrantContract and the
     * actual server-verified audio Range still validate the ticket afterwards.
     */
    static boolean legacyAuthenticatedPositiveResolve(boolean found,
            boolean hasApproved,boolean hasEntitled,String relativeAudioUrl) {
        if(!found || hasApproved || hasEntitled || relativeAudioUrl==null
                || relativeAudioUrl.length()>1024)return false;
        try {
            URI u=new URI(relativeAudioUrl);
            if(u.isAbsolute() || u.getRawAuthority()!=null
                    || u.getRawFragment()!=null || u.getRawPath()==null
                    || !u.getRawPath().matches("/api/v1/audio/[1-9][0-9]{0,17}"))
                return false;
            String q=u.getRawQuery();
            if(q==null || q.length()>512)return false;
            String[] parts=q.split("&",-1);
            if(parts.length!=3)return false;
            Set<String> seen=new HashSet<>();
            for(String part:parts) {
                int eq=part.indexOf('=');
                if(eq<=0 || eq!=part.lastIndexOf('='))return false;
                String key=part.substring(0,eq),value=part.substring(eq+1);
                if(!seen.add(key))return false;
                switch(key) {
                    case "token":
                        if(!value.matches("[a-f0-9]{64}"))return false;
                        break;
                    case "expires":
                        if(!value.matches("[0-9]{9,12}"))return false;
                        break;
                    case "sid":
                        if(!value.matches("[1-9][0-9]{0,17}"))return false;
                        break;
                    default:return false;
                }
            }
            return seen.contains("token") && seen.contains("expires")
                && seen.contains("sid");
        } catch(URISyntaxException ignored) {return false;}
    }

    /**
     * Parse only the result of the authenticated, uncached, nonredirecting
     * CELIKOM resolve GET for this exact allowlisted track. Deployed v1
     * selects on service+track_id but does not echo track_id. For that
     * specific legacy schema the request scope is the catalogue identity,
     * NOT independent publisher identity or proof of audio access.
     * A present mismatched ID, a partial approval schema, and an unknown
     * legacy shape fail closed. The exact original source, session-bound
     * signature/expiry and actual Range validation remain mandatory.
     */
    static NativeGrantContract.Grant parseTrialResolve(
            String requestedTrackId,Map<String,?> fields,String allowedOrigin) {
        if(!allows(requestedTrackId) || fields==null
                || !Boolean.TRUE.equals(fields.get("found")))return null;
        Object rawUrl=fields.get("audio_url");
        if(!(rawUrl instanceof String))return null;
        String relative=(String)rawUrl;
        boolean legacy=legacyAuthenticatedPositiveResolve(true,
            fields.containsKey("approved"),fields.containsKey("entitled"),relative);
        if(!legacy && !(Boolean.TRUE.equals(fields.get("approved"))
                && Boolean.TRUE.equals(fields.get("entitled"))))return null;
        if(fields.containsKey("track_id")) {
            if(!requestedTrackId.equals(fields.get("track_id")))return null;
        } else {
            if(!legacy || fields.containsKey("album_id") || fields.containsKey("edition_id"))
                return null;
            Set<String> known=Set.of("found","replacement_id","audio_url",
                "duration_ms","mime_type","version","gain_db","gain_applied",
                "expires_at","cache_ttl_seconds");
            if(!known.containsAll(fields.keySet()))return null;
            // Exact deployed v1 response, not an arbitrary positive JSON.
            if(!Boolean.FALSE.equals(fields.get("gain_applied")))return null;
        }
        long duration=positiveInteger(fields.get("duration_ms"));
        long version=positiveInteger(fields.get("version"));
        long expiry=positiveInteger(fields.get("expires_at"));
        long replacement=positiveInteger(fields.get("replacement_id"));
        if(duration<=0 || version<=0 || expiry<=0 || expiry>Long.MAX_VALUE/1000L)
            return null;
        Object mime=fields.get("mime_type");
        if(!"audio/mpeg".equals(mime) && !"audio/mp4".equals(mime))return null;
        try {
            URI url=new URI(allowedOrigin).resolve(relative);
            if(legacy && (replacement<=0 ||
                    !("/api/v1/audio/"+replacement).equals(url.getRawPath())))
                return null;
            Object album=fields.get("album_id"),edition=fields.get("edition_id");
            // Only explicit metadata is carried; no album/edition synthesis.
            if(album!=null && !(album instanceof String)
                    || edition!=null && !(edition instanceof String))return null;
            return new NativeGrantContract.Grant(requestedTrackId,
                (String)album,(String)edition,duration,version,true,true,
                url.toString(),expiry*1000L,(String)mime);
        } catch(URISyntaxException | IllegalArgumentException | NullPointerException e) {
            return null;
        }
    }

    private static long positiveInteger(Object value) {
        if(!(value instanceof Integer) && !(value instanceof Long))return -1L;
        long number=((Number)value).longValue();
        return number>0?number:-1L;
    }

    /**
     * Validate issuer-approved CELIKOM audio against original publisher trackId
     * WITHOUT pretending the server provided original Album/Edition. The tags
     * are only a local, explicitly consented admission token for the allowlisted trial IDs.
     * The duration belongs to the signed server audio, NOT Yandex metadata.
     */
    static NativeGrantContract.Grant signedTrialGrant(
            String publisherTrackId,NativeGrantContract.Grant serverGrant,
            String allowedOrigin,long unixNowMs) {
        if(!allows(publisherTrackId) || serverGrant==null
                || !publisherTrackId.equals(serverGrant.trackId))return null;
        NativeGrantContract.Grant scoped=new NativeGrantContract.Grant(
            publisherTrackId,BETA_ALBUM,BETA_EDITION,
            serverGrant.durationMs,serverGrant.version,serverGrant.approved,
            serverGrant.entitled,serverGrant.audioUrl,
            serverGrant.expiresAtMs,serverGrant.mimeType);
        return NativeGrantContract.isAcceptable(
            scoped,publisherTrackId,BETA_ALBUM,BETA_EDITION,
            scoped.durationMs,allowedOrigin,unixNowMs)?scoped:null;
    }
}
