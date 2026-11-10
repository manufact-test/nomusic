import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_ga4_field_receiver import (
    type_provenance_writes, direct_field_accesses, field_key
)


class FakeDex:
    def __init__(self,code,methods=()):
        self.words=[0]*8+code
        self.words[6]=len(code)
        self.methods=list(methods)
    def bounds(self,off,size):
        if off<0 or off+size>len(self.words)*2:raise ValueError("BOUNDS")
    def u16(self,offset):
        return self.words[offset//2]
    def u32(self,offset):
        return self.u16(offset)|(self.u16(offset+2)<<16)
    def method(self,i):
        return self.methods[i]
    def descriptor(self,idx):
        return {1:"Lzcd;",2:"Le48;"}.get(idx,"Lother;")


class FieldReceiverTests(unittest.TestCase):
    def test_constructor_provenance_uses_identical_register_and_slot(self):
        # new-instance v0,Lzcd; / invoke-direct v0 / iput-object v0,v1,field0
        code=[0x0022,1, 0x1070,0,0, 0x105b,0, 0x000e]
        dex=FakeDex(code,[("Lzcd;","<init>","()V")])
        key=("Lga4;","Le48;","private_field_never_export")
        with patch("audit_native_ga4_field_receiver.field_key",return_value=key):
            res=type_provenance_writes(dex,0,{key})
        self.assertEqual(res[0]["new_instance_type_on_same_unbranched_register"],
                         "Lzcd;")
        self.assertFalse(res[0]["has_branch_or_exception_uncertainty"])
        self.assertFalse(res[0]["constructor_instance_bound_to_live_receiver"])

    def test_unknown_constructor_instance_not_inferred(self):
        code=[0x105b,0,0x000e]
        dex=FakeDex(code)
        key=("Lga4;","Le48;","private")
        with patch("audit_native_ga4_field_receiver.field_key",return_value=key):
            res=type_provenance_writes(dex,0,{key})
        self.assertEqual(res[0]["new_instance_type_on_same_unbranched_register"],
                         "unknown")

    def test_exact_read_reg_to_interface_invocation(self):
        key=("Lga4;","Le48;","private")
        # iget-object v2,v0,field0; invoke-interface {v2} Le48.a
        code=[0x0254,0,0x1072,0,0x0002,0x000e]
        dex=FakeDex(code,[("Le48;","a","()Lm48;")])
        with patch("audit_native_ga4_field_receiver.field_key",return_value=key):
            res=direct_field_accesses(dex,0,{key})
        self.assertTrue(res[0]["value_register_directly_consumed_by_Le48_a"])

    def test_unrelated_register_or_field_not_authoritative(self):
        key=("Lga4;","Le48;","private")
        code=[0x0254,0,0x1072,0,0x0003,0x000e]
        dex=FakeDex(code,[("Le48;","a","()Lm48;")])
        with patch("audit_native_ga4_field_receiver.field_key",return_value=key):
            res=direct_field_accesses(dex,0,{key})
        self.assertFalse(res[0]["value_register_directly_consumed_by_Le48_a"])


if __name__=="__main__":
    unittest.main()
