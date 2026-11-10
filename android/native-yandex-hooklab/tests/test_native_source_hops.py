import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trace_native_source_hops import call_graph_hops


class StaticSourceHopTests(unittest.TestCase):
    def test_chain_1_to_3_hops(self):
        start = ("Lsource;", "start", "()V")
        middle = ("Lmiddle;", "a", "()V")
        bridge = ("Lbridge;", "b", "()V")
        media = ("Landroidx/media3/exoplayer/source/DefaultMediaSourceFactory;",
                 "createMediaSource", "()V")
        reverse = {
            media: {bridge}, bridge: {middle},
            middle: {start},
        }
        p = call_graph_hops(reverse, {start, middle, bridge}, {media})
        self.assertEqual([len(x) - 1 for x in p], [1, 2, 3])
        self.assertEqual(p[0][-1], media)

    def test_disconnected_and_out_of_scope_are_excluded(self):
        a = ("La;", "a", "()V")
        b = ("Lb;", "b", "()V")
        c = ("Lc;", "c", "()V")
        d = ("Ld;", "d", "()V")
        e = ("Le;", "e", "()V")
        sink = ("Landroidx/media3/exoplayer/ExoPlayerImpl;", "prepare", "()V")
        reverse = {sink: {e}, e: {d}, d: {c}, c: {b}, b: {a}}
        self.assertEqual(call_graph_hops(reverse, {a, b, c, d}, {sink}),
                         [[d, e, sink], [c, d, e, sink]])
        self.assertFalse(call_graph_hops({}, {a}, {sink}))

    def test_hop_limit_rejects_unbounded_search(self):
        with self.assertRaises(ValueError):
            call_graph_hops({}, set(), set(), 9)

    def test_cycle_does_not_loop(self):
        a = ("La;", "a", "()V")
        b = ("Lb;", "b", "()V")
        sink = ("Lc;", "m", "()V")
        paths = call_graph_hops({a: {b}, b: {a}, sink: {a}}, {a, b}, {sink})
        self.assertEqual(len(paths), 2)
        self.assertLessEqual(max(map(len, paths)), 4)


if __name__ == "__main__":
    unittest.main()
