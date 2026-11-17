#!/usr/bin/env python3
"""Targeted parser contract tests; never infer playback from SDK naming."""
import unittest
from exact_mediasource_lsl6_handoff import (
    NATIVE_SOURCE_IFACE, NATIVE_SOURCE_CLASS, NATIVE_SOURCE_BASE,
    FACTORY_ADAPTER, PUBLISHER_SOURCE_CONSTRUCTOR, EXACT_TARGETS,
    source_typed_method, PLAYER_OWNERS,
)


class ExactMediaSourceHandoffTests(unittest.TestCase):
    def test_grounded_subtype_chain_and_factory(self):
        self.assertEqual(NATIVE_SOURCE_IFACE, "LSl6;")
        self.assertEqual(NATIVE_SOURCE_CLASS, "LIr8;")
        self.assertEqual(NATIVE_SOURCE_BASE, "LdC0;")
        self.assertIn(FACTORY_ADAPTER, EXACT_TARGETS)
        self.assertIn(PUBLISHER_SOURCE_CONSTRUCTOR, EXACT_TARGETS)

    def test_exact_type_not_mediaitem_or_guess(self):
        self.assertTrue(source_typed_method(("LSl6;", "x", "()V")))
        self.assertTrue(source_typed_method(("Lfoo;", "x", "(LSl6;)V")))
        self.assertFalse(source_typed_method(("Lfoo;", "x", "(LOf6;)V")))
        self.assertFalse(source_typed_method(("Lfoo;", "x", "(Ljava/util/List;)V")))

    def test_no_synthetic_player_or_runtime_assertions(self):
        self.assertIn("LfH7;", PLAYER_OWNERS)
        self.assertNotIn("LIr8;", PLAYER_OWNERS)
        self.assertFalse(source_typed_method(
            ("LfH7;", "setMediaSource", "(Ljava/lang/Object;)V")
        ))


if __name__=="__main__":
    unittest.main()
