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

    def test_media_service_public_bind_is_only_candidate(self):
        xml = """
E: manifest
  E: application
    E: service
      A: android:name="x.Media3Library"
      A: android:exported="true"
      E: intent-filter
        E: action
          A: android:name="androidx.media3.session.MediaLibraryService"
    E: service
      A: android:name="x.PrivateSession"
      A: android:exported="false"
      E: intent-filter
        E: action
          A: android:name="androidx.media3.session.MediaSessionService"
    E: service
      A: android:name="x.GuardedMediaBrowser"
      A: android:exported="true"
      A: android:permission="private.SIGNATURE_ONLY"
      E: intent-filter
        E: action
          A: android:name="android.media.browse.MediaBrowserService"
    E: service
      A: android:name="x.OtherNonMedia"
      A: android:exported="true"
"""
        summary = collect_components(xml)
        surface = summary["media_session_surface"]
        self.assertEqual(surface["media_services_declared"], 3)
        self.assertEqual(surface["media_browser_action"], 1)
        self.assertEqual(surface["media3_session_action"], 1)
        self.assertEqual(surface["media3_library_action"], 1)
        self.assertEqual(surface["exported_no_manifest_permission_candidates"], 1)
        self.assertEqual(surface["exported_permission_guarded"], 1)
        self.assertEqual(surface["unexported"], 1)
        self.assertFalse(surface["runtime_session_or_commands_observed"])
        self.assertFalse(surface["any_native_source_change_proven"])
        self.assertNotIn("private.SIGNATURE_ONLY", repr(summary))
        self.assertNotIn("x.Media3Library", repr(summary))

    def test_inherited_application_permission_and_disabled_service(self):
        xml = """
E: manifest
  E: application
    A: android:permission="private.INHERITED_GUARD"
    E: service
      A: android:exported="true"
      E: intent-filter
        E: action
          A: android:name="android.media.browse.MediaBrowserService"
    E: service
      A: android:exported="true"
      A: android:enabled="false"
      E: intent-filter
        E: action
          A: android:name="androidx.media3.session.MediaSessionService"
"""
        summary = collect_components(xml)["media_session_surface"]
        self.assertEqual(summary["exported_no_manifest_permission_candidates"], 0)
        self.assertEqual(summary["exported_permission_guarded"], 2)
        self.assertEqual(summary["disabled"], 1)

    def test_no_implicit_exported_or_source_inference(self):
        xml = """
E: manifest
  E: application
    E: service
      E: intent-filter
        E: action
          A: android:name="androidx.media3.session.MediaSessionService"
"""
        surface = collect_components(xml)["media_session_surface"]
        self.assertEqual(surface["export_unspecified"], 1)
        self.assertEqual(surface["exported_no_manifest_permission_candidates"], 0)
        self.assertFalse(surface["any_native_source_change_proven"])

    def test_private_values_never_returned(self):
        xml = 'E: provider\n A: android:authorities="SECRET_PRIVATE"\n A: android:permission="SECRET_PERMISSION"\n'
        r=collect_components(xml)
        self.assertNotIn("SECRET", repr(r))
        self.assertTrue(r["component_roles"]["provider"]["explicit_permission_guard"])

if __name__ == "__main__":
    unittest.main()
