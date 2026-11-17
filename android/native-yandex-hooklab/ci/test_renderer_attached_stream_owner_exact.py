#!/usr/bin/env python3
"""A bounded exact renderer subtree, not a global playback search."""
import unittest
from renderer_attached_stream_owner_exact import (
    RENDERER, descendants_from_renderer, directly_matches_renderer,
)
def item(parent, interfaces=()):
    return {"parent":parent,"interfaces":list(interfaces),"flags":0}

class RendererExactTests(unittest.TestCase):
    def test_transitive_implementation_only(self):
        root={RENDERER:item("Ljava/lang/Object;"),
              "LDirect;":item("Ljava/lang/Object;",(RENDERER,)),
              "LConcrete;":item("LDirect;"),
              "LUnrelated;":item("Ljava/lang/Object;")}
        self.assertEqual(descendants_from_renderer(root),
                         {RENDERER,"LDirect;","LConcrete;"})
        self.assertTrue(directly_matches_renderer(root["LDirect;"]))
        self.assertFalse(directly_matches_renderer(root["LConcrete;"]))
    def test_missing_interface_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"RENDERER_EXACT_INTERFACE_MISSING"):
            descendants_from_renderer({"LUnrelated;":item("Ljava/lang/Object;")})
    def test_no_unrelated_types(self):
        root={RENDERER:item("Ljava/lang/Object;"),"LmQ8;":item("Ljava/lang/Object;"),
              "Lchild;":item("LmQ8;")}
        self.assertEqual(descendants_from_renderer(root),{RENDERER})

if __name__=="__main__":unittest.main()
