import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_obfuscated_dispatch_bridge import (
    possible_virtual_overrides,reachable_media,type_subclasses,media_destination
)


class VirtualMediaBridgeTests(unittest.TestCase):
    def test_signed_interface_can_have_possible_implementation_edges(self):
        root=("Le48;","a","()V")
        concrete=("Lbridge;","a","()V")
        relations={
            "Le48;":(0x601,("Ljava/lang/Object;",)),
            "Lbridge;":(17,("Le48;",))
        }
        defs={"Lbridge;":{concrete}}
        virtual,summary=possible_virtual_overrides({root:{("Lcq7;","D","()V")}},
                                                    relations,defs,("Le48;",))
        self.assertEqual(virtual[root],{concrete})
        self.assertEqual(summary["Le48;"]["candidate_dispatch_edges"],1)
        self.assertFalse(summary["Le48;"]["actual_receiver_bound"])

    def test_virtual_path_to_named_player_is_not_exact_decoder(self):
        seed=("Lcq7;","D","()V")
        root=("Le48;","a","()V")
        impl=("Lbridge;","a","()V")
        sink=("Lfxc;","play","()V")
        trace=reachable_media({seed:{root},impl:{sink}}, {root:{impl}},{seed})
        path=trace["media_paths"][0]
        self.assertEqual(path["hops"],3)
        self.assertTrue(path["possible_virtual_dispatch_used"])
        self.assertEqual(len(path["signed_method_prototypes"]),4)
        self.assertEqual(path["edge_qualification"][1]["kind"],"possible_virtual_dispatch")
        self.assertEqual(path["edge_qualification"][1]["dispatch_candidate_count"],1)
        self.assertFalse(path["audio_source_identity_or_decoder_proven"])
        self.assertFalse(trace["current_decoder_source_proven"])

    def test_no_path_does_not_rule_out_coroutines(self):
        seed=("Lcq7;","T","()V")
        trace=reachable_media({seed:set()},{},{seed})
        self.assertFalse(trace["media_paths"])
        self.assertTrue(trace["no_path_does_not_rule_out_async_runtime"])

    def test_concrete_descendants_have_real_hierarchy(self):
        relations={
            "Le48;":(0x601,("Ljava/lang/Object;",)),
            "Lone;":(17,("Le48;",)),
            "Labstract;":(0x401,("Le48;",))
        }
        self.assertEqual(type_subclasses(relations,"Le48;"),["Lone;"])

    def test_only_sdk_media_owners_count(self):
        self.assertTrue(media_destination(("Lfxc;","play","()V")))
        self.assertFalse(media_destination(("Lnonmedia;","play","()V")))


if __name__=="__main__":
    unittest.main()
