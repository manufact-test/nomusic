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
        return new NativeSourceGate.Candidate(id, edition,
                true,true,true,true,true,true);
    }
    private static NativeGrantContract.Grant grant(String id) {
        return new NativeGrantContract.Grant(id,true,true,SIGNED,EXPIRY,"audio/mpeg");
    }
    private static NativePrePrepareAdmission.Offer offer(
            NativeReplacementLifecycle s, long token, long elapsed) {
        return s.offerValidated(token,candidate(TRACK,EDITION),
                grant(TRACK),ORIGIN,elapsed,EPOCH);
    }

    private static void stopCancelsPendingAndPreventsGrantLeaks() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        long disabled=s.beginTrack(TRACK,EDITION,10);
        yes(!s.observeFileInfo(disabled,TRACK,EDITION),"disabled never observes");
        eq(NativePrePrepareAdmission.Offer.REJECTED,offer(s,disabled,11),"disabled cannot offer");
        yes(!s.atNativePrepare(disabled,TRACK,EDITION,12).applyOnce,
                "OFF does not create alternate or second source");
        s.start();
        long token=s.beginTrack(TRACK,EDITION,100);
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,token,110),
                "valid Windows-parity grant pending");
        yes(s.observeFileInfo(token,TRACK,EDITION),"native FileInfo can match");
        eq(NativeReplacementLifecycle.StopVerdict.CANCELLED_PENDING,s.stop(),
                "stop cancels in-flight request");
        eq(NativePrePrepareAdmission.Offer.STALE,offer(s,token,120),
                "late fetch from cancelled session invalid");
        yes(!s.atNativePrepare(token,TRACK,EDITION,125).applyOnce,
                "late completion cannot map source after Stop");
        long off=s.beginTrack(TRACK,EDITION,130);
        yes(!s.atNativePrepare(off,TRACK,EDITION,131).applyOnce,
                "new track after Stop always original");
        s.start();
        long again=s.beginTrack(TRACK,EDITION,150);
        yes(again!=token,"re-enable changes generation");
        yes(s.observeFileInfo(again,TRACK,EDITION),"fresh same-ID identity only");
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,again,152),
                "new grant can proceed on fresh generation");
        eq(NativeSourceGate.Choice.ALTERNATE,
                s.atNativePrepare(again,TRACK,EDITION,155).source,
                "correct native descriptor still gates alternate");
        yes(!s.atNativePrepare(again,TRACK,EDITION,160).applyOnce,
                "duplicate must not remap source");
    }

    private static void stopCannotRetractAlreadyBufferedAudio() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long t=s.beginTrack(TRACK,EDITION,100);
        yes(s.observeFileInfo(t,TRACK,EDITION),"matched request");
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,t,110),
                "approved source pending");
        eq(NativeSourceGate.Choice.ALTERNATE,
                s.atNativePrepare(t,TRACK,EDITION,130).source,
                "issued once");
        s.onNativePlay(t);s.onNativeSeek(t);s.onNativePause(t);
        eq(NativeReplacementLifecycle.StopVerdict.ALREADY_ISSUED_SOURCE_UNCHANGED,
                s.stop(),"stop cannot rewrite native already-loaded Yandex media");
        yes(!s.isEnabled(),"OFF state is effective for future lookup");
        eq(NativeReplacementLifecycle.StopVerdict.ALREADY_OFF,s.stop(),
                "repeat Stop idempotent");
        long next=s.beginTrack("39949113","radio",500);
        yes(!s.atNativePrepare(next,"39949113","radio",510).applyOnce,
                "next mapping OFF, don't interrupt native Yandex");
        yes(s.lastIssuedSource()==NativeSourceGate.Choice.ORIGINAL,
                "next future source remains original");
    }

    private static void invalidGrantNeverMapsDespiteMatchingSource() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        long t=s.beginTrack(TRACK,EDITION,100);
        yes(s.observeFileInfo(t,TRACK,EDITION),"FileInfo match");
        NativeGrantContract.Grant malformed=new NativeGrantContract.Grant(
                TRACK,true,true,SIGNED+"?vsid=YT11&source_index=2",
                EXPIRY,"audio/mpeg");
        eq(NativePrePrepareAdmission.Offer.REJECTED,
                s.offerValidated(t,candidate(TRACK,EDITION),malformed,ORIGIN,110,EPOCH),
                "desktop double-query pattern must be rejected in native Android");
        eq(NativeSourceGate.Choice.ORIGINAL,
                s.atNativePrepare(t,TRACK,EDITION,120).source,
                "native original when signed URL malformed");
    }

    private static void stressNextRaceAndOffSwitch() {
        NativeReplacementLifecycle s=new NativeReplacementLifecycle(850);
        s.start();
        for(int i=0;i<5000;i++){
            long now=10000L+i*2500L;
            long old=s.beginTrack(TRACK,EDITION,now);
            s.observeFileInfo(old,TRACK,EDITION);
            eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,offer(s,old,now+1),
                    "old audio candidate accepted but not committed");
            long newer=s.beginTrack("39949113","radio",now+2);
            yes(old!=newer, "generation rotates at Next/radio");
            eq(NativePrePrepareAdmission.Offer.STALE,offer(s,old,now+3),
                    "old response cannot change next track");
            yes(!s.atNativePrepare(old,TRACK,EDITION,now+4).applyOnce,
                    "old source cannot prepare");
            yes(s.observeFileInfo(newer,"39949113","radio"),
                    "new native FileInfo checked");
            eq(NativeSourceGate.Choice.ORIGINAL,
                    s.atNativePrepare(newer,"39949113","radio",now+5).source,
                    "no new grant means original");
            if (i%11 == 0) {s.stop();s.start();}
        }
    }

    public static void main(String[] args) {
        stopCancelsPendingAndPreventsGrantLeaks();
        stopCannotRetractAlreadyBufferedAudio();
        invalidGrantNeverMapsDespiteMatchingSource();
        stressNextRaceAndOffSwitch();
        System.out.println("PASS: NativeReplacementLifecycle " + assertions
                + " assertions; W58 Stop, Next/radio generations, fail-closed signed audio URL");
    }
}
