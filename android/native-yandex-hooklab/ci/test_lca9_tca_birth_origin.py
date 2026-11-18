#!/usr/bin/env python3
"""Synthetic-only category and argument-position tests for the tCa birth audit."""
import unittest

from lca9_tca_birth_origin import (
    logical_parameter_positions,
    wrapper_origin_categories,
)
from audit_native_selected_item_handoff import ACC_STATIC


class Lca9TcaBirthOriginTests(unittest.TestCase):
    def test_common_exact_new_wrapper_argument(self):
        event = {
            "kind": "CALL_WITH_TYPED_IDENTITY",
            "identity_arguments": [{
                "argument_position": 2,
                "declared_argument_type": "LtCa;",
                "identity_type": "TRACK_WRAPPER",
                "origins": ["TRACK_WRAPPER_NEW_INSTANCE"],
            }],
        }
        self.assertEqual(
            wrapper_origin_categories(event, 2), ("COMMON_NEW_INSTANCE",)
        )

    def test_common_parameter_is_not_misreported_as_constructor(self):
        event = {
            "kind": "CALL_WITH_TYPED_IDENTITY",
            "identity_arguments": [{
                "argument_position": 3,
                "declared_argument_type": "LtCa;",
                "identity_type": "TRACK_WRAPPER",
                "origins": ["TRACK_WRAPPER_PARAMETER"],
            }],
        }
        self.assertEqual(
            wrapper_origin_categories(event, 3), ("COMMON_PARAMETER",)
        )
        self.assertEqual(wrapper_origin_categories(event, 2), ("NO_IDENTITY",))

    def test_possible_identity_stays_possible(self):
        event = {
            "kind": "CALL_WITH_POSSIBLE_IDENTITY",
            "possible_identity_arguments": [{
                "argument_position": 1,
                "declared_argument_type": "LtCa;",
                "identity_type": "TRACK_WRAPPER",
                "possible_origins": ["TRACK_WRAPPER_FROM_THIS_FIELD"],
            }],
        }
        self.assertEqual(
            wrapper_origin_categories(event, 1), ("POSSIBLE_THIS_FIELD",)
        )

    def test_unknown_identity_is_not_upgraded(self):
        event = {
            "kind": "CALL_WITH_TYPED_IDENTITY",
            "identity_arguments": [{
                "argument_position": 0,
                "declared_argument_type": "LtCa;",
                "identity_type": "TRACK_WRAPPER",
                "origins": ["SOME_UNEXPECTED_ORIGIN"],
            }],
        }
        self.assertEqual(
            wrapper_origin_categories(event, 0), ("COMMON_UNCLASSIFIED_ORIGIN",)
        )
        self.assertEqual(
            wrapper_origin_categories({"kind": "CALL_TARGET_ROLE_WITHOUT_IDENTITY"}, 0),
            ("NO_IDENTITY",),
        )

    def test_logical_parameter_position_skips_wide_register_word(self):
        method = (
            "Lexample/Owner;", "call",
            "(Ljava/lang/Object;J LtCa;)V".replace(" ", ""),
        )
        self.assertEqual(
            logical_parameter_positions(method, ACC_STATIC, "LtCa;"), [2]
        )

    def test_instance_receiver_counts_as_logical_position(self):
        method = (
            "Lexample/Owner;", "call",
            "(Ljava/lang/Object;J LtCa;)V".replace(" ", ""),
        )
        self.assertEqual(
            logical_parameter_positions(method, 0, "LtCa;"), [3]
        )


if __name__ == "__main__":
    unittest.main()
