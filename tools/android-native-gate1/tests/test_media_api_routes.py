"""Whitelisted media-route annotation tests; only synthetic DEX."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_inspect_android_host import synthetic_dex
from trace_media_api_routes import inspect_media_route_annotations,ROUTES
class MediaApiAnnotationTests(unittest.TestCase):
    def test_no_route_in_synthetic_dex(self):
        r=inspect_media_route_annotations(synthetic_dex())
        self.assertEqual(r["route_matches"],[])
        self.assertEqual(r["method_annotations_examined"],0)
        self.assertEqual(r["evidence"],"ANNOTATION_STATIC_ONLY_NOT_PROOF_OF_RUNTIME_STREAM_SELECTION")
    def test_route_allowlist_is_narrow(self):
        self.assertIn("resources/v2/file-info",ROUTES)
        self.assertNotIn("Authorization",ROUTES)
        self.assertNotIn("plays",ROUTES)
if __name__=="__main__":
    unittest.main()
