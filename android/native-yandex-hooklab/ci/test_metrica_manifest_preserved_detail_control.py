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


class PassportOwnProviderAuthorityControl(unittest.TestCase):
    def test_owned_passport_providers_match_the_original_sdk_generated_uris(self):
        # Exact original Android SDK: provider lookup uses this app's own
        # Context.getPackageName(), not a provider-authority hash.
        expected={
          "com.yandex.passport.internal.provider.InternalProvider":
              "com.yandex.passport.internal.provider."+DEST,
          "com.yandex.passport.internal.authsdk.AuthSdkProvider":
              "com.yandex.passport.authsdk.provider."+DEST,
          "com.yandex.passport.internal.sso.SsoContentProvider":
              "com.yandex.passport.internal.sso."+DEST,
        }
        source={
          "com.yandex.passport.internal.provider.InternalProvider":
              "com.yandex.passport.internal.provider.ru.yandex.music",
          "com.yandex.passport.internal.authsdk.AuthSdkProvider":
              "com.yandex.passport.authsdk.provider.ru.yandex.music",
          "com.yandex.passport.internal.sso.SsoContentProvider":
              "com.yandex.passport.internal.sso.ru.yandex.music",
        }
        parts=[
            '<provider android:name="'+name+'" android:authorities="'+auth+'"/>'
            for name,auth in source.items()
        ]
        parts.append(
            '<provider android:name="com.yandex.metrica.impl.Provider"'
            ' android:authorities="com.yandex.metrica.provider"/>')
        xml=HEADER+'<application>'+''.join(parts)+'</application>'+END
        data,stats=patch_manifest(xml.encode())
        root=ET.fromstring(data)
        providers={
            p.attrib[ANDROID+"name"]:p.attrib[ANDROID+"authorities"]
            for p in root.findall("./application/provider")
        }
        for name,expected_authority in expected.items():
            self.assertEqual(providers[name],expected_authority)
            self.assertNotEqual(providers[name],source[name])
        self.assertEqual(stats["passport_sdk_own_provider_components_seen"],3)
        self.assertTrue(providers["com.yandex.metrica.impl.Provider"].startswith(
            DEST+".provider."))

    def test_previously_hashed_owned_passport_authority_must_repair(self):
        import hashlib
        original="com.yandex.passport.internal.provider.ru.yandex.music"
        old=DEST+".provider."+hashlib.sha256(
            original.encode("utf-8")).hexdigest()[:16]
        xml=(HEADER+'<application><provider '
             'android:name="com.yandex.passport.internal.provider.InternalProvider" '
             'android:authorities="'+old+'"/>'
             '</application>'+END)
        data,stats=patch_manifest(xml.encode())
        provider=ET.fromstring(data).find("./application/provider")
        self.assertEqual(provider.attrib[ANDROID+"authorities"],
                         "com.yandex.passport.internal.provider."+DEST)
        self.assertEqual(stats["passport_sdk_own_provider_components_seen"],1)

    def test_unknown_passport_authority_fails_closed(self):
        xml=(HEADER+'<application><provider '
             'android:name="com.yandex.passport.internal.provider.InternalProvider" '
             'android:authorities="unrelated.package.provider"/>'
             '</application>'+END)
        with self.assertRaises(Exception):
            patch_manifest(xml.encode())


if __name__=="__main__":
    unittest.main()
