"""Read-only neighboring invocation tracer contract tests."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_inspect_android_host import synthetic_dex
from trace_audio_neighbors import inspect_neighbors

class NeighborTests(unittest.TestCase):
    def test_unrelated_dex_produces_no_candidate(self):
        report=inspect_neighbors(synthetic_dex())
        self.assertEqual(report["method_id_candidates"],0)
        self.assertEqual(report["bounded_inbound_calls"],[])
        self.assertEqual(report["qdw_a_bodies"],[])
        self.assertEqual(report["errors"],[])
        self.assertEqual(report["verdict"],"STATIC_NOT_RUNTIME_PLAYER_SOURCE_PROOF")

if __name__=="__main__":
    unittest.main()
