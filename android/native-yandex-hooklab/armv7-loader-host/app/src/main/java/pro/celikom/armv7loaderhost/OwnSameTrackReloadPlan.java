package pro.celikom.armv7loaderhost;

/**
 * W60 Windows principle applied ONLY to our synthetic Android MediaPlayer host:
 * preserve transport state while deciding whether the CURRENT source needs
 * rebuilding, instead of creating a second player or switching mid-decoder.
 *
 * This is NOT an implementation of Yandex reloadEntity on Android.
 * The target 0/1/2 represents only 440/660/330 Hz OWN WAV tone IDs.
 */
public final class OwnSameTrackReloadPlan {
    public static final class Decision {
        public final boolean reload;
        public final int targetSource, positionMs;
        public final boolean resumeAfterPrepare;
        Decision(boolean reload,int source,int positionMs,boolean resume) {
            this.reload=reload;
            this.targetSource=source;
            this.positionMs=positionMs;
            this.resumeAfterPrepare=resume;
        }
    }
    private OwnSameTrackReloadPlan() { }

    /** No track = no source/transport commands. Track B is always original. */
    public static Decision decide(int currentTrack,int existingSource,
                                  boolean celikomOn,int observedAlternativeA,
                                  int currentPositionMs,boolean wasOrShouldPlay) {
        if (currentTrack!=1 && currentTrack!=2)
            return new Decision(false,-1,0,false);
        int target=currentTrack==2 ? AudioSmokeSource.B_ORIGINAL
                : celikomOn && observedAlternativeA==AudioSmokeSource.A_ALT
                    ? AudioSmokeSource.A_ALT : AudioSmokeSource.A_ORIGINAL;
        if (existingSource==target)
            return new Decision(false,target,Math.max(0,currentPositionMs),wasOrShouldPlay);
        int safePosition=Math.max(0,Math.min(7900,currentPositionMs));
        return new Decision(true,target,safePosition,wasOrShouldPlay);
    }
}
