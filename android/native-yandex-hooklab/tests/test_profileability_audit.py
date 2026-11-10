import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_native_identity_phase2_ephemeral import classify_manifest_shell_profileability

NS = "http://schemas.android.com/apk/res/android"


def xml(profile="", app_flags=""):
    return (
        f'<manifest xmlns:android="{NS}" package="ru.yandex.music">'
        f'<application {app_flags}>{profile}</application></manifest>'
    ).encode()


class PublicPublisherProfileabilityTests(unittest.TestCase):
    def test_no_declaration_non_debuggable_means_not_profileable(self):
        result = classify_manifest_shell_profileability(xml())
        self.assertFalse(result["ordinary_shell_method_tracing_authorized"])
        self.assertFalse(result["profileable_declaration_present"])
        self.assertFalse(result["raw_manifest_exposed"])

    def test_explicit_shell_profileable_can_be_profiled(self):
        result = classify_manifest_shell_profileability(xml(
            '<profileable android:shell="true" />'
        ))
        self.assertTrue(result["ordinary_shell_method_tracing_authorized"])
        self.assertTrue(result["profileable_shell_granted"])

    def test_shell_false_or_disabled_cannot_profile(self):
        for el in (
            '<profileable android:shell="false" />',
            '<profileable android:shell="true" android:enabled="false"/>'
        ):
            with self.subTest(el=el):
                result = classify_manifest_shell_profileability(xml(el))
                self.assertFalse(result["ordinary_shell_method_tracing_authorized"])

    def test_debuggable_separate_from_shell_profileable(self):
        result = classify_manifest_shell_profileability(
            xml(app_flags='android:debuggable="true"'))
        self.assertTrue(result["publisher_debuggable"])
        self.assertTrue(result["ordinary_shell_method_tracing_authorized"])


if __name__ == "__main__":
    unittest.main()
