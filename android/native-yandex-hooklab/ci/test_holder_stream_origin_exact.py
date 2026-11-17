#!/usr/bin/env python3
import unittest
from holder_stream_origin_exact import scope_owner, scope_call, strict_scoped_alias_transition

class ExactHolderStreamScopeTest(unittest.TestCase):
    def test_exact_owner_scope(self):
        self.assertTrue(scope_owner("Lxh6;"))
        self.assertTrue(scope_owner("Lup1;"))
        self.assertFalse(scope_owner("Landroidx/media3/exoplayer/e;"))
        self.assertFalse(scope_owner("Ljava/lang/Object;"))
    def test_exact_register_move_retains_alias_and_field_store_does_not_clobber(self):
        before = frozenset((0,))
        moved = strict_scoped_alias_transition(None, 0x07, [0x0107], before)
        self.assertEqual(moved, frozenset((0, 1)))
        stored = strict_scoped_alias_transition(None, 0x5b, [0x105b, 0], moved)
        self.assertEqual(stored, moved)

    def test_branch_keeps_alias_but_instructions_with_dest_overwrite(self):
        before = frozenset((0,))
        after_branch = strict_scoped_alias_transition(None, 0x32, [0x0032, 0], before)
        self.assertEqual(after_branch, before)
        # const/4 writes v0: it must invalidate v0's identity alias.
        after_write = strict_scoped_alias_transition(None, 0x12, [0x0012], before)
        self.assertEqual(after_write, frozenset())

    def test_no_blanket_byte_sink_or_mediaitem(self):
        self.assertFalse(scope_call(("Lx;","read","(Ljava/nio/ByteBuffer;)I")))
        self.assertFalse(scope_call(("Lx;","getItem","()LOf6;")))
        self.assertTrue(scope_call(("Lwh6;","class","([LR29;)V")))
        self.assertTrue(scope_call(("Lxh6;","case","()J")))

if __name__=="__main__":unittest.main()
