"""Native FileInfo API caller graph checks on synthetic data only."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_inspect_android_host import synthetic_dex
from trace_source_api_consumers import trace_source_api_calls
class NativeFileInfoCallsTests(unittest.TestCase):
    def test_unrelated_dex_is_not_runtime_hook(self):
        r=trace_source_api_calls(synthetic_dex())
        self.assertEqual(r["target_method_refs"],0)
        self.assertEqual(r["callsite_count"],0)
        self.assertEqual(r["bounded_callsite_neighborhoods"],[])
        self.assertEqual(r["evidence"],"STATIC_GRAPH_ONLY_NOT_YET_A_PLAYER_SOURCE_HOOK")
if __name__=="__main__":
    unittest.main()
