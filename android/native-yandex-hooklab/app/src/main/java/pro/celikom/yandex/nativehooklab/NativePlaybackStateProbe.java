package pro.celikom.yandex.nativehooklab;

/**
 * Read-only aggregate of PUBLISHED platform MediaSession playback states.
 *
 * Distinguishes reported playback state transitions from the actual audio
 * decoder and actual user transport commands. Never records position, session,
 * mediaId, track, account, or raw PlaybackState object; does not hook audio.
 *
 * The Android framework defines PlaybackState state constants 0..11:
 * NONE, STOPPED, PAUSED, PLAYING, FAST_FORWARDING, REWINDING, BUFFERING,
 * ERROR, CONNECTING, SKIPPING_TO_PREVIOUS, SKIPPING_TO_NEXT,
 * SKIPPING_TO_QUEUE_ITEM.
 */
public final class NativePlaybackStateProbe {
    public static final int PAUSED = 2;
    public static final int PLAYING = 3;
    public static final int BUFFERING = 6;
    public static final int ERROR = 7;
    public static final int CONNECTING = 8;
    private static final long RAPID_WINDOW_MS = 2000L;

    private int lastState = -1;
    private long lastChangeMs = -1;
    private long lastSeenMs = -1;
    private long reports, transitions, repeated, pausesSoonAfterPlay,
            playsSoonAfterPause, buffersThenPauses, reportedBufferings,
            reportedErrors, timeResets, unknownStates;

    /**
     * Return only a bounded anonymous summary, never a track-specific verdict.
     * A rapid pause can be normal (user pressed pause) or a different track.
     */
    public synchronized Snapshot onPublishedState(int state, long elapsedMs) {
        if (elapsedMs < 0 || (lastSeenMs >= 0 && elapsedMs < lastSeenMs)) {
            timeResets++;
            lastState = -1;
            lastChangeMs = -1;
            lastSeenMs = elapsedMs < 0 ? -1 : elapsedMs;
            return snapshot();
        }
        lastSeenMs = elapsedMs;
        if (state < 0 || state > 11) {
            unknownStates++;
            // Do not infer transitions across a state we cannot classify.
            lastState = -1;
            lastChangeMs = -1;
            return snapshot();
        }
        reports++;
        if (state == BUFFERING) reportedBufferings++;
        if (state == ERROR) reportedErrors++;
        if (state == lastState) {
            repeated++;
            return snapshot();
        }
        boolean rapid = lastChangeMs >= 0
                && elapsedMs >= lastChangeMs
                && elapsedMs - lastChangeMs <= RAPID_WINDOW_MS;
        if (lastState >= 0) transitions++;
        if (rapid && lastState == PLAYING && state == PAUSED)
            pausesSoonAfterPlay++;
        if (rapid && lastState == PAUSED && state == PLAYING)
            playsSoonAfterPause++;
        if (rapid && lastState == BUFFERING && state == PAUSED)
            buffersThenPauses++;
        lastState = state;
        lastChangeMs = elapsedMs;
        return snapshot();
    }

    public synchronized Snapshot snapshot() {
        return new Snapshot(reports, transitions, repeated,
                pausesSoonAfterPlay, playsSoonAfterPause,
                buffersThenPauses, reportedBufferings, reportedErrors,
                timeResets, unknownStates);
    }

    public static final class Snapshot {
        public final long reports, transitions, repeated, pausesSoonAfterPlay,
                playsSoonAfterPause, buffersThenPauses, reportedBufferings,
                reportedErrors, timeResets, unknownStates;
        private Snapshot(long reports, long transitions, long repeated,
                long pausesSoonAfterPlay, long playsSoonAfterPause,
                long buffersThenPauses, long reportedBufferings,
                long reportedErrors, long timeResets, long unknownStates) {
            this.reports = reports;
            this.transitions = transitions;
            this.repeated = repeated;
            this.pausesSoonAfterPlay = pausesSoonAfterPlay;
            this.playsSoonAfterPause = playsSoonAfterPause;
            this.buffersThenPauses = buffersThenPauses;
            this.reportedBufferings = reportedBufferings;
            this.reportedErrors = reportedErrors;
            this.timeResets = timeResets;
            this.unknownStates = unknownStates;
        }
    }
}
