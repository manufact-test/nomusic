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


    def test_only_exact_extractor_overload_source_argument_is_classified(self):
        from a1_private_2025_audio_entrypoints import (
            _exact_extractor_register_origin, classify_private_extractor_sink_rows)
        from a1_private_dex_flow import decode_instructions
        import struct
        class Fake:
            def type(self,i):
                return "Lprivate/Source;" if i==7 else "Lprivate/Other;"
        # new-instance v1,type@7, invoke-virtual {v0,v1},setDataSource
        code=bytes([0x22,0x01,0x07,0x00,0x6e,0x20,0x00,0x00,0x10,0x00,
                    0x0e,0x00])
        instructions=decode_instructions(code)
        raw=_exact_extractor_register_origin(Fake(),code,instructions,1)
        self.assertEqual(raw,("NEW_INSTANCE","Lprivate/Source;"))
        summary=classify_private_extractor_sink_rows(
            [("Lprivate/Caller;",raw)],
            {"Lprivate/Source;":"Landroid/media/MediaDataSource;",
             "Lprivate/Other;":"Landroid/media/MediaDataSource;"},
            {"Lprivate/Source;","Lprivate/Other;"},
            {"Lprivate/Source;","Lprivate/Other;"})
        self.assertEqual(summary["exact_2025_extractor_mediadatasource_argument_categories"],
                         ["DIRECT_NEW_NON_TARGET"] if False else ["DIRECT_NEW_TARGET_1"])
        self.assertFalse(summary["same_decoder_active_track_proven"])
        self.assertFalse(summary["real_player_execution_proven"])
        self.assertNotIn("private/",str(summary))

    def test_extractor_source_origin_range_alias_and_ambiguous_control_flow(self):
        from a1_private_2025_audio_entrypoints import _exact_extractor_register_origin
        from a1_private_dex_flow import decode_instructions
        class Fake:
            def type(self,i): return "Lprivate/Unexpected;"
        # new-instance v2; move-object v1,v2; invoke-virtual/range {v0,v1}
        code=bytes([0x22,0x02,0x04,0x00,0x07,0x21,
                    0x74,0x02,0x00,0x00,0x00,0x00,0x0e,0x00])
        ins=decode_instructions(code)
        self.assertEqual(
            _exact_extractor_register_origin(Fake(),code,ins,2),
            ("NEW_INSTANCE","Lprivate/Unexpected;"))
        # Unconditional goto between source and sink is never traced through.
        amb=bytes([0x22,0x01,0x04,0x00,0x28,0x01,
                   0x6e,0x20,0x00,0x00,0x10,0x00])
        self.assertEqual(
            _exact_extractor_register_origin(Fake(),amb,decode_instructions(amb),2),
            ("FLOW_BOUNDARY_UNRESOLVED",None))
        # An argument passed from a caller remains unknown, no fabricated type.
        bare=bytes([0x6e,0x20,0x00,0x00,0x10,0x00])
        self.assertEqual(
            _exact_extractor_register_origin(Fake(),bare,decode_instructions(bare),0),
            ("PARAMETER_OR_CAPTURE_UNRESOLVED",None))

    def test_exact_extractor_classification_failclosed_without_target(self):
        from a1_private_2025_audio_entrypoints import classify_private_extractor_sink_rows
        x=classify_private_extractor_sink_rows(
            [("Lprivate/Caller;",("INVOKE_RETURN_OBJECT",None))],{},set(),set())
        self.assertEqual(x["exact_2025_extractor_mediadatasource_argument_categories"],
                         ["INVOKE_RETURN_OBJECT"])
        self.assertFalse(x["private_source_class_or_caller_disclosed"])
        self.assertNotIn("Caller",str(x))


    def test_public_extractor_steps_are_whitelisted_without_vendor_names(self):
        from a1_private_2025_audio_entrypoints import public_extractor_lifecycle_role
        self.assertEqual(public_extractor_lifecycle_role(
            "Landroid/media/MediaExtractor;","readSampleData"),"READ_SAMPLE_DATA")
        self.assertEqual(public_extractor_lifecycle_role(
            "Landroid/media/MediaMetadataRetriever;","getEmbeddedPicture"),"GET_EMBEDDED_PICTURE")
        self.assertIsNone(public_extractor_lifecycle_role(
            "Lprivate/Hidden;","readSampleData"))
        self.assertIsNone(public_extractor_lifecycle_role(
            "Landroid/media/MediaExtractor;","privateMethod"))

    def test_exact_media_sink_lifecycle_scans_only_same_method_and_same_class(self):
        from a1_private_2025_audio_entrypoints import (
            count_direct_public_invocations, classify_private_extractor_sink_lifecycle)
        import struct
        raw=bytearray(140)
        struct.pack_into("<II",raw,72,1,100)   # one proto at byte 100
        struct.pack_into("<I",raw,108,120)   # parameters offset
        struct.pack_into("<I",raw,120,1)     # one MediaDataSource argument
        struct.pack_into("<H",raw,124,4)
        class Mock:
            data=bytes(raw)
            method_count=4
            def type(self,i):
                return "Landroid/media/MediaDataSource;" if i==4 else "Lhidden/Other;"
            def method_signature(self,i):
                return (*self.method(i),0)
            def method(self,i):
                return [
                    ("Landroid/media/MediaExtractor;","setDataSource"),
                    ("Landroid/media/MediaExtractor;","getTrackCount"),
                    ("Landroid/media/MediaExtractor;","readSampleData"),
                    ("Lprivate/Hidden;","invoke"),
                ][i]
            def code_methods(self):
                # Sink and getTrackCount in Lprivate/Caller; readSampleData
                # in Lprivate/Other; prevent leaking either private owner.
                yield 0,bytes([0x6e,0x20,0x00,0x00,0x10,0x00,
                               0x6e,0x10,0x01,0x00,0x00,0x00,
                               0x0e,0x00])
                yield 1,bytes([0x6e,0x10,0x02,0x00,0x00,0x00,0x0e,0x00])
        # In this synthetic Dex method IDs carry framework owners themselves,
        # so same-class is the MediaExtractor owner for both methods.
        rows=[]
        count_direct_public_invocations(Mock(), [], rows)
        report=classify_private_extractor_sink_lifecycle(rows)
        self.assertTrue(report["unambiguous_single_static_sink"])
        self.assertEqual(report["same_method_public_framework_steps"],
                         ["GET_TRACK_COUNT","SET_SOURCE"])
        self.assertEqual(report["same_class_public_framework_steps"],
                         ["GET_TRACK_COUNT","READ_SAMPLE_DATA","SET_SOURCE"])
        self.assertFalse(report["same_method_reads_samples"])
        self.assertTrue(report["same_class_reads_samples"])
        self.assertFalse(report["live_playback_or_same_object_proven"])
        for private in ("Hidden","Caller","/private/"):
            self.assertNotIn(private,str(report))

    def test_exact_sink_lifecycle_multiple_callsites_is_fail_closed(self):
        from a1_private_2025_audio_entrypoints import classify_private_extractor_sink_lifecycle
        x=classify_private_extractor_sink_lifecycle([
            {"same_method_steps":["SET_SOURCE","READ_SAMPLE_DATA"],
             "same_class_steps":["READ_SAMPLE_DATA"]},
            {"same_method_steps":["SET_SOURCE"],"same_class_steps":["SET_SOURCE"]},
        ])
        self.assertFalse(x["unambiguous_single_static_sink"])
        self.assertEqual(x["same_method_public_framework_steps"],[])
        self.assertFalse(x["live_playback_or_same_object_proven"])


    def test_exact_extractor_caller_return_type_categories_redact_private_values(self):
        from a1_private_2025_audio_entrypoints import exact_extractor_caller_return_shape
        import struct
        class Fake:
            data=bytearray(140)
            def method_signature(self,_index):
                return ("Lsecret/Caller;","x",0)
            def type(self,index):
                return {
                    1:"Landroid/media/MediaExtractor;",
                    2:"V",
                    3:"Lsecret/OtherThing;",
                    4:"[B",
                    5:"Landroid/media/MediaFormat;",
                }[index]
        f=Fake()
        struct.pack_into("<II",f.data,72,1,100)
        for idx,expected in [
            (1,"RETURNS_EXTRACTOR"),(2,"RETURNS_VOID"),
            (3,"RETURNS_OTHER_OBJECT"),(4,"RETURNS_BYTES"),
            (5,"RETURNS_MEDIA_FORMAT")]:
            struct.pack_into("<I",f.data,104,idx)
            got=exact_extractor_caller_return_shape(f,0)
            self.assertEqual(got,expected)
            self.assertNotIn("secret",got)
        struct.pack_into("<II",f.data,72,0,100)
        self.assertEqual(exact_extractor_caller_return_shape(f,0),"UNREADABLE_PROTO")

    def test_exact_sink_lifecycle_includes_only_return_type_categories(self):
        from a1_private_2025_audio_entrypoints import classify_private_extractor_sink_lifecycle
        got=classify_private_extractor_sink_lifecycle([
            {"same_method_steps":["SET_SOURCE"],
             "same_class_steps":["SET_SOURCE"],
             "return_shape":"RETURNS_EXTRACTOR",
             "return_object_opcode":True}
        ])
        self.assertEqual(got["caller_return_shapes"],["RETURNS_EXTRACTOR"])
        self.assertTrue(got["caller_return_object_opcode_present"])
        self.assertFalse(got["live_playback_or_same_object_proven"])
        self.assertNotIn("Caller",str(got))

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
