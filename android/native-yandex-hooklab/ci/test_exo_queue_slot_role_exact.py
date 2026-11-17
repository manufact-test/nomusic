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
            self.assertEqual(direct_getter([(0,0x54,[0x0,3]),(1,0x11,[0x0])],StubDex(),s),None)
            self.assertEqual(direct_getter([(0,0x54,[0x0,3]),(1,0x11,[0x0000])],StubDex(),s),None)
            # iget A=v1; return-object v1 -> identical direct field
            self.assertEqual(direct_getter([(0,0x54,[0x0100,3]),(1,0x11,[0x0100])],StubDex(),s),"SLOT_A")
            # branch destroys the direct proof
            self.assertIsNone(direct_getter([(0,0x54,[0x0100,3]),(1,0x32,[0]),(2,0x11,[0x0100])],StubDex(),s))
        finally: audit.field_id=old

if __name__=="__main__": unittest.main()
