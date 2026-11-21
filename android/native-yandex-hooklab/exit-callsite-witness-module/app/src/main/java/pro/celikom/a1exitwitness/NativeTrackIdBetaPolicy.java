package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import java.util.concurrent.atomic.AtomicIntegerArray;

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
        ISSUER_TRACKID, EXACT_BETA_CREATOR, ORIGINAL_SETTER, OWNER_ENABLED,
        PREFETCH_STARTED, SIGNED_MPEG_READY, OWNER_RESOLVE_REQUEST,
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
