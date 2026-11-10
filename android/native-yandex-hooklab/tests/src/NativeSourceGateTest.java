import pro.celikom.yandex.nativehooklab.NativeSourceGate;
import static pro.celikom.yandex.nativehooklab.NativeSourceGate.Choice;
import static pro.celikom.yandex.nativehooklab.NativeSourceGate.Stage;
import static pro.celikom.yandex.nativehooklab.NativeSourceGate.Reason;

public final class NativeSourceGateTest {
    private static int count;
    private static void eq(Object expected,Object got,String message) {
        count++; if(!expected.equals(got))
            throw new AssertionError(message+" expected="+expected+" got="+got);
    }
    private static NativeSourceGate.Candidate ready(String track,String edition) {
        return new NativeSourceGate.Candidate(track,edition,true,true,true,true,true,true);
    }
    private static NativeSourceGate.Candidate unready(String track,String edition) {
        return new NativeSourceGate.Candidate(track,edition,true,true,true,false,true,true);
    }
    private static void acceptedBeforePrepareOnly() {
        NativeSourceGate gate=new NativeSourceGate(850);
        long r=gate.beginTrack("control","edition-v1",100);
        eq(Reason.ACCEPTED,gate.propose(r,ready("control","edition-v1"),140).reason,"source admitted");
        eq(Choice.ALTERNATE,gate.prepare(r,150),"alternate prepared");
        gate.onPlay(r);gate.onPause(r);gate.onSeek(r);
        eq(Stage.PAUSED,gate.stage(),"native pause persists");
        eq(Reason.ALREADY_COMMITTED,gate.propose(r,ready("control","edition-v1"),170).reason,"no mid-play swap");
        eq(1,gate.commits(),"single source");
        gate.onDecoderFailure(r);
        eq(Choice.ALTERNATE,gate.choice(),"no automatic audible alternation after decoder failure");
        eq(Stage.FAILED,gate.stage(),"failure explicit");
    }
    private static void raskolAndDymPositionDelay() {
        for(String name:new String[]{"RASKOL-42884423","DYM-39949113"}) {
            NativeSourceGate g=new NativeSourceGate(850);
            long r=g.beginTrack(name,"owner-edition",1000);
            eq(Choice.ORIGINAL,g.prepare(r,1500),"cold original before available alternative");
            g.onPlay(r);g.onPause(r);g.onSeek(r);g.onPlay(r);
            eq(Stage.PLAYING,g.stage(),"native clock resumes; no external 3.2s session");
            eq(Reason.ALREADY_COMMITTED,g.propose(r,ready(name,"owner-edition"),4300).reason,
                "late remote observation cannot flip decoder");
            eq(1,g.commits(),"no second decoder on seek");
        }
    }
    private static void nextCancelsInflight() {
        NativeSourceGate g=new NativeSourceGate(850);
        long a=g.beginTrack("A","remix1",10);
        long b=g.beginTrack("B","remix1",50);
        eq(Reason.STALE_REVISION,g.propose(a,ready("A","remix1"),70).reason,"late previous response rejected");
        eq(Reason.WRONG_TRACK,g.propose(b,ready("A","remix1"),75).reason,"same generation wrong song rejected");
        eq(Reason.WRONG_TRACK,g.propose(b,ready("B","other-edition"),75).reason,"edition mismatch rejected");
        eq(Reason.ACCEPTED,g.propose(b,ready("B","remix1"),75).reason,"current next accepted");
        eq(Choice.ALTERNATE,g.prepare(b,80),"only correct next selected");
        eq(1,g.commits(),"one commit");
    }
    private static void notReadyOrCryptoMismatchFailClosed() {
        NativeSourceGate g=new NativeSourceGate(850);
        long r=g.beginTrack("RASKOL","exact",100);
        eq(Reason.NOT_READY,g.propose(r,unready("RASKOL","exact"),200).reason,"no sparse cold audio");
        NativeSourceGate.Candidate encrypted=new NativeSourceGate.Candidate(
            "RASKOL","exact",true,true,true,true,true,false);
        eq(Reason.NOT_READY,g.propose(r,encrypted,300).reason,"no blind stripping key/iv");
        eq(Choice.ORIGINAL,g.prepare(r,310),"no audio before ready");
        eq(1,g.commits(),"one original");
    }
    private static void lateResolveBeforePrepare() {
        NativeSourceGate g=new NativeSourceGate(850);
        long r=g.beginTrack("random","edition",100);
        eq(Reason.TOO_LATE,g.propose(r,ready("random","edition"),1100).reason,"no long delayed first join");
        eq(Choice.ORIGINAL,g.prepare(r,1200),"bounded original startup");
    }
    private static void explicitFallbackOnlyBeforePrepare() {
        NativeSourceGate g=new NativeSourceGate(850);
        long a=g.beginTrack("A","edition",0);
        eq(true,g.rejectBeforePrepare(a),"pre-prepare fail-closed");
        eq(Choice.ORIGINAL,g.prepare(a,80),"original fallback selected");
        eq(false,g.rejectBeforePrepare(a),"no late fallback crossfade");
        eq(1,g.commits(),"single native source");
    }
    private static void stressQuickNextAndStaleCallbacks() {
        NativeSourceGate g=new NativeSourceGate(850);
        for(int i=0;i<2500;i++){
            long prev=g.beginTrack("old"+i,"v",i*1000L);
            long now=g.beginTrack("next"+i,"v",i*1000L+5);
            eq(Reason.STALE_REVISION,g.propose(prev,ready("old"+i,"v"),i*1000L+9).reason,"stale");
            eq(Choice.ORIGINAL,g.prepare(now,i*1000L+16),"one current source");
            g.onSeek(prev);g.onPause(prev);g.onDecoderFailure(prev);
            eq(Stage.PREPARED,g.stage(),"old callbacks cannot affect next");
            eq(1,g.commits(),"single source per Next");
        }
    }
    private static void staleOrRejectedOffersNeverLeakAnotherTracksChoice() {
        NativeSourceGate g = new NativeSourceGate(850);
        long stale = g.beginTrack("A", "edition", 0);
        long live = g.beginTrack("B", "edition", 10);
        eq(Choice.ALTERNATE, g.propose(live, ready("B", "edition"), 20).choice,
                "B accepted independently");
        NativeSourceGate.Result old = g.propose(stale, ready("A", "edition"), 21);
        eq(Reason.STALE_REVISION, old.reason, "stale rejected");
        eq(Choice.UNDECIDED, old.choice, "stale cannot leak B alternate");
        NativeSourceGate.Result wrong = g.propose(live, ready("B", "edition"), 22);
        eq(Reason.ALREADY_COMMITTED, wrong.reason, "second offer rejected");
        eq(Choice.UNDECIDED, wrong.choice, "rejection cannot imply source switch");
        eq(Choice.ALTERNATE, g.prepare(live, 23), "live B still owns its single source");
    }
    public static void main(String[] args){
        acceptedBeforePrepareOnly();raskolAndDymPositionDelay();
        nextCancelsInflight();notReadyOrCryptoMismatchFailClosed();
        lateResolveBeforePrepare();explicitFallbackOnlyBeforePrepare();
        stressQuickNextAndStaleCallbacks();staleOrRejectedOffersNeverLeakAnotherTracksChoice();
        System.out.println("PASS: NativeSourceGate "+count+" assertions; RASKOL/DYM, startup, 2500 quick Next, pause/seek, no mid-play crossfade");
    }
}
