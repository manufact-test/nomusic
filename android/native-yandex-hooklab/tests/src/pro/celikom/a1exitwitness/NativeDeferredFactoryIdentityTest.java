package pro.celikom.a1exitwitness;

/** Fully real Java object-reference witness before issuer Exo DataSource.open. */
public final class NativeDeferredFactoryIdentityTest {
    static void check(boolean ok,String message) {
        if(!ok)throw new AssertionError(message);
    }
    public static void main(String[] args) {
        StageBAudioEvidence stage=new StageBAudioEvidence();
        NativeRendererStreamEvidence renderer=new NativeRendererStreamEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object();
        Object source=new Object(),descriptor=new Object(),factory=new Object();
        Object dataSource=new Object();
        stage.onNativeTrackAlbumConstructed(track,album);
        stage.enterNativeTrackSourceRequest(track,null);
        stage.onPublisherAnnotatedTrackId("42884423");
        stage.exitNativeTrackSourceRequest();
        stage.enterNativeTcaCreatorOwner(new Object());
        stage.enterNativeTcaCreatorTrackScope(track,1);
        stage.onNativeTrackWrapperCreated(wrapper,"42884423");
        stage.exitNativeTcaCreatorTrackScope();
        stage.exitNativeTcaCreatorOwner();
        stage.onNativeTrackFlowEmission(track);
        check("42884423".equals(stage.exactPublisherTrackIdForCreator(
            wrapper,track,album)),"SIGNED_ORIGINAL_CREATOR_TRACKID_LINK");

        renderer.setEarlyOriginalSourceEvidence(
            stage::exactCreatorTrackAlbumBeforeSourceSet);
        renderer.setExactPublisherTrackIdEvidence(
            stage::exactPublisherTrackIdForCreator);
        NativeRendererStreamEvidence.TrackPlayerScope scope=
            renderer.enterTrackPlayerSource(wrapper);
        NativeRendererStreamEvidence.EarlyOriginalSourceFrame frame=
            renderer.beginEarlyOriginalSourceSet(source);
        check(frame!=null && frame.generation==1,
            "SCOPED_ORIGINAL_PLAYER_SETTER_CREATED");
        renderer.finishEarlyOriginalSourceSet(frame,true);
        renderer.exitTrackPlayerSource(scope);
        check(renderer.exactSetterForFreshSourceCreator(wrapper,track,
            new Object())==null,"WRONG_ALBUM_MUST_NOT_BIND");
        check(renderer.exactSetterForFreshSourceCreator(new Object(),track,
            album)==null,"WRONG_WRAPPER_MUST_NOT_BIND");

        stage.enterNativeMainSourceRequest(wrapper,null);
        stage.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);
        stage.exitNativeMainSourceRequest();
        stage.onExoFactoryCreated(descriptor,factory);
        stage.onExoSourceInstanceCreated(dataSource,factory);
        Object[] creator=stage.exactFreshCreatorForDataSource(dataSource);
        check(creator!=null && creator.length==3 && creator[0]==wrapper
            && creator[1]==track && creator[2]==album,
            "EXO_FACTORY_CREATOR_UNOPENED_REFERENCE_LINK");
        Object[] setter=renderer.exactSetterForFreshSourceCreator(
            creator[0],creator[1],creator[2]);
        check(setter!=null && ((Long)setter[0])==1 && setter[1]==source,
            "SAME_PUBLISHER_PLAYER_SOURCE_FROM_EXO_FACTORY");
        check(stage.exactFreshCreatorForDataSource(new Object())==null,
            "UNRELATED_EXO_SOURCE_NEVER_BIND");
        stage.onExoSourceInstanceOpenAttempt(dataSource);
        check(stage.exactFreshCreatorForDataSource(dataSource)==null,
            "OPENED_SOURCE_CANNOT_BE_RETROACTIVELY_ARMED");

        NativeRendererStreamEvidence.TrackPlayerScope next=
            renderer.enterTrackPlayerSource(wrapper);
        renderer.beginEarlyOriginalSourceSet(new Object());
        renderer.exitTrackPlayerSource(next);
        check(renderer.exactSetterForFreshSourceCreator(wrapper,track,
            album)==null,"NEXT_INVALIDATES_PREVIOUS_SETTER_LINK");
        System.out.println("NATIVE_DEFERRED_FACTORY_SAME_SOURCE_IDENTITY_PASS");
    }
}
