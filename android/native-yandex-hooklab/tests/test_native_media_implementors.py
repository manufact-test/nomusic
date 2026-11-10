import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_native_media_implementors import (
    INTERFACES, transitive_implementors, summarize, bounded_name,
)


class NativePlayerImplementorTests(unittest.TestCase):
    def test_inherited_interface_from_obfuscated_base(self):
        target=INTERFACES["media3_exoplayer"]
        rel={
            target:(0x200,tuple()),
            "Lmedbase;":(0x400,(target,)),
            "Labc;":(0,("Lmedbase;",)),
            "Lxyz;":(0,("Labc;",)),
            "Lunrelated;":(0,tuple()),
        }
        self.assertEqual(transitive_implementors(rel,target),["Labc;","Lxyz;"])
        body={"Labc;":{("prepare","()V")},"Lxyz;":{("setMediaItem","(I)V")}}
        report=summarize(rel,body)["media3_exoplayer"]
        self.assertEqual(report["concrete_implementor_count"],2)
        self.assertEqual(report["concrete_prepare_method_body_count"],1)
        self.assertFalse(report["audio_decoder_or_real_player_proven"])

    def test_reject_self_and_cycle(self):
        target=INTERFACES["legacy_exoplayer2"]
        rel={target:(0x200,tuple()),"Lcycle1;":(0,("Lcycle2;",)),
             "Lcycle2;":(0,("Lcycle1;",))}
        self.assertEqual(transitive_implementors(rel,target),[])

    def test_no_private_class_details(self):
        rel={INTERFACES["media3_exoplayer"]:(0x200,tuple()),
             "Lprivate/secret/UserTokenDecoder;":(0,(INTERFACES["media3_exoplayer"],))}
        report=summarize(rel,{})["media3_exoplayer"]
        self.assertEqual(report["first_concrete_candidates"][0]["bounded_owner"],
                         "REDACTED_NAMED_CLASS")
        self.assertNotIn("UserToken", repr(report))
        self.assertEqual(bounded_name("Lx1;"),"Lx1;")


if __name__=="__main__":
    unittest.main()
