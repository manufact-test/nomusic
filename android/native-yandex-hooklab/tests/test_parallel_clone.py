import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit_parallel_clone as audit

class CloneManifestTests(unittest.TestCase):
    def test_package_bound_providers_and_schemes_counts_only(self):
        tree = '''
E: manifest (line=1)
  A: package="ru.yandex.music"
  E: application (line=2)
    E: provider (line=3)
      A: android:name(0x01)="androidx.core.content.FileProvider"
      A: android:authorities(0x01)="ru.yandex.music.files"
    E: activity (line=4)
      E: intent-filter (line=5)
        E: data (line=6)
          A: android:scheme(0x01)="yandexmusic"
    E: permission (line=7)
      A: android:name(0x01)="ru.yandex.music.permission.PUSH"
'''
        info = audit.manifest_summary(tree)
        self.assertEqual(info["providers"], 1)
        self.assertEqual(info["original_package_provider_authorities"], 1)
        self.assertEqual(info["package_bound_manifest_attributes"], 3)
        self.assertEqual(info["custom_schemes"], 1)
        self.assertEqual(info["intent_filters"], 1)
        self.assertEqual(info["custom_permissions"], 1)
        self.assertNotIn("ru.yandex.music.files", repr(info))

    def test_unrelated_provider_not_counted_as_collision(self):
        tree = 'E: provider (line=1)\nA: android:authorities(0x01)="separate.safe.provider"\n'
        info = audit.manifest_summary(tree)
        self.assertEqual(info["provider_authorities"], 1)
        self.assertEqual(info["original_package_provider_authorities"], 0)

    def test_no_export_of_user_strings(self):
        tree = 'E: activity (line=1)\nA: android:name(0x01)="https://bad.example/?token=SECRET"\n'
        self.assertNotIn("SECRET", repr(audit.manifest_summary(tree)))

    def test_shared_user_id_risk_signal(self):
        text = 'E: manifest\nA: android:sharedUserId(0x01)="any.id"'
        self.assertEqual(audit.manifest_summary(text)["shared_user_id_attributes"], 1)

if __name__ == "__main__":
    unittest.main()
