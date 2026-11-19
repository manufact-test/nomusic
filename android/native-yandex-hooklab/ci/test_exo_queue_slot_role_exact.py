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

if __name__=="__main__": unittest.main()
