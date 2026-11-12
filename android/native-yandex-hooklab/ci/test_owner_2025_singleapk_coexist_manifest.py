"""Synthetic-only original/clone global manifest collision checks; no vendor APK."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from owner_2025_lspatch_sigcompat_arm13 import coexist_manifest_2025, PKG, ANDROID

HEADER = '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="ru.yandex.music">'
FOOTER = '</manifest>'


class CoexistManifestTest(unittest.TestCase):
    def test_removes_only_conflicting_declarations_not_uses_permissions(self):
        source = (HEADER +
                  '<permission android:name="com.yandex.permission.READ_CREDENTIALS" android:protectionLevel="signature"/>'
                  '<permission android:name="com.yandex.music.RELAY_PERMISSION" android:protectionLevel="signature"/>'
                  '<permission android:name="com.example.unique.permission" android:protectionLevel="normal"/>'
                  '<uses-permission android:name="com.yandex.permission.READ_CREDENTIALS"/>'
                  '<application><activity android:name="ru.yandex.music.main.MainScreenActivity"/></application>' +
                  FOOTER)
        result, stats = coexist_manifest_2025(source)
        root = ET.fromstring(result)
        declarations = [e.attrib[ANDROID + "name"] for e in root.findall("permission")]
        requested = [e.attrib[ANDROID + "name"] for e in root.findall("uses-permission")]
        self.assertEqual(declarations, ["com.example.unique.permission"])
        self.assertEqual(requested, ["com.yandex.permission.READ_CREDENTIALS"])
        self.assertEqual(stats["publisher_signature_permission_declarations_removed"], 2)
        self.assertEqual(root.attrib["package"], PKG)

    def test_all_provider_authorities_are_unique_clone_namespace(self):
        source = (HEADER +
                  '<application>'
                  '<provider android:name="com.example.Provider" '
                  'android:authorities="com.yandex.preinstallsatellite.appmetrica.provider;ru.yandex.music.files"/>'
                  '</application>' + FOOTER)
        rewritten, stats = coexist_manifest_2025(source)
        root = ET.fromstring(rewritten)
        authority = root.find("./application/provider").attrib[ANDROID + "authorities"]
        items = authority.split(";")
        self.assertEqual(len(items), 2)
        self.assertTrue(all(x.startswith(PKG + ".") for x in items))
        self.assertNotIn("com.yandex.preinstallsatellite.appmetrica.provider", authority)
        self.assertGreaterEqual(stats["provider_authorities"], 1)

    def test_rejects_non_signature_permission_mutation(self):
        source = (HEADER +
                  '<permission android:name="com.yandex.permission.READ_CREDENTIALS" '
                  'android:protectionLevel="dangerous"/>' + FOOTER)
        with self.assertRaisesRegex(RuntimeError, "SIGCOMPAT_2025_PERMISSION_PROTECTION_CHANGED"):
            coexist_manifest_2025(source)

    def test_does_not_accept_wrong_original_package(self):
        source = HEADER.replace("ru.yandex.music", "org.example.other") + FOOTER
        with self.assertRaisesRegex(ValueError, "MANIFEST_SOURCE_IDENTITY_MISMATCH"):
            coexist_manifest_2025(source)


if __name__ == "__main__":
    unittest.main()
