import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_typed_wrapper_coroutines import (
    brief_type, parse_types, method_profile, profile_tracked_results,
    class_field_shapes, field_at, safe_instruction_shape, focused_producer_windows
)


class FakeDex:
    def __init__(self, code, methods):
        self.words=[0]*8+code
        self.words[6]=len(code)
        self.methods=methods
        self.method_count=len(methods)
    def bounds(self,off,size):
        if off<0 or off+size>len(self.words)*2:
            raise ValueError("DEX_BOUNDS")
    def u16(self,off):
        return self.words[off//2]
    def u32(self,off):
        return self.u16(off)|(self.u16(off+2)<<16)
    def method(self,idx):
        return self.methods[idx]


class TypedWrapperTests(unittest.TestCase):
    def test_descriptor_parser_for_mixed_arrays_and_coroutines(self):
        args,out=parse_types("(Leed;[I[[Lxa7;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;")
        self.assertEqual(args,["Leed;","[I","[[Lxa7;","Lkotlin/coroutines/Continuation;"])
        self.assertEqual(out,"Ljava/lang/Object;")
        self.assertEqual(brief_type("Leed;"),"Leed;")
        self.assertEqual(brief_type("[[Lxa7;"),"array")
        self.assertEqual(method_profile(("Lta7;","c","(Leed;I)Lwa7;"))["return_type"],"Lwa7;")
        with self.assertRaises(ValueError):
            parse_types("(Lbad)")

    def test_converter_result_reaches_constructor_only_at_argument_one(self):
        producer=("Lsw7;","y0","(Ljava/lang/Object;)Leed;")
        ctor=("Lxa7;","<init>","(Leed;)V")
        # invoke-static {v1} -> result v2 -> invoke-direct {v4(this),v2} -> return
        code=[0x1071,0,0x0001, 0x020c,
              0x2070,1,0x0024, 0x000e]
        rows=profile_tracked_results(FakeDex(code,[producer,ctor]),0,{producer})
        self.assertEqual(rows[0]["events"],[{"action":"invoke","target":"Lxa7;-><init>","arg_word":1}])
        self.assertFalse(rows[0]["proven_exact_track"])

    def test_converter_result_does_not_reach_unrelated_interface(self):
        producer=("Lsw7;","y0","()Leed;")
        sink=("Leod;","emit","(Leed;)V")
        code=[0x0071,0,0, 0x020c, 0x0212,
              0x1072,1,0x0002, 0x000e]
        rows=profile_tracked_results(FakeDex(code,[producer,sink]),0,{producer})
        self.assertEqual(rows[0]["events"],[])

    def test_branch_join_return_may_flow(self):
        producer=("Lged;","a","()Ljava/lang/Object;")
        code=[0x0071,0,0, 0x020c, 0x0038,3, 0x000e, 0x0211]
        rows=profile_tracked_results(FakeDex(code,[producer]),0,{producer})
        self.assertIn({"action":"return_object","target":"none","arg_word":0},
                      rows[0]["events"])
        self.assertFalse(rows[0]["bounded_search_truncated"])

    def test_opcode_excerpt_shows_structure_not_raw_literals(self):
        producer=("Lged;","a","()Ljava/lang/Object;")
        # const-string points at local string ID, which must never be emitted
        code=[0x0071,0,0,0x020c,0x011a,0x0200,0x0211]
        dex=FakeDex(code,[producer])
        excerpt=focused_producer_windows(dex,0,{("Lged;","a")},pre=0,post=4)
        self.assertEqual(excerpt[0]["producer"],"Lged;->a")
        self.assertEqual(excerpt[0]["structural_window"][2]["kind"],
                         "const_string_reference_redacted")
        self.assertNotIn("0x0200",str(excerpt))
        self.assertFalse(excerpt[0]["register_or_decoder_proven"])

    def test_object_field_shape_only_without_name(self):
        class WithField(FakeDex):
            def table(self, offset, width):
                return 1,16
            def u16(self,offset):
                if offset == 16:return 0
                if offset == 18:return 1
                return super().u16(offset)
            def descriptor(self,idx):
                return ("Lxa7;","Leed;")[idx]
        result=safe_instruction_shape(WithField([0x005b,0],[]),0x5b,(0x005b,0))
        self.assertEqual(result,{"kind":"iput_object","owner":"Lxa7;","field_type":"Leed;"})

    def test_iget_object_wrapper_projection_kills_alias_not_identity(self):
        # Lcq7.i0 -> wrapper v1; iget-object v1,v1,field; check-cast Lga4
        # then Lero.<init>{v1}; must NOT call it direct wrapper-object flow.
        src=("Lcq7;","i0","()Ljava/lang/Object;")
        consumer=("Lero;","<init>","(Lga4;)V")
        code=[0x0071,0,0, 0x010c, 0x1154,0,
              0x1070,1,0x0001, 0x000e]
        rows=profile_tracked_results(FakeDex(code,[src,consumer]),0,{src})
        self.assertEqual(rows[0]["events"],[])
        self.assertFalse(rows[0]["proven_exact_track"])

    def test_move_object_alias_is_different_from_field_projection(self):
        src=("Lcq7;","i0","()Ljava/lang/Object;")
        consumer=("Lero;","<init>","(Ljava/lang/Object;)V")
        # move-object v2,v1 still preserves identity (unlike iget-object).
        code=[0x0071,0,0,0x010c,0x1207,0x1070,1,0x0002,0x000e]
        rows=profile_tracked_results(FakeDex(code,[src,consumer]),0,{src})
        self.assertIn({"action":"invoke","target":"Lero;-><init>","arg_word":0},
                      rows[0]["events"])

    def test_nibble_const_overwrites_object_alias(self):
        src=("Lcq7;","i0","()Ljava/lang/Object;")
        consumer=("Lero;","<init>","(Ljava/lang/Object;)V")
        # const/4 v1, -1 is encoded 0xf112; kills result object.
        code=[0x0071,0,0,0x010c,0xf112,0x1070,1,0x0001,0x000e]
        rows=profile_tracked_results(FakeDex(code,[src,consumer]),0,{src})
        self.assertEqual(rows[0]["events"],[])

    def test_bad_proto_rejected(self):
        for bad in ["","()", "(Labc)V","(Z)","(I)VV"]:
            with self.assertRaises(ValueError,msg=bad):
                parse_types(bad)

    def test_privacy_restricts_named_class_descriptors(self):
        self.assertEqual(brief_type("Lcom/yandex/music/analytics/Internal;"),"other-object")
        self.assertEqual(brief_type("Ljava/lang/String;"),"java-string")
        self.assertEqual(brief_type("Landroidx/media3/datasource/DataSource;"),"public-media3-type")


if __name__=="__main__":
    unittest.main()
