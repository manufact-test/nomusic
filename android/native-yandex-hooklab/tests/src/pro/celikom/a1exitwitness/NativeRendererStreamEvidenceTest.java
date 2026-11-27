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
    private static void testExactSecondaryCallerUnscopedMatch() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        e.onHookRegistration("SECONDARY_CALLER",true);
        Object renderer=new Object(),stream=new Object();
        NativeRendererStreamEvidence.CallerFrame frame=
            e.enterSecondaryCaller(renderer,stream);
        try { e.onAttach(renderer,stream); }
        finally {e.exitSecondaryCaller(frame);}
        e.onReadReturn(renderer,stream,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=SECONDARY_CALLER;error=REGISTERED"),
            "SECONDARY_CALLER_REGISTERED");
        check(contains(snap,"origin=SECONDARY_CALLER_ENTER;error=ONE"),
            "EXACT_SECONDARY_CALLED");
        check(contains(snap,"origin=SECONDARY_CALLER_STREAM_MATCH;error=ONE"),
            "SECONDARY_SAME_STREAM");
        check(contains(snap,"origin=UNSCOPED_ATTACH_SECONDARY_MATCH;error=ONE"),
            "SECONDARY_WEAK_LINK");
        check(contains(snap,"origin=UNSCOPED_READ_RETURN_MINUS4;error=ONE"),
            "SECONDARY_WEAK_RETURN");
        check(contains(snap,"origin=QUEUE_SCOPED_READ_RETURN_MINUS4;error=NONE"),
            "SECONDARY_NOT_STRONG_QUEUE_PROOF");
    }
    private static void testSecondaryCallerAndQueueScopeRemainDistinct() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        e.onHookRegistration("SECONDARY_CALLER",true);
        Object renderer=new Object(),stream=new Object(),holder=new Object();
        NativeRendererStreamEvidence.Scope q=e.enter(renderer,holder);
        NativeRendererStreamEvidence.CallerFrame frame=
            e.enterSecondaryCaller(renderer,stream);
        try {e.onAttach(renderer,stream);}
        finally {e.exitSecondaryCaller(frame);e.exit(q);}
        e.onReadReturn(renderer,stream,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=SECONDARY_CALLER_STREAM_MATCH;error=ONE"),
            "SECONDARY_WITHIN_QUEUE");
        check(contains(snap,"origin=UNSCOPED_ATTACH_SECONDARY_MATCH;error=NONE"),
            "STRONG_NOT_COUNTED_WEAK");
        check(contains(snap,"origin=QUEUE_SCOPED_READ_RETURN_MINUS4;error=ONE"),
            "QUEUE_REMAINS_STRONG");
    }
    private static void testOutsideSecondaryOnlyWhenHookActive() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object renderer=new Object(),stream=new Object();
        e.onAttach(renderer,stream);
        check(contains(e.exportLines(),"origin=UNSCOPED_ATTACH_OUTSIDE_SECONDARY;error=NONE"),
            "CANNOT_CALL_NONHOOKED_OUTSIDE");
        e.onHookRegistration("SECONDARY_CALLER",true);
        e.onAttach(renderer,new Object());
        check(contains(e.exportLines(),"origin=UNSCOPED_ATTACH_OUTSIDE_SECONDARY;error=ONE"),
            "PROVED_OUTSIDE_ACTIVE_SECONDARY_SCOPE");
    }
    private static void testSecondaryDifferentStreamCannotBecomeMatch() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        e.onHookRegistration("SECONDARY_CALLER",true);
        Object renderer=new Object(),expected=new Object(),actual=new Object();
        NativeRendererStreamEvidence.CallerFrame frame=
            e.enterSecondaryCaller(renderer,expected);
        try {e.onAttach(renderer,actual);}
        finally {e.exitSecondaryCaller(frame);}
        String[] snap=e.exportLines();
        check(contains(snap,"origin=SECONDARY_CALLER_STREAM_DIFFERENT;error=ONE"),
            "SECONDARY_MISMATCH_SEEN");
        check(contains(snap,"origin=UNSCOPED_ATTACH_SECONDARY_DIFFERENT;error=ONE"),
            "SECONDARY_MISMATCH_NOT_PROMOTED");
        check(contains(snap,"origin=UNSCOPED_ATTACH_SECONDARY_MATCH;error=NONE"),
            "SECONDARY_MISMATCH_CANNOT_MATCH");
    }
    private static void testSecondaryScopeUnwindsBeforeNextAttach() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        e.onHookRegistration("SECONDARY_CALLER",true);
        Object renderer=new Object(),stream=new Object();
        NativeRendererStreamEvidence.CallerFrame frame=
            e.enterSecondaryCaller(renderer,stream);
        try {e.onAttach(renderer,stream);}
        finally {e.exitSecondaryCaller(frame);}
        e.onAttach(renderer,new Object());
        String[] snap=e.exportLines();
        check(contains(snap,"origin=UNSCOPED_ATTACH_SECONDARY_MATCH;error=ONE"),
            "SECONDARY_FIRST_ATTACH");
        check(contains(snap,"origin=UNSCOPED_ATTACH_OUTSIDE_SECONDARY;error=ONE"),
            "SECONDARY_FRAME_MUST_NOT_LEAK");
        check(contains(snap,"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
            "SECONDARY_STILL_NOT_AUDIBLE");
    }

    private static final class FakePeriodHolder {
        Object[] streams;
        FakePeriodHolder(Object... streams) { this.streams=streams; }
    }

    private static void registerExactEngineField(NativeRendererStreamEvidence e) {
        try {
            java.lang.reflect.Field f=FakePeriodHolder.class.getDeclaredField("streams");
            f.setAccessible(true);
            e.setEngineHolderStreamArrayField(f);
            e.onHookRegistration("ENGINE_HOLDER_SCOPE",true);
            e.onHookRegistration("SECONDARY_CALLER",true);
        } catch (ReflectiveOperationException exc) {
            throw new AssertionError(exc);
        }
    }

    private static void testEngineExactHolderArrayStreamAndLiveReturn() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        NativeRendererStreamEvidence.EngineFrame engine=e.enterEngine(holder);
        NativeRendererStreamEvidence.CallerFrame secondary=e.enterSecondaryCaller(renderer,stream);
        try {e.onAttach(renderer,stream);}
        finally {e.exitSecondaryCaller(secondary);e.exitEngine(engine);}
        e.onReadReturn(renderer,stream,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=ENGINE_HOLDER_SCOPE;error=REGISTERED"),
              "ENGINE_HOOK_REGISTERED");
        check(contains(snap,"origin=ENGINE_HOLDER_SCOPE_ENTER;error=ONE"),
              "ENGINE_ENTRY");
        check(contains(snap,"origin=ENGINE_HOLDER_STREAM_ARRAY_MATCH;error=ONE"),
              "ENGINE_HOLDER_TO_STREAM_STRICT_SAME_REF");
        check(contains(snap,"origin=ENGINE_HOLDER_READ_RETURN_MINUS4;error=ONE"),
              "ENGINE_HOLDER_REAL_READ_RETURN");
        check(contains(snap,"origin=QUEUE_SCOPED_READ_RETURN_MINUS4;error=NONE"),
              "ENGINE_MUST_NOT_LIE_ABOUT_QUEUE_SCOPE");
        check(contains(snap,"origin=UNSCOPED_READ_RETURN_MINUS4;error=ONE"),
              "EXISTING_WEAK_NAV22_PRESERVED");
        check(contains(snap,"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "ENGINE_NOT_YET_AUDIBLE_TRACK_IDENTITY");
    }

    private static void testEngineRejectsDifferentMemberWithoutFakingHolder() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(new Object());
        NativeRendererStreamEvidence.EngineFrame engine=e.enterEngine(holder);
        NativeRendererStreamEvidence.CallerFrame secondary=e.enterSecondaryCaller(renderer,stream);
        try {e.onAttach(renderer,stream);}
        finally {e.exitSecondaryCaller(secondary);e.exitEngine(engine);}
        e.onReadReturn(renderer,stream,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=ENGINE_HOLDER_STREAM_ARRAY_DIFFERENT;error=ONE"),
              "ENGINE_MISMATCH_RECORDED");
        check(contains(snap,"origin=ENGINE_HOLDER_STREAM_ARRAY_MATCH;error=NONE"),
              "ENGINE_MISMATCH_NOT_PROMOTED");
        check(contains(snap,"origin=ENGINE_HOLDER_READ_RETURN_MINUS4;error=NONE"),
              "ENGINE_MISMATCH_CANNOT_ATTEST_READ");
        check(contains(snap,"origin=UNSCOPED_READ_RETURN_MINUS4;error=ONE"),
              "LEGACY_WEAK_READ_PRESERVED");
    }

    private static void testEngineHolderNoSecondaryCannotProveStream() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        Object renderer=new Object(),stream=new Object();
        NativeRendererStreamEvidence.EngineFrame engine=e.enterEngine(new FakePeriodHolder(stream));
        try {e.onAttach(renderer,stream);}
        finally {e.exitEngine(engine);}
        e.onReadReturn(renderer,stream,-4);
        check(contains(e.exportLines(),"origin=ENGINE_HOLDER_STREAM_ARRAY_MATCH;error=NONE"),
              "ENGINE_CALL_NESTING_WITHOUT_SECONDARY_NOT_PROOF");
        check(contains(e.exportLines(),"origin=ENGINE_HOLDER_READ_RETURN_MINUS4;error=NONE"),
              "NO_ENGINE_REFERENCE_PROOF");
    }

    private static void testEngineLinkRevokedOnDetachAndReattach() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        Object renderer=new Object(),stream=new Object();
        NativeRendererStreamEvidence.EngineFrame engine=e.enterEngine(new FakePeriodHolder(stream));
        NativeRendererStreamEvidence.CallerFrame sec=e.enterSecondaryCaller(renderer,stream);
        try {e.onAttach(renderer,stream);}
        finally {e.exitSecondaryCaller(sec);e.exitEngine(engine);}
        e.onDetach(renderer);
        e.onReadReturn(renderer,stream,-4);
        check(contains(e.exportLines(),"origin=ENGINE_HOLDER_READ_RETURN_MINUS4;error=NONE"),
              "DETACHED_ENGINE_PROOF_REVOKED");
        // A later unscoped re-attach must not inherit old holder.
        e.onAttach(renderer,stream);
        e.onReadReturn(renderer,stream,-4);
        check(contains(e.exportLines(),"origin=ENGINE_HOLDER_READ_RETURN_MINUS4;error=NONE"),
              "REATTACH_CANNOT_INHERIT_ENGINE");
    }

    private static void testEngineArrayUnavailableFailsClosed() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        e.onHookRegistration("ENGINE_HOLDER_SCOPE",true);
        e.onHookRegistration("SECONDARY_CALLER",true);
        Object renderer=new Object(),stream=new Object();
        NativeRendererStreamEvidence.EngineFrame engine=e.enterEngine(new FakePeriodHolder(stream));
        NativeRendererStreamEvidence.CallerFrame secondary=e.enterSecondaryCaller(renderer,stream);
        try {e.onAttach(renderer,stream);}
        finally {e.exitSecondaryCaller(secondary);e.exitEngine(engine);}
        e.onReadReturn(renderer,stream,-4);
        check(contains(e.exportLines(),"origin=ENGINE_HOLDER_STREAM_ARRAY_UNAVAILABLE;error=ONE"),
              "UNAVAILABLE_MEMBER_NOT_PROOF");
        check(contains(e.exportLines(),"origin=ENGINE_HOLDER_READ_RETURN_MINUS4;error=NONE"),
              "UNAVAILABLE_HOLDER_NOT_PROMOTED");
    }

    private static void testEngineFrameLifetimeDoesNotLeak() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        Object renderer=new Object(),stream=new Object();
        NativeRendererStreamEvidence.EngineFrame frame=e.enterEngine(new FakePeriodHolder(stream));
        e.exitEngine(frame);
        NativeRendererStreamEvidence.CallerFrame secondary=e.enterSecondaryCaller(renderer,stream);
        try {e.onAttach(renderer,stream);}
        finally {e.exitSecondaryCaller(secondary);}
        check(contains(e.exportLines(),"origin=ENGINE_HOLDER_STREAM_ARRAY_MATCH;error=NONE"),
              "ENGINE_FRAME_LEAK");
        check(contains(e.exportLines(),"origin=UNSCOPED_ATTACH_SECONDARY_MATCH;error=ONE"),
              "OLD_SECONDARY_UNSCOPED_PATH_PRESERVED");
    }

    private static void makeBoundEngineLink(NativeRendererStreamEvidence e,
            Object renderer,Object stream) {
        NativeRendererStreamEvidence.EngineFrame frame=
            e.enterEngine(new FakePeriodHolder(stream));
        NativeRendererStreamEvidence.CallerFrame caller=
            e.enterSecondaryCaller(renderer,stream);
        try { e.onAttach(renderer,stream); }
        finally { e.exitSecondaryCaller(caller); e.exitEngine(frame); }
    }

    private static void makeBoundEngineLink(NativeRendererStreamEvidence e,
            Object holder,Object renderer,Object stream) {
        NativeRendererStreamEvidence.EngineFrame frame=e.enterEngine(holder);
        NativeRendererStreamEvidence.CallerFrame caller=
            e.enterSecondaryCaller(renderer,stream);
        try { e.onAttach(renderer,stream); }
        finally { e.exitSecondaryCaller(caller); e.exitEngine(frame); }
    }

    private static void testAudioType1State2StrictHolderRead() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        Object renderer=new Object(),stream=new Object();
        makeBoundEngineLink(e,renderer,stream);
        e.onReadReturn(renderer,stream,-4);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=RENDERER_TYPE_STATE_ACCESS;error=REGISTERED"),
              "TYPE_STATE_METHODS_REGISTERED");
        check(contains(snap,"origin=ENGINE_HOLDER_RENDERER_TYPE1;error=ONE"),
              "ONLY_REFERENCED_AUDIO_KIND");
        check(contains(snap,"origin=ENGINE_HOLDER_TYPE1_STATE2;error=ONE"),
              "TYPE1_AND_STATE2_LIVE_READ");
        check(contains(snap,"origin=ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4;error=ONE"),
              "EXACT_ORIGINAL_AUDIO_RETURN");
        check(contains(snap,"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "AUDIO_STATE_IS_NOT_AUDIBLE_CELIKOM");
    }

    private static void testAudioType2CannotMasqueradeAsAudio() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        Object r=new Object(),stream=new Object();
        makeBoundEngineLink(e,r,stream);
        e.onRendererTypeStateRead(r,stream,2,2,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=ENGINE_HOLDER_RENDERER_TYPE_OTHER;error=ONE"),
            "TYPE2_DIFFERENT_FROM_AUDIO");
        check(contains(snap,"origin=ENGINE_HOLDER_TYPE1_STATE2;error=NONE"),
            "OTHER_KIND_NOT_PROMOTED");
    }

    private static void testAudioType1State1IsNotStartedState() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        Object r=new Object(),stream=new Object();
        makeBoundEngineLink(e,r,stream);
        e.onRendererTypeStateRead(r,stream,1,1,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=ENGINE_HOLDER_TYPE1_STATE_NOT2;error=ONE"),
            "TYPE1_STATE_NOT2");
        check(contains(snap,"origin=ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4;error=NONE"),
            "PREPARED_NOT_STARTED");
    }

    private static void testAudioTypeStateWrongStreamAndDetachFailClosed() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        Object r=new Object(),stream=new Object();
        makeBoundEngineLink(e,r,stream);
        e.onRendererTypeStateRead(r,new Object(),1,2,-4);
        e.onDetach(r);
        e.onRendererTypeStateRead(r,stream,1,2,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=ENGINE_HOLDER_TYPE1_STATE2;error=NONE"),
            "STALE_RENDERER_NEVER_PROVES_AUDIO");
    }

    private static void testAudioTypeStateAbsentReflectionNotFalselyCounted() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",false);
        Object r=new Object(),stream=new Object();
        makeBoundEngineLink(e,r,stream);
        e.onRendererTypeStateRead(r,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=ENGINE_HOLDER_TYPE1_STATE2;error=NONE"),
            "NO_METHODS_NO_AUDIO_PROOF");
    }

    private static void testAudioTypeStateExceptionCountsUnavailableOnly() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        Object r=new Object(),stream=new Object();
        makeBoundEngineLink(e,r,stream);
        e.onRendererTypeStateUnavailable(r,stream);
        e.onRendererTypeStateUnavailable(r,new Object());
        String[] snap=e.exportLines();
        check(contains(snap,"origin=ENGINE_HOLDER_TYPE_STATE_UNAVAILABLE;error=ONE"),
            "EXCEPTION_ONLY_ON_STRICT_ENGINE_LINK");
        check(contains(snap,"origin=ENGINE_HOLDER_TYPE1_STATE2;error=NONE"),
            "EXCEPTION_CANNOT_ATTEST_STARTED_AUDIO");
    }

    private static void testNav25NonEosStartedAudioStrictLink() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("BUFFER_EOS_ACCESS",true);
        Object renderer=new Object(),stream=new Object();
        makeBoundEngineLink(e,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.TRUE);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        e.onRendererTypeStateRead(renderer,stream,1,2,-3,Boolean.FALSE);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=BUFFER_EOS_ACCESS;error=REGISTERED"),
            "NAV25_BUFFER_GETTER_REGISTERED");
        check(contains(snap,"origin=ENGINE_AUDIO_TYPE1_STATE2_BUFFER_NON_EOS;error=ONE"),
            "NAV25_EXACT_NON_EOS_READ");
        check(contains(snap,"origin=ENGINE_AUDIO_TYPE1_STATE2_BUFFER_EOS;error=ONE"),
            "NAV25_EXACT_EOS_READ");
        check(contains(snap,"origin=ENGINE_AUDIO_TYPE1_STATE2_BUFFER_UNAVAILABLE;error=ONE"),
            "NAV25_UNKNOWN_IS_NOT_NON_EOS");
        check(contains(snap,"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
            "NAV25_AUDIO_BUFFER_NOT_SELECTED_TRACK_OR_PCM");
    }

    private static void testNav25NoFalseAudioSampleOnWrongLinkOrState() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("BUFFER_EOS_ACCESS",true);
        Object renderer=new Object(),stream=new Object();
        makeBoundEngineLink(e,renderer,stream);
        e.onRendererTypeStateRead(renderer,new Object(),1,2,-4,Boolean.FALSE);
        e.onRendererTypeStateRead(renderer,stream,2,2,-4,Boolean.FALSE);
        e.onRendererTypeStateRead(renderer,stream,1,1,-4,Boolean.FALSE);
        e.onDetach(renderer);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=ENGINE_AUDIO_TYPE1_STATE2_BUFFER_NON_EOS;error=NONE"),
            "NAV25_STALE_OR_WRONG_RENDERER_NOT_SAMPLED");
    }

    private static void testNav25MissingBufferMethodCannotAttestSample() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("BUFFER_EOS_ACCESS",false);
        Object renderer=new Object(),stream=new Object();
        makeBoundEngineLink(e,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=BUFFER_EOS_ACCESS;error=NO_HOOK"),
            "NAV25_FAIL_CLOSED_REGISTRATION");
        check(contains(snap,"origin=ENGINE_AUDIO_TYPE1_STATE2_BUFFER_NON_EOS;error=NONE"),
            "NAV25_CANNOT_INVENT_BUFFER_FLAG");
        check(contains(snap,"origin=ENGINE_AUDIO_TYPE1_STATE2_BUFFER_UNAVAILABLE;error=ONE"),
            "NAV25_UNAVAILABLE_BEFORE_AUDIO_IDENTITY");
    }

    private static void testNav26ComparatorTrueCorrelatesExactActiveRendererRead() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("RENDERER_COMPARATOR",true);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        NativeRendererStreamEvidence.EngineFrame engine=e.enterEngine(holder);
        NativeRendererStreamEvidence.CallerFrame caller=e.enterSecondaryCaller(renderer,stream);
        try { e.onAttach(renderer,stream); }
        finally { e.exitSecondaryCaller(caller); e.exitEngine(engine); }
        e.onRendererComparatorResult(holder,renderer,stream,true);
        e.onReadReturn(renderer,stream,-4);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=RENDERER_COMPARATOR;error=REGISTERED"),
            "NAV26_COMPARATOR_HOOK_REGISTERED");
        check(contains(snap,"origin=RENDERER_COMPARATOR_TRUE;error=ONE"),
            "NAV26_EXACT_COMPARATOR_TRUE");
        check(contains(snap,"origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE;error=ONE"),
            "NAV26_SAME_HOLDER_RENDERER_STREAM_AUDIO_READ");
        check(contains(snap,"origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE_MINUS4;error=ONE"),
            "NAV26_SAME_PAIR_ORIGINAL_READ_RESULT");
        check(contains(snap,"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
            "NAV26_NOT_SELECTED_TRACK_OR_AUDIBLE_CELIKOM");
    }

    private static void testNav26ComparatorFalseNeverPromotesAudioRead() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("RENDERER_COMPARATOR",true);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        makeBoundEngineLink(e,holder,renderer,stream);
        e.onRendererComparatorResult(holder,renderer,stream,false);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=RENDERER_COMPARATOR_FALSE;error=ONE"),
            "NAV26_EXACT_COMPARATOR_FALSE");
        check(contains(snap,"origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_FALSE;error=ONE"),
            "NAV26_FALSE_OUTCOME_CORRELATED_WITH_SAME_ACTIVE_READ");
        check(contains(snap,"origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE;error=NONE"),
            "NAV26_FALSE_NEVER_PROMOTED");
    }

    private static void testNav26ComparatorRequiresExactHolderRendererAndStream() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("RENDERER_COMPARATOR",true);
        Object renderer=new Object(),stream=new Object(),other=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        makeBoundEngineLink(e,renderer,stream);
        e.onRendererComparatorResult(new FakePeriodHolder(stream),renderer,stream,true);
        e.onRendererComparatorResult(holder,new Object(),stream,true);
        e.onRendererComparatorResult(holder,renderer,other,true);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=RENDERER_COMPARATOR_TRUE;error=FEW"),
            "NAV26_COMPARATOR_OBSERVATIONS_COUNTED");
        check(contains(snap,"origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE;error=NONE"),
            "NAV26_NO_CROSS_OBJECT_PROMOTION");
    }

    private static void testNav26ComparatorDetachedRendererAndMissingHookFailClosed() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("RENDERER_COMPARATOR",true);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        makeBoundEngineLink(e,holder,renderer,stream);
        e.onRendererComparatorResult(holder,renderer,stream,true);
        e.onDetach(renderer);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE;error=NONE"),
            "NAV26_DETACH_INVALIDATES_COMPARATOR");
        NativeRendererStreamEvidence missing=new NativeRendererStreamEvidence();
        missing.onRendererComparatorResult(holder,renderer,stream,true);
        check(contains(missing.exportLines(),"origin=RENDERER_COMPARATOR;error=NOT_SEEN"),
            "NAV26_MISSING_HOOK_NOT_REGISTERED");
        check(contains(missing.exportLines(),"origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE;error=NONE"),
            "NAV26_MISSING_HOOK_NO_AUDIO_PROOF");
    }

    private static void testNav26ComparatorOutcomeClearedOnReattach() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("RENDERER_COMPARATOR",true);
        Object renderer=new Object(),streamA=new Object(),streamB=new Object();
        FakePeriodHolder holderA=new FakePeriodHolder(streamA);
        FakePeriodHolder holderB=new FakePeriodHolder(streamB);
        makeBoundEngineLink(e,holderA,renderer,streamA);
        e.onRendererComparatorResult(holderA,renderer,streamA,true);
        makeBoundEngineLink(e,holderB,renderer,streamB);
        e.onRendererTypeStateRead(renderer,streamB,1,2,-4);
        String[] snap=e.exportLines();
        check(contains(snap,"origin=RENDERER_COMPARATOR_TRUE;error=ONE"),
            "NAV26_OLD_COMPARATOR_EVENT_RETAINED_AS_HISTORY");
        check(contains(snap,"origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE;error=NONE"),
            "NAV26_REATTACH_CANNOT_INHERIT_OLD_COMPARATOR_RESULT");
    }

    private static final class FakeQueue {
        FakePeriodHolder slotB;
        FakeQueue(FakePeriodHolder holder) { slotB=holder; }
    }
    private static final class FakeEngine {
        FakeQueue queue;
        FakeEngine(FakePeriodHolder holder) { queue=new FakeQueue(holder); }
    }
    private static void registerLiveQueueFields(NativeRendererStreamEvidence e) {
        try {
            java.lang.reflect.Field queue=FakeEngine.class.getDeclaredField("queue");
            java.lang.reflect.Field slot=FakeQueue.class.getDeclaredField("slotB");
            e.setLiveQueueSlotFields(queue,slot);
            e.onHookRegistration("LIVE_QUEUE_SLOT_B",true);
        } catch(ReflectiveOperationException ex) { throw new AssertionError(ex); }
    }
    private static void bindLiveQueue(NativeRendererStreamEvidence e,
            FakeEngine engine,FakePeriodHolder holder,Object renderer,Object stream) {
        NativeRendererStreamEvidence.EngineFrame frame=e.enterEngine(engine,holder);
        NativeRendererStreamEvidence.CallerFrame sec=e.enterSecondaryCaller(renderer,stream);
        try { e.onAttach(renderer,stream); }
        finally { e.exitSecondaryCaller(sec); e.exitEngine(frame); }
    }
    private static final class FakeMediaItem {
        final String mediaId;
        FakeMediaItem(String mediaId){this.mediaId=mediaId;}
    }
    private static final class FakeSource { FakeMediaItem item; }
    private interface FakePublisherPeriodInterface {}
    private static final class FakeOtherPublisherPeriod implements FakePublisherPeriodInterface {}
    private static final class FakePeriod implements FakePublisherPeriodInterface {
        FakeSource source;
        FakePeriod(FakeSource source) {this.source=source;}
    }
    private interface FakeSampleStream {}
    private static final class FakeChildStream implements FakeSampleStream {}
    private static final class FakeStreamAdapter implements FakeSampleStream {
        FakeSampleStream child;
        FakeStreamAdapter(FakeSampleStream child){this.child=child;}
    }
    private static final class FakeNested {
        Object period;
        FakeStreamAdapter[] adapters=new FakeStreamAdapter[0];
        FakeNested(FakePeriod period) {this.period=period;}
    }
    private static final class FakeHolderSource {
        Object nested;
        Object[] streams;
        FakeHolderSource(FakeSource source,Object stream) {
            nested=new FakeNested(new FakePeriod(source));
            streams=new Object[]{stream};
        }
    }
    private static final class FakeActiveQueue {
        FakeHolderSource slotB;
        FakeActiveQueue(FakeHolderSource h) {slotB=h;}
    }
    private static final class FakeActiveEngine {
        FakeActiveQueue queue;
        FakeActiveEngine(FakeHolderSource holder) {queue=new FakeActiveQueue(holder);}
    }
    private static void setUpNav29(NativeRendererStreamEvidence e) {
        try {
            java.lang.reflect.Field holderStream=FakeHolderSource.class.getDeclaredField("streams");
            holderStream.setAccessible(true);
            e.setEngineHolderStreamArrayField(holderStream);
            e.onHookRegistration("ENGINE_HOLDER_SCOPE",true);
            e.onHookRegistration("SECONDARY_CALLER",true);
            e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
            e.onHookRegistration("LIVE_QUEUE_SLOT_B",true);
            e.setLiveQueueSlotFields(
                FakeActiveEngine.class.getDeclaredField("queue"),
                FakeActiveQueue.class.getDeclaredField("slotB"));
            e.setExactActivePeriodFields(
                FakeHolderSource.class.getDeclaredField("nested"),
                FakeNested.class.getDeclaredField("period"),
                FakePeriod.class.getDeclaredField("source"),
                FakeNested.class,FakePeriod.class,FakeSource.class);
            e.onHookRegistration("LIVE_PERIOD_ORIGINAL_SOURCE",true);
            e.onHookRegistration("TRACK_PLAYER_SOURCE_SCOPE",true);
            e.onHookRegistration("NATIVE_PLAYER_SOURCE_SETTER",true);
        } catch(ReflectiveOperationException ex) {throw new AssertionError(ex);}
    }
    private static void nav29BindLive(NativeRendererStreamEvidence e,
            FakeActiveEngine engine,FakeHolderSource holder,Object renderer,Object stream) {
        NativeRendererStreamEvidence.EngineFrame f=e.enterEngine(engine,holder);
        NativeRendererStreamEvidence.CallerFrame c=e.enterSecondaryCaller(renderer,stream);
        try {e.onAttach(renderer,stream);}
        finally {e.exitSecondaryCaller(c);e.exitEngine(f);}
    }
    private static final class FakePeriodAdapter {}
    private static void testNav30AdapterMapsExactFactoryToLiveWrapper() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.onHookRegistration("NATIVE_PERIOD_ADAPTER",true);
        e.onHookRegistration("NATIVE_PERIOD_FACTORY",true);
        Object render=new Object(),stream=new Object(),wrapper=new Object();
        Object owner=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        FakePeriod inner=(FakePeriod)((FakeNested)holder.nested).period;
        FakeNested adapted=new FakeNested(inner); // exact known Lup1 field stores Lo96
        ((FakeNested)holder.nested).period=adapted;
        NativeRendererStreamEvidence.TrackPlayerScope player=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(source);}
        finally{e.exitTrackPlayerSource(player);}
        NativeRendererStreamEvidence.NativePeriodAdapterScope frame=
            e.enterNativePeriodAdapter(owner);
        try {
            e.onNativePeriodFactoryResult(owner,inner);
            e.onNativePeriodAdapterReturn(frame,adapted);
        } finally {e.exitNativePeriodAdapter(frame);}
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        nav29BindLive(e,engine,holder,render,stream);
        e.onRendererTypeStateRead(render,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_WRAPPED_NON_LO96;error=ONE"),
              "NAV30_WRAPPED_NOT_DIRECT");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_ADAPTER_MAPPED;error=ONE"),
              "NAV30_EXACT_FACTORY_BRIDGE");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=ONE"),
              "NAV30_ACTIVE_ORIGINAL_SOURCE_REF_MATCH");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "NAV30_NO_ALBUM_EDITION_GENERATION");
    }
    private static void testNav30SameFrameUnrelatedAdapterNeverLinks() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.onHookRegistration("NATIVE_PERIOD_ADAPTER",true);
        e.onHookRegistration("NATIVE_PERIOD_FACTORY",true);
        Object render=new Object(),stream=new Object(),owner=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        FakePeriodAdapter unrelated=new FakePeriodAdapter();
        ((FakeNested)holder.nested).period=unrelated;
        NativeRendererStreamEvidence.NativePeriodAdapterScope frame=
            e.enterNativePeriodAdapter(owner);
        try {
            e.onNativePeriodFactoryResult(owner,new FakePeriod(source));
            e.onNativePeriodAdapterReturn(frame,unrelated);
        } finally {e.exitNativePeriodAdapter(frame);}
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        nav29BindLive(e,engine,holder,render,stream);
        e.onRendererTypeStateRead(render,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=NATIVE_PERIOD_ADAPTER_LINK_CREATED;error=NONE"),
              "NAV30_TEMPORAL_ONLY_REJECTED");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_ADAPTER_MAPPED;error=NONE"),
              "NAV30_NO_FAKE_PERIOD_IDENTITY_FROM_TIMING");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=NONE"),
              "NAV30_UNRELATED_ADAPTER_NEVER_PROMOTES");
    }
    private static void testNav30AdapterNoScopeOrWrongFactoryFailsClosed() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.onHookRegistration("NATIVE_PERIOD_ADAPTER",true);
        e.onHookRegistration("NATIVE_PERIOD_FACTORY",true);
        Object render=new Object(),stream=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        ((FakeNested)holder.nested).period=new FakePeriodAdapter();
        // Factory without exact Lp96.goto frame cannot bind.
        e.onNativePeriodFactoryResult(new Object(),new FakePeriod(source));
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        nav29BindLive(e,engine,holder,render,stream);
        e.onRendererTypeStateRead(render,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_ADAPTER_UNMAPPED;error=ONE"),
              "NAV30_NO_UNSCOPED_ADAPTER_PROMOTION");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_ORIGINAL_SOURCE_UNAVAILABLE;error=ONE"),
              "NAV30_WRAPPED_SOURCE_UNAVAILABLE");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=NONE"),
              "NAV30_NO_FALSE_POSITIVE");
    }
    private static void testNav30RejectsNestedDuplicateFactoryAndDetach() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.onHookRegistration("NATIVE_PERIOD_ADAPTER",true);
        e.onHookRegistration("NATIVE_PERIOD_FACTORY",true);
        Object render=new Object(),stream=new Object(),owner=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        FakePeriodAdapter adapted=new FakePeriodAdapter();
        ((FakeNested)holder.nested).period=adapted;
        NativeRendererStreamEvidence.NativePeriodAdapterScope frame=
            e.enterNativePeriodAdapter(owner);
        try {
            e.onNativePeriodFactoryResult(owner,new FakePeriod(source));
            e.onNativePeriodFactoryResult(owner,new FakePeriod(source));
            e.onNativePeriodAdapterReturn(frame,adapted);
        } finally {e.exitNativePeriodAdapter(frame);}
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        nav29BindLive(e,engine,holder,render,stream);
        e.onRendererTypeStateRead(render,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=NATIVE_PERIOD_FACTORY_CONFLICT;error=ONE"),
              "NAV30_DUPLICATE_FACTORY_FAIL_CLOSED");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_ADAPTER_UNMAPPED;error=ONE"),
              "NAV30_CONFLICT_NOT_MAPPED");
        e.onDetach(render);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=NONE"),
              "NAV30_DETACH_NEVER_PROMOTES");
    }

    private static void testNav29SameSelectedWrapperSourceToLivePeriod() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        Object renderer=new Object(),stream=new Object(),wrapper=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        NativeRendererStreamEvidence.TrackPlayerScope f=e.enterTrackPlayerSource(wrapper);
        try { e.onNativePlayerSourceSetter(source); }
        finally {e.exitTrackPlayerSource(f);}
        nav29BindLive(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=TRACK_PLAYER_SOURCE_SAME_SCOPE;error=ONE"),
              "NAV29_SAME_TRACK_TO_PLAYER_SOURCE");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED;error=ONE"),
              "NAV29_LO96_SOURCE_REACHED");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=ONE"),
              "NAV29_ACTIVE_SOURCE_EQUALITY");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "NAV29_NO_EDITION_CLAIM");
    }
    private static void testNav29RejectsOtherSourceOrChangedQueueSlot() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        Object r=new Object(),s=new Object(),wrapper=new Object();
        FakeSource chosen=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(new FakeSource(),s);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        NativeRendererStreamEvidence.TrackPlayerScope f=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(chosen);}
        finally{e.exitTrackPlayerSource(f);}
        nav29BindLive(e,engine,holder,r,s);
        e.onRendererTypeStateRead(r,s,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_NO_LINK;error=ONE"),
              "NAV29_WRONG_SOURCE_NO_LINK");
        engine.queue.slotB=new FakeHolderSource(chosen,s);
        e.onRendererTypeStateRead(r,s,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=NONE"),
              "NAV29_CHANGED_QUEUE_CANNOT_PROMOTE");
    }
    private static void testNav29RejectsUnscopedAndConflictingWrapper() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        Object r=new Object(),s=new Object(),w1=new Object(),w2=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,s);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        e.onNativePlayerSourceSetter(source); // no track scope
        NativeRendererStreamEvidence.TrackPlayerScope f=e.enterTrackPlayerSource(w1);
        try {e.onNativePlayerSourceSetter(source);}
        finally{e.exitTrackPlayerSource(f);}
        f=e.enterTrackPlayerSource(w2);
        try {e.onNativePlayerSourceSetter(source);}
        finally{e.exitTrackPlayerSource(f);}
        nav29BindLive(e,engine,holder,r,s);
        e.onRendererTypeStateRead(r,s,1,2,-4);
        check(contains(e.exportLines(),"origin=TRACK_PLAYER_SOURCE_CONFLICT;error=ONE"),
              "NAV29_CONFLICT_RECORDED");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=NONE"),
              "NAV29_CONFLICT_NOT_PROMOTED");
    }

    private static void testNav28LiveQueueSlotMatchesAtAttachAndStartedRead() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        registerLiveQueueFields(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        FakeEngine engine=new FakeEngine(holder);
        bindLiveQueue(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_QUEUE_SLOT_B_ATTACH_MATCH;error=ONE"),
              "NAV28_LIVE_SLOT_ATTACH_IDENTITY");
        check(contains(e.exportLines(),
              "origin=LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH;error=ONE"),
              "NAV28_LIVE_SLOT_STILL_SAME_AT_STARTED_AUDIO_READ");
        check(contains(e.exportLines(),
              "origin=LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MINUS4;error=ONE"),
              "NAV28_RETURN_CLASS_ONLY");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "NAV28_LIVE_SLOT_ALONE_NOT_TRACK_EDITION");
    }
    private static void testNav28RejectsLiveQueueSlotChangeAndDetach() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        registerLiveQueueFields(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        FakeEngine engine=new FakeEngine(holder);
        bindLiveQueue(e,engine,holder,renderer,stream);
        engine.queue.slotB=new FakePeriodHolder(stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_OTHER;error=ONE"),
              "NAV28_LIVE_SLOT_CHANGED_FAIL_CLOSED");
        check(contains(e.exportLines(),"origin=LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH;error=NONE"),
              "NAV28_NOT_STALE");
        e.onDetach(renderer);
        engine.queue.slotB=holder;
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH;error=NONE"),
              "NAV28_DETACH_NOT_STALE");
    }
    private static void testNav28WrongOrUnavailableSlotNeverClaimsMatch() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        registerLiveQueueFields(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        FakeEngine engine=new FakeEngine(holder);
        engine.queue.slotB=new FakePeriodHolder(stream);
        bindLiveQueue(e,engine,holder,renderer,stream);
        check(contains(e.exportLines(),"origin=LIVE_QUEUE_SLOT_B_ATTACH_OTHER;error=ONE"),
              "NAV28_OTHER_QUEUE_SLOT_NOT_SELECTED");
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),
              "origin=LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH;error=NONE"),
              "NAV28_WRONG_SLOT_CANNOT_READ_PROVE");
        engine.queue=null;
        bindLiveQueue(e,engine,holder,renderer,stream);
        check(contains(e.exportLines(),"origin=LIVE_QUEUE_SLOT_B_ATTACH_UNAVAILABLE;error=ONE"),
              "NAV28_UNAVAILABLE_REPORTED");
    }

    private static void testNav27AtCallEngineAndAttachmentCohorts() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("RENDERER_COMPARATOR",true);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        e.onRendererComparatorResult(holder,renderer,stream,false);
        check(contains(e.exportLines(),"origin=COMPARATOR_AT_CALL_NO_ENGINE;error=ONE"),
              "NAV27_BEFORE_ATTACH_WITHOUT_ENGINE");
        check(contains(e.exportLines(),
              "origin=COMPARATOR_AT_CALL_NO_ATTACHED_STREAM;error=ONE"),
              "NAV27_BEFORE_ATTACH_WITHOUT_STREAM_ALIAS");
        makeBoundEngineLink(e,holder,renderer,stream);
        e.onRendererComparatorResult(holder,renderer,stream,false);
        String[] snapshot=e.exportLines();
        check(contains(snapshot,"origin=COMPARATOR_AT_CALL_ENGINE_MATCH;error=ONE"),
              "NAV27_AFTER_ATTACH_EXACT_ENGINE_MATCH");
        check(contains(snapshot,"origin=COMPARATOR_AT_CALL_ATTACHED_STREAM;error=ONE"),
              "NAV27_AFTER_ATTACH_SAME_STREAM");
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),
              "origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_FALSE;error=ONE"),
              "NAV27_EXISTING_VALID_SAME_TRIO_COHORT_PRESERVED");
    }

    private static void testNav27PendingComparatorClearedOnExactAttach() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
        e.onHookRegistration("RENDERER_COMPARATOR",true);
        Object renderer=new Object(),stream=new Object();
        FakePeriodHolder holder=new FakePeriodHolder(stream);
        e.onRendererComparatorResult(holder,renderer,stream,false);
        makeBoundEngineLink(e,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] snapshot=e.exportLines();
        check(contains(snapshot,
              "origin=COMPARATOR_CLEARED_ATTACH_SAME_TRIO;error=ONE"),
              "NAV27_PRE_ATTACH_SAME_TRIO_RECORDED_ONLY_AS_PHASE");
        check(contains(snapshot,
              "origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_FALSE;error=NONE"),
              "NAV27_PRE_ATTACH_EVIDENCE_NOT_PROMOTED_TO_LIVE_AUDIO");
    }

    private static void testNav27PendingComparatorWrongHolderOrStream() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        registerExactEngineField(e);
        e.onHookRegistration("RENDERER_COMPARATOR",true);
        Object renderer=new Object(),streamA=new Object(),streamB=new Object();
        FakePeriodHolder holderA=new FakePeriodHolder(streamA);
        FakePeriodHolder holderB=new FakePeriodHolder(streamB);
        e.onRendererComparatorResult(holderA,renderer,streamA,false);
        makeBoundEngineLink(e,holderB,renderer,streamB);
        check(contains(e.exportLines(),
              "origin=COMPARATOR_CLEARED_ATTACH_DIFFERENT_STREAM;error=ONE"),
              "NAV27_WRONG_STREAM_NEVER_MATCHES_NEW_ATTACH");
        e.onRendererComparatorResult(holderA,renderer,streamB,false);
        makeBoundEngineLink(e,holderB,renderer,streamB);
        check(contains(e.exportLines(),
              "origin=COMPARATOR_CLEARED_ATTACH_DIFFERENT_HOLDER;error=ONE"),
              "NAV27_WRONG_HOLDER_NEVER_MATCHES_NEW_ATTACH");
        e.onRendererComparatorResult(holderA,renderer,streamA,false);
        check(contains(e.exportLines(),
              "origin=COMPARATOR_AT_CALL_ENGINE_OTHER;error=FEW"),
              "NAV27_DIFFERENT_ENGINE_LINK_EXPLICITLY_CLASSIFIED");
        e.onDetach(renderer);
        check(contains(e.exportLines(),
              "origin=ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_FALSE;error=NONE"),
              "NAV27_NO_STALE_FALSE_PROMOTION");
    }

    private static void testNav31HolderSelectBeforeVsAfterAndActiveRead() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.onHookRegistration("HOLDER_SELECT_PHASE",true);
        Object render=new Object(),stream=new Object();
        FakeHolderSource holder=new FakeHolderSource(new FakeSource(),stream);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        e.onExactHolderSelectPhase(holder,false); // exact Lup1 wrapper present
        holder.nested=null; // original may clear holder field, not our hook
        e.onExactHolderSelectPhase(holder,true);
        nav29BindLive(e,engine,holder,render,stream);
        e.onRendererTypeStateRead(render,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=HOLDER_SELECT_ENTER_EXACT;error=ONE"),
              "NAV31_EXACT_EARLY_FIELD");
        check(contains(e.exportLines(),"origin=HOLDER_SELECT_EXIT_NULL;error=ONE"),
              "NAV31_AFTER_SELECT_NULL");
        check(contains(e.exportLines(),"origin=HOLDER_ATTACH_NULL;error=ONE"),
              "NAV31_ATTACH_ALREADY_NULL");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_HOLDER_WRAPPER_NULL_AT_READ;error=ONE"),
              "NAV31_NULL_NOT_WRONG_CLASS");
        check(contains(e.exportLines(),"origin=LIVE_HOLDER_PRIOR_SELECT_EXACT_CLEARED;error=ONE"),
              "NAV31_PRIOR_EXACT_SEEN_BUT_NOW_GONE");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=NONE"),
              "NAV31_NO_STALE_EARLY_SELECTION_PROMOTION");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "NAV31_NO_SELECTED_TRACK_EDITION_OR_PCM");
    }

    private static void testNav31OtherObjectTypeIsNotNullAndNotMatched() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.onHookRegistration("HOLDER_SELECT_PHASE",true);
        Object render=new Object(),stream=new Object();
        FakeHolderSource holder=new FakeHolderSource(new FakeSource(),stream);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        holder.nested=new Object(); // not exact publisher type Lup1
        e.onExactHolderSelectPhase(holder,false);
        nav29BindLive(e,engine,holder,render,stream);
        e.onRendererTypeStateRead(render,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=HOLDER_SELECT_ENTER_OTHER;error=ONE"),
              "NAV31_EXPLICIT_WRONG_CLASS");
        check(contains(e.exportLines(),"origin=HOLDER_ATTACH_OTHER;error=ONE"),
              "NAV31_WRONG_TYPE_AT_ATTACH");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_HOLDER_WRAPPER_OTHER_AT_READ;error=ONE"),
              "NAV31_WRONG_TYPE_AT_ACTIVE_READ");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_HOLDER_WRAPPER_NULL_AT_READ;error=NONE"),
              "NAV31_WRONG_CLASS_NOT_NULL");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=NONE"),
              "NAV31_NEVER_USE_WRONG_CLASS_AS_ACTIVE_PERIOD");
    }

    private static void testNav31NoSelectionHookNoPhantomHistory() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        Object render=new Object(),stream=new Object();
        FakeHolderSource holder=new FakeHolderSource(new FakeSource(),stream);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        e.onExactHolderSelectPhase(holder,false); // unregistered, fail closed
        holder.nested=null;
        nav29BindLive(e,engine,holder,render,stream);
        e.onRendererTypeStateRead(render,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=HOLDER_SELECT_ENTER_EXACT;error=NONE"),
              "NAV31_UNREGISTERED_SELECT_NOT_OBSERVED");
        check(contains(e.exportLines(),"origin=LIVE_HOLDER_PRIOR_SELECT_EXACT_CLEARED;error=NONE"),
              "NAV31_NO_FABRICATED_HISTORY");
    }

    // NAV32 replays the exact owner NAV31 OTHER-at-every-phase observation.
    // Reference identities are historical only. Never permit replacement
    // based on an interface flag or one matching original object reference.
    private static void testNav32OtherNativePeriodInterfaceAndSameLiveReference() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.setPublisherMediaPeriodInterface(FakePublisherPeriodInterface.class);
        e.onHookRegistration("HOLDER_SELECT_PHASE",true);
        Object renderer=new Object(),stream=new Object();
        FakeHolderSource holder=new FakeHolderSource(new FakeSource(),stream);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        holder.nested=new FakeOtherPublisherPeriod();
        e.onExactHolderSelectPhase(holder,false);
        e.onExactHolderSelectPhase(holder,true);
        nav29BindLive(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] lines=e.exportLines();
        check(contains(lines,"origin=HOLDER_OTHER_WH6_SELECT_ENTER;error=ONE"),
              "NAV32_OTHER_IMPL_AT_ORIGINAL_SELECT_ENTER");
        check(contains(lines,"origin=HOLDER_OTHER_WH6_SELECT_EXIT;error=ONE"),
              "NAV32_OTHER_IMPL_AT_ORIGINAL_SELECT_EXIT");
        check(contains(lines,"origin=HOLDER_OTHER_WH6_ATTACH;error=ONE"),
              "NAV32_OTHER_IMPL_AT_STRICT_SLOT_ATTACH");
        check(contains(lines,"origin=HOLDER_OTHER_WH6_AT_READ;error=ONE"),
              "NAV32_OTHER_IMPL_AT_STARTED_AUDIO_READ");
        check(contains(lines,"origin=HOLDER_OTHER_SELECT_SAME_AT_READ;error=ONE"),
              "NAV32_EXACT_OTHER_OBJECT_SAME_AS_SELECT_EXIT");
        check(contains(lines,"origin=HOLDER_OTHER_ATTACH_SAME_AT_READ;error=ONE"),
              "NAV32_EXACT_OTHER_OBJECT_SAME_AS_ATTACH");
        check(contains(lines,"origin=LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED;error=NONE"),
              "NAV32_INTERFACE_IS_NOT_SOURCE_IDENTITY");
        check(contains(lines,"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "NAV32_NEVER_PROMOTE_TO_SELECTED_TRACK");
    }

    private static void testNav32OtherObjectSwappedAfterAttachFailsClosed() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.setPublisherMediaPeriodInterface(FakePublisherPeriodInterface.class);
        e.onHookRegistration("HOLDER_SELECT_PHASE",true);
        Object renderer=new Object(),stream=new Object();
        FakeHolderSource holder=new FakeHolderSource(new FakeSource(),stream);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        holder.nested=new Object();
        e.onExactHolderSelectPhase(holder,false);
        e.onExactHolderSelectPhase(holder,true);
        nav29BindLive(e,engine,holder,renderer,stream);
        holder.nested=new Object(); // original later changes same field
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] lines=e.exportLines();
        check(contains(lines,"origin=HOLDER_OTHER_NON_WH6_AT_READ;error=ONE"),
              "NAV32_NON_VENDOR_MEDIA_PERIOD");
        check(contains(lines,"origin=HOLDER_OTHER_SELECT_DIFFERENT_AT_READ;error=ONE"),
              "NAV32_NO_STALE_SELECT_ALIAS");
        check(contains(lines,"origin=HOLDER_OTHER_ATTACH_DIFFERENT_AT_READ;error=ONE"),
              "NAV32_NO_STALE_ATTACH_ALIAS");
        check(contains(lines,"origin=HOLDER_OTHER_SELECT_SAME_AT_READ;error=NONE"),
              "NAV32_WRONG_OBJECT_NOT_SAME_SELECT");
        check(contains(lines,"origin=LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED;error=NONE"),
              "NAV32_NO_FAKE_SOURCE");
    }

    private static void testNav32NoOriginalSelectionHistoryIsExplicitlyUnproven() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.setPublisherMediaPeriodInterface(FakePublisherPeriodInterface.class);
        e.onHookRegistration("HOLDER_SELECT_PHASE",true);
        Object renderer=new Object(),stream=new Object();
        FakeHolderSource holder=new FakeHolderSource(new FakeSource(),stream);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        holder.nested=new FakeOtherPublisherPeriod();
        nav29BindLive(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),
              "origin=HOLDER_OTHER_SELECT_NO_HISTORY_AT_READ;error=ONE"),
              "NAV32_NO_PHANTOM_SELECT_HISTORY");
        check(contains(e.exportLines(),
              "origin=HOLDER_OTHER_ATTACH_SAME_AT_READ;error=ONE"),
              "NAV32_VERIFIED_SAME_ATTACH_NOT_SAME_TRACK");
    }


    private static void testNav33DirectOriginalLo96MatchesSource() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        setUpNav29(e);
        e.setPublisherMediaPeriodInterface(FakePublisherPeriodInterface.class);
        e.onHookRegistration("HOLDER_SELECT_PHASE",true);
        Object renderer=new Object(),stream=new Object(),wrapper=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        holder.nested=new FakePeriod(source); // exact original Lo96, not Lup1
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        NativeRendererStreamEvidence.TrackPlayerScope f=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(source);}
        finally {e.exitTrackPlayerSource(f);}
        e.onExactHolderSelectPhase(holder,false);
        e.onExactHolderSelectPhase(holder,true);
        nav29BindLive(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] report=e.exportLines();
        check(contains(report,"origin=HOLDER_OTHER_SELECT_SAME_AT_READ;error=ONE"),
              "NAV33_SAME_ORIGINAL_SELECT_HOLDER");
        check(contains(report,"origin=HOLDER_OTHER_ATTACH_SAME_AT_READ;error=ONE"),
              "NAV33_SAME_ORIGINAL_ATTACHED_HOLDER");
        check(contains(report,"origin=LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_PRESENT;error=ONE"),
              "NAV33_DIRECT_PINNED_PERIOD_SOURCE");
        check(contains(report,"origin=LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED;error=ONE"),
              "NAV33_ORIGINAL_SOURCE_RESOLVED");
        check(contains(report,"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=ONE"),
              "NAV33_EXACT_JAVA_SOURCE_REF_EQUALITY");
        check(contains(report,"origin=LIVE_PERIOD_HOLDER_WRAPPER_MISSING;error=NONE"),
              "NAV33_DIRECT_LO96_NOT_WRAPPER_MISSING");
        check(contains(report,"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "NAV33_NO_SELECTED_TRACK_EDITION_OR_QUEUE_IDENTITY");
        engine.queue.slotB=new FakeHolderSource(source,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED;error=ONE"),
              "NAV33_CHANGED_QUEUE_BLOCKS_SECOND_SOURCE");
    }
    private static void testNav33DirectLo96NullAndDifferentSourcesFailClosed() {
        for(int mode=0;mode<2;mode++) {
            NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
            setUpNav29(e);
            Object renderer=new Object(),stream=new Object(),wrapper=new Object();
            FakeSource originalSource=new FakeSource();
            FakeHolderSource holder=new FakeHolderSource(originalSource,stream);
            holder.nested=new FakePeriod(mode==0?null:new FakeSource());
            FakeActiveEngine engine=new FakeActiveEngine(holder);
            NativeRendererStreamEvidence.TrackPlayerScope f=e.enterTrackPlayerSource(wrapper);
            try {e.onNativePlayerSourceSetter(originalSource);}
            finally {e.exitTrackPlayerSource(f);}
            nav29BindLive(e,engine,holder,renderer,stream);
            e.onRendererTypeStateRead(renderer,stream,1,2,-4);
            String[] report=e.exportLines();
            check(contains(report,"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=NONE"),
                  "NAV33_NO_FALSE_SOURCE_MATCH");
            if(mode==0) {
                check(contains(report,"origin=LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_NULL;error=ONE"),
                      "NAV33_NULL_DIRECT_SOURCE");
                check(contains(report,"origin=LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED;error=NONE"),
                      "NAV33_NULL_NOT_RESOLVED");
            } else {
                check(contains(report,"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_NO_LINK;error=ONE"),
                      "NAV33_DIFFERENT_SOURCE_NO_LINK");
            }
        }
    }

    // NAV34: same tCa wrapper from original Player source setter must be the
    // same previously observed Track Flow -> Track/Album wrapper in Stage B.
    private static void testNav34LiveOriginalSourceMatchesFlowTrackAlbumWrapper() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        StageBAudioEvidence stage=new StageBAudioEvidence();
        e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        setUpNav29(e);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        stage.enterNativeTrackSourceRequest(track,null);
        try {stage.onNativeTrackWrapperCreated(wrapper);}
        finally {stage.exitNativeTrackSourceRequest();}
        Object renderer=new Object(),stream=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        holder.nested=new FakePeriod(source);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        NativeRendererStreamEvidence.TrackPlayerScope f=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(source);}
        finally {e.exitTrackPlayerSource(f);}
        nav29BindLive(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] report=e.exportLines();
        check(contains(report,"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=ONE"),
              "NAV34_STRICT_ORIGINAL_PLAYER_SOURCE_MATCH");
        check(contains(report,"origin=LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH;error=ONE"),
              "NAV34_IDENTICAL_TCA_REFERENCE_HAS_FLOW_TRACK_AND_ALBUM");
        check(contains(report,"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "NAV34_HISTORICAL_ALBUM_NOT_SELECTED_EDITION_OR_QUEUE_GENERATION");
        // Replacing live SLOT_B invalidates a stale holder link.
        engine.queue.slotB=new FakeHolderSource(source,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH;error=ONE"),
              "NAV34_STALE_QUEUE_CANNOT_ADD_ANOTHER_MATCH");
    }
    private static void testNav34MissingAlbumAndWrongScopedWrapperNeverPromote() {
        for(int mode=0;mode<3;mode++) {
            NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
            StageBAudioEvidence stage=new StageBAudioEvidence();
            e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
            setUpNav29(e);
            Object track=new Object(),album=new Object(),stageWrapper=new Object();
            stage.onNativeTrackAlbumConstructed(track,album);
            stage.onNativeTrackFlowEmission(track);
            stage.enterNativeTrackSourceRequest(track,null);
            try {stage.onNativeTrackWrapperCreated(stageWrapper);}
            finally {stage.exitNativeTrackSourceRequest();}
            if(mode==1)stage.onNativeTrackAlbumConstructed(track,new Object());
            Object playerWrapper=mode==0?new Object():stageWrapper;
            Object renderer=new Object(),stream=new Object();
            FakeSource source=new FakeSource(),playerSource=mode==2?new FakeSource():source;
            FakeHolderSource holder=new FakeHolderSource(source,stream);
            holder.nested=new FakePeriod(source);
            NativeRendererStreamEvidence.TrackPlayerScope f=e.enterTrackPlayerSource(playerWrapper);
            try {e.onNativePlayerSourceSetter(playerSource);}
            finally {e.exitTrackPlayerSource(f);}
            nav29BindLive(e,new FakeActiveEngine(holder),holder,renderer,stream);
            e.onRendererTypeStateRead(renderer,stream,1,2,-4);
            String[] report=e.exportLines();
            check(contains(report,"origin=LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH;error=NONE"),
                  "NAV34_UNRELATED_WRAPPER_CONFLICTED_ALBUM_OR_WRONG_SOURCE_FAIL_CLOSED");
            if(mode<2)check(contains(report,
                    "origin=LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_NO_LINK;error=ONE"),
                    "NAV34_WRAPPER_OR_ALBUM_UNAVAILABLE_EXPLICIT");
            else check(contains(report,"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_NO_LINK;error=ONE"),
                    "NAV34_PLAYER_SOURCE_MISMATCH_NEVER_QUERIES_ALBUM");
        }
    }

    // NAV35: real NAV34 phone had strict source=MANY but album NO_LINK=MANY.
    // Expose the exact reason without ever guessing by title or time.
    private static void testNav35DifferentPlayerWrapperHasExactReason() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        StageBAudioEvidence stage=new StageBAudioEvidence();
        e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        setUpNav29(e);
        Object track=new Object(),album=new Object(),stageWrapper=new Object(),playerWrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        stage.enterNativeTrackSourceRequest(track,null);
        try {stage.onNativeTrackWrapperCreated(stageWrapper);}
        finally {stage.exitNativeTrackSourceRequest();}
        Object renderer=new Object(),stream=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        holder.nested=new FakePeriod(source);
        NativeRendererStreamEvidence.TrackPlayerScope frame=e.enterTrackPlayerSource(playerWrapper);
        try {e.onNativePlayerSourceSetter(source);}
        finally {e.exitTrackPlayerSource(frame);}
        nav29BindLive(e,new FakeActiveEngine(holder),holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] out=e.exportLines();
        check(contains(out,"origin=LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_WRAPPER_ABSENT;error=ONE"),
              "NAV35_SAME_PLAYER_SOURCE_BUT_DIFFERENT_TCA_REFERENCE");
        check(contains(out,"origin=LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH;error=NONE"),
              "NAV35_NEVER_INVENT_ALBUM_ON_DIFFERENT_WRAPPER");
    }

    private static void testNav35AlbumUnsetAndAmbiguousWrapperReasons() {
        for(int mode=0;mode<2;mode++) {
            NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
            StageBAudioEvidence stage=new StageBAudioEvidence();
            e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
            setUpNav29(e);
            Object track=new Object(),wrapper=new Object();
            if(mode==1)stage.onNativeTrackAlbumConstructed(track,new Object());
            stage.onNativeTrackFlowEmission(track);
            stage.enterNativeTrackSourceRequest(track,null);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTrackSourceRequest();}
            if(mode==1) {
                Object anotherTrack=new Object();
                stage.onNativeTrackAlbumConstructed(anotherTrack,new Object());
                stage.onNativeTrackFlowEmission(anotherTrack);
                stage.enterNativeTrackSourceRequest(anotherTrack,null);
                try {stage.onNativeTrackWrapperCreated(wrapper);}
                finally {stage.exitNativeTrackSourceRequest();}
            }
            FakeSource source=new FakeSource();
            Object renderer=new Object(),stream=new Object();
            FakeHolderSource holder=new FakeHolderSource(source,stream);
            holder.nested=new FakePeriod(source);
            NativeRendererStreamEvidence.TrackPlayerScope frame=e.enterTrackPlayerSource(wrapper);
            try {e.onNativePlayerSourceSetter(source);}
            finally {e.exitTrackPlayerSource(frame);}
            nav29BindLive(e,new FakeActiveEngine(holder),holder,renderer,stream);
            e.onRendererTypeStateRead(renderer,stream,1,2,-4);
            String[] out=e.exportLines();
            String expected=mode==0?"ALBUM_UNSET":"WRAPPER_AMBIGUOUS";
            check(contains(out,"origin=LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_"+expected+";error=ONE"),
                  "NAV35_DISTINGUISH_MISSING_ALBUM_FROM_AMBIGUOUS_WRAPPER");
            check(contains(out,"origin=LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH;error=NONE"),
                  "NAV35_NO_FALSE_POSITIVE");
        }
    }

    private static void testNav35WrongPlayerSourceDoesNotClassifyReason() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        StageBAudioEvidence stage=new StageBAudioEvidence();
        e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        setUpNav29(e);
        Object renderer=new Object(),stream=new Object(),wrapper=new Object();
        FakeSource source=new FakeSource(),wrong=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        holder.nested=new FakePeriod(source);
        NativeRendererStreamEvidence.TrackPlayerScope frame=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(wrong);}
        finally {e.exitTrackPlayerSource(frame);}
        nav29BindLive(e,new FakeActiveEngine(holder),holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] out=e.exportLines();
        check(contains(out,"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_NO_LINK;error=ONE"),
              "NAV35_WRONG_SOURCE_REJECTED");
        check(contains(out,"origin=LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_WRAPPER_ABSENT;error=NONE"),
              "NAV35_NOT_CLASSIFIED_WITHOUT_ORIGINAL_SOURCE_MATCH");
        check(contains(out,"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "NAV35_DOES_NOT_ENABLE_REPLACEMENT");
    }

    // NAV36: distinguish exact original tCa constructor histories after
    // the bounded per-wrapper link table evicts the original wrapper. A later
    // wrapper for the same Track is a sibling, not a replacement.
    private static void testNav36OriginalTcaBirthCategories() {
        String[] categories={"NOT_IN_WINDOW","NO_TRACK_SCOPE","TRACK_NOT_IN_FLOW",
            "FLOW_NO_ALBUM","FLOW_ALBUM_LINK_MISSING"};
        for(int mode=0;mode<categories.length;mode++) {
            NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
            StageBAudioEvidence stage=new StageBAudioEvidence();
            e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
            setUpNav29(e);
            Object wrapper=new Object(),track=new Object(),album=new Object();
            if(mode==1)stage.onNativeTrackWrapperCreated(wrapper);
            if(mode==2) {
                stage.enterNativeTrackSourceRequest(track,null);
                try {stage.onNativeTrackWrapperCreated(wrapper);}
                finally {stage.exitNativeTrackSourceRequest();}
            }
            if(mode>=3) {
                if(mode!=3)stage.onNativeTrackAlbumConstructed(track,album);
                stage.onNativeTrackFlowEmission(track);
                stage.enterNativeTrackSourceRequest(track,null);
                try {stage.onNativeTrackWrapperCreated(wrapper);}
                finally {stage.exitNativeTrackSourceRequest();}
                // Evict the first bounded link using unrelated Track objects.
                // The original wrapper birth remains exact and independently
                // classifiable; a same-Track sibling is tested separately by NAV49.
                for(int i=0;i<16;i++) {
                    Object siblingTrack=new Object();
                    if(mode!=3)
                        stage.onNativeTrackAlbumConstructed(siblingTrack,new Object());
                    stage.onNativeTrackFlowEmission(siblingTrack);
                    stage.enterNativeTrackSourceRequest(siblingTrack,null);
                    try {stage.onNativeTrackWrapperCreated(new Object());}
                    finally {stage.exitNativeTrackSourceRequest();}
                }
            }
            FakeSource source=new FakeSource();
            Object renderer=new Object(),stream=new Object();
            FakeHolderSource holder=new FakeHolderSource(source,stream);
            holder.nested=new FakePeriod(source);
            NativeRendererStreamEvidence.TrackPlayerScope frame=e.enterTrackPlayerSource(wrapper);
            try {e.onNativePlayerSourceSetter(source);}
            finally {e.exitTrackPlayerSource(frame);}
            nav29BindLive(e,new FakeActiveEngine(holder),holder,renderer,stream);
            e.onRendererTypeStateRead(renderer,stream,1,2,-4);
            String[] out=e.exportLines();
            check(contains(out,"origin=LIVE_PERIOD_SCOPED_TCA_BIRTH_"
                      +categories[mode]+";error=ONE"),
                  "NAV36_ORIGINAL_CONSTRUCTOR_WITNESS_"+mode);
            check(contains(out,"origin=LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_WRAPPER_ABSENT;error=ONE"),
                  "NAV36_PRESERVES_NAV35_ABSENT_"+mode);
            check(contains(out,"origin=LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH;error=NONE"),
                  "NAV36_NEVER_PROMOTES_HISTORICAL_WRAPPER_"+mode);
        }
    }
    // NAV37: a null exact creator field must not borrow an outer synchronous Track scope.
    private static void testNav37ExactTcaCreatorTrackFieldLinksWrapperAndAlbum() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object owner=new Object(),track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        stage.enterNativeTcaCreatorOwner(owner);
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try { stage.onNativeTrackWrapperCreated(wrapper); }
            finally { stage.exitNativeTcaCreatorTrackScope(); }
        } finally { stage.exitNativeTcaCreatorOwner(); }
        String[] out=stage.exportLines();
        check(contains(out,"origin=TCA_CREATOR_OWNER_ENTER;error=ONE"),
            "NAV37_EXACT_CREATOR_OWNER_ENTER");
        check(contains(out,"origin=TCA_CREATOR_TRACK_FIELD_READ;error=ONE"),
            "NAV37_EXACT_TRACK_FIELD_READ");
        check(contains(out,"origin=TCA_CREATOR_WRAPPER_FLOW_MATCH;error=ONE"),
            "NAV37_CREATOR_TRACK_IS_FLOW_ITEM");
        check(contains(out,"origin=TCA_CREATOR_WRAPPER_ALBUM_LINK;error=ONE"),
            "NAV37_CREATOR_TRACK_ALBUM_LINK");
        check(contains(out,"origin=TRACK_WRAPPER_LINK;error=ONE"),
            "NAV37_EXACT_WRAPPER_TRACK_LINK");
        check(contains(out,"origin=TRACK_WRAPPER_ALBUM_LINK;error=ONE"),
            "NAV37_EXACT_WRAPPER_ALBUM_LINK");
    }

    private static void testNav37NullCreatorTrackFieldShadowsOuterTrackScope() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object owner=new Object(),track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        stage.enterNativeTrackSourceRequest(track,null);
        try {
            stage.enterNativeTcaCreatorOwner(owner);
            try {
                stage.enterNativeTcaCreatorTrackScope(null,2);
                try { stage.onNativeTrackWrapperCreated(wrapper); }
                finally { stage.exitNativeTcaCreatorTrackScope(); }
            } finally { stage.exitNativeTcaCreatorOwner(); }
        } finally { stage.exitNativeTrackSourceRequest(); }
        String[] out=stage.exportLines();
        check(contains(out,"origin=TCA_CREATOR_TRACK_FIELD_NULL;error=ONE"),
            "NAV37_NULL_FIELD_CATEGORIZED");
        check(contains(out,"origin=TCA_CREATOR_WRAPPER_NO_TRACK;error=ONE"),
            "NAV37_NULL_FIELD_SHADOWS_OUTER_SCOPE");
        check(contains(out,"origin=TRACK_WRAPPER_LINK;error=NONE"),
            "NAV37_NULL_FIELD_NEVER_LINKS_OUTER_TRACK");
    }


    private static void testNav38CreatorTrackLaterFlowExactIdentity() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object owner=new Object(),track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(owner);
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        check(contains(stage.exportLines(),"origin=TCA_CREATOR_WRAPPER_NOT_FLOW;error=ONE"),
            "NAV38_NOT_FLOW_AT_BIRTH");
        check(contains(stage.exportLines(),"origin=TCA_CREATOR_NOT_FLOW_ALBUM_OBSERVED;error=ONE"),
            "NAV38_ALBUM_OBSERVED_AT_BIRTH");
        stage.onNativeTrackFlowEmission(new Object());
        check(contains(stage.exportLines(),"origin=TCA_CREATOR_FLOW_LATER_SAME_TRACK;error=NONE"),
            "NAV38_UNRELATED_TRACK_NEVER_MATCHES");
        stage.onNativeTrackFlowEmission(track);
        stage.onNativeTrackFlowEmission(track);
        check(contains(stage.exportLines(),"origin=TCA_CREATOR_FLOW_LATER_SAME_TRACK;error=ONE"),
            "NAV38_LATER_SAME_TRACK_ONCE");
        check(contains(stage.exportLines(),"origin=TCA_CREATOR_FLOW_LATER_ALBUM_OBSERVED;error=ONE"),
            "NAV38_LATER_ALBUM_OBSERVED");
        check(contains(stage.exportLines(),"origin=TRACK_WRAPPER_LINK;error=NONE"),
            "NAV38_NO_FALSE_RETROACTIVE_WRAPPER_LINK");
        StageBAudioEvidence missing=new StageBAudioEvidence();
        Object different=new Object();
        missing.enterNativeTcaCreatorOwner(new Object());
        try {
            missing.enterNativeTcaCreatorTrackScope(different,1);
            try {missing.onNativeTrackWrapperCreated(new Object());}
            finally {missing.exitNativeTcaCreatorTrackScope();}
        } finally {missing.exitNativeTcaCreatorOwner();}
        check(contains(missing.exportLines(),"origin=TCA_CREATOR_NOT_FLOW_ALBUM_UNOBSERVED;error=ONE"),
            "NAV38_NO_ALBUM_OBSERVED");
        missing.onNativeTrackFlowEmission(different);
        check(contains(missing.exportLines(),"origin=TCA_CREATOR_FLOW_LATER_SAME_TRACK;error=ONE"),
            "NAV38_LATE_MATCH_WITHOUT_ALBUM");
        check(contains(missing.exportLines(),"origin=TCA_CREATOR_FLOW_LATER_ALBUM_OBSERVED;error=NONE"),
            "NAV38_NO_FALSE_ALBUM");
        StageBAudioEvidence prior=new StageBAudioEvidence();
        Object priorTrack=new Object();
        prior.onNativeTrackFlowEmission(priorTrack);
        prior.enterNativeTcaCreatorOwner(new Object());
        try {
            prior.enterNativeTcaCreatorTrackScope(priorTrack,1);
            try {prior.onNativeTrackWrapperCreated(new Object());}
            finally {prior.exitNativeTcaCreatorTrackScope();}
        } finally {prior.exitNativeTcaCreatorOwner();}
        prior.onNativeTrackFlowEmission(priorTrack);
        check(contains(prior.exportLines(),"origin=TCA_CREATOR_FLOW_LATER_SAME_TRACK;error=NONE"),
            "NAV38_PRIOR_FLOW_NOT_MISLABELED_LATER");
        check(contains(prior.exportLines(),"origin=CELIKOM_REPLACEMENT;error=NOT_CONNECTED"),
            "NAV38_REPLACEMENT_STAYS_DISABLED");
    }

    // NAV40: the only permissible new proof is original tCa's exact
    // birth-time creator Track, later SAME Flow ref, SAME Album and strictly
    // same live original Player source. Still no edition/queue admission.
    private static void testNav40ExactLaterFlowUnderLiveOriginalSource() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        setUpNav29(e);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==12,"NAV40_NOT_IN_FLOW_AT_BIRTH");
        Object renderer=new Object(),stream=new Object();
        FakeSource source=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        holder.nested=new FakePeriod(source);
        NativeRendererStreamEvidence.TrackPlayerScope scope=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(source);}
        finally {e.exitTrackPlayerSource(scope);}
        nav29BindLive(e,new FakeActiveEngine(holder),holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_SCOPED_TCA_BIRTH_TRACK_NOT_IN_FLOW;error=ONE"),"NAV40_BEFORE_FLOW");
        stage.onNativeTrackFlowEmission(new Object());
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==12,"NAV40_WRONG_TRACK_CANNOT_LINK");
        stage.onNativeTrackFlowEmission(track);
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==16,"NAV40_SAME_TRACK_AND_ALBUM");
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME;error=ONE"),"NAV40_LIVE_SOURCE_SCOPED_SAME");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH;error=NONE"),"NAV40_NO_AT_BIRTH_FALSE_MATCH");
        check(contains(stage.exportLines(),"origin=TRACK_WRAPPER_LINK;error=NONE"),"NAV40_NO_RETROACTIVE_SOURCE");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),"NAV40_NO_SELECTED_EDITION");
        stage.onNativeTrackAlbumConstructed(track,new Object());
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==17,"NAV40_CONFLICT_FAIL_CLOSED");
        NativeRendererStreamEvidence wrong=new NativeRendererStreamEvidence();
        wrong.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        setUpNav29(wrong);
        NativeRendererStreamEvidence.TrackPlayerScope bad=wrong.enterTrackPlayerSource(wrapper);
        try {wrong.onNativePlayerSourceSetter(new FakeSource());}
        finally {wrong.exitTrackPlayerSource(bad);}
        nav29BindLive(wrong,new FakeActiveEngine(holder),holder,renderer,stream);
        wrong.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(wrong.exportLines(),"origin=LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME;error=NONE"),"NAV40_WRONG_SOURCE_CANNOT_CLASSIFY");
    }


    private static void testNav48TcaCreatorFlowBirthSurvivesWrapperLinkEvictionOnLivePeriod() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        e.setExactOriginalTrackAlbumEvidence(stage::exactOriginalTrackAlbumForWrapper);
        setUpNav29(e);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper,"144530503");}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        for(int i=0;i<16;i++) {
            Object otherTrack=new Object(),otherAlbum=new Object(),otherWrapper=new Object();
            stage.onNativeTrackAlbumConstructed(otherTrack,otherAlbum);
            stage.onNativeTrackFlowEmission(otherTrack);
            stage.enterNativeTcaCreatorOwner(new Object());
            try {
                stage.enterNativeTcaCreatorTrackScope(otherTrack,1);
                try {stage.onNativeTrackWrapperCreated(otherWrapper,"987654321");}
                finally {stage.exitNativeTcaCreatorTrackScope();}
            } finally {stage.exitNativeTcaCreatorOwner();}
        }
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==20,
            "NAV48_SAME_CREATOR_TRACK_ALBUM_AT_FLOW_BIRTH_SURVIVES_LINK_EVICTION");
        Object[] pair=stage.exactOriginalTrackAlbumForWrapper(wrapper);
        check(pair!=null && pair[0]==track && pair[1]==album,
            "NAV48_EXACT_BIRTH_PAIR_REMAINS_RECOVERABLE");
        FakeSource source=new FakeSource();
        Object renderer=new Object(),stream=new Object();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        holder.nested=new FakePeriod(source);
        FakeActiveEngine engine=new FakeActiveEngine(holder);
        NativeRendererStreamEvidence.TrackPlayerScope selected=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(source);}
        finally {e.exitTrackPlayerSource(selected);}
        nav29BindLive(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        String[] report=e.exportLines();
        check(contains(report,"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH;error=ONE"),
            "NAV48_EXACT_LIVE_SOURCE_STILL_MATCHES");
        check(contains(report,"origin=LIVE_PERIOD_SCOPED_TCA_BIRTH_FLOW_ALBUM_SAME;error=ONE"),
            "NAV48_CURRENT_DIRECT_PERIOD_RECOVERS_SAME_CREATOR_BIRTH");
        check(contains(report,"origin=LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH;error=ONE"),
            "NAV48_RECOVERED_CREATOR_BIRTH_IS_EXACT_TRACK_ALBUM");
        check(contains(report,"origin=LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_WRAPPER_ABSENT;error=NONE"),
            "NAV48_EVICTED_LINK_NO_LONGER_LOOKS_LIKE_DIFFERENT_WRAPPER");
    }

    private static void testNav36ConstructorWitnessCannotCrossWrongSource() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        StageBAudioEvidence stage=new StageBAudioEvidence();
        e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        setUpNav29(e);
        Object wrapper=new Object(),renderer=new Object(),stream=new Object();
        stage.onNativeTrackWrapperCreated(wrapper);
        FakeSource source=new FakeSource(),wrong=new FakeSource();
        FakeHolderSource holder=new FakeHolderSource(source,stream);
        holder.nested=new FakePeriod(source);
        NativeRendererStreamEvidence.TrackPlayerScope frame=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(wrong);}
        finally {e.exitTrackPlayerSource(frame);}
        nav29BindLive(e,new FakeActiveEngine(holder),holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4);
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_SCOPED_TCA_BIRTH_NO_TRACK_SCOPE;error=NONE"),
              "NAV36_NO_WRONG_SOURCE_CLASSIFICATION");
        check(contains(e.exportLines(),"origin=LIVE_PERIOD_TRACK_WRAPPER_SOURCE_NO_LINK;error=ONE"),
              "NAV36_ORIGINAL_LIVE_SOURCE_GUARD");
    }

    private static final class Nav41Id {
        final Object uid; final int first; final int second;
        Nav41Id(Object uid,int first,int second){
            this.uid=uid;this.first=first;this.second=second;
        }
    }
    private static final class Nav41Info {
        Nav41Id currentId;
        ItemTimeline timeline;
        Nav41Info(Nav41Id id){currentId=id;}
    }
    private static final class Nav41HolderInfo {
        Nav41Id id;
        Nav41HolderInfo(Nav41Id value){id=value;}
    }
    private static final class Nav41Holder {
        Nav41HolderInfo info;
        Object nested; // exact NAV29 fake original period; unused by NAV41 tests
        final Object[] streams;
        Nav41Holder(Nav41Id id,Object stream){
            info=new Nav41HolderInfo(id);streams=new Object[]{stream};
        }
    }
    private static final class Nav41Queue {
        Nav41Holder slotB;
        Nav41Queue(Nav41Holder value){slotB=value;}
    }
    private static final class Nav41Engine {
        Nav41Queue queue;
        Nav41Info playback;
        Nav41Engine(Nav41Holder holder,Nav41Id id){
            queue=new Nav41Queue(holder);playback=new Nav41Info(id);
        }
    }
    private static void nav41Setup(NativeRendererStreamEvidence e) {
        try {
            e.setEngineHolderStreamArrayField(
                Nav41Holder.class.getDeclaredField("streams"));
            e.onHookRegistration("ENGINE_HOLDER_SCOPE",true);
            e.onHookRegistration("SECONDARY_CALLER",true);
            e.onHookRegistration("RENDERER_TYPE_STATE_ACCESS",true);
            e.setLiveQueueSlotFields(Nav41Engine.class.getDeclaredField("queue"),
                Nav41Queue.class.getDeclaredField("slotB"));
            e.onHookRegistration("LIVE_QUEUE_SLOT_B",true);
            e.setCurrentPlaybackPeriodFields(
                Nav41Engine.class.getDeclaredField("playback"),
                Nav41Info.class.getDeclaredField("currentId"),
                Nav41Holder.class.getDeclaredField("info"),
                Nav41HolderInfo.class.getDeclaredField("id"),
                Nav41Id.class.getDeclaredField("uid"),
                Nav41Id.class.getDeclaredField("first"),
                Nav41Id.class.getDeclaredField("second"));
            e.onHookRegistration("PLAYER_PERIOD_AT_AUDIO_READ",true);
        } catch(ReflectiveOperationException ex){throw new AssertionError(ex);}
    }
    private static void nav41Attach(NativeRendererStreamEvidence e,
            Nav41Engine engine,Nav41Holder holder,Object renderer,Object stream) {
        NativeRendererStreamEvidence.EngineFrame f=e.enterEngine(engine,holder);
        NativeRendererStreamEvidence.CallerFrame c=e.enterSecondaryCaller(renderer,stream);
        try{e.onAttach(renderer,stream);}
        finally{e.exitSecondaryCaller(c);e.exitEngine(f);}
    }
    private static void nav47Setup(NativeRendererStreamEvidence e) {
        nav41Setup(e);
        try {
            e.setExactActivePeriodFields(
                Nav41Holder.class.getDeclaredField("nested"),
                FakeNested.class.getDeclaredField("period"),
                FakePeriod.class.getDeclaredField("source"),
                FakeNested.class,FakePeriod.class,FakeSource.class);
            e.setExactActivePeriodStreamFields(
                FakeNested.class.getDeclaredField("adapters"),
                FakeStreamAdapter.class.getDeclaredField("child"),
                FakeNested.class,FakeStreamAdapter.class,FakeSampleStream.class);
            e.onHookRegistration("LIVE_PERIOD_ORIGINAL_SOURCE",true);
            e.onHookRegistration("PERIOD_STREAM_ADAPTER",true);
            e.onHookRegistration("TRACK_PLAYER_SOURCE_SCOPE",true);
            e.onHookRegistration("NATIVE_PLAYER_SOURCE_SETTER",true);
        } catch(ReflectiveOperationException ex) {throw new AssertionError(ex);}
    }

    private static void testNav47ExactAdapterAndCurrentSourceSameStartedRead() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav47Setup(e);
        Object uid=new Object(),renderer=new Object(),wrapper=new Object();
        FakeSource source=new FakeSource();
        FakeStreamAdapter adapter=new FakeStreamAdapter(new FakeChildStream());
        Nav41Id id=new Nav41Id(uid,-1,5);
        Nav41Holder holder=new Nav41Holder(id,adapter);
        holder.nested=new FakeNested(new FakePeriod(source));
        ((FakeNested)holder.nested).adapters=new FakeStreamAdapter[]{adapter};
        Nav41Engine engine=new Nav41Engine(holder,id);
        NativeRendererStreamEvidence.TrackPlayerScope player=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(source);} finally {e.exitTrackPlayerSource(player);}
        nav41Attach(e,engine,holder,renderer,adapter);
        e.onRendererTypeStateRead(renderer,adapter,1,1,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PERIOD_ADAPTER_RENDERER_STREAM_MATCH;error=ONE"),
              "NAV47_EXACT_ADAPTER_REFERENCE_MATCH_WHILE_ENABLED");
        check(contains(e.exportLines(),"origin=PERIOD_ADAPTER_CHILD_STREAM_PRESENT;error=ONE"),
              "NAV47_EXACT_CHILD_STREAM_REFERENCE_PRESENT");
        check(contains(e.exportLines(),"origin=PERIOD_ADAPTER_STARTED_NON_EOS_SOURCE_MATCH;error=NONE"),
              "NAV47_ENABLED_IS_NOT_STARTED");
        e.onRendererTypeStateRead(renderer,adapter,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PERIOD_ADAPTER_STARTED_NON_EOS_SOURCE_MATCH;error=ONE"),
              "NAV47_SAME_CALLBACK_STARTED_NON_EOS_LIVE_SLOT_SOURCE_MATCH");
    }

    private static void testNav47DifferentRendererStreamCannotMatchPeriodAdapter() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav47Setup(e);
        Object uid=new Object(),renderer=new Object(),wrapper=new Object();
        FakeSource source=new FakeSource();
        FakeStreamAdapter adapter=new FakeStreamAdapter(new FakeChildStream());
        Object differentStream=new Object();
        Nav41Id id=new Nav41Id(uid,-1,6);
        Nav41Holder holder=new Nav41Holder(id,differentStream);
        holder.nested=new FakeNested(new FakePeriod(source));
        ((FakeNested)holder.nested).adapters=new FakeStreamAdapter[]{adapter};
        Nav41Engine engine=new Nav41Engine(holder,id);
        NativeRendererStreamEvidence.TrackPlayerScope player=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(source);} finally {e.exitTrackPlayerSource(player);}
        nav41Attach(e,engine,holder,renderer,differentStream);
        e.onRendererTypeStateRead(renderer,differentStream,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PERIOD_ADAPTER_RENDERER_STREAM_DIFFERENT;error=ONE"),
              "NAV47_DIFFERENT_STREAM_REJECTED");
        check(contains(e.exportLines(),"origin=PERIOD_ADAPTER_STARTED_NON_EOS_SOURCE_MATCH;error=NONE"),
              "NAV47_DIFFERENT_STREAM_CANNOT_PROMOTE");
    }

    private static void testNav47AdapterWithoutChildCannotPromote() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav47Setup(e);
        Object uid=new Object(),renderer=new Object(),wrapper=new Object();
        FakeSource source=new FakeSource();
        FakeStreamAdapter adapter=new FakeStreamAdapter(null);
        Nav41Id id=new Nav41Id(uid,-1,7);
        Nav41Holder holder=new Nav41Holder(id,adapter);
        holder.nested=new FakeNested(new FakePeriod(source));
        ((FakeNested)holder.nested).adapters=new FakeStreamAdapter[]{adapter};
        Nav41Engine engine=new Nav41Engine(holder,id);
        NativeRendererStreamEvidence.TrackPlayerScope player=e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(source);} finally {e.exitTrackPlayerSource(player);}
        nav41Attach(e,engine,holder,renderer,adapter);
        e.onRendererTypeStateRead(renderer,adapter,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PERIOD_ADAPTER_RENDERER_STREAM_MATCH;error=ONE"),
              "NAV47_ADAPTER_REFERENCE_SEEN");
        check(contains(e.exportLines(),"origin=PERIOD_ADAPTER_CHILD_STREAM_MISSING;error=ONE"),
              "NAV47_MISSING_CHILD_EXPLICIT");
        check(contains(e.exportLines(),"origin=PERIOD_ADAPTER_STARTED_NON_EOS_SOURCE_MATCH;error=NONE"),
              "NAV47_MISSING_CHILD_CANNOT_PROMOTE");
    }

    private static void testNav50AlternateSourceReadIsJoinedToLiveCurrentPeriod() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav47Setup(e);
        Object uid=new Object(),wrapper=new Object(),renderer=new Object(),stream=new Object();
        FakeSource source=new FakeSource();
        Nav41Id id=new Nav41Id(uid,-1,5);
        Nav41Holder holder=new Nav41Holder(id,stream);
        holder.nested=new FakePeriod(source); // exact direct Lo96 holder path
        Nav41Engine engine=new Nav41Engine(holder,id);
        NativeRendererStreamEvidence.TrackPlayerScope player=
            e.enterTrackPlayerSource(wrapper);
        try {e.onNativePlayerSourceSetter(source);}
        finally {e.exitTrackPlayerSource(player);}
        e.setAlternateSourceReadEvidence(w -> w==wrapper ? 1 : -2);
        nav41Attach(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),
            "origin=LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD;error=ONE"),
            "NAV50_SAME_ARMED_DATASOURCE_IS_IN_LIVE_UNKNOWN_EOS_PERIOD");
        check(contains(e.exportLines(),
            "origin=LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_EOS_UNKNOWN;error=ONE"),
            "NAV50_UNKNOWN_EOS_REMAINS_SEPARATE");
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),
            "origin=LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS;error=ONE"),
            "NAV50_SAME_ARMED_DATASOURCE_REACHES_LIVE_NON_EOS_RENDERER_READ");

        NativeRendererStreamEvidence different=new NativeRendererStreamEvidence();
        nav47Setup(different);
        Object otherUid=new Object(),otherWrapper=new Object();
        Object otherRenderer=new Object(),otherStream=new Object();
        FakeSource otherSource=new FakeSource();
        Nav41Id otherId=new Nav41Id(otherUid,-1,6);
        Nav41Holder otherHolder=new Nav41Holder(otherId,otherStream);
        otherHolder.nested=new FakePeriod(otherSource);
        Nav41Engine otherEngine=new Nav41Engine(otherHolder,otherId);
        NativeRendererStreamEvidence.TrackPlayerScope otherPlayer=
            different.enterTrackPlayerSource(otherWrapper);
        try {different.onNativePlayerSourceSetter(otherSource);}
        finally {different.exitTrackPlayerSource(otherPlayer);}
        different.setAlternateSourceReadEvidence(w -> -1);
        nav41Attach(different,otherEngine,otherHolder,otherRenderer,otherStream);
        different.onRendererTypeStateRead(otherRenderer,otherStream,1,2,-4,Boolean.FALSE);
        check(contains(different.exportLines(),
            "origin=LIVE_RENDERER_ALT_SOURCE_DIFFERENT_CURRENT_PERIOD;error=ONE"),
            "NAV50_PREFETCH_OR_STALE_DATASOURCE_CANNOT_CLAIM_LIVE_RENDERER");
        check(contains(different.exportLines(),
            "origin=LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD;error=NONE"),
            "NAV50_DIFFERENT_DATASOURCE_NEVER_COUNTS_AS_ACTIVE_ALTERNATE");
    }

    private static void testNav41OnlySameNonEosSlotBReadExaminesCurrentPeriod() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav41Setup(e);
        Object uid=new Object(),stream=new Object(),renderer=new Object();
        Nav41Id current=new Nav41Id(uid,-1,3);
        Nav41Holder h=new Nav41Holder(current,stream);
        Nav41Engine engine=new Nav41Engine(h,current);
        nav41Attach(e,engine,h,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_AT_READ_SAME_REFERENCE;error=ONE"),
            "NAV41_READ_EXACT_SAME_ID_REFERENCE");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
            "NAV41_NO_FALSE_SELECTED_ITEM");
        // EOS, not sample, non-audio and a changed live slot must not count.
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.TRUE);
        e.onRendererTypeStateRead(renderer,stream,1,2,-3,Boolean.FALSE);
        e.onRendererTypeStateRead(renderer,stream,2,2,-4,Boolean.FALSE);
        engine.queue.slotB=new Nav41Holder(current,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_AT_READ_SAME_REFERENCE;error=ONE"),
            "NAV41_INELIGIBLE_PATH_NOT_COUNTED");
    }
    private static void testNav41RejectUidOnlyAndOldPeriodSameUidNotEdition() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav41Setup(e);
        Object uid=new Object(),stream=new Object(),renderer=new Object();
        Nav41Holder h=new Nav41Holder(new Nav41Id(uid,-1,5),stream);
        Nav41Engine engine=new Nav41Engine(h,new Nav41Id(uid,-1,5));
        nav41Attach(e,engine,h,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_AT_READ_UID_AND_INDEX_MATCH;error=ONE"),
            "NAV41_EQUAL_VALUES_NOT_GENERATION");
        engine.playback.currentId=new Nav41Id(uid,-1,6);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_AT_READ_UID_ONLY;error=ONE"),
            "NAV41_REPLAY_OR_STALE_ID_UID_ONLY");
        engine.playback.currentId=new Nav41Id(new Object(),-1,5);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_AT_READ_DIFFERENT;error=ONE"),
            "NAV41_OLD_OR_NEXT_PERIOD_DIFFERENT");
        engine.playback.currentId=null;
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_AT_READ_UNAVAILABLE;error=ONE"),
            "NAV41_NULL_FAILS_CLOSED");
        for(String line:e.exportLines()) {
            check(!line.contains("uid@") && !line.contains("Nav41Id@"),
                "NAV41_NO_PRIVATE_OBJECT_ID_EXPORT");
        }
    }
    private static void testNav41NoFieldsOrNoActiveSlotCannotProduceMatch() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object uid=new Object(),stream=new Object(),renderer=new Object();
        Nav41Id current=new Nav41Id(uid,-1,1);
        Nav41Holder h=new Nav41Holder(current,stream);
        Nav41Engine engine=new Nav41Engine(h,current);
        nav41Setup(e);
        e.onHookRegistration("PLAYER_PERIOD_AT_AUDIO_READ",false);
        nav41Attach(e,engine,h,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.FALSE);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_AT_READ_SAME_REFERENCE;error=NONE"),
              "NAV41_NO_UNREGISTERED_POSITIVE");
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_AT_AUDIO_READ;error=NO_HOOK"),
              "NAV41_MISSING_REGISTRATION_EXPLICIT");
    }


    // NAV42: the actual owner NAV41 diagnostic has original -4 reads on
    // live SLOT_B, but RF2 EOS accessor is not readable. Do not suppress all
    // structural PeriodID evidence, and do not mislabel it as non-EOS.
    private static void testNav42UnknownEosUsesSeparateStructuralCohorts() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav41Setup(e);
        Object uid=new Object(),stream=new Object(),renderer=new Object();
        Nav41Id id=new Nav41Id(uid,-1,7);
        Nav41Holder h=new Nav41Holder(id,stream);
        Nav41Engine engine=new Nav41Engine(h,id);
        nav41Attach(e,engine,h,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_SAME_REF;error=ONE"),
            "NAV42_UNKNOWN_EOS_SAME_REFERENCE_OBSERVED");
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_AT_READ_SAME_REFERENCE;error=NONE"),
            "NAV42_UNKNOWN_EOS_NEVER_NON_EOS_PROMOTED");
        check(contains(e.exportLines(),"origin=ENGINE_AUDIO_TYPE1_STATE2_BUFFER_NON_EOS;error=NONE"),
            "NAV42_NO_FAKE_BUFFER_NEGATIVE");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
            "NAV42_NO_FAKE_SELECTED_EDITION");
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.TRUE);
        e.onRendererTypeStateRead(renderer,stream,1,2,-3,null);
        e.onRendererTypeStateRead(renderer,stream,2,2,-4,null);
        e.onRendererTypeStateRead(renderer,stream,1,1,-4,null);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_SAME_REF;error=ONE"),
            "NAV42_EOS_TRUE_OR_NON_AUDIO_NOT_COUNTED");
    }
    private static void testNav42UnknownEosUidAndIndexAndStaleGuard() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav41Setup(e);
        Object uid=new Object(),stream=new Object(),renderer=new Object();
        Nav41Holder h=new Nav41Holder(new Nav41Id(uid,-1,4),stream);
        Nav41Engine engine=new Nav41Engine(h,new Nav41Id(uid,-1,4));
        nav41Attach(e,engine,h,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS;error=ONE"),
            "NAV42_UNKNOWN_VALUE_MATCH_NOT_SAME_JAVA_REFERENCE");
        engine.playback.currentId=new Nav41Id(uid,-1,6);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_UID_ONLY;error=ONE"),
            "NAV42_REPLAY_UID_ONLY");
        engine.playback.currentId=new Nav41Id(new Object(),-1,4);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_DIFFERENT;error=ONE"),
            "NAV42_DIFFERENT_PERIOD");
        engine.playback.currentId=null;
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_UNAVAILABLE;error=ONE"),
            "NAV42_NULL_FAIL_CLOSED");
        engine.playback.currentId=h.info.id;
        engine.queue.slotB=new Nav41Holder(h.info.id,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_SAME_REF;error=NONE"),
            "NAV42_CHANGED_SLOT_REJECTED");
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS;error=ONE"),
            "NAV42_CHANGED_SLOT_NOT_MATCHED");
        for(String line:e.exportLines()) {
            check(!line.contains("uid@") && !line.contains("Nav41Id@"),
                "NAV42_NEVER_EXPORT_RAW_IDENTITIES");
        }
    }
    private static void testNav42DisabledPeriodHookAndReattachNeverMatch() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav41Setup(e);
        Object stream=new Object(),renderer=new Object();
        Nav41Id id=new Nav41Id(new Object(),-1,8);
        Nav41Holder h=new Nav41Holder(id,stream);
        Nav41Engine engine=new Nav41Engine(h,id);
        nav41Attach(e,engine,h,renderer,stream);
        e.onHookRegistration("PLAYER_PERIOD_AT_AUDIO_READ",false);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_SAME_REF;error=NONE"),
            "NAV42_NO_HOOK_NO_PROOF");
        e.onHookRegistration("PLAYER_PERIOD_AT_AUDIO_READ",true);
        e.onDetach(renderer);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),"origin=PLAYER_PERIOD_EOS_UNKNOWN_SAME_REF;error=NONE"),
            "NAV42_DETACHED_NO_PROOF");
    }


    private static void nav43SetupLiveSource(NativeRendererStreamEvidence e) {
        try {
            e.setExactActivePeriodFields(
                Nav41Holder.class.getDeclaredField("nested"),
                FakeNested.class.getDeclaredField("period"),
                FakePeriod.class.getDeclaredField("source"),
                FakeNested.class,FakePeriod.class,FakeSource.class);
            e.onHookRegistration("LIVE_PERIOD_ORIGINAL_SOURCE",true);
            e.onHookRegistration("TRACK_PLAYER_SOURCE_SCOPE",true);
            e.onHookRegistration("NATIVE_PLAYER_SOURCE_SETTER",true);
        } catch(ReflectiveOperationException ex) {throw new AssertionError(ex);}
    }

    private static void nav43LinkOriginalSource(NativeRendererStreamEvidence e,
            Object wrapper,FakeSource source) {
        NativeRendererStreamEvidence.TrackPlayerScope scope=e.enterTrackPlayerSource(wrapper);
        try{e.onNativePlayerSourceSetter(source);}
        finally{e.exitTrackPlayerSource(scope);}
    }

    private static void testNav43JointUnknownEosExactSourceAndPlayerSameRead() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav41Setup(e);
        nav43SetupLiveSource(e);
        e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        e.setExactOriginalTrackAlbumEvidence(stage::exactOriginalTrackAlbumForWrapper);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        final int[] exactLiveObservations={0};
        // Never permit a prefetch/stale/other source callback to claim this
        // exact original Track, Album and active native source as selected.
        final Object[] sourceForOriginalIdentity={null};
        e.setActiveOriginalTrackObserver((t,audioAlbum,audioSource)->{
            check(t==track && audioAlbum==album
                && audioSource==sourceForOriginalIdentity[0],
                "NAV46_SAME_JAVA_OBJECTS_ACTIVE_ORIGINAL_SOURCE");
            exactLiveObservations[0]++;
        });
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try{stage.onNativeTrackWrapperCreated(wrapper);}
            finally{stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        stage.onNativeTrackFlowEmission(track);
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==16,
            "NAV43_TEST_FIXTURE_EXACT_LATE_FLOW");

        Object uid=new Object(),stream=new Object(),renderer=new Object();
        Nav41Id originalId=new Nav41Id(uid,-1,5);
        Nav41Holder h=new Nav41Holder(originalId,stream);
        FakeSource originalSource=new FakeSource();
        sourceForOriginalIdentity[0]=originalSource;
        h.nested=new FakeNested(new FakePeriod(originalSource));
        Nav41Engine engine=new Nav41Engine(h,new Nav41Id(uid,-1,5));
        nav43LinkOriginalSource(e,wrapper,originalSource);
        nav41Attach(e,engine,h,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(exactLiveObservations[0]==1,
            "NAV46_CURRENT_ORIGINAL_TRACK_SOURCE_REFERENCE_DELIVERED");
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK;error=ONE"),
            "NAV43_EXACT_CALLBACK_JOIN");
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS;error=ONE"),
            "NAV43_ORIGINAL_PLAYER_PERIOD_BOUND");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
            "NAV43_DOES_NOT_CLAIM_SELECTED_EDITION");

        // Same holder/UID but a fresh queue sequence is NOT this selection.
        engine.playback.currentId=new Nav41Id(uid,-1,6);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(exactLiveObservations[0]==1,"NAV46_REPLAY_GENERATION_CHANGE_REJECTED");
        engine.playback.currentId=new Nav41Id(uid,-1,5);
        // The original source can change without the SLOT_B pointer changing.
        ((FakePeriod)((FakeNested)h.nested).period).source=new FakeSource();
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(exactLiveObservations[0]==1,"NAV46_SOURCE_REBIND_REJECTED");
        ((FakePeriod)((FakeNested)h.nested).period).source=originalSource;
        stage.onNativeTrackAlbumConstructed(track,new Object());
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(exactLiveObservations[0]==1,"NAV46_ALBUM_CONFLICT_REJECTED");

        // EOS, wrong read code, wrong player period and changed queue slot
        // never turn the one earlier positive into another callback join.
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,Boolean.TRUE);
        e.onRendererTypeStateRead(renderer,stream,1,2,-3,null);
        engine.playback.currentId=new Nav41Id(new Object(),-1,5);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        engine.queue.slotB=new Nav41Holder(originalId,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK;error=ONE"),
            "NAV43_NO_STALE_EXTRA_JOIN");
        check(exactLiveObservations[0]==1,
            "NAV46_NO_ORIGINAL_TRACK_DELIVERY_AFTER_EOS_NEXT_OR_DETACH");
    }

    private static void testNav43JointRequiresFlowAndUniqueSourceAndStableSlot() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav41Setup(e);
        nav43SetupLiveSource(e);
        Object uid=new Object(),stream=new Object(),renderer=new Object(),wrapper=new Object();
        Nav41Id originalId=new Nav41Id(uid,-1,6);
        Nav41Holder h=new Nav41Holder(originalId,stream);
        FakeSource originalSource=new FakeSource();
        h.nested=new FakeNested(new FakePeriod(originalSource));
        Nav41Engine engine=new Nav41Engine(h,new Nav41Id(uid,-1,6));
        nav41Attach(e,engine,h,renderer,stream);
        nav43LinkOriginalSource(e,wrapper,originalSource);
        // No exact same-flow original Track/Album classification.
        e.setScopedAlbumEvidence(x->12);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_NO_LINK;error=ONE"),
            "NAV43_NO_LATE_FLOW_DOES_NOT_JOIN");
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK;error=NONE"),
            "NAV43_NO_PRIOR_FALSE_POSITIVE");
        // Same callback but queue slot changes inside source observer.
        e.setScopedAlbumEvidence(x->{engine.queue.slotB=new Nav41Holder(originalId,stream);return 16;});
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SLOT_CHANGED;error=ONE"),
            "NAV43_CHANGED_SLOT_DURING_SOURCE_CLASSIFICATION_REJECTED");
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK;error=NONE"),
            "NAV43_NO_SLOT_LEAK");
    }

    private static void testNav43MissingSourceNoHistoryJoin() {
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav41Setup(e);
        nav43SetupLiveSource(e);
        Object uid=new Object(),stream=new Object(),renderer=new Object(),wrapper=new Object();
        Nav41Id id=new Nav41Id(uid,-1,4);
        Nav41Holder h=new Nav41Holder(id,stream);
        h.nested=new FakeNested(new FakePeriod(new FakeSource()));
        Nav41Engine engine=new Nav41Engine(h,new Nav41Id(uid,-1,4));
        // Wrong original source in a different player scope.
        nav43LinkOriginalSource(e,wrapper,new FakeSource());
        e.setScopedAlbumEvidence(x->16);
        nav41Attach(e,engine,h,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_NO_LINK;error=ONE"),
            "NAV43_WRONG_SOURCE_FAIL_CLOSED");
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK;error=NONE"),
            "NAV43_WRONG_SOURCE_NO_FALSE_JOIN");
    }

    // NAV44 isolated, publisher-shaped fake objects. No raw identifiers,
    // metadata or source content in these tests.
    private static final class ItemPeriod { int windowIndex; }
    private static final class ItemWindow { FakeMediaItem mediaItem; }
    private static final class ItemTimeline {
        final Object uid;
        final FakeMediaItem item;
        Runnable afterWindow;
        ItemTimeline(Object uid,FakeMediaItem item){this.uid=uid;this.item=item;}
        ItemPeriod getPeriodByUid(Object searched,ItemPeriod scratch){
            if(searched!=uid)return null;
            scratch.windowIndex=0;
            return scratch;
        }
        ItemWindow getWindow(int index,ItemWindow scratch,long projectionUs){
            if(index!=0)return null;
            scratch.mediaItem=item;
            if(afterWindow!=null)afterWindow.run();
            return scratch;
        }
    }

    private static void nav44SetupItem(NativeRendererStreamEvidence e) {
        try {
            e.setSelectedMediaItemSourceFields(
                Nav41Info.class.getDeclaredField("timeline"),
                ItemPeriod.class.getDeclaredField("windowIndex"),
                ItemWindow.class.getDeclaredField("mediaItem"),
                FakeSource.class.getDeclaredField("item"),
                ItemTimeline.class.getDeclaredMethod("getPeriodByUid",
                    Object.class,ItemPeriod.class),
                ItemTimeline.class.getDeclaredMethod("getWindow",
                    int.class,ItemWindow.class,long.class),
                ItemPeriod.class.getDeclaredConstructor(),
                ItemWindow.class.getDeclaredConstructor());
            e.onHookRegistration("CURRENT_MEDIAITEM_SOURCE",true);
            e.setSelectedLogicalMediaIdField(
                FakeMediaItem.class.getDeclaredField("mediaId"));
            e.onHookRegistration("CURRENT_MEDIAITEM_LOGICAL_ID",true);
        } catch(ReflectiveOperationException ex){throw new AssertionError(ex);}
    }

    private static void testNav44OriginalTimelineAndSourceSameItem() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        nav41Setup(e);
        nav43SetupLiveSource(e);
        nav44SetupItem(e);
        e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try{
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try{stage.onNativeTrackWrapperCreated(wrapper);}
            finally{stage.exitNativeTcaCreatorTrackScope();}
        } finally{stage.exitNativeTcaCreatorOwner();}
        stage.onNativeTrackFlowEmission(track);
        Object uid=new Object();
        FakeMediaItem item=new FakeMediaItem("TRACK_11");
        Object renderer=new Object(),stream=new Object();
        Nav41Id period=new Nav41Id(uid,-1,11);
        Nav41Holder holder=new Nav41Holder(period,stream);
        FakeSource source=new FakeSource();source.item=item;
        holder.nested=new FakeNested(new FakePeriod(source));
        Nav41Engine engine=new Nav41Engine(holder,new Nav41Id(uid,-1,11));
        engine.playback.timeline=new ItemTimeline(uid,item);
        nav43LinkOriginalSource(e,wrapper,source);
        nav41Attach(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(contains(e.exportLines(),
            "origin=PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK;error=FEW"),
            "NAV44_NAV43_JOINT_STILL_ACTIVE");
        check(contains(e.exportLines(),
            "origin=PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_SAME_REF;error=ONE"),
            "NAV44_LIVE_ORIGINAL_ITEM_SAME_REF");
        check(contains(e.exportLines(),
            "origin=PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_DIFFERENT;error=NONE"),
            "NAV44_NO_FALSE_DIFFERENT");
        check(contains(e.exportLines(),
            "origin=PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_MATCH;error=ONE"),
            "NAV45_SAME_REF_AND_SAME_NONEMPTY_ID");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
            "NAV44_MEDIAITEM_IS_NOT_TRACK_EDITION_OR_PCM");
    }

    private static void testNav44DifferentAndChangedSlotFailClosed() {
        for(int scenario=0;scenario<5;scenario++){
            StageBAudioEvidence stage=new StageBAudioEvidence();
            NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
            nav41Setup(e);
            nav43SetupLiveSource(e);
            nav44SetupItem(e);
            e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
            Object track=new Object(),album=new Object(),wrapper=new Object();
            stage.onNativeTrackAlbumConstructed(track,album);
            stage.enterNativeTcaCreatorOwner(new Object());
            try {
                stage.enterNativeTcaCreatorTrackScope(track,1);
                try{stage.onNativeTrackWrapperCreated(wrapper);}
                finally{stage.exitNativeTcaCreatorTrackScope();}
            } finally {stage.exitNativeTcaCreatorOwner();}
            stage.onNativeTrackFlowEmission(track);
            Object uid=new Object(),renderer=new Object(),stream=new Object();
            Nav41Id id=new Nav41Id(uid,-1,12);
            Nav41Holder holder=new Nav41Holder(id,stream);
            FakeSource source=new FakeSource();
            source.item=new FakeMediaItem(scenario==4?"":"TRACK_12");
            holder.nested=new FakeNested(new FakePeriod(source));
            Nav41Engine engine=new Nav41Engine(holder,new Nav41Id(uid,-1,12));
            ItemTimeline timeline=new ItemTimeline(uid,
                scenario==2?source.item:
                    new FakeMediaItem(scenario==3?"DIFFERENT_TRACK":"TRACK_12"));
            engine.playback.timeline=timeline;
            if(scenario==1)timeline.afterWindow=()->
                engine.queue.slotB=new Nav41Holder(id,stream);
            if(scenario==2)timeline.afterWindow=()->
                holder.nested=new FakeNested(new FakePeriod(new FakeSource()));
            nav43LinkOriginalSource(e,wrapper,source);
            nav41Attach(e,engine,holder,renderer,stream);
            e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
            if(scenario==0 || scenario==3 || scenario==4) {
                check(contains(e.exportLines(),
                    "origin=PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_DIFFERENT;error=ONE"),
                    "NAV44_DIFFERENT_MEDIAITEM_NEVER_MATCHES");
                if(scenario==0)check(contains(e.exportLines(),
                    "origin=PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_MATCH;error=ONE"),
                    "NAV45_DISTINCT_JAVA_ITEMS_SAME_LOGICAL_ID");
                if(scenario==3)check(contains(e.exportLines(),
                    "origin=PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_DIFFERENT;error=ONE"),
                    "NAV45_DIFFERENT_NONEMPTY_IDS_NOT_PROMOTED");
                if(scenario==4)check(contains(e.exportLines(),
                    "origin=PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_BLANK;error=ONE"),
                    "NAV45_DEFAULT_EMPTY_ID_NOT_PROMOTED");
            } else {
                check(contains(e.exportLines(),
                    "origin=PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_SLOT_CHANGED;error=ONE"),
                    scenario==1?"NAV44_WINDOW_LOOKUP_CHANGE_REJECTS":
                        "NAV44_SAME_HOLDER_DIFFERENT_PERIOD_SOURCE_REJECTS");
            }
            check(contains(e.exportLines(),
                "origin=PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_SAME_REF;error=NONE"),
                "NAV44_NEGATIVE_NEVER_PROMOTES");
        }
    }

    private static void testOriginalCreatorEarlySourceSetterBeforeFlow() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object(),source=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        check(stage.exactOriginalTrackAlbumForWrapper(wrapper)==null,
              "FLOW_PROOF_NOT_AVAILABLE_BEFORE_FLOW");
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        final int[] called={0,0,0};
        final long[] lastGeneration={0};
        e.setEarlyOriginalSourceObserver(new NativeRendererStreamEvidence.EarlyOriginalSourceObserver() {
            public void pending(long generation,Object actualTrack,Object actualAlbum,
                                Object actualSource) {
                check(actualTrack==track && actualAlbum==album && actualSource==source,
                      "EARLY_EXACT_CREATOR_ORIGINAL_REFERENCES");
                check(generation>lastGeneration[0],"EARLY_MONOTONIC_SOURCE_GENERATION");
                lastGeneration[0]=generation;
                called[0]++;
            }
            public void completed(long generation,boolean succeeded) {
                check(generation==lastGeneration[0],"EARLY_SAME_GENERATION");
                if(succeeded)called[1]++;else called[2]++;
            }
        });
        NativeRendererStreamEvidence.TrackPlayerScope scope=e.enterTrackPlayerSource(wrapper);
        try {
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame f=
                e.beginEarlyOriginalSourceSet(source);
            check(f!=null && called[0]==1,"EARLY_CREATOR_BOUND_BEFORE_ORIGINAL_SETTER");
            // Original setter executes exactly once externally; finality is
            // observed only after it returns successfully.
            e.finishEarlyOriginalSourceSet(f,true);
            check(called[1]==1 && called[2]==0,"EARLY_VALID_SETTER_COMPLETION");
            Object[] proof=e.exactEarlySetterSourceAtGeneration(source,f.generation);
            check(proof!=null && proof.length==3 && proof[0]==track
                && proof[1]==album && proof[2]==source,
                "EARLY_COMMITTED_EXACT_SOURCE_SAME_GENERATION");
            check(e.exactEarlySetterSourceAtGeneration(new Object(),f.generation)==null,
                "EARLY_DIFFERENT_SOURCE_NOT_MATCHED");
            check(e.exactEarlySetterSourceAtGeneration(source,f.generation+1)==null,
                "EARLY_GUESSED_GENERATION_REJECTED");
        } finally {e.exitTrackPlayerSource(scope);}
        check(e.beginEarlyOriginalSourceSet(source)==null,
              "EARLY_UNSCOPED_SETTER_FAILS_CLOSED");
        check(e.exactEarlySetterSourceAtGeneration(source,lastGeneration[0])==null,
              "UNSCOPED_NEXT_INVALIDATES_OLD_SUCCESS");
        check(contains(e.exportLines(),"origin=IDENTITY_STATUS;error=STRUCTURAL_ONLY"),
              "EARLY_IDENTITY_NEVER_UPGRADED_TO_AUDIO");
    }

    private static void testEarlySourceFailureConflictAndNextGeneration() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        final int[] pending={0},complete={0},rejected={0};
        e.setEarlyOriginalSourceObserver(new NativeRendererStreamEvidence.EarlyOriginalSourceObserver() {
            public void pending(long generation,Object a,Object b,Object c){pending[0]++;}
            public void completed(long generation,boolean success) {
                complete[0]++;if(!success)rejected[0]++;
            }
        });
        NativeRendererStreamEvidence.TrackPlayerScope scope=e.enterTrackPlayerSource(wrapper);
        try {
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame first=
                e.beginEarlyOriginalSourceSet(new Object());
            check(first!=null,"EARLY_PENDING_FIRST");
            check(e.beginEarlyOriginalSourceSet(new Object())==null,
                  "OVERLAPPING_SETTER_NOT_ADMITTED");
            e.finishEarlyOriginalSourceSet(first,true);
            check(rejected[0]==1,"OVERLAPPING_INVALIDATES_PREVIOUS_GENERATION");
            check(e.exactEarlySetterSourceAtGeneration(first.source,first.generation)==null,
                "NESTED_OVERLAP_CANNOT_CREATE_COMMITTED_ORIGINAL_LINK");
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame failed=
                e.beginEarlyOriginalSourceSet(new Object());
            check(failed!=null,"FAILURE_ATTEMPT_CAN_OBSERVE_PENDING");
            e.finishEarlyOriginalSourceSet(failed,false);
            check(rejected[0]==2,"THROWING_SETTER_MUST_ROLLBACK_PENDING");
            check(e.exactEarlySetterSourceAtGeneration(failed.source,failed.generation)==null,
                "THROWING_SETTER_NO_SOURCE_PROOF");
            // Same wrapper's original Album has changed after construction.
            stage.onNativeTrackAlbumConstructed(track,new Object());
            check(e.beginEarlyOriginalSourceSet(new Object())==null,
                  "CONFLICTING_ALBUM_BEFORE_SETTER_REJECTED");
        } finally {e.exitTrackPlayerSource(scope);}
        check(pending[0]==2 && complete[0]==2,
              "ONLY_EXACT_EARLY_CREATOR_SELECTIONS_NOTIFIED");
        check(stage.exactCreatorTrackAlbumBeforeSourceSet(new Object())==null,
              "UNRELATED_WRAPPER_NO_EARLY_IDENTITY");
    }

    private static void testEarlySetterWhenFlowPrecedesWrapperBirth() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object(),source=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==1,
              "FLOW_BEFORE_WRAPPER_STAYS_EXACT");
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        NativeRendererStreamEvidence.TrackPlayerScope scope=e.enterTrackPlayerSource(wrapper);
        try {
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame pending=
                e.beginEarlyOriginalSourceSet(source);
            check(pending!=null && pending.track==track && pending.album==album,
                  "FLOW_FIRST_CREATOR_REACHES_EARLY_ORIGINAL_SETTER");
            e.finishEarlyOriginalSourceSet(pending,true);
            check(e.exactEarlySetterSourceAtGeneration(source,pending.generation)!=null,
                  "FLOW_FIRST_SUCCESSFUL_ORIGINAL_SETTER_LINEAGE");
            stage.onNativeTrackAlbumConstructed(track,new Object());
            check(e.exactEarlySetterSourceAtGeneration(source,pending.generation)==null,
                  "ALBUM_CONFLICT_INVALIDATES_COMMITTED_LINEAGE");
        } finally {e.exitTrackPlayerSource(scope);}
    }

    private static void testEarlySetterSameSourceReachesActualCurrentPeriod() {
        final long[] now={100};
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        NativeEarlySourceLifecycleBridge bridge=
            new NativeEarlySourceLifecycleBridge(() -> now[0]);
        nav41Setup(e);
        nav43SetupLiveSource(e);
        e.setScopedAlbumEvidence(stage::classifyNativeTrackAlbumForWrapper);
        e.setExactOriginalTrackAlbumEvidence(stage::exactOriginalTrackAlbumForWrapper);
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        e.setEarlyOriginalSourceObserver(bridge);
        e.setActiveOriginalTrackObserver(bridge);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        stage.onNativeTrackFlowEmission(track);
        FakeSource source=new FakeSource();
        NativeRendererStreamEvidence.TrackPlayerScope scope=e.enterTrackPlayerSource(wrapper);
        NativeRendererStreamEvidence.EarlyOriginalSourceFrame early;
        try {
            early=e.beginEarlyOriginalSourceSet(source);
            check(early!=null,"LIVE_EARLY_SETTER_HAS_CREATOR_PAIR");
            e.onNativePlayerSourceSetter(source);
            e.finishEarlyOriginalSourceSet(early,true);
        } finally {e.exitTrackPlayerSource(scope);}
        check(!bridge.wasCurrentOriginalSource(early.generation,track,album,source),
            "ORIGINAL_SETTER_ONLY_IS_NOT_ACTIVE_RENDERER_PROOF");
        Object uid=new Object(),stream=new Object(),renderer=new Object();
        Nav41Id originalId=new Nav41Id(uid,-1,5);
        Nav41Holder holder=new Nav41Holder(originalId,stream);
        holder.nested=new FakeNested(new FakePeriod(source));
        Nav41Engine engine=new Nav41Engine(holder,new Nav41Id(uid,-1,5));
        nav41Attach(e,engine,holder,renderer,stream);
        e.onRendererTypeStateRead(renderer,stream,1,2,-4,null);
        check(bridge.wasCurrentOriginalSource(early.generation,track,album,source),
            "EXACT_EARLY_GENERATION_REACHES_STRICT_LIVE_ORIGINAL_PERIOD");
        check(!bridge.wasCurrentOriginalSource(early.generation,track,album,new FakeSource()),
            "OTHER_SOURCE_CANNOT_REUSE_LIVE_PERIOD_WITNESS");
        check(!bridge.replacementEnabled() &&
            bridge.chosenSource()==pro.celikom.yandex.nativehooklab.NativeSourceGate.Choice.ORIGINAL,
            "LIVE_SAME_SOURCE_DOES_NOT_TURN_ON_ALTERNATE");
        now[0]=200;
        NativeRendererStreamEvidence.TrackPlayerScope next=e.enterTrackPlayerSource(wrapper);
        try {
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame second=
                e.beginEarlyOriginalSourceSet(new FakeSource());
            check(second!=null,"NEXT_HAS_INDEPENDENT_SETTER");
            check(!bridge.wasCurrentOriginalSource(early.generation,track,album,source),
                "NEXT_REVOKES_LATE_CURRENT_CONFIRMATION");
            e.finishEarlyOriginalSourceSet(second,true);
            check(!bridge.wasCurrentOriginalSource(second.generation,track,album,source),
                "NEW_GENERATION_MUST_NOT_REUSE_OLD_LIVE_SOURCE");
        } finally {e.exitTrackPlayerSource(next);}
    }

    private static void testOriginalExactMediaPeriodBeforePrepareNoAlternate() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        NativeEarlySourceLifecycleBridge bridge=new NativeEarlySourceLifecycleBridge(() -> 123);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        FakeSource source=new FakeSource();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        e.setEarlyOriginalSourceObserver(bridge);
        e.setOriginalPeriodBeforePrepareObserver(bridge);
        nav43SetupLiveSource(e);
        e.onHookRegistration("ORIGINAL_PERIOD_PREPARE",true);
        NativeRendererStreamEvidence.TrackPlayerScope scope=e.enterTrackPlayerSource(wrapper);
        NativeRendererStreamEvidence.EarlyOriginalSourceFrame frame;
        try {
            frame=e.beginEarlyOriginalSourceSet(source);
            check(frame!=null,"PREPARE_ORIGINAL_CREATOR_LINK");
            e.onNativePlayerSourceSetter(source);
            e.finishEarlyOriginalSourceSet(frame,true);
        } finally {e.exitTrackPlayerSource(scope);}
        FakePeriod good=new FakePeriod(source);
        check(!bridge.sawOriginalPeriodPrePrepare(frame.generation,good),
            "PREPARE_NOT_ATTESTED_UNTIL_ACTUAL_ENTER");
        check(e.onOriginalPeriodBeforePrepare(good),
            "SAME_ORIGINAL_SOURCE_BEFORE_REAL_PERIOD_PREPARE");
        check(bridge.sawOriginalPeriodPrePrepare(frame.generation,good),
            "SAME_GENERATION_EXACT_ORIGINAL_PERIOD_BOUND");
        check(!bridge.replacementEnabled() &&
            bridge.chosenSource()==pro.celikom.yandex.nativehooklab.NativeSourceGate.Choice.ORIGINAL,
            "NO_SEMANTIC_IDS_PERIOD_PREPARE_REMAINS_ORIGINAL");
        FakePeriod second=new FakePeriod(source);
        check(e.onOriginalPeriodBeforePrepare(second),
            "SAME_SOURCE_DIFFERENT_PERIOD_IS_OBSERVED_BUT_AMBIGUOUS");
        check(!bridge.sawOriginalPeriodPrePrepare(frame.generation,good)
                && !bridge.sawOriginalPeriodPrePrepare(frame.generation,second),
            "TWO_PERIODS_SAME_SOURCE_FENCE_QUEUED_PREFETCH");
        e.onOriginalPeriodBeforePrepare(good);
        check(!bridge.sawOriginalPeriodPrePrepare(frame.generation,good),
            "AMBIGUOUS_GENERATION_CANNOT_REGAIN_PREPARE_PROOF");
        NativeRendererStreamEvidence.TrackPlayerScope next=e.enterTrackPlayerSource(wrapper);
        try {
            e.beginEarlyOriginalSourceSet(null);
            check(!bridge.sawOriginalPeriodPrePrepare(frame.generation,good),
                "UNKNOWN_NEXT_INVALIDATES_PRIOR_PREPARE");
            check(!e.onOriginalPeriodBeforePrepare(good),
                "STALE_PREPARE_SOURCE_NOT_ACCEPTED");
        } finally {e.exitTrackPlayerSource(next);}
    }

    private static void testOriginalEarlySetterFeedsExistingNativeLifecycle() {
        final long[] now={1000};
        NativeEarlySourceLifecycleBridge bridge =
            new NativeEarlySourceLifecycleBridge(() -> now[0]);
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object(),
               source=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        e.setEarlyOriginalSourceObserver(bridge);
        NativeRendererStreamEvidence.TrackPlayerScope frame=e.enterTrackPlayerSource(wrapper);
        try {
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame first=
                e.beginEarlyOriginalSourceSet(source);
            check(first!=null && bridge.reservedNativeGeneration()>0,
                "REAL_ORIGINAL_SETTER_RESERVES_CANONICAL_LIFECYCLE_GENERATION");
            e.finishEarlyOriginalSourceSet(first,true);
            check(bridge.isSuccessfulOriginalSource(first.generation,track,album,source),
                "AFTER_SUCCESSFUL_ORIGINAL_SETTER_SAME_REFERENCES");
            Object[] freshSetter=e.exactSetterForFreshSourceCreator(wrapper,track,album);
            check(freshSetter!=null && freshSetter[0].equals(first.generation)
                    && freshSetter[1]==source,
                "FIRST_OPEN_EXACT_SETTER_SOURCE_GENERATION");
            check(e.exactSetterForFreshSourceCreator(new Object(),track,album)==null,
                "FIRST_OPEN_WRONG_WRAPPER_REJECTED");
            check(contains(e.exportLines(),
                    "origin=FIRST_OPEN_SETTER_ACCEPTED;error=ONE"),
                "FIRST_OPEN_SETTER_ACCEPTED_BUCKET");
            check(contains(e.exportLines(),
                    "origin=FIRST_OPEN_SETTER_WRAPPER_MISMATCH;error=ONE"),
                "FIRST_OPEN_SETTER_WRAPPER_REJECTION_REASON");
            check(!bridge.replacementEnabled()
                    && bridge.chosenSource()==pro.celikom.yandex.nativehooklab.NativeSourceGate.Choice.ORIGINAL,
                "UNKNOWN_SEMANTIC_ID_NEVER_ENABLES_ALTERNATE");
            now[0]=1100;
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame again=
                e.beginEarlyOriginalSourceSet(source);
            check(!bridge.isSuccessfulOriginalSource(first.generation,track,album,source),
                "NEXT_INVALIDATES_LIFECYCLE_AND_ORIGINAL_PROOF");
            e.finishEarlyOriginalSourceSet(again,false);
            check(!bridge.isSuccessfulOriginalSource(again.generation,track,album,source),
                "THROWING_ORIGINAL_SETTER_CANNOT_RESTORE_OLD_AUDIO");
            check(bridge.reservedNativeGeneration()!=0L
                  && bridge.chosenSource()==pro.celikom.yandex.nativehooklab.NativeSourceGate.Choice.ORIGINAL,
                "FAILED_PUBLISHER_SETTER_NEVER_ISSUES_ALTERNATE");
            now[0]=1200;
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame unknown=
                e.beginEarlyOriginalSourceSet(new Object());
            check(unknown!=null,"SAME_WRAPPER_WITH_DIFFERENT_SOURCE_CAN_BE_PENDING");
            e.finishEarlyOriginalSourceSet(unknown,true);
            check(!bridge.isSuccessfulOriginalSource(first.generation,track,album,source),
                "UNKNOWN_ORIGINAL_SETTER_DISCARDS_OLD_SOURCE_GENERATION");
            now[0]=1300;
            check(e.beginEarlyOriginalSourceSet(null)==null,
                "NULL_ORIGINAL_SOURCE_IS_REJECTED");
            check(bridge.currentNativeGeneration()>bridge.reservedNativeGeneration(),
                "NULL_SOURCE_REJECT_ABORTS_RESERVED_NATIVE_GENERATION");
            check(!bridge.isSuccessfulOriginalSource(unknown.generation,track,album,unknown.source),
                "REJECTED_NEW_SELECTION_INVALIDATES_EARLIER_SUCCESS");
        } finally {e.exitTrackPlayerSource(frame);}
    }

    private static void testNestedEarlySourceRejectCannotLeavePendingRevision() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        NativeEarlySourceLifecycleBridge bridge=
            new NativeEarlySourceLifecycleBridge(() -> 1000);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        e.setEarlyOriginalSourceObserver(bridge);
        NativeRendererStreamEvidence.TrackPlayerScope scope=e.enterTrackPlayerSource(wrapper);
        try {
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame outer=
                e.beginEarlyOriginalSourceSet(new Object());
            check(outer!=null,"NESTED_FIRST_VALID_EARLY_SOURCE");
            check(e.beginEarlyOriginalSourceSet(new Object())==null,
                "NESTED_ORIGINAL_SETTER_NOT_ADMITTED");
            check(bridge.currentNativeGeneration()>bridge.reservedNativeGeneration(),
                "NESTED_ORIGINAL_SETTER_CANCELS_UNRESOLVED_GENERATION");
            e.finishEarlyOriginalSourceSet(outer,true);
            check(!bridge.isSuccessfulOriginalSource(outer.generation,track,album,outer.source),
                "NESTED_FIRST_RESULT_CANNOT_RESTORE_STALE_SOURCE");
        } finally {e.exitTrackPlayerSource(scope);}
    }


    private static void testOriginalPrepareSealsNativeLifecycleBeforeLateIdentity() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        final long[] clock={1000};
        NativeEarlySourceLifecycleBridge bridge=
            new NativeEarlySourceLifecycleBridge(() -> clock[0]);
        pro.celikom.yandex.nativehooklab.NativeReplacementLifecycle lifecycle;
        try {
            java.lang.reflect.Field field=
                NativeEarlySourceLifecycleBridge.class.getDeclaredField("lifecycle");
            field.setAccessible(true);
            lifecycle=(pro.celikom.yandex.nativehooklab.NativeReplacementLifecycle)
                field.get(bridge);
        } catch(ReflectiveOperationException exception) {
            throw new AssertionError("TEST_NATIVE_LIFECYCLE_NOT_ACCESSIBLE",exception);
        }
        // Test-only enabled state: production hook remains OFF.
        lifecycle.start();
        Object track=new Object(),album=new Object(),wrapper=new Object();
        FakeSource source=new FakeSource();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        e.setEarlyOriginalSourceObserver(bridge);
        e.setOriginalPeriodBeforePrepareObserver(bridge);
        nav43SetupLiveSource(e);
        e.onHookRegistration("ORIGINAL_PERIOD_PREPARE",true);
        NativeRendererStreamEvidence.TrackPlayerScope scope=
            e.enterTrackPlayerSource(wrapper);
        NativeRendererStreamEvidence.EarlyOriginalSourceFrame frame;
        try {
            frame=e.beginEarlyOriginalSourceSet(source);
            check(frame!=null,"PREPARE_SEAL_HAS_ORIGINAL_SETTER");
            e.onNativePlayerSourceSetter(source);
            e.finishEarlyOriginalSourceSet(frame,true);
        } finally {e.exitTrackPlayerSource(scope);}
        long token=bridge.reservedNativeGeneration();
        check(token==lifecycle.generation() && lifecycle.isEnabled(),
            "PREPARE_SEAL_RESERVES_ACTIVE_ENABLED_GENERATION");
        FakePeriod period=new FakePeriod(source);
        check(e.onOriginalPeriodBeforePrepare(period),
            "PREPARE_SEAL_REACHED_EXACT_ORIGINAL_PERIOD");
        check(bridge.sawOriginalPeriodPrePrepare(frame.generation,period)
            && lifecycle.lastIssuedSource()
                ==pro.celikom.yandex.nativehooklab.NativeSourceGate.Choice.ORIGINAL,
            "PREPARE_SEAL_DOES_NOT_CHANGE_PUBLISHER_SOURCE");
        clock[0]=1001;
        check(!lifecycle.certifyNativeIdentity(
                token,"42884423","42","original-edition",clock[0]),
            "LATE_EXACT_TRACK_ALBUM_EDITION_CANNOT_UPGRADE_PREPARED_ORIGINAL");
        check(e.onOriginalPeriodBeforePrepare(period)
            && !lifecycle.certifyNativeIdentity(
                token,"42884423","42","original-edition",clock[0]),
            "REPEATED_PREPARE_NEVER_REOPENS_SOURCE_ADMISSION");
    }

    private static void testUnlinkedOriginalPrepareSealsLateNativeAdmission() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        final long[] clock={1000};
        NativeEarlySourceLifecycleBridge bridge=
            new NativeEarlySourceLifecycleBridge(() -> clock[0]);
        pro.celikom.yandex.nativehooklab.NativeReplacementLifecycle lifecycle;
        try {
            java.lang.reflect.Field field=
                NativeEarlySourceLifecycleBridge.class.getDeclaredField("lifecycle");
            field.setAccessible(true);
            lifecycle=(pro.celikom.yandex.nativehooklab.NativeReplacementLifecycle)
                field.get(bridge);
        } catch(ReflectiveOperationException exception) {
            throw new AssertionError("TEST_LIFECYCLE_REFLECTION_FAILED",exception);
        }
        lifecycle.start(); // Test only: runtime module never calls start().
        Object track=new Object(),album=new Object(),wrapper=new Object();
        FakeSource source=new FakeSource();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        e.setEarlyOriginalSourceObserver(bridge);
        e.setOriginalPeriodBeforePrepareObserver(bridge);
        nav43SetupLiveSource(e);
        e.onHookRegistration("ORIGINAL_PERIOD_PREPARE",true);
        NativeRendererStreamEvidence.TrackPlayerScope scope=
            e.enterTrackPlayerSource(wrapper);
        NativeRendererStreamEvidence.EarlyOriginalSourceFrame frame;
        try {
            frame=e.beginEarlyOriginalSourceSet(source);
            check(frame!=null,"UNKNOWN_PREPARE_CANONICAL_GENERATION");
            e.onNativePlayerSourceSetter(source);
            e.finishEarlyOriginalSourceSet(frame,true);
        } finally {e.exitTrackPlayerSource(scope);}
        long reserved=bridge.reservedNativeGeneration();
        FakePeriod wrong=new FakePeriod(new FakeSource());
        check(!e.onOriginalPeriodBeforePrepare(wrong),
            "FOREIGN_PERIOD_NOT_PROMOTED_TO_OWN_TRACK");
        clock[0]=1001;
        check(!lifecycle.certifyNativeIdentity(reserved,
                "42884423","album-1","edition-1",clock[0]),
            "FOREIGN_PREPARE_SEALS_ORIGINAL_BEFORE_LATE_CERTIFICATION");
        check(lifecycle.lastIssuedSource()
                ==pro.celikom.yandex.nativehooklab.NativeSourceGate.Choice.ORIGINAL,
            "FOREIGN_PREPARE_MUST_PRESERVE_PUBLISHER_AUDIO");
        FakePeriod original=new FakePeriod(source);
        check(e.onOriginalPeriodBeforePrepare(original),
            "LATER_SAME_SOURCE_STRUCTURAL_EVENT_CAN_BE_SEEN");
        check(!bridge.sawOriginalPeriodPrePrepare(frame.generation,original),
            "FOREIGN_PREPARE_POISONS_EVEN_LATER_SAME_SOURCE_PERIOD");
        check(!lifecycle.certifyNativeIdentity(reserved,
                "42884423","album-1","edition-1",clock[0]),
            "LATER_MATCHED_PERIOD_MUST_NOT_REOPEN_SEALED_ORIGINAL");
        // A new publisher setter starts an independent (unsealed) revision.
        scope=e.enterTrackPlayerSource(wrapper);
        try {
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame next=
                e.beginEarlyOriginalSourceSet(new FakeSource());
            check(next!=null,"NEXT_AFTER_UNKNOWN_PREPARE_NEW_GENERATION");
            e.onNativePlayerSourceSetter(next.source);
            e.finishEarlyOriginalSourceSet(next,true);
            check(bridge.reservedNativeGeneration()!=reserved,
                "NEXT_NEVER_USES_OLD_PREPARE_REVISION");
        } finally {e.exitTrackPlayerSource(scope);}
    }

    private static void testExactOriginalPrepareTracksPreopenDataSourceCandidate() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence e=new NativeRendererStreamEvidence();
        NativeEarlySourceLifecycleBridge bridge=
            new NativeEarlySourceLifecycleBridge(() -> 1000);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        FakeSource originalSource=new FakeSource();
        Object descriptor=new Object(),factory=new Object(),dataSource=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        // The original Track already entered Flow before this creator birth:
        // this is the version that can link the descriptor/factory/instance.
        stage.onNativeTrackFlowEmission(track);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        stage.enterNativeMainSourceRequest(wrapper,null);
        try {stage.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);}
        finally {stage.exitNativeMainSourceRequest();}
        stage.onExoFactoryCreated(descriptor,factory);
        stage.onExoSourceInstanceCreated(dataSource,factory);
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)==dataSource,
            "SAME_ORIGINAL_CREATOR_TO_UNOPENED_DATASOURCE_INSTANCE");
        check(stage.exactFreshSourceInstanceForCreator(wrapper,new Object(),album)==null,
            "OTHER_TRACK_CANNOT_ADOPT_ORIGINAL_BYTES_ROUTE");
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,new Object())==null,
            "OTHER_ALBUM_CANNOT_ADOPT_ORIGINAL_BYTES_ROUTE");
        e.setEarlyOriginalSourceEvidence(stage::exactCreatorTrackAlbumBeforeSourceSet);
        e.setOriginalPrePrepareSourceInstanceEvidence(
            stage::exactFreshSourceInstanceForCreator);
        e.setEarlyOriginalSourceObserver(bridge);
        e.setOriginalPeriodBeforePrepareObserver(bridge);
        nav43SetupLiveSource(e);
        e.onHookRegistration("ORIGINAL_PERIOD_PREPARE",true);
        NativeRendererStreamEvidence.TrackPlayerScope scope=e.enterTrackPlayerSource(wrapper);
        NativeRendererStreamEvidence.EarlyOriginalSourceFrame frame;
        try {
            frame=e.beginEarlyOriginalSourceSet(originalSource);
            check(frame!=null,"DATASOURCE_CANDIDATE_SETTER_CREATOR_LINK");
            e.onNativePlayerSourceSetter(originalSource);
            e.finishEarlyOriginalSourceSet(frame,true);
        } finally {e.exitTrackPlayerSource(scope);}
        FakePeriod originalPeriod=new FakePeriod(originalSource);
        check(e.onOriginalPeriodBeforePrepare(originalPeriod),
            "DATASOURCE_CANDIDATE_SEEN_BEFORE_ORIGINAL_PREPARE");
        check(bridge.wasPrePrepareOriginalSourceInstance(
                frame.generation,originalPeriod,dataSource),
            "EXACT_ORIGINAL_PERIOD_AND_UNOPENED_DATASOURCE_CANDIDATE");
        check(!bridge.wasPrePrepareOriginalSourceInstance(
                frame.generation,new FakePeriod(originalSource),dataSource)
                && !bridge.wasPrePrepareOriginalSourceInstance(
                    frame.generation,originalPeriod,new Object()),
            "NO_CROSS_PERIOD_OR_DATA_SOURCE_REUSE");
        check(e.onOriginalPeriodBeforePrepare(originalPeriod),
            "REPEATED_SAME_ORIGINAL_PERIOD_PREPARE_OBSERVED");
        check(!bridge.wasPrePrepareOriginalSourceInstance(
                frame.generation,originalPeriod,dataSource),
            "DUPLICATE_PREPARE_CANNOT_REUSE_FIRST_UNOPENED_SOURCE");
        // A later different prepare, even with the same source, irrevocably
        // cancels the supposedly unique period candidate for this revision.
        e.onOriginalPeriodBeforePrepare(new FakePeriod(originalSource));
        check(!bridge.wasPrePrepareOriginalSourceInstance(
                frame.generation,originalPeriod,dataSource),
            "PREFETCH_SECOND_PERIOD_REVOKES_CANDIDATE");
        // A real opened instance is too late to classify as pre-open.
        stage.onExoSourceInstanceOpenAttempt(dataSource);
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)==null,
            "OPEN_STARTED_BEFORE_SUCCESS_CANNOT_BE_PREPREPARE_CANDIDATE");
        stage.onExoSourceInstanceOpenFailure(dataSource);
        stage.onExoSourceInstanceClose(dataSource);
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)==null,
            "FAILED_OPEN_AND_CLOSE_CANNOT_RESET_SOURCE_FRESHNESS");
        stage.onExoSourceInstanceCreated(dataSource,factory);
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)==null,
            "REUSED_SAME_DATASOURCE_INSTANCE_CANNOT_BE_FRESH");
        Object genuinelyNewSource=new Object();
        stage.onExoSourceInstanceCreated(genuinelyNewSource,factory);
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)
                ==genuinelyNewSource,
            "FRESH_FACTORY_SOURCE_INSTANCE_ELIGIBLE_BEFORE_FIRST_READ");
        stage.onExoSourceInstanceReadAttempt(genuinelyNewSource);
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)==null,
            "READ_ENTRY_REVOKES_FRESHNESS_BEFORE_BYTES_RETURN");
        stage.onExoSourceInstanceOpen(dataSource);
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)==null,
            "OPENED_SOURCE_CANNOT_BE_USED_AS_PREPREPARE_CANDIDATE");
        check(!bridge.replacementEnabled(),
            "SOURCE_INSTANCE_CONTINUITY_NOT_AUDIO_SUBSTITUTION");
    }

    private static void testExactCreatorBeforeFlowOriginalDataSourceLink() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object();
        Object descriptor=new Object(),factory=new Object(),source=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        // Original Gp0 creator runs before the matching Track Flow emission.
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==12,
            "CREATOR_PRE_FLOW_PRESERVES_NAV40_NOT_IN_FLOW");
        Object[] pair=stage.exactCreatorTrackAlbumBeforeSourceSet(wrapper);
        check(pair!=null && pair[0]==track && pair[1]==album,
            "CREATOR_PRE_FLOW_EXACT_TRACK_ALBUM");
        stage.enterNativeMainSourceRequest(wrapper,null);
        try {stage.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);}
        finally {stage.exitNativeMainSourceRequest();}
        stage.onExoFactoryCreated(descriptor,factory);
        stage.onExoSourceInstanceCreated(source,factory);
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)==source,
            "CREATOR_PRE_FLOW_EXO_INSTANCE_PROVEN_BY_ORIGINAL_REFS");
        stage.onNativeTrackFlowEmission(new Object());
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==12,
            "CREATOR_OTHER_FLOW_CANNOT_PROMOTE_ORIGINAL");
        stage.onNativeTrackFlowEmission(track);
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==16,
            "CREATOR_OWN_FLOW_PRESERVES_NAV40_LATE_MATCH_CATEGORY");
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)==source,
            "CREATOR_SAME_EXO_INSTANCE_SURVIVES_LATE_FLOW");
        stage.onNativeTrackAlbumConstructed(track,new Object());
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==17,
            "CREATOR_ALBUM_CONFLICT_PRESERVES_NAV40_VERDICT");
        check(stage.exactFreshSourceInstanceForCreator(wrapper,track,album)==null,
            "CREATOR_ALBUM_CONFLICT_REVOKES_EXO_INSTANCE");
        // No other Track's factory result can adopt this original wrapper.
        StageBAudioEvidence noCreator=new StageBAudioEvidence();
        Object unknownTrack=new Object(),unknownWrapper=new Object();
        noCreator.onNativeTrackAlbumConstructed(unknownTrack,album);
        noCreator.enterNativeTrackSourceRequest(unknownTrack,null);
        try {noCreator.onNativeTrackWrapperCreated(unknownWrapper);}
        finally {noCreator.exitNativeTrackSourceRequest();}
        noCreator.enterNativeMainSourceRequest(unknownWrapper,null);
        try {noCreator.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);}
        finally {noCreator.exitNativeMainSourceRequest();}
        noCreator.onExoFactoryCreated(descriptor,factory);
        noCreator.onExoSourceInstanceCreated(source,factory);
        check(noCreator.exactFreshSourceInstanceForCreator(
                unknownWrapper,unknownTrack,album)==null,
            "NON_CREATOR_PRE_FLOW_CANNOT_LEARN_ORIGINAL_EXO");
    }


    private static void createNav49CreatorWrapper(StageBAudioEvidence stage,
            Object track,Object wrapper) {
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper,"144530503");}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
    }

    private static void testNav49SameTrackWrappersKeepIndependentSourceLineages() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object track=new Object(),album=new Object(),firstWrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        createNav49CreatorWrapper(stage,track,firstWrapper);

        Object descriptor=new Object(),factory=new Object(),source=new Object();
        stage.enterNativeMainSourceRequest(firstWrapper,null);
        try {stage.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);}
        finally {stage.exitNativeMainSourceRequest();}
        stage.onExoFactoryCreated(descriptor,factory);
        stage.onExoSourceInstanceCreated(source,factory);

        // A repeated callback for the exact same wrapper must not clear the
        // existing source chain or reset its touched/open guard.
        createNav49CreatorWrapper(stage,track,firstWrapper);
        Object secondWrapper=new Object();
        createNav49CreatorWrapper(stage,track,secondWrapper);
        Object[] fresh=stage.exactFreshCreatorOrBetaAtFirstOpen(source);
        check(fresh!=null && fresh[0]==firstWrapper
                && fresh[1]==track && fresh[2]==album,
            "NAV49_SECOND_WRAPPER_FOR_SAME_TRACK_DOES_NOT_REBIND_FIRST_SOURCE");
        check(contains(stage.exportLines(),
                "origin=TRACK_WRAPPER_SAME_TRACK_PARALLEL;error=ONE"),
            "NAV49_PARALLEL_SAME_TRACK_WRAPPER_IS_EXPLICIT");
        check(contains(stage.exportLines(),
                "origin=TRACK_WRAPPER_SAME_IDENTITY_REFRESH;error=ONE"),
            "NAV49_SAME_WRAPPER_REFRESH_PRESERVES_EXISTING_LINEAGE");
        check(contains(stage.exportLines(),
                "origin=TRACK_DESCRIPTOR_FACTORY_LINK;error=ONE"),
            "NAV49_FIRST_DESCRIPTOR_FACTORY_LINEAGE_SURVIVES");
        check(contains(stage.exportLines(),
                "origin=TRACK_FACTORY_SOURCE_LINK;error=ONE"),
            "NAV49_FIRST_FACTORY_SOURCE_LINEAGE_SURVIVES");
    }

    private static void testNav49EvictedSameTrackWrapperRestoresBesideSibling() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object track=new Object(),album=new Object(),firstWrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        createNav49CreatorWrapper(stage,track,firstWrapper);
        for(int i=0;i<16;i++)
            createNav49CreatorWrapper(stage,track,new Object());

        Object descriptor=new Object(),factory=new Object(),source=new Object();
        stage.enterNativeMainSourceRequest(firstWrapper,null);
        try {stage.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);}
        finally {stage.exitNativeMainSourceRequest();}
        stage.onExoFactoryCreated(descriptor,factory);
        stage.onExoSourceInstanceCreated(source,factory);
        Object[] fresh=stage.exactFreshCreatorOrBetaAtFirstOpen(source);
        check(fresh!=null && fresh[0]==firstWrapper
                && fresh[1]==track && fresh[2]==album,
            "NAV49_EVICTED_CREATOR_WRAPPER_RESTORES_WITH_SAME_TRACK_SIBLINGS");
        check(contains(stage.exportLines(),
                "origin=TRACK_WRAPPER_LINK_RESTORED_WITH_SAME_TRACK_SIBLING;error=ONE"),
            "NAV49_RESTORATION_DOES_NOT_REJECT_SAME_TRACK_SIBLINGS");
    }

    private static void testTcaCreatorFlowBirthRestoresEvictedWrapperLineage() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper,"144530503");}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        for(int i=0;i<16;i++) {
            Object otherTrack=new Object(),otherAlbum=new Object(),otherWrapper=new Object();
            stage.onNativeTrackAlbumConstructed(otherTrack,otherAlbum);
            stage.onNativeTrackFlowEmission(otherTrack);
            stage.enterNativeTcaCreatorOwner(new Object());
            try {
                stage.enterNativeTcaCreatorTrackScope(otherTrack,1);
                try {stage.onNativeTrackWrapperCreated(otherWrapper,"987654321");}
                finally {stage.exitNativeTcaCreatorTrackScope();}
            } finally {stage.exitNativeTcaCreatorOwner();}
        }
        check(stage.classifyNativeTrackAlbumForWrapper(wrapper)==20,
            "NAV48_FLOW_AT_BIRTH_CLASSIFICATION_AFTER_RING_EVICTION");
        Object[] original=stage.exactCreatorTrackAlbumBeforeSourceSet(wrapper);
        check(original!=null && original[0]==track && original[1]==album,
            "NAV48_CREATOR_BIRTH_TRACK_ALBUM_DOES_NOT_DEPEND_ON_RING");
        Object descriptor=new Object(),factory=new Object(),source=new Object();
        stage.enterNativeMainSourceRequest(wrapper,null);
        try {stage.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);}
        finally {stage.exitNativeMainSourceRequest();}
        stage.onExoFactoryCreated(descriptor,factory);
        stage.onExoSourceInstanceCreated(source,factory);
        Object[] fresh=stage.exactFreshCreatorOrBetaAtFirstOpen(source);
        check(fresh!=null && fresh[0]==wrapper && fresh[1]==track && fresh[2]==album,
            "NAV48_RESTORED_CREATOR_LINK_REACHES_EXACT_FIRST_OPEN");
        check(contains(stage.exportLines(),"origin=TRACK_WRAPPER_LINK_RESTORED;error=ONE"),
            "NAV48_RESTORE_IS_EXPLICITLY_DIAGNOSTIC");
        check(contains(stage.exportLines(),"origin=TRACK_DESCRIPTOR_FACTORY_LINK;error=ONE"),
            "NAV48_RESTORED_LINK_REBUILDS_DESCRIPTOR_FACTORY");
        check(contains(stage.exportLines(),"origin=TRACK_FACTORY_SOURCE_LINK;error=ONE"),
            "NAV48_RESTORED_LINK_REBUILDS_FACTORY_SOURCE");
    }

    private static void testRealPublisherAnnotatedTrackIdCorrelatesCreator() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onPublisherAnnotatedTrackId("42884423"); // unscoped: NEVER trusted
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper,"42884423");}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        check(stage.exactPublisherTrackIdForCreator(wrapper,track,album)==null,
            "UNSCOPED_ANNOTATED_ID_NOT_NATIVE_PROOF");
        stage.enterNativeTrackSourceRequest(track,null);
        try {stage.onPublisherAnnotatedTrackId("42884423");}
        finally {stage.exitNativeTrackSourceRequest();}
        check("42884423".equals(stage.exactPublisherTrackIdForCreator(
                wrapper,track,album)), "SIGNED_API_EXACT_TRACK_AND_TCA_KEY");
        check(stage.exactPublisherTrackIdForCreator(wrapper,new Object(),album)==null,
            "NO_CROSS_TRACK_ID");
        check(stage.exactPublisherTrackIdForCreator(wrapper,track,new Object())==null,
            "NO_CROSS_ALBUM_ID");
        Object incompatible=new Object();
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(incompatible,"42884424");}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        check(stage.exactPublisherTrackIdForCreator(incompatible,track,album)==null,
            "ORIGINAL_WRAPPER_KEY_MISMATCH_DENIED");
        stage.enterNativeTrackSourceRequest(track,null);
        try {stage.onPublisherAnnotatedTrackId("42884424");}
        finally {stage.exitNativeTrackSourceRequest();}
        check(stage.exactPublisherTrackIdForCreator(wrapper,track,album)==null,
            "API_ID_CONFLICT_NEVER_RECOVERS");
        check(!contains(stage.exportLines(),"42884423"),
            "ORIGINAL_ID_NOT_EXPORTED");
    }

    private static void testRealPublisherTrackIdAtNativeSourceSetter() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence renderer=new NativeRendererStreamEvidence();
        renderer.setEarlyOriginalSourceEvidence(
            stage::exactCreatorTrackAlbumBeforeSourceSet);
        renderer.setExactPublisherTrackIdEvidence(
            stage::exactPublisherTrackIdForCreator);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTrackSourceRequest(track,null);
        try {stage.onPublisherAnnotatedTrackId("42884423");}
        finally {stage.exitNativeTrackSourceRequest();}
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper,"42884423");}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        NativeRendererStreamEvidence.TrackPlayerScope scope=
            renderer.enterTrackPlayerSource(wrapper);
        try {
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame frame=
                renderer.beginEarlyOriginalSourceSet(new FakeSource());
            check(frame!=null && "42884423".equals(
                    frame.originalPublisherTrackIdCandidate),
                "EXACT_ISSUER_API_TRACK_ID_REACHES_EARLY_ORIGINAL_SETTER");
            renderer.finishEarlyOriginalSourceSet(frame,true);
        } finally {renderer.exitTrackPlayerSource(scope);}
        StageBAudioEvidence absent=new StageBAudioEvidence();
        NativeRendererStreamEvidence empty=new NativeRendererStreamEvidence();
        empty.setEarlyOriginalSourceEvidence(
            absent::exactCreatorTrackAlbumBeforeSourceSet);
        empty.setExactPublisherTrackIdEvidence(
            absent::exactPublisherTrackIdForCreator);
        Object plainTrack=new Object(),plainAlbum=new Object(),
            plainWrapper=new Object();
        absent.onNativeTrackAlbumConstructed(plainTrack,plainAlbum);
        absent.enterNativeTcaCreatorOwner(new Object());
        try {
            absent.enterNativeTcaCreatorTrackScope(plainTrack,1);
            try {absent.onNativeTrackWrapperCreated(plainWrapper,"42884423");}
            finally {absent.exitNativeTcaCreatorTrackScope();}
        } finally {absent.exitNativeTcaCreatorOwner();}
        NativeRendererStreamEvidence.TrackPlayerScope blank=
            empty.enterTrackPlayerSource(plainWrapper);
        try {
            NativeRendererStreamEvidence.EarlyOriginalSourceFrame noId=
                empty.beginEarlyOriginalSourceSet(new FakeSource());
            check(noId!=null && noId.originalPublisherTrackIdCandidate==null,
                "UNPROVEN_PROXY_REQUEST_NEVER_BECOMES_SOURCE_ID");
            empty.finishEarlyOriginalSourceSet(noId,true);
        } finally {empty.exitTrackPlayerSource(blank);}
    }

    private static void testApprovedNativeGrantRoutesRealOriginalExoPreprepare()
            throws java.io.IOException {
        final long[] clock={1000};
        final long unix=1795160000000L,expire=((unix/1000)+500)*1000;
        Object track=new Object(),album=new Object(),originalSource=new Object();
        Object period=new Object(),exoSource=new Object(),prefetch=new Object();
        byte[] encoded="CELIKOM".getBytes(java.nio.charset.StandardCharsets.US_ASCII);
        NativeExoAlternateByteRoute router=new NativeExoAlternateByteRoute(
            (url,mime)->new NativeExoAlternateByteRoute.Cursor() {
                int index;
                public long open(long start) {
                    index=(int)start;return encoded.length-start;
                }
                public int read(byte[] target,int offset,int length) {
                    if(index>=encoded.length)return -1;
                    int count=Math.min(encoded.length-index,length);
                    System.arraycopy(encoded,index,target,offset,count);
                    index+=count;
                    return count;
                }
                public void close() {}
            });
        NativeEarlySourceLifecycleBridge bridge=new NativeEarlySourceLifecycleBridge(
            ()->clock[0],router,()->unix);
        bridge.startForAuthenticatedOwner();
        bridge.invalidated(1);
        bridge.pending(1,track,album,originalSource);
        bridge.originalPublisherTrackIdCandidate(1,"42884423");
        bridge.completed(1,true);
        check(bridge.onSourceBoundPublisherFileInfo(
            1,track,album,originalSource,"42884423","41","main"),
            "ORIGINAL_TRACK_AND_PUBLISHER_FILEINFO_TRIPLE_CERTIFIED");
        String signedUrl="https://audio.example/api/v1/audio/42?token="
            +"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            +"&expires="+(expire/1000)+"&sid=8";
        pro.celikom.yandex.nativehooklab.NativeGrantContract.Grant grant=
            new pro.celikom.yandex.nativehooklab.NativeGrantContract.Grant(
                "42884423","41","main",180000,2,true,true,
                signedUrl,expire,"audio/mpeg");
        pro.celikom.yandex.nativehooklab.NativeSourceGate.Candidate candidate=
            new pro.celikom.yandex.nativehooklab.NativeSourceGate.Candidate(
                "42884423","41","main",true,true,true,true,true,true);
        check(bridge.offerAuthenticatedApprovedAudio(
            1,track,album,originalSource,candidate,grant,
            "https://audio.example",180000),
            "APPROVED_ID_AND_SIGNED_GRANT_QUEUED_BEFORE_PREPARE");
        check(!router.isArmed(exoSource),
            "NO_BYTES_BEFORE_ACTUAL_PUBLISHER_PREPARE");
        bridge.beforeOriginalPeriodPrepare(1,track,album,originalSource,
            period,null);
        check(!router.isArmed(exoSource),
            "DEFERRED_APPROVAL_WAITS_FOR_EXACT_FIRST_OPEN");
        check(!bridge.armDeferredOriginalDataSource(2,track,album,
                originalSource,exoSource),
            "WRONG_FIRST_OPEN_GENERATION_REJECTED");
        check(contains(bridge.exportLines(),
                "origin=DEFERRED_ARM_GENERATION_MISMATCH;error=ONE"),
            "DEFERRED_GENERATION_REJECTION_REASON");
        check(bridge.armDeferredOriginalDataSource(1,track,album,
                originalSource,exoSource),
            "EXACT_FIRST_OPEN_INSTALLS_DEFERRED_NATIVE_EXO_SOURCE");
        check(router.isArmed(exoSource)
            && bridge.chosenSource()
                ==pro.celikom.yandex.nativehooklab.NativeSourceGate.Choice.ALTERNATE,
            "DEFERRED_ORIGINAL_PREPREPARE_INSTALLS_ONE_NATIVE_EXO_SOURCE");
        check(contains(bridge.exportLines(),
                "origin=DEFERRED_ARM_ACCEPTED;error=ONE"),
            "DEFERRED_ARM_ACCEPTED_SUMMARY");
        check(!router.isArmed(prefetch)
                && router.openIfApproved(prefetch,0)==null,
            "OTHER_ORIGINAL_DATASOURCE_NEVER_SEES_ALT_BYTES");
        try {
            check(router.openIfApproved(exoSource,0)==encoded.length,
                "EXO_ALT_OPEN_RETURNS_REAL_ENCODED_LENGTH");
            byte[] actual=new byte[8];
            check(router.readIfApproved(exoSource,actual,0,7)==7
                && "CELIKOM".equals(new String(actual,0,7,
                    java.nio.charset.StandardCharsets.US_ASCII)),
                "REAL_ALTERNATE_ENCODED_BYTES_REACH_SAME_ORIGINAL_EXO");
            check(router.closeIfApproved(exoSource),"EXO_CLOSE_ALTERNATE_ONCE");
        } catch(java.io.IOException failure) {
            throw new AssertionError("EXO_TRANSPORT_ERROR",failure);
        }
        bridge.stopForAuthenticatedOwner();
        check(!bridge.replacementEnabled(),
            "STOP_DISALLOWS_FUTURE_ADMISSIONS_NOT_SECOND_PLAYER");

        NativeExoAlternateByteRoute noGrantRouter=
            new NativeExoAlternateByteRoute();
        NativeEarlySourceLifecycleBridge noGrant=
            new NativeEarlySourceLifecycleBridge(()->1000,noGrantRouter,()->unix);
        noGrant.startForAuthenticatedOwner();
        noGrant.invalidated(2);
        noGrant.pending(2,track,album,originalSource);
        noGrant.completed(2,true);
        check(!noGrant.onSourceBoundPublisherFileInfo(
            2,track,album,originalSource,"42884423","41","main"),
            "NO_UNCORROBORATED_PUBLISHER_TRACK_ID");
        noGrant.beforeOriginalPeriodPrepare(2,track,album,
            originalSource,new Object(),new Object());
        check(noGrant.chosenSource()
            ==pro.celikom.yandex.nativehooklab.NativeSourceGate.Choice.ORIGINAL,
            "NO_VERIFIED_ISSUER_TRACK_ID_MEANS_ORIGINAL_EXO");
        check(!noGrant.armDeferredOriginalDataSource(
                2,track,album,originalSource,new Object()),
            "NO_PENDING_GRANT_CANNOT_ARM_FIRST_OPEN");
        check(contains(noGrant.exportLines(),
                "origin=DEFERRED_ARM_NO_PENDING_APPROVED;error=ONE"),
            "DEFERRED_NO_PENDING_REASON");
    }


    /** Regression: first factory creation is NOT first opened decoder source. */
    private static void testNativeFirstOpenedFactorySourceNotFirstConstructed() {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object();
        Object descriptor=new Object(),factory=new Object();
        Object unopenedPrefetch=new Object(),actuallyOpened=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.onNativeTrackFlowEmission(track);
        stage.enterNativeTcaCreatorOwner(new Object());
        try {
            stage.enterNativeTcaCreatorTrackScope(track,1);
            try {stage.onNativeTrackWrapperCreated(wrapper);}
            finally {stage.exitNativeTcaCreatorTrackScope();}
        } finally {stage.exitNativeTcaCreatorOwner();}
        stage.enterNativeMainSourceRequest(wrapper,null);
        try {stage.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);}
        finally {stage.exitNativeMainSourceRequest();}
        stage.onExoFactoryCreated(descriptor,factory);
        // BETA19 armed the first constructed source and never revisited it.
        stage.onExoSourceInstanceCreated(unopenedPrefetch,factory);
        stage.onExoSourceInstanceCreated(actuallyOpened,factory);
        check(stage.exactFreshCreatorOrBetaAtFirstOpen(new Object())==null,
            "UNRELATED_DATASOURCE_CANNOT_USE_APPROVED_FACTORY");
        Object[] actual=stage.exactFreshCreatorOrBetaAtFirstOpen(actuallyOpened);
        check(actual!=null && actual[0]==wrapper && actual[1]==track
                && actual[2]==album,
            "FIRST_ACTUAL_OPEN_OWNS_APPROVED_EXACT_FACTORY_LINEAGE");
        stage.onExoSourceInstanceOpenAttempt(actuallyOpened);
        check(stage.exactFreshCreatorOrBetaAtFirstOpen(unopenedPrefetch)==null,
            "OPENED_SIBLING_PREVENTS_CROSS_SOURCE_AUDIO_MIX");
        check(stage.exactFreshCreatorOrBetaAtFirstOpen(actuallyOpened)==null,
            "ALREADY_OPENED_SOURCE_CANNOT_REARM");
        stage.onExoSourceInstanceOpen(actuallyOpened);
        stage.onExoSourceInstanceRead(actuallyOpened,7);
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==actuallyOpened,
            "LIVE_RENDERER_RESOLVES_EXACT_TRACK_ALBUM_DATASOURCE_AFTER_READ");
        check(stage.linkedSourceInstanceForCreatorOrBeta(new Object())==null,
            "LIVE_RENDERER_NEVER_GUESSES_ANOTHER_TRACK_DATASOURCE");
        // New independent creator/factory remains strict: no promoted source
        // from the previous Track, even if a different factory produced it.
        StageBAudioEvidence missing=new StageBAudioEvidence();
        missing.onExoSourceInstanceCreated(new Object(),factory);
        check(missing.exactFreshCreatorOrBetaAtFirstOpen(new Object())==null,
            "NO_CREATOR_NO_NATIVE_AUDIO_ADMISSION");
    }

    public static void main(String[] args) throws java.io.IOException {
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
        testExactSecondaryCallerUnscopedMatch();
        testSecondaryCallerAndQueueScopeRemainDistinct();
        testOutsideSecondaryOnlyWhenHookActive();
        testSecondaryDifferentStreamCannotBecomeMatch();
        testSecondaryScopeUnwindsBeforeNextAttach();
        testEngineExactHolderArrayStreamAndLiveReturn();
        testEngineRejectsDifferentMemberWithoutFakingHolder();
        testEngineHolderNoSecondaryCannotProveStream();
        testEngineLinkRevokedOnDetachAndReattach();
        testEngineArrayUnavailableFailsClosed();
        testEngineFrameLifetimeDoesNotLeak();
        testAudioType1State2StrictHolderRead();
        testAudioType2CannotMasqueradeAsAudio();
        testAudioType1State1IsNotStartedState();
        testAudioTypeStateWrongStreamAndDetachFailClosed();
        testAudioTypeStateAbsentReflectionNotFalselyCounted();
        testAudioTypeStateExceptionCountsUnavailableOnly();
        testNav25NonEosStartedAudioStrictLink();
        testNav25NoFalseAudioSampleOnWrongLinkOrState();
        testNav25MissingBufferMethodCannotAttestSample();
        testNav26ComparatorTrueCorrelatesExactActiveRendererRead();
        testNav26ComparatorFalseNeverPromotesAudioRead();
        testNav26ComparatorRequiresExactHolderRendererAndStream();
        testNav26ComparatorDetachedRendererAndMissingHookFailClosed();
        testNav26ComparatorOutcomeClearedOnReattach();
        testNav27AtCallEngineAndAttachmentCohorts();
        testNav27PendingComparatorClearedOnExactAttach();
        testNav27PendingComparatorWrongHolderOrStream();
        testNav28LiveQueueSlotMatchesAtAttachAndStartedRead();
        testNav28RejectsLiveQueueSlotChangeAndDetach();
        testNav28WrongOrUnavailableSlotNeverClaimsMatch();
        testNav29SameSelectedWrapperSourceToLivePeriod();
        testNav29RejectsOtherSourceOrChangedQueueSlot();
        testNav29RejectsUnscopedAndConflictingWrapper();
        testNav30AdapterMapsExactFactoryToLiveWrapper();
        testNav30SameFrameUnrelatedAdapterNeverLinks();
        testNav30AdapterNoScopeOrWrongFactoryFailsClosed();
        testNav30RejectsNestedDuplicateFactoryAndDetach();
        testNav31HolderSelectBeforeVsAfterAndActiveRead();
        testNav31OtherObjectTypeIsNotNullAndNotMatched();
        testNav31NoSelectionHookNoPhantomHistory();
        testNav32OtherNativePeriodInterfaceAndSameLiveReference();
        testNav32OtherObjectSwappedAfterAttachFailsClosed();
        testNav32NoOriginalSelectionHistoryIsExplicitlyUnproven();
        testNav33DirectOriginalLo96MatchesSource();
        testNav33DirectLo96NullAndDifferentSourcesFailClosed();
        testNav34LiveOriginalSourceMatchesFlowTrackAlbumWrapper();
        testNav34MissingAlbumAndWrongScopedWrapperNeverPromote();
        testNav35DifferentPlayerWrapperHasExactReason();
        testNav35AlbumUnsetAndAmbiguousWrapperReasons();
        testNav35WrongPlayerSourceDoesNotClassifyReason();
        testNav36OriginalTcaBirthCategories();
        testNav37ExactTcaCreatorTrackFieldLinksWrapperAndAlbum();
        testNav37NullCreatorTrackFieldShadowsOuterTrackScope();
        testNav38CreatorTrackLaterFlowExactIdentity();
        testNav40ExactLaterFlowUnderLiveOriginalSource();
        testNav48TcaCreatorFlowBirthSurvivesWrapperLinkEvictionOnLivePeriod();
        testNav36ConstructorWitnessCannotCrossWrongSource();
        testNav47ExactAdapterAndCurrentSourceSameStartedRead();
        testNav47DifferentRendererStreamCannotMatchPeriodAdapter();
        testNav47AdapterWithoutChildCannotPromote();
        testNav50AlternateSourceReadIsJoinedToLiveCurrentPeriod();
        testNav41OnlySameNonEosSlotBReadExaminesCurrentPeriod();
        testNav41RejectUidOnlyAndOldPeriodSameUidNotEdition();
        testNav41NoFieldsOrNoActiveSlotCannotProduceMatch();
        testNav42UnknownEosUsesSeparateStructuralCohorts();
        testNav42UnknownEosUidAndIndexAndStaleGuard();
        testNav42DisabledPeriodHookAndReattachNeverMatch();
        testNav43JointUnknownEosExactSourceAndPlayerSameRead();
        testNav43JointRequiresFlowAndUniqueSourceAndStableSlot();
        testNav43MissingSourceNoHistoryJoin();
        testNav44OriginalTimelineAndSourceSameItem();
        testNav44DifferentAndChangedSlotFailClosed();
        testOriginalCreatorEarlySourceSetterBeforeFlow();
        testEarlySourceFailureConflictAndNextGeneration();
        testEarlySetterWhenFlowPrecedesWrapperBirth();
        testOriginalEarlySetterFeedsExistingNativeLifecycle();
        testEarlySetterSameSourceReachesActualCurrentPeriod();
        testOriginalExactMediaPeriodBeforePrepareNoAlternate();
        testOriginalPrepareSealsNativeLifecycleBeforeLateIdentity();
        testUnlinkedOriginalPrepareSealsLateNativeAdmission();
        testExactOriginalPrepareTracksPreopenDataSourceCandidate();
        testExactCreatorBeforeFlowOriginalDataSourceLink();
        testNav49SameTrackWrappersKeepIndependentSourceLineages();
        testNav49EvictedSameTrackWrapperRestoresBesideSibling();
        testTcaCreatorFlowBirthRestoresEvictedWrapperLineage();
        testNativeFirstOpenedFactorySourceNotFirstConstructed();
        testRealPublisherAnnotatedTrackIdCorrelatesCreator();
        testRealPublisherTrackIdAtNativeSourceSetter();
        testApprovedNativeGrantRoutesRealOriginalExoPreprepare();
        testNestedEarlySourceRejectCannotLeavePendingRevision();
        System.out.println("NATIVE_RENDERER_READONLY_EVIDENCE_MODEL_PASS");
    }
}
