#!/usr/bin/env python3
"""Exact native ExoPlayer engine holder caller only; no active audio inference."""
import unittest
from native_engine_period_queue_exact import (
    ENGINE,PERIOD_HOLDER,only_grounded_engine
)


class EnginePeriodQueueTests(unittest.TestCase):
    def test_one_exact_engine_method(self):
        self.assertTrue(only_grounded_engine((
            "Landroidx/media3/exoplayer/e;","break","()V")))
        self.assertEqual(PERIOD_HOLDER[0],"Lxh6;")

    def test_no_global_renderer_or_period_entry_census(self):
        self.assertFalse(only_grounded_engine((
            "Landroidx/media3/exoplayer/e;","break","(Ljava/lang/Object;)V")))
        self.assertFalse(only_grounded_engine((
            "Lp96;","transient","(LSl6$b;LrH2;J)Lo96;")))
        self.assertFalse(only_grounded_engine((
            "Landroidx/media3/exoplayer/d;","T0",
            "(Ljava/util/List;IJZ)V")))


if __name__=="__main__":
    unittest.main()
