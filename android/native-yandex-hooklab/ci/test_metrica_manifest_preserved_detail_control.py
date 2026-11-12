"""The AppMetrica SDK components stay installed; this is not a stripping experiment."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from owner_2025_lspatch2_namespaced_clone_arm13 import patch_manifest, ANDROID, DEST

HEADER='<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="ru.yandex.music">'
END='</manifest>'


class MetricaPreservedControl(unittest.TestCase):
    def test_metrica_provider_service_and_receiver_survive_in_clone(self):
        xml=(HEADER + '<application>'
            '<provider android:name="com.yandex.metrica.impl.Provider" android:authorities="com.yandex.metrica.provider"/>'
            '<receiver android:name="com.yandex.appmetrica.impl.Receiver"/>'
            '<service android:name="com.yandex.metrica.impl.Service"/>'
            '<service android:name="ru.yandex.music.player.PlaybackService"/>'
            '<activity android:name="ru.yandex.music.main.MainScreenActivity"/>'
            '</application>' + END)
        data,stats=patch_manifest(xml.encode())
        root=ET.fromstring(data)
        names={e.attrib.get(ANDROID+"name") for e in root.iter()
               if e.tag in ("provider","receiver","service","activity")}
        self.assertIn("com.yandex.metrica.impl.Provider",names)
        self.assertIn("com.yandex.appmetrica.impl.Receiver",names)
        self.assertIn("com.yandex.metrica.impl.Service",names)
        self.assertIn("ru.yandex.music.player.PlaybackService",names)
        self.assertIn("ru.yandex.music.main.MainScreenActivity",names)
        self.assertEqual(stats["optional_metrica_components_excluded"],0)
        self.assertEqual(root.attrib["package"],DEST)
        authority=root.find("./application/provider").attrib[ANDROID+"authorities"]
        self.assertTrue(authority.startswith(DEST+".provider."))

    def test_signature_declaration_avoids_duplicate_without_changing_uses(self):
        xml=(HEADER+
             '<permission android:name="com.yandex.permission.READ_CREDENTIALS" android:protectionLevel="signature"/>'
             '<uses-permission android:name="com.yandex.permission.READ_CREDENTIALS"/>'
             '<application/>'+END)
        data,stats=patch_manifest(xml.encode())
        root=ET.fromstring(data)
        self.assertEqual(len(root.findall("permission")),0)
        self.assertEqual(len(root.findall("uses-permission")),1)
        self.assertEqual(stats["duplicate_publisher_permission_declarations_removed"],1)
        self.assertEqual(stats["optional_metrica_components_excluded"],0)


if __name__=="__main__":
    unittest.main()
