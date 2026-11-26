#!/usr/bin/env python3
import unittest
from a1_private_active_period_source_target import require_adapter_identity_proofs


class ExactPrivateActivePeriodTargetProofTest(unittest.TestCase):
    def setUp(self):
        self.adapter = {
            "child_stream_array_allocated_and_passed_to_nested_MediaPeriod": True,
            "child_sample_stream_array_element_loaded_for_adapter": True,
            "adapter_child_stream_identity_compared_with_existing_delegate": True,
            "new_adapter_stores_exact_child_stream_typed_field": True,
            "same_adapter_array_field_read_after_store": True,
            "selected_adapter_written_into_original_holder_stream_array": True,
        }
        self.child = {
            "child_same_reference_on_all_scoped_ctor_reaching_states": True,
            "scoped_reaching_state_count": 3,
            "constructor_stores_exact_incoming_LR29_argument": True,
        }

    def test_requires_both_independent_proofs(self):
        require_adapter_identity_proofs(self.adapter, self.child)

    def test_rejects_missing_constructor_argument_identity(self):
        child = dict(self.child)
        child["constructor_stores_exact_incoming_LR29_argument"] = False
        with self.assertRaisesRegex(ValueError, "NAV31_CHILD_STREAM_ADAPTER_IDENTITY_UNPROVEN"):
            require_adapter_identity_proofs(self.adapter, child)

    def test_rejects_missing_holder_array_publication(self):
        adapter = dict(self.adapter)
        adapter["selected_adapter_written_into_original_holder_stream_array"] = False
        with self.assertRaisesRegex(ValueError, "NAV31_CHILD_STREAM_ADAPTER_IDENTITY_UNPROVEN"):
            require_adapter_identity_proofs(adapter, self.child)

    def test_rejects_empty_cfg_constructor_paths(self):
        child = dict(self.child)
        child["scoped_reaching_state_count"] = 0
        with self.assertRaisesRegex(ValueError, "NAV31_CHILD_STREAM_ADAPTER_IDENTITY_UNPROVEN"):
            require_adapter_identity_proofs(self.adapter, child)


if __name__ == "__main__":
    unittest.main()
