"""Bytecode equivalence tests use synthetic DEX only, never Yandex binaries."""
import sys, unittest, struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_inspect_android_host import synthetic_dex
from test_trace_native_callers import with_code
from compare_dex_method_bodies import compare_dex_code

class SemanticCodeTests(unittest.TestCase):
    def test_identical_synthetic_method_bytes(self):
        x=with_code([0x0e])
        c=compare_dex_code(x,x)
        self.assertEqual(c["changed_instruction_body_count"],0)
        self.assertEqual(c["code_comparison"],"IDENTICAL_INSTRUCTIONS_ALL_PAIRED_METHODS")

    def test_different_body_not_same_code(self):
        a=with_code([0x0e])
        b=with_code([0x0f])
        c=compare_dex_code(a,b)
        self.assertEqual(c["changed_instruction_body_count"],1)
        self.assertEqual(c["code_comparison"],"SOME_METHOD_INSTRUCTIONS_DIFFER")

    def test_large_dex_string_over_4096_is_supported(self):
        from inspect_android_host import Dex
        raw=bytearray(synthetic_dex())
        string_index=3
        string_table=struct.unpack_from("<I",raw,60)[0]
        text="x"*6000
        pos=len(raw)
        length=len(text)
        def uleb(n):
            out=[]
            while True:
                byte=n&127;n>>=7
                out.append(byte | (128 if n else 0))
                if not n:return bytes(out)
        raw.extend(uleb(length)+text.encode("ascii")+b"\\0")
        struct.pack_into("<I",raw,string_table+4*string_index,pos)
        struct.pack_into("<I",raw,32,len(raw))
        self.assertEqual(Dex(bytes(raw)).string(3),text)

    def test_method_name_difference_fails_comparison(self):
        a=synthetic_dex("createMediaSource")
        b=synthetic_dex("createMediaSourcd")
        c=compare_dex_code(a,b)
        self.assertFalse(c["method_signatures_equal"])
        self.assertEqual(c["code_comparison"],"INCOMPARABLE_METHOD_IDENTITY_CHANGED")

if __name__=="__main__":
    unittest.main()
