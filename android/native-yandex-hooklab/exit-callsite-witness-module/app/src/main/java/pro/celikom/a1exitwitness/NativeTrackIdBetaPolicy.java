package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeGrantContract;

/**
 * OWNER-APPROVED LIMITED TRIAL ONLY: the original publisher's trackId and
 * exact same original Track/Album/source object lineage are the sole source
 * identities. Neither the CELIKOM server album/edition nor these synthetic
 * gate tags are evidence of a publisher album/edition. Never enable globally.
 */
final class NativeTrackIdBetaPolicy {
    private static final String RASKOL="42884423";
    private static final String LESHA_SVIK="39949113";
    static final String BETA_ALBUM="CELIKOM_BETA_ALBUM_UNVERIFIED";
    static final String BETA_EDITION="CELIKOM_BETA_EDITION_UNVERIFIED";
    private NativeTrackIdBetaPolicy(){}
    static boolean allows(String publisherTrackId) {
        return RASKOL.equals(publisherTrackId)
            || LESHA_SVIK.equals(publisherTrackId);
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
