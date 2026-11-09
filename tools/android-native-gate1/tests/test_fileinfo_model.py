"""Only type/field signatures from synthetic DEX."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_inspect_android_host import synthetic_dex
from trace_fileinfo_model import inspect_fileinfo_shapes
class FileInfoModelTests(unittest.TestCase):
    def test_no_false_fileinfo_model_in_unrelated_dex(self):
        x=inspect_fileinfo_shapes(synthetic_dex())
        self.assertEqual(x["defined_targets"],{})
        self.assertEqual(x["reference_only_targets"],[])
        self.assertEqual(x["verdict"],"STATIC_DATA_MODEL_ONLY_SOURCE_HOOK_NOT_PROVEN")
if __name__=="__main__":
    unittest.main()
