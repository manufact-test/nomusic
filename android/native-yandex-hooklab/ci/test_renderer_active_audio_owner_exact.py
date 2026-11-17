#!/usr/bin/env python3
"""Fail-closed static 2025 exact audio renderer / queue field fixtures."""
import unittest
from renderer_active_audio_owner_exact import (
    ENGINE, QUEUE, RENDERER, RENDERER_BASE, HOLDER,
    ENGINE_BREAK, ENGINE_RESET, ENGINE_ENABLE, renderer_subtree,
    signature_rows, TRACK_TYPE, GET_STATE,
)
class AudioLiveGate(unittest.TestCase):
    def test_exact_2025_engine_and_holder_contract(self):
        self.assertEqual(ENGINE_BREAK,(ENGINE,"break","()V"))
        self.assertEqual(ENGINE_RESET,(ENGINE,"class","([ZJ)V"))
        self.assertEqual(ENGINE_ENABLE,(ENGINE,"catch","(Lxh6;IZJ)V"))
        self.assertEqual(QUEUE,"Landroidx/media3/exoplayer/h;")
        self.assertEqual(HOLDER,"Lxh6;")
    def test_must_have_renderer_interface_and_base(self):
        with self.assertRaisesRegex(ValueError,"ROOT_MISSING"):
            renderer_subtree({})
        with self.assertRaisesRegex(ValueError,"BASE_NOT_INTERFACE_IMPL"):
            renderer_subtree({RENDERER:{"parent":None,"interfaces":[]},
                RENDERER_BASE:{"parent":"Lunknown;","interfaces":[]}})
    def test_renderer_subtree_obeys_exact_hierarchy(self):
        defs={RENDERER:{"parent":None,"interfaces":[]},
              RENDERER_BASE:{"parent":"Ljava/lang/Object;","interfaces":[RENDERER]},
              "Laudio;":{"parent":RENDERER_BASE,"interfaces":[]},
              "Lvideo;":{"parent":RENDERER_BASE,"interfaces":[]},
              "Lunrelated;":{"parent":"Ljava/lang/Object;","interfaces":[]}}
        self.assertEqual(renderer_subtree(defs),{RENDERER,RENDERER_BASE,"Laudio;","Lvideo;"})
    def test_track_type_and_state_exact_descriptor_only(self):
        methods={(RENDERER,"getTrackType","()I"):(None,0,0),
                 (RENDERER_BASE,"getState","()I"):(None,0,20),
                 ("Laudio;","getTrackType","()Ljava/lang/String;"):(None,0,20),
                 ("Lunrelated;","getState","()I"):(None,0,20)}
        types=signature_rows(methods,{RENDERER,RENDERER_BASE},TRACK_TYPE)
        states=signature_rows(methods,{RENDERER,RENDERER_BASE},GET_STATE)
        self.assertEqual(len(types),1)
        self.assertEqual(types[0]["owner"],RENDERER)
        self.assertFalse(types[0]["has_code"])
        self.assertEqual(len(states),1)
        self.assertTrue(states[0]["has_code"])
    def test_no_selected_track_claim_from_static(self):
        import inspect
        import renderer_active_audio_owner_exact as m
        source=inspect.getsource(m.analyze_signed)
        self.assertIn('"currently_audible_track_or_celikom_replacement_proven":False',source)
        self.assertIn('"audio_type_runtime_value_1_observed":False',source)
        self.assertIn('"started_state_runtime_value_2_observed":False',source)
if __name__=="__main__":
    unittest.main()
