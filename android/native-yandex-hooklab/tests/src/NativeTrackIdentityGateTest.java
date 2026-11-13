package pro.celikom.yandex.nativehooklab;

/** JVM-only identity gate regression; NOT audio/Yandex hook/runtime proof. */
public final class NativeTrackIdentityGateTest {
    private static int assertions;
    private static void yes(boolean value) {
        assertions++;
        if (!value) throw new AssertionError("identity invariant #" + assertions);
    }
    private static void eq(Object a, Object b) { yes(a.equals(b)); }

    public static void main(String[] args) {
        NativeTrackIdentityGate g = new NativeTrackIdentityGate();
        long raskol = g.beginNativeTrack("42884423", "77", "original-edition");
        yes(g.observeFileInfo(raskol, "42884423", "77", "original-edition"));
        eq(g.sealAtNativePrepare(raskol, "42884423", "77", "original-edition"),
            NativeTrackIdentityGate.Verdict.MATCH);
        eq(g.sealAtNativePrepare(raskol, "42884423", "77", "original-edition"),
            NativeTrackIdentityGate.Verdict.ORIGINAL_DUPLICATE);

        long dym = g.beginNativeTrack("39949113", "88", "live-edition");
        yes(!g.observeFileInfo(raskol, "42884423", "77", "original-edition"));
        yes(g.observeFileInfo(dym, "39949113", "88", "live-edition"));
        eq(g.sealAtNativePrepare(dym, "39949113", "99", "live-edition"),
            NativeTrackIdentityGate.Verdict.ORIGINAL_MISMATCH);

        long unknown = g.beginNativeTrack(null, null, null);
        yes(!g.observeFileInfo(unknown, null, null, null));
        eq(g.sealAtNativePrepare(unknown, null, null, null),
            NativeTrackIdentityGate.Verdict.ORIGINAL_UNPROVEN);

        long mismatched = g.beginNativeTrack("111", "77", "studio");
        yes(!g.observeFileInfo(mismatched, "112", "77", "studio"));
        yes(!g.observeFileInfo(mismatched, "111", "88", "studio"));
        eq(g.sealAtNativePrepare(mismatched, "111", "77", "studio"),
            NativeTrackIdentityGate.Verdict.ORIGINAL_MISMATCH);

        long badEdition = g.beginNativeTrack("100", "77", " ");
        yes(!g.observeFileInfo(badEdition, "100", "77", " "));
        eq(g.sealAtNativePrepare(badEdition, "100", "77", " "),
            NativeTrackIdentityGate.Verdict.ORIGINAL_UNPROVEN);

        long aborted = g.beginNativeTrack("222", "77", "edition");
        yes(g.observeFileInfo(aborted, "222", "77", "edition"));
        g.invalidate(aborted);
        eq(g.sealAtNativePrepare(aborted, "222", "77", "edition"),
            NativeTrackIdentityGate.Verdict.ORIGINAL_STALE);

        for (int i = 0; i < 2500; i++) {
            long before = g.beginNativeTrack("" + (100000 + i), "77", "edition-a");
            long after = g.beginNativeTrack("" + (100001 + i), "77", "edition-b");
            yes(!g.observeFileInfo(before, "" + (100000 + i), "77", "edition-a"));
            yes(g.observeFileInfo(after, "" + (100001 + i), "77", "edition-b"));
            eq(g.sealAtNativePrepare(before, "" + (100000 + i), "77", "edition-a"),
                NativeTrackIdentityGate.Verdict.ORIGINAL_STALE);
            eq(g.sealAtNativePrepare(after, "" + (100001 + i), "77", "edition-b"),
                NativeTrackIdentityGate.Verdict.MATCH);
        }
        System.out.println("NATIVE_TRACK_IDENTITY_GATE_PASS assertions=" + assertions
            + " (MODEL ONLY; track+album+edition)");
    }
}
