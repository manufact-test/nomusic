package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;

/** The original Exo factory may create a DataSource after MediaPeriod.prepare. */
public final class NativeDeferredExoArmTest {
    static void check(boolean ok,String message) {
        if(!ok)throw new AssertionError(message);
    }
    public static void main(String[] args) {
        final long unix=1795160000000L;
        final String trackId="42884423",albumId="77",edition="studio-edition-v1";
        final long expires=(unix/1000+300)*1000;
        final String audio="https://audio.example/api/v1/audio/42?token="
            +"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            +"&expires="+expires/1000+"&sid=8";
        NativeGrantContract.Grant grant=new NativeGrantContract.Grant(
            trackId,albumId,edition,180000,2,true,true,audio,expires,"audio/mpeg");
        NativeSourceGate.Candidate candidate=new NativeSourceGate.Candidate(
            trackId,albumId,edition,true,true,true,true,true,true);
        NativeExoAlternateByteRoute route=new NativeExoAlternateByteRoute();
        NativeEarlySourceLifecycleBridge bridge=
            new NativeEarlySourceLifecycleBridge(()->1000L,route,()->unix);
        Object track=new Object(),album=new Object(),source=new Object();
        Object period=new Object(),actualDataSource=new Object();
        bridge.startForAuthenticatedOwner();
        bridge.invalidated(1);
        bridge.pending(1,track,album,source);
        bridge.originalPublisherTrackIdCandidate(1,trackId);
        bridge.completed(1,true);
        check(bridge.onSourceBoundPublisherFileInfo(1,track,album,source,
            trackId,albumId,edition),"ORIGINAL_SOURCE_TRIPLE_CERTIFIED");
        check(bridge.offerAuthenticatedApprovedAudio(1,track,album,source,
            candidate,grant,"https://audio.example",180000),
            "AUTHORIZED_GRANT_READY_BEFORE_ORIGINAL_PREPARE");
        bridge.beforeOriginalPeriodPrepare(1,track,album,source,period,null);
        check(bridge.chosenSource()==NativeSourceGate.Choice.ORIGINAL,
            "DEFERRED_NOT_YET_AUDIBLE");
        check(!bridge.armDeferredOriginalDataSource(1,track,album,new Object(),
            new Object()),"DIFFERENT_ORIGINAL_SOURCE_REJECTED");
        check(!bridge.armDeferredOriginalDataSource(0,track,album,source,
            new Object()),"OLD_GENERATION_REJECTED");
        check(bridge.armDeferredOriginalDataSource(1,track,album,source,
            actualDataSource),"SAME_FRESH_FACTORY_SOURCE_ARMED");
        check(route.isArmed(actualDataSource),"ORIGINAL_EXO_DATASOURCE_ARMED");
        check(bridge.chosenSource()==NativeSourceGate.Choice.ALTERNATE,
            "ONLY_ACTUAL_ROUTE_CAN_REPORT_ALTERNATE");
        check(!bridge.armDeferredOriginalDataSource(1,track,album,source,
            new Object()),"NO_SECOND_SOURCE_FROM_SAME_PREPARE");
        bridge.invalidated(2);
        check(!route.isArmed(actualDataSource),"NEXT_RETIRES_ARMED_SOURCE");
        check(bridge.chosenSource()==NativeSourceGate.Choice.ORIGINAL,
            "NEXT_CANNOT_KEEP_OLD_ALTERNATE_STATUS");

        NativeExoAlternateByteRoute ambiguousRoute=new NativeExoAlternateByteRoute();
        NativeEarlySourceLifecycleBridge ambiguous=new NativeEarlySourceLifecycleBridge(
            ()->1000L,ambiguousRoute,()->unix);
        ambiguous.startForAuthenticatedOwner();
        ambiguous.invalidated(1);
        ambiguous.pending(1,track,album,source);
        ambiguous.originalPublisherTrackIdCandidate(1,trackId);
        ambiguous.completed(1,true);
        check(ambiguous.onSourceBoundPublisherFileInfo(1,track,album,source,
            trackId,albumId,edition),"AMBIGUOUS_FIXTURE_ID_CERTIFIED");
        check(ambiguous.offerAuthenticatedApprovedAudio(1,track,album,source,
            candidate,grant,"https://audio.example",180000),
            "AMBIGUOUS_FIXTURE_GRANT_PENDING");
        ambiguous.beforeOriginalPeriodPrepare(1,track,album,source,period,null);
        ambiguous.beforeOriginalPeriodPrepare(1,track,album,source,
            new Object(),null);
        check(!ambiguous.armDeferredOriginalDataSource(1,track,album,source,
            new Object()),"SECOND_PERIOD_NEVER_ARMED");
        check(ambiguous.chosenSource()==NativeSourceGate.Choice.ORIGINAL,
            "AMBIGUOUS_PERIOD_CANNOT_CLAIM_AUDIO");

        System.out.println("NATIVE_DEFERRED_EXO_AFTER_PREPARE_EXACT_SOURCE_PASS");
    }
}
