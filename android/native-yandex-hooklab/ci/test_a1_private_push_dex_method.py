"""Synthetic-only regression, no original APK or identifiers."""
import io
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from a1_private_push_dex_method import Dex,DexError,uleb,group_class,group_call,code_candidates,helper_chain

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
        blob[:8]=bytes((100,101,120,10,48,51,53,0))
        struct.pack_into("<II",blob,56,1,112)
        struct.pack_into("<I",blob,112,116)
        blob[116:118]=bytes((0x88,0x27))
        blob[118:5118]=b"x"*5000
        blob[5118]=0
        self.assertEqual(Dex(bytes(blob)).string(0),"")

    def test_helper_chain_bounded_and_synthetic(self):
        class FakeDex:
            method_count=5
            def method(self,ref):
                return {1:("Lcom/yandex/metrica/push/impl/TEST;","a"),
                        2:("Lio/appmetrica/analytics/ModulesFacade;","isActivatedForApp")
                        }.get(ref,("Lprivate/secret/Class;","token"))
        code=bytes((0x71,0,2,0,0,0))
        result=helper_chain(FakeDex(),{1:code},{1})
        self.assertEqual(len(result),3)
        self.assertTrue(result[0]["modern_predicate"])
        self.assertFalse(result[0]["legacy_predicate"])
        self.assertEqual(result[1]["methods_found"],0)
        self.assertNotIn("TEST",str(result))

    def test_abstract_interface_dispatch_to_concrete_predicate(self):
        class Fake:
            method_count=5
            def method_signature(self,ref):
                return ("Lcom/yandex/metrica/push/impl/ITest;","d",1)
            def method(self,ref):
                return {2:("Lio/appmetrica/analytics/ModulesFacade;","isActivatedForApp")
                        }.get(ref,("Lcom/yandex/metrica/push/impl/ITest;","d"))
        interface={"Lcom/yandex/metrica/push/impl/ITest;":
                   {"Lcom/yandex/metrica/push/impl/Impl;"}}
        methods={("Lcom/yandex/metrica/push/impl/Impl;","d",1):4}
        result=helper_chain(Fake(),{4:bytes((0x71,0,2,0,0,0))},
                            {1},interface,methods)
        self.assertTrue(result[0]["interface_dispatch_resolved"])
        self.assertTrue(result[0]["modern_predicate"])
        self.assertEqual(result[0]["methods_found"],1)
        self.assertEqual(result[1]["methods_found"],0)
        self.assertNotIn("Impl",str(result))

    def test_bad_dex_rejected_without_data(self):
        with self.assertRaises(DexError):Dex(b"PK\x03\x04")

if __name__=="__main__":unittest.main()
