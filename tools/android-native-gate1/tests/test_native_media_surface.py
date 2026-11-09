"""Static-only media surface tests against synthetic DEX; no proprietary payloads."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_inspect_android_host import synthetic_dex
from inventory_native_media_surface import inspect_surface

class SurfaceInventoryTests(unittest.TestCase):
    def test_media3_ref_is_not_native_android_framework_call(self):
        result=inspect_surface(synthetic_dex())
        self.assertEqual(result["android_framework_media_method_refs"],0)
        self.assertEqual(result["android_framework_media_invoke_calls"],0)
        self.assertEqual(result["type_counts"]["yandex_defined_classes"],0)
        self.assertEqual(result["evidence_level"],
                         "STATIC_ONLY_NOT_PROOF_OF_LIVE_SOURCE_SELECTION")

if __name__=="__main__":unittest.main()
