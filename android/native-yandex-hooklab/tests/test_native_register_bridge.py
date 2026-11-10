import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_native_register_bridge import (
    invoke_registers, move_object_registers, register_witnesses, instructions,
    summarize_graph
)


class FakeDex:
    def __init__(self, code_units, methods):
        self.words = [0] * 8 + code_units
        self.words[6] = len(code_units)
        self.methods = methods
    def bounds(self, off, size):
        if off < 0 or off + size > 2 * len(self.words):
            raise ValueError("OUT_OF_BOUNDS")
    def u16(self, off):
        return self.words[off // 2]
    def u32(self, off):
        return self.u16(off) | self.u16(off+2) << 16
    def method(self, idx):
        return self.methods[idx]


class RegisterBridgeTests(unittest.TestCase):
    def test_invoke_35c_register_order(self):
        # args C=2 D=3 E=4 F=5 G=6
        self.assertEqual(invoke_registers(0x72, (0x5672, 3, 0x5432)), [2,3,4,5,6])

    def test_invoke_range_registers(self):
        self.assertEqual(invoke_registers(0x78, (0x0378, 3, 20)), [20,21,22])

    def test_moves_decode(self):
        self.assertEqual(move_object_registers(0x07, (0x2107,)), (1,2))
        self.assertEqual(move_object_registers(0x08, (0x0108, 14)), (1,14))
        self.assertEqual(move_object_registers(0x09, (0x0009, 14, 21)), (14,21))

    def test_register_from_converter_to_interface(self):
        converter=("Lsw7;","y0","(Lx;)Leed;")
        interface=("Labc;","a","(Leed;)V")
        # invoke-static {v1} / move-result-object v2 / move-object v3,v2
        # invoke-interface {v3} / return-void
        code=[0x1071,0,0x0001, 0x020c, 0x2307,
              0x1072,1,0x0003, 0x000e]
        result=register_witnesses(FakeDex(code,[converter,interface]),0)
        self.assertEqual(result["converter_sites_with_object_result"],1)
        self.assertEqual(result["bounded_result_use_candidates"][0]["kind"],"invoke_interface")
        self.assertFalse(result["local_register_witness_is_decoder_proof"])

    def test_branch_terminates_taint_path(self):
        conv=("Lsw7;","z0","()Leed;")
        target=("Labc;","a","(Leed;)V")
        code=[0x0071,0,0, 0x010c, 0x0028,
              0x1071,1,0x0001, 0x000e]
        result=register_witnesses(FakeDex(code,[conv,target]),0)
        self.assertEqual(result["bounded_result_use_candidates"],[])

    def test_no_false_candidate_without_move_result(self):
        conv=("Lsw7;","y0","()Leed;")
        code=[0x0071,0,0, 0x000e]
        result=register_witnesses(FakeDex(code,[conv]),0)
        self.assertEqual(result["converter_sites_with_object_result"],0)

    def test_source_seeds_not_from_names_only(self):
        src=("Lhee;","a","()V")
        other=("Lged;","a","(Leed;)V")
        scan={"complete":True,"_source_methods":{
          "converter_caller":{src}, "model_consumer":{other}},
          "_reverse_edges":{src:{("La;","b","()V")}}}
        reverse, sources, models, neighbors=summarize_graph([scan])
        self.assertIn(src,neighbors)
        self.assertIn(other,neighbors)
        self.assertEqual(len(reverse[src]),1)

    def test_incomplete_dex_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            summarize_graph([{"complete":False}])


if __name__=="__main__":
    unittest.main()
