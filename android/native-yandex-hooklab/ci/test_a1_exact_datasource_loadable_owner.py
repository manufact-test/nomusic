#!/usr/bin/env python3
"""Fail-closed fixtures for the one exact signed DataSource open caller audit."""
import unittest

from a1_exact_datasource_loadable_owner import (
    CLOSE, DATA_SOURCE, DATA_SPEC, LOADABLE, OPEN, PERIOD, READ,
    collect_dispatch_targets, hierarchy_owners,
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

    def test_datasource_dispatch_is_restricted_to_its_exact_type_hierarchy(self):
        classes = {
            DATA_SOURCE: (None, "Lbase;", ["Ldatasource-contract;"]),
            "Lbase;": (None, "Ljava/lang/Object;", []),
            "Ldatasource-contract;": (None, "Ljava/lang/Object;", []),
            "Lunrelated;": (None, "Ljava/lang/Object;", []),
        }
        scope = hierarchy_owners(DATA_SOURCE, classes)
        self.assertEqual(
            scope,
            {DATA_SOURCE, "Lbase;", "Ldatasource-contract;"}
        )

        class FakeDex:
            method_count = 3
            methods = [
                ("Ldatasource-contract;", "open", "(LUC2;)J"),
                ("Lunrelated;", "open", "(LUC2;)J"),
                (DATA_SOURCE, "if", "(LUC2;)J"),
            ]
            def method(self, index):
                return self.methods[index]

        targets = collect_dispatch_targets(
            [FakeDex()], scope, "(LUC2;)J"
        )
        self.assertEqual(
            targets,
            {
                ("Ldatasource-contract;", "open", "(LUC2;)J"),
                (DATA_SOURCE, "if", "(LUC2;)J"),
            }
        )

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
