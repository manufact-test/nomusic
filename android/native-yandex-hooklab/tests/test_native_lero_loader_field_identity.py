import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_lero_loader_field_identity import (
    basic_block_return_into_reader_ctor,constructor_source_field,
    loader_source_field_reads
)


class FakeDex:
    def __init__(self,words,methods=(),types=None,register_count=7,incoming=5):
        self.words=[0]*8+list(words)
        self.words[0]=register_count
        self.words[1]=incoming
        self.words[6]=len(words)
        self.methods=list(methods)
        self.types=types or {}
    def bounds(self,off,n):
        if off<0 or off+n>2*len(self.words):raise ValueError("BOUNDS")
    def u16(self,off):return self.words[off//2]
    def u32(self,off):return self.u16(off)|(self.u16(off+2)<<16)
    def method(self,i):return self.methods[i]
    def descriptor(self,i):return self.types.get(i,"Lother;")


class ExactLeroReaderFieldTests(unittest.TestCase):
    def test_Lga4_c_result_to_Lmb4_ctor_arg_one(self):
        methods=[
            ("Lga4;","c","()Lha4;"),
            ("Lmb4;","<init>","(Lha4;La58;[BLlb4;)V"),
        ]
        # invoke-virtual Lga4.c ; move-result-object v2;
        # new-instance v3; invoke-direct Lmb4.<init>{v3,v2,v4,v5,v6}
        dex=FakeDex([],methods)
        # DEX 35c: count 5, G=v6, C=v3, D=v2, E=v4, F=v5.
        # Simpler verify decoders by constructing direct instruction iterator
        from unittest.mock import patch as mock
        ins=[
            (0,0x6e,(0x106e,0,0x0001)),
            (3,0x0c,(0x020c,)),
            (4,0x22,(0x0322,1)),
            (6,0x70,(0x5670,1,0x5423)),
            (9,0x0e,(0x000e,))
        ]
        with mock("audit_native_lero_loader_field_identity.instructions",return_value=iter(ins)):
            rows=basic_block_return_into_reader_ctor(dex,0)
        self.assertTrue(rows[0]["source_to_reader_ctor_argument_basic_block_witness"])
        self.assertEqual(rows[0]["bounded_direct_target_events"][0]["source_argument_word"],1)

    def test_constructor_p1_written_to_exact_m48_slot(self):
        dex=FakeDex([0x235b,0,0x000e],register_count=7,incoming=5)
        key=("Lmb4;","Lm48;","private_slot")
        with patch("audit_native_lero_loader_field_identity.field_key",return_value=key):
            self.assertEqual(constructor_source_field(dex,0,("Lmb4;","<init>","()V")),key)

    def test_mismatching_field_does_not_identify_loader_source(self):
        dex=FakeDex([0x235b,0,0x000e],register_count=7,incoming=5)
        key=("Lmb4;","Lother;","private")
        with patch("audit_native_lero_loader_field_identity.field_key",return_value=key):
            self.assertIsNone(constructor_source_field(dex,0,("Lmb4;","<init>","()V")))

    def test_reader_field_get_cast_and_open_is_only_static(self):
        method=[("Lha4;","b","(La58;)J")]
        ins=[(0,0x54,(0x0854,0)),(2,0x1f,(0x081f,1)),
             (4,0x6e,(0x206e,0,0x0018)),(7,0x0e,(0x000e,))]
        dex=FakeDex([],methods=method,types={1:"Lha4;"})
        key=("Lmb4;","Lm48;","field_same")
        with patch("audit_native_lero_loader_field_identity.instructions",return_value=iter(ins)),\
             patch("audit_native_lero_loader_field_identity.field_key",return_value=key):
            result=loader_source_field_reads(dex,0,key)
        self.assertTrue(result[0]["subclass_cast_to_Lha4_within_four_instructions"])
        self.assertTrue(result[0]["same_instance_across_conditionals_not_proven"])

    def test_wrong_loader_field_ref_rejected_even_if_same_type(self):
        ins=[(0,0x54,(0x0854,0)),(2,0x1f,(0x081f,1))]
        dex=FakeDex([],types={1:"Lha4;"})
        key=("Lmb4;","Lm48;","slot-A")
        other=("Lmb4;","Lm48;","slot-B")
        with patch("audit_native_lero_loader_field_identity.instructions",return_value=iter(ins)),\
             patch("audit_native_lero_loader_field_identity.field_key",return_value=other):
            self.assertEqual(loader_source_field_reads(dex,0,key),[])


if __name__=="__main__":
    unittest.main()
