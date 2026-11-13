"""Only synthetic public API descriptors; no publisher APK required."""
import unittest
from a1_private_2025_audio_entrypoints import PUBLIC_METHODS, classify, summarize_methods, count_direct_public_invocations,public_extractor_shape,extractor_argument_shape,summarize_mediadatasource_inheritance,make_ephemeral_mediadatasource_targets

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


    def test_mediadatasource_subclasses_including_indirect_are_private(self):
        parents={
            "Lvendor/private/A;":"Landroid/media/MediaDataSource;",
            "Lvendor/private/B;":"Lvendor/private/A;",
            "Lunrelated/X;":"Ljava/lang/Object;",
            "Lcyclic/A;":"Lcyclic/B;",
            "Lcyclic/B;":"Lcyclic/A;",
        }
        x=summarize_mediadatasource_inheritance(
            parents,{"Lvendor/private/A;","Lunrelated/X;"},
            {"Lvendor/private/B;"})
        self.assertEqual(x["direct_2025_mediadatasource_subclasses_bounded"],1)
        self.assertEqual(x["transitive_2025_mediadatasource_subclasses_bounded"],2)
        self.assertEqual(x["descendant_readat_method_bodies_bounded"],1)
        self.assertEqual(x["descendant_getsize_method_bodies_bounded"],1)
        self.assertFalse(x["current_playback_or_current_track_proven"])
        self.assertFalse(x["third_party_class_names_disclosed"])
        self.assertNotIn("vendor/private",str(x))

    def test_generated_private_media_target_is_synthetic_and_never_logged(self):
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory(prefix="exit-callsite-witness-module-") as root:
            target=Path(root)/"PrivateMediaDataSourceTargets.java"
            supers={
                "Lexample/One;":"Landroid/media/MediaDataSource;",
                "Lexample/Two;":"Landroid/media/MediaDataSource;",
            }
            amount=make_ephemeral_mediadatasource_targets(
                target,supers,set(supers),set(supers))
            self.assertEqual(amount,2)
            data=target.read_text()
            self.assertIn("final class PrivateMediaDataSourceTargets",data)
            self.assertIn("example.One",data)
            self.assertIn("example.Two",data)
            with self.assertRaises(RuntimeError):
                make_ephemeral_mediadatasource_targets(
                    target,supers,set(supers),set(supers))
            self.assertNotIn("example.One",str(amount))

    def test_exact_public_extractor_argument_shapes_never_export_paths(self):
        self.assertEqual(public_extractor_shape(["Landroid/content/Context;","Landroid/net/Uri;"]),
                         "CONTEXT_URI")
        self.assertEqual(public_extractor_shape(["Ljava/io/FileDescriptor;","J","J"]),
                         "FD_OFFSET_LENGTH")
        self.assertEqual(public_extractor_shape(["Ljava/lang/String;"]),
                         "STRING_UNKNOWN_URI_OR_FILE")
        self.assertEqual(public_extractor_shape(["Landroid/media/MediaDataSource;"]),
                         "MEDIA_DATA_SOURCE")
        self.assertEqual(public_extractor_shape(["Lvendor/private/Stream;"]), "OTHER_PUBLIC_SHAPE")

    def test_bounded_dex_public_proto_decoder(self):
        import struct
        raw=bytearray(140)
        # proto_ids_size=1, proto_ids_off=100, parameters_off=120.
        struct.pack_into("<II",raw,72,1,100)
        struct.pack_into("<I",raw,108,120)
        struct.pack_into("<I",raw,120,2)
        struct.pack_into("<HH",raw,124,4,5)
        class Fake:
            data=bytes(raw)
            def method_signature(self,index):
                return ("Landroid/media/MediaExtractor;","setDataSource",0)
            def type(self,index):
                return {4:"Landroid/content/Context;",5:"Landroid/net/Uri;"}[index]
        self.assertEqual(extractor_argument_shape(Fake(),0),"CONTEXT_URI")
        self.assertEqual(extractor_argument_shape(Fake(),1),"CONTEXT_URI")

    def test_exact_dex_invoke_instructions_not_just_method_references(self):
        class MockDex:
            method_count=4
            def method(self,index):
                return [
                    ("Landroid/media/MediaExtractor;","setDataSource"),
                    ("Landroid/media/MediaPlayer;","prepare"),
                    ("Landroid/media/AudioTrack;","write"),
                    ("Lprivate/secrets/Raw;","open"),
                ][index]
            def code_methods(self):
                # invoke-virtual {v0}, method @0 ; return-void
                yield 7,bytes([0x6e,0x10,0x00,0x00,0x00,0x00,0x0e,0x00])
                # invoke-virtual {v0}, method @2 ; return-void
                yield 9,bytes([0x6e,0x10,0x02,0x00,0x00,0x00,0x0e,0x00])
                # Unsupported opcode must not be read as an invoke.
                yield 11,bytes([0x79,0x00])
        x=count_direct_public_invocations(MockDex())
        self.assertEqual(x["direct_public_invocation_counts"]["ANDROID_MEDIA_EXTRACTOR_SOURCE"],1)
        self.assertEqual(x["direct_public_invocation_counts"]["ANDROID_AUDIO_TRACK_OUTPUT"],1)
        self.assertEqual(x["direct_public_invocation_counts"]["ANDROID_MEDIA_PLAYER_PREPARE"],0)
        self.assertEqual(x["decoded_code_bodies_bounded"],2)
        self.assertEqual(x["undecoded_code_bodies_bounded"],1)
        self.assertFalse(x["executed_on_real_player_proven"])
        self.assertNotIn("Raw",str(x))

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
