#!/usr/bin/env python3
"""Exact signed source mutator target fixtures, no guessed audio proof."""
import unittest
from exact_mediasource_player_sink import (
    SOURCE,PLAYER_METHODS,COMPOSITE_ADD,is_exact_mutator,EXACT_TARGETS
)


class SourcePlayerExactSinkTests(unittest.TestCase):
    def test_exact_source_typed_mutators(self):
        self.assertEqual(SOURCE,"LSl6;")
        self.assertIn(("LA14;","T","(LSl6;)V"),PLAYER_METHODS)
        self.assertIn(("Lp24;","e","(LSl6;J)V"),PLAYER_METHODS)
        self.assertTrue(is_exact_mutator(("Lp24;","T","(LSl6;)V")))

    def test_composite_is_not_player_setter(self):
        self.assertIn(COMPOSITE_ADD,EXACT_TARGETS)
        self.assertFalse(is_exact_mutator(COMPOSITE_ADD))
        self.assertFalse(is_exact_mutator(("LfH7;","V","(LOf6;)V")))

    def test_no_erased_list_or_data_factory_inference(self):
        self.assertFalse(is_exact_mutator(("LA14;","T","(Ljava/util/List;)V")))
        self.assertFalse(is_exact_mutator(("LA14;","T","(LOr2$a;)V")))


if __name__=="__main__":
    unittest.main()
