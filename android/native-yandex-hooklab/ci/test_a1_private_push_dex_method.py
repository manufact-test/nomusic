"""Synthetic-only regression, no original APK or identifiers."""
import io
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from a1_private_push_dex_method import Dex,DexError,uleb,group_class,group_call,code_candidates

class PrivateDexAnalysisUnitTest(unittest.TestCase):
    def test_uleb_bounds(self):
        for num,seq in [(0,b"\x00"),(127,b"\x7f"),(128,b"\x80\x01"),(16383,b"\xff\x7f")]:
            self.assertEqual(uleb(seq,0)[0],num)
        with self.assertRaises(DexError):uleb(b"\x80",0)
    def test_only_fixed_enum_categories(self):
        self.assertEqual(group_class("Lcom/yandex/metrica/push/impl/PRIVATE;"),"PUSH_IMPL")
        self.assertEqual(group_call("Lio/appmetrica/analytics/ModulesFacade;","isActivatedForApp"),"MODERN_PREDICATE")
        self.assertEqual(group_call("Lcom/secret/vendor;","secret"),"OTHER")
        self.assertEqual(code_candidates(b"\x1a\x00\x05\x00", {5})[0],[0])
        self.assertEqual(code_candidates(b"\x1b\x00\x05\x00\x00\x00", {5})[0],[0])
    def test_large_non_target_dex_string_is_skipped_not_fatal(self):
        # Real APK DEX can contain thousands of bytes in one data string.
        blob=bytearray(112+4+2+5000+1)
        blob[:8]=b"dex\\n035\\0".replace(b"\\\\",b"\\")
        struct.pack_into("<II",blob,56,1,112)
        struct.pack_into("<I",blob,112,116)
        blob[116:118]=bytes((0x88,0x27))
        blob[118:5118]=b"x"*5000
        blob[5118]=0
        self.assertEqual(Dex(bytes(blob)).string(0),"")

    def test_bad_dex_rejected_without_data(self):
        with self.assertRaises(DexError):Dex(b"PK\x03\x04")

if __name__=="__main__":unittest.main()
