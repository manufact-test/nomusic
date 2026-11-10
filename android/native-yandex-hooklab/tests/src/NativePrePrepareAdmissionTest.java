import pro.celikom.yandex.nativehooklab.NativePrePrepareAdmission;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;
import pro.celikom.yandex.nativehooklab.NativeTrackIdentityGate;

public final class NativePrePrepareAdmissionTest {
    private static int checks;
    private static void yes(boolean value, String why) {
        checks++;
        if (!value) throw new AssertionError(why + " assertion=" + checks);
    }
    private static void eq(Object a, Object b, String why) {
        yes(a == b || (a != null && a.equals(b)), why);
    }
    private static NativeSourceGate.Candidate ready(String song, String edition) {
        return new NativeSourceGate.Candidate(song, edition, true, true,
                true, true, true, true);
    }
    private static NativeSourceGate.Candidate unsafe(String song, String edition) {
        return new NativeSourceGate.Candidate(song, edition, true, true,
                true, false, true, true);
    }
    private static void nativeExactBeforePrepareOnly() {
        NativePrePrepareAdmission gate = new NativePrePrepareAdmission(850);
        long rev = gate.begin("42884423", "album-1", 100);
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,
                gate.offer(rev, ready("42884423", "album-1"), 101),
                "candidate only pending; never starts second clock");
        yes(gate.observeFileInfo(rev, "42884423", "album-1"), "trusted request observed");
        NativePrePrepareAdmission.Decision d =
                gate.commitAtNativePrepare(rev, "42884423", "album-1", 150);
        yes(d.applyOnce && d.readyToPrepare, "exactly one native prepare");
        eq(d.source, NativeSourceGate.Choice.ALTERNATE, "alternate before decoder prepare");
        eq(d.identity, NativeTrackIdentityGate.Verdict.MATCH, "track and edition exact");
        yes(!gate.commitAtNativePrepare(rev, "42884423", "album-1", 160).applyOnce,
                "duplicate prepare must not apply");
        eq(NativePrePrepareAdmission.Offer.REJECTED,
                gate.offer(rev, ready("42884423", "album-1"), 200), "late replacement rejected");
        gate.onPlay(rev);
        gate.onSeek(rev);
        gate.onPause(rev);
        eq(gate.committedSourceDecisions(), 1, "single media source decision");
    }
    private static void blockedIdentityAlwaysOriginal() {
        NativePrePrepareAdmission gate = new NativePrePrepareAdmission(850);
        long rev = gate.begin("39949113", "studio", 1);
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,
                gate.offer(rev, ready("39949113", "studio"), 2), "candidate pending");
        yes(gate.observeFileInfo(rev, "39949113", "studio"), "fileinfo verified");
        NativePrePrepareAdmission.Decision other =
                gate.commitAtNativePrepare(rev, "39949113", "radio", 3);
        eq(other.source, NativeSourceGate.Choice.ORIGINAL, "different edition never replaced");
        eq(other.identity, NativeTrackIdentityGate.Verdict.ORIGINAL_MISMATCH,
                "proof of different edition");
        eq(gate.committedSourceDecisions(), 1, "one original decision");
        long rev2 = gate.begin("39949113", "studio", 5);
        gate.offer(rev2, ready("39949113", "studio"), 6);
        NativePrePrepareAdmission.Decision absent =
                gate.commitAtNativePrepare(rev2, "39949113", "studio", 7);
        eq(absent.source, NativeSourceGate.Choice.ORIGINAL,
                "no observed native fileinfo, no replacement");
        eq(absent.identity, NativeTrackIdentityGate.Verdict.ORIGINAL_UNPROVEN,
                "unknown fileinfo remains unknown");
        long rev3 = gate.begin(null, null, 8);
        eq(NativePrePrepareAdmission.Offer.REJECTED,
                gate.offer(rev3, ready("x", "y"), 9), "missing initial identity not accepted");
        yes(gate.commitAtNativePrepare(rev3, null, null, 10).applyOnce,
                "unknown track still permits ORIGINAL prepare");
        eq(gate.committedSourceDecisions(), 1, "unknown source decides once");
        long rev4 = gate.begin("39949113", " ", 11);
        eq(NativePrePrepareAdmission.Offer.REJECTED,
                gate.offer(rev4, ready("39949113", " "), 12),
                "blank edition never approved");
        eq(gate.commitAtNativePrepare(rev4, "39949113", " ", 13).source,
                NativeSourceGate.Choice.ORIGINAL, "invalid edition keeps original");
    }
    private static void raceNextAndUnsafe() {
        NativePrePrepareAdmission g = new NativePrePrepareAdmission(850);
        for (int i = 0; i < 5000; i++) {
            long start = i * 2000L;
            long stale = g.begin("track-" + i, "v1", start);
            long now = g.begin("next-" + i, "v2", start + 4);
            yes(!g.observeFileInfo(stale, "track-" + i, "v1"),
                "stale observer rejected");
            eq(g.offer(stale, ready("track-" + i, "v1"), start + 6),
                    NativePrePrepareAdmission.Offer.STALE, "old answer cannot queue");
            yes(!g.commitAtNativePrepare(stale, "track-" + i, "v1", start + 7).applyOnce,
                    "old decoder never commits");
            yes(g.observeFileInfo(now, "next-" + i, "v2"), "current native ID");
            eq(g.offer(now, unsafe("next-" + i, "v2"), start + 8),
                    NativePrePrepareAdmission.Offer.REJECTED, "unsafe source rejected");
            eq(g.commitAtNativePrepare(now, "next-" + i, "v2", start + 9).source,
                    NativeSourceGate.Choice.ORIGINAL, "original when alternate unsafe");
            g.onPlay(stale);
            g.onPause(stale);
            g.onSeek(stale);
            eq(g.committedSourceDecisions(), 1, "one source after rapid next");
        }
    }
    private static void deadlineAndAbort() {
        NativePrePrepareAdmission g = new NativePrePrepareAdmission(850);
        long a = g.begin("normal", "album-1", 100);
        yes(g.observeFileInfo(a, "normal", "album-1"), "fileinfo");
        g.offer(a, ready("normal", "album-1"), 120);
        eq(g.commitAtNativePrepare(a, "normal", "album-1", 1000).source,
                NativeSourceGate.Choice.ORIGINAL, "candidate expired before native prepare");
        long b = g.begin("normal", "album-1", 2000);
        g.abort(b);
        yes(!g.commitAtNativePrepare(b, "normal", "album-1", 2001).applyOnce,
                "abort must never prepare");
        long c = g.begin("new", "album", 3000);
        yes(g.observeFileInfo(c, "new", "album"), "new selection unaffected");
        g.offer(c, ready("new", "album"), 3001);
        eq(g.commitAtNativePrepare(c, "new", "album", 3002).source,
                NativeSourceGate.Choice.ALTERNATE, "new selection can prepare alternate");
        eq(g.committedSourceDecisions(), 1, "one successful commit");
    }
    private static void conflictingFileInfoAndSafeOneCommit() {
        NativePrePrepareAdmission gate = new NativePrePrepareAdmission(850);
        long rev = gate.begin("42884423", "version-1", 10);
        eq(NativePrePrepareAdmission.Offer.ACCEPTED_PENDING,
                gate.offer(rev, ready("42884423", "version-1"), 11), "pending");
        yes(gate.observeFileInfo(rev, "42884423", "version-1"),
                "first fileinfo matches");
        yes(!gate.observeFileInfo(rev, "42884423", "version-2"),
                "conflicting native edition rejected");
        NativePrePrepareAdmission.Decision d =
                gate.commitAtNativePrepare(rev, "42884423", "version-1", 13);
        eq(d.source, NativeSourceGate.Choice.ORIGINAL,
                "conflicting identity vetoes already queued alternate");
        eq(d.identity, NativeTrackIdentityGate.Verdict.ORIGINAL_MISMATCH,
                "conflict irreversible for this generation");
        eq(gate.committedSourceDecisions(), 1, "exactly one prepare");
    }
    public static void main(String[] args) {
        nativeExactBeforePrepareOnly();
        blockedIdentityAlwaysOriginal();
        raceNextAndUnsafe();
        deadlineAndAbort();
        conflictingFileInfoAndSafeOneCommit();
        System.out.println("PASS: NativePrePrepareAdmission MODEL " + checks
                + " assertions; same-generation FileInfo→decoder identity, no double clock,"
                + " 5000 Next races, missing edition, unsafe/late candidate and abort");
    }
}
