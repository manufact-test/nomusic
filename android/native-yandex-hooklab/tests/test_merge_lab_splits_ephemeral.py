import sys
import unittest
import tempfile
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from merge_lab_splits_ephemeral import byte_payloads, verify_merged_payloads

class MergeContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def apk(self,name,entries):
        file=self.root/name
        with zipfile.ZipFile(file,"w") as zipout:
            for path,data in entries.items():
                zipout.writestr(path,data)
        return file
    def test_preserves_dex_and_native_payloads(self):
        a=self.apk("base.apk",{"classes.dex":b"dex-a","classes2.dex":b"dex-b"})
        b=self.apk("split.apk",{"lib/armeabi-v7a/libx.so":b"ELF"})
        merged=self.apk("merged.apk",{"classes.dex":b"dex-a","classes2.dex":b"dex-b",
                                    "lib/armeabi-v7a/libx.so":b"ELF",
                                    "resources.arsc":b"resources can change"})
        result=verify_merged_payloads([a,b],merged)
        self.assertTrue(result["payload_byte_hashes_match"])
        self.assertEqual(result["single_apk_payload_dex_count"],2)
        self.assertEqual(result["single_apk_payload_native_library_count"],1)
    def test_rejects_changed_code_or_library(self):
        a=self.apk("base.apk",{"classes.dex":b"original","lib/armeabi-v7a/libx.so":b"elf"})
        merged=self.apk("merged.apk",{"classes.dex":b"replaced","lib/armeabi-v7a/libx.so":b"elf"})
        with self.assertRaisesRegex(ValueError,"DRIFT"):
            verify_merged_payloads([a],merged)
    def test_detects_inconsistent_input_duplicates(self):
        a=self.apk("base.apk",{"classes.dex":b"dex-a"})
        b=self.apk("split.apk",{"classes.dex":b"dex-b"})
        with self.assertRaisesRegex(ValueError,"INCONSISTENT"):
            byte_payloads([a,b])
    def test_no_base_dex(self):
        a=self.apk("split.apk",{"lib/arm64-v8a/libx.so":b"ELF"})
        with self.assertRaisesRegex(ValueError,"BASE_CODE"):
            byte_payloads([a])

if __name__=="__main__":
    unittest.main()
