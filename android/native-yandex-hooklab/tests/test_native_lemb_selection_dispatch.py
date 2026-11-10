import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_lemb_selection_dispatch import classification,callsite_window


class FakeDex:
    def __init__(self,methods):self.methods=methods
    def method(self,i):return self.methods[i]


class SignedLembDispatchTests(unittest.TestCase):
    def test_explicit_media3_host_does_not_prove_current_selected_source(self):
        x=classification("Lro7;",{},{"Lro7;"})
        self.assertEqual(x,"concrete_public_exoplayer_implementor")
        self.assertEqual(classification("Lro7;",{},set()),
                         "obfuscated_exoplayer_candidate")
        self.assertEqual(classification("Lero;",{},set()),
                         "known_source_lifecycle_owner")
        self.assertEqual(classification("Lrandom;",{},set()),"other_unknown")

    def test_callsite_preserves_exact_argument_coordinate_without_receiver_claim(self):
        dex=FakeDex([("Lemb;","t","(Ldmb;)V")])
        ins=[(0,0x72,(0x2072,0,0x0098))]
        result=callsite_window(dex,ins,0)
        self.assertEqual(result["receiver_register_coordinate"],8)
        self.assertEqual(result["argument_word_count"],2)
        self.assertTrue(result["opcode_is_invoke_interface"])
        self.assertFalse(result["receiver_class_or_selected_player_proven"])
        self.assertEqual(result["target"]["owner"],"Lemb;")

    def test_virtual_reference_is_not_actual_dispatch(self):
        dex=FakeDex([("Lemb;","remove","()V")])
        ins=[(0,0x6e,(0x106e,0,0x0003))]
        result=callsite_window(dex,ins,0)
        self.assertFalse(result["opcode_is_invoke_interface"])
        self.assertFalse(result["receiver_class_or_selected_player_proven"])

    def test_static_callsite_owner_classification_not_player_authorization(self):
        self.assertEqual(classification("Landroidx/media3/exoplayer/source/MediaSource;",{},set()),
                         "named_media3_owner")
        self.assertEqual(classification("Locv;",{},set()),
                         "known_source_lifecycle_owner")


if __name__=="__main__":
    unittest.main()
