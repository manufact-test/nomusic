"""Privacy-safe parser tests for our OWN app's categorical public-session result."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parent / "public_session_ci.py"
spec = importlib.util.spec_from_file_location("celikom_probe", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProbeResultTests(unittest.TestCase):
    def test_valid_boolean_only_result(self):
        sample = ("2026 I/CELIKOMPublicSessionProbe: PROBE_RESULT "
                  "state=CONNECTED_READONLY eligible=1 connected=true "
                  "change_items=false set_item=false get_item=true "
                  "play_pause=true seek=true "
                  "browser_connected=false platform_play_from_uri=false "
                  "platform_play_from_media_id=false "
                  "source_replace_proven=false audio_tested=false")
        result = module.sanitize_logcat(sample)
        self.assertEqual(result["state"], "CONNECTED_READONLY")
        self.assertFalse(result["command_change_media_items_advertised"])
        self.assertTrue(result["media3_session_connected"])
        self.assertNotIn("uri", repr(result).lower())

    def test_non_matching_line_or_private_data_rejected(self):
        self.assertIsNone(module.sanitize_logcat(
            "PROBE_RESULT state=CONNECTED_READONLY eligible=1 "
            "connected=true token=secret"))
        self.assertIsNone(module.sanitize_logcat(
            "PROBE_RESULT state=BOGUS eligible=1 connected=true "
            "change_items=true set_item=true get_item=true "
            "play_pause=true seek=true browser_connected=false "
            "platform_play_from_uri=false platform_play_from_media_id=false "
            "source_replace_proven=false audio_tested=false"))

    def test_platform_browser_connected_only(self):
        sample = ("PROBE_RESULT state=PLATFORM_BROWSER_CONNECTED eligible=1 "
                  "connected=false change_items=false set_item=false "
                  "get_item=false play_pause=false seek=false "
                  "browser_connected=true platform_play_from_uri=true "
                  "platform_play_from_media_id=false "
                  "source_replace_proven=false audio_tested=false")
        result = module.sanitize_logcat(sample)
        self.assertTrue(result["platform_browser_connected"])
        self.assertTrue(result["platform_action_play_from_uri"])
        self.assertFalse(result["command_change_media_items_advertised"])

    def test_inconsistent_or_excess_candidates_rejected(self):
        base = ("PROBE_RESULT state=TIMEOUT eligible=1 connected=true "
                "change_items=false set_item=false get_item=false "
                "play_pause=false seek=false "
                "browser_connected=false platform_play_from_uri=false "
                "platform_play_from_media_id=false "
                "source_replace_proven=false audio_tested=false")
        self.assertIsNone(module.sanitize_logcat(base))
        self.assertIsNone(module.sanitize_logcat(base.replace(
            "connected=true", "connected=false").replace("eligible=1","eligible=9")))


if __name__ == "__main__":
    unittest.main()
