import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_source_factory_register_handoff import (
    concrete_invoke_result_to_field,source_constructor_argument_flow
)


class FakeDex:
    def __init__(self,code,methods=()):
        self.words=[0]*8+list(code)
        self.words[6]=len(code)
        self.methods=list(methods)
    def bounds(self,offset,size):
        if offset<0 or offset+size>len(self.words)*2:raise ValueError("DEX_BOUNDS")
    def u16(self,offset):return self.words[offset//2]
    def u32(self,offset):return self.u16(offset)|(self.u16(offset+2)<<16)
    def method(self,idx):return self.methods[idx]
    def descriptor(self,idx):return {1:"Lga4;"}[idx]


class SourceFactoryRegisterHandoffTests(unittest.TestCase):
    def test_signed_factory_return_exact_primary_field_store(self):
        methods=[("Lcq7;","A","(Leyc;Lthq;)Luiq;"),
                 ("Lga4;","<init>","()V")]
        # invoke-static{v0,v1} A, move-result v5, new-instance v6,
        # invoke-direct{v6}, iput-object v5,v6, exact PRIMARY Le48 slot
        code=[0x2071,0,0x0010, 0x050c, 0x0622,1,
              0x1070,1,0x0006, 0x655b,0, 0x000e]
        key=("Lga4;","Le48;","original_slot")
        with patch("audit_native_source_factory_register_handoff.field_key",
                   return_value=key):
            result=concrete_invoke_result_to_field(
                FakeDex(code,methods),0,"Lcq7;","A",key)
        self.assertTrue(result[0]["basic_block_register_link_observed"])
        self.assertEqual(result[0]["direct_primary_store_candidates"][0]["sink"],
                         "exact_primary_le48_iput")
        self.assertFalse(result[0]["across_coroutine_and_decoder_proven"])

    def test_unrelated_field_not_counted(self):
        methods=[("Lcq7;","A","(Leyc;Lthq;)Luiq;")]
        code=[0x0071,0,0,0x050c,0x655b,0,0x000e]
        key=("Lga4;","Le48;","correct")
        with patch("audit_native_source_factory_register_handoff.field_key",
                   return_value=("Lga4;","Le48;","other")):
            result=concrete_invoke_result_to_field(FakeDex(code,methods),0,
                                                   "Lcq7;","A",key)
        self.assertFalse(result[0]["basic_block_register_link_observed"])

    def test_register_overwrite_prevents_primary_link(self):
        methods=[("Lcq7;","A","(Leyc;Lthq;)Luiq;")]
        code=[0x0071,0,0,0x050c,0x0512,0x655b,0,0x000e]
        key=("Lga4;","Le48;","original")
        with patch("audit_native_source_factory_register_handoff.field_key",
                   return_value=key):
            result=concrete_invoke_result_to_field(FakeDex(code,methods),0,
                                                   "Lcq7;","A",key)
        self.assertFalse(result[0]["basic_block_register_link_observed"])

    def test_branch_between_factory_and_field_stops_proof(self):
        methods=[("Lcq7;","A","(Leyc;Lthq;)Luiq;")]
        code=[0x0071,0,0,0x050c,0x0028,0x655b,0,0x000e]
        key=("Lga4;","Le48;","original")
        with patch("audit_native_source_factory_register_handoff.field_key",
                   return_value=key):
            result=concrete_invoke_result_to_field(FakeDex(code,methods),0,
                                                   "Lcq7;","A",key)
        self.assertFalse(result[0]["basic_block_register_link_observed"])

    def test_source_return_to_lha4_ctor_argument_position(self):
        methods=[("Le48;","a","()Lm48;"),
                 ("Lha4;","<init>","(Lq94;Lm48;Lm48;Lc48;Lsa4;ILlno;I)V")]
        # interface{v2}→move-result v3→invoke-direct/range {v0..v8}
        code=[0x1072,0,0x0002,0x030c,
              0x0976,1,0,0x000e]
        result=source_constructor_argument_flow(FakeDex(code,methods),0)
        self.assertEqual(result[0]["same_basic_block_construction_argument_sites"][0]
                         ["constructor_argument_word"],3)
        self.assertFalse(result[0]["polymorphic_receiver_class_proven"])

    def test_source_ctor_link_invalidated_by_branch(self):
        methods=[("Le48;","a","()Lm48;"),
                 ("Lha4;","<init>","(Lq94;Lm48;Lm48;Lc48;Lsa4;ILlno;I)V")]
        code=[0x1072,0,0x0002,0x030c,0x0028,
              0x0976,1,0,0x000e]
        result=source_constructor_argument_flow(FakeDex(code,methods),0)
        self.assertFalse(result[0]["same_basic_block_construction_argument_sites"])


if __name__=="__main__":
    unittest.main()
