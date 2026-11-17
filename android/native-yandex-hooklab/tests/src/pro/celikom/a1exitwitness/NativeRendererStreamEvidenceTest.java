package pro.celikom.a1exitwitness;

public final class NativeRendererStreamEvidenceTest {
    private static void check(boolean assertion,String code) {
        if(!assertion)throw new AssertionError(code);
    }
    private static boolean contains(String[] lines,String piece) {
        for(String x:lines)if(x.contains(piece))return true;
        return false;
    }
    private static void testAttachmentAndRealReadAlias() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object renderer=new Object(),holder=new Object(),stream=new Object();
        NativeRendererStreamEvidence.Scope scope=e.enter(renderer,holder);
        try { e.onAttach(renderer,stream); }
        finally { e.exit(scope); }
        check(e.shouldSampleRead(),"FIRST_SAMPLING");
        e.onRead(renderer,stream);
        check(contains(e.exportLines(),"origin=QUEUED_HOLDER_ATTACHED;error=ONE"),
              "EXPECTED_PAIRED_ATTACHMENT");
        check(contains(e.exportLines(),"origin=ATTACHED_STREAM_READ_MATCH;error=ONE"),
              "EXPECTED_STREAM_MATCH");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "STATIC_NOT_AUDIO_PASS");
        for(int i=1;i<8;i++) check(e.shouldSampleRead(),"READ_BUDGET_MISSING");
        check(!e.shouldSampleRead(),"READ_BUDGET_NOT_CAPPED");
    }
    private static void testDetachesAndReattachmentAcrossNext() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object renderer=new Object();
        Object holderA=new Object(),holderB=new Object();
        Object streamA=new Object(),streamB=new Object();
        NativeRendererStreamEvidence.Scope a=e.enter(renderer,holderA);
        try {e.onAttach(renderer,streamA);}
        finally{e.exit(a);}
        NativeRendererStreamEvidence.Scope b=e.enter(renderer,holderB);
        try {e.onAttach(renderer,streamB);}
        finally{e.exit(b);}
        check(e.shouldSampleRead(),"NEXT_BUDGET_RESET");
        e.onRead(renderer,streamA);
        check(contains(e.exportLines(),"origin=STREAM_REATTACH_TRANSITION;error=ONE"),
              "NEXT_TRANSITION_CATEGORY");
        check(contains(e.exportLines(),"origin=ATTACHED_STREAM_READ_DIFFERENT;error=ONE"),
              "STALE_READ_NOT_TRUSTED");
        e.onRead(renderer,streamB);
        e.onDetach(renderer);
        e.onRead(renderer,streamB);
        check(contains(e.exportLines(),"origin=READ_NO_MATCHED_ATTACHMENT;error=ONE"),
              "DETACHED_STREAM_CANNOT_PASS");
    }
    private static void testUnscopedAndPoisonedStack() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object renderer=new Object(),stream=new Object();
        e.onAttach(renderer,stream);
        check(contains(e.exportLines(),"origin=UNSCOPED_ATTACH;error=ONE"),
              "UNSCOPED_ATTACH_MUST_NOT_PASS");
        NativeRendererStreamEvidence.Scope outer=e.enter(renderer,new Object());
        NativeRendererStreamEvidence.Scope inner=e.enter(renderer,new Object());
        e.exit(outer);
        e.exit(inner);
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=INVALID"),
              "BAD_LIFETIME_MUST_POISON");
        check(!e.shouldSampleRead(),"POISONED_SAMPLE_MUST_NOT_RUN");
    }
    private static void testNoPrivateValuesInReport() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object renderer=new Object();
        NativeRendererStreamEvidence.Scope scope=e.enter(renderer,new Object());
        try {e.onAttach(renderer,new Object());}
        finally{e.exit(scope);}
        String text=String.join("\n",e.exportLines());
        check(!text.contains("@"),"OBJECT_REFERENCE_LEAK");
        check(!text.contains("http"),"URL_LEAK");
        check(!text.contains("track"),"TRACK_LEAK");
        check(!text.contains("java.lang"),"CLASS_LEAK");
    }
    public static void main(String[] args) {
        testAttachmentAndRealReadAlias();
        testDetachesAndReattachmentAcrossNext();
        testUnscopedAndPoisonedStack();
        testNoPrivateValuesInReport();
        System.out.println("NATIVE_RENDERER_READONLY_EVIDENCE_MODEL_PASS");
    }
}
