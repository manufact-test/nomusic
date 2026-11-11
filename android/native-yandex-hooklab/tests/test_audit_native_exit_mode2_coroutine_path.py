"""Synthetic edge reachability checks, never inspect private original APK."""
import pathlib
import struct
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from audit_native_exit_mode2_coroutine_path import valid_cfg, reachable
from inspect_android_host import DexError


class FakeDex:
    def __init__(self, words):
        self.raw = bytearray(16 + len(words)*2)
        struct.pack_into("<I", self.raw, 12, len(words))
        for n, w in enumerate(words):
            struct.pack_into("<H", self.raw, 16+n*2, w)
    def bounds(self, o, n):
        if o < 0 or o + n > len(self.raw):
            raise DexError("Out of bounds")
    def u16(self, o):
        self.bounds(o, 2)
        return struct.unpack_from("<H", self.raw, o)[0]
    def u32(self, o):
        self.bounds(o, 4)
        return struct.unpack_from("<I", self.raw, o)[0]


class StaticGraph(unittest.TestCase):
    def test_branch_paths_and_blocked_nodes(self):
        # if-eqz v0, +3; return-void; return-void
        dex = FakeDex([0x0038, 0x0003, 0x000e, 0x000e])
        ops, graph, sw = valid_cfg(dex, 0)
        self.assertEqual(len(sw), 0)
        self.assertEqual(graph[0], [2, 3])
        self.assertTrue(reachable(graph, 0, 3))
        self.assertFalse(reachable(graph, 0, 3, excluded=0))
        self.assertFalse(reachable(graph, 2, 3))

    def test_no_unaligned_jump_allowed(self):
        with self.assertRaises(DexError):
            valid_cfg(FakeDex([0x0038, 0x7FFF, 0x000e]), 0)

    def test_exit_nodes_have_no_successors(self):
        dex = FakeDex([0x000e, 0x000e])
        _, graph, _ = valid_cfg(dex, 0)
        self.assertEqual(graph[0], [])
        self.assertFalse(reachable(graph, 0, 1))


if __name__ == "__main__":
    unittest.main()
