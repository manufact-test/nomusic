#!/usr/bin/env python3
"""Lock the exact A0 method; refuse unrelated List/MediaItem paths."""
import unittest
from exoplayer_a0_source_holder_exact import (
    TARGET,PARENT,SOURCE,exact_source_handoff
)


class ExactSourceHolderTests(unittest.TestCase):
    def test_only_proven_player_list_methods_are_in_scope(self):
        self.assertTrue(exact_source_handoff(TARGET))
        self.assertTrue(exact_source_handoff(PARENT))
        self.assertEqual(TARGET,(
            "Landroidx/media3/exoplayer/d;","A0",
            "(Ljava/util/List;I)Ljava/util/ArrayList;"))
        self.assertEqual(SOURCE,"LSl6;")

    def test_ambiguous_collection_not_proof(self):
        self.assertFalse(exact_source_handoff((
            "Ljava/util/List;","add","(Ljava/lang/Object;)Z")))
        self.assertFalse(exact_source_handoff((
            "Landroidx/media3/exoplayer/d;","A0",
            "(Ljava/lang/Object;I)Ljava/util/ArrayList;")))
        self.assertFalse(exact_source_handoff((
            "Landroidx/media3/exoplayer/d;","e","(LOf6;J)V")))


if __name__=="__main__":
    unittest.main()
