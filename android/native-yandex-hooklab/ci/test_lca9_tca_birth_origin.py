#!/usr/bin/env python3
"""Synthetic-only category and argument-position tests for the tCa birth audit."""
import unittest

from lca9_tca_birth_origin import (
    logical_parameter_positions,
    logical_parameter_type,
    tca_origin_category,
    wrapper_origin_categories,
    _parameter_register_from_tca_token,
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


    def test_casted_opaque_reference_origin_categories(self):
        self.assertEqual(
            tca_origin_category("TCA_CAST@REF_PARAMETER@4"),
            "CAST_FROM_REFERENCE_PARAMETER",
        )
        self.assertEqual(
            tca_origin_category("TCA_CAST@REF_THIS_FIELD@12"),
            "CAST_FROM_THIS_FIELD",
        )
        self.assertEqual(
            tca_origin_category("TCA_CAST@REF_RETURN@27"),
            "CAST_FROM_METHOD_RETURN",
        )
        self.assertEqual(
            tca_origin_category("REF_PARAMETER@4"),
            "REFERENCE_PARAMETER",
        )

    def test_constructor_and_null_origins_are_distinct(self):
        self.assertEqual(
            tca_origin_category("TCA_INIT@TCA_ALLOC@15"),
            "CONSTRUCTED_IN_SAME_METHOD",
        )
        self.assertEqual(
            tca_origin_category("TCA_NULL@19"),
            "EXPLICIT_NULL",
        )

    def test_casted_parameter_register_is_recoverable_for_one_upstream_hop(self):
        self.assertEqual(
            _parameter_register_from_tca_token("TCA_CAST@REF_PARAMETER@7"),
            7,
        )
        self.assertEqual(
            _parameter_register_from_tca_token("TCA_PARAMETER@5"),
            5,
        )
        self.assertIsNone(
            _parameter_register_from_tca_token("TCA_CAST@REF_FIELD@9")
        )

    def test_logical_parameter_type_handles_instance_and_wide_arguments(self):
        method = (
            "Lexample/Owner;", "call",
            "(Ljava/lang/Object;J LtCa;)V".replace(" ", ""),
        )
        self.assertEqual(logical_parameter_type(method, ACC_STATIC, 0), "Ljava/lang/Object;")
        self.assertEqual(logical_parameter_type(method, ACC_STATIC, 2), "LtCa;")
        self.assertEqual(logical_parameter_type(method, 0, 1), "Ljava/lang/Object;")
        self.assertEqual(logical_parameter_type(method, 0, 3), "LtCa;")

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
