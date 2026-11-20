package pro.celikom.a1exitwitness;

import java.util.concurrent.atomic.AtomicInteger;
import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;

/** Consent-limited, original source/trackID, signed audio, no fake Yandex album. */
public final class NativeTrackIdBetaTrialTest {
    private static void check(boolean yes,String message) {
        if(!yes)throw new AssertionError(message);
    }
    private static final long NOW=1795160000000L;
    private static NativeGrantContract.Grant grant(String track,
            boolean approved,boolean entitled,long expiry) {
        final String url="https://audio.example/api/v1/audio/42?token="
            +"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            +"&expires="+expiry/1000+"&sid=8";
        // Deliberately NO original AlbumID or EditionID, per owner beta consent.
        return new NativeGrantContract.Grant(track,null,null,180000,2,
            approved,entitled,url,expiry,"audio/mpeg");
    }
    private static final String RASKOL="42884423";
    private static final String LESHA="39949113";
    private static void allowlistAndSignedGrant() {
        check(NativeTrackIdBetaPolicy.allows(RASKOL)
            && NativeTrackIdBetaPolicy.allows(LESHA)
            && NativeTrackIdBetaPolicy.allows(NativeTrackIdBetaPolicy.RAMIL_AU),
            "BETA_ONLY_TWO_OWNER_CHOSEN_TRACKS");
        check(!NativeTrackIdBetaPolicy.allows("42884424")
            && !NativeTrackIdBetaPolicy.allows("1")
            && !NativeTrackIdBetaPolicy.allows(null),
            "ANY_OTHER_SONG_MUST_USE_ORIGINAL");
        NativeGrantContract.Grant raw=grant(RASKOL,true,true,NOW+300000);
        NativeGrantContract.Grant approved=NativeTrackIdBetaPolicy.signedTrialGrant(
            RASKOL,raw,"https://audio.example",NOW);
        check(approved!=null && RASKOL.equals(approved.trackId)
            && NativeTrackIdBetaPolicy.BETA_ALBUM.equals(approved.albumId)
            && NativeTrackIdBetaPolicy.BETA_EDITION.equals(approved.editionId),
            "BETA_TAGS_NEVER_CLAIM_ISSUER_ALBUM_OR_EDITION");
        check(NativeTrackIdBetaPolicy.signedTrialGrant(
            LESHA,raw,"https://audio.example",NOW)==null,
            "SERVER_TRACK_ID_MISMATCH_MUST_NOT_APPLY");
        check(NativeTrackIdBetaPolicy.signedTrialGrant(
            RASKOL,grant(RASKOL,false,true,NOW+300000),
            "https://audio.example",NOW)==null,"MAPPING_NOT_APPROVED");
        check(NativeTrackIdBetaPolicy.signedTrialGrant(
            RASKOL,grant(RASKOL,true,false,NOW+300000),
            "https://audio.example",NOW)==null,"NO_USER_ENTITLEMENT");
        check(NativeTrackIdBetaPolicy.signedTrialGrant(
            RASKOL,grant(RASKOL,true,true,NOW-1000),
            "https://audio.example",NOW)==null,"EXPIRED_SIGNED_AUDIO");
        check(NativeTrackIdBetaPolicy.signedTrialGrant(
            RASKOL,raw,"https://attacker.example",NOW)==null,"BAD_AUDIO_ORIGIN");
    }
    private static void sourceAndPrepare(String trackId) {
        NativeExoAlternateByteRoute route=new NativeExoAlternateByteRoute();
        NativeEarlySourceLifecycleBridge bridge=new NativeEarlySourceLifecycleBridge(
            ()->1000L,route,()->NOW);
        Object track=new Object(),album=new Object(),source=new Object();
        Object period=new Object(),dataSource=new Object();
        AtomicInteger callbacks=new AtomicInteger();
        bridge.setLimitedBetaGrantRequester((gen,t,a,s,originalId)->{
            callbacks.incrementAndGet();
            check(gen==1 && t==track && a==album && s==source
                && originalId.equals(trackId),"ONLY_SAME_PUBLISHER_LINEAGE_CAN_BETA");
            check(!bridge.offerLimitedBetaSignedAudio(gen,track,album,new Object(),
                originalId,grant(trackId,true,true,NOW+300000),
                "https://audio.example"),"WRONG_ORIGINAL_SOURCE_REJECTED");
            check(!bridge.offerLimitedBetaSignedAudio(gen,track,album,source,
                originalId,grant("1234567",true,true,NOW+300000),
                "https://audio.example"),"WRONG_SIGNED_ID_REJECTED");
            check(bridge.offerLimitedBetaSignedAudio(gen,track,album,source,
                originalId,grant(trackId,true,true,NOW+300000),
                "https://audio.example"),"SIGNED_BETA_SCOPED_PENDING");
        });
        bridge.startForAuthenticatedOwner();
        bridge.invalidated(1);
        bridge.pending(1,track,album,source);
        bridge.originalPublisherTrackIdCandidate(1,trackId);
        bridge.completed(1,true);
        check(callbacks.get()==1,"APPROVED_BETA_REQUEST_ON_TRUE_SETTER");
        check(bridge.chosenSource()==NativeSourceGate.Choice.ORIGINAL,
            "PENDING_DOES_NOT_CLAIM_AUDIO");
        bridge.beforeOriginalPeriodPrepare(1,track,album,source,period,null);
        check(bridge.chosenSource()==NativeSourceGate.Choice.ORIGINAL,
            "POST_PREPARE_NOT_YET_EXO_ARMED");
        check(bridge.armDeferredOriginalDataSource(1,track,album,source,
            dataSource),"APPROVED_BETA_USES_ONE_ORIGINAL_EXO_SOURCE");
        check(route.isArmed(dataSource),"SAME_EXO_DATASOURCE_OWNED_BY_BETA_BYTES");
        check(bridge.chosenSource()==NativeSourceGate.Choice.ALTERNATE,
            "ALTERNATE_ONLY_AFTER_REAL_EXO_SOURCE_ARM");
        check(!bridge.offerLimitedBetaSignedAudio(1,track,album,source,
            trackId,grant(trackId,true,true,NOW+300000),
            "https://audio.example"),"LATE_BETA_NEVER_UPGRADES_PREPARED_SONG");
        bridge.invalidated(2);
        check(!route.isArmed(dataSource),"MYWAVE_NEXT_REVOKES_STALE_BYTES");
        check(bridge.chosenSource()==NativeSourceGate.Choice.ORIGINAL,
            "NEXT_ORIGINAL_UNTIL_NEW_SOURCE");
    }
    private static void noGrantNoAudio() {
        NativeEarlySourceLifecycleBridge bridge=new NativeEarlySourceLifecycleBridge(
            ()->1000L,new NativeExoAlternateByteRoute(),()->NOW);
        Object track=new Object(),album=new Object(),source=new Object();
        bridge.startForAuthenticatedOwner();
        bridge.invalidated(1);
        bridge.pending(1,track,album,source);
        bridge.originalPublisherTrackIdCandidate(1,RASKOL);
        bridge.completed(1,true);
        bridge.beforeOriginalPeriodPrepare(1,track,album,source,new Object(),null);
        check(!bridge.offerLimitedBetaSignedAudio(1,track,album,source,RASKOL,
            grant(RASKOL,true,true,NOW+300000),"https://audio.example"),
            "LATE_NETWORK_RESPONSE_CANNOT_UPGRADE_ORIGINAL");
        bridge.stopForAuthenticatedOwner();
        check(!bridge.replacementEnabled(),"OWNER_STOP_REVOKES_NEW_ADMISSION");
    }
    public static void main(String[] args) {
        allowlistAndSignedGrant();
        sourceAndPrepare(RASKOL);
        sourceAndPrepare(LESHA);
        sourceAndPrepare(NativeTrackIdBetaPolicy.RAMIL_AU);
        noGrantNoAudio();
        System.out.println("NATIVE_TWO_TRACK_CONSENTED_BETA_STRICT_SOURCE_PASS");
    }
}
