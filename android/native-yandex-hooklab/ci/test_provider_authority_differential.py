"""Synthetic-only manifest differential, original APK is never modified."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from owner_2025_lspatch2_namespaced_clone_arm13 import patch_manifest, DEST, ANDROID

BASE = '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="ru.yandex.music">'
END = '</manifest>'


class ProviderIdentityDifferential(unittest.TestCase):
    def test_original_authority_remains_but_package_is_independently_named(self):
        manifest = (BASE +
                    '<application><provider android:name="ru.yandex.music.PrivateProvider" '
                    'android:authorities="ru.yandex.music.files;com.yandex.global.provider"/>'
                    '<activity android:name="ru.yandex.music.main.MainScreenActivity"/>'
                    '</application>' + END)
        rewritten, stats = patch_manifest(manifest.encode())
        clone = ET.fromstring(rewritten)
        self.assertEqual(clone.attrib["package"], DEST)
        self.assertEqual(clone.find("./application/provider").attrib[ANDROID+"authorities"],
                         "ru.yandex.music.files;com.yandex.global.provider")
        self.assertEqual(clone.find("./application/activity").attrib[ANDROID+"name"],
                         "ru.yandex.music.main.MainScreenActivity")
        self.assertEqual(stats["global_appmetrica_provider_rewrites"], 0)

    def test_publisher_signature_declaration_removed_only_from_independent_clone(self):
        manifest=(BASE +
                  '<permission android:name="com.yandex.permission.READ_CREDENTIALS" '
                  'android:protectionLevel="signature"/>'
                  '<uses-permission android:name="com.yandex.permission.READ_CREDENTIALS"/>'
                  '<application/>' + END)
        result, stats=patch_manifest(manifest.encode())
        tree=ET.fromstring(result)
        self.assertEqual(len(tree.findall("permission")), 0)
        self.assertEqual(len(tree.findall("uses-permission")), 1)
        self.assertEqual(stats["duplicate_publisher_permission_declarations_removed"], 1)

    def test_wrong_source_package_fails_closed(self):
        manifest=BASE.replace("ru.yandex.music", "not.publisher") + '<application/>' + END
        with self.assertRaisesRegex(ValueError, "MANIFEST_SOURCE_IDENTITY_MISMATCH"):
            patch_manifest(manifest.encode())


if __name__ == "__main__":
    unittest.main()
