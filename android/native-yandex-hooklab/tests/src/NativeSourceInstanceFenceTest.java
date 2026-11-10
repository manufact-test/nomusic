import pro.celikom.yandex.nativehooklab.NativeSourceInstanceFence;
import pro.celikom.yandex.nativehooklab.NativeSourceInstanceFence.Verdict;
import pro.celikom.yandex.nativehooklab.NativeSourceInstanceFence.Phase;

import java.util.Random;

/**
 * Only OWN-OBJECT synthetic lifecycle proofs. There are no Yandex classes,
 * no decoder, network, audio, track metadata or actual playback here.
 */
public final class NativeSourceInstanceFenceTest {
    private static int checks;
    private static final class SameEquals {
        @Override public boolean equals(Object other) { return other instanceof SameEquals; }
        @Override public int hashCode() { return 1; }
    }
    private static void yes(boolean ok,String why){
        checks++;if(!ok)throw new AssertionError(why+" assertion="+checks);
    }
    private static void eq(Object expected,Object got,String why) {
        yes(expected==got || (expected!=null&&expected.equals(got)),
                why+" expected="+expected+" actual="+got);
    }
    private static final class Fixture {
        final NativeSourceInstanceFence fence=new NativeSourceInstanceFence();
        final Object selection=new SameEquals(),owner=new SameEquals(),
                reader=new SameEquals(),loader=new SameEquals(),
                task=new SameEquals(),spec=new SameEquals();
        long epoch;
        void begin(long at){epoch=fence.begin(selection,at);}
        void bind(long at){
            eq(Verdict.RECORDED,fence.sourceBound(epoch,selection,owner,reader,at),
                    "factory binds same selected source");
        }
        void prepare(long at){
            eq(Verdict.RECORDED,fence.descriptorBeforePrepare(epoch,selection,owner,reader,at),
                    "one synthetic trusted descriptor");
        }
        void schedule(long at){
            eq(Verdict.RECORDED,fence.scheduled(epoch,owner,loader,task,at),
                    "task linked to source owner");
        }
        void dispatch(long at){
            eq(Verdict.RECORDED,fence.dispatched(epoch,owner,loader,task,at),
                    "same task executed");
        }
        void open(long at){
            eq(Verdict.RECORDED,fence.opened(epoch,loader,reader,spec,at),
                    "same instance open");
        }
        void read(long at){
            eq(Verdict.RECORDED,fence.read(epoch,loader,reader,spec,512,at),
                    "same instance read");
        }
        void close(long at){
            eq(Verdict.RECORDED,fence.closed(epoch,loader,reader,at),
                    "same instance closed");
        }
        void ready(long at){
            begin(at);bind(at+1);prepare(at+2);
            schedule(at+3);dispatch(at+4);
        }
        void full(long at){
            ready(at);open(at+5);read(at+6);close(at+7);
        }
    }

    private static void completeSequenceIsOnlySyntheticWitness() {
        Fixture f=new Fixture();
        f.full(100);
        NativeSourceInstanceFence.Snapshot s=f.fence.snapshot();
        eq(Phase.CLOSED,s.phase,"closed");
        yes(s.syntheticSequenceComplete,"own in-memory events observed");
        eq(1,s.prepareCount,"exactly one synthetic prepare");
        eq(1,s.openCount,"one open");
        eq(1,s.readCount,"one nonzero read");
        eq(1,s.closeCount,"one close");
        eq(0,s.rejectedCount,"no rejects");
        eq(Verdict.OUT_OF_ORDER,f.fence.opened(f.epoch,f.loader,f.reader,f.spec,109),
                "cannot reopen without seek");
        eq(Verdict.OUT_OF_ORDER,
                f.fence.descriptorBeforePrepare(f.epoch,f.selection,f.owner,f.reader,110),
                "cannot double prepare");
        eq(1,f.fence.snapshot().prepareCount,"no second decision");
        yes(!f.fence.snapshot().syntheticSequenceComplete,
                "a rejected event makes whole observed epoch unfit for causal proof");
    }

    private static void sameEqualsDoesNotMeanSameInstance() {
        Fixture f=new Fixture();
        f.begin(1);
        // Every two SameEquals objects compare equal, but are distinct refs.
        yes(f.selection.equals(f.owner),"test tokens deliberately equals()");
        eq(Verdict.IDENTITY_CONFLICT,
                f.fence.sourceBound(f.epoch,new SameEquals(),f.owner,f.reader,2),
                "reference equality must reject spoofed source");
        eq(Phase.INVALIDATED,f.fence.snapshot().phase,"poison current epoch");
        yes(!f.fence.snapshot().syntheticSequenceComplete,"no false proof");
    }

    private static void staleCallbacksAndRecycledHandlesCannotRearmNewEpoch() {
        Fixture f=new Fixture();
        f.full(100);
        long old=f.epoch;
        f.begin(200);
        eq(Verdict.STALE,f.fence.closed(old,f.loader,f.reader,201),
                "late old close must not change new epoch");
        eq(Verdict.STALE,f.fence.sourceBound(old,f.selection,f.owner,f.reader,202),
                "old source cannot bind new epoch");
        eq(Phase.SELECTED,f.fence.snapshot().phase,"new selection survives old callbacks");
        f.bind(203);f.prepare(204);f.schedule(205);f.dispatch(206);
        f.open(207);f.read(208);f.close(209);
        yes(f.fence.snapshot().syntheticSequenceComplete,"new source independent");
    }

    private static void wrongTaskOrLoaderPoisonsCurrentGenerationOnly() {
        Fixture f=new Fixture();
        f.begin(100);f.bind(101);f.prepare(102);f.schedule(103);
        eq(Verdict.IDENTITY_CONFLICT,
                f.fence.dispatched(f.epoch,f.owner,f.loader,new SameEquals(),104),
                "different task with same equals() is not original task");
        eq(Phase.INVALIDATED,f.fence.snapshot().phase,"mismatch sealed");
        yes(!f.fence.snapshot().syntheticSequenceComplete,"no audio claim");
        f.full(200);
        yes(f.fence.snapshot().syntheticSequenceComplete,
                "new generation after poison is independent");
    }

    private static void sourcePrePrepareCannotFollowReadAndUnknownNotAccepted() {
        Fixture f=new Fixture();
        f.begin(1);
        eq(Verdict.OUT_OF_ORDER,
                f.fence.opened(f.epoch,f.loader,f.reader,f.spec,2),
                "open before factory cannot be retroactively attributed");
        eq(Verdict.OUT_OF_ORDER,
                f.fence.scheduled(f.epoch,f.owner,f.loader,f.task,3),
                "unscheduled source unknown");
        f.bind(4);
        eq(Verdict.OUT_OF_ORDER,
                f.fence.dispatched(f.epoch,f.owner,f.loader,f.task,5),
                "execute before selected prepare cannot count");
        f.prepare(6);f.schedule(7);f.dispatch(8);f.open(9);
        eq(Verdict.OUT_OF_ORDER,
                f.fence.read(f.epoch,f.loader,f.reader,f.spec,-2,10),
                "negative read count invalid");
        f.read(11);f.close(12);
        yes(!f.fence.snapshot().syntheticSequenceComplete,
                "old invalid observation cannot be rehabilitated by later calls");
        eq(3,f.fence.snapshot().rejectedCount,
                "two out-of-order calls and invalid negative byte count recorded");
        Fixture unknown=new Fixture();
        long missing=unknown.fence.begin(null,10);
        eq(Phase.INVALIDATED,unknown.fence.snapshot().phase,"null selection unavailable");
        eq(Verdict.ALREADY_SEALED,
                unknown.fence.sourceBound(missing,unknown.selection,unknown.owner,unknown.reader,11),
                "missing selected source fail-closed");
    }

    private static void seekReopenSameSourceWithoutSecondPrepare() {
        Fixture f=new Fixture();
        f.ready(100);f.open(105);f.read(106);
        eq(Verdict.RECORDED,f.fence.seek(f.epoch,f.owner,107),
                "seek is same selection, not second source commit");
        f.close(108);
        f.open(109);f.read(110);f.close(111);
        NativeSourceInstanceFence.Snapshot snap=f.fence.snapshot();
        eq(1,snap.prepareCount,"one prepare across seeks");
        eq(2,snap.openCount,"two opens");
        eq(2,snap.readCount,"two observed byte reads");
        eq(2,snap.closeCount,"two closes");
        eq(1,snap.seekCount,"one seek");
        yes(snap.syntheticSequenceComplete,"synthetic successful seek reopen");
    }

    private static void abortStopAndClockReset() {
        Fixture f=new Fixture();
        f.ready(100);
        f.fence.abort(f.epoch);
        eq(Verdict.ALREADY_SEALED,f.fence.opened(f.epoch,f.loader,f.reader,f.spec,105),
                "Stop cancels pending original task");
        f.begin(300);f.bind(301);
        eq(Verdict.CLOCK_INVALID,
                f.fence.descriptorBeforePrepare(f.epoch,f.selection,f.owner,f.reader,200),
                "backwards monotonic clock must poison");
        eq(Phase.INVALIDATED,f.fence.snapshot().phase,"clock invalidates source proof");
        yes(!f.fence.snapshot().syntheticSequenceComplete,"no false success");
    }

    private static void stressRadioNextReorderAndSameIdReplay() {
        Fixture f=new Fixture();
        Random random=new Random(0xCE11C0AL);
        long time=1000;
        for(int i=0;i<5000;i++){
            long old=f.epoch;
            f.begin(time);
            if(i>0) {
                eq(Verdict.STALE,
                        f.fence.scheduled(old,f.owner,f.loader,f.task,time+1),
                        "old Next/radio task cannot enter active epoch");
                eq(Verdict.STALE,
                        f.fence.opened(old,f.loader,f.reader,f.spec,time+2),
                        "old open cannot enter active epoch");
            }
            f.bind(time+3);f.prepare(time+4);
            if((random.nextInt(7)==0)){
                f.fence.abort(f.epoch);
                eq(Phase.INVALIDATED,f.fence.snapshot().phase,"random Stop");
            } else {
                f.schedule(time+5);f.dispatch(time+6);
                f.open(time+7);
                if(random.nextBoolean()) {
                    f.read(time+8);
                    f.close(time+9);
                    yes(f.fence.snapshot().syntheticSequenceComplete,"read completed");
                } else {
                    f.close(time+9);
                    yes(!f.fence.snapshot().syntheticSequenceComplete,
                            "open+close without bytes not a successful read");
                }
            }
            time+=20;
        }
    }

    public static void main(String[] args){
        completeSequenceIsOnlySyntheticWitness();
        sameEqualsDoesNotMeanSameInstance();
        staleCallbacksAndRecycledHandlesCannotRearmNewEpoch();
        wrongTaskOrLoaderPoisonsCurrentGenerationOnly();
        sourcePrePrepareCannotFollowReadAndUnknownNotAccepted();
        seekReopenSameSourceWithoutSecondPrepare();
        abortStopAndClockReset();
        stressRadioNextReorderAndSameIdReplay();
        System.out.println("PASS: NativeSourceInstanceFence "+checks
                +" OWN-ONLY assertions; exact object refs, 5000 Next/radio races,"
                +" seek reopen, Stop and clock rollback; NOT Yandex playback");
    }
}
