import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnose_emulator import observer_event_category, TAG

class PlaybackStatePrivacyLogTests(unittest.TestCase):
    def test_safe_categories(self):
        self.assertEqual(observer_event_category("I/" + TAG + ": observer: published-playback aggregate reports=20 transitions=10 rapid-play-pause=4"), "PLAYBACK_STATE_AGGREGATE")
        self.assertEqual(observer_event_category("I/" + TAG + ": observer: published playback-state witness armed; counts only"), "PLAYBACK_STATE_HOOK_ARMED")
    def test_unknown_data_ignored(self):
        self.assertIsNone(observer_event_category("I/other: observer: published-playback aggregate reports=2"))
        self.assertIsNone(observer_event_category("I/" + TAG + ": observer: raw media URL https://example.com"))
if __name__ == "__main__":
    unittest.main()
