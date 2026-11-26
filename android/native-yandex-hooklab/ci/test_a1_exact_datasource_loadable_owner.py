#!/usr/bin/env python3
"""Fail-closed fixtures for the one exact signed DataSource open caller audit."""
import unittest

from a1_exact_datasource_loadable_owner import (
    CLOSE, DATA_SOURCE, DATA_SPEC, LOADABLE, OPEN, PERIOD, READ,
    is_exact_datasource_target, is_loadable_load_method, implements,
)


class ExactDatasourceLoadableOwnerTests(unittest.TestCase):
    def test_only_exact_pinned_2025_source_lifecycle_methods_are_targets(self):
        self.assertEqual(OPEN, (DATA_SOURCE, "if", "(" + DATA_SPEC + ")J"))
        self.assertEqual(READ, (DATA_SOURCE, "read", "([BII)I"))
        self.assertEqual(CLOSE, (DATA_SOURCE, "close", "()V"))
        self.assertTrue(is_exact_datasource_target(OPEN))
        self.assertTrue(is_exact_datasource_target(READ))
        self.assertTrue(is_exact_datasource_target(CLOSE))
        self.assertFalse(is_exact_datasource_target(
            ("Landroidx/media3/datasource/DataSource;", "open", "(LUC2;)J")
        ))
        self.assertFalse(is_exact_datasource_target(
            (DATA_SOURCE, "open", "(LUC2;)J")
        ))
        self.assertFalse(is_exact_datasource_target(
            ("Lcom/yandex/music/shared/player/download2/exo/RetryingBalancingDataSource$Other;",
             "if", "(LUC2;)J")
        ))

    def test_only_exact_loadable_contract_is_promoted(self):
        self.assertEqual(
            LOADABLE,
            "Landroidx/media3/exoplayer/upstream/Loader$Loadable;"
        )
        self.assertTrue(is_loadable_load_method(
            ("Lx;", "load", "()V"), True
        ))
        self.assertFalse(is_loadable_load_method(
            ("Lx;", "load", "()V"), False
        ))
        self.assertFalse(is_loadable_load_method(
            ("Lx;", "run", "()V"), True
        ))
        self.assertFalse(is_loadable_load_method(
            ("Lx;", "load", "(J)V"), True
        ))

    def test_period_hierarchy_walk_is_bounded_and_exact(self):
        classes = {
            "Lchild;": (None, "Lparent;", []),
            "Lparent;": (None, "Ljava/lang/Object;", [LOADABLE]),
            "LperiodChild;": (None, PERIOD, []),
            PERIOD: (None, "Ljava/lang/Object;", []),
        }
        self.assertTrue(implements("Lchild;", LOADABLE, classes))
        self.assertFalse(implements("LperiodChild;", LOADABLE, classes))
        self.assertTrue(implements(PERIOD, PERIOD, classes))


if __name__ == "__main__":
    unittest.main()
