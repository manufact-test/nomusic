#!/usr/bin/env python3
"""Self-contained synthetic DEX CFG tests; no signed XAPK or vendor data."""
import unittest
from a1_trackid_cfg_track_alias import prove_original_track_receiver

TRACK="Lru/yandex/music/data/audio/o;"

class FakeDex:
    def __init__(self, register_size=4, ins_size=1, tries=0):
        self.meta={0:register_size,2:ins_size,6:tries}
    def u16(self,offset):
        return self.meta.get(offset,0)

class FakeAudit:
    @staticmethod
    def parse_types(sig):
        return [TRACK] if sig == "("+TRACK+")V" else (
            [TRACK,TRACK] if sig == "("+TRACK+TRACK+")V" else [])
    @staticmethod
    def written_register(op,w):
        if op == 0x54: return (w[0] >> 8) & 15
        if op == 0x12: return (w[0] >> 8) & 15
        if op == 0x0c: return w[0] >> 8
        return None

def move(op,w):
    if op==0x07:
        return ((w[0] >> 8) & 15, (w[0] >> 12) & 15)
    return None

def word_move(dst,src):
    return (0x07 | (dst << 8) | (src << 12),)

def check(ins,read_at,receiver=0,dex=None,signature=None):
    return prove_original_track_receiver(
        dex or FakeDex(), ("LGp0;","foo",signature or "("+TRACK+")V"),
        0x8,0,ins,read_at,receiver,FakeAudit,move)

class AliasCfgTests(unittest.TestCase):
    def test_all_branches_assign_exact_track(self):
        ins=[
            (0,0x38,(0x38,3)),              # if-eqz -> pc3
            (1,0x07,word_move(0,3)),
            (2,0x28,(0x28 | 2<<8,)),        # goto -> pc4
            (3,0x07,word_move(0,3)),
            (4,0x54,(0x54 | 1<<8,0)),
            (5,0x0e,(0x0e,))]
        self.assertEqual(check(ins,4),"CFG_EXACT_FORMAL_TRACK_RECEIVER")

    def test_branch_skipping_alias_kills_proof(self):
        ins=[
            (0,0x38,(0x38,2)),              # direct pc2 skips move
            (1,0x07,word_move(0,3)),
            (2,0x54,(0x54 | 1<<8,0)),
            (3,0x0e,(0x0e,))]
        self.assertEqual(check(ins,2),"CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN")

    def test_one_branch_replaces_receiver_with_other_object(self):
        ins=[
            (0,0x38,(0x38,3)),
            (1,0x07,word_move(0,3)),
            (2,0x28,(0x28 | 2<<8,)),
            (3,0x12,(0x12 | 0<<8,)),
            (4,0x54,(0x54 | 1<<8,0)),
            (5,0x0e,(0x0e,))]
        self.assertEqual(check(ins,4),"CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN")

    def test_cast_preserves_reference(self):
        ins=[
            (0,0x07,word_move(0,3)),
            (1,0x1f,(0x1f,0)),
            (2,0x54,(0x54 | 1<<8,0)),
            (3,0x0e,(0x0e,))]
        self.assertEqual(check(ins,2),"CFG_EXACT_FORMAL_TRACK_RECEIVER")

    def test_unmodelled_opcode_and_try_fail_closed(self):
        ins=[(0,0xff,(0xff,)),(1,0x54,(0x54 | 1<<8,0)),(2,0x0e,(0x0e,))]
        self.assertEqual(check(ins,1),"CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN")
        self.assertEqual(check(ins,1,dex=FakeDex(tries=1)),"CFG_UNSUPPORTED_METHOD")

    def test_packed_switch_all_paths_keep_track(self):
        # Encoded 31t switch at pc0 -> payload pc8, one target pc14.
        # Both case and default must write exact formal Track into v0.
        ins=[
            (0,0x2b,(0x2b,8,0)),
            (3,0x07,word_move(0,3)),
            (4,0x28,(0x28 | 11<<8,)),
            (5,0x00,(0,)),(6,0x00,(0,)),(7,0x00,(0,)),
            (8,0x00,(0x0100,1,0,0,14,0)),
            (14,0x07,word_move(0,3)),
            (15,0x54,(0x54 | 1<<8,0)),
            (16,0x0e,(0x0e,))]
        self.assertEqual(check(ins,8),"CFG_EXACT_FORMAL_TRACK_RECEIVER")
        # A case that skips its formal Track copy kills the claim.
        ins[7]=(14,0x12,(0x12,))
        self.assertEqual(check(ins,8),"CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN")

    def test_sparse_switch_and_filled_array_are_not_executable_alias_sources(self):
        # pc0 sparse switch references a one-case payload at pc8, target pc16.
        ins=[
            (0,0x2c,(0x2c,8,0)),
            (3,0x07,word_move(0,3)),
            (4,0x28,(0x28 | 13<<8,)),
            (5,0x00,(0,)),(6,0x00,(0,)),(7,0x00,(0,)),
            (8,0x00,(0x0200,1,1,0,16,0)),
            (14,0x00,(0,)),(15,0x00,(0,)),
            (16,0x07,word_move(0,3)),
            (17,0x54,(0x54 | 1<<8,0)),
            (18,0x0e,(0x0e,))]
        self.assertEqual(check(ins,11),"CFG_EXACT_FORMAL_TRACK_RECEIVER")

    def test_wrong_target_and_switch_fail_closed(self):
        ins=[(0,0x38,(0x38,9)),(1,0x54,(0x54,0))]
        self.assertEqual(check(ins,1),"CFG_UNSUPPORTED_FLOW")
        ins=[(0,0x2b,(0x2b,0,0)),(1,0x54,(0x54,0))]
        self.assertEqual(check(ins,1),"CFG_UNSUPPORTED_FLOW")

    def test_no_track_or_multiple_track_formals(self):
        ins=[(0,0x54,(0x54,0)),(1,0x0e,(0x0e,))]
        self.assertEqual(check(ins,0,signature="()V"),"CFG_TRACK_FORMAL_NOT_UNIQUE")
        self.assertEqual(check(ins,0,signature="("+TRACK+TRACK+")V"),
                         "CFG_TRACK_FORMAL_NOT_UNIQUE")

    def test_unreachable_read_is_not_proof(self):
        ins=[(0,0x28,(0x28 | 2<<8,)),(1,0x54,(0x54,0)),(2,0x0e,(0x0e,))]
        self.assertEqual(check(ins,1),"CFG_FIELD_READ_UNREACHABLE")

if __name__=="__main__":
    unittest.main()
