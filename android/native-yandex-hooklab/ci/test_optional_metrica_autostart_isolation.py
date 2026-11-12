"""Synthetic only: isolate optional analytics components without media/auth changes."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from owner_2025_lspatch2_namespaced_clone_arm13 import patch_manifest, ANDROID, DEST

HEADER='<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="ru.yandex.music">'
END='</manifest>'


class OptionalMetricaAutostartTest(unittest.TestCase):
    def test_only_known_optional_metrica_components_are_excluded(self):
        xml=(HEADER+
            '<application>'
            '<provider android:name="com.yandex.metrica.impl.Provider" android:authorities="com.yandex.metrica.provider"/>'
            '<receiver android:name="com.yandex.appmetrica.impl.Receiver"/>'
            '<service android:name="ru.yandex.music.player.PlaybackService"/>'
            '<provider android:name="com.yandex.passport.Provider" android:authorities="ru.yandex.music.passport"/>'
            '<activity android:name="ru.yandex.music.main.MainScreenActivity"/>'
            '</application>'+END)
        changed,stats=patch_manifest(xml.encode())
        tree=ET.fromstring(changed)
        names={item.attrib.get(ANDROID+"name") for item in tree.iter()
               if item.tag in ("provider","receiver","service","activity")}
        self.assertNotIn("com.yandex.metrica.impl.Provider",names)
        self.assertNotIn("com.yandex.appmetrica.impl.Receiver",names)
        self.assertIn("ru.yandex.music.player.PlaybackService",names)
        self.assertIn("com.yandex.passport.Provider",names)
        self.assertIn("ru.yandex.music.main.MainScreenActivity",names)
        self.assertEqual(tree.attrib["package"],DEST)
        self.assertEqual(stats["optional_metrica_components_excluded"],2)

    def test_independent_no_metrica_manifest_is_unchanged_by_optional_filter(self):
        xml=(HEADER+
             '<application><service android:name="ru.yandex.music.player.PlaybackService"/></application>'+END)
        changed,stats=patch_manifest(xml.encode())
        self.assertEqual(stats["optional_metrica_components_excluded"],0)
        self.assertIn(b"PlaybackService",changed)

    def test_publisher_signature_permissions_rewrite_remains_fail_closed(self):
        xml=(HEADER+'<permission android:name="com.yandex.permission.READ_CREDENTIALS" '
             'android:protectionLevel="dangerous"/><application/>'+END)
        with self.assertRaisesRegex(RuntimeError,"NAMESPACED_CLONE_PERMISSION_PROTECTION_DRIFT"):
            patch_manifest(xml.encode())


if __name__=="__main__":
    unittest.main()
