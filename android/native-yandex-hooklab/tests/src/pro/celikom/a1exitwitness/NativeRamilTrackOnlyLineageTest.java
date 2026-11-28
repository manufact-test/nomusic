package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeSourceGate;
import java.lang.reflect.Field;
import java.lang.ref.WeakReference;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** Real original object references, no original Album/Edition ever asserted. */
public final class NativeRamilTrackOnlyLineageTest {
    private static final class TestPeriod { Object source; }
    private static final class TestWrapper { TestPeriod period; }
    private static final class TestHolder { Object nested; }

    private static void check(boolean ok,String message) {
        if(!ok)throw new AssertionError(message);
    }
    private static StageBAudioEvidence fresh(String publisherId,Object track,
            Object wrapper,boolean signedConstructor,boolean issuerCalled) {
        StageBAudioEvidence evidence=new StageBAudioEvidence();
        if(issuerCalled) {
            evidence.enterNativeTrackSourceRequest(track,null);
            evidence.onPublisherAnnotatedTrackId(publisherId);
            evidence.exitNativeTrackSourceRequest();
        }
        evidence.enterNativeTcaCreatorOwner(new Object());
        evidence.enterNativeTcaCreatorTrackScope(track,1);
        evidence.onNativeTrackWrapperCreated(wrapper,
            signedConstructor?publisherId:"321321321");
        evidence.exitNativeTcaCreatorTrackScope();
        evidence.exitNativeTcaCreatorOwner();
        return evidence;
    }
    private static int lateFlowRequests(boolean prepareBeforeFlow) {
        final String ramil=NativeTrackIdBetaPolicy.RAMIL_AU;
        StageBAudioEvidence stage=new StageBAudioEvidence(()->1000L);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        Object source=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        stage.enterNativeTcaCreatorTrackScope(track,1);
        stage.onNativeTrackWrapperCreated(wrapper,ramil);
        stage.exitNativeTcaCreatorTrackScope();
        stage.exitNativeTcaCreatorOwner();

        NativeRendererStreamEvidence renderer=new NativeRendererStreamEvidence();
        NativeEarlySourceLifecycleBridge bridge=new NativeEarlySourceLifecycleBridge(
            ()->1000L);
        renderer.setEarlyOriginalSourceEvidence(
            stage::exactCreatorTrackAlbumOrBetaBeforeSourceSet);
        renderer.setExactPublisherTrackIdEvidence(
            stage::exactPublisherTrackIdForCreatorOrBeta);
        renderer.setPublisherTrackIdPendingEvidence(
            stage::mayResolvePublisherTrackIdAfterFlow);
        renderer.setEarlyOriginalSourceObserver(bridge);
        AtomicInteger requests=new AtomicInteger();
        bridge.setLimitedBetaGrantRequester((generation,t,a,s,id)->{
            check(generation==1 && t==track && a==album && s==source
                && ramil.equals(id),"LATE_FLOW_RETAINS_EXACT_ORIGINAL_SETTER");
            requests.incrementAndGet();
        });
        bridge.startForAuthenticatedOwner();
        NativeRendererStreamEvidence.TrackPlayerScope player=
            renderer.enterTrackPlayerSource(wrapper);
        NativeRendererStreamEvidence.EarlyOriginalSourceFrame frame=
            renderer.beginEarlyOriginalSourceSet(source);
        check(frame!=null && frame.track==track && frame.album==album
            && frame.originalPublisherTrackIdCandidate==null
            && frame.publisherTrackIdCandidatePending,
            "CREATOR_KEY_WITHHELD_BUT_EXACT_FLOW_IS_PENDING");
        renderer.finishEarlyOriginalSourceSet(frame,true);
        check(requests.get()==0,"NO_BETA_REQUEST_BEFORE_CREATOR_FLOW");
        if(prepareBeforeFlow)
            bridge.beforeOriginalPeriodPrepare(1,track,album,source,new Object(),null);
        stage.onNativeTrackFlowEmission(track);
        renderer.refreshEarlyOriginalPublisherTrackIdCandidate();
        renderer.exitTrackPlayerSource(player);
        return requests.get();
    }

    private static int lateFlowDuringPrepareWait() {
        final String ramil=NativeTrackIdBetaPolicy.RAMIL_AU;
        StageBAudioEvidence stage=new StageBAudioEvidence(()->1000L);
        Object track=new Object(),album=new Object(),wrapper=new Object();
        Object source=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTcaCreatorOwner(new Object());
        stage.enterNativeTcaCreatorTrackScope(track,1);
        stage.onNativeTrackWrapperCreated(wrapper,ramil);
        stage.exitNativeTcaCreatorTrackScope();
        stage.exitNativeTcaCreatorOwner();

        NativeRendererStreamEvidence renderer=new NativeRendererStreamEvidence();
        NativeEarlySourceLifecycleBridge bridge=new NativeEarlySourceLifecycleBridge(
            ()->1000L);
        renderer.setEarlyOriginalSourceEvidence(
            stage::exactCreatorTrackAlbumOrBetaBeforeSourceSet);
        renderer.setExactPublisherTrackIdEvidence(
            stage::exactPublisherTrackIdForCreatorOrBeta);
        renderer.setPublisherTrackIdPendingEvidence(
            stage::mayResolvePublisherTrackIdAfterFlow);
        renderer.setEarlyOriginalSourceObserver(bridge);
        AtomicInteger requests=new AtomicInteger();
        bridge.setLimitedBetaGrantRequester((generation,t,a,s,id)->{
            check(generation==1 && t==track && a==album && s==source
                && ramil.equals(id),"PREPARE_WAIT_USES_EXACT_CREATOR_ID");
            requests.incrementAndGet();
        });
        bridge.startForAuthenticatedOwner();
        NativeRendererStreamEvidence.TrackPlayerScope player=
            renderer.enterTrackPlayerSource(wrapper);
        NativeRendererStreamEvidence.EarlyOriginalSourceFrame frame=
            renderer.beginEarlyOriginalSourceSet(source);
        check(frame!=null && frame.publisherTrackIdCandidatePending,
            "PREPARE_WAIT_HAS_EXACT_PENDING_CREATOR");
        renderer.finishEarlyOriginalSourceSet(frame,true);

        AtomicBoolean returned=new AtomicBoolean(false);
        Thread waiter=new Thread(()->{
            bridge.awaitLimitedBetaGrantAtPrepare(250);
            returned.set(true);
        });
        waiter.start();
        pause(35);
        check(!returned.get(),"PREPARE_WAIT_DOES_NOT_SKIP_PENDING_FLOW");
        stage.onNativeTrackFlowEmission(track);
        renderer.refreshEarlyOriginalPublisherTrackIdCandidate();
        check(requests.get()==1,"PENDING_FLOW_DISPATCHES_SOURCE_BOUND_REQUEST");
        try {waiter.join(1000L);}
        catch(InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new AssertionError("PREPARE_WAIT_INTERRUPTED",interrupted);
        }
        check(returned.get(),"PREPARE_WAIT_REMAINS_BOUNDED");
        renderer.exitTrackPlayerSource(player);
        return requests.get();
    }

    private static void clearWeakFactoryWitnesses(StageBAudioEvidence evidence,
            Object wrapper) {
        try {
            Field linksField=StageBAudioEvidence.class
                .getDeclaredField("nativeTrackSourceLinks");
            linksField.setAccessible(true);
            java.util.List<?> links=(java.util.List<?>)linksField.get(evidence);
            Object found=null;
            for(Object candidate:links) {
                Field wrapperField=candidate.getClass().getDeclaredField("wrapper");
                wrapperField.setAccessible(true);
                WeakReference<?> ref=(WeakReference<?>)wrapperField.get(candidate);
                if(ref!=null && ref.get()==wrapper) {
                    if(found!=null)throw new AssertionError("DUPLICATE_WRAPPER_LINK");
                    found=candidate;
                }
            }
            check(found!=null,"EXACT_WRAPPER_LINK_PRESENT");
            for(String name:new String[]{"descriptor","factoryResult"}) {
                Field field=found.getClass().getDeclaredField(name);
                field.setAccessible(true);
                field.set(found,new WeakReference<Object>(null));
            }
        } catch(ReflectiveOperationException failure) {
            throw new AssertionError("WEAK_FACTORY_WITNESS_FIXTURE",failure);
        }
    }

    private static void pause(long millis) {
        try {Thread.sleep(millis);}
        catch(InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new AssertionError("TEST_INTERRUPTED",interrupted);
        }
    }

    public static void main(String[] args) {
        final String ramil=NativeTrackIdBetaPolicy.RAMIL_AU;
        Object track=new Object(), wrapper=new Object(), nativeSource=new Object();
        StageBAudioEvidence stage=fresh(ramil,track,wrapper,true,true);
        check(stage.exactCreatorTrackAlbumBeforeSourceSet(wrapper)==null,
            "NO_FAKE_ORIGINAL_ALBUM_PERMITTED");
        Object[] scope=stage.exactBetaCreatorWithoutAlbum(wrapper);
        check(scope!=null && scope[0]==track && scope[1]==wrapper,
            "EXACT_SOURCE_CREATOR_AND_BETA_TOKEN");
        check(ramil.equals(stage.exactPublisherTrackIdForCreatorOrBeta(
            wrapper,track,wrapper)),"SAME_ISSUER_API_AND_TCA_CONSTRUCTOR_ID");

        NativeRendererStreamEvidence renderer=new NativeRendererStreamEvidence();
        NativeEarlySourceLifecycleBridge bridge=new NativeEarlySourceLifecycleBridge(
            ()->1000L);
        renderer.setEarlyOriginalSourceEvidence(
            stage::exactCreatorTrackAlbumOrBetaBeforeSourceSet);
        renderer.setExactPublisherTrackIdEvidence(
            stage::exactPublisherTrackIdForCreatorOrBeta);
        renderer.setPublisherTrackIdPendingEvidence(
            stage::mayResolvePublisherTrackIdAfterFlow);
        renderer.setEarlyOriginalSourceObserver(bridge);
        bridge.startForAuthenticatedOwner();
        NativeRendererStreamEvidence.TrackPlayerScope player=
            renderer.enterTrackPlayerSource(wrapper);
        NativeRendererStreamEvidence.EarlyOriginalSourceFrame frame=
            renderer.beginEarlyOriginalSourceSet(nativeSource);
        check(frame!=null && frame.track==track && frame.album==wrapper
            && ramil.equals(frame.originalPublisherTrackIdCandidate),
            "ORIGINAL_PUBLISHER_ID_AND_SOURCE_REFERENCES_ON_SETTER");
        renderer.finishEarlyOriginalSourceSet(frame,true);
        renderer.exitTrackPlayerSource(player);
        try {
            Field holderWrapper=TestHolder.class.getDeclaredField("nested");
            Field wrapperPeriod=TestWrapper.class.getDeclaredField("period");
            Field periodSource=TestPeriod.class.getDeclaredField("source");
            renderer.setExactActivePeriodFields(holderWrapper,wrapperPeriod,
                periodSource,TestWrapper.class,TestPeriod.class,Object.class);
            TestPeriod exactPeriod=new TestPeriod();
            exactPeriod.source=nativeSource;
            check(renderer.exactOriginalWrapperForPeriod(exactPeriod)==wrapper,
                "PERIOD_SOURCE_RETAINS_EXACT_PLAYER_WRAPPER");
            TestPeriod unrelatedPeriod=new TestPeriod();
            unrelatedPeriod.source=new Object();
            check(renderer.exactOriginalWrapperForPeriod(unrelatedPeriod)==null,
                "UNRELATED_PERIOD_CANNOT_INHERIT_PLAYER_WRAPPER");
        } catch(ReflectiveOperationException failure) {
            throw new AssertionError("EXACT_PERIOD_SOURCE_TEST_SETUP",failure);
        }
        check(bridge.isSuccessfulOriginalSource(1,track,wrapper,nativeSource),
            "SUCCESSFUL_NATIVE_PLAYER_SOURCE_SETTER");
        check(renderer.exactEarlySetterSourceAtGeneration(nativeSource,1)!=null,
            "EXACT_EARLY_SETTER_SURVIVES_PREPARE");

        Object descriptor=new Object(),factory=new Object(),dataSource=new Object();
        stage.enterNativePlayerSourceSelection(wrapper);
        stage.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);
        stage.exitNativePlayerSourceSelection();
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==null,
            "DESCRIPTOR_WITHOUT_FACTORY_PRODUCT_CANNOT_RESOLVE");
        stage.onExoFactoryCreated(descriptor,factory);
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==null,
            "FACTORY_WITHOUT_DATASOURCE_CANNOT_RESOLVE");
        stage.onExoSourceInstanceCreated(dataSource,factory);
        Object[] link=stage.exactFreshCreatorOrBetaForDataSource(dataSource);
        check(link!=null && link[0]==wrapper && link[1]==track
            && link[2]==wrapper,"EXACT_EXO_FACTORY_SOURCE_WITHOUT_ALBUM");
        Object[] firstOpen=stage.exactFreshCreatorOrBetaAtFirstOpen(dataSource);
        check(firstOpen!=null && firstOpen[0]==wrapper && firstOpen[1]==track
            && firstOpen[2]==wrapper,"NAV53_EXACT_FIRST_OPEN_COMMITS_SOURCE");
        Object[] publisher=renderer.exactSetterForFreshSourceCreator(
            link[0],link[1],link[2]);
        check(publisher!=null && ((Long)publisher[0])==1
            && publisher[1]==nativeSource,"EXACT_PLAYER_SOURCE_TO_EXO_DATA_SOURCE");
        stage.onExoSourceInstanceOpenAttempt(dataSource);
        stage.onExoSourceInstanceOpen(dataSource);
        stage.onExoSourceInstanceRead(dataSource,7);
        check(stage.exactFreshCreatorOrBetaForDataSource(dataSource)==null,
            "OPENED_ORIGINAL_SOURCE_CANNOT_BE_ARMED");
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==dataSource,
            "LIVE_RENDERER_RESOLVES_EXACT_BETA_DATASOURCE_AFTER_READ");
        Object laterSiblingDataSource=new Object();
        stage.onExoSourceInstanceCreated(laterSiblingDataSource,factory);
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==dataSource,
            "NAV53_FIRST_OPEN_SOURCE_PIN_SURVIVES_LATER_FACTORY_PRODUCT");
        check(stage.exactFreshCreatorOrBetaAtFirstOpen(laterSiblingDataSource)==null,
            "NAV53_LATER_SIBLING_CANNOT_REPLACE_OR_REARM_COMMITTED_SOURCE");
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==dataSource,
            "NAV53_REJECTED_SIBLING_DOES_NOT_REBIND_LIVE_SOURCE");
        clearWeakFactoryWitnesses(stage,wrapper);
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==dataSource,
            "LIVE_RENDERER_SOURCE_IDENTITY_SURVIVES_WEAK_DESCRIPTOR_FACTORY_LOSS");
        Object replacementDescriptor=new Object(),replacementFactory=new Object();
        Object replacementDataSource=new Object();
        stage.enterNativePlayerSourceSelection(wrapper);
        stage.onNativeExoDescriptorBuiltForCurrentWrapper(replacementDescriptor);
        stage.exitNativePlayerSourceSelection();
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==null,
            "DESCRIPTOR_REBIND_INVALIDATES_OLD_SOURCE_IDENTITY");
        stage.onExoFactoryCreated(replacementDescriptor,replacementFactory);
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==null,
            "REBOUND_FACTORY_WITHOUT_PRODUCT_REMAINS_UNRESOLVED");
        stage.onExoSourceInstanceCreated(replacementDataSource,replacementFactory);
        check(stage.linkedSourceInstanceForCreatorOrBeta(wrapper)==replacementDataSource,
            "REBOUND_EXACT_FACTORY_SOURCE_RESOLVES");
        check(String.join("\n",stage.exportLines()).contains(
            "origin=LIVE_PERIOD_SOURCE_LOOKUP_RESOLVED;error=FEW"),
            "LIVE_SOURCE_LOOKUP_RESOLUTION_COUNTER");
        check(stage.linkedSourceInstanceForCreatorOrBeta(new Object())==null,
            "LIVE_RENDERER_NEVER_GUESSES_ANOTHER_WRAPPER_DATASOURCE");

        StageBAudioEvidence wrongIssuer=fresh(ramil,new Object(),new Object(),
            true,false);
        check(wrongIssuer.exactBetaCreatorWithoutAlbum(wrapper)==null,
            "DIFFERENT_WRAPPER_MUST_NOT_PROMOTE");
        Object deniedWrapper=new Object(),deniedTrack=new Object();
        StageBAudioEvidence missingIssuer=fresh(ramil,deniedTrack,deniedWrapper,
            true,false);
        check(missingIssuer.exactBetaCreatorWithoutAlbum(deniedWrapper)==null,
            "NO_ISSUER_ANNOTATION_NEVER_BETA");
        StageBAudioEvidence wrongKey=fresh(ramil,new Object(),
            deniedWrapper,false,true);
        check(wrongKey.exactBetaCreatorWithoutAlbum(deniedWrapper)==null,
            "MISMATCHED_PUBLISHER_TCA_KEY_NEVER_BETA");
        Object unrelatedWrapper=new Object(),unrelatedTrack=new Object();
        StageBAudioEvidence unrelated=fresh("1234567",unrelatedTrack,
            unrelatedWrapper,true,true);
        check(unrelated.exactBetaCreatorWithoutAlbum(unrelatedWrapper)==null,
            "ALL_OTHERS_REMAIN_ORIGINAL");

        NativeRendererStreamEvidence.TrackPlayerScope next=
            renderer.enterTrackPlayerSource(wrapper);
        renderer.beginEarlyOriginalSourceSet(new Object());
        renderer.exitTrackPlayerSource(next);
        check(renderer.exactSetterForFreshSourceCreator(
            wrapper,track,wrapper)==null,
            "NEXT_INVALIDATES_ORIGINAL_BETA_TRACKID_SOURCE");
        check(bridge.chosenSource()==NativeSourceGate.Choice.ORIGINAL,
            "STILL_ORIGINAL_WITHOUT_SIGNED_AUDIO_AND_REAL_PREPARE");
        check(lateFlowRequests(false)==1,
            "LATE_CREATOR_FLOW_COMPLETES_TRACKID_BEFORE_PREPARE");
        check(lateFlowRequests(true)==0,
            "LATE_CREATOR_FLOW_AFTER_PREPARE_CANNOT_UPGRADE");
        check(lateFlowDuringPrepareWait()==1,
            "PREPARE_GRACE_WAITS_FOR_LATE_EXACT_FLOW_ID");
        System.out.println("RAMIL_AU_ORIGINAL_TRACK_ONLY_BETA_LINEAGE_PASS");
    }
}
