import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_native_identity_phase2_ephemeral import (
    omit_shadowed_signature_permission_declarations
)

ANDROID = "http://schemas.android.com/apk/res/android"
ORIGINAL = """<manifest xmlns:android="http://schemas.android.com/apk/res/android"
package="pro.celikom.yandex.nativeclonelab">
<permission android:name="com.yandex.permission.READ_CREDENTIALS" android:protectionLevel="signature"/>
<permission android:name="com.yandex.music.RELAY_PERMISSION" android:protectionLevel="signature"/>
<uses-permission android:name="com.yandex.permission.READ_CREDENTIALS"/>
<application android:label="test"/>
</manifest>"""

class ShadowedSignatureDeclarationTests(unittest.TestCase):
    def test_issuer_permissions_not_redeclared_but_still_requested(self):
        out, count = omit_shadowed_signature_permission_declarations(ORIGINAL.encode())
        text = out.decode()
        self.assertEqual(2, count)
        self.assertNotIn("<permission ", text)
        self.assertIn("uses-permission", text)
        self.assertIn("com.yandex.permission.READ_CREDENTIALS", text)
        self.assertIn("<application", text)

    def test_refuse_protection_weakening(self):
        with self.assertRaisesRegex(Exception, "SHADOWED_PERMISSION_PROTECTION_LEVEL_DRIFT"):
            omit_shadowed_signature_permission_declarations(
                ORIGINAL.replace('android:protectionLevel="signature"',
                                 'android:protectionLevel="dangerous"', 1).encode())

    def test_refuse_incomplete_declaration_set(self):
        with self.assertRaisesRegex(Exception, "SIGNED_DUPLICATE_PERMISSION_SET_DRIFT"):
            omit_shadowed_signature_permission_declarations(
                ORIGINAL.replace('<permission android:name="com.yandex.music.RELAY_PERMISSION" android:protectionLevel="signature"/>', '').encode())

if __name__ == "__main__":
    unittest.main()
