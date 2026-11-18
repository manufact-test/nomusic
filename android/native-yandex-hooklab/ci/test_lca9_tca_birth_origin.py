#!/usr/bin/env python3
"""Synthetic-only category and argument-position tests for the tCa birth audit."""
import unittest

from lca9_tca_birth_origin import (
    logical_parameter_positions,
    logical_parameter_type,
    tca_origin_category,
    tca_constructor_string_origin,
    wrapper_origin_categories,
    _parameter_register_from_tca_token,
    trace_exact_tca_constructor_to_callsites,
    private_tca_track_creator_target,
    TARGET,
    WRAPPER_CTOR,
)
import lca9_tca_birth_origin as tca_audit
from audit_native_selected_item_handoff import ACC_STATIC


class Lca9TcaBirthOriginTests(unittest.TestCase):
    def test_private_creator_target_uses_exact_track_field_owner_parameter(self):
        method = ("LCreator;", "build", "(LOwner;)V")
        row = {
            "caller_definition": (None, method, 0, 0),
            "constructor_to_writer_same_object": True,
            "constructor_string_origin_categories": ["TRACK_FIELD"],
            "constructor_string_track_field_owner_parameter_positions": [1],
            "constructor_string_track_source_field_refs": [
                ("LOwner;", "track", "Lru/yandex/music/data/audio/o;")
            ],
        }
        target = private_tca_track_creator_target({"upstream_rows": [row]})
        self.assertEqual(target["creator_owner_descriptor"], "LCreator;")
        self.assertEqual(target["creator_method_name"], "build")
        self.assertEqual(target["track_field_owner_descriptor"], "LOwner;")
        self.assertEqual(target["track_field_descriptor"], "Lru/yandex/music/data/audio/o;")
        self.assertEqual(target["owner_argument_index"], 0)

    def test_private_creator_target_fails_closed_for_ambiguous_or_wrong_field(self):
        method = ("LCreator;", "build", "(LOwner;)V")
        base = {
            "caller_definition": (None, method, 0, 0),
            "constructor_to_writer_same_object": True,
            "constructor_string_origin_categories": ["TRACK_FIELD"],
            "constructor_string_track_field_owner_parameter_positions": [1],
            "constructor_string_track_source_field_refs": [
                ("LOwner;", "track", "Ljava/lang/String;")
            ],
        }
        with self.assertRaisesRegex(ValueError, "TCA_PRIVATE_CREATOR_FIELD_NOT_TRACK_TYPED"):
            private_tca_track_creator_target({"upstream_rows": [base]})
        ambiguous = dict(base)
        ambiguous["constructor_string_track_source_field_refs"] = [
            ("LOwner;", "trackA", "Lru/yandex/music/data/audio/o;"),
            ("LOwner;", "trackB", "Lru/yandex/music/data/audio/o;"),
        ]
        with self.assertRaisesRegex(ValueError, "TCA_PRIVATE_CREATOR_TRACK_FIELD_NOT_UNIQUE"):
            private_tca_track_creator_target({"upstream_rows": [ambiguous]})

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




    def test_tca_field_store_traces_value_and_same_this_receiver(self):
        from unittest.mock import patch

        class FakeDex:
            def u16(self, offset):
                return {100: 3, 102: 2}[offset]
            def descriptor(self, index):
                return "LtCa;"
            def method(self, index):
                return TARGET

        method = ("LHolder;", "<init>", "(LtCa;)V")
        field_ref = ("LHolder;", "wrapper", "LtCa;")
        instructions = [
            (0, 0x5b, [0x125b, 1]),  # iput-object v2, v1, wrapper
            (1, 0x0e, [0x000e]),     # return-void
        ]
        cfg = {
            "entry": 0,
            "by_pc": {pc: (op, words) for pc, op, words in instructions},
            "successors": {0: (1,), 1: ()},
            "instructions": instructions,
        }
        with patch.object(tca_audit.audit, "build_dex_control_flow", return_value=cfg), \
             patch.object(tca_audit.audit, "field_id", return_value=field_ref):
            trace = trace_exact_tca_constructor_to_callsites(
                FakeDex(), method, 0, 100, None, [0], 0,
                target_argument_type=None, target_field_ref=field_ref,
            )
        site = trace["site_results"][0]
        self.assertEqual(site["origin_category"], "TYPED_PARAMETER")
        self.assertEqual(site["origin_parameter_position"], 1)
        self.assertEqual(site["receiver_origin_category"], "THIS")
        self.assertTrue(trace["same_receiver_reference_on_all_sites"])
        self.assertTrue(trace["same_tca_reference_on_all_sites"])

    def test_object_parameter_cast_preserves_exact_reference_to_lca9(self):
        from unittest.mock import patch

        class FakeDex:
            def u16(self, offset):
                return {100: 5, 102: 1}[offset]
            def descriptor(self, index):
                return "LtCa;"
            def method(self, index):
                return TARGET

        method = ("LCaller;", "call", "(Ljava/lang/Object;)V")
        instructions = [
            (0, 0x1f, [0x041f, 1]),  # check-cast v4, tCa
            (1, 0x71, [0x0071, 2]),  # invoke-static LcA9.extends(..., v4, ...)
            (2, 0x0e, [0x000e]),     # return-void
        ]
        cfg = {
            "entry": 0,
            "by_pc": {pc: (op, words) for pc, op, words in instructions},
            "successors": {0: (1,), 1: (2,), 2: ()},
            "instructions": instructions,
        }
        target_registers = [0, 1, 4, 2, 3, 5, 6, 7, 8, 9, 10, 11]
        with patch.object(tca_audit.audit, "build_dex_control_flow", return_value=cfg), \
             patch.object(tca_audit.audit, "invoke_registers",
                          return_value=target_registers):
            trace = trace_exact_tca_constructor_to_callsites(
                FakeDex(), method, ACC_STATIC, 100, TARGET, [1], 2,
                target_argument_type="LtCa;",
            )
        self.assertTrue(trace["same_tca_reference_on_all_sites"])
        self.assertFalse(trace["same_constructed_tca_on_all_sites"])
        self.assertEqual(
            trace["site_results"][0]["origin_category"],
            "CAST_FROM_REFERENCE_PARAMETER",
        )
        self.assertEqual(
            trace["site_results"][0]["origin_parameter_position"], 0
        )

    def test_unique_tca_constructor_instance_reaches_lca9(self):
        from unittest.mock import patch

        class FakeDex:
            def u16(self, offset):
                return {100: 3, 102: 0}[offset]
            def descriptor(self, index):
                return "LtCa;"
            def method(self, index):
                return {
                    2: WRAPPER_CTOR,
                    3: TARGET,
                }[index]

        method = ("LCaller;", "call", "()V")
        instructions = [
            (0, 0x22, [0x0022, 1]),  # new-instance v0, tCa
            (1, 0x70, [0x0170, 2]),  # invoke-direct {v0,v1}, tCa.<init>
            (2, 0x71, [0x0071, 3]),  # invoke-static LcA9.extends(..., v0, ...)
            (3, 0x0e, [0x000e]),     # return-void
        ]
        cfg = {
            "entry": 0,
            "by_pc": {pc: (op, words) for pc, op, words in instructions},
            "successors": {0: (1,), 1: (2,), 2: (3,), 3: ()},
            "instructions": instructions,
        }
        def invoke_registers(op, words):
            if words[1] == 2:
                return [0, 1]
            return [1, 2, 0, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        with patch.object(tca_audit.audit, "build_dex_control_flow", return_value=cfg), \
             patch.object(tca_audit.audit, "invoke_registers",
                          side_effect=invoke_registers):
            trace = trace_exact_tca_constructor_to_callsites(
                FakeDex(), method, ACC_STATIC, 100, TARGET, [2], 2,
                target_argument_type="LtCa;",
            )
        self.assertTrue(trace["same_constructed_tca_on_all_sites"])
        self.assertTrue(trace["same_tca_reference_on_all_sites"])
        self.assertEqual(
            trace["site_results"][0]["origin_category"],
            "CONSTRUCTED_IN_SAME_METHOD",
        )
        self.assertEqual(trace["wrapper_allocation_count"], 1)
        self.assertEqual(trace["wrapper_constructor_call_count"], 1)

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
        self.assertEqual(
            tca_origin_category("TRACK_PARAMETER@6"),
            "TRACK_PARAMETER",
        )
        self.assertEqual(
            tca_origin_category("TRACK_FIELD_FROM_CONTINUATION@9"),
            "TRACK_FROM_CONTINUATION_FIELD",
        )
        self.assertEqual(
            tca_origin_category("TRACK_CONTINUATION_FIELD@9"),
            "TRACK_CONTINUATION_FIELD",
        )
        self.assertEqual(
            tca_origin_category("TRACK_CONTINUATION_NEW_INSTANCE@11"),
            "CONTINUATION_NEW_INSTANCE",
        )
        self.assertEqual(
            tca_origin_category("TRACK_CONTINUATION_INIT@TRACK_CONTINUATION_NEW_INSTANCE@11"),
            "CONTINUATION_CONSTRUCTED_IN_SAME_METHOD",
        )
        self.assertEqual(
            tca_origin_category("TRACK_CONTINUATION_RETURN@15"),
            "CONTINUATION_METHOD_RETURN",
        )
        self.assertEqual(
            _parameter_register_from_tca_token("TRACK_PARAMETER@8"),
            8,
        )


    def test_tca_constructor_string_origin_is_categorical_only(self):
        self.assertEqual(
            tca_constructor_string_origin(
                "TCA_INIT@TCA_ALLOC@10|STRING=STRING_TRACK_FIELD@8"
            ),
            "TRACK_FIELD",
        )
        self.assertEqual(
            tca_constructor_string_origin(
                "TCA_INIT@TCA_ALLOC@10|STRING=STRING_TRACK_METHOD_RETURN@12"
            ),
            "TRACK_METHOD_RETURN",
        )
        self.assertEqual(
            tca_constructor_string_origin(
                "TCA_INIT@TCA_ALLOC@10|STRING=STRING_PARAMETER@4"
            ),
            "STRING_PARAMETER",
        )
        self.assertEqual(
            tca_constructor_string_origin("TCA_INIT@TCA_ALLOC@10"),
            "UNKNOWN",
        )
        self.assertEqual(
            tca_constructor_string_origin(
                "TCA_INIT@TCA_ALLOC@10|STRING=STRING_CONSTANT@13"
            ),
            "CONSTANT",
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
