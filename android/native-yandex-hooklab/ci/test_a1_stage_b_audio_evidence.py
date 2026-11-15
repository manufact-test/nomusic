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
HARNESS = """
package pro.celikom.a1exitwitness;
public final class StageBAudioEvidenceTest {
    static void check(boolean value) { if (!value) throw new AssertionError(); }
    static void bucket(String[] rows,int index,String category,String value) {
        check(rows[index].equals("event=AUDIO_STAGE_B_SUMMARY;origin="+category+
            ";error="+value+";thread=OTHER"));
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
    public static void main(String[] argv) {
        StageBAudioEvidence e = new StageBAudioEvidence();
        String[] initial = e.exportLines();
        check(initial.length == 44);
        for (int i=0;i<43;i++) check(initial[i].contains(";error=NONE;"));
        check(initial[43].contains("CELIKOM_REPLACEMENT;error=NOT_CONNECTED"));

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
        check(links[43].contains("CELIKOM_REPLACEMENT;error=NOT_CONNECTED"));

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

        // A newer wrapper/descriptor/factory resets every downstream hop.
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
        bucket(reset.exportLines(),29,"TRACK_SOURCE_OPEN_LINK","ONE");
        bucket(reset.exportLines(),30,"TRACK_SOURCE_READ_LINK","ONE");
        bucket(reset.exportLines(),27,"TRACK_DESCRIPTOR_FACTORY_LINK","ONE");
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
        System.out.println("PASS Stage B exact Track-to-Exo identity chain; mismatches fail closed");
    }
}
"""


class StageBAudioEvidenceTest(unittest.TestCase):
    def test_actual_java_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            test = pathlib.Path(tmp) / "StageBAudioEvidenceTest.java"
            test.write_text(HARNESS, encoding="utf-8")
            subprocess.run(["javac", "-d", tmp, str(EVIDENCE), str(test)],
                           check=True, capture_output=True, text=True)
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
        self.assertIn("STAGE_B_AUDIO.onNativeTrackWrapperCreated(chain.getThisObject())", code)
        self.assertIn("STAGE_B_AUDIO.enterNativeMainSourceRequest(", code)
        self.assertIn("chain.getArg(2),chain.getArg(5)", code)
        self.assertIn("STAGE_B_AUDIO.onNativeMainContinuationConstructed(", code)
        self.assertIn('Class.forName("RAa",false,loader)', code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceCreated( result,chain.getThisObject());", " ".join(code.split()))
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceOpen(chain.getThisObject())", code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceOpenAttempt(", code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceClose(", code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceOpenFailure(", code)
        self.assertIn('source.getDeclaredMethod("close")', code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceRead(", code)
        self.assertIn("STAGE_B_AUDIO.onExoOpen()", code)
        self.assertIn("STAGE_B_AUDIO.onExoReadResult(", code)
        self.assertIn("STAGE_B_AUDIO.onExoFailure()", code)
        self.assertIn("STAGE_B_AUDIO.exportLines()", code)
        self.assertIn("result=chain.proceed(); // exactly one unmodified original call", code)
        self.assertIn("result=chain.proceed();", code)
        self.assertIn('Class.forName("Dp0",false,loader)', code)
        self.assertIn('Class.forName("Gp0",false,loader)', code)
        self.assertIn('Class.forName("tCa",false,loader)', code)
        self.assertNotIn('Class.forName("LDp0",false,loader)', code)
        self.assertNotIn('Class.forName("LGp0",false,loader)', code)
        self.assertNotIn('Class.forName("LtCa",false,loader)', code)
        self.assertNotIn("MEDIA_SOURCE_REPLACEMENT_APPLIED", code)


if __name__ == "__main__":
    unittest.main()
