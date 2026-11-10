import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_source_real_callers import relevant,invocation_windows,class_ancestry


class FakeDex:
    def __init__(self,methods):
        self.methods=methods
    def method(self,i):return self.methods[i]


class ActualSignedCallersAuditTests(unittest.TestCase):
    def test_selected_methods_match_exact_owner_and_name(self):
        self.assertTrue(relevant(("Lo4y;","c","(Ljgv;)Lkq7;")))
        self.assertTrue(relevant(("Locv;","i0","()Ljava/lang/Object;")))
        self.assertFalse(relevant(("Lother;","i0","()Ljava/lang/Object;")))
        self.assertFalse(relevant(("Lo4y;","x","()V")))

    def test_direct_call_site_no_runtime_audio_claim(self):
        target=("Lcq7;","i0","(Lxfs;Ljgv;Lacb;)Ljava/lang/Object;")
        dex=FakeDex([target])
        instructions=[
            (0,0x71,(0x2071,0,0x0010)),
            (3,0x0c,(0x050c,)),
            (4,0x11,(0x0511,)),
        ]
        row=invocation_windows(dex,instructions,{("Lcq7;","i0")})[0]
        self.assertEqual(row["called"],"Lcq7;->i0")
        self.assertEqual(row["opcode_window"][0]["argument_register_coordinates"],[0,1])
        self.assertTrue(row["may_cross_branch_or_async_execution"])

    def test_called_method_name_without_correct_owner_excluded(self):
        dex=FakeDex([("Lstranger;","i0","()V")])
        ins=[(0,0x71,(0x0071,0,0))]
        self.assertEqual(invocation_windows(dex,ins,{("Lcq7;","i0")}),[])

    def test_ancestry_cannot_prove_decoder(self):
        self.assertFalse(class_ancestry({"Lmir;":(17,("Lbase;",))},"Lmir;")
                         ["runtime_player_instance_proven"])
        self.assertEqual(class_ancestry({"Lmir;":(17,("Lbase;",))},"Lmir;")
                         ["direct_parents"],["Lbase;"])


if __name__=="__main__":
    unittest.main()
