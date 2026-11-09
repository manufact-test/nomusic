"""Synthetic Dalvik caller tracing tests (no Yandex APK or user data)."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_inspect_android_host import synthetic_dex
from trace_native_callers import Dex,DexError,dex_callers,method_definitions

def uleb(n):
    result=[]
    while True:
        b=n&127;n>>=7
        result.append(b|(128 if n else 0))
        if not n:return bytes(result)

def with_code(insns):
    b=bytearray(synthetic_dex())
    class_off=struct.unpack_from("<I",b,100)[0]
    data_off=len(b)
    code_off=data_off+8
    while True:
        new=(data_off+6+len(uleb(code_off))+3)&~3
        if new==code_off:break
        code_off=new
    struct.pack_into("<I",b,class_off+24,data_off)
    b+=b"\x00\x00\x01\x00\x00\x01"+uleb(code_off)
    b+=b"\x00"*(code_off-len(b))
    b+=struct.pack("<HHHHII",1,1,1,0,0,len(insns))
    b+=struct.pack("<"+"H"*len(insns),*insns)
    struct.pack_into("<I",b,32,len(b))
    return bytes(b)

class TraceCallersTests(unittest.TestCase):
    def test_real_invoke(self):
        r=dex_callers(with_code([0x106e,0,0,0x0e]))
        self.assertEqual(r["target_refs"],1)
        self.assertEqual(r["call_sites"],1)
        self.assertEqual(r["callers"][0]["target_method"],"createMediaSource")
        self.assertTrue(r["complete"])
    def test_reference_is_not_invocation(self):
        r=dex_callers(with_code([0x0e]))
        self.assertEqual(r["target_refs"],1)
        self.assertEqual(r["call_sites"],0)
    def test_fake_invoke_inside_const_wide_operand(self):
        r=dex_callers(with_code([0x0018,0x106e,0,0,0,0x0e]))
        self.assertEqual(r["call_sites"],0)
    def test_range_invoke(self):
        r=dex_callers(with_code([0x0174,0,0,0x0e]))
        self.assertEqual(r["call_sites"],1)
        self.assertEqual(r["callers"][0]["opcode"],"0x74")
    def test_invalid_invoke_marks_incomplete(self):
        r=dex_callers(with_code([0x106e,2,0,0x0e]))
        self.assertFalse(r["complete"])
        self.assertEqual(r["call_sites"],0)
    def test_wrong_class_data_offset(self):
        b=bytearray(with_code([0x0e]))
        class_off=struct.unpack_from("<I",b,100)[0]
        struct.pack_into("<I",b,class_off+24,len(b)+50)
        with self.assertRaises(DexError):
            list(method_definitions(Dex(bytes(b))))
    def test_unused_opcode_marks_incomplete(self):
        r=dex_callers(with_code([0x0073]))
        self.assertFalse(r["complete"])
    def test_data_payload_skips_apparent_invoke(self):
        r=dex_callers(with_code([0x0300,1,2,0,0x106e,0x0e,0x0e]))
        self.assertEqual(r["call_sites"],0)
        self.assertTrue(r["complete"])
if __name__=="__main__":
    unittest.main()
