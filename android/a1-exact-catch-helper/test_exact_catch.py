"""Synthetic-only DEX catch metadata and TRUE-path exception-graph unit tests."""
from pathlib import Path
import importlib.util
import struct
import unittest

spec=importlib.util.spec_from_file_location("exact_catch",Path(__file__).with_name("exact_catch.py"))
subject=importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

class Dex:
    method_count=2
    type_count=1
    def __init__(self,catch_type="Ljava/lang/Throwable;"):
        self.catch_type=catch_type
    def method(self,idx):
        return (("Lcom/yandex/metrica/push/impl/a;","a") if idx==0 else
                ("Lcom/yandex/metrica/push/YandexMetricaPush;","init"))
    def type(self,idx):
        assert idx==0
        return self.catch_type

def method_bytes():
    # off 0: invoke near-helper, then direct move-result + if-nez.
    # TRUE -> offset 14: SDK init invoke; normal jump skips error-throw.
    # catch -> off 22: move-exception, const-string, throw at 28.
    return bytes((
        0x71,0x00,0x00,0x00,0x00,0x00,  # invoke-static ref 0 (near)
        0x0a,0x00,                      # move-result v0
        0x39,0x00,0x03,0x00,            # if-nez v0 +3 code units = 14
        0x0e,0x00,                      # return-void
        0x71,0x00,0x01,0x00,0x00,0x00,  # invoke-static ref 1 (SDK init)
        0x28,0x05,                      # goto +5 code units = 30
        0x0d,0x02,                      # move-exception v2, catch entry
        0x1a,0x00,0x00,0x00,            # const-string index0: modeled error
        0x27,0x00,                      # throw v0
        0x0e,0x00,                      # normal return
    ))

def codeitem(kind="all",start=7,count=3,handler_off=1):
    code=method_bytes()
    if kind=="none":
        return struct.pack("<HHHHII",3,1,1,0,0,len(code)//2)+code
    # encoded_catch_handler_list relative offset 1 for its single entry.
    if kind=="all":handlers=b"\x01\x00\x0b"
    else:handlers=b"\x01\x01\x00\x0b"  # catch typed class index0, address11
    return (struct.pack("<HHHHII",3,1,1,1,0,len(code)//2)+code+
            struct.pack("<IHH",start,count,handler_off)+handlers)

class CatchTests(unittest.TestCase):
    def classified(self,kind="all",catch_type="Ljava/lang/Throwable;"):
        d=Dex(catch_type)
        code,ranges=subject.read_catches(codeitem(kind),0,d)
        return subject.classify(code,ranges,{0},{0},d)

    def test_catch_all_routes_true_path_into_error_throw(self):
        r=self.classified()
        self.assertEqual(r["true_normal_cfg"],"TRUE_NORMAL_BLOCKS_THROW")
        self.assertEqual(r["EXACT_HELPER_IN_TRY"],"NOT_IN_TRY")
        self.assertEqual(r["HELPER_OWN_HANDLER_REACH"],"NOT_REACH")
        self.assertEqual(r["TRUE_PATH_INVOKE_CATCH_REACH"],"EXACT_THROW_IN_HANDLER_REACH")
        self.assertEqual(r["EXACT_THROW_IN_HANDLER_REACH"],"EXACT_THROW_IN_HANDLER_REACH")
        self.assertEqual(r["SDK_INIT_NEARBY_IN_TRY"],"SDK_INIT_NEARBY_IN_TRY")
        self.assertEqual(r["TRY_COVERS_THROW_BUILD"],"NOT")
        self.assertEqual(r["HANDLER_KIND_FAMILIES"],["CATCH_ALL"])

    def test_typed_throwable_can_reach(self):
        r=self.classified("typed","Ljava/lang/Throwable;")
        self.assertEqual(r["TRUE_PATH_INVOKE_CATCH_REACH"],"EXACT_THROW_IN_HANDLER_REACH")
        self.assertEqual(r["HANDLER_KIND_FAMILIES"],["TYPED_THROWABLE"])

    def test_other_typed_catch_not_proven_to_match_throw(self):
        r=self.classified("typed","Lorg/example/SpecificOnly;")
        self.assertEqual(r["TRUE_PATH_INVOKE_CATCH_REACH"],"UNKNOWN")
        self.assertEqual(r["EXACT_THROW_IN_HANDLER_REACH"],"UNKNOWN")
        self.assertEqual(r["HANDLER_KIND_FAMILIES"],["TYPED_OTHER"])

    def test_no_try_means_no_exception_route(self):
        r=self.classified("none")
        self.assertEqual(r["EXACT_HELPER_IN_TRY"],"NOT_IN_TRY")
        self.assertEqual(r["TRUE_PATH_INVOKE_CATCH_REACH"],"NOT_REACH")
        self.assertEqual(r["EXACT_THROW_IN_HANDLER_REACH"],"NOT_REACH")
        self.assertEqual(r["TRY_COVERS_THROW_BUILD"],"NOT")

    def test_reject_malformed_encoded_handler_offset(self):
        with self.assertRaises(subject.Closed):
            subject.read_catches(codeitem("all",handler_off=0),0,Dex())

    def test_reject_try_out_of_code_and_non_instruction_boundaries(self):
        for start,count in ((15,3),(8,3),(7,0)):
            with self.subTest(start=start,count=count),self.assertRaises(subject.Closed):
                subject.read_catches(codeitem("all",start=start,count=count),0,Dex())

    def test_reject_unknown_handler_address(self):
        b=bytearray(codeitem())
        b[-1]=250
        with self.assertRaises(subject.Closed):
            subject.read_catches(bytes(b),0,Dex())

    def test_signed_leb_zero_and_negative_one(self):
        self.assertEqual(subject._s(b"\x00",0,1),(0,1))
        self.assertEqual(subject._s(b"\x7f",0,1),(-1,1))
        with self.assertRaises(subject.Closed):
            subject._s(b"\x80",0,1)

if __name__=="__main__":unittest.main()
