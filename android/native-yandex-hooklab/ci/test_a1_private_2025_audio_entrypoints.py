"""Only synthetic public API descriptors; no publisher APK required."""
import unittest
from a1_private_2025_audio_entrypoints import PUBLIC_METHODS, classify, summarize_methods

class AudioEntryPointSafetyTests(unittest.TestCase):
    def test_public_media3_and_legacy_methods_classified(self):
        for role, methods in PUBLIC_METHODS.items():
            for owner,name in methods:
                self.assertEqual(classify(owner,name),role)

    def test_obfuscated_and_private_app_methods_never_leak(self):
        self.assertIsNone(classify("Lrandom/private/Secret;","open"))
        self.assertIsNone(classify("Landroidx/media3/datasource/other/Secret;","open"))
        self.assertIsNone(classify("Landroidx/media3/datasource/DataSource;","prepare"))
        self.assertIsNone(classify("Lcq7;","i0"))
        rows=[
          ("Lrandom/private/Secret;","open"),
          ("Lcq7;","i0"), ("Lga4;","d"),
          ("Landroidx/media3/datasource/DataSource;", "open"),
          ("Landroidx/media3/datasource/DataSource$Factory;", "createDataSource"),
          ("Landroidx/media3/exoplayer/ExoPlayer;","prepare")
        ]
        got=summarize_methods(rows,{1,3,5})
        self.assertEqual(got["historical_2026_candidate_symbols_present_bounded"],2)
        self.assertEqual(got["public_api_references"]["MEDIA3_DATA_SOURCE_OPEN"],1)
        self.assertEqual(got["public_api_references"]["MEDIA3_DATA_SOURCE_FACTORY"],1)
        self.assertEqual(got["public_api_references"]["MEDIA3_PLAYER_PREPARE"],1)
        self.assertEqual(got["public_api_defined_bodies"]["MEDIA3_DATA_SOURCE_OPEN"],1)
        self.assertEqual(got["public_api_defined_bodies"]["MEDIA3_PLAYER_PREPARE"],1)
        self.assertFalse(got["active_current_track_or_decoder_binding_proven"])
        for value in ("Secret","random","Lcq7","Lga4"):
            self.assertNotIn(value,str(got))

    def test_empty_and_duplicate_pure_invokes_no_execution_claim(self):
        empty=summarize_methods([])
        self.assertTrue(all(x==0 for x in empty["public_api_references"].values()))
        self.assertFalse(empty["actual_audio_or_account_observed"])
        rows=[("Landroidx/media3/datasource/DataSource;","open")]*4
        got=summarize_methods(rows,{0,1})
        self.assertEqual(got["public_api_references"]["MEDIA3_DATA_SOURCE_OPEN"],4)
        self.assertEqual(got["public_api_defined_bodies"]["MEDIA3_DATA_SOURCE_OPEN"],2)
        self.assertFalse(got["active_current_track_or_decoder_binding_proven"])

if __name__=="__main__":
    unittest.main()
