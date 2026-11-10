import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_lero_async_case import (
    int_constant_from_words,nearby_constructor_tag,switch_table_for_ins,
    branch_contains_loader,constructor_tag_field
)


class FakeDex:
    def __init__(self,methods=(),types=()):
        self.methods=list(methods)
        self.types={i:t for i,t in enumerate(types)}
    def method(self,idx):return self.methods[idx]
    def descriptor(self,i):return self.types.get(i,"other")


class SignedAsyncCaseTests(unittest.TestCase):
    def test_const4_signed_selector(self):
        self.assertEqual(int_constant_from_words(0x12,(0xf212,)),-1)
        self.assertEqual(int_constant_from_words(0x12,(0x2212,)),2)
        self.assertEqual(int_constant_from_words(0x13,(0x0113,0xfffe)),-2)
        self.assertIsNone(int_constant_from_words(0x11,(0x0111,)))

    def test_constructor_uses_literal_from_same_block_only(self):
        dex=FakeDex([("Lwq7;","<init>","(ILjava/lang/Object;)V")])
        # new-instance v1; const/4 v2,4; invoke-direct {v1,v2,v3}
        ins=[(0,0x22,(0x0122,5)),(2,0x12,(0x4212,)),
             (3,0x70,(0x3070,0,0x0321))]
        record=nearby_constructor_tag(dex,ins,2)
        self.assertEqual(record["tag"],4)
        self.assertTrue(record["single_basic_block"])
        self.assertEqual(record["arg_coords"],[1,2,3])

    def test_branch_barrier_cannot_prove_constructor_tag(self):
        dex=FakeDex([("Lwq7;","<init>","(ILjava/lang/Object;)V")])
        ins=[(0,0x12,(0x4212,)),(1,0x38,(0x0038,4)),
             (3,0x70,(0x3070,0,0x0321))]
        row=nearby_constructor_tag(dex,ins,2)
        self.assertIsNone(row["tag"])

    def test_exact_packed_switch_case_maps_to_target_pc(self):
        # packed-switch v0,+5, then block A at pc3, block B at pc5,
        # payload at pc8, first key 4 targets (3,5) relative to switch pc0
        ins=[
            (0,0x2b,(0x002b,8,0)),
            (3,0x0e,(0x000e,)),(4,0x0e,(0x000e,)),
            (5,0x0e,(0x000e,)),
            (8,0,(0x0100,2,4,0,3,0,5,0)),
        ]
        table=switch_table_for_ins(ins,0)
        self.assertEqual(table[4],3)
        self.assertEqual(table[5],5)
        self.assertNotIn(6,table)

    def test_sparse_switch_exact_key_lookup(self):
        ins=[(0,0x2c,(0x002c,7,0)),
             (3,0x0e,(0x000e,)),(5,0x0e,(0x000e,)),
             (7,0,(0x0200,2,3,0,10,0,3,0,5,0))]
        self.assertEqual(switch_table_for_ins(ins,0),{3:3,10:5})

    def test_wrong_payload_kind_is_not_accepted(self):
        ins=[(0,0x2b,(0x002b,7,0)),
             (7,0,(0x0200,1,0,0,3,0))]
        with self.assertRaisesRegex(Exception,"SWITCH_PAYLOAD_KIND"):
            switch_table_for_ins(ins,0)

    def test_loader_case_requires_lero_cast_and_exact_lmb4_field_read(self):
        methods=[("Lmb4;","a","()V")]
        dex=FakeDex(methods,["Lero;"])
        ins=[(3,0x54,(0x0054,1)),
             (5,0x1f,(0x001f,0)),
             (7,0x54,(0x0054,2)),
             (9,0x70,(0x1070,0,0)),
             (12,0x0e,(0x000e,))]
        with patch("audit_native_lero_async_case.field_key",
                   side_effect=[
                       ("Lwq7;","Ljava/lang/Object;","private"),
                       ("Lero;","Lmb4;","private")
                   ]):
            self.assertTrue(branch_contains_loader(dex,ins,3))
        with patch("audit_native_lero_async_case.field_key",
                   side_effect=[
                       ("Lwq7;","Ljava/lang/Object;","private"),
                       ("Lother;","Lmb4;","private")
                   ]):
            self.assertFalse(branch_contains_loader(dex,ins,3))

    def test_exact_constructor_tag_field_not_object_field(self):
        dex=FakeDex()
        ins=[
            (0,0x59,(0x1259,1)), # iput v2,v1,int-tag
            (2,0x5b,(0x135b,2)), # iput-object v3,v1, object
        ]
        with patch("audit_native_lero_async_case.field_key",return_value=("Lwq7;","I","private")):
            self.assertEqual(constructor_tag_field(dex,ins,2),("Lwq7;","I","private"))


if __name__=="__main__":
    unittest.main()
