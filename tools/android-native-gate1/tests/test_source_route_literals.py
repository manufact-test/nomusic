"""Exact route-literal scanner negative tests without APK."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_inspect_android_host import synthetic_dex
from trace_source_route_literals import source_route_scan,safe_route

class SourceRouteTests(unittest.TestCase):
    def test_sensitive_values_never_eligible(self):
        self.assertFalse(safe_route("Authorization: Bearer secret"))
        self.assertFalse(safe_route("token_id_12345"))
        self.assertFalse(safe_route("plays"))
        self.assertFalse(safe_route("https://api.music.yandex.net/stream?token=123"))
    def test_source_candidates_are_routes(self):
        self.assertTrue(safe_route("tracks/download-info"))
        self.assertTrue(safe_route("playback/source/{id}"))
    def test_no_apk_no_false_source_proof(self):
        out=source_route_scan(synthetic_dex())
        self.assertEqual(out["matching_strings_total"],0)
        self.assertEqual(out["const_string_usage_examples"],[])
        self.assertEqual(out["verdict"],"STATIC_ONLY_ROUTE_LITERALS_NOT_DECODER_HOOK")
if __name__=="__main__":
    unittest.main()
