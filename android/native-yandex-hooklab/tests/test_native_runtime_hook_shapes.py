"""Synthetic checks for pinned signed-only runtime hook preflight."""
import importlib.util
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
SPEC=importlib.util.spec_from_file_location("audit_native_runtime_hook_shapes",
    ROOT/"audit_native_runtime_hook_shapes.py")
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ExactNativeHookShapeTests(unittest.TestCase):
    def test_all_synthetic_shapes_only_one_field(self):
        result=mod.check_shapes(mod.TARGETS,1)
        self.assertTrue(result["all_seven_concrete_runtime_methods_defined"])
        self.assertTrue(result["one_typed_lero_lmb4_field"])
        self.assertEqual(result["exact_target_definitions_found"],7)
        self.assertFalse(result["runtime_selected_receiver_proven"])
        self.assertFalse(result["decoder_preprepare_proven"])

    def test_missing_lha4_open_rejected(self):
        known=mod.TARGETS-{("Lha4;","b","(La58;)J")}
        r=mod.check_shapes(known,1)
        self.assertFalse(r["all_seven_concrete_runtime_methods_defined"])
        self.assertEqual(r["missing_target_count"],1)

    def test_different_signature_rejected(self):
        known=mod.TARGETS-{("Lmb4;","a","()V")}
        known.add(("Lmb4;","a","()Ljava/lang/Object;"))
        r=mod.check_shapes(known,1)
        self.assertFalse(r["all_seven_concrete_runtime_methods_defined"])

    def test_ambiguous_or_missing_reader_fields_rejected(self):
        for n in (0,2,9):
            with self.subTest(fields=n):
                self.assertFalse(mod.check_shapes(mod.TARGETS,n)["one_typed_lero_lmb4_field"])

    def test_direct_lero_construction_is_not_synonymous_with_factory(self):
        cases=[("(Lwzi;Lga4;)V","(Lwzi;Lga4;Ljava/lang/Object;)V")]
        for pair in cases:
            r=mod.check_lero_constructors(pair)
            self.assertTrue(r["both_exact_lero_creation_shapes_proven"])
            self.assertTrue(r["direct_Locv_construction_can_bypass_kvs_factory"])
            self.assertEqual(r["exact_lero_constructor_short_count"],1)
            self.assertEqual(r["exact_lero_constructor_long_count"],1)
            self.assertFalse(r["actual_live_selected_source_or_decoder_proven"])

    def test_missing_or_ambiguous_constructor_fails_closed(self):
        long="(Lwzi;Lga4;Ljava/lang/Object;)V"
        short="(Lwzi;Lga4;)V"
        for pair in [(),(short,),(long,),(short,short,long),
                     (short,long,long),(short,"(Lwzi;Lga4;I)V"),
                     (short,"(Lwzi;Lga4;[B)V"),
                     (short,"(Lwzi;Lga4;Lfoo;Ljava/lang/Object;)V")]:
            with self.subTest(pair=pair):
                self.assertFalse(
                    mod.check_lero_constructors(pair)[
                        "both_exact_lero_creation_shapes_proven"])

    def test_never_outputs_private_field_name(self):
        source=(ROOT/"audit_native_runtime_hook_shapes.py").read_text()
        self.assertIn("reader_fields.add(",source)
        self.assertNotIn("sorted(reader_fields)",source)
        self.assertNotIn("print(reader_fields)",source)


if __name__=="__main__":
    unittest.main()
