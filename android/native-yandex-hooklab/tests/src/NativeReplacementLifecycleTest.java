import pro.celikom.yandex.nativehooklab.NativeReplacementLifecycle;
import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;
import pro.celikom.yandex.nativehooklab.NativePrePrepareAdmission;

public final class NativeReplacementLifecycleTest {
    private static int assertions;
    private static final long EPOCH = 1_799_000_000_000L;
    private static final long EXPIRY = EPOCH + 300000L;
    private static final String ORIGIN = "https://api.celikom.test";
    private static final String TRACK = "42884423";
    private static final String ALBUM = "album-main";
    private static final long DURATION = 200_000L;
    private static final String EDITION = "studio";
    private static final String SIGNED = ORIGIN + "/api/v1/audio/139?token="
            + "a".repeat(64) + "&expires=" + EXPIRY/1000 + "&sid=7";

    private static void yes(boolean condition, String label) {
        assertions++;
        if (!condition) throw new AssertionError(label + " #" + assertions);
    }
    private static void eq(Object a, Object b, String label) {
        yes(a == b || (a != null && a.equals(b)), label);
    }
    private static NativeSourceGate.Candidate candidate(String id, String edition) {
        return new NativeSourceGate.Candidate(id, ALBUM, edition,
                true,true,true,true,true,true);
    }
    private static NativeGrantContract.Grant grant(String id) {
        return new NativeGrantContract.Grant(id, ALBUM, EDITION, DURATION, 1, true, true, SIGNED, EXPIRY, "audio/mpeg");
    }
    private static NativePrePrepareAdmission.Offer offer(
            NativeReplacementLifecycle s, long token, long elapsed) {
        return s.offerValidated(token, candidate(TRACK,EDITION), grant(TRACK), ORIGIN, DURATION, elapsed, EPOCH);
    }

    private static void stopCancelsPendingAndPreventsGrantLeaks() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        long disabled=s.beginTrack(TRACK, ALBUM, EDITION, 10);
        yes(!s.observeFileInfo(disabled, TRACK, ALBUM, EDITION),"disabled never observes");
        eq(NativePrePrepareAdmission.Offer.REJECTED,offer(s,disabled,11),"disabled cannot offer");
        yes(!s.atNativePrepare(disabled, TRACK, ALBUM, EDITION, 12).applyOnce,
                "OFF does not create alternate or second source");
        s.start();
        long token=s.beginTrack(TRACK, ALBUM, EDITION, 100);
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,token,110),
                "valid Windows-parity grant pending");
        yes(s.observeFileInfo(token, TRACK, ALBUM, EDITION),"native FileInfo can match");
        eq(NativeReplacementLifecycle.StopVerdict.CANCELLED_PENDING,s.stop(),
                "stop cancels in-flight request");
        eq(NativePrePrepareAdmission.Offer.STALE,offer(s,token,120),
                "late fetch from cancelled session invalid");
        yes(!s.atNativePrepare(token, TRACK, ALBUM, EDITION, 125).applyOnce,
                "late completion cannot map source after Stop");
        long off=s.beginTrack(TRACK, ALBUM, EDITION, 130);
        yes(!s.atNativePrepare(off, TRACK, ALBUM, EDITION, 131).applyOnce,
                "new track after Stop always original");
        s.start();
        long again=s.beginTrack(TRACK, ALBUM, EDITION, 150);
        yes(again!=token,"re-enable changes generation");
        yes(s.observeFileInfo(again, TRACK, ALBUM, EDITION),"fresh same-ID identity only");
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,again,152),
                "new grant can proceed on fresh generation");
        eq(NativeSourceGate.Choice.ALTERNATE,
                s.atNativePrepare(again, TRACK, ALBUM, EDITION, 155).source,
                "correct native descriptor still gates alternate");
        yes(!s.atNativePrepare(again, TRACK, ALBUM, EDITION, 160).applyOnce,
                "duplicate must not remap source");
    }

    private static void stopCannotRetractAlreadyBufferedAudio() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long t=s.beginTrack(TRACK, ALBUM, EDITION, 100);
        yes(s.observeFileInfo(t, TRACK, ALBUM, EDITION),"matched request");
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,t,110),
                "approved source pending");
        eq(NativeSourceGate.Choice.ALTERNATE,
                s.atNativePrepare(t, TRACK, ALBUM, EDITION, 130).source,
                "issued once");
        s.onNativePlay(t);s.onNativeSeek(t);s.onNativePause(t);
        eq(NativeReplacementLifecycle.StopVerdict.ALREADY_ISSUED_SOURCE_UNCHANGED,
                s.stop(),"stop cannot rewrite native already-loaded Yandex media");
        yes(!s.isEnabled(),"OFF state is effective for future lookup");
        eq(NativeReplacementLifecycle.StopVerdict.ALREADY_OFF,s.stop(),
                "repeat Stop idempotent");
        long next=s.beginTrack("39949113", ALBUM, "radio", 500);
        yes(!s.atNativePrepare(next, "39949113", ALBUM, "radio", 510).applyOnce,
                "next mapping OFF, don't interrupt native Yandex");
        yes(s.lastIssuedSource()==NativeSourceGate.Choice.ORIGINAL,
                "next future source remains original");
    }

    private static void invalidGrantNeverMapsDespiteMatchingSource() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long t=s.beginTrack(TRACK, ALBUM, EDITION, 100);
        yes(s.observeFileInfo(t, TRACK, ALBUM, EDITION),"FileInfo match");
        NativeGrantContract.Grant malformed=new NativeGrantContract.Grant(TRACK, ALBUM, EDITION, DURATION, 1, true, true, SIGNED+"?vsid=YT11&source_index=2", EXPIRY, "audio/mpeg");
        eq(NativePrePrepareAdmission.Offer.REJECTED,
                s.offerValidated(t, candidate(TRACK,EDITION), malformed, ORIGIN, DURATION, 110, EPOCH),
                "desktop double-query pattern must be rejected in native Android");
        eq(NativeSourceGate.Choice.ORIGINAL,
                s.atNativePrepare(t, TRACK, ALBUM, EDITION, 120).source,
                "native original when signed URL malformed");
    }

    private static void stressNextRaceAndOffSwitch() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        for(int i=0;i<5000;i++){
            long now=10000L+i*2500L;
            long old=s.beginTrack(TRACK, ALBUM, EDITION, now);
            s.observeFileInfo(old, TRACK, ALBUM, EDITION);
            eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,old,now+1),
                    "old audio candidate accepted but not committed");
            long newer=s.beginTrack("39949113", ALBUM, "radio", now+2);
            yes(old!=newer, "generation rotates at Next/radio");
            eq(NativePrePrepareAdmission.Offer.STALE,offer(s,old,now+3),
                    "old response cannot change next track");
            yes(!s.atNativePrepare(old, TRACK, ALBUM, EDITION, now+4).applyOnce,
                    "old source cannot prepare");
            yes(s.observeFileInfo(newer, "39949113", ALBUM, "radio"),
                    "new native FileInfo checked");
            eq(NativeSourceGate.Choice.ORIGINAL,
                    s.atNativePrepare(newer, "39949113", ALBUM, "radio", now+5).source,
                    "no new grant means original");
            if (i%11 == 0) {s.stop();s.start();}
        }
    }

    private static void wrongAlbumAndMissingAlbumAlwaysOriginal() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long g=s.beginTrack(TRACK,ALBUM,EDITION,100);
        yes(s.observeFileInfo(g,TRACK,ALBUM,EDITION),"full triple fileinfo");
        NativeSourceGate.Candidate other=new NativeSourceGate.Candidate(
            TRACK,"another-album",EDITION,true,true,true,true,true,true);
        eq(s.offerValidated(g, other, grant(TRACK), ORIGIN, DURATION, 110, EPOCH),
            NativePrePrepareAdmission.Offer.REJECTED,"wrong album candidate blocked");
        eq(s.atNativePrepare(g,TRACK,ALBUM,EDITION,120).source,
            NativeSourceGate.Choice.ORIGINAL,"invalid candidate never applied");
        long nullAlbum=s.beginTrack(TRACK,null,EDITION,130);
        yes(!s.observeFileInfo(nullAlbum,TRACK,ALBUM,EDITION),"null album proof impossible");
        eq(offer(s,nullAlbum,135),NativePrePrepareAdmission.Offer.REJECTED,
            "null album can't authorize alternate");
        eq(s.atNativePrepare(nullAlbum,TRACK,null,EDITION,140).source,
            NativeSourceGate.Choice.ORIGINAL,"null decoder album original");
    }


    private static void grantFromDifferentAlbumCannotAuthorize() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long token=s.beginTrack(TRACK,ALBUM,EDITION,100);
        yes(s.observeFileInfo(token,TRACK,ALBUM,EDITION),"native triple");
        NativeGrantContract.Grant wrong=new NativeGrantContract.Grant(
            TRACK,"unrelated-album",EDITION,DURATION,3,true,true,SIGNED,EXPIRY,"audio/mpeg");
        eq(s.offerValidated(token,candidate(TRACK,EDITION),wrong,ORIGIN,DURATION,110,EPOCH),
            NativePrePrepareAdmission.Offer.REJECTED,
            "server grant must match selected album, not merely track ID");
        eq(s.atNativePrepare(token,TRACK,ALBUM,EDITION,120).source,
            NativeSourceGate.Choice.ORIGINAL,
            "rejected server album cannot reach native alternate");
    }

    private static void unresolvedOriginalSourceMustNotUpgradeAfterPrepare() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long first=s.beginUnresolvedNativeSelection(100);
        yes(s.isEnabled() && s.generation()==first,"early selection reserved");
        yes(!s.observeFileInfo(first,TRACK,ALBUM,EDITION),"unresolved no FileInfo");
        eq(NativePrePrepareAdmission.Offer.REJECTED,offer(s,first,105),
                "unresolved grant rejected");
        NativePrePrepareAdmission.Decision original=
            s.atNativePrepare(first,TRACK,ALBUM,EDITION,110);
        yes(!original.applyOnce && original.source==NativeSourceGate.Choice.ORIGINAL,
                "unresolved original prepare is not alternate");
        yes(!s.certifyNativeIdentity(first,TRACK,ALBUM,EDITION,115),
                "after real prepare cannot upgrade audio");
        eq(NativePrePrepareAdmission.Offer.REJECTED,offer(s,first,120),
                "postprepare grant cannot enter audio");
        eq(NativeReplacementLifecycle.StopVerdict.ALREADY_ISSUED_SOURCE_UNCHANGED,
                s.stop(),"stop does not retract already prepared original source");
    }

    private static void exactIdentityCanCertifySameUnpreparedSelection() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long first=s.beginUnresolvedNativeSelection(100);
        yes(!s.certifyNativeIdentity(first,"title",ALBUM,EDITION,105),
                "no guessed title as native trackId");
        yes(!s.certifyNativeIdentity(first,TRACK,null,EDITION,105),
                "missing album never certified");
        yes(!s.certifyNativeIdentity(first,TRACK,ALBUM,EDITION,99),
                "clock going backwards never certifies");
        long next=s.beginUnresolvedNativeSelection(120);
        yes(!s.certifyNativeIdentity(first,TRACK,ALBUM,EDITION,121),
                "Next invalidates old original Track identity");
        yes(s.certifyNativeIdentity(next,TRACK,ALBUM,EDITION,122),
                "same early setter generation accepts independently proven triple");
        yes(!s.certifyNativeIdentity(next,TRACK,ALBUM,EDITION,123),
                "same selected source cannot be certified twice");
        yes(s.observeFileInfo(next,TRACK,ALBUM,EDITION),
                "only exact FileInfo on same generation");
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,next,125),
                "approved signed source waits for real prepare");
        eq(NativeSourceGate.Choice.ALTERNATE,
                s.atNativePrepare(next,TRACK,ALBUM,EDITION,128).source,
                "exact same native generation accepts once");
        yes(!s.atNativePrepare(next,TRACK,ALBUM,EDITION,129).applyOnce,
                "no second prepare commit");
        yes(!s.certifyNativeIdentity(next,TRACK,ALBUM,EDITION,130),
                "issued source is not recertifiable");
        long replay=s.beginUnresolvedNativeSelection(131);
        yes(!s.atNativePrepare(next,TRACK,ALBUM,EDITION,132).applyOnce,
                "late old track cannot change replay source");
        yes(s.certifyNativeIdentity(replay,TRACK,ALBUM,EDITION,133),
                "same track replay is a fresh native generation");
        eq(NativeSourceGate.Choice.ORIGINAL,
                s.atNativePrepare(replay,TRACK,ALBUM,EDITION,134).source,
                "without independent fresh FileInfo and grant replay stays original");
    }

    private static void unresolvedBudgetCannotRestartOnLateIdentity() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long late=s.beginUnresolvedNativeSelection(100);
        yes(!s.certifyNativeIdentity(late,TRACK,ALBUM,EDITION,951),
                "late semantic discovery does not refresh original deadline");
        yes(!s.certifyNativeIdentity(late,TRACK,ALBUM,EDITION,1000),
                "no late alternate after 850ms");
        eq(NativeSourceGate.Choice.ORIGINAL,
            s.atNativePrepare(late,TRACK,ALBUM,EDITION,1001).source,
            "expired original selection never maps alternate");
        long eligible=s.beginUnresolvedNativeSelection(2000);
        yes(s.certifyNativeIdentity(eligible,TRACK,ALBUM,EDITION,2700),
            "in-budget certificate accepted");
        yes(s.observeFileInfo(eligible,TRACK,ALBUM,EDITION),
            "in-budget fileinfo");
        eq(NativePrePrepareAdmission.Offer.REJECTED,offer(s,eligible,2851),
            "source deadline remains at original begin, not certificate time");
        eq(NativeSourceGate.Choice.ORIGINAL,
            s.atNativePrepare(eligible,TRACK,ALBUM,EDITION,2852).source,
            "expired grant resolution keeps original");
    }

    private static void certificationMustRequireActualOriginalSelection() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long generationWithoutTrack=s.generation();
        yes(!s.certifyNativeIdentity(generationWithoutTrack,TRACK,ALBUM,EDITION,10),
                "start is not an original source selection");
        long unresolved=s.beginUnresolvedNativeSelection(-1);
        yes(!s.certifyNativeIdentity(unresolved,TRACK,ALBUM,EDITION,0),
                "invalid original clock cannot yield valid alternate");
        long exact=s.beginTrack(TRACK,ALBUM,EDITION,100);
        yes(!s.certifyNativeIdentity(exact,TRACK,ALBUM,EDITION,101),
                "legacy exact selection cannot be recertified");
    }

    private static void failedOriginalSetterCancelsPendingAdmission() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long unresolved=s.beginUnresolvedNativeSelection(100);
        yes(s.cancelPendingNativeSelection(unresolved),
            "failed publisher setter must cancel unresolved generation");
        yes(!s.certifyNativeIdentity(unresolved,TRACK,ALBUM,EDITION,102),
            "cannot promote failed source after cancel");
        yes(!s.cancelPendingNativeSelection(unresolved),
            "cannot abort the next selection using old token");
        long fresh=s.beginUnresolvedNativeSelection(200);
        yes(s.certifyNativeIdentity(fresh,TRACK,ALBUM,EDITION,201),
            "fresh exact selection still allowed");
        yes(s.observeFileInfo(fresh,TRACK,ALBUM,EDITION),
            "fresh certified FileInfo");
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,fresh,203),
            "fresh authorized source offered");
        yes(s.cancelPendingNativeSelection(fresh),
            "throwing publisher setter cancels pending signed grant too");
        eq(NativePrePrepareAdmission.Offer.STALE,offer(s,fresh,204),
            "pending signed grant cannot leak across failed publisher setter");
        long committed=s.beginUnresolvedNativeSelection(300);
        yes(s.atNativePrepare(committed,TRACK,ALBUM,EDITION,305).source
                == NativeSourceGate.Choice.ORIGINAL,
                "unknown decoder selects original");
        yes(!s.cancelPendingNativeSelection(committed),
            "already issued original decoder cannot be cancelled");
    }

    private static void stopAndRestartInvalidateUnresolvedGeneration() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        long disabled=s.beginUnresolvedNativeSelection(10);
        yes(!s.certifyNativeIdentity(disabled,TRACK,ALBUM,EDITION,11),
                "disabled unresolved track cannot start alternate");
        s.start();
        long active=s.beginUnresolvedNativeSelection(20);
        eq(NativeReplacementLifecycle.StopVerdict.NO_SOURCE_ISSUED,s.stop(),
                "stop unresolved request before native source safely");
        s.start();
        yes(!s.certifyNativeIdentity(active,TRACK,ALBUM,EDITION,22),
                "old pending original binding after Stop is stale");
    }

    private static void ownerOnlyColdNetworkGraceHasMatchingAdmissionDeadline() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(3000);
        s.start();
        long t=s.beginUnresolvedNativeSelection(100);
        yes(s.certifyNativeIdentity(t,TRACK,ALBUM,EDITION,2600),
            "same native source may certify after a slow first HTTPS resolve");
        yes(s.observeFileInfo(t,TRACK,ALBUM,EDITION),
            "matching native identity required even for cold audio");
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,t,2601),
            "owner signed grant admitted within matching 3000ms window");
        eq(NativeSourceGate.Choice.ALTERNATE,
            s.atNativePrepare(t,TRACK,ALBUM,EDITION,2610).source,
            "first original period may commit signed alternate");
        long late=s.beginUnresolvedNativeSelection(4000);
        yes(!s.certifyNativeIdentity(late,TRACK,ALBUM,EDITION,7100),
            "deadline stays closed after 3000ms");
        eq(NativeSourceGate.Choice.ORIGINAL,
            s.atNativePrepare(late,TRACK,ALBUM,EDITION,7101).source,
            "late grants never replace already-preparing original audio");
        long interrupted=s.beginUnresolvedNativeSelection(8000);
        long next=s.beginUnresolvedNativeSelection(8100);
        yes(!s.certifyNativeIdentity(interrupted,TRACK,ALBUM,EDITION,8200),
            "Next cancels the previous owner network generation");
        yes(next!=interrupted,"generation changes on next");
    }

    public static void main(String[] args) {
        ownerOnlyColdNetworkGraceHasMatchingAdmissionDeadline();
        stopAndRestartInvalidateUnresolvedGeneration();
        failedOriginalSetterCancelsPendingAdmission();
        certificationMustRequireActualOriginalSelection();
        unresolvedBudgetCannotRestartOnLateIdentity();
        unresolvedOriginalSourceMustNotUpgradeAfterPrepare();
        exactIdentityCanCertifySameUnpreparedSelection();
        grantFromDifferentAlbumCannotAuthorize();
        wrongAlbumAndMissingAlbumAlwaysOriginal();
        stopCancelsPendingAndPreventsGrantLeaks();
        stopCannotRetractAlreadyBufferedAudio();
        invalidGrantNeverMapsDespiteMatchingSource();
        stressNextRaceAndOffSwitch();
        System.out.println("PASS: NativeReplacementLifecycle " + assertions
                + " assertions; W58 Stop, Next/radio generations, fail-closed signed audio URL");
    }
}
