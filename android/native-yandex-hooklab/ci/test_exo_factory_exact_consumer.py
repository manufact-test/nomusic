#!/usr/bin/env python3
"""Exact typed Exo factory scope, fail-closed fixtures."""
import unittest
from exo_factory_exact_consumer import (
    EXO_FACTORY, RDS_FACTORY, SOURCE_FACTORY_INTERFACE, related_method,
    LG_LB_BUILD, LL_LB_ADAPT, AS2_CONSTRUCTOR, EXACT_DIRECT_TARGETS,
)


class ExoFactoryExactConsumerTests(unittest.TestCase):
    def test_exact_factories_matched(self):
        self.assertTrue(related_method(EXO_FACTORY))
        self.assertTrue(related_method(RDS_FACTORY))

    def test_type_only_exact_factory_interface(self):
        self.assertTrue(related_method(("Lholder;", "x", "(" + SOURCE_FACTORY_INTERFACE + ")V")))
        self.assertTrue(related_method(("Lholder;", "y", "()" + SOURCE_FACTORY_INTERFACE)))
        self.assertTrue(related_method((SOURCE_FACTORY_INTERFACE, "for", "()LCC2;")))
        self.assertFalse(related_method(("Lholder;", "x", "(Ljava/lang/Object;)V")))

    def test_focused_adapter_targets_only(self):
        self.assertEqual(len(EXACT_DIRECT_TARGETS), 3)
        self.assertIn(LG_LB_BUILD, EXACT_DIRECT_TARGETS)
        self.assertIn(LL_LB_ADAPT, EXACT_DIRECT_TARGETS)
        self.assertIn(AS2_CONSTRUCTOR, EXACT_DIRECT_TARGETS)
        self.assertNotIn(("LfT2;", "equals", "(Ljava/lang/Object;)Z"), EXACT_DIRECT_TARGETS)

    def test_no_track_wrapper_or_mediaitem_false_bridge(self):
        self.assertFalse(related_method(("Lother;", "x", "(LtCa;)LOf6;")))
        self.assertFalse(related_method(("LsO7;", "Z", "(ILOf6;)V")))


if __name__ == "__main__":
    unittest.main()
