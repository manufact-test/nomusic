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
    public static void main(String[] argv) {
        StageBAudioEvidence e = new StageBAudioEvidence();
        String[] initial = e.exportLines();
        check(initial.length == 32);
        for (int i=0;i<31;i++) check(initial[i].contains(";error=NONE;"));
        check(initial[31].contains("CELIKOM_REPLACEMENT;error=NOT_CONNECTED"));

        Object track=new Object(), wrapper=new Object(), descriptor=new Object();
        Object factory=new Object(), source=new Object();
        Object unselectedTrack=new Object(), unselectedWrapper=new Object();
        Object wrongDescriptor=new Object(), wrongFactory=new Object(), wrongSource=new Object();

        e.onNativeTrackFlowEmission(track);
        e.enterNativeTrackSourceRequest(track);
        e.onNativeTrackWrapperCreated(wrapper);
        e.exitNativeTrackSourceRequest();
        e.enterNativeTrackSourceRequest(unselectedTrack);
        e.onNativeTrackWrapperCreated(unselectedWrapper);
        e.exitNativeTrackSourceRequest();
        e.enterNativeMainSourceRequest(wrapper);
        e.onExoDescriptorBuilt(descriptor);
        e.onNativeExoDescriptorBuiltForCurrentWrapper(descriptor);
        e.exitNativeMainSourceRequest();
        e.enterNativeMainSourceRequest(unselectedWrapper);
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
        for(int i=0;i<names.length;i++) bucket(links,21+i,names[i],"ONE");
        check(links[31].contains("CELIKOM_REPLACEMENT;error=NOT_CONNECTED"));

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
        check(rows[17].contains(";error=ONE;"));
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
                                  check=True, capture_output=True, text=True)
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
        self.assertIn("STAGE_B_AUDIO.enterNativeTrackSourceRequest(selectedTrack)", code)
        self.assertIn("STAGE_B_AUDIO.onNativeTrackWrapperCreated(chain.getThisObject())", code)
        self.assertIn("STAGE_B_AUDIO.enterNativeMainSourceRequest(chain.getArg(2))", code)
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceCreated( result,chain.getThisObject());", " ".join(code.split()))
        self.assertIn("STAGE_B_AUDIO.onExoSourceInstanceOpen(chain.getThisObject())", code)
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
