package pro.celikom.a1exitwitness;

import java.util.concurrent.atomic.AtomicInteger;

/** A real original source triple is required before an owner resolve is launched. */
public final class NativeCertifiedResolveBridgeTest {
    static void check(boolean accepted,String message) {
        if(!accepted)throw new AssertionError(message);
    }
    public static void main(String[] args) {
        long[] clock={100L};
        NativeEarlySourceLifecycleBridge bridge =
            new NativeEarlySourceLifecycleBridge(()->clock[0]);
        AtomicInteger resolved=new AtomicInteger();
        Object track=new Object(),album=new Object(),source=new Object(),other=new Object();
        bridge.setAuthenticatedSourceGrantRequester((generation,t,a,s,id,al,edition,duration)->{
            check(generation==1 && t==track && a==album && s==source,
                "REQUESTER_EXACT_ORIGINAL_SOURCE_REFS");
            check(id.equals("42884423") && al.equals("77")
                && edition.equals("studio-edition-v1") && duration==180000,
                "REQUESTER_EXACT_CERTIFIED_NATIVE_FIELDS");
            resolved.incrementAndGet();
        });
        bridge.startForAuthenticatedOwner();
        bridge.invalidated(1);
        bridge.pending(1,track,album,source);
        bridge.originalPublisherTrackIdCandidate(1,"42884423");
        bridge.completed(1,true);
        check(!bridge.onCertifiedOriginalSourceWithDuration(1,other,album,
            source,"42884423","77","studio-edition-v1",180000),
            "UNRELATED_TRACK_MUST_NOT_LAUNCH_HTTP");
        check(!bridge.onCertifiedOriginalSourceWithDuration(1,track,album,
            other,"42884423","77","studio-edition-v1",180000),
            "UNRELATED_SOURCE_MUST_NOT_LAUNCH_HTTP");
        check(!bridge.onCertifiedOriginalSourceWithDuration(1,track,album,
            source,"42884423","77","studio-edition-v1",0),
            "UNPROVEN_DURATION_MUST_NOT_LAUNCH_HTTP");
        check(!bridge.onCertifiedOriginalSourceWithDuration(1,track,album,
            source,"39949113","77","studio-edition-v1",180000),
            "WRONG_PUBLISHER_TRACK_ID_MUST_NOT_LAUNCH_HTTP");
        check(resolved.get()==0,"UNVERIFIED_REQUESTER_INVOKED");
        check(bridge.onCertifiedOriginalSourceWithDuration(1,track,album,
            source,"42884423","77","studio-edition-v1",180000),
            "EXACT_ORIGINAL_SOURCE_ALLOWED_TO_REQUEST_GRANT");
        check(resolved.get()==1,"EXACT_ONE_OWNER_RESOLVE_REQUEST");
        bridge.beforeUnverifiedOriginalPeriodPrepare();
        check(!bridge.onCertifiedOriginalSourceWithDuration(1,track,album,
            source,"42884423","77","studio-edition-v1",180000),
            "LATE_RESOLVE_CANNOT_UPGRADE_PREPARED_ORIGINAL");
        bridge.invalidated(2);
        check(!bridge.onCertifiedOriginalSourceWithDuration(1,track,album,
            source,"42884423","77","studio-edition-v1",180000),
            "NEXT_REVOKES_OLD_RESOLVE");
        check(resolved.get()==1,"NO_REQUEST_AFTER_NEXT");
        bridge.stopForAuthenticatedOwner();
        check(!bridge.replacementEnabled(),"OWNER_STOP_DISABLED");
        System.out.println("NATIVE_CERTIFIED_RESOLVE_ORIGINAL_IDENTITY_ONLY_PASS");
    }
}
