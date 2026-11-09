import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from clone_native_splits_ephemeral import rewrite_manifest,SOURCE,DEST

class ManifestCloneTests(unittest.TestCase):
    def test_authority_and_package_but_keep_java_classes(self):
        xml='''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="ru.yandex.music">
        <application>
          <activity android:name="ru.yandex.music.MainActivity" android:exported="true" />
          <provider android:name="ru.yandex.music.Provider" android:authorities="ru.yandex.music.files" />
          <permission android:name="ru.yandex.music.MY_PERMISSION"/>
          <uses-permission android:name="ru.yandex.music.MY_PERMISSION"/>
        </application>
        </manifest>'''
        out,m=rewrite_manifest(xml)
        t=out.decode()
        self.assertIn(DEST,t)
        self.assertIn('ru.yandex.music.MainActivity',t)
        self.assertIn('ru.yandex.music.Provider',t)
        self.assertNotIn('ru.yandex.music.files"',t)
        self.assertEqual(m["provider_authorities"],1)
        self.assertEqual(m["declared_permissions"],2)
        self.assertEqual(m["unchanged_component_classes"],2)

    def test_reject_non_target(self):
        with self.assertRaisesRegex(ValueError,"MANIFEST_SOURCE_IDENTITY_MISMATCH"):
            rewrite_manifest('<manifest package="something.other"/>')

    def test_reject_shared_user_id(self):
        with self.assertRaisesRegex(ValueError,"SHARED_USER_ID_UNSUPPORTED"):
            rewrite_manifest('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="ru.yandex.music" android:sharedUserId="ru.yandex.music"/>')

if __name__=="__main__":unittest.main()
