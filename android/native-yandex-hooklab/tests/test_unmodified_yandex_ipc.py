import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_unmodified_yandex_ipc import collect_components

class UnmodifiedAppIpcTests(unittest.TestCase):
    def test_exported_service_with_media_action_not_audio_replacement(self):
        xml = """
E: manifest (line=2)
  E: application (line=5)
    E: service (line=11)
      A: android:name(0x01010003)="x.Service"
      A: android:exported(0x01010010)=(type 0x12)0xffffffff
      E: intent-filter (line=14)
        E: action (line=15)
          A: android:name(0x01010003)="android.media.browse.MediaBrowserService"
    E: provider (line=22)
      A: android:exported(0x01010010)=(type 0x12)0x0
      A: android:grantUriPermissions(0x0101001b)=(type 0x12)0xffffffff
      A: android:authorities(0x01010018)="ru.yandex.music.secret"
"""
        out = collect_components(xml)
        self.assertEqual(out["component_roles"]["service"]["exported_true"], 1)
        self.assertEqual(out["component_roles"]["service"]["media_action_declared"], 1)
        self.assertEqual(out["component_roles"]["provider"]["exported_false"], 1)
        self.assertEqual(out["component_roles"]["provider"]["grant_uri_permission_true"], 1)
        self.assertNotIn("ru.yandex.music.secret", repr(out))
        self.assertIn("NO_EXTERNAL_AUDIO_REPLACEMENT_PROOF", out["external_manifest"]["manifest_claim"] if "external_manifest" in out else out["manifest_claim"])

    def test_aapt_quote_boolean_and_intent_nested(self):
        xml = """
E: manifest
  E: application
    E: activity
      A: android:exported="true"
      E: intent-filter
        E: action
          A: android:name="android.intent.action.VIEW"
    E: receiver
      A: android:exported="false"
"""
        result = collect_components(xml)
        self.assertEqual(result["component_roles"]["activity"]["exported_true"], 1)
        self.assertEqual(result["component_roles"]["receiver"]["exported_false"], 1)
        self.assertEqual(result["media_action_counts"]["android.intent.action.VIEW"], 1)

    def test_private_values_never_returned(self):
        xml = 'E: provider\n A: android:authorities="SECRET_PRIVATE"\n A: android:permission="SECRET_PERMISSION"\n'
        r=collect_components(xml)
        self.assertNotIn("SECRET", repr(r))
        self.assertTrue(r["component_roles"]["provider"]["explicit_permission_guard"])

if __name__ == "__main__":
    unittest.main()
