import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_ga4_field2_value_origins import (
    find_definition,exact_store_witnesses,destination_reg,source_register
)


class FakeDex:
    def __init__(self,words,methods=(),types=None):
        self.words=[0]*8+words
        self.words[6]=len(words)
        self.methods=list(methods)
        self.types=types or {}
    def bounds(self,off,size):
        if off<0 or off+size>len(self.words)*2:
            raise ValueError("BAD BOUNDS")
    def u16(self,offset):
        return self.words[offset//2]
    def u32(self,offset):
        return self.u16(offset)|(self.u16(offset+2)<<16)
    def descriptor(self,i):
        return self.types[i]
    def method(self,i):
        return self.methods[i]


class ExactWriterProvenanceTests(unittest.TestCase):
    def test_writer_after_constructor_from_same_register(self):
        # new-instance v2, Lya4; ; iput-object v2,v1,field0
        code=[0x0222,1,0x125b,0,0x000e]
        dex=FakeDex(code,types={1:"Lya4;"})
        key=("Lga4;","Le48;","private")
        with patch("audit_native_ga4_field2_value_origins.field_key",return_value=key):
            rows=exact_store_witnesses(dex,0,{key})
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["value_provenance"]["kind"],"new_instance")
        self.assertEqual(rows[0]["value_provenance"]["inferred_type"],"Lya4;")
        self.assertFalse(rows[0]["exact_current_audio_receiver_proven"])

    def test_cast_does_not_invent_a_concrete_instance(self):
        # invoke-static{} foo -> result v2 -> check-cast v2 Le48; -> store v2
        callee=("Lfoo;","a","()Ljava/lang/Object;")
        code=[0x0071,0,0, 0x020c, 0x021f,2, 0x125b,0,0x000e]
        dex=FakeDex(code,[callee],{2:"Le48;"})
        key=("Lga4;","Le48;","private")
        with patch("audit_native_ga4_field2_value_origins.field_key",return_value=key):
            row=exact_store_witnesses(dex,0,{key})[0]
        self.assertEqual(row["value_provenance"]["kind"],"invoke_result")
        self.assertEqual(row["value_provenance"]["producer"],"Lfoo;->a")
        self.assertIn("Le48;",row["value_provenance"]["cast_type_hints"])
        self.assertFalse(row["value_provenance"]["direct_producer_unambiguous"])

    def test_move_object_alias_reaches_field_read(self):
        # iget-object v2,v0,field0 ; move-object v3,v2; iput-object v3,v1,field0
        code=[0x0254,0, 0x2307, 0x135b,0,0x000e]
        dex=FakeDex(code)
        key=("Lga4;","Le48;","private")
        with patch("audit_native_ga4_field2_value_origins.field_key",return_value=key):
            row=exact_store_witnesses(dex,0,{key})[0]
        self.assertEqual(row["value_provenance"]["kind"],"instance_field_read")
        self.assertEqual(row["value_provenance"]["register_copy_hops"],1)

    def test_branch_barrier_prevents_cross_path_conclusions(self):
        code=[0x0222,1,0x0028,0x125b,0,0x000e]
        dex=FakeDex(code,types={1:"Lya4;"})
        key=("Lga4;","Le48;","private")
        with patch("audit_native_ga4_field2_value_origins.field_key",return_value=key):
            row=exact_store_witnesses(dex,0,{key})[0]
        self.assertEqual(row["value_provenance"]["kind"],"control_flow_boundary")

    def test_22c_and_11n_destinations_mask_register_nibbles(self):
        self.assertEqual(destination_reg(0x54,(0xf254,0)),2)
        self.assertEqual(destination_reg(0x12,(0xf212,)),2)
        self.assertEqual(source_register(0x5b,(0xf35b,0)),3)

    def test_cross_field_does_not_make_same_instance(self):
        dex=FakeDex([0x0222,1,0x125b,0,0x000e],types={1:"Lya4;"})
        a=("Lga4;","Le48;","private_slot_a")
        b=("Lga4;","Le48;","private_slot_b")
        with patch("audit_native_ga4_field2_value_origins.field_key",return_value=a):
            self.assertEqual(exact_store_witnesses(dex,0,{b}),[])


if __name__=="__main__":
    unittest.main()
