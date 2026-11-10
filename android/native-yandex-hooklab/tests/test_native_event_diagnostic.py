import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnose_emulator import observer_event_category, TAG

class NativeHookDiagnosticRedactionTests(unittest.TestCase):
    def test_recognized_aggregate_counts_only(self):
        cases = {
            "observer: native file-info converter hooks armed; read-only": "HOOKS_ARMED",
            "observer: platform metadata witness armed; counts only": "METADATA_HOOK_ARMED",
            "observer: modern file-info conversion count=1": "CONVERSION_WITNESSED",
            "observer: platform-media-metadata-update metadata update count=1": "METADATA_WITNESSED",
            "observer: temporal-only aggregate single=2 ambiguous=5 no-source=3 clock-reset=0 metadata-updates=10 last-category=MULTIPLE_FILEINFO_AMBIGUOUS": "TEMPORAL_ORDER_AGGREGATE",
        }
        for message, expected in cases.items():
            self.assertEqual(observer_event_category("I/" + TAG + ": " + message),expected)
    def test_does_not_return_raw_sensitive_values(self):
        self.assertIsNone(observer_event_category("D/other-app: observer: file-info conversion count=2"))
        self.assertIsNone(observer_event_category("I/" + TAG + ": Metadata title=SECRET"))
        self.assertIsNone(observer_event_category("I/" + TAG + ": hello"))
        self.assertEqual(observer_event_category("I/" + TAG + ": observer: temporal-only aggregate single=5 actor=PRIVATE_USER"),
                         "TEMPORAL_ORDER_AGGREGATE")

if __name__=="__main__":
    unittest.main()
