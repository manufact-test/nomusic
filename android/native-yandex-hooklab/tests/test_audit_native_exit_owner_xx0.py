"""Focused instruction-width regression for signed-only xx0.run audit."""
import pathlib
import struct
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from audit_native_exit_owner_xx0 import control_flow_shape, guard_path_evidence

class FakeDex:
    def __init__(self, instructions, tries=0):
        self.data = bytearray(16 + 2 * len(instructions))
        struct.pack_into("<H", self.data, 6, tries)
        struct.pack_into("<I", self.data, 12, len(instructions))
        for n, item in enumerate(instructions):
            struct.pack_into("<H", self.data, 16 + 2 * n, item)
    def bounds(self, off, size):
        if off < 0 or off + size > len(self.data):
            raise ValueError("out of bounds")
    def u32(self, off):
        self.bounds(off, 4)
        return struct.unpack_from("<I", self.data, off)[0]
    def u16(self, off):
        self.bounds(off, 2)
        return struct.unpack_from("<H", self.data, off)[0]

class BranchShape(unittest.TestCase):
    def test_two_instruction_calls_and_no_branches(self):
        # invoke-static 3 code units, return-void 1
        dex = FakeDex([0x0071, 1, 0, 0x000e])
        result = control_flow_shape(dex, 0)
        self.assertEqual(result["if_branch_count_bounded"], 0)
        self.assertEqual(result["return_count_bounded"], 1)
        self.assertTrue(result["scan_complete"])
        self.assertTrue(result["absence_of_branches_not_proof_of_unconditional_execution"])

    def test_if_goto_switch_are_separate(self):
        # if-eqz width2; goto width1; return width1
        dex = FakeDex([0x0038, 0x0000, 0x0028, 0x000e], tries=2)
        result = control_flow_shape(dex, 0)
        self.assertEqual(result["if_branch_count_bounded"], 1)
        self.assertEqual(result["goto_count_bounded"], 1)
        self.assertEqual(result["try_region_count_bounded"], 2)

    def test_guard_path_no_invocations_returns_false_flags(self):
        dex = FakeDex([0x0038, 0x0003, 0x000e, 0x000e])
        x = guard_path_evidence(dex, 0)
        self.assertEqual(x["kill_process_invocations"], 0)
        self.assertEqual(x["control_flow_guarding_kill_count_bounded"], 0)
        self.assertTrue(x["all_cfg_edges_well_formed"])

    def test_guard_path_malformed_branch_target_fails_closed(self):
        from inspect_android_host import DexError
        with self.assertRaises(DexError):
            guard_path_evidence(FakeDex([0x0038, 0x7fff, 0x000e]), 0)

    def test_malformed_or_truncated_bytecode_rejected(self):
        from inspect_android_host import DexError
        with self.assertRaises(DexError):
            control_flow_shape(FakeDex([0x0071, 0x0000]), 0)

if __name__ == "__main__":
    unittest.main()
