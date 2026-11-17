#!/usr/bin/env python3
import unittest
from lp96_media_period_entry_exact import TARGET,period_target,PERIOD,SOURCE


class ExactPeriodEntryTests(unittest.TestCase):
    def test_one_exact_signed_lp96_candidate(self):
        self.assertTrue(period_target((
            "Lp96;","transient","(LSl6$b;LrH2;J)Lo96;")))
        self.assertEqual(PERIOD,"Lo96;")
        self.assertEqual(SOURCE,"LSl6;")

    def test_other_period_or_renderer_not_in_scope(self):
        self.assertFalse(period_target(("LiLb;","transient","(LSl6$b;LrH2;J)Lo96;")))
        self.assertFalse(period_target(("Lp96;","transient","(Ljava/lang/Object;)Lo96;")))
        self.assertFalse(period_target(("LrD0;","createPeriod","(Ljava/lang/Object;)Lo96;")))


if __name__=="__main__":
    unittest.main()
