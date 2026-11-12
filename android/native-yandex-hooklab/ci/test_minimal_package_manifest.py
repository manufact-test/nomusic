"""Synthetic-only test: minimal package renaming excludes all other manifest edits."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from owner_2025_lspatch2_namespaced_clone_arm13 import patch_manifest, DEST, ANDROID

MANIFEST = (
    '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="ru.yandex.music">'
    '<permission android:name="com.yandex.permission.READ_CREDENTIALS" android:protectionLevel="signature"/>'
    '<application android:process="ru.yandex.music">'
    '<provider android:name="ru.yandex.music.PrivateProvider" '
    'android:authorities="ru.yandex.music.files;com.yandex.global.provider"/>'
    '<activity android:name="ru.yandex.music.main.MainScreenActivity"/>'
    '</application></manifest>'
)


class MinimalManifestCausalTest(unittest.TestCase):
    def test_only_outer_manifest_package_changes(self):
        before = ET.fromstring(MANIFEST)
        result, stats = patch_manifest(MANIFEST.encode())
        after = ET.fromstring(result)
        self.assertEqual(after.attrib["package"], DEST)
        after.set("package", "ru.yandex.music")
        self.assertEqual(ET.tostring(before), ET.tostring(after))
        self.assertEqual(stats["source_scoped_provider_rewrites"], 0)
        self.assertEqual(stats["global_appmetrica_provider_rewrites"], 0)
        self.assertEqual(stats["duplicate_publisher_permission_declarations_removed"], 0)
        self.assertEqual(after.find("./application").attrib[ANDROID+"process"],
                         "ru.yandex.music")

    def test_wrong_publisher_package_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "PACKAGE_ONLY_SOURCE_MANIFEST_IDENTITY_DRIFT"):
            patch_manifest(MANIFEST.replace("package=\"ru.yandex.music\"",
                                            "package=\"not.yandex\"").encode())


if __name__=="__main__":
    unittest.main()
