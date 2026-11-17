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
    private static void testUnscopedReadNeverAttestsQueueHolder() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object renderer=new Object(),stream=new Object();
        e.onAttach(renderer,stream); // no mQ8.catch scope observed
        check(e.shouldSampleRead(),"UNSCOPED_READ_BUDGET");
        e.onRead(renderer,stream);
        check(contains(e.exportLines(),
                "origin=UNSCOPED_ATTACHED_STREAM_READ_MATCH;error=ONE"),
              "UNSCOPED_RENDERER_STREAM_ALIAS");
        check(contains(e.exportLines(),"origin=QUEUED_HOLDER_ATTACHED;error=NONE"),
              "UNSCOPED_MUST_NOT_INVENT_QUEUE");
        check(contains(e.exportLines(),"origin=ATTACHED_STREAM_READ_MATCH;error=NONE"),
              "UNSCOPED_MUST_NOT_COUNT_STRONG_MATCH");
        e.onRead(renderer,new Object());
        check(contains(e.exportLines(),
                "origin=UNSCOPED_ATTACHED_STREAM_READ_DIFFERENT;error=ONE"),
              "UNSCOPED_DIFFERENT_STREAM");
        e.onDetach(renderer);
        e.onRead(renderer,stream);
        check(contains(e.exportLines(),"origin=READ_NO_MATCHED_ATTACHMENT;error=ONE"),
              "UNSCOPED_DETACH_DROPS_ALIAS");
    }
    private static void testEarlyReadBudgetMustNotHideLaterUnscopedAttach() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        for(int i=0;i<8;i++)check(e.shouldSampleRead(),"EARLY_READ");
        check(!e.shouldSampleRead(),"EARLY_READ_LIMIT");
        Object renderer=new Object(),stream=new Object();
        e.onAttach(renderer,stream);
        check(e.shouldSampleRead(),"REARM_AFTER_UNSCOPED_ATTACH");
        e.onRead(renderer,stream);
        check(contains(e.exportLines(),
                "origin=UNSCOPED_ATTACHED_STREAM_READ_MATCH;error=ONE"),
              "LATE_VALID_RENDERER_READ");
    }
    private static void testRegistrationSurvivesTrimmedEventLog() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        check(contains(e.exportLines(),
            "origin=QUEUE_SCOPE;error=NOT_SEEN"),"DEFAULT_UNOBSERVED");
        e.onHookRegistration("QUEUE_SCOPE",false);
        e.onHookRegistration("STREAM_ATTACH",true);
        e.onHookRegistration("SAMPLE_READ",true);
        e.onHookRegistration("STREAM_DETACH",true);
        check(contains(e.exportLines(),"origin=QUEUE_SCOPE;error=NO_HOOK"),
              "HOOK_INSTALL_FAILURE_SNAPSHOT");
        check(contains(e.exportLines(),"origin=STREAM_ATTACH;error=REGISTERED"),
              "HOOK_INSTALL_SUCCESS_SNAPSHOT");
    }
    private static void testRealReturnCodesNeverInferAudibleTrack() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object renderer=new Object(),stream=new Object();
        e.onAttach(renderer,stream); // no queue-holder proof, like NAV19 owner
        e.onReadReturn(renderer,stream,-4);
        e.onReadReturn(renderer,stream,-5);
        e.onReadReturn(renderer,stream,-3);
        e.onReadReturn(renderer,stream,0);
        check(contains(e.exportLines(),
            "origin=STREAM_ALIASED_READ_RETURN_MINUS4;error=ONE"),
            "RETURN_CODE_MINUS4");
        check(contains(e.exportLines(),
            "origin=STREAM_ALIASED_READ_RETURN_MINUS5;error=ONE"),
            "RETURN_CODE_MINUS5");
        check(contains(e.exportLines(),
            "origin=STREAM_ALIASED_READ_RETURN_MINUS3;error=ONE"),
            "RETURN_CODE_MINUS3");
        check(contains(e.exportLines(),
            "origin=STREAM_ALIASED_READ_RETURN_OTHER;error=ONE"),
            "RETURN_CODE_OTHER");
        check(contains(e.exportLines(),
            "origin=QUEUED_HOLDER_ATTACHED;error=NONE"),
            "RETURN_IS_NOT_QUEUE_IDENTITY");
        e.onReadReturn(renderer,new Object(),-4);
        e.onDetach(renderer);
        e.onReadReturn(renderer,stream,-4);
        check(contains(e.exportLines(),
            "origin=READ_RETURN_LINK_LOST;error=FEW"),
            "STALE_STREAM_RETURN_MUST_NOT_COUNT");
        check(contains(e.exportLines(),
            "origin=STREAM_ALIASED_READ_RETURN_MINUS4;error=ONE"),
            "STALE_STREAM_MUST_NOT_INCREASE_MINUS4");
    }
    private static void testScopedAndUnscopedReturnsNeverMix() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object strongRenderer=new Object(),strongHolder=new Object(),strongStream=new Object();
        Object weakRenderer=new Object(),weakStream=new Object();
        NativeRendererStreamEvidence.Scope scope=e.enter(strongRenderer,strongHolder);
        try {e.onAttach(strongRenderer,strongStream);} finally {e.exit(scope);}
        e.onAttach(weakRenderer,weakStream);
        e.onReadReturn(strongRenderer,strongStream,-4);
        e.onReadReturn(strongRenderer,strongStream,-5);
        e.onReadReturn(strongRenderer,strongStream,-3);
        e.onReadReturn(strongRenderer,strongStream,0);
        e.onReadReturn(weakRenderer,weakStream,-4);
        e.onReadReturn(weakRenderer,weakStream,-5);
        e.onReadReturn(weakRenderer,weakStream,-3);
        e.onReadReturn(weakRenderer,weakStream,0);
        String[] snap=e.exportLines();
        String[] returns={"MINUS4","MINUS5","MINUS3","OTHER"};
        for(String code:returns){
            check(contains(snap,"origin=QUEUE_SCOPED_READ_RETURN_"+code+";error=ONE"),
                  "STRONG_COHORT_"+code);
            check(contains(snap,"origin=UNSCOPED_READ_RETURN_"+code+";error=ONE"),
                  "WEAK_COHORT_"+code);
        }
        check(contains(snap,"origin=STREAM_ALIASED_READ_RETURN_MINUS4;error=FEW"),
              "AGGREGATE_PRESERVED");
        e.onDetach(strongRenderer);
        e.onReadReturn(strongRenderer,strongStream,-4);
        snap=e.exportLines();
        check(contains(snap,"origin=QUEUE_SCOPED_READ_RETURN_MINUS4;error=ONE"),
              "DETACHED_STRONG_NOT_COUNTED");
        check(contains(snap,"origin=READ_RETURN_LINK_LOST;error=ONE"),
              "DETACHED_STRONG_REJECTED");
    }
    private static void testNoFalseStrongAfterUnscopedReattachment() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object renderer=new Object(),holder=new Object(),oldStream=new Object();
        NativeRendererStreamEvidence.Scope scope=e.enter(renderer,holder);
        try {e.onAttach(renderer,oldStream);} finally {e.exit(scope);}
        Object freshStream=new Object();
        e.onAttach(renderer,freshStream); // same renderer, outside queue scope
        e.onReadReturn(renderer,freshStream,-4);
        check(contains(e.exportLines(),
              "origin=QUEUE_SCOPED_READ_RETURN_MINUS4;error=NONE"),
              "STALE_QUEUE_PROOF_REVOKED");
        check(contains(e.exportLines(),
              "origin=UNSCOPED_READ_RETURN_MINUS4;error=ONE"),
              "UNSCOPED_REATTACH_ONLY");
        e.onReadReturn(renderer,oldStream,-4);
        check(contains(e.exportLines(),"origin=READ_RETURN_LINK_LOST;error=ONE"),
              "STALE_STREAM_CANNOT_CLAIM_NEW_RETURN");
    }
    public static void main(String[] args) {
        testAttachmentAndRealReadAlias();
        testDetachesAndReattachmentAcrossNext();
        testUnscopedAndPoisonedStack();
        testNoPrivateValuesInReport();
        testUnscopedReadNeverAttestsQueueHolder();
        testEarlyReadBudgetMustNotHideLaterUnscopedAttach();
        testRegistrationSurvivesTrimmedEventLog();
        testRealReturnCodesNeverInferAudibleTrack();
        testScopedAndUnscopedReturnsNeverMix();
        testNoFalseStrongAfterUnscopedReattachment();
        System.out.println("NATIVE_RENDERER_READONLY_EVIDENCE_MODEL_PASS");
    }
}
