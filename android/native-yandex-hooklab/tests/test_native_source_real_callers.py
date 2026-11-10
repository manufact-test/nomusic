import sys
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_source_real_callers import (relevant,invocation_windows,
    class_ancestry,source_wrapper_field_projections,model_input_to_i0_windows)


class FakeDex:
    def __init__(self,methods):
        self.methods=methods
    def method(self,i):return self.methods[i]



class CodeDex(FakeDex):
    def __init__(self,code,methods):
        super().__init__(methods)
        self.words=[0]*8+list(code)
        self.words[6]=len(code)
    def bounds(self,offset,size):
        if offset<0 or offset+size>2*len(self.words):
            raise ValueError("DEX_BOUNDS")
    def u16(self,offset):return self.words[offset//2]
    def u32(self,offset):return self.u16(offset)|(self.u16(offset+2)<<16)
    def descriptor(self,i):return {1:"Lga4;"}[i]


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

    def test_exact_wrapper_iget_field_projection_to_lero_conditional_path(self):
        producer=("Lcq7;","i0","()Ljava/lang/Object;")
        sink=("Lero;","<init>","(Ljava/lang/Object;Lga4;)V")
        # invoke, result v1, iget-object v1,v1, check-cast Lga4,
        # if-eqz v1 skip, invoke-direct {v7,v4,v1} constructor, return
        code=[0x0071,0,0,0x010c,0x1154,0,
              0x011f,1,0x0138,5,0x3070,1,0x0147,0x000e]
        key=("LoriginalWrapper;","Lga4;","private_not_exported")
        with patch("audit_native_source_real_callers.field_key",return_value=key):
            rows=source_wrapper_field_projections(CodeDex(code,[producer,sink]),0)
        self.assertEqual(len(rows),1)
        row=rows[0]
        self.assertTrue(row["distinct_object_identity_from_wrapper"])
        self.assertEqual(row["projection_cast_types"],["Lga4;"])
        event=row["projected_field_may_flow_events"][0]
        self.assertEqual(event["callee"],"Lero;-><init>")
        self.assertEqual(event["argument_word"],2)
        self.assertTrue(event["conditional_branch_crossed"])
        self.assertFalse(event["actual_runtime_call_proven"])

    def test_wrong_iget_receiver_does_not_prove_wrapper_projection(self):
        producer=("Lcq7;","i0","()Ljava/lang/Object;")
        code=[0x0071,0,0,0x010c,0x2154,0,0x000e]
        key=("Lwrapper;","Lga4;","hidden")
        with patch("audit_native_source_real_callers.field_key",return_value=key):
            self.assertEqual(source_wrapper_field_projections(
                CodeDex(code,[producer]),0),[])

    def test_shared_register_wrapper_and_field_are_distinct_objects(self):
        producer=("Lcq7;","i0","()Ljava/lang/Object;")
        sink=("Lero;","<init>","(Lga4;)V")
        code=[0x0071,0,0,0x010c,0x1154,0,0x1070,1,0x0001,0x000e]
        key=("Lwrapper;","Lga4;","private")
        with patch("audit_native_source_real_callers.field_key",return_value=key):
            result=source_wrapper_field_projections(
                CodeDex(code,[producer,sink]),0)
        self.assertTrue(result[0]["distinct_object_identity_from_wrapper"])
        self.assertEqual(result[0]["projected_field_may_flow_events"][0]
                         ["argument_word"],0)

    def test_structural_i0_input_registers_are_not_current_track_proof(self):
        producer=("Lcq7;","i0","(Lxfs;Ljgv;Lacb;)Ljava/lang/Object;")
        dex=FakeDex([producer])
        rows=model_input_to_i0_windows(
            dex,[(0,0x71,(0x3071,0,0x0321))])
        self.assertEqual(rows[0]["i0_argument_registers"],[1,2,3])
        self.assertEqual(rows[0]["i0_invoke_ordinal"],0)
        self.assertFalse(rows[0]["proven_current_music_track"])

    def test_ancestry_cannot_prove_decoder(self):
        self.assertFalse(class_ancestry({"Lmir;":(17,("Lbase;",))},"Lmir;")
                         ["runtime_player_instance_proven"])
        self.assertEqual(class_ancestry({"Lmir;":(17,("Lbase;",))},"Lmir;")
                         ["direct_parents"],["Lbase;"])


if __name__=="__main__":
    unittest.main()
