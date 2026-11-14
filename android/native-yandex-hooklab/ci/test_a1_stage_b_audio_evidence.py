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
    static void check(boolean b) { if (!b) throw new AssertionError(); }
    static void line(String[] rows,int index,String expected) {
        check(rows[index].equals("event=AUDIO_STAGE_B_SUMMARY;origin="+expected+";error="+
            (index==0 ? "FEW" : index==2 || index==5 || index==6 || index==8 ? "ONE" : "NONE")+
            ";thread=OTHER"));
    }
    public static void main(String[] argv) {
        StageBAudioEvidence e = new StageBAudioEvidence();
        String[] initial = e.exportLines();
        check(initial.length == 12);
        for (int i=0;i<11;i++) check(initial[i].contains(";error=NONE;"));
        check(initial[11].contains("CELIKOM_REPLACEMENT;error=NOT_CONNECTED"));
        e.onFileInfoResult();
        e.onDirectDownloadInfoResult();
        e.onReader(0, true);
        e.onReader(0, false);
        e.onExtractorSource(0);
        e.onReadReturn(512);
        e.onReadReturn(-1);
        e.onReadReturn(0);
        e.onReadException();
        String[] rows = e.exportLines();
        for(int i=0;i<11;i++){
            String[] categories = {"FILEINFO_DTO","DOWNLOADINFO_DTO",
                "READER_0","READER_1","EXTRACTOR_0","EXTRACTOR_1",
                "EXTRACTOR_OTHER","SAME_SOURCE_OBJECT","POSITIVE_READS",
                "SOURCE_END","READ_EXCEPTIONS"};
            String bucket = i==2 ? "FEW" :
                (i==0||i==1||i==4||i==7||i==8||i==9||i==10 ? "ONE" : "NONE");
            check(rows[i].equals("event=AUDIO_STAGE_B_SUMMARY;origin="+categories[i]+
                 ";error="+bucket+";thread=OTHER"));
            check(!rows[i].contains("512") && !rows[i].contains("http"));
        }
        for (int i=0;i<10;i++) e.onReader(1,false);
        check(e.exportLines()[3].contains(";error=MANY;"));
        check(e.exportLines()[11].contains("NOT_CONNECTED"));
        System.out.println("PASS Stage B scoped native summary: no source, URL or identity disclosure");
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
        self.assertIn("STAGE_B_AUDIO.exportLines()", code)
        self.assertIn("result=chain.proceed(); // exactly one unmodified original call", code)
        self.assertIn("result=chain.proceed();", code)
        self.assertNotIn("MEDIA_SOURCE_REPLACEMENT_APPLIED", code)


if __name__ == "__main__":
    unittest.main()
