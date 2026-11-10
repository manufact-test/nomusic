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

    def test_never_outputs_private_field_name(self):
        source=(ROOT/"audit_native_runtime_hook_shapes.py").read_text()
        self.assertIn("reader_fields.add(",source)
        self.assertNotIn("sorted(reader_fields)",source)
        self.assertNotIn("print(reader_fields)",source)


if __name__=="__main__":
    unittest.main()
