"""Synthetic read-only exact-SDK DEX classifier tests, no real APK."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_native_media_engine import ENTRYPOINTS, family_for, snapshot, combine


class FakeDex:
    def __init__(self, classes, methods):
        self.classes = classes
        self.methods = methods
        self.method_count = len(methods)

    def defined_classes(self):
        return set(self.classes)

    def method(self, i):
        return self.methods[i]


class NativeMediaEngineAuditTests(unittest.TestCase):
    def test_exact_sdk_type_not_fuzzy_obfuscated(self):
        class_ = ENTRYPOINTS["media3_exoplayer_impl"]
        result = snapshot(FakeDex(
            {class_, "Lsecret/SessionTokenReader;"},
            [(class_, "prepare", "()V"),
             ("Lsecret/SessionTokenReader;", "prepare", "()V")]
        ))
        self.assertEqual(result["public_sdk_class_count"], 1)
        self.assertTrue(result["entrypoints"]["media3_exoplayer_impl"]["class_defined"])
        self.assertEqual(result["entrypoints"]["media3_exoplayer_impl"]["declared_methods"],
                         [("prepare", "()V")])
        self.assertNotIn("secret", repr(result).lower())

    def test_reference_only_is_not_implementation(self):
        role = "legacy_exoplayer2_impl"
        result = snapshot(FakeDex(
            set(), [(ENTRYPOINTS[role], "prepare", "()V")]))
        self.assertFalse(result["entrypoints"][role]["class_defined"])
        self.assertFalse(combine([result])["exact_public_entrypoints"][role]["class_defined_in_signed_dex"])

    def test_no_decoder_conclusion_from_method_reference(self):
        role = "media3_exoplayer_impl"
        result = combine([snapshot(FakeDex(
            {ENTRYPOINTS[role]}, [(ENTRYPOINTS[role], "prepare", "()V")]))])
        self.assertFalse(result["real_decoder_source_association_proven"])
        self.assertFalse(result["exact_public_entrypoints"][role]["declared_method_body_confirmed"])

    def test_public_namespace_only(self):
        self.assertEqual(family_for("Landroidx/media3/exoplayer/ExoPlayerImpl;"), "exoplayer")
        self.assertEqual(family_for("Lcom/google/android/exoplayer2/ExoPlayerImpl;"), "legacy_player")
        self.assertEqual(family_for("Lprivate/yandex/token;"), "not_public_sdk")


if __name__ == "__main__":
    unittest.main()
