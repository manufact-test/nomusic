import pro.celikom.yandex.nativehooklab.NativeEventOrderProbe;

public final class NativeEventOrderProbeTest {
    private static int checks;
    private static void yes(boolean condition, String why) {
        checks++;
        if (!condition) throw new AssertionError(why + " check=" + checks);
    }
    private static void equal(Object expected, Object actual, String why) {
        yes(expected.equals(actual), why + " wanted=" + expected + " got=" + actual);
    }

    private static void basicOrderAndDuplicateMetadata() {
        NativeEventOrderProbe p = new NativeEventOrderProbe(12000);
        p.onFileInfo(100);
        equal(NativeEventOrderProbe.Verdict.SINGLE_RECENT_FILEINFO_TEMPORAL_ONLY,
                p.onMetadata(300), "one recent conversion is NOT track identity");
        equal(NativeEventOrderProbe.Verdict.METADATA_WITHOUT_RECENT_FILEINFO,
                p.onMetadata(301), "repeated metadata cannot reuse conversion");
        p.onFileInfo(400);
        p.onFileInfo(401);
        equal(NativeEventOrderProbe.Verdict.MULTIPLE_FILEINFO_AMBIGUOUS,
                p.onMetadata(450), "prefetch/radio FileInfo ambiguous");
        NativeEventOrderProbe.Snapshot s = p.snapshot();
        yes(s.fileInfoCallbacks == 3 && s.metadataCallbacks == 3,
                "event totals");
        yes(s.oneSourceWindows == 1 && s.ambiguousWindows == 1
                && s.noSourceWindows == 1, "privacy-only categories");
        yes(s.pendingSourceCountBounded == 0, "evidence consumed");
    }

    private static void timeoutsAndClockResets() {
        NativeEventOrderProbe p = new NativeEventOrderProbe(50);
        p.onFileInfo(10);
        equal(NativeEventOrderProbe.Verdict.METADATA_WITHOUT_RECENT_FILEINFO,
                p.onMetadata(61), "late source no longer usable");
        p.onFileInfo(80);
        equal(NativeEventOrderProbe.Verdict.CLOCK_DISCONTINUITY,
                p.onMetadata(70), "non-monotonic time resets evidence");
        equal(NativeEventOrderProbe.Verdict.METADATA_WITHOUT_RECENT_FILEINFO,
                p.onMetadata(72), "reset cannot create false evidence");
        p.onFileInfo(-1);
        equal(NativeEventOrderProbe.Verdict.METADATA_WITHOUT_RECENT_FILEINFO,
                p.onMetadata(10), "negative timestamp clears state");
        yes(p.snapshot().clockDiscontinuities == 2, "two discontinuities");
    }

    private static void rapidlyAlternatingRadioAndNext() {
        NativeEventOrderProbe p = new NativeEventOrderProbe(900);
        for (int i = 0; i < 12000; i++) {
            long t = i * 3000L;
            p.onFileInfo(t);
            p.onFileInfo(t+1);
            equal(NativeEventOrderProbe.Verdict.MULTIPLE_FILEINFO_AMBIGUOUS,
                    p.onMetadata(t+2), "never guess prefetched source");
            equal(NativeEventOrderProbe.Verdict.METADATA_WITHOUT_RECENT_FILEINFO,
                    p.onMetadata(t+3), "do not reuse previous track event");
            yes(p.snapshot().pendingSourceCountBounded == 0,
                    "no unbounded history");
        }
        yes(p.snapshot().ambiguousWindows == 12000, "all bursts ambiguous");
        yes(p.snapshot().oneSourceWindows == 0, "no invented identity");
    }

    private static void longPrefetchBurst() {
        NativeEventOrderProbe p = new NativeEventOrderProbe(800);
        p.onFileInfo(10);
        for (int i = 0; i < 20000; i++) p.onFileInfo(11);
        yes(p.snapshot().pendingSourceCountBounded == 2,
                "huge burst capped at two pending events");
        equal(NativeEventOrderProbe.Verdict.MULTIPLE_FILEINFO_AMBIGUOUS,
                p.onMetadata(12), "dense burst is ambiguous");
        p.onFileInfo(10000);
        equal(NativeEventOrderProbe.Verdict.METADATA_WITHOUT_RECENT_FILEINFO,
                p.onMetadata(10801), "event outside window");
        yes(p.snapshot().pendingSourceCountBounded == 0,
                "expired evidence cleared");
    }

    public static void main(String[] args) {
        basicOrderAndDuplicateMetadata();
        timeoutsAndClockResets();
        rapidlyAlternatingRadioAndNext();
        longPrefetchBurst();
        System.out.println("PASS: NativeEventOrderProbe " + checks
                + " assertions; no ID/edition/audio/decoder confidence");
    }
}
