#!/usr/bin/env python3
"""Fail-closed tests for exact, 2025-only secondary native renderer caller."""
import unittest
from secondary_renderer_attach_caller_owner_exact import (
    SECONDARY, ATTACH, ATTACH_INTERFACE, match_direct_secondary_invoke,
    classify_secondary_invoke,
)

class SecondaryCallerExactTests(unittest.TestCase):
    def test_secondary_2025_full_descriptor(self):
        self.assertEqual(SECONDARY,(
            "Landroidx/media3/exoplayer/b;", "super",
            "(LlQ8;[LSr4;LR29;ZZJJLSl6$b;)V"))
        self.assertTrue(match_direct_secondary_invoke(SECONDARY))
        self.assertEqual(classify_secondary_invoke(SECONDARY),"EXACT_SECONDARY")
    def test_wrong_name_owner_and_stream_rejected(self):
        self.assertFalse(match_direct_secondary_invoke((
            "Landroidx/media3/exoplayer/b;","package",SECONDARY[2])))
        self.assertFalse(match_direct_secondary_invoke((
            "Landroidx/media3/exoplayer/k;","super",SECONDARY[2])))
        self.assertFalse(match_direct_secondary_invoke((
            SECONDARY[0],SECONDARY[1],SECONDARY[2].replace("LR29;","Ljava/lang/Object;"))))
        self.assertFalse(match_direct_secondary_invoke((
            SECONDARY[0],SECONDARY[1],SECONDARY[2].replace("LlQ8;","Lwrong;"))))
    def test_2026_names_not_accidentally_accepted(self):
        self.assertFalse(match_direct_secondary_invoke((
            "Landroidx/media3/exoplayer/b;","super",
            "(Ljava/lang/Object;[LSr4;LR29;ZZJJLSl6$b;)V")))
    def test_true_attach_not_misclassified_as_secondary(self):
        self.assertEqual(classify_secondary_invoke(ATTACH),"EXACT_ATTACH")
        self.assertEqual(classify_secondary_invoke(ATTACH_INTERFACE),"EXACT_ATTACH")
        self.assertNotEqual(classify_secondary_invoke(ATTACH),"EXACT_SECONDARY")
    def test_unknown_other_fail_closed(self):
        self.assertEqual(classify_secondary_invoke(("Lx;","foo","()V")),"OTHER")
        self.assertEqual(classify_secondary_invoke(("Lx;","super",SECONDARY[2])),"OTHER")

if __name__=="__main__":unittest.main()
