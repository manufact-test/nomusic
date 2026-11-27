#!/usr/bin/env python3
"""Verify live-module Stage B export categories with isolated JDK only.

This tests real Java evidence counter/export code, not native Yandex playback,
owner account, decoder selection, entitlement or replacement.
"""
import pathlib
import subprocess
import tempfile
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
SRC = BASE / "exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness"
HOOK = SRC / "ExitCallsiteWitness.java"
EVIDENCE = SRC / "StageBAudioEvidence.java"
BETA_POLICY = SRC / "NativeTrackIdBetaPolicy.java"
GRANT_CONTRACT = BASE / "app/src/main/java/pro/celikom/yandex/nativehooklab/NativeGrantContract.java"
HARNESS = """
package pro.celikom.a1exitwitness;
public final class StageBAudioEvidenceTest {
    static void check(boolean value) { if (!value) throw new AssertionError(); }
    static void bucket(String[] rows,int index,String category,String value) {
        String expected="event=AUDIO_STAGE_B_SUMMARY;origin="+category+
            ";error="+value+";thread=OTHER";
        for(String row:rows) {
            if(row.contains(";origin="+category+";")) {
                if(!row.equals(expected))
                    throw new AssertionError("BUCKET_MISMATCH category="+category
                        +" expected="+expected+" actual="+row);
                return;
            }
        }
        throw new AssertionError("MISSING_CATEGORY_"+category);
    }
    static boolean contains(String[] rows,String fragment) {
        for(String row:rows) if(row.contains(fragment)) return true;
        return false;
    }
    static StageBAudioEvidence exactAlbumLinked(Object track,Object album,Object wrapper,
            Object descriptor,Object factory,Object source) {
        StageBAudioEvidence evidence=new StageBAudioEvidence();
        evidence.onNativeTrackAlbumConstructed(track,album);
        evidence.onNativeTrackFlowEmission(track);
        evidence.enterNativeTrackSourceRequest(track,null);
        evidence.onNativeTrackWrapperCreated(wrapper);
        evidence.exitNativeTrackSourceRequest();
        evidence.enterNativeMainSourceRequest(wrapper,null);
        evidence.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);
        evidence.exitNativeMainSourceRequest();
        evidence.onExoFactoryCreated(descriptor,factory);
        evidence.onExoSourceInstanceCreated(source,factory);
        return evidence;
    }
    static StageBAudioEvidence exactLinked(Object track,Object wrapper,Object descriptor,
            Object factory,Object source) {
        StageBAudioEvidence evidence=new StageBAudioEvidence();
        evidence.onNativeTrackFlowEmission(track);
        evidence.enterNativeTrackSourceRequest(track,null);
        evidence.onNativeTrackWrapperCreated(wrapper);
        evidence.exitNativeTrackSourceRequest();
        evidence.enterNativeMainSourceRequest(wrapper,null);
        evidence.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);
        evidence.exitNativeMainSourceRequest();
        evidence.onExoFactoryCreated(descriptor,factory);
        evidence.onExoSourceInstanceCreated(source,factory);
        return evidence;
    }

    static void beta9CrossThreadFixture() {
        java.util.concurrent.atomic.AtomicLong clock=new java.util.concurrent.atomic.AtomicLong(1000L);
        String id=NativeTrackIdBetaPolicy.RAMIL_AU;
        StageBAudioEvidence e=new StageBAudioEvidence(clock::get);
        e.onPublisherAnnotatedTrackId(id); // concrete Retrofit worker, no Track ThreadLocal
        Object track=new Object(),album=new Object(),wrapper=new Object();
        e.onNativeTrackAlbumConstructed(track,album);
        e.enterNativeTcaCreatorOwner(new Object());
        e.enterNativeTcaCreatorTrackScope(track,1);
        e.onNativeTrackWrapperCreated(wrapper,id);
        e.exitNativeTcaCreatorTrackScope();
        e.exitNativeTcaCreatorOwner();
        Object[] pair=e.exactCreatorTrackAlbumOrBetaBeforeSourceSet(wrapper);
        check(pair!=null && pair[0]==track && pair[1]==album);
        check(id.equals(e.exactPublisherTrackIdForCreatorOrBeta(
            wrapper,pair[0],pair[1])));
        clock.set(75000L); // a bound original wrapper can outlive issuer ticket
        check(id.equals(e.exactPublisherTrackIdForCreatorOrBeta(
            wrapper,pair[0],pair[1])));
        e.onNativeTrackAlbumConstructed(track,new Object());
        check(e.exactPublisherTrackIdForCreatorOrBeta(
            wrapper,pair[0],pair[1])==null);

        StageBAudioEvidence none=new StageBAudioEvidence(clock::get);
        Object nt=new Object(),na=new Object(),nw=new Object();
        none.onNativeTrackAlbumConstructed(nt,na);
        none.enterNativeTcaCreatorOwner(new Object());
        none.enterNativeTcaCreatorTrackScope(nt,1);
        none.onNativeTrackWrapperCreated(nw,id);
        none.exitNativeTcaCreatorTrackScope();
        none.exitNativeTcaCreatorOwner();
        Object[] noIssuer=none.exactCreatorTrackAlbumOrBetaBeforeSourceSet(nw);
        check(noIssuer!=null && none.exactPublisherTrackIdForCreatorOrBeta(
            nw,noIssuer[0],noIssuer[1])==null); // creator not yet in Flow
        none.onNativeTrackFlowEmission(nt);
        check(id.equals(none.exactPublisherTrackIdForCreatorOrBeta(
            nw,noIssuer[0],noIssuer[1]))); // cached publisher source, no FileInfo

        clock.set(1000L);
        StageBAudioEvidence expired=new StageBAudioEvidence(clock::get);
        expired.onPublisherAnnotatedTrackId(id);
        clock.set(90000L);
        Object et=new Object(),ea=new Object(),ew=new Object();
        expired.onNativeTrackAlbumConstructed(et,ea);
        expired.enterNativeTcaCreatorOwner(new Object());
        expired.enterNativeTcaCreatorTrackScope(et,1);
        expired.onNativeTrackWrapperCreated(ew,id);
        expired.exitNativeTcaCreatorTrackScope();
        expired.exitNativeTcaCreatorOwner();
        expired.onNativeTrackFlowEmission(et);
        Object[] old=expired.exactCreatorTrackAlbumOrBetaBeforeSourceSet(ew);
        check(old!=null && expired.exactPublisherTrackIdForCreatorOrBeta(
            ew,old[0],old[1])==null); // stale API ticket still rejects

        clock.set(1000L);
        StageBAudioEvidence beta=new StageBAudioEvidence(clock::get);
        beta.onPublisherAnnotatedTrackId(id);
        Object bt=new Object(),bw=new Object();
        beta.enterNativeTcaCreatorOwner(new Object());
        beta.enterNativeTcaCreatorTrackScope(bt,1);
        beta.onNativeTrackWrapperCreated(bw,id);
        beta.exitNativeTcaCreatorTrackScope();
        beta.exitNativeTcaCreatorOwner();
        check(beta.exactCreatorTrackAlbumOrBetaBeforeSourceSet(bw)==null);
        beta.onNativeTrackFlowEmission(bt);
        Object[] bound=beta.exactCreatorTrackAlbumOrBetaBeforeSourceSet(bw);
        check(bound!=null && bound[0]==bt && bound[1]==bw);
        check(id.equals(beta.exactPublisherTrackIdForCreatorOrBeta(
            bw,bound[0],bound[1])));

        // The owner may have other numeric FileInfo calls for unrelated
        // songs while the actual selected original is served from cache.
        StageBAudioEvidence unrelatedRequest=new StageBAudioEvidence(clock::get);
        unrelatedRequest.onPublisherAnnotatedTrackId("987654321");
        Object urt=new Object(),ura=new Object(),urw=new Object();
        unrelatedRequest.onNativeTrackAlbumConstructed(urt,ura);
        unrelatedRequest.enterNativeTcaCreatorOwner(new Object());
        unrelatedRequest.enterNativeTcaCreatorTrackScope(urt,1);
        unrelatedRequest.onNativeTrackWrapperCreated(urw,id);
        unrelatedRequest.exitNativeTcaCreatorTrackScope();
        unrelatedRequest.exitNativeTcaCreatorOwner();
        unrelatedRequest.onNativeTrackFlowEmission(urt);
        Object[] unrelatedPair=unrelatedRequest.exactCreatorTrackAlbumOrBetaBeforeSourceSet(urw);
        check(unrelatedPair!=null && id.equals(
            unrelatedRequest.exactPublisherTrackIdForCreatorOrBeta(
                urw,unrelatedPair[0],unrelatedPair[1])));

        // Cached original publisher source without an Album reference:
        // still requires the exact Track creator birth and later original Flow.
        StageBAudioEvidence cachedNoAlbum=new StageBAudioEvidence(clock::get);
        Object ct=new Object(),cw=new Object();
        cachedNoAlbum.enterNativeTcaCreatorOwner(new Object());
        cachedNoAlbum.enterNativeTcaCreatorTrackScope(ct,1);
        cachedNoAlbum.onNativeTrackWrapperCreated(cw,id);
        cachedNoAlbum.exitNativeTcaCreatorTrackScope();
        cachedNoAlbum.exitNativeTcaCreatorOwner();
        check(cachedNoAlbum.exactCreatorTrackAlbumOrBetaBeforeSourceSet(cw)==null);
        cachedNoAlbum.onNativeTrackFlowEmission(ct);
        Object[] cached=cachedNoAlbum.exactCreatorTrackAlbumOrBetaBeforeSourceSet(cw);
        check(cached!=null && cached[0]==ct && cached[1]==cw);
        check(id.equals(cachedNoAlbum.exactPublisherTrackIdForCreatorOrBeta(
            cw,cached[0],cached[1])));

        // Real owner device also observes tCa creator when Track is already
        // in Flow and its original Album is present (birth scope 14).
        StageBAudioEvidence inFlow=new StageBAudioEvidence(clock::get);
        inFlow.onPublisherAnnotatedTrackId(id);
        Object ft=new Object(),fa=new Object(),fw=new Object();
        inFlow.onNativeTrackAlbumConstructed(ft,fa);
        inFlow.onNativeTrackFlowEmission(ft);
        inFlow.enterNativeTcaCreatorOwner(new Object());
        inFlow.enterNativeTcaCreatorTrackScope(ft,1);
        inFlow.onNativeTrackWrapperCreated(fw,id);
        inFlow.exitNativeTcaCreatorTrackScope();
        inFlow.exitNativeTcaCreatorOwner();
        Object[] found=inFlow.exactCreatorTrackAlbumOrBetaBeforeSourceSet(fw);
        check(found!=null && found[0]==ft && found[1]==fa);
        check(id.equals(inFlow.exactPublisherTrackIdForCreatorOrBeta(
            fw,found[0],found[1])));

        // Another original signed constructor ID never borrows Ramil's
        // Retrofit ticket, even with an otherwise exact original object chain.
        StageBAudioEvidence mismatched=new StageBAudioEvidence(clock::get);
        mismatched.onPublisherAnnotatedTrackId(id);
        Object mt=new Object(),ma=new Object(),mw=new Object();
        mismatched.onNativeTrackAlbumConstructed(mt,ma);
        mismatched.enterNativeTcaCreatorOwner(new Object());
        mismatched.enterNativeTcaCreatorTrackScope(mt,1);
        mismatched.onNativeTrackWrapperCreated(mw,"123456789");
        mismatched.exitNativeTcaCreatorTrackScope();
        mismatched.exitNativeTcaCreatorOwner();
        Object[] mismatch=mismatched.exactCreatorTrackAlbumOrBetaBeforeSourceSet(mw);
        check(mismatch!=null && mismatched.exactPublisherTrackIdForCreatorOrBeta(
            mw,mismatch[0],mismatch[1])==null);
    }

    static void clearAnchorWeakRef(StageBAudioEvidence evidence,String field) {
        try {
            java.lang.reflect.Field list=StageBAudioEvidence.class
                .getDeclaredField("originalMediaSourceItems");
            list.setAccessible(true);
            Object entry=((java.util.List<?>)list.get(evidence)).get(0);
            java.lang.reflect.Field ref=entry.getClass().getDeclaredField(field);
            ref.setAccessible(true);
            ((java.lang.ref.WeakReference<?>)ref.get(entry)).clear();
        } catch(ReflectiveOperationException ex) {
            throw new AssertionError(ex);
        }
    }
    static void originalChildCallerContextFixture() {
        // Passive only: the same original dA9 and gA9 arguments can be
        // observed without treating a different Of6 MediaItem as approved.
        StageBAudioEvidence e=new StageBAudioEvidence();
        Object track=new Object(),wrapper=new Object();
        Object owner=new Object(),config=new Object();
        Object item=new Object(),source=new Object(),different=new Object();
        e.onNativeTrackFlowEmission(track); // real wrapper link prerequisite
        e.enterNativeTrackSourceRequest(track,null);
        e.onNativeTrackWrapperCreated(wrapper);
        e.exitNativeTrackSourceRequest();
        e.enterNativePlayerSourceSelection(wrapper);
        e.onOriginalMediaSourceConstructed(source,item,owner,config);
        e.exitNativePlayerSourceSelection();
        e.onOriginalChildContextComparison(owner,config,item);
        e.onOriginalChildContextComparison(owner,config,different);
        check(e.exactOriginalMediaItemCreator(different)==null);
        e.onOriginalChildContextComparison(owner,new Object(),different);
        e.onOriginalChildContextComparison(new Object(),config,different);
        e.onOriginalChildContextComparison(new Object(),new Object(),different);
        e.onOriginalChildContextComparison(null,config,item);
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_CALLER_PAIR_SAME_ITEM","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_CALLER_PAIR_DIFFERENT_ITEM","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_CALLER_OWNER_ONLY","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_CALLER_CONFIG_ONLY","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_CALLER_NO_MATCH","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_CALLER_CONTEXT_UNAVAILABLE","ONE");
        e.enterNativePlayerSourceSelection(wrapper);
        Object secondSource=new Object(),secondItem=new Object();
        e.onOriginalMediaSourceConstructed(secondSource,secondItem,owner,config);
        e.exitNativePlayerSourceSelection();
        e.onOriginalChildContextComparison(owner,config,item);
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_CALLER_PAIR_AMBIGUOUS","ONE");
        // A shared caller pair does not bypass the original MediaItem == gate.
        check(e.exactOriginalMediaItemCreator(different)==null);
    }

    static void originalMediaItemSourceBridgeFixture() {
        // Same original iLb+Of6 across later child factory. No item values
        // read; a different item, source or wrapper must never inherit it.
        String id=NativeTrackIdBetaPolicy.RAMIL_AU;
        StageBAudioEvidence e=new StageBAudioEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object();
        Object mediaItem=new Object(),nativeMediaSource=new Object();
        Object descriptor=new Object(),factory=new Object(),dataSource=new Object();
        e.onNativeTrackAlbumConstructed(track,album);
        e.onNativeTrackFlowEmission(track);
        e.enterNativeTcaCreatorOwner(new Object());
        e.enterNativeTcaCreatorTrackScope(track,1);
        e.onNativeTrackWrapperCreated(wrapper,id);
        e.exitNativeTcaCreatorTrackScope();
        e.exitNativeTcaCreatorOwner();
        e.enterNativePlayerSourceSelection(wrapper);
        e.onOriginalMediaSourceConstructed(nativeMediaSource,mediaItem);
        e.exitNativePlayerSourceSelection();
        Object[] creator=e.exactOriginalMediaItemCreator(mediaItem);
        check(creator!=null && creator.length==4 && creator[0]==wrapper
            && creator[1]==track && creator[2]==album
            && creator[3]==nativeMediaSource);
        check(e.exactOriginalMediaItemCreator(new Object())==null);
        check(e.exactOriginalMediaItemCreator(null)==null);
        check(!e.onOriginalMediaItemDescriptor(mediaItem,new Object(),descriptor));
        check(!e.onOriginalMediaItemDescriptor(new Object(),wrapper,descriptor));
        check(e.onOriginalMediaItemDescriptor(mediaItem,wrapper,descriptor));
        e.onExoFactoryCreated(descriptor,factory);
        e.onExoSourceInstanceCreated(dataSource,factory);
        Object[] fresh=e.exactFreshCreatorOrBetaForDataSource(dataSource);
        check(fresh!=null && fresh[0]==wrapper && fresh[1]==track
            && fresh[2]==album);
        bucket(e.exportLines(),0,"ORIGINAL_MEDIAITEM_SOURCE_ANCHOR","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_MEDIAITEM_DESCRIPTOR_LINK","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_ITEM_NULL","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_LIVE_OTHER_ITEM_ANCHOR","FEW");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_NO_ITEM_ANCHORS","NONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_ORIGINAL_TRACK_ALBUM_REJECT","NONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_BETA_CREATOR_REJECT","NONE");
        // Runtime-safe BETA15 stage classification (no private values logged).
        e.onOriginalChildHookRegistered();
        e.onOriginalChildEntered();
        e.onOriginalChildCreatorMatch(true);
        e.onOriginalChildSetterMatch(true);
        e.onOriginalChildEntered();
        e.onOriginalChildCreatorMatch(false);
        e.onOriginalChildEntered();
        e.onOriginalChildCreatorMatch(true);
        e.onOriginalChildSetterMatch(false);
        e.onOriginalChildSetterSourceDifferent();
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_HOOK_REGISTERED","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_ENTER","FEW");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_CREATOR_MATCH","FEW");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_CREATOR_MISSING","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_SETTER_MATCH","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_SETTER_MISSING","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_SETTER_SOURCE_DIFFERENT","ONE");
        bucket(e.exportLines(),0,"TRACK_DESCRIPTOR_FACTORY_LINK","ONE");
        bucket(e.exportLines(),0,"TRACK_FACTORY_SOURCE_LINK","ONE");

        StageBAudioEvidence conflict=new StageBAudioEvidence();
        Object ct=new Object(),ca=new Object(),cw=new Object();
        Object commonItem=new Object(),firstSource=new Object();
        conflict.onNativeTrackAlbumConstructed(ct,ca);
        conflict.onNativeTrackFlowEmission(ct);
        conflict.enterNativeTcaCreatorOwner(new Object());
        conflict.enterNativeTcaCreatorTrackScope(ct,1);
        conflict.onNativeTrackWrapperCreated(cw,id);
        conflict.exitNativeTcaCreatorTrackScope();
        conflict.exitNativeTcaCreatorOwner();
        conflict.enterNativePlayerSourceSelection(cw);
        conflict.onOriginalMediaSourceConstructed(firstSource,commonItem);
        conflict.onOriginalMediaSourceConstructed(new Object(),commonItem);
        conflict.exitNativePlayerSourceSelection();
        check(conflict.exactOriginalMediaItemCreator(commonItem)==null);
        check(!conflict.onOriginalMediaItemDescriptor(commonItem,cw,new Object()));
        bucket(conflict.exportLines(),0,"ORIGINAL_MEDIAITEM_IDENTITY_CONFLICT","ONE");
        bucket(conflict.exportLines(),0,"ORIGINAL_CHILD_ITEM_ANCHOR_CONFLICT","FEW");
        // Deterministically simulate weak-reference loss without GC timing.
        clearAnchorWeakRef(e,"source");
        check(e.exactOriginalMediaItemCreator(mediaItem)==null);
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_WEAK_SOURCE_LOST","ONE");
        StageBAudioEvidence weakWrapper=new StageBAudioEvidence();
        Object wt=new Object(),wa=new Object(),ww=new Object();
        Object wi=new Object(),ws=new Object();
        weakWrapper.onNativeTrackAlbumConstructed(wt,wa);
        weakWrapper.onNativeTrackFlowEmission(wt);
        weakWrapper.enterNativeTcaCreatorOwner(new Object());
        weakWrapper.enterNativeTcaCreatorTrackScope(wt,1);
        weakWrapper.onNativeTrackWrapperCreated(ww,id);
        weakWrapper.exitNativeTcaCreatorTrackScope();
        weakWrapper.exitNativeTcaCreatorOwner();
        weakWrapper.enterNativePlayerSourceSelection(ww);
        weakWrapper.onOriginalMediaSourceConstructed(ws,wi);
        weakWrapper.exitNativePlayerSourceSelection();
        clearAnchorWeakRef(weakWrapper,"wrapper");
        check(weakWrapper.exactOriginalMediaItemCreator(wi)==null);
        bucket(weakWrapper.exportLines(),0,"ORIGINAL_CHILD_WEAK_WRAPPER_LOST","ONE");
        clearAnchorWeakRef(weakWrapper,"item");
        check(weakWrapper.exactOriginalMediaItemCreator(wi)==null);
        bucket(weakWrapper.exportLines(),0,
            "ORIGINAL_CHILD_ONLY_EXPIRED_ITEM_ANCHORS","ONE");
        StageBAudioEvidence noCreator=new StageBAudioEvidence();
        Object nt=new Object(),nw=new Object(),ni=new Object(),ns=new Object();
        noCreator.enterNativeTcaCreatorOwner(new Object());
        noCreator.enterNativeTcaCreatorTrackScope(nt,1);
        noCreator.onNativeTrackWrapperCreated(nw,id);
        noCreator.exitNativeTcaCreatorTrackScope();
        noCreator.exitNativeTcaCreatorOwner();
        noCreator.enterNativePlayerSourceSelection(nw);
        noCreator.onOriginalMediaSourceConstructed(ns,ni);
        noCreator.exitNativePlayerSourceSelection();
        check(noCreator.exactOriginalMediaItemCreator(ni)==null);
        bucket(noCreator.exportLines(),0,
            "ORIGINAL_CHILD_ORIGINAL_TRACK_ALBUM_REJECT","ONE");
        bucket(noCreator.exportLines(),0,"ORIGINAL_CHILD_BETA_CREATOR_REJECT","ONE");
        // Repeat of the same Track must not recycle an old wrapper selection.
        noCreator.enterNativeTcaCreatorOwner(new Object());
        noCreator.enterNativeTcaCreatorTrackScope(nt,1);
        noCreator.onNativeTrackWrapperCreated(new Object(),id);
        noCreator.exitNativeTcaCreatorTrackScope();
        noCreator.exitNativeTcaCreatorOwner();
        check(noCreator.exactOriginalMediaItemCreator(ni)==null);
        bucket(noCreator.exportLines(),0,"ORIGINAL_CHILD_WRAPPER_LINK_MISSING","NONE");
        bucket(noCreator.exportLines(),0,"TRACK_WRAPPER_SAME_TRACK_PARALLEL","ONE");

        StageBAudioEvidence wrongScope=new StageBAudioEvidence();
        wrongScope.onOriginalMediaSourceConstructed(new Object(),new Object());
        bucket(wrongScope.exportLines(),0,"ORIGINAL_MEDIAITEM_SOURCE_ANCHOR","NONE");
        check(wrongScope.exactOriginalMediaItemCreator(new Object())==null);
        bucket(wrongScope.exportLines(),0,"ORIGINAL_CHILD_NO_ITEM_ANCHORS","ONE");
    }

    static void originalChildCoroutineCaptureFixture() {
        StageBAudioEvidence e=new StageBAudioEvidence();
        Object track=new Object(),album=new Object(),wrapper=new Object();
        Object source=new Object(),item=new Object(),childItem=new Object();
        Object coroutine=new Object(),wrongCoroutine=new Object(),descriptor=new Object();
        e.onNativeTrackAlbumConstructed(track,album);
        e.onNativeTrackFlowEmission(track);
        e.enterNativeTcaCreatorOwner(new Object());
        e.enterNativeTcaCreatorTrackScope(track,1);
        e.onNativeTrackWrapperCreated(wrapper,NativeTrackIdBetaPolicy.RAMIL_AU);
        e.exitNativeTcaCreatorTrackScope();
        e.exitNativeTcaCreatorOwner();
        e.enterNativePlayerSourceSelection(wrapper);
        e.onOriginalMediaSourceConstructed(source,item);
        e.exitNativePlayerSourceSelection();
        check(e.exactOriginalMediaItemCreator(childItem)==null);
        check(e.exactOriginalChildCoroutineCreator(childItem)==null);
        e.onOriginalChildCoroutineConstructed(coroutine,source,source);
        e.onOriginalChildCoroutineConstructed(wrongCoroutine,source,new Object());
        e.onOriginalChildCoroutineConstructed(wrongCoroutine,source,source); // invalid first capture stays poisoned
        e.enterOriginalChildCoroutineResume(wrongCoroutine,source);
        check(e.exactOriginalChildCoroutineCreator(childItem)==null);
        e.exitOriginalChildCoroutineResume();
        e.enterOriginalChildCoroutineResume(coroutine,new Object());
        check(e.exactOriginalChildCoroutineCreator(childItem)==null);
        e.exitOriginalChildCoroutineResume();
        e.enterOriginalChildCoroutineResume(coroutine,source);
        Object[] creator=e.exactOriginalChildCoroutineCreator(childItem);
        check(creator!=null && creator[0]==wrapper && creator[1]==track
            && creator[2]==album && creator[3]==source);
        e.enterOriginalChildCoroutineResume(wrongCoroutine,source);
        check(e.exactOriginalChildCoroutineCreator(childItem)==null);
        e.exitOriginalChildCoroutineResume();
        check(e.exactOriginalChildCoroutineCreator(childItem)!=null);
        check(!e.onOriginalChildCoroutineDescriptor(childItem,new Object(),descriptor));
        Object otherSource=new Object(),otherItem=new Object();
        e.enterNativePlayerSourceSelection(wrapper);
        e.onOriginalMediaSourceConstructed(otherSource,otherItem);
        e.exitNativePlayerSourceSelection();
        check(e.exactOriginalChildCoroutineCreator(otherItem)==null);
        check(e.onOriginalChildCoroutineDescriptor(childItem,wrapper,descriptor));
        Object factory=new Object(),dataSource=new Object();
        e.onExoFactoryCreated(descriptor,factory);
        e.onExoSourceInstanceCreated(dataSource,factory);
        Object[] fresh=e.exactFreshCreatorOrBetaForDataSource(dataSource);
        check(fresh!=null && fresh[0]==wrapper && fresh[1]==track && fresh[2]==album);
        e.onOriginalChildCoroutineConstructed(coroutine,source,source); // invalidate even inside active scope
        check(e.exactOriginalChildCoroutineCreator(childItem)==null);
        e.exitOriginalChildCoroutineResume();
        check(e.exactOriginalChildCoroutineCreator(childItem)==null);
        e.enterOriginalChildCoroutineResume(coroutine,source);
        check(e.exactOriginalChildCoroutineCreator(childItem)==null);
        e.exitOriginalChildCoroutineResume();
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_COROUTINE_DESCRIPTOR_LINK","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_COROUTINE_SOURCE_SCOPE_MATCH","ONE");
        bucket(e.exportLines(),0,"ORIGINAL_CHILD_COROUTINE_SOURCE_SCOPE_REJECT","FEW");
    }

    static StageBAudioEvidence exactTcaFactorySource(Object track,Object album,
            Object wrapper,Object descriptor,Object factory,Object source) {
        StageBAudioEvidence e=new StageBAudioEvidence();
        e.onNativeTrackAlbumConstructed(track,album);
        e.onNativeTrackFlowEmission(track);
        e.enterNativeTcaCreatorOwner(new Object());
        e.enterNativeTcaCreatorTrackScope(track,1);
        e.onNativeTrackWrapperCreated(wrapper,NativeTrackIdBetaPolicy.RAMIL_AU);
        e.exitNativeTcaCreatorTrackScope();
        e.exitNativeTcaCreatorOwner();
        e.enterNativeMainSourceRequest(wrapper,null);
        e.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);
        e.exitNativeMainSourceRequest();
        e.onExoFactoryCreated(descriptor,factory);
        e.onExoSourceInstanceCreated(source,factory);
        return e;
    }

    // Deterministic reference-lifetime regression: inspect the actual retained
    // object, not GC timing or a relaxed first-open admission predicate.
    static Object descriptorPin(StageBAudioEvidence e) {
        try {
            java.lang.reflect.Field links=StageBAudioEvidence.class
                .getDeclaredField("nativeTrackSourceLinks");
            links.setAccessible(true);
            java.util.List<?> list=(java.util.List<?>)links.get(e);
            check(list.size()==1);
            Object link=list.get(0);
            java.lang.reflect.Field pin=link.getClass()
                .getDeclaredField("firstOpenDescriptorPin");
            pin.setAccessible(true);
            return pin.get(link);
        } catch(ReflectiveOperationException ex) {
            throw new AssertionError(ex);
        }
    }

    static void firstOpenDescriptorPinFixture() {
        Object track=new Object(),album=new Object(),wrapper=new Object();
        Object descriptor=new Object(),factory=new Object(),source=new Object();
        StageBAudioEvidence e=exactTcaFactorySource(
            track,album,wrapper,descriptor,factory,source);
        check(descriptorPin(e)==descriptor);
        check(e.exactFreshCreatorOrBetaAtFirstOpen(new Object())==null);
        check(descriptorPin(e)==descriptor);
        Object[] accepted=e.exactFreshCreatorOrBetaAtFirstOpen(source);
        check(accepted!=null && accepted[0]==wrapper && accepted[1]==track
            && accepted[2]==album);
        check(descriptorPin(e)==descriptor);
        e.onExoSourceInstanceOpenAttempt(source);
        check(descriptorPin(e)==null);
        check(e.exactFreshCreatorOrBetaAtFirstOpen(source)==null);

        Object d2=new Object(),f2=new Object(),s2=new Object(),sibling=new Object();
        StageBAudioEvidence other=exactTcaFactorySource(
            track,album,wrapper,d2,f2,s2);
        other.onExoSourceInstanceCreated(sibling,f2);
        other.onExoSourceInstanceClose(s2);
        check(descriptorPin(other)==null);
        check(other.exactFreshCreatorOrBetaAtFirstOpen(sibling)==null);

        Object d3=new Object(),f3=new Object(),s3=new Object();
        StageBAudioEvidence rebound=exactTcaFactorySource(
            track,album,wrapper,d3,f3,s3);
        Object replacementDescriptor=new Object();
        rebound.enterNativeMainSourceRequest(wrapper,null);
        rebound.onNativeExoDescriptorBuiltForCurrentWrapper(replacementDescriptor);
        rebound.exitNativeMainSourceRequest();
        check(descriptorPin(rebound)==null);
        check(rebound.exactFreshCreatorOrBetaAtFirstOpen(s3)==null);
        java.lang.ref.Reference.reachabilityFence(descriptor);
        java.lang.ref.Reference.reachabilityFence(d2);
        java.lang.ref.Reference.reachabilityFence(d3);
    }

    static void firstOpenReasonBucketsFixture() {
        Object track=new Object(),album=new Object(),wrapper=new Object();
        Object descriptor=new Object(),factory=new Object(),source=new Object();
        StageBAudioEvidence accepted=exactTcaFactorySource(
            track,album,wrapper,descriptor,factory,source);
        accepted.onExoFirstOpenHookEnter();
        Object[] creator=accepted.exactFreshCreatorOrBetaAtFirstOpen(source);
        check(creator!=null && creator[0]==wrapper && creator[1]==track
                && creator[2]==album);
        accepted.onExoFirstOpenSetterResult(true);
        accepted.onExoFirstOpenDeferredArmCalled();
        accepted.onExoFirstOpenDeferredArmResult(false);
        bucket(accepted.exportLines(),0,"FIRST_OPEN_HOOK_ENTERED","ONE");
        bucket(accepted.exportLines(),0,"FIRST_OPEN_CANDIDATE_ACCEPTED","ONE");
        bucket(accepted.exportLines(),0,"FIRST_OPEN_SETTER_MATCH","ONE");
        bucket(accepted.exportLines(),0,"FIRST_OPEN_DEFERRED_ARM_CALLED","ONE");
        bucket(accepted.exportLines(),0,"FIRST_OPEN_DEFERRED_ARM_REJECTED","ONE");
        String report=String.join("\\n",accepted.exportLines());
        check(!report.contains("144530503") && !report.contains("http"));

        StageBAudioEvidence noBirth=new StageBAudioEvidence();
        check(noBirth.exactFreshCreatorOrBetaAtFirstOpen(new Object())==null);
        bucket(noBirth.exportLines(),0,"FIRST_OPEN_BIRTH_NOT_FOUND","ONE");
        bucket(noBirth.exportLines(),0,"FIRST_OPEN_CANDIDATE_REJECTED","ONE");

        Object tt=new Object(),ta=new Object(),tw=new Object(),td=new Object(),tf=new Object();
        Object siblingOne=new Object(),siblingTwo=new Object();
        StageBAudioEvidence sibling=exactTcaFactorySource(
            tt,ta,tw,td,tf,siblingOne);
        sibling.onExoSourceInstanceCreated(siblingTwo,tf);
        sibling.onExoSourceInstanceOpenAttempt(siblingOne);
        check(sibling.exactFreshCreatorOrBetaAtFirstOpen(siblingTwo)==null);
        bucket(sibling.exportLines(),0,"FIRST_OPEN_SIBLING_TOUCHED","ONE");
    }

    public static void main(String[] argv) {
        originalChildCoroutineCaptureFixture();
        firstOpenDescriptorPinFixture();
        firstOpenReasonBucketsFixture();
        originalMediaItemSourceBridgeFixture();
        originalChildCallerContextFixture();
        beta9CrossThreadFixture();
        StageBAudioEvidence e = new StageBAudioEvidence();
        String[] initial = e.exportLines();
        check(initial.length == 142);
        for (int i=0;i<104;i++) check(initial[i].contains(";error=NONE;"));
        check(contains(initial,"CELIKOM_REPLACEMENT;error=NOT_CONNECTED"));

        Object track=new Object(), wrapper=new Object(), descriptor=new Object();
        Object factory=new Object(), source=new Object();
        Object unselectedTrack=new Object(), unselectedWrapper=new Object();
        Object wrongDescriptor=new Object(), wrongFactory=new Object(), wrongSource=new Object();

        e.onNativeTrackFlowEmission(track);
        e.enterNativeTrackSourceRequest(track,null);
        e.onNativeTrackWrapperCreated(wrapper);
        e.exitNativeTrackSourceRequest();
        e.enterNativeTrackSourceRequest(unselectedTrack,null);
        e.onNativeTrackWrapperCreated(unselectedWrapper);
        e.exitNativeTrackSourceRequest();
        e.enterNativeMainSourceRequest(wrapper,null);
        e.onExoDescriptorBuilt(descriptor);
        e.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);
        e.exitNativeMainSourceRequest();
        e.enterNativeMainSourceRequest(unselectedWrapper,null);
        e.onExoDescriptorBuilt(wrongDescriptor);
        e.onNativeExoDescriptorBuiltForCurrentWrapper(wrongDescriptor);
        e.exitNativeMainSourceRequest();
        e.onExoFactoryCreated(descriptor,factory);
        e.onExoFactoryCreated(wrongDescriptor,wrongFactory);
        e.onExoSourceInstanceCreated(source,factory);
        e.onExoSourceInstanceCreated(wrongSource,wrongFactory);
        e.onExoSourceInstanceOpen(source);
        e.onExoSourceInstanceRead(source,512);
        e.onExoSourceInstanceOpen(wrongSource);
        e.onExoSourceInstanceRead(wrongSource,1024);

        String[] links=e.exportLines();
        String[] names={"NATIVE_TRACK_FLOW_EMIT","NATIVE_TRACK_SOURCE_REQUEST",
            "FLOW_TRACK_SAME_OBJECT","TRACK_WRAPPER_LINK","WRAPPER_MAIN_SOURCE",
            "WRAPPER_DESCRIPTOR_LINK","TRACK_DESCRIPTOR_FACTORY_LINK",
            "TRACK_FACTORY_SOURCE_LINK","TRACK_SOURCE_OPEN_LINK","TRACK_SOURCE_READ_LINK"};
        for(int i=0;i<names.length;i++) bucket(links,21+i,names[i],i==1?"FEW":"ONE");
        bucket(links,31,"NATIVE_TRACK_WRAPPER_CONSTRUCTED","FEW");
        bucket(links,32,"NATIVE_MAIN_SOURCE_ENTER","FEW");
        bucket(links,40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","ONE");
        check(contains(links,"CELIKOM_REPLACEMENT;error=NOT_CONNECTED"));

        // The exact Album constructor argument is carried only by weak object
        // identity through the Track Flow → wrapper → descriptor → source.
        // No Track/Album fields, IDs, titles or edition values are read.
        Object at=new Object(), aa=new Object(), aw=new Object(), ad=new Object();
        Object af=new Object(), as=new Object();
        StageBAudioEvidence albumChain=exactAlbumLinked(at,aa,aw,ad,af,as);
        albumChain.onExoSourceInstanceOpen(as);
        albumChain.onExoSourceInstanceRead(as,64);
        String[] albumRows=albumChain.exportLines();
        bucket(albumRows,43,"TRACK_ALBUM_CONSTRUCTOR_LINK","ONE");
        bucket(albumRows,44,"FLOW_TRACK_ALBUM_LINK","ONE");
        bucket(albumRows,45,"TRACK_WRAPPER_ALBUM_LINK","ONE");
        bucket(albumRows,46,"TRACK_DESCRIPTOR_ALBUM_LINK","ONE");
        bucket(albumRows,47,"TRACK_FACTORY_ALBUM_LINK","ONE");
        bucket(albumRows,48,"TRACK_SOURCE_ALBUM_LINK","ONE");
        bucket(albumRows,49,"TRACK_SOURCE_ALBUM_OPEN_LINK","ONE");
        bucket(albumRows,50,"TRACK_SOURCE_ALBUM_READ_LINK","ONE");
        bucket(albumRows,51,"TRACK_ALBUM_IDENTITY_CONFLICT","NONE");
        StageBAudioEvidence noAlbum=exactLinked(new Object(),new Object(),
            new Object(),new Object(),new Object());
        bucket(noAlbum.exportLines(),43,"TRACK_ALBUM_CONSTRUCTOR_LINK","NONE");
        bucket(noAlbum.exportLines(),44,"FLOW_TRACK_ALBUM_LINK","NONE");
        Object ct=new Object(), ca1=new Object(), ca2=new Object();
        StageBAudioEvidence albumConflict=new StageBAudioEvidence();
        albumConflict.onNativeTrackAlbumConstructed(ct,ca1);
        albumConflict.onNativeTrackAlbumConstructed(ct,ca2);
        albumConflict.onNativeTrackFlowEmission(ct);
        bucket(albumConflict.exportLines(),43,"TRACK_ALBUM_CONSTRUCTOR_LINK","ONE");
        bucket(albumConflict.exportLines(),44,"FLOW_TRACK_ALBUM_LINK","NONE");
        bucket(albumConflict.exportLines(),51,"TRACK_ALBUM_IDENTITY_CONFLICT","ONE");
        Object pt=new Object(),pa=new Object(),pw=new Object(),pd=new Object();
        Object pf=new Object(),ps=new Object();
        StageBAudioEvidence albumReadGate=exactAlbumLinked(pt,pa,pw,pd,pf,ps);
        albumReadGate.onExoSourceInstanceRead(ps,32);
        bucket(albumReadGate.exportLines(),50,"TRACK_SOURCE_ALBUM_READ_LINK","NONE");
        albumReadGate.onExoSourceInstanceOpen(ps);
        albumReadGate.onExoSourceInstanceRead(ps,32);
        bucket(albumReadGate.exportLines(),50,"TRACK_SOURCE_ALBUM_READ_LINK","ONE");
        albumReadGate.onExoSourceInstanceClose(ps);
        albumReadGate.onExoSourceInstanceRead(ps,32);
        bucket(albumReadGate.exportLines(),50,"TRACK_SOURCE_ALBUM_READ_LINK","ONE");
        albumReadGate.onExoSourceInstanceOpen(ps);
        albumReadGate.onExoSourceInstanceRead(ps,32);
        bucket(albumReadGate.exportLines(),50,"TRACK_SOURCE_ALBUM_READ_LINK","FEW");

        // A nested missing argument/collected weak ref must never borrow its
        // outer track or wrapper. Scope accounting survives null arguments.
        StageBAudioEvidence nested=new StageBAudioEvidence();
        Object nt=new Object(), nw=new Object(), nd=new Object();
        Object nf=new Object(), ns=new Object();
        nested.onNativeTrackFlowEmission(nt);
        nested.enterNativeTrackSourceRequest(nt,null);
        nested.enterNativeTrackSourceRequest(null,null);
        nested.onNativeTrackWrapperCreated(new Object());
        nested.exitNativeTrackSourceRequest();
        nested.onNativeTrackWrapperCreated(nw);
        nested.exitNativeTrackSourceRequest();
        bucket(nested.exportLines(),24,"TRACK_WRAPPER_LINK","ONE");
        nested.enterNativeMainSourceRequest(nw,null);
        nested.enterNativeMainSourceRequest(null,null);
        nested.onNativeExoDescriptorBuiltForCurrentWrapper(new Object());
        nested.exitNativeMainSourceRequest();
        nested.onNativeExoDescriptorBuiltForCurrentWrapper(nd);
        nested.exitNativeMainSourceRequest();
        nested.onExoFactoryCreated(nd,nf);
        nested.onExoSourceInstanceCreated(ns,nf);
        nested.onExoSourceInstanceOpen(ns);
        nested.onExoSourceInstanceRead(ns,1);
        bucket(nested.exportLines(),26,"WRAPPER_DESCRIPTOR_LINK","ONE");
        bucket(nested.exportLines(),30,"TRACK_SOURCE_READ_LINK","ONE");

        // A sibling wrapper for the same Track keeps the first wrapper's
        // descriptor/factory/source lineage independent.
        StageBAudioEvidence reset=new StageBAudioEvidence();
        Object rt=new Object(), rw1=new Object(), rw2=new Object();
        Object rd1=new Object(), rd2=new Object(), rf1=new Object(), rf2=new Object();
        Object rs1=new Object(), rs2=new Object();
        reset.onNativeTrackFlowEmission(rt);
        reset.enterNativeTrackSourceRequest(rt,null);
        reset.onNativeTrackWrapperCreated(rw1);
        reset.exitNativeTrackSourceRequest();
        reset.enterNativeMainSourceRequest(rw1,null);
        reset.onNativeExoDescriptorBuiltForCurrentWrapper(rd1);
        reset.exitNativeMainSourceRequest();
        reset.onExoFactoryCreated(rd1,rf1);
        reset.onExoSourceInstanceCreated(rs1,rf1);
        reset.onExoSourceInstanceOpen(rs1);
        reset.onExoSourceInstanceRead(rs1,1);
        reset.enterNativeTrackSourceRequest(rt,null);
        reset.onNativeTrackWrapperCreated(rw2);
        reset.exitNativeTrackSourceRequest();
        reset.onExoSourceInstanceOpen(rs1);
        reset.onExoSourceInstanceRead(rs1,1);
        reset.onExoFactoryCreated(rd1,new Object());
        bucket(reset.exportLines(),29,"TRACK_SOURCE_OPEN_LINK","FEW");
        bucket(reset.exportLines(),30,"TRACK_SOURCE_READ_LINK","FEW");
        bucket(reset.exportLines(),27,"TRACK_DESCRIPTOR_FACTORY_LINK","FEW");
        reset.enterNativeMainSourceRequest(rw2,null);
        reset.onNativeExoDescriptorBuiltForCurrentWrapper(rd2);
        reset.exitNativeMainSourceRequest();
        reset.onExoFactoryCreated(rd2,rf2);
        reset.onExoSourceInstanceCreated(rs2,rf2);
        reset.onExoSourceInstanceOpen(rs2);
        reset.onExoSourceInstanceRead(rs2,1);
        bucket(reset.exportLines(),29,"TRACK_SOURCE_OPEN_LINK","FEW");
        bucket(reset.exportLines(),30,"TRACK_SOURCE_READ_LINK","FEW");

        // Shared descriptor across two different tracks is ambiguous: fail closed.
        StageBAudioEvidence collision=new StageBAudioEvidence();
        Object ct1=new Object(),ct2=new Object(),cw1=new Object(),cw2=new Object();
        Object cd=new Object(),cf=new Object(),cs=new Object();
        collision.onNativeTrackFlowEmission(ct1);
        collision.onNativeTrackFlowEmission(ct2);
        collision.enterNativeTrackSourceRequest(ct1,null);
        collision.onNativeTrackWrapperCreated(cw1);
        collision.exitNativeTrackSourceRequest();
        collision.enterNativeTrackSourceRequest(ct2,null);
        collision.onNativeTrackWrapperCreated(cw2);
        collision.exitNativeTrackSourceRequest();
        collision.enterNativeMainSourceRequest(cw1,null);
        collision.onNativeExoDescriptorBuiltForCurrentWrapper(cd);
        collision.exitNativeMainSourceRequest();
        collision.enterNativeMainSourceRequest(cw2,null);
        collision.onNativeExoDescriptorBuiltForCurrentWrapper(cd);
        collision.exitNativeMainSourceRequest();
        collision.onExoFactoryCreated(cd,cf);
        collision.onExoSourceInstanceCreated(cs,cf);
        collision.onExoSourceInstanceOpen(cs);
        collision.onExoSourceInstanceRead(cs,1);
        bucket(collision.exportLines(),27,"TRACK_DESCRIPTOR_FACTORY_LINK","NONE");
        bucket(collision.exportLines(),30,"TRACK_SOURCE_READ_LINK","NONE");

        // The pinned Kotlin Fp0 continuation is created before suspension.
        // A second Gp0.new invocation on resume may have a null track arg.
        StageBAudioEvidence resumed=new StageBAudioEvidence();
        Object rt0=new Object(), continuation0=new Object(), wrapped0=new Object();
        resumed.onNativeTrackFlowEmission(rt0);
        resumed.enterNativeTrackSourceRequest(rt0,null);
        resumed.onNativeTrackContinuationConstructed(continuation0);
        resumed.exitNativeTrackSourceRequest(); // coroutine suspended
        resumed.enterNativeTrackSourceRequest(null,new Object());
        resumed.onNativeTrackWrapperCreated(new Object()); // unknown resume FAIL
        resumed.exitNativeTrackSourceRequest();
        resumed.enterNativeTrackSourceRequest(null,continuation0);
        resumed.onNativeTrackWrapperCreated(wrapped0);
        resumed.exitNativeTrackSourceRequest();
        bucket(resumed.exportLines(),33,"NATIVE_TRACK_CONTINUATION_CONSTRUCTED","ONE");
        bucket(resumed.exportLines(),34,"TRACK_CONTINUATION_RECOVERED","ONE");
        bucket(resumed.exportLines(),23,"FLOW_TRACK_SAME_OBJECT","ONE");
        bucket(resumed.exportLines(),35,"TRACK_CONTINUATION_CONFLICT","NONE");
        bucket(resumed.exportLines(),24,"TRACK_WRAPPER_LINK","ONE");
        // Explicit different selected Track with the same Fp0 must revoke
        // continuation identity permanently, including subsequent null args.
        Object rt1=new Object();
        resumed.onNativeTrackFlowEmission(rt1);
        resumed.enterNativeTrackSourceRequest(rt1,continuation0);
        resumed.onNativeTrackWrapperCreated(new Object());
        resumed.exitNativeTrackSourceRequest();
        resumed.enterNativeTrackSourceRequest(null,continuation0);
        resumed.onNativeTrackWrapperCreated(new Object());
        resumed.exitNativeTrackSourceRequest();
        bucket(resumed.exportLines(),35,"TRACK_CONTINUATION_CONFLICT","ONE");
        bucket(resumed.exportLines(),24,"TRACK_WRAPPER_LINK","ONE");
        // Reentrancy: a null inner resumed continuation must mask outer Track.
        StageBAudioEvidence masked=new StageBAudioEvidence();
        Object mt=new Object();
        masked.onNativeTrackFlowEmission(mt);
        masked.enterNativeTrackSourceRequest(mt,null);
        masked.enterNativeTrackSourceRequest(null,new Object());
        masked.onNativeTrackWrapperCreated(new Object());
        masked.exitNativeTrackSourceRequest();
        masked.onNativeTrackWrapperCreated(new Object());
        masked.exitNativeTrackSourceRequest();
        bucket(masked.exportLines(),24,"TRACK_WRAPPER_LINK","ONE");

        // The publisher FileInfo proxy may be invoked only after Gp0's Fp0
        // coroutine resumes. Restore the exact Track through that same object.
        StageBAudioEvidence issuerResume=new StageBAudioEvidence();
        Object issuerTrack=new Object(), issuerContinuation=new Object();
        Object issuerWrapper=new Object();
        issuerResume.onNativeTrackFlowEmission(issuerTrack);
        issuerResume.enterNativeTrackSourceRequest(issuerTrack,null);
        issuerResume.onNativeTrackContinuationConstructed(issuerContinuation);
        issuerResume.exitNativeTrackSourceRequest();
        issuerResume.enterNativeTrackSourceRequest(null,issuerContinuation);
        issuerResume.onPublisherAnnotatedTrackId(NativeTrackIdBetaPolicy.RAMIL_AU);
        issuerResume.exitNativeTrackSourceRequest();
        issuerResume.enterNativeTcaCreatorOwner(new Object());
        issuerResume.enterNativeTcaCreatorTrackScope(issuerTrack,1);
        issuerResume.onNativeTrackWrapperCreated(
            issuerWrapper,NativeTrackIdBetaPolicy.RAMIL_AU);
        issuerResume.exitNativeTcaCreatorTrackScope();
        issuerResume.exitNativeTcaCreatorOwner();
        check(issuerResume.exactBetaCreatorWithoutAlbum(issuerWrapper)!=null);

        // RAa resumes the pinned main source builder with null wrapper,
        // but with the identical RAa instance as final continuation argument.
        StageBAudioEvidence mainResume=new StageBAudioEvidence();
        Object mtrack=new Object(), mwrapper=new Object(), mra=new Object();
        Object mdesc=new Object(), mfactory=new Object(), msource=new Object();
        mainResume.onNativeTrackFlowEmission(mtrack);
        mainResume.enterNativeTrackSourceRequest(mtrack,null);
        mainResume.onNativeTrackWrapperCreated(mwrapper);
        mainResume.exitNativeTrackSourceRequest();
        mainResume.enterNativeMainSourceRequest(mwrapper,null);
        mainResume.onNativeMainContinuationConstructed(mra);
        mainResume.exitNativeMainSourceRequest(); // original source coroutine suspended
        mainResume.enterNativeMainSourceRequest(null,new Object());
        mainResume.onNativeExoDescriptorBuiltForCurrentWrapper(new Object());
        mainResume.exitNativeMainSourceRequest(); // foreign resume, not linked
        mainResume.enterNativeMainSourceRequest(null,mra);
        mainResume.onNativeExoDescriptorBuiltForCurrentWrapper(mdesc);
        mainResume.exitNativeMainSourceRequest();
        mainResume.onExoFactoryCreated(mdesc,mfactory);
        mainResume.onExoSourceInstanceCreated(msource,mfactory);
        mainResume.onExoSourceInstanceOpen(msource);
        mainResume.onExoSourceInstanceRead(msource,8);
        bucket(mainResume.exportLines(),36,"NATIVE_MAIN_CONTINUATION_CONSTRUCTED","ONE");
        bucket(mainResume.exportLines(),37,"MAIN_CONTINUATION_RECOVERED","ONE");
        bucket(mainResume.exportLines(),38,"MAIN_CONTINUATION_CONFLICT","NONE");
        bucket(mainResume.exportLines(),25,"WRAPPER_MAIN_SOURCE","ONE");
        bucket(mainResume.exportLines(),26,"WRAPPER_DESCRIPTOR_LINK","ONE");
        bucket(mainResume.exportLines(),30,"TRACK_SOURCE_READ_LINK","ONE");
        Object mtrackOther=new Object(), mwrapperOther=new Object();
        mainResume.onNativeTrackFlowEmission(mtrackOther);
        mainResume.enterNativeTrackSourceRequest(mtrackOther,null);
        mainResume.onNativeTrackWrapperCreated(mwrapperOther);
        mainResume.exitNativeTrackSourceRequest();
        mainResume.enterNativeMainSourceRequest(mwrapperOther,mra);
        mainResume.onNativeExoDescriptorBuiltForCurrentWrapper(new Object());
        mainResume.exitNativeMainSourceRequest();
        mainResume.enterNativeMainSourceRequest(null,mra);
        mainResume.onNativeExoDescriptorBuiltForCurrentWrapper(new Object());
        mainResume.exitNativeMainSourceRequest();
        bucket(mainResume.exportLines(),38,"MAIN_CONTINUATION_CONFLICT","ONE");
        bucket(mainResume.exportLines(),26,"WRAPPER_DESCRIPTOR_LINK","ONE");

        // A positive read BEFORE a linked source's successful open() must
        // never be mistaken for complete Track -> descriptor -> source proof.
        StageBAudioEvidence readGate=new StageBAudioEvidence();
        Object gt=new Object(), gw=new Object(), gd=new Object();
        Object gf=new Object(), gs=new Object();
        readGate.onNativeTrackFlowEmission(gt);
        readGate.enterNativeTrackSourceRequest(gt,null);
        readGate.onNativeTrackWrapperCreated(gw);
        readGate.exitNativeTrackSourceRequest();
        readGate.enterNativeMainSourceRequest(gw,null);
        readGate.onNativeExoDescriptorBuiltForCurrentWrapper(gd);
        readGate.exitNativeMainSourceRequest();
        readGate.onExoFactoryCreated(gd,gf);
        readGate.onExoSourceInstanceCreated(gs,gf);
        readGate.onExoSourceInstanceRead(gs,512); // NEVER proof before open
        bucket(readGate.exportLines(),30,"TRACK_SOURCE_READ_LINK","NONE");
        bucket(readGate.exportLines(),39,"TRACK_SOURCE_UNOPENED_READ","ONE");
        bucket(readGate.exportLines(),40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","NONE");
        readGate.onExoSourceInstanceOpen(gs);
        readGate.onExoSourceInstanceRead(gs,512);
        readGate.onExoSourceInstanceRead(gs,512);
        bucket(readGate.exportLines(),30,"TRACK_SOURCE_READ_LINK","FEW");
        bucket(readGate.exportLines(),40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","ONE");
        // Rebinding a new descriptor/factory to the SAME source object
        // requires a fresh open before its positive read becomes evidence.
        Object gd2=new Object(), gf2=new Object();
        readGate.enterNativeMainSourceRequest(gw,null);
        readGate.onNativeExoDescriptorBuiltForCurrentWrapper(gd2);
        readGate.exitNativeMainSourceRequest();
        readGate.onExoFactoryCreated(gd2,gf2);
        readGate.onExoSourceInstanceCreated(gs,gf2);
        readGate.onExoSourceInstanceRead(gs,512);
        bucket(readGate.exportLines(),40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","ONE");
        bucket(readGate.exportLines(),39,"TRACK_SOURCE_UNOPENED_READ","FEW");
        readGate.onExoSourceInstanceOpen(gs);
        readGate.onExoSourceInstanceRead(gs,512);
        // Rebinding did NOT create a new source instance: distinct == stays 1.
        bucket(readGate.exportLines(),40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","ONE");
        // A failed reopen must not inherit the previous positive open proof.
        readGate.onExoSourceInstanceOpenAttempt(gs);
        readGate.onExoSourceInstanceRead(gs,2);
        bucket(readGate.exportLines(),40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","ONE");
        bucket(readGate.exportLines(),39,"TRACK_SOURCE_UNOPENED_READ","FEW");
        readGate.onExoSourceInstanceOpen(gs);
        readGate.onExoSourceInstanceRead(gs,2);
        bucket(readGate.exportLines(),40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","ONE");
        readGate.onExoSourceInstanceClose(gs);
        readGate.onExoSourceInstanceRead(gs,9);
        bucket(readGate.exportLines(),41,"TRACK_SOURCE_CLOSE_LINK","ONE");
        bucket(readGate.exportLines(),40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","ONE");
        readGate.onExoSourceInstanceOpenAttempt(gs);
        readGate.onExoSourceInstanceOpen(gs);
        readGate.onExoSourceInstanceRead(gs,9);
        // Even a later, overlapping failed retry revokes the earlier success.
        readGate.onExoSourceInstanceOpenFailure(gs);
        readGate.onExoSourceInstanceRead(gs,7);
        bucket(readGate.exportLines(),40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","ONE");
        readGate.onExoSourceInstanceOpenAttempt(gs);
        readGate.onExoSourceInstanceOpen(gs);
        readGate.onExoSourceInstanceRead(gs,7);
        // A genuinely different source instance counts as a second one.
        Object gd3=new Object(),gf3=new Object(),gs3=new Object();
        readGate.enterNativeMainSourceRequest(gw,null);
        readGate.onNativeExoDescriptorBuiltForCurrentWrapper(gd3);
        readGate.exitNativeMainSourceRequest();
        readGate.onExoFactoryCreated(gd3,gf3);
        readGate.onExoSourceInstanceCreated(gs3,gf3);
        readGate.onExoSourceInstanceOpen(gs3);
        readGate.onExoSourceInstanceRead(gs3,2);
        bucket(readGate.exportLines(),40,"TRACK_SOURCE_DISTINCT_POSITIVE_READ","FEW");
        // Ensure close() and late open failure MUST revoke READ_LINK, not
        // just change an unrelated distinct-read counter.
        Object cTrack=new Object(),cWrapper=new Object(),cDescriptor=new Object();
        Object cFactory=new Object(),cSource=new Object();
        StageBAudioEvidence afterClose=exactLinked(
            cTrack,cWrapper,cDescriptor,cFactory,cSource);
        afterClose.onExoSourceInstanceOpen(cSource);
        afterClose.onExoSourceInstanceClose(cSource);
        afterClose.onExoSourceInstanceRead(cSource,8);
        bucket(afterClose.exportLines(),30,"TRACK_SOURCE_READ_LINK","NONE");
        bucket(afterClose.exportLines(),39,"TRACK_SOURCE_UNOPENED_READ","ONE");
        bucket(afterClose.exportLines(),41,"TRACK_SOURCE_CLOSE_LINK","ONE");
        afterClose.onExoSourceInstanceOpen(cSource);
        afterClose.onExoSourceInstanceRead(cSource,8);
        bucket(afterClose.exportLines(),30,"TRACK_SOURCE_READ_LINK","ONE");

        Object fTrack=new Object(),fWrapper=new Object(),fDescriptor=new Object();
        Object fFactory=new Object(),fSource=new Object();
        StageBAudioEvidence failedOpen=exactLinked(
            fTrack,fWrapper,fDescriptor,fFactory,fSource);
        failedOpen.onExoSourceInstanceOpen(fSource);
        failedOpen.onExoSourceInstanceOpenFailure(fSource);
        failedOpen.onExoSourceInstanceRead(fSource,8);
        bucket(failedOpen.exportLines(),30,"TRACK_SOURCE_READ_LINK","NONE");
        bucket(failedOpen.exportLines(),39,"TRACK_SOURCE_UNOPENED_READ","ONE");
        failedOpen.onExoSourceInstanceOpen(fSource);
        failedOpen.onExoSourceInstanceRead(fSource,8);
        bucket(failedOpen.exportLines(),30,"TRACK_SOURCE_READ_LINK","ONE");

        Object bTrack=new Object(),bWrapper=new Object(),bDescriptor=new Object();
        Object bFactory=new Object(),bSource=new Object();
        StageBAudioEvidence rebound=exactLinked(
            bTrack,bWrapper,bDescriptor,bFactory,bSource);
        rebound.onExoSourceInstanceOpen(bSource);
        Object newDesc=new Object(),newFactory=new Object();
        rebound.enterNativeMainSourceRequest(bWrapper,null);
        rebound.onNativeExoDescriptorBuiltForCurrentWrapper(newDesc);
        rebound.exitNativeMainSourceRequest();
        rebound.onExoFactoryCreated(newDesc,newFactory);
        rebound.onExoSourceInstanceCreated(bSource,newFactory);
        rebound.onExoSourceInstanceRead(bSource,8);
        bucket(rebound.exportLines(),30,"TRACK_SOURCE_READ_LINK","NONE");
        bucket(rebound.exportLines(),39,"TRACK_SOURCE_UNOPENED_READ","ONE");
        rebound.onExoSourceInstanceOpen(bSource);
        rebound.onExoSourceInstanceRead(bSource,8);
        bucket(rebound.exportLines(),30,"TRACK_SOURCE_READ_LINK","ONE");

        StageBAudioEvidence limited=new StageBAudioEvidence();
        Object lt=new Object(),lw=new Object(),ld=new Object(),lf=new Object();
        limited.onNativeTrackFlowEmission(lt);
        limited.enterNativeTrackSourceRequest(lt,null);
        limited.onNativeTrackWrapperCreated(lw);
        limited.exitNativeTrackSourceRequest();
        limited.enterNativeMainSourceRequest(lw,null);
        limited.onNativeExoDescriptorBuiltForCurrentWrapper(ld);
        limited.exitNativeMainSourceRequest();
        limited.onExoFactoryCreated(ld,lf);
        limited.onExoSourceInstanceCreated(new Object(),lf);
        Object unknownSource=new Object();
        for(int i=0;i<300;i++) limited.onExoSourceInstanceRead(unknownSource,5);
        bucket(limited.exportLines(),42,"TRACK_SOURCE_READ_SCAN_EXHAUSTED","ONE");
        bucket(limited.exportLines(),30,"TRACK_SOURCE_READ_LINK","NONE");

        Object different=new Object();
        e.onExoSourceInstanceCreated(different);
        e.onExoSourceInstanceOpen(different);
        e.onExoSourceInstanceRead(different,1024);
        e.onExoSourceInstanceOpen(source);
        e.onExoSourceInstanceRead(source,512);
        e.onExoDescriptorBuilt(descriptor);
        e.onExoFactoryCreated(different);
        e.onExoFactoryCreated(descriptor);
        e.onExoOpen();
        e.onExoReadResult(8192);
        e.onExoReadResult(0);
        e.onExoReadResult(-1);
        e.onExoReadResult(Integer.MIN_VALUE);
        e.onExoFailure();
        e.onFileInfoResult();
        e.onDirectDownloadInfoResult();
        e.onReader(0,true);
        e.onReader(0,false);
        e.onExtractorSource(0);
        e.onReadReturn(512);
        e.onReadReturn(-1);
        e.onReadReturn(0);
        e.onReadException();

        String[] rows=e.exportLines();
        String[] categories={"FILEINFO_DTO","DOWNLOADINFO_DTO","READER_0","READER_1",
            "EXTRACTOR_0","EXTRACTOR_1","EXTRACTOR_OTHER","SAME_SOURCE_OBJECT",
            "POSITIVE_READS","SOURCE_END","READ_EXCEPTIONS"};
        for(int i=0;i<11;i++){
            String value=i==2?"FEW":
                (i==0||i==1||i==4||i==7||i==8||i==9||i==10?"ONE":"NONE");
            bucket(rows,i,categories[i],value);
            check(!rows[i].contains("512") && !rows[i].contains("http"));
        }
        check(rows[11].contains(";error=FEW;"));
        check(rows[12].contains(";error=ONE;"));
        check(rows[13].contains(";error=ONE;"));
        check(rows[14].contains(";error=ONE;"));
        check(rows[15].contains(";error=ONE;"));
        check(rows[16].contains(";error=FEW;"));
        check(rows[17].contains(";error=FEW;"));
        check(rows[18].contains(";error=FEW;"));
        check(rows[19].contains(";error=FEW;"));
        check(rows[20].contains(";error=FEW;"));
        for(int i=0;i<10;i++) e.onReader(1,false);
        check(e.exportLines()[3].contains(";error=MANY;"));
        for(int i=0;i<50;i++) e.onExoReadResult(1);
        check(e.exportLines()[13].contains(";error=MANY;"));
        // New original Track/Album identity handle is exact for an already
        // linked wrapper, but never a guessed ID or a later player selection.
        Object[] linkedPair=albumChain.exactOriginalTrackAlbumForWrapper(aw);
        check(linkedPair!=null && linkedPair.length==2
              && linkedPair[0]==at && linkedPair[1]==aa);
        check(albumChain.exactOriginalTrackAlbumForWrapper(new Object())==null);
        albumChain.onNativeTrackAlbumConstructed(at,new Object());
        check(albumChain.exactOriginalTrackAlbumForWrapper(aw)==null);

        // NAV40 real-phone late-Flow case: creator owns this exact Track at
        // wrapper birth, and the SAME original Track enters Flow afterwards.
        StageBAudioEvidence lateHandle=new StageBAudioEvidence();
        Object ltrack=new Object(),lalbum=new Object(),lwrapper=new Object();
        lateHandle.onNativeTrackAlbumConstructed(ltrack,lalbum);
        lateHandle.enterNativeTcaCreatorOwner(new Object());
        lateHandle.enterNativeTcaCreatorTrackScope(ltrack,1);
        lateHandle.onNativeTrackWrapperCreated(lwrapper);
        lateHandle.exitNativeTcaCreatorTrackScope();
        lateHandle.exitNativeTcaCreatorOwner();
        check(lateHandle.exactOriginalTrackAlbumForWrapper(lwrapper)==null);
        lateHandle.onNativeTrackFlowEmission(new Object());
        check(lateHandle.exactOriginalTrackAlbumForWrapper(lwrapper)==null);
        lateHandle.onNativeTrackFlowEmission(ltrack);
        check(lateHandle.classifyNativeTrackAlbumForWrapper(lwrapper)==16);
        Object[] latePair=lateHandle.exactOriginalTrackAlbumForWrapper(lwrapper);
        check(latePair!=null && latePair[0]==ltrack && latePair[1]==lalbum);
        // Same creator callback but a conflicting Album must reject the
        // whole handle even if previously classified as SAME.
        lateHandle.onNativeTrackAlbumConstructed(ltrack,new Object());
        check(lateHandle.exactOriginalTrackAlbumForWrapper(lwrapper)==null);
        StageBAudioEvidence reusedBirth=new StageBAudioEvidence();
        Object rbTrack=new Object(),rbAlbum=new Object(),rbWrapper=new Object();
        reusedBirth.onNativeTrackAlbumConstructed(rbTrack,rbAlbum);
        reusedBirth.enterNativeTcaCreatorOwner(new Object());
        reusedBirth.enterNativeTcaCreatorTrackScope(rbTrack,1);
        reusedBirth.onNativeTrackWrapperCreated(rbWrapper);
        reusedBirth.onNativeTrackWrapperCreated(rbWrapper);
        reusedBirth.exitNativeTcaCreatorTrackScope();
        reusedBirth.exitNativeTcaCreatorOwner();
        reusedBirth.onNativeTrackFlowEmission(rbTrack);
        Object[] reusedPair=reusedBirth.exactOriginalTrackAlbumForWrapper(rbWrapper);
        check(reusedPair!=null && reusedPair[0]==rbTrack && reusedPair[1]==rbAlbum);

        System.out.println("PASS Stage B exact Track-to-Exo identity chain; mismatches fail closed");
    }
}
"""


class StageBAudioEvidenceTest(unittest.TestCase):
    def test_actual_java_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            test = pathlib.Path(tmp) / "StageBAudioEvidenceTest.java"
            test.write_text(HARNESS, encoding="utf-8")
            compiled = subprocess.run(["javac", "-d", tmp, str(GRANT_CONTRACT),
                                       str(BETA_POLICY), str(EVIDENCE), str(test)],
                                      check=False, capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0,
                             compiled.stdout + "\\n" + compiled.stderr)
            done = subprocess.run(["java", "-cp", tmp,
                                   "pro.celikom.a1exitwitness.StageBAudioEvidenceTest"],
                                  check=False, capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stdout + "\\n" + done.stderr)
            self.assertIn("PASS Stage B", done.stdout)

    def test_hook_uses_actual_reader_and_export_but_never_replaces_source(self):
        code = HOOK.read_text(encoding="utf-8")
        self.assertIn("STAGE_B_AUDIO.onReader(privateReaderIndex, sameSource)", code)
        self.assertIn("STAGE_B_AUDIO.onExtractorSource(", code)
        self.assertIn("STAGE_B_AUDIO.onReadReturn(", code)
        self.assertIn("STAGE_B_AUDIO.onReadException()", code)
        self.assertIn("installExactNativeSourceDtoWitness(loader)", code)
        self.assertIn("STAGE_B_AUDIO.onFileInfoResult()", code)
        self.assertIn("STAGE_B_AUDIO.onDirectDownloadInfoResult()", code)
        self.assertIn("installExactNativeExoSourceWitness(loader)", code)
        self.assertIn("STAGE_B_AUDIO.onExoFactoryCreated(chain.getArg(1),result)", code)
        self.assertIn("STAGE_B_AUDIO.onExoDescriptorBuilt(result)", code)
        self.assertIn("STAGE_B_AUDIO.onNativeExoDescriptorBuiltForCurrentWrapper(result)", code)
        self.assertIn("STAGE_B_AUDIO.onNativeTrackFlowEmission(chain.getArg(0))", code)
        self.assertIn("STAGE_B_AUDIO.enterNativeTrackSourceRequest(", code)
        self.assertIn("selectedTrack,chain.getArg(2)", code)
        self.assertIn("STAGE_B_AUDIO.onNativeTrackContinuationConstructed(", code)
        self.assertIn('Class.forName("Fp0",false,loader)', code)
        self.assertIn('getDeclaredMethod("invokeSuspend",Object.class)', code)
        self.assertIn("STAGE_B_AUDIO.enterNativeTrackSourceRequest(null,current)", code)
        self.assertIn("STAGE_B_AUDIO.enterNativeMainSourceRequest(null,current)", code)
        self.assertIn('emit("AUDIO_NATIVE_TRACK_RESUME_HOOK"', code)
        self.assertIn('emit("AUDIO_NATIVE_MAIN_RESUME_HOOK"', code)
        self.assertIn("installPublisherTrackIdProxyWitness(earlyLoader)", code)
        self.assertIn("autoStartOwnerIfSession(activity)", code)
        self.assertIn("attachDiagnosticExportButton(activity)", code)
        self.assertIn("private void attachDiagnosticExportButton(Activity activity)", code)
        self.assertIn("private void updateDiagnosticButtonStatus(Activity activity,String status)", code)
        self.assertIn('button.setOnClickListener(view->exportDiagnosticReport(activity))', code)
        self.assertIn('emit("BETA_OWNER_AUTO_START","CELIKOM_SESSION","START_REQUESTED")', code)
        self.assertIn("ownerAutoStartRetryAfterMs", code)
        self.assertNotIn("attachSettingsEntry(activity)", code)
        self.assertNotIn("A1_SETTINGS_ENTRY_TAG", code)
        self.assertNotIn("private static boolean isSettingsActivity(Activity activity)", code)
        self.assertNotIn("attachOwnerControlButton(activity,root)", code)
        self.assertNotIn("OWNER_BUTTON_TAG", code)
        self.assertNotIn("CELIKOM BETA:", code)
        self.assertNotIn("capturePreviousProcessExits(diagnosticContext)", code)
        self.assertIn("control.hasSession()", code)
        self.assertIn("CELIKOM_SESSION", code)
        self.assertIn("STAGE_B_AUDIO.onNativeTrackWrapperCreated(", code)
        self.assertIn("chain.getThisObject(),chain.getArg(0)", code)
        self.assertIn("STAGE_B_AUDIO.enterNativeMainSourceRequest(", code)
        self.assertIn("chain.getArg(2),chain.getArg(5)", code)
        self.assertIn("STAGE_B_AUDIO.onNativeMainContinuationConstructed(", code)
        self.assertIn('Class.forName("RAa",false,loader)', code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceCreated( result,chain.getThisObject());", " ".join(code.split()))
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceOpen(chain.getThisObject())", code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceOpenAttempt(", code)
        self.assertIn("STAGE_B_AUDIO.onExoFirstOpenHookEnter()", code)
        self.assertIn("STAGE_B_AUDIO.onExoFirstOpenDeferredArmResult(armed)", code)
        self.assertIn("NATIVE_EARLY_ADMISSION.exportLines()", code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceClose(", code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceOpenFailure(", code)
        self.assertIn('source.getDeclaredMethod("close")', code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceRead(", code)
        self.assertIn("STAGE_B_AUDIO.onExoOpen()", code)
        self.assertIn("STAGE_B_AUDIO.onExoReadResult(", code)
        self.assertIn("STAGE_B_AUDIO.onExoFailure()", code)
        self.assertIn("STAGE_B_AUDIO.exportLines()", code)
        self.assertIn('Class.forName("iLb",false,loader)', code)
        self.assertIn('Class.forName("lLb",false,loader)', code)
        self.assertIn('STAGE_B_AUDIO.onOriginalMediaSourceConstructed(', code)
        self.assertIn('STAGE_B_AUDIO.exactOriginalMediaItemCreator(item)', code)
        self.assertIn('STAGE_B_AUDIO.onOriginalChildContextComparison(', code)
        self.assertIn('chain.getArg(0),chain.getArg(3),item', code)
        self.assertIn('setter[1]==creator[3]', code)
        self.assertIn('STAGE_B_AUDIO.onOriginalMediaItemDescriptor(', code)
        self.assertIn('"SOURCE_ANCHOR","REGISTERED"', code)
        self.assertIn('"CHILD_DESCRIPTOR","REGISTERED"', code)
        self.assertIn("STAGE_B_AUDIO.onOriginalChildHookRegistered()",code)
        self.assertIn("STAGE_B_AUDIO.onOriginalChildEntered()",code)
        self.assertIn("STAGE_B_AUDIO.onOriginalChildCreatorMatch(creator!=null)",code)
        self.assertIn("STAGE_B_AUDIO.onOriginalChildSetterMatch(setter!=null)",code)
        self.assertIn("result=chain.proceed(); // exactly one unmodified original call", code)
        self.assertIn("result=chain.proceed();", code)
        self.assertIn('Class.forName("Dp0",false,loader)', code)
        self.assertIn('Class.forName("Gp0",false,loader)', code)
        self.assertIn('Class.forName("tCa",false,loader)', code)
        self.assertNotIn('Class.forName("LDp0",false,loader)', code)
        self.assertNotIn('Class.forName("LGp0",false,loader)', code)
        self.assertNotIn('Class.forName("LtCa",false,loader)', code)
        self.assertNotIn("MEDIA_SOURCE_REPLACEMENT_APPLIED", code)



    def test_nav40_creator_late_flow_strict_guard_readonly(self):
        code = HOOK.read_text(encoding="utf-8")
        self.assertIn('DIAGNOSTIC_BUILD = "NAV_V45_CURRENT_MEDIAITEM_LOGICAL_ID_READONLY"', code)
        self.assertIn('PrivateNativeCurrentMediaItemTarget', code)
        self.assertIn('CURRENT_MEDIAITEM_SOURCE', code)
        self.assertIn('CURRENT_MEDIAITEM_LOGICAL_ID', code)
        self.assertIn('PrivateNativePlayerPeriodTarget', code)
        self.assertIn('PLAYER_PERIOD_AT_AUDIO_READ', code)
        self.assertIn("installNativeTcaCreatorScopeHook(loader)", code)
        self.assertIn('emit("AUDIO_NATIVE_TCA_CREATOR_HOOK","TRACK_CREATOR","REGISTERED")', code)
        self.assertIn('emit("AUDIO_NATIVE_TCA_CREATOR_HOOK","TRACK_CREATOR","NO_HOOK")', code)
        self.assertIn("STAGE_B_AUDIO.enterNativeTcaCreatorTrackScope(track,fieldStatus)", code)
        self.assertIn("STAGE_B_AUDIO.onNativeTrackWrapperCreated(", code)
        self.assertIn("chain.getThisObject(),chain.getArg(0)", code)
        self.assertNotIn("MEDIA_SOURCE_REPLACEMENT_APPLIED", code)
        workflow = (BASE.parents[1] / ".github/workflows/android-a1-metrica-init-state-observer-arm13.yml").read_text(encoding="utf-8")
        self.assertIn("a1_private_live_queue_slot_target.py", workflow)
        self.assertIn("a1_private_active_period_source_target.py", workflow)
        self.assertIn("a1_private_player_period_current_target.py", workflow)


if __name__ == "__main__":
    unittest.main()
