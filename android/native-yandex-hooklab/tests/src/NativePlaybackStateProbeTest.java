import pro.celikom.yandex.nativehooklab.NativePlaybackStateProbe;

/** Deterministic tests, never uses a real Yandex app or Android state object. */
public final class NativePlaybackStateProbeTest {
    private static int checks;
    private static void yes(boolean v, String why) {
        checks++;
        if (!v) throw new AssertionError(why + ": #" + checks);
    }

    private static void rapidReportedPlayPausePattern() {
        NativePlaybackStateProbe p = new NativePlaybackStateProbe();
        p.onPublishedState(3, 100);
        p.onPublishedState(2, 110);
        p.onPublishedState(3, 250);
        p.onPublishedState(2, 300);
        NativePlaybackStateProbe.Snapshot s = p.snapshot();
        yes(s.reports == 4 && s.transitions == 3, "transitions counted");
        yes(s.pausesSoonAfterPlay == 2, "two rapid reported pauses");
        yes(s.playsSoonAfterPause == 1, "rapid re-play counted");
        yes(s.reportedErrors == 0 && s.reportedBufferings == 0, "no inferred errors");
        p.onPublishedState(2, 305);
        yes(p.snapshot().repeated == 1, "repeat state not counted as transition");
    }

    private static void bufferingAndLongPauses() {
        NativePlaybackStateProbe p = new NativePlaybackStateProbe();
        p.onPublishedState(3, 10);
        p.onPublishedState(6, 20);
        p.onPublishedState(2, 30);
        p.onPublishedState(3, 10000);
        p.onPublishedState(2, 13000);
        p.onPublishedState(7, 13100);
        NativePlaybackStateProbe.Snapshot s=p.snapshot();
        yes(s.reportedBufferings == 1 && s.buffersThenPauses == 1, "buffering then pause");
        yes(s.pausesSoonAfterPlay == 0, "long playback not rapid");
        yes(s.playsSoonAfterPause == 0, "long resume not rapid");
        yes(s.reportedErrors == 1, "error only if actual state ERROR");
    }

    private static void skipUnknownAndClockReset() {
        NativePlaybackStateProbe p = new NativePlaybackStateProbe();
        p.onPublishedState(3, 100);
        p.onPublishedState(23, 110);
        p.onPublishedState(2, 120);
        yes(p.snapshot().unknownStates == 1, "unknown platform state");
        yes(p.snapshot().pausesSoonAfterPlay == 0, "unknown cannot bridge rapid pair");
        p.onPublishedState(3, 70);
        p.onPublishedState(2, 75);
        yes(p.snapshot().timeResets == 1, "clock reversal invalidates previous state");
        yes(p.snapshot().pausesSoonAfterPlay == 1, "fresh post-reset pair allowed");
        p.onPublishedState(3, -1);
        yes(p.snapshot().timeResets == 2, "negative clock also invalidates state");
    }

    private static void radioBurstsNoUnboundedHistory() {
        NativePlaybackStateProbe p = new NativePlaybackStateProbe();
        for (int i=0; i<12000; i++) {
            long t=i * 5000L;
            p.onPublishedState(6, t);
            p.onPublishedState(3, t+200);
            p.onPublishedState(2, t+300);
            p.onPublishedState(3, t+3300);
        }
        NativePlaybackStateProbe.Snapshot s = p.snapshot();
        yes(s.reports == 48000, "48k published states only");
        yes(s.pausesSoonAfterPlay == 12000, "rapid within burst");
        yes(s.playsSoonAfterPause == 0, "late restart excluded");
        yes(s.reportedBufferings == 12000, "count buffering");
        yes(s.reportedErrors == 0 && s.timeResets == 0, "no phantom failures");
    }

    public static void main(String[] args) {
        rapidReportedPlayPausePattern();
        bufferingAndLongPauses();
        skipUnknownAndClockReset();
        radioBurstsNoUnboundedHistory();
        System.out.println("PASS: NativePlaybackStateProbe " + checks
                + " assertions, 48k state updates; published states only, no decoder or track identity");
    }
}
