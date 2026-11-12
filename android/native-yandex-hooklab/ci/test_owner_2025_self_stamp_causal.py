"""Synthetic-only source-stamp provenance invariants, no proprietary APKs."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from owner_2025_self_stamp_causal_arm13 import (
    STAMP_ENTRY, manifest_and_content_equal_except_honest_stamp,
)


def write_apk(path, stamp, resource=b"ORIGINAL_RESOURCE"):
    with zipfile.ZipFile(path,"w") as apk:
        apk.writestr("AndroidManifest.xml",b"MANIFEST_SAME")
        apk.writestr("classes.dex",b"SYNTHETIC_CLASSES_SAME")
        apk.writestr("resources.arsc",resource)
        if stamp is not None:
            apk.writestr(STAMP_ENTRY,stamp)


class OwnSourceStampContentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a=Path(self.temp.name)/"issuer_fixture.apk"
        self.b=Path(self.temp.name)/"own_fixture.apk"
        write_apk(self.a,b"ISSUER_MARKER")
        write_apk(self.b,b"INDEPENDENT_OWN_MARKER")

    def test_own_distinct_stamp_preserves_all_other_bytes(self):
        result=manifest_and_content_equal_except_honest_stamp(self.a,self.b)
        self.assertTrue(result["every_nonstamp_app_content_entry_byte_identical"])
        self.assertEqual(result["ordinary_entry_count_bounded"],3)
        self.assertFalse(result["publisher_source_stamp_reused"])
        self.assertNotIn("ISSUER_MARKER",str(result))

    def test_reused_publisher_stamp_is_not_acceptable(self):
        write_apk(self.b,b"ISSUER_MARKER")
        with self.assertRaisesRegex(RuntimeError,"OWN_STAMP_MUST_NOT_REUSE_PUBLISHER_STAMP"):
            manifest_and_content_equal_except_honest_stamp(self.a,self.b)

    def test_non_stamp_file_byte_change_is_rejected(self):
        write_apk(self.b,b"INDEPENDENT_OWN_MARKER",b"TAMPERED_RESOURCE")
        with self.assertRaisesRegex(RuntimeError,"OWN_STAMP_ORDINARY_PAYLOAD_CHANGED"):
            manifest_and_content_equal_except_honest_stamp(self.a,self.b)

    def test_missing_stamp_never_passes_as_valid(self):
        write_apk(self.b,None)
        with self.assertRaisesRegex(RuntimeError,"OWN_STAMP_MARKER_MISSING"):
            manifest_and_content_equal_except_honest_stamp(self.a,self.b)


if __name__=="__main__":
    unittest.main()
