import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_datasource_read_lifecycle import (
    safe_events_for_call,source_field_load_to_call,typed_callsite_facts,
    exact_source_register_reuse
)


class FakeDex:
    def __init__(self,methods):
        self.methods=methods
    def method(self,index):return self.methods[index]


class SourceExecutionCallsiteTests(unittest.TestCase):
    def test_callsite_ordinal_not_runtime_audio_order(self):
        dex=FakeDex([("Lha4;","b","(La58;)J")])
        ins=[(0,0x71,(0x2071,0,0x0010))]
        row=safe_events_for_call(dex,ins,0)
        self.assertEqual(row["callee"]["owner"],"Lha4;")
        self.assertEqual(row["callee"]["method"],"b")
        self.assertEqual(row["register_arguments"],[0,1])
        self.assertTrue(row["requires_control_flow_and_runtime_validation"])
        self.assertFalse(row["actual_audio_decoding_witness"])

    def test_selected_read_and_open_are_two_calls_not_sequence_proof(self):
        dex=FakeDex([
            ("Lha4;","b","(La58;)J"),
            ("Lha4;","read","([BII)I"),
        ])
        ins=[
            (0,0x71,(0x2071,0,0x0010)),
            (3,0x38,(0x0038,7)),
            (5,0x71,(0x4071,1,0x3210)),
            (8,0x0e,(0x000e,)),
        ]
        facts=typed_callsite_facts(dex,ins)
        self.assertEqual(len(facts),2)
        self.assertEqual(facts[0]["callsite"]["callee"]["method"],"b")
        self.assertEqual(facts[1]["callsite"]["callee"]["method"],"read")
        self.assertTrue(all(x["same_method_order_not_guaranteed_runtime_order"] for x in facts))

    def test_register_field_origin_exact_same_basic_block(self):
        dex=FakeDex([("Lha4;","read","([BII)I")])
        ins=[(0,0x54,(0x2254,3)),
             (2,0x71,(0x1071,0,0x0002))]
        key=("Lmb4;","Lha4;","hidden")
        with patch("audit_native_ga4_field_receiver.field_key",return_value=key):
            row=source_field_load_to_call(dex,ins,1)
        self.assertTrue(row["receiver_loaded_from_field_in_same_basic_block"])
        self.assertEqual(row["field_value_type"],"Lha4;")
        self.assertTrue(row["same_object_through_heap_not_proven"])

    def test_branch_stops_source_register_attribution(self):
        dex=FakeDex([("Lha4;","read","([BII)I")])
        ins=[
            (0,0x54,(0x2254,3)),
            (2,0x38,(0x0038,5)),
            (4,0x71,(0x1071,0,0x0002))
        ]
        key=("Lmb4;","Lha4;","hidden")
        with patch("audit_native_ga4_field_receiver.field_key",return_value=key):
            row=source_field_load_to_call(dex,ins,2)
        self.assertFalse(row["receiver_loaded_from_field_in_same_basic_block"])

    def test_exact_receiver_register_reuse_is_not_object_or_decoder_proof(self):
        ev=[
            {"callsite":{"callee":{"owner":"Lha4;","method":"b"},
                          "register_arguments":[8,2]}},
            {"callsite":{"callee":{"owner":"Lha4;","method":"read"},
                          "register_arguments":[8,2,3,4]}},
            {"callsite":{"callee":{"owner":"Lha4;","method":"close"},
                          "register_arguments":[8]}},
        ]
        row=exact_source_register_reuse(ev,("Lmb4;","a","()V"))
        self.assertTrue(row["all_open_read_close_callsite_receiver_registers_identical"])
        self.assertTrue(row["register_identity_across_branches_not_live_object_identity"])
        self.assertFalse(row["decoder_or_active_track_proven"])

    def test_register_reassigned_in_different_source_sites_is_not_reuse(self):
        ev=[
            {"callsite":{"callee":{"owner":"Lha4;","method":"b"},
                          "register_arguments":[8,2]}},
            {"callsite":{"callee":{"owner":"Lha4;","method":"read"},
                          "register_arguments":[9,2,3,4]}},
            {"callsite":{"callee":{"owner":"Lha4;","method":"close"},
                          "register_arguments":[8]}},
        ]
        row=exact_source_register_reuse(ev,("Lmb4;","a","()V"))
        self.assertFalse(row["all_open_read_close_callsite_receiver_registers_identical"])

    def test_early_register_overwrite_kills_same_source_claim(self):
        dex=FakeDex([("Lha4;","read","([BII)I")])
        ins=[
            (0,0x54,(0x2254,3)),
            (2,0x12,(0x0212,)),
            (3,0x71,(0x1071,0,0x0002))
        ]
        row=source_field_load_to_call(dex,ins,2)
        self.assertFalse(row["receiver_loaded_from_field_in_same_basic_block"])


if __name__=="__main__":
    unittest.main()
