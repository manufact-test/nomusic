import pro.celikom.armv7loaderhost.OwnSameTrackReloadPlan;
import pro.celikom.armv7loaderhost.AudioSmokeSource;

/** JVM simulation of W60 same-current-track source refresh, OWN audio only. */
public final class OwnSameTrackReloadPlanTest {
    private static int checks;
    static void yes(boolean ok,String msg) {
        checks++;
        if(!ok)throw new AssertionError(msg+" #"+checks);
    }
    static void eq(int expected,int got,String label){
        yes(expected==got,label+" expected="+expected+" got="+got);
    }
    static void firstSwitchPreservesPauseAndPosition() {
        OwnSameTrackReloadPlan.Decision toOriginal=OwnSameTrackReloadPlan.decide(
                1,AudioSmokeSource.A_ALT,false,AudioSmokeSource.A_ORIGINAL,3560,false);
        yes(toOriginal.reload,"Stop CELIKOM on already playing A rebuilds current source");
        eq(AudioSmokeSource.A_ORIGINAL,toOriginal.targetSource,"Stop chooses original");
        eq(3560,toOriginal.positionMs,"position is preserved");
        yes(!toOriginal.resumeAfterPrepare,"paused source remains paused");
        OwnSameTrackReloadPlan.Decision toAlt=OwnSameTrackReloadPlan.decide(
                1,AudioSmokeSource.A_ORIGINAL,true,AudioSmokeSource.A_ALT,3560,false);
        yes(toAlt.reload,"Start CELIKOM on same paused A rebuilds current source");
        eq(AudioSmokeSource.A_ALT,toAlt.targetSource,"Start selects alt");
        yes(!toAlt.resumeAfterPrepare,"does not spuriously resume");
        eq(3560,toAlt.positionMs,"same track progress preserved");
    }
    static void originalOnNextAndNoPhantomAudio() {
        OwnSameTrackReloadPlan.Decision b=OwnSameTrackReloadPlan.decide(
                2,AudioSmokeSource.B_ORIGINAL,true,AudioSmokeSource.A_ALT,1000,true);
        yes(!b.reload,"ON must not replace non-approved B on Next");
        eq(AudioSmokeSource.B_ORIGINAL,b.targetSource,"B original");
        OwnSameTrackReloadPlan.Decision nothing=OwnSameTrackReloadPlan.decide(
                0,-1,true,AudioSmokeSource.A_ALT,3000,true);
        yes(!nothing.reload,"Start without a selected song does not start own player");
        eq(-1,nothing.targetSource,"no phantom source");
        yes(!nothing.resumeAfterPrepare,"no phantom playback");
    }
    static void absentModuleFailClosed() {
        OwnSameTrackReloadPlan.Decision a=OwnSameTrackReloadPlan.decide(
                1,AudioSmokeSource.A_ORIGINAL,true,AudioSmokeSource.A_ORIGINAL,
                4000,true);
        yes(!a.reload,"unhooked own app cannot claim audio source changed");
        eq(AudioSmokeSource.A_ORIGINAL,a.targetSource,"native fallback");
        OwnSameTrackReloadPlan.Decision broken=OwnSameTrackReloadPlan.decide(
                1,AudioSmokeSource.A_ORIGINAL,true,-99,4000,true);
        yes(!broken.reload,"unknown source ID is original, no alternate");
    }
    static void boundsAndSingleSource() {
        OwnSameTrackReloadPlan.Decision high=OwnSameTrackReloadPlan.decide(
                1,0,true,1,9999999,true);
        eq(7900,high.positionMs,"8 second WAV position clamped");
        yes(high.resumeAfterPrepare,"playing remains playing");
        OwnSameTrackReloadPlan.Decision low=OwnSameTrackReloadPlan.decide(
                1,1,false,0,-9,false);
        eq(0,low.positionMs,"negative progress not propagated");
        yes(!low.resumeAfterPrepare,"paused remains paused");
    }
    static void tenThousandRepeatedTogglesAndNext() {
        for(int i=0;i<10000;i++){
            int source=i%2==0?AudioSmokeSource.A_ALT:AudioSmokeSource.A_ORIGINAL;
            boolean on=i%2!=0;
            OwnSameTrackReloadPlan.Decision d=OwnSameTrackReloadPlan.decide(
                    1,source,on,AudioSmokeSource.A_ALT,i%8000,i%3==0);
            yes(d.reload,"actual different A source requires one rebuild");
            eq(on?AudioSmokeSource.A_ALT:AudioSmokeSource.A_ORIGINAL,
                    d.targetSource,"one target per toggle");
            yes(d.resumeAfterPrepare==(i%3==0),"preserves own player intent");
            OwnSameTrackReloadPlan.Decision duplicate=OwnSameTrackReloadPlan.decide(
                    1,d.targetSource,on,AudioSmokeSource.A_ALT,i%8000,i%3==0);
            yes(!duplicate.reload,"repeated same toggle has no extra player/reload");
            OwnSameTrackReloadPlan.Decision next=OwnSameTrackReloadPlan.decide(
                    2,AudioSmokeSource.B_ORIGINAL,on,AudioSmokeSource.A_ALT,i%8000,true);
            yes(!next.reload,"a prefetched unrelated B never changes source");
        }
    }
    public static void main(String[] args) {
        firstSwitchPreservesPauseAndPosition();
        originalOnNextAndNoPhantomAudio();
        absentModuleFailClosed();
        boundsAndSingleSource();
        tenThousandRepeatedTogglesAndNext();
        System.out.println("PASS: own Android/W60 source reload plan "+checks+
                " assertions; paused/position/Next/no module; no Yandex runtime");
    }
}
