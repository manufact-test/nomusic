import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_namespaced_signature_permissions import MAP, NS, PACKAGE, namespace_clone_signature_permissions as rewrite

def manifest(protect="signature",with_request=True):
    request=('<uses-permission android:name="com.yandex.permission.READ_CREDENTIALS"/>'
             if with_request else "")
    return ('<manifest xmlns:android="http://schemas.android.com/apk/res/android" '
            'package="' + PACKAGE + '">'
            + request
            + '<permission android:name="com.yandex.permission.READ_CREDENTIALS" android:protectionLevel="' + protect + '"/>'
            '<permission android:name="com.yandex.music.RELAY_PERMISSION" android:protectionLevel="' + protect + '"/>'
            '<application android:name="ru.yandex.music.YMApplication">'
            '<service android:name="ru.yandex.music.Service" android:permission="com.yandex.music.RELAY_PERMISSION"/>'
            '</application></manifest>')

class NamespacedPermissionTest(unittest.TestCase):
    def test_all_publisher_signature_names_removed_from_own_manifest(self):
        changed,flags=rewrite(manifest().encode())
        self.assertEqual(flags,{"declarations":2,"requests":1,"component_references":1})
        tree=ET.fromstring(changed)
        self.assertEqual(tree.get("package"),PACKAGE)
        self.assertEqual({x.get(NS+"name") for x in tree.findall("permission")},set(MAP.values()))
        self.assertEqual({x.get(NS+"protectionLevel") for x in tree.findall("permission")},{"signature"})
        self.assertEqual(tree.find("application").get(NS+"name"),"ru.yandex.music.YMApplication")
        self.assertIn(MAP["com.yandex.permission.READ_CREDENTIALS"],str(changed))
        for original in MAP:
            self.assertNotIn(('"' + original + '"').encode(),changed)
    def test_never_rename_on_issuer_signed_original(self):
        with self.assertRaisesRegex(ValueError,"CLONE_ONLY"):
            rewrite(manifest().replace(PACKAGE,"ru.yandex.music").encode())
    def test_preserve_signature_protection_level(self):
        with self.assertRaisesRegex(ValueError,"ORIGINAL_SIGNATURE_PROTECTION"):
            rewrite(manifest(protect="normal").encode())
    def test_must_keep_usage_evidence(self):
        with self.assertRaisesRegex(ValueError,"REQUEST_MISSING"):
            rewrite(manifest(with_request=False).encode())

if __name__=="__main__":
    unittest.main()
