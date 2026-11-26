#!/usr/bin/env python3
"""Fail-closed fixtures for the one exact signed DataSource open caller audit."""
import unittest

from a1_exact_datasource_loadable_owner import (
    CLOSE, DATA_SOURCE, DATA_SPEC, OPEN, PERIOD, READ,
    collect_dispatch_targets, hierarchy_owners, loader_contract_for_method,
    is_exact_datasource_target, implements,
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

    def test_obfuscated_loadable_contract_is_derived_from_exact_loader_inner_interface(self):
        loader_interface = "Landroidx/media3/exoplayer/upstream/Loader$a;"
        owner = "Lsigned-loadable;"
        classes = {
            owner: (None, "Ljava/lang/Object;", [loader_interface], 0x11),
            loader_interface: (None, "Ljava/lang/Object;", [], 0x200),
        }
        methods = {
            loader_interface: [
                ((loader_interface, "for", "()V"), 0x401, 0)
            ]
        }
        self.assertEqual(
            loader_contract_for_method(
                owner, (owner, "for", "()V"), classes, methods
            ),
            [loader_interface]
        )
        self.assertEqual(
            loader_contract_for_method(
                owner, (owner, "run", "()V"), classes, methods
            ),
            []
        )
        self.assertEqual(
            loader_contract_for_method(
                owner, (owner, "for", "(J)V"), classes, methods
            ),
            []
        )

    def test_datasource_dispatch_is_restricted_to_its_exact_type_hierarchy(self):
        classes = {
            DATA_SOURCE: (None, "Lbase;", ["Ldatasource-contract;"], 0x11),
            "Lbase;": (None, "Ljava/lang/Object;", [], 0x11),
            "Ldatasource-contract;": (None, "Ljava/lang/Object;", [], 0x200),
            "Lunrelated;": (None, "Ljava/lang/Object;", [], 0x11),
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
            "Lchild;": (None, "Lparent;", [], 0x11),
            "Lparent;": (None, "Ljava/lang/Object;", ["Lmarker;"], 0x11),
            "LperiodChild;": (None, PERIOD, [], 0x11),
            PERIOD: (None, "Ljava/lang/Object;", [], 0x11),
        }
        self.assertTrue(implements("Lchild;", "Lmarker;", classes))
        self.assertFalse(implements("LperiodChild;", "Lmarker;", classes))
        self.assertTrue(implements(PERIOD, PERIOD, classes))


if __name__ == "__main__":
    unittest.main()
