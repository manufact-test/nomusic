import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_jgv_media_candidates import (
    hierarchy_verdict, bounded_method_media_calls,
    TARGET_METHODS, CLASSES, MEDIA_CONCRETES
)


class DummyDex:
    def __init__(self, code, methods):
        self.words=[0]*8+code
        self.words[6]=len(code)
        self.methods=methods
    def bounds(self,off,size):
        if off<0 or off+size>len(self.words)*2:
            raise ValueError("BUND")
    def u16(self,off):
        return self.words[off//2]
    def u32(self,off):
        return self.u16(off) | self.u16(off+2)<<16
    def method(self,index):
        return self.methods[index]


class SignedLjgvMediaCandidatesTests(unittest.TestCase):
    def test_class_hierarchy_media_interface_is_not_live_playback(self):
        chain={
          "Lchild;":(17,("Lparent;",)),
          "Lparent;":(1,("Landroidx/media3/datasource/DataSource;",))
        }
        result=hierarchy_verdict(chain,"Lchild;")
        self.assertEqual(result["named_media_ancestry"][0]["steps"],2)
        self.assertFalse(result["media_instance_in_actual_player_proven"])

    def test_unrelated_class_does_not_inherit_media_contract(self):
        info=hierarchy_verdict({"Lchild;":(17,("Ljava/lang/Object;",))},"Lchild;")
        self.assertEqual(info["named_media_ancestry"],[])
        self.assertFalse(info["media_instance_in_actual_player_proven"])

    def test_real_method_reference_counts_without_audio_claim(self):
        owner=("Lygv;","r","(Ldiv;)Ljgv;")
        media=("Lfxc;","setMediaSource","()V")
        call_model=("Ljgv;","b","()Lk27;")
        dex=DummyDex([0x0071,0,0, 0x0071,1,0, 0x000e],[media,call_model])
        result=bounded_method_media_calls(owner,dex,0)
        self.assertEqual(result["direct_named_media_call_count"],1)
        self.assertEqual(result["related_model_method_invokes"],["Ljgv;->b"])
        self.assertFalse(result["direct_player_source_proven"])

    def test_no_sdk_symbols_no_false_method_connection(self):
        method=("Lygv;","r","(Ldiv;)Ljgv;")
        callee=("Lother;","f","()V")
        result=bounded_method_media_calls(method,DummyDex([0x0071,0,0,0x000e],[callee]),0)
        self.assertEqual(result["direct_named_media_call_count"],0)

    def test_large_lambda_may_contain_unrelated_media_call_arms(self):
        method=("Lsu5;","invoke","()Ljava/lang/Object;")
        media=("Lro7;","y0","(Lzzm;)V")
        code=[0x000e]*90+[0x0071,0,0,0x000e]
        report=bounded_method_media_calls(method,DummyDex(code,[media]),0)
        self.assertTrue(report["same_body_media_calls_may_be_different_switch_arms"])
        self.assertEqual(report["direct_named_media_call_count"],1)
        self.assertFalse(report["direct_player_source_proven"])

    def test_exact_interest_groups_not_media_names_only(self):
        self.assertIn("Lcq7;",TARGET_METHODS)
        self.assertIn("Lro7;",TARGET_METHODS)
        self.assertIn("Le48;",CLASSES)
        self.assertIn("Lya4;",TARGET_METHODS)
        self.assertIn("Lkc6;",TARGET_METHODS)
        self.assertIn("Lzcd;",TARGET_METHODS)
        self.assertIn("Ljgv;",CLASSES)
        self.assertIn("Lfxc;",MEDIA_CONCRETES)


if __name__=="__main__":
    unittest.main()
