#!/usr/bin/env python3
"""Fail-closed scoped native ExoPlayer queue-slot audit fixtures."""
import unittest
from exo_queue_slot_role_exact import QUEUE, HOLDER, ENGINE, slot_field, direct_getter

class StubDex:
    def __init__(self): self.fields={3:(QUEUE,"hidden_a",HOLDER),4:(QUEUE,"hidden_b",HOLDER)}
    def __repr__(self): return "StubDex"
    def method(self, idx): raise AssertionError("not used")

class SlotRoleTests(unittest.TestCase):
    def test_typed_field_only(self):
        from exo_queue_slot_role_exact import audit
        old=audit.field_id
        audit.field_id=lambda d,i: (QUEUE,"internal",HOLDER) if i==3 else ("LX;","other",HOLDER)
        try:
            self.assertEqual(slot_field(StubDex(),0x54,[0x10,3]),(QUEUE,"internal",HOLDER))
            self.assertIsNone(slot_field(StubDex(),0x54,[0x10,4]))
            self.assertIsNone(slot_field(StubDex(),0x55,[0x10,3]))
        finally: audit.field_id=old

    def test_no_false_current_on_unrelated_return(self):
        from exo_queue_slot_role_exact import audit
        old=audit.field_id
        audit.field_id=lambda d,i: (QUEUE,"hidden_a",HOLDER)
        try:
            s={(QUEUE,"hidden_a",HOLDER):"SLOT_A"}
            self.assertEqual(direct_getter([(0,0x54,[0x0,3]),(1,0x11,[0x0])],StubDex(),s),"SLOT_A")
            self.assertEqual(direct_getter([(0,0x54,[0x0,3]),(1,0x11,[0x0100])],StubDex(),s),None)
            # iget A=v1; return-object v1 -> identical direct field
            self.assertEqual(direct_getter([(0,0x54,[0x0100,3]),(1,0x11,[0x0100])],StubDex(),s),"SLOT_A")
            # branch destroys the direct proof
            self.assertIsNone(direct_getter([(0,0x54,[0x0100,3]),(1,0x32,[0]),(2,0x11,[0x0100])],StubDex(),s))
        finally: audit.field_id=old

class SignedSlotBWriterCensusTests(unittest.TestCase):
    def test_exact_five_sites_only(self):
        from exo_queue_slot_role_exact import (SIGNED_SLOT_B_DIRECT_WRITES,
            validate_signed_slot_b_direct_writes)
        proven=validate_signed_slot_b_direct_writes(list(SIGNED_SLOT_B_DIRECT_WRITES))
        self.assertEqual(proven["publisher_base_direct_iput_object_site_count"],5)
        self.assertTrue(proven["bounded_exact_site_proven"])
        self.assertFalse(proven["currently_selected_track_or_queue_epoch_proven"])
        self.assertFalse(proven["reflective_or_native_mutations_excluded"])

    def test_extra_missing_duplicate_and_pc_drift_fail_closed(self):
        from exo_queue_slot_role_exact import (SIGNED_SLOT_B_DIRECT_WRITES,
            validate_signed_slot_b_direct_writes)
        sites=list(SIGNED_SLOT_B_DIRECT_WRITES)
        for altered in (
            sites[:-1],
            sites+[sites[0]],
            sites+[(QUEUE,"unexpected","()V",999)],
            [(*sites[0][:3],sites[0][3]+1)]+sites[1:],
        ):
            with self.subTest(altered=altered):
                with self.assertRaisesRegex(ValueError,"QUEUE_SIGNED_SLOT_B_DIRECT_WRITES_CHANGED"):
                    validate_signed_slot_b_direct_writes(altered)

class SignedSlotBProvenanceTests(unittest.TestCase):
    """Tiny synthetic DEX instructions: no publisher method values in tests."""
    def _w(self,op,val,receiver):
        return (receiver<<12)|(val<<8)|op

    def _fixture(self):
        from exo_queue_slot_role_exact import QUEUE,HOLDER,ENGINE
        w=self._w
        # Fake IDs are arbitrary. Field names are synthetic, not private.
        fields={1:(QUEUE,"a",HOLDER),2:(QUEUE,"b",HOLDER),
                3:(QUEUE,"c",HOLDER),4:(QUEUE,"d",HOLDER),
                5:(HOLDER,"next",HOLDER),6:(QUEUE,"other","I"),
                7:(HOLDER,"different",HOLDER)}
        scripts={
            1:{305:(0x5b,(w(0x5b,3,2),1)),
               307:(0x5b,(w(0x5b,3,2),2)),
               309:(0x5b,(w(0x5b,3,2),3)),
               311:(0x5b,(w(0x5b,15,2),6)),
               313:(0x5b,(w(0x5b,3,2),4)),
               652:(0x54,(w(0x54,3,9),2)),
               654:(0x71,(0x71,1,0)),
               657:(0x54,(w(0x54,3,3),5)),
               659:(0x5b,(w(0x5b,3,9),2))},
            2:{0:(0x54,(w(0x54,0,3),1)),
               6:(0x54,(w(0x54,2,3),2)),
               8:(0x33,(w(0x33,0,2),6)),
               10:(0x54,(w(0x54,2,0),5)),
               12:(0x5b,(w(0x5b,2,3),2)),
               49:(0x54,(w(0x54,0,3),1)),
               51:(0x54,(w(0x54,0,0),5)),
               53:(0x5b,(w(0x5b,0,3),1))},
            3:{19:(0x54,(w(0x54,0,2),2)),
               21:(0x33,(w(0x33,3,0),9)),
               23:(0x54,(w(0x54,0,2),1)),
               25:(0x5b,(w(0x5b,0,2),2))},
            4:{30:(0x12,(0x0012,)),
               31:(0x5b,(w(0x5b,0,3),1)),
               33:(0x5b,(w(0x5b,0,3),4)),
               35:(0x5b,(w(0x5b,0,3),2)),
               37:(0x5b,(w(0x5b,0,3),3))},
        }
        stub=object()
        targets={
            ENGINE:(stub,0,1),
            (QUEUE,"if","()Lxh6;"):(stub,0,2),
            (QUEUE,"while","(Lxh6;)I"):(stub,0,3),
            (QUEUE,"for","()V"):(stub,0,4),
        }
        slots={fields[i]:"SLOT_"+letter for i,letter in
               ((1,"A"),(2,"B"),(3,"C"),(4,"D"))}
        return scripts,fields,targets,slots

    def _prove(self,scripts,fields,targets,slots):
        from exo_queue_slot_role_exact import (
            verify_signed_slot_b_local_provenance,audit)
        from unittest.mock import patch
        with patch.object(audit,"instructions",
                side_effect=lambda _dex,off: [
                    (pc,op,w) for pc,(op,w) in scripts[off].items()]), \
             patch.object(audit,"field_id",
                side_effect=lambda _dex,index: fields[index]):
            return verify_signed_slot_b_local_provenance(targets,slots)

    def test_five_source_categories_without_epoch_claim(self):
        scripts,fields,targets,slots=self._fixture()
        result=self._prove(scripts,fields,targets,slots)
        self.assertEqual(
            [row["origin"] for row in result["exact_writer_local_reference_origin_categories"]],
            ["INITIAL_SAME_HOLDER_REFERENCE",
             "OLD_SLOT_B_HOLDER_SUCCESSOR",
             "FRONT_HOLDER_SUCCESSOR_CONDITIONAL",
             "SLOT_A_REFERENCE_CONDITIONAL",
             "ZERO_NULL_REFERENCE"])
        self.assertFalse(result["whole_program_queue_epoch_proven"])
        self.assertFalse(result["runtime_selected_edition_proven"])

    def test_wrong_branch_field_register_successor_and_zero_fail_closed(self):
        base,fields,targets,slots=self._fixture()
        from copy import deepcopy
        variants=[]
        w=self._w
        for scope,pc,replacement in (
            (1,307,(0x5b,(w(0x5b,1,2),2))),
            (1,657,(0x54,(w(0x54,3,3),7))),
            (2,8,(0x33,(w(0x33,0,2),7))),
            (2,12,(0x5b,(w(0x5b,1,3),2))),
            (3,23,(0x54,(w(0x54,0,2),3))),
            (4,30,(0x12,(0x1012,))),
        ):
            changed=deepcopy(base);changed[scope][pc]=replacement
            variants.append((scope,pc,changed))
        for scope,pc,changed in variants:
            with self.subTest(scope=scope,pc=pc):
                with self.assertRaisesRegex(ValueError,"SLOT_B_PROVENANCE_"):
                    self._prove(changed,fields,targets,slots)

if __name__=="__main__": unittest.main()
