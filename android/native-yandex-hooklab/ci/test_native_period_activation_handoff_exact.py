#!/usr/bin/env python3
"""Fail-closed exact signed native period activation candidates only."""
import unittest
from native_period_activation_handoff_exact import (
    PERIOD_FACTORY, PERIOD_ADAPTER, PERIOD_HOLDER_CTOR, PERIOD_WRAPPER_CTOR,
    EXACT_METHODS, only_exact_entry,
)


class NativePeriodActivationTests(unittest.TestCase):
    def test_exact_signed_period_factory_and_two_callers(self):
        self.assertEqual(len(EXACT_METHODS), 4)
        self.assertIn(PERIOD_FACTORY, EXACT_METHODS)
        self.assertIn(PERIOD_ADAPTER, EXACT_METHODS)
        self.assertIn(PERIOD_HOLDER_CTOR, EXACT_METHODS)
        self.assertIn(PERIOD_WRAPPER_CTOR, EXACT_METHODS)
        self.assertTrue(only_exact_entry(PERIOD_ADAPTER))

    def test_no_generic_media_period_or_list_census(self):
        self.assertFalse(only_exact_entry((
            "Landroidx/media3/exoplayer/d;", "T0",
            "(Ljava/util/List;IJZ)V"
        )))
        self.assertFalse(only_exact_entry((
            "Lxh6;", "<init>", "(Ljava/lang/Object;)V"
        )))
        self.assertFalse(only_exact_entry((
            "LrD0;", "E", "()LOf6;"
        )))

    def test_witness_is_not_runtime_audible_claim(self):
        self.assertEqual(PERIOD_FACTORY[2], "(LSl6$b;LrH2;J)Lo96;")
        self.assertEqual(PERIOD_ADAPTER[2], "(LSl6$b;LrH2;J)Lwh6;")


if __name__ == "__main__":
    unittest.main()
