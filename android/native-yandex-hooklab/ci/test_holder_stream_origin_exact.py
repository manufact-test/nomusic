#!/usr/bin/env python3
import unittest
from holder_stream_origin_exact import scope_owner,scope_call

class ExactHolderStreamScopeTest(unittest.TestCase):
    def test_exact_owner_scope(self):
        self.assertTrue(scope_owner("Lxh6;"))
        self.assertTrue(scope_owner("Lup1;"))
        self.assertFalse(scope_owner("Landroidx/media3/exoplayer/e;"))
        self.assertFalse(scope_owner("Ljava/lang/Object;"))
    def test_no_blanket_byte_sink_or_mediaitem(self):
        self.assertFalse(scope_call(("Lx;","read","(Ljava/nio/ByteBuffer;)I")))
        self.assertFalse(scope_call(("Lx;","getItem","()LOf6;")))
        self.assertTrue(scope_call(("Lwh6;","class","([LR29;)V")))
        self.assertTrue(scope_call(("Lxh6;","case","()J")))

if __name__=="__main__":unittest.main()
