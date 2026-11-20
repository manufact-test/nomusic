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
        ISSUER_TRACKID, EXACT_BETA_CREATOR, ORIGINAL_SETTER, OWNER_ENABLED,
        PREFETCH_STARTED, SIGNED_MPEG_READY, OWNER_RESOLVE_REQUEST,
        GRANT_ADMITTED, EXACT_PREPARE, DECISION_ALTERNATE,
        DATASOURCE_ARMED, AUDIO_OPEN, AUDIO_READ
    }
    private static final AtomicIntegerArray counts=
        new AtomicIntegerArray(Step.values().length);
    static void mark(Step step) {if(step!=null)counts.incrementAndGet(step.ordinal());}
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
     * are only a local, explicitly consented admission token for these 2 IDs.
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
