#!/usr/bin/env python3
"""Exact source-setter-only negative/positive fixtures."""
import unittest
from exoplayer_source_commit_exact import (
    INTERFACE,SOURCE,SOURCE_SETTER,SOURCE_SETTER_NO_POS,
    PLAYER_GETTER,exact_source_setter,declared_source_setter,
)


class ExactExoplayerSourceCommitTests(unittest.TestCase):
    def test_exact_typed_source_signature(self):
        self.assertEqual(SOURCE,"LSl6;")
        self.assertTrue(exact_source_setter(("LrD0;","e","(LSl6;J)V")))
        self.assertTrue(declared_source_setter(("Lp24;","T","(LSl6;)V")))

    def test_does_not_infer_media_item_or_erased_source(self):
        self.assertFalse(exact_source_setter(("LrD0;","e","(LOf6;J)V")))
        self.assertFalse(declared_source_setter(("LA14;","e","(Ljava/lang/Object;J)V")))
        self.assertFalse(declared_source_setter(("LfH7;","V","(LOf6;)V")))

    def test_player_interface_and_exact_receiver(self):
        self.assertEqual(INTERFACE,"Landroidx/media3/exoplayer/ExoPlayer;")
        self.assertEqual(PLAYER_GETTER,(
            "LA14;","v0","()Landroidx/media3/exoplayer/ExoPlayer;"))


if __name__=="__main__":
    unittest.main()
