import unittest
from audit_native_selected_item_handoff import (
    parse_types, written_register, MODEL, WRAPPER, DESCRIPTOR_BUILDER,
    PLAYER_OWNERS, PLAYER_METHODS, MEDIA_SESSION_OWNER,
    MEDIA_SESSION_METADATA_METHODS, MEDIA_SESSION_STATE_METHODS,
    DECODER_BOUNDARY_METHODS, EDITION_MARKERS, GENERATION_MARKERS,
    classify_boundary_call, boundary_callsite_census,
    summarize_track_field_owner_inventory, summarize_boundary_callsite_census,
    candidate_owner_descriptors, typed_parameter_registers,
    trace_identity_method, select_next_identity_method_refs,
    build_dex_control_flow,
    summarize_boundary_callsite_owner_profiles, method_signature_type_profile,
    select_exact_interface_contracts, select_audio_output_focus_methods,
    trace_byte_buffer_parameter, expand_invoke_register_types,
    audio_output_dispatch_contracts, owner_ancestry_profiles,
    trace_renderer_buffer_field_candidates, collect_sink_buffer_field_refs,
    trace_renderer_buffer_field_writes, trace_native_track_coroutine_continuation,
    trace_track_value_to_exact_field_store
)

class SelectedItemAuditTests(unittest.TestCase):
    def test_method_descriptor_parser_handles_objects_arrays_and_wide_values(self):
        self.assertEqual(parse_types("(ILjava/lang/String;[B[[JDLru/yandex/music/data/audio/o;)V"),
            ["I", "Ljava/lang/String;", "[B", "[[J", "D", MODEL])

    def test_pinned_input_is_the_exact_2025_owner_asset(self):
        from audit_native_selected_item_handoff import (
            PINNED_XAPK_BYTES, PINNED_XAPK_SHA256, PUBLISHER_VERSION
        )
        self.assertEqual(PINNED_XAPK_BYTES, 45961661)
        self.assertEqual(PINNED_XAPK_SHA256,
            "8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053")
        self.assertEqual(PUBLISHER_VERSION, "2025.10.4 #120.1gpr")

    def test_album_model_is_a_distinct_native_object(self):
        from audit_native_selected_item_handoff import ALBUM_MODEL
        self.assertEqual(ALBUM_MODEL, "Lru/yandex/music/data/audio/Album;")
        self.assertNotEqual(ALBUM_MODEL, MODEL)

    def test_album_constructor_verifier_requires_same_object_stored_on_track(self):
        from unittest.mock import patch
        from audit_native_selected_item_handoff import (
            album_constructor_argument_store, ALBUM_MODEL
        )
        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:2}[offset]
        method=(MODEL,"<init>",f"({ALBUM_MODEL})V")
        direct=[(0,0x5b,[0x235b,0]),(1,0x0e,[0x000e])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=direct), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=(MODEL,"hidden",ALBUM_MODEL)):
            result=album_constructor_argument_store(FakeDex(),method,0,100)
        self.assertEqual(result["album_parameter_index"],0)
        self.assertTrue(result["stores_same_album_argument_on_track"])
        self.assertEqual(result["album_argument_field_write_receiver_alias_count"],1)

        moved=[(0,0x07,[0x0307]),(1,0x5b,[0x205b,0]),(2,0x0e,[0x000e])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=moved), \
             patch("audit_native_selected_item_handoff.move_object_registers",
                   side_effect=lambda op,words:(0,3) if op==0x07 else None), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=(MODEL,"hidden",ALBUM_MODEL)):
            result=album_constructor_argument_store(FakeDex(),method,0,100)
        self.assertTrue(result["stores_same_album_argument_on_track"])

        wrong_receiver=[(0,0x5b,[0x135b,0]),(1,0x0e,[0x000e])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=wrong_receiver), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=(MODEL,"hidden",ALBUM_MODEL)):
            result=album_constructor_argument_store(FakeDex(),method,0,100)
        self.assertFalse(result["stores_same_album_argument_on_track"])

        branched=[(0,0x28,[0x0028]),(1,0x5b,[0x205b,0]),(2,0x0e,[0x000e])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=branched), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=(MODEL,"hidden",ALBUM_MODEL)):
            result=album_constructor_argument_store(FakeDex(),method,0,100)
        self.assertFalse(result["stores_same_album_argument_on_track"])

    def test_track_album_copy_flow_requires_album_arg_on_new_track_result(self):
        from unittest.mock import patch
        from audit_native_selected_item_handoff import track_album_copy_flow, ALBUM_MODEL
        class FakeDex:
            def u16(self, offset):
                return {100:8,102:7}[offset]
            def descriptor(self, index):
                return MODEL
            def method(self, index):
                return (MODEL,"<init>",f"({ALBUM_MODEL})V")
        method=(MODEL,"new",f"({MODEL}J{ALBUM_MODEL}Ljava/util/List;LfCa;I){MODEL}")
        rows=[(0,0x22,[0x0022,0]),(1,0x70,[0x0070,0,0]),(2,0x11,[0x0011])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=rows), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[0,4]):
            result=track_album_copy_flow(FakeDex(),method,0x8,100)
        self.assertTrue(result["album_argument_passed_to_new_track_constructor"])
        self.assertTrue(result["returns_new_track"])
        with patch("audit_native_selected_item_handoff.instructions",return_value=rows), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[0,5]):
            result=track_album_copy_flow(FakeDex(),method,0x8,100)
        self.assertFalse(result["album_argument_passed_to_new_track_constructor"])

    def test_track_album_copy_method_requires_exact_track_and_album_inputs(self):
        from audit_native_selected_item_handoff import is_native_track_album_copy_method, ALBUM_MODEL
        good=(MODEL,"new",f"({MODEL}J{ALBUM_MODEL}Ljava/util/List;LfCa;I){MODEL}")
        bad=(MODEL,"new",f"({MODEL}JLjava/lang/String;Ljava/util/List;LfCa;I){MODEL}")
        wrong_return=(MODEL,"new",f"({MODEL}J{ALBUM_MODEL}Ljava/util/List;LfCa;I)V")
        self.assertTrue(is_native_track_album_copy_method(good))
        self.assertFalse(is_native_track_album_copy_method(bad))
        self.assertFalse(is_native_track_album_copy_method(wrong_return))

    def test_exact_zero_const4_does_not_confuse_nonzero_or_other_register(self):
        from audit_native_selected_item_handoff import const4_zero_to_register
        self.assertTrue(const4_zero_to_register(0x12, [0x0012], 0))
        self.assertTrue(const4_zero_to_register(0x12, [0x0112], 1))
        self.assertFalse(const4_zero_to_register(0x12, [0xF012], 0))
        self.assertFalse(const4_zero_to_register(0x12, [0x0112], 0))
        self.assertFalse(const4_zero_to_register(0x13, [0x0013,0], 0))

    def test_descriptor_builder_is_exact(self):
        self.assertEqual(DESCRIPTOR_BUILDER,
            ("Lcom/yandex/music/shared/player/download2/o;", "while"))
        self.assertNotEqual(DESCRIPTOR_BUILDER,
            ("Lcom/yandex/music/shared/player/download2/o;", "if"))

    def test_only_public_player_owner_methods_are_player_selection_calls(self):
        self.assertIn("Landroidx/media3/common/Player;", PLAYER_OWNERS)
        self.assertIn("setMediaItem", PLAYER_METHODS)
        self.assertIn("getCurrentMediaItem", PLAYER_METHODS)
        self.assertNotIn("getTitle", PLAYER_METHODS)

    def test_media_session_and_decoder_boundaries_are_explicitly_classified(self):
        self.assertEqual(MEDIA_SESSION_OWNER,
            "Landroid/media/session/MediaSession;")
        self.assertIn("setMetadata", MEDIA_SESSION_METADATA_METHODS)
        self.assertIn("setPlaybackState", MEDIA_SESSION_STATE_METHODS)
        self.assertIn("queueInputBuffer",
            DECODER_BOUNDARY_METHODS["Landroid/media/MediaCodec;"])
        self.assertIn("readSampleData",
            DECODER_BOUNDARY_METHODS["Landroid/media/MediaExtractor;"])
        self.assertIn("write",
            DECODER_BOUNDARY_METHODS["Landroid/media/AudioTrack;"])

    def test_boundary_call_classifier_is_exact(self):
        self.assertEqual(classify_boundary_call((
            MEDIA_SESSION_OWNER, "setMetadata", "(Landroid/media/MediaMetadata;)V"
        )), "MEDIA_SESSION_METADATA")
        self.assertEqual(classify_boundary_call((
            "Landroid/media/MediaCodec;", "queueInputBuffer", "()V"
        )), "DECODER_BOUNDARY")
        self.assertIsNone(classify_boundary_call((
            MEDIA_SESSION_OWNER, "getController", "()V"
        )))

    def test_boundary_callsite_census_only_counts_prior_typed_field_reads(self):
        from unittest.mock import patch
        from audit_native_selected_item_handoff import MODEL
        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:2}[offset]
            def method(self, index):
                return (MEDIA_SESSION_OWNER, "setMetadata",
                        "(Landroid/media/MediaMetadata;)V")
        method=("LPlayerState;", "publish",
                "(Landroid/media/MediaMetadata;)V")
        field_read=(0,0x54,[0x2054,0])
        invoke=(1,0x6e,[0x006e,0])
        with patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LPlayerState;", "opaque", MODEL)), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   return_value=[2,1]):
            before=boundary_callsite_census(FakeDex(),method,0,100,[field_read,invoke])
            after=boundary_callsite_census(FakeDex(),method,0,100,[invoke,field_read])
        self.assertEqual(len(before),1)
        self.assertTrue(before[0]["track_field_read_on_this_before"])
        self.assertFalse(after[0]["track_field_read_on_this_before"])

    def test_boundary_census_detects_track_returning_helper_before_publish(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:1}[offset]
            def method(self, index):
                if index == 0:
                    return ("LPlayerState;", "current",
                            "()Lru/yandex/music/data/audio/o;")
                return (MEDIA_SESSION_OWNER, "setMetadata",
                        "(Landroid/media/MediaMetadata;)V")
        method=("LPlayerState;", "publish", "()V")
        helper=(0,0x6e,[0x006e,0])
        publish=(1,0x6e,[0x006e,1])
        with patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=[[3],[3,2]]):
            rows=boundary_callsite_census(FakeDex(),method,0,100,[helper,publish])
            reverse=boundary_callsite_census(FakeDex(),method,0,100,[publish,helper])
        self.assertTrue(rows[0]["track_returning_method_call_before"])
        self.assertFalse(reverse[0]["track_returning_method_call_before"])

    def test_byte_buffer_parameter_identity_reaches_audio_sink(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5,102:1}[offset]
            def method(self, index):
                return ("LbJ2;","native","(Ljava/nio/ByteBuffer;JI)Z")
        method=("LCaller;","write","(Ljava/nio/ByteBuffer;)V")
        # invoke-static {v4, v0, v1, v2}: ByteBuffer, long-wide, int.
        ins=[(0,0x71,[0x4071,0,0x2104])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            trace=trace_byte_buffer_parameter(FakeDex(),method,0x8,100)
        self.assertTrue(trace["same_byte_buffer_parameter_to_audio_sink_proven"])
        self.assertEqual(
            trace["events"][0]["buffer_argument_origins"],
            [{"argument_position":0,"origins":["CALLER_TYPED_PARAMETER"]}]
        )
        self.assertEqual(trace["events"][0]["invoke_kind"],"STATIC")

    def test_byte_buffer_instance_sink_accounts_for_receiver_and_wide_words(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:6,102:1}[offset]
            def method(self, index):
                return ("LbJ2;","native","(Ljava/nio/ByteBuffer;JI)Z")
        method=("LCaller;","write","(Ljava/nio/ByteBuffer;)V")
        # invoke-virtual {v0, v5, v1, v2, v3}: receiver, ByteBuffer, long-wide, int.
        ins=[(0,0x6e,[0x536e,0,0x2150])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            trace=trace_byte_buffer_parameter(FakeDex(),method,0x8,100)
        self.assertTrue(trace["same_byte_buffer_parameter_to_audio_sink_proven"])
        self.assertEqual(
            trace["events"][0]["buffer_argument_origins"],
            [{"argument_position":1,"origins":["CALLER_TYPED_PARAMETER"]}]
        )
        self.assertEqual(trace["events"][0]["invoke_kind"],"INSTANCE_OR_INTERFACE")

    def test_byte_buffer_alias_survives_backward_branch_only_when_register_is_stable(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5,102:1}[offset]
            def method(self, index):
                return ("LbJ2;","native","(Ljava/nio/ByteBuffer;JI)Z")
        method=("LCaller;","write","(Ljava/nio/ByteBuffer;)V")
        # if-eqz at pc 1 can loop to pc 0 or fall through to the sink at pc 3.
        ins=[
            (0,0x00,[0]),
            (1,0x38,[0x0038,0xffff]),
            (3,0x71,[0x4071,0,0x2104])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            trace=trace_byte_buffer_parameter(FakeDex(),method,0x8,100)
        self.assertTrue(trace["same_byte_buffer_parameter_to_audio_sink_proven"])
        self.assertTrue(trace["branch_seen"])
        self.assertFalse(trace["backward_branch_aliases_cleared"])
        self.assertFalse(trace["branch_seen_aliases_cleared"])
        self.assertEqual(trace["branch_preserved_parameter_registers"],[4])

    def test_forward_branch_preserves_unchanged_byte_buffer_parameter(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5,102:1}[offset]
            def method(self, index):
                return ("LbJ2;","native","(Ljava/nio/ByteBuffer;JI)Z")
        method=("LCaller;","write","(Ljava/nio/ByteBuffer;)V")
        # Both the conditional target and fall-through arrive at the sink.
        ins=[
            (0,0x38,[0x0038,0x0002]),
            (2,0x71,[0x4071,0,0x2104])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            trace=trace_byte_buffer_parameter(FakeDex(),method,0x8,100)
        self.assertTrue(trace["same_byte_buffer_parameter_to_audio_sink_proven"])
        self.assertTrue(trace["branch_seen"])
        self.assertFalse(trace["branch_seen_aliases_cleared"])

    def test_branch_drops_parameter_alias_if_its_register_is_written(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5,102:1}[offset]
            def method(self, index):
                return ("LbJ2;","native","(Ljava/nio/ByteBuffer;JI)Z")
        method=("LCaller;","write","(Ljava/nio/ByteBuffer;)V")
        # const/4 writes v4, the caller's ByteBuffer parameter register.
        ins=[
            (0,0x12,[0x0412]),
            (1,0x38,[0x0038,0x0002]),
            (3,0x71,[0x4071,0,0x2104])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            trace=trace_byte_buffer_parameter(FakeDex(),method,0x8,100)
        self.assertFalse(trace["same_byte_buffer_parameter_to_audio_sink_proven"])
        self.assertTrue(trace["branch_seen"])
        self.assertFalse(trace["branch_seen_aliases_cleared"])
        self.assertEqual(trace["parameter_registers_written"],[4])
        self.assertEqual(trace["stable_parameter_registers_across_branches"],[])

    def test_byte_buffer_returned_from_method_reaches_audio_sink(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5,102:0}[offset]
            def method(self, index):
                if index == 0:
                    return ("LCodec;","getOutputBuffer","()Ljava/nio/ByteBuffer;")
                return ("LbJ2;","native","(Ljava/nio/ByteBuffer;JI)Z")
        method=("LCaller;","write","()V")
        ins=[
            (0,0x71,[0x0071,0,0]),
            (3,0x0c,[0x010c]),
            (4,0x71,[0x4071,1,0x3201])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            trace=trace_byte_buffer_parameter(FakeDex(),method,0x8,100)
        self.assertTrue(trace["byte_buffer_object_to_audio_sink_proven"])
        self.assertEqual(
            trace["events"][0]["buffer_argument_origins"],
            [{"argument_position":0,"origins":["RETURNED_BYTEBUFFER_FROM_METHOD"]}]
        )

    def test_byte_buffer_field_read_reaches_audio_sink(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:6,102:1}[offset]
            def method(self, index):
                return ("LbJ2;","native","(Ljava/nio/ByteBuffer;JI)Z")
        method=("LCaller;","write","(Ljava/lang/Object;)V")
        ins=[
            (0,0x54,[0x1054,0]),
            (2,0x71,[0x4071,1,0x4320])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LHolder;","buffer","Ljava/nio/ByteBuffer;")):
            trace=trace_byte_buffer_parameter(FakeDex(),method,0x8,100)
        self.assertTrue(trace["byte_buffer_object_to_audio_sink_proven"])
        self.assertEqual(
            trace["events"][0]["buffer_argument_origins"],
            [{"argument_position":0,"origins":["BYTEBUFFER_FIELD_READ"]}]
        )

    def test_invoke_register_type_expansion_accounts_for_wide_values(self):
        from audit_native_selected_item_handoff import expand_invoke_register_types
        self.assertEqual(
            expand_invoke_register_types(
                "LReceiver;",["J",MODEL,"D",WRAPPER],False
            ),
            ["LReceiver;","J",None,MODEL,"D",None,WRAPPER]
        )
        self.assertEqual(
            expand_invoke_register_types("LStatic;",["J",MODEL],True),
            ["J",None,MODEL]
        )

    def test_audio_output_focus_includes_constructor_buffer_and_factory_methods(self):
        methods=[
            ("LbJ2;","<init>","(LbJ2$c;)V"),
            ("LbJ2;","native","(Ljava/nio/ByteBuffer;JI)Z"),
            ("LbJ2;","case","(Lpk0$a;LGi0;ILSr4;)Landroid/media/AudioTrack;"),
            ("LbJ2;","play","()V"),
        ]
        rows=select_audio_output_focus_methods(
            "LbJ2;",methods,{"Landroid/media/AudioTrack;","Ljava/nio/ByteBuffer;"}
        )
        self.assertEqual(
            [(method[1],reason) for method,reason in rows],
            [
                ("<init>","AUDIO_OUTPUT_CONSTRUCTOR"),
                ("case","AUDIO_TRACK_FACTORY_OR_ADAPTER"),
                ("native","AUDIO_BUFFER_ENTRY"),
            ]
        )
        self.assertEqual(
            select_audio_output_focus_methods(
                "Lru/yandex/speechkit/internal/SoundPlayerHelper;",
                methods,{"Landroid/media/AudioTrack;"}
            ),
            []
        )

    def test_exact_interface_contract_requires_owner_and_full_signature(self):
        owner_methods=[
            ("LbJ2;","write","(J)V"),
            ("LbJ2;","flush","()V"),
        ]
        interface_refs={
            ("Laudio/Output;","write","(J)V"),
            ("Laudio/Output;","flush","()V"),
            ("Laudio/Output;","write","(I)V"),
        }
        matches=select_exact_interface_contracts(
            "LbJ2;",owner_methods,{"Laudio/Output;"},interface_refs
        )
        self.assertEqual(matches,[
            ("Laudio/Output;","flush","()V"),
            ("Laudio/Output;","write","(J)V"),
        ])

    def test_audio_output_dispatch_contracts_follow_exact_interface_and_superclass_shapes(self):
        focus=("LImpl;","write","(Ljava/nio/ByteBuffer;JI)Z")
        profiles={
            "LImpl;":{
                "static_types":set(),"instance_types":{"Ljava/nio/ByteBuffer;"},
                "interfaces":{"LApi;"},"superclass":"LBase;"
            },
            "LApi;":{
                "static_types":set(),"instance_types":set(),
                "interfaces":{"LParentApi;"},"superclass":"Ljava/lang/Object;"
            },
            "LParentApi;":{
                "static_types":set(),"instance_types":set(),
                "interfaces":set(),"superclass":"Ljava/lang/Object;"
            },
            "LBase;":{
                "static_types":set(),"instance_types":set(),
                "interfaces":set(),"superclass":"Ljava/lang/Object;"
            }
        }
        contracts, owners=audio_output_dispatch_contracts([focus],profiles)
        self.assertIn(focus,contracts)
        self.assertIn(("LApi;","write",focus[2]),contracts)
        self.assertIn(("LParentApi;","write",focus[2]),contracts)
        self.assertIn(("LBase;","write",focus[2]),contracts)
        self.assertEqual(
            contracts[("LApi;","write",focus[2])]["contract_kinds"],
            {"INTERFACE_METHOD_CONTRACT"}
        )
        self.assertEqual(
            contracts[("LBase;","write",focus[2])]["contract_kinds"],
            {"SUPERCLASS_VIRTUAL_CANDIDATE"}
        )
        self.assertNotIn(("LApi;","write","(Ljava/nio/ByteBuffer;)Z"),contracts)
        self.assertEqual(owners[0]["owner"],"LImpl;")
        self.assertFalse(owners[0]["has_track_field"])

    def test_audio_output_dispatch_contracts_fail_closed_on_large_hierarchy(self):
        profiles={"LImpl;":{
            "static_types":set(),"instance_types":set(),
            "interfaces":{f"LApi{i};" for i in range(130)},
            "superclass":None
        }}
        with self.assertRaises(ValueError):
            audio_output_dispatch_contracts(
                [("LImpl;","write","()V")],profiles
            )

    def test_method_signature_type_profile_is_type_only(self):
        from audit_native_selected_item_handoff import method_signature_type_profile
        profile=method_signature_type_profile((
            "LCaller;","submit",
            "(Landroidx/media3/common/MediaItem;Landroid/media/MediaMetadata;Landroid/net/Uri;)V"
        ))
        self.assertTrue(profile["accepts_media_item"])
        self.assertTrue(profile["accepts_media_metadata"])
        self.assertTrue(profile["accepts_uri"])
        self.assertFalse(profile["accepts_track"])
        self.assertFalse(profile["accepts_data_source"])

    def test_owner_profile_detects_media_item_and_decoder_types_without_values(self):
        from audit_native_selected_item_handoff import classify_track_owner_profile
        profile=classify_track_owner_profile({
            "static_types":set(),
            "instance_types":{
                "Landroidx/media3/common/MediaItem;",
                "Landroid/media/AudioTrack;",
                "Landroid/media/MediaCodec;",
                "Landroid/media/MediaMetadata;",
                "Landroid/media/session/PlaybackState;",
            },
            "interfaces":set(),"superclass":None
        })
        self.assertTrue(profile["has_media_item_field"])
        self.assertTrue(profile["has_audio_track_field"])
        self.assertTrue(profile["has_media_codec_field"])
        self.assertTrue(profile["has_media_metadata_field"])
        self.assertTrue(profile["has_playback_state_field"])
        self.assertTrue(profile["has_decoder_field"])

    def test_boundary_callsite_owner_profiles_group_exact_callers(self):
        from audit_native_selected_item_handoff import summarize_boundary_callsite_owner_profiles
        rows=[{
            "kind":"DECODER_BOUNDARY",
            "caller_key":("LPlayerCore;","write","()V"),
            "target_key":("Landroid/media/AudioTrack;","write","()V"),
            "ordinal":0
        },{
            "kind":"DECODER_BOUNDARY",
            "caller_key":("LPlayerCore;","flush","()V"),
            "target_key":("Landroid/media/AudioTrack;","pause","()V"),
            "ordinal":1
        }]
        profiles={
            "LPlayerCore;":{
                "static_types":set(),
                "instance_types":{"Landroid/media/AudioTrack;","Landroidx/media3/common/MediaItem;"},
                "interfaces":set(),"superclass":None
            }
        }
        result=summarize_boundary_callsite_owner_profiles(rows,profiles)
        entry=result["DECODER_BOUNDARY"][0]
        self.assertEqual(entry["call_site_count"],2)
        self.assertEqual(entry["distinct_caller_method_count"],2)
        self.assertTrue(entry["has_audio_track_field"])
        self.assertTrue(entry["has_media_item_field"])

    def test_track_field_owner_inventory_separates_player_and_queue_shape(self):
        profiles={
            "LPlayerState;": {
                "static_types": set(),
                "instance_types": {
                    MODEL, "Lru/yandex/music/data/audio/Album;", "LtCa;",
                    "Ljava/util/List;", "J", "Landroidx/media3/common/Player;"
                },
                "interfaces": set(), "superclass": None
            },
            "LDownloadState;": {
                "static_types": set(),
                "instance_types": {MODEL, "Ljava/util/List;"},
                "interfaces": set(), "superclass": None
            }
        }
        result=summarize_track_field_owner_inventory(profiles)
        self.assertEqual(result["track_instance_field_owner_count"],2)
        self.assertEqual(result["track_and_album_same_owner_count"],1)
        self.assertEqual(result["track_and_wrapper_same_owner_count"],1)
        self.assertEqual(result["track_owner_with_player_api_field_count"],1)
        self.assertEqual(result["track_owner_with_collection_field_count"],2)
        self.assertEqual(result["track_owner_with_numeric_field_count"],1)

    def test_boundary_census_joins_caller_owner_track_state_without_reading_values(self):
        profiles={
            "LPlayerState;": {
                "static_types": set(), "instance_types": {MODEL},
                "interfaces": set(), "superclass": None
            }
        }
        row={
            "kind":"MEDIA_SESSION_METADATA",
            "caller_key":("LPlayerState;","publish","()V"),
            "track_parameter_present":False,"album_parameter_present":False,
            "track_field_read_on_this_before":False,"album_field_read_on_this_before":False,
            "numeric_field_read_on_this_before":False,"track_model_method_call_before":False,
            "album_model_method_call_before":False,"track_returning_method_call_before":False,
            "album_returning_method_call_before":False,"track_field_reads_before":0,
            "album_field_reads_before":0
        }
        result=summarize_boundary_callsite_census([row],profiles)
        self.assertEqual(result["MEDIA_SESSION_METADATA"]["caller_owner_has_track_field_call_site_count"],1)

    def test_candidate_owner_descriptors_only_select_shared_track_shapes(self):
        from audit_native_selected_item_handoff import ALBUM_MODEL, WRAPPER
        profiles={
            "LTrackAlbumOwner;": {
                "static_types": set(),
                "instance_types": {MODEL, ALBUM_MODEL},
                "interfaces": set(), "superclass": None
            },
            "LTrackWrapperOwner;": {
                "static_types": set(),
                "instance_types": {MODEL, WRAPPER},
                "interfaces": set(), "superclass": None
            },
            "LTrackOnlyOwner;": {
                "static_types": set(),
                "instance_types": {MODEL, "Ljava/util/List;"},
                "interfaces": set(), "superclass": None
            }
        }
        rows=candidate_owner_descriptors(profiles)
        self.assertEqual([row["owner"] for row in rows],
                         ["LTrackAlbumOwner;", "LTrackWrapperOwner;"])

    def test_typed_parameter_registers_preserve_exact_reference_registers(self):
        from audit_native_selected_item_handoff import (
            ALBUM_MODEL, WRAPPER, typed_parameter_registers
        )
        class FakeDex:
            def u16(self, offset):
                return {100:7,102:5}[offset]
        method=("LCaller;","handoff",f"({MODEL}{ALBUM_MODEL}J{WRAPPER})V")
        self.assertEqual(typed_parameter_registers(FakeDex(),method,0x8,100,MODEL),{2})
        self.assertEqual(typed_parameter_registers(FakeDex(),method,0x8,100,ALBUM_MODEL),{3})
        self.assertEqual(typed_parameter_registers(FakeDex(),method,0x8,100,WRAPPER),{6})

    def test_identity_method_trace_preserves_track_field_alias_to_call(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:1}[offset]
            def method(self, index):
                return ("LTarget;", "consume", f"({MODEL})V")
        method=("LCaller;", "run", "()V")
        ins=[(0,0x54,[0x3154,0]),(1,0x6e,[0x006e,0])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LCaller;","hidden",MODEL)), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   return_value=[0,1]):
            trace=trace_identity_method(FakeDex(),method,0,100,{"LTarget;"})
        calls=[row for row in trace["events"] if row["kind"]=="CALL_WITH_TYPED_IDENTITY"]
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0]["identity_arguments"][0]["identity_type"],"TRACK")
        self.assertIn("FIELD_READ_FROM_THIS",calls[0]["identity_arguments"][0]["origins"])

    def test_identity_method_trace_tracks_returned_track_to_call(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:1}[offset]
            def method(self, index):
                if index==0:
                    return ("LFactory;","get","()"+MODEL)
                return ("LTarget;","consume",f"({MODEL})V")
        method=("LCaller;","run","()V")
        ins=[
            (0,0x71,[0x0071,0]),
            (1,0x0c,[0x010c]),
            (2,0x6e,[0x006e,1])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=[[],[0,1]]):
            trace=trace_identity_method(FakeDex(),method,0,100)
        calls=[row for row in trace["events"] if row["kind"]=="CALL_WITH_TYPED_IDENTITY"]
        self.assertEqual(len(calls),1)
        self.assertIn("RETURNED_FROM_METHOD",calls[0]["identity_arguments"][0]["origins"])

    def test_identity_method_trace_proves_same_field_object_returned(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:1}[offset]
        method=("LHolder;", "current", "()"+MODEL)
        ins=[
            (0,0x54,[0x3154,0]),
            (1,0x11,[0x0111])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LHolder;","hidden",MODEL)):
            trace=trace_identity_method(FakeDex(),method,0,100)
        returned=[row for row in trace["events"] if row["kind"]=="RETURN_TYPED_IDENTITY"]
        self.assertEqual(len(returned),1)
        self.assertEqual(returned[0]["identity_type"],"TRACK")
        self.assertIn("FIELD_READ_FROM_THIS",returned[0]["origins"])

    def test_identity_method_trace_classifies_source_call_without_identity(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:2, 102:1}[offset]
            def method(self, index):
                return ("LGp0;", "new", "()Ljava/lang/Object;")
        method=("LCaller;", "run", "()V")
        ins=[
            (0,0x28,[0x0028]),
            (1,0x71,[0x0071,0])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[]):
            trace=trace_identity_method(FakeDex(),method,0,100)
        rows=[row for row in trace["events"]
              if row["kind"]=="CALL_TARGET_ROLE_WITHOUT_IDENTITY"]
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["role"],"NATIVE_SOURCE_OR_DOWNLOAD_METHOD")
        self.assertFalse(rows[0]["identity_proven"])

    def test_identity_method_trace_can_census_call_target_after_alias_reset(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:3, 102:1}[offset]
            def method(self, index):
                return ("LBuilder;", "build", f"({MODEL})V")
        method=("LCaller;", "run", f"({MODEL})V")
        ins=[
            (0,0x28,[0x0028]),
            (1,0x6e,[0x006e,0])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[0,2]):
            trace=trace_identity_method(
                FakeDex(),method,0x8,100,capture_unproven_calls=True
            )
        calls=[row for row in trace["events"]
               if row["kind"]=="CALL_TARGET_WITHOUT_IDENTITY"]
        self.assertEqual(len(calls),1)
        self.assertTrue(calls[0]["target_accepts_track_parameter"])
        self.assertFalse(calls[0]["identity_proven"])

    def test_reader_field_identity_matches_only_actual_sink_buffer_argument(self):
        from unittest.mock import patch
        class FakeDex:
            def method(self, index):
                return ("LRenderer;", "output", "(Ljava/nio/ByteBuffer;)Z")
        method=("LRenderer;", "consume", "()Z")
        target=("LRenderer;", "output", "(Ljava/nio/ByteBuffer;)Z")
        ins=[
            (0,0x54,[0x2154,3]), # field 3 -> v1 from this v2
            (1,0x54,[0x2254,4]), # unrelated field 4 -> v2
            (2,0x6e,[0x006e,0])
        ]
        fields={
            3:("LOwner;","privateOne","Ljava/nio/ByteBuffer;"),
            4:("LOwner;","privateTwo","Ljava/nio/ByteBuffer;")
        }
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",side_effect=lambda d,i: fields[i]), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[0,1]):
            result=collect_sink_buffer_field_refs(FakeDex(),method,0,100,{target})
        self.assertEqual(result,{fields[3]})

    def test_writer_buffer_return_provenance_is_basic_block_only(self):
        from unittest.mock import patch
        class FakeDex:
            def method(self, index):
                return ("LDecoder;", "take", "(I)Ljava/nio/ByteBuffer;")
        method=("LRenderer;", "read", "()V")
        target=("LRenderer;","privateBuffer","Ljava/nio/ByteBuffer;")
        ins=[
            (0,0x6e,[0x006e,0]),
            (1,0x0c,[0x000c]),
            (2,0x5b,[0x105b,7]),
            (3,0x28,[0x0028]),
            (4,0x5b,[0x105b,7])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target):
            events,branch=trace_renderer_buffer_field_writes(
                FakeDex(),method,0,100,{target}
            )
        self.assertEqual(len(events),2)
        self.assertEqual(events[0]["same_basic_block_buffer_return_source"]["owner"],"LDecoder;")
        self.assertIsNone(events[1]["same_basic_block_buffer_return_source"])
        self.assertTrue(branch)

    def test_track_parameter_register_survives_branch_until_actual_write(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5,102:2}[offset]
            def descriptor(self,index):
                return "Lru/yandex/music/data/audio/o;"
            def method(self,index):
                return ("LTarget;","get","()Ljava/lang/Object;")
        method=("LGp0;","new","(Lru/yandex/music/data/audio/o;LOe2;)V")
        ins=[
            (0,0x28,[0x0028]),
            (1,0x5b,[0x135b,7]),
            (2,0x12,[0x0012])
        ]
        target=("LFp0;","hiddenTrack","Lru/yandex/music/data/audio/o;")
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target):
            result=trace_track_value_to_exact_field_store(
                FakeDex(),method,0x8,100,target
            )
        site=result["field_store_sites"][0]
        self.assertTrue(result["branch_seen"])
        self.assertTrue(site["source_is_original_track_parameter"])
        self.assertEqual(site["track_source_provenance"],"SAME_TRACK_PARAMETER_REFERENCE")
        self.assertFalse(result["control_flow_feasibility_proven"])
        self.assertNotIn("hiddenTrack",str(result))

    def test_track_return_value_is_not_mistaken_for_same_parameter_identity(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5,102:2}[offset]
            def descriptor(self,index):
                return "Lru/yandex/music/data/audio/o;"
            def method(self,index):
                return ("LTarget;","get","()Lru/yandex/music/data/audio/o;")
        method=("LGp0;","new","(LOe2;)V")
        ins=[
            (0,0x71,[0x0071,9]),
            (1,0x0c,[0x020c]),
            (2,0x5b,[0x125b,7])
        ]
        target=("LFp0;","hiddenTrack","Lru/yandex/music/data/audio/o;")
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target):
            result=trace_track_value_to_exact_field_store(
                FakeDex(),method,0x8,100,target
            )
        site=result["field_store_sites"][0]
        self.assertFalse(site["source_is_original_track_parameter"])
        self.assertTrue(site["source_is_unlinked_track_return_candidate"])
        self.assertEqual(site["track_source_provenance"],"UNLINKED_TRACK_RETURN_CANDIDATE")
        self.assertNotIn("hiddenTrack",str(result))

    def test_exact_continuation_field_writer_tracks_object_cast_and_same_field(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:6,102:3}[offset]
            def descriptor(self,index):
                return "Lru/yandex/music/data/audio/o;"
            def method(self,index):
                return ("LTarget;","get","()Ljava/lang/Object;")
        method=("LFp0;","create","(Ljava/lang/Object;LOe2;)V")
        ins=[
            (0,0x1f,[0x041f,1]),
            (1,0x5b,[0x345b,7]),
            (2,0x0e,[0x000e])
        ]
        target=("LFp0;","privateTrack","Lru/yandex/music/data/audio/o;")
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target):
            result=trace_track_value_to_exact_field_store(
                FakeDex(),method,0,100,target
            )
        self.assertTrue(result["field_store_sites"][0]["source_is_track_parameter_or_field"])
        self.assertEqual(result["field_store_sites"][0]["track_source_provenance"],
                         "CAST_OBJECT_PARAMETER_REFERENCE")
        self.assertNotIn("privateTrack",str(result))

    def test_exact_continuation_field_writer_does_not_accept_unchecked_object(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:6,102:3}[offset]
            def descriptor(self,index):
                return "Ljava/lang/Object;"
            def method(self,index):
                return ("LTarget;","get","()Ljava/lang/Object;")
        method=("LFp0;","create","(Ljava/lang/Object;LOe2;)V")
        ins=[(0,0x5b,[0x345b,7]),(1,0x0e,[0x000e])]
        target=("LFp0;","privateTrack","Lru/yandex/music/data/audio/o;")
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target):
            result=trace_track_value_to_exact_field_store(
                FakeDex(),method,0,100,target
            )
        self.assertFalse(result["field_store_sites"][0]["source_is_track_parameter_or_field"])
        self.assertTrue(result["field_store_sites"][0]["source_is_object_parameter_not_yet_cast"])
        self.assertNotIn("privateTrack",str(result))

    def test_native_track_coroutine_capture_roundtrip_and_wrapper_identity(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:8,102:3,200:4,202:1}[offset]
            def descriptor(self, index):
                return {1:"LFp0;",5:"LtCa;"}[index]
            def method(self, index):
                return {
                    2:("LFp0;","<init>","(LGp0;LOe2;)V"),
                    6:("LtCa;","<init>","(Ljava/lang/String;)V"),
                    7:("Lou3;","new","(LtCa;LFp0;)Ljava/lang/Object;"),
                    8:("LGp0;","new",
                       "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
                }[index]
        initial=("LGp0;","new",
                 "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        resume=("LFp0;","invokeSuspend","(Ljava/lang/Object;)Ljava/lang/Object;")
        initial_ins=[
            (0,0x22,[0x0022,1]),
            (2,0x70,[0x0070,2,0]),
            (5,0x5b,[0x0600,3]),
            (7,0x54,[0x0154,3]),
            (9,0x54,[0x1254,4]),
            (11,0x22,[0x0322,5]),
            (13,0x70,[0x0070,6,0]),
            (16,0x71,[0x0071,7,0])
        ]
        resume_ins=[(0,0x71,[0x0071,8,0])]
        fields={
            3:("LFp0;","hiddenTrack","Lru/yandex/music/data/audio/o;"),
            4:("Lru/yandex/music/data/audio/o;","hiddenString","Ljava/lang/String;")
        }
        with patch("audit_native_selected_item_handoff.instructions",
                   side_effect=lambda d,c: initial_ins if c==100 else resume_ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   side_effect=lambda d,i: fields[i]), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=lambda op,w:{2:[0,5,7],6:[3,2],7:[3,0],8:[2,0,3]}[w[1]]):
            result=trace_native_track_coroutine_continuation(
                FakeDex(),initial,0x8,100,resume,0,200
            )
        self.assertEqual(result["track_parameter_capture_store_candidates"][0]["field_slot"],3)
        self.assertTrue(result["track_parameter_capture_store_candidates"][0]["same_original_track_parameter"])
        self.assertTrue(result["same_field_slot_store_to_resume_read_candidates"])
        self.assertTrue(result["resume_continuation_call_sites"][0]["invokeSuspend_this_passed_as_continuation"])
        self.assertTrue(result["continuation_field_track_to_opaque_wrapper_candidate"])
        self.assertTrue(result["control_flow_graph_built"])
        self.assertTrue(result["wrapper_continuation_handoff_sites"][0]["wrapper_instance_passed"])
        self.assertFalse(result["coroutine_runtime_resume_dispatch_proven"])
        self.assertNotIn("hiddenTrack",str(result))
        self.assertNotIn("hiddenString",str(result))

    def test_coroutine_cfg_merge_drops_track_alias_when_one_branch_overwrites(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:8,102:3,200:4,202:1}[offset]
            def descriptor(self,index):
                return {1:"LFp0;"}
            def method(self,index):
                return {
                    2:("LFp0;","<init>","(LGp0;LOe2;)V"),
                    8:("LGp0;","new","(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
                }[index]
        initial=("LGp0;","new","(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        resume=("LFp0;","invokeSuspend","(Ljava/lang/Object;)Ljava/lang/Object;")
        initial_ins=[
            (0,0x22,[0x0022,1]),
            (2,0x70,[0x0070,2,0]),
            (5,0x38,[0x0038,8]),
            (7,0x1a,[0x061a,0]),
            (9,0x28,[0x0428]),
            (10,0x00,[0x0000]),
            (11,0x00,[0x0000]),
            (12,0x00,[0x0000]),
            (13,0x5b,[0x0600,3]),
            (15,0x0e,[0x000e])
        ]
        resume_ins=[(0,0x71,[0x0071,8,0])]
        target=("LFp0;","privateTrack","Lru/yandex/music/data/audio/o;")
        with patch("audit_native_selected_item_handoff.instructions",
                   side_effect=lambda d,c: initial_ins if c==100 else resume_ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=lambda op,w:{2:[0,5,7],8:[2,0,3]}[w[1]]):
            cfg=build_dex_control_flow(FakeDex(),100)
            result=trace_native_track_coroutine_continuation(
                FakeDex(),initial,0x8,100,resume,0,200
            )
        self.assertEqual(cfg["successors"][5],[7,13])
        self.assertEqual(cfg["successors"][9],[13])
        self.assertIn(13,cfg["reachable"])
        self.assertTrue(result["control_flow_graph_built"])
        self.assertEqual(len(result["branch_sites"]),2)
        self.assertTrue(result["raw_track_field_store_sites"], repr({
            "track_registers":result["track_parameter_registers"],
            "branches":result["branch_sites"],
            "raw_stores":result["raw_track_field_store_sites"],
            "reachable":result["reachable_instruction_count"]
        }))
        self.assertTrue(any(
            "NEW_LFp0_CONTINUATION" in row["receiver_origins"]
            for row in result["raw_track_field_store_sites"]
        ), repr(result["raw_track_field_store_sites"]))
        self.assertFalse(result["original_track_parameter_to_continuation_field_candidate"])
        self.assertNotIn("privateTrack",str(result))

    def test_native_track_coroutine_does_not_match_different_continuation_field(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:8,102:3,200:4,202:1}[offset]
            def descriptor(self,index):
                return {1:"LFp0;"}
            def method(self,index):
                return {
                    2:("LFp0;","<init>","(LGp0;LOe2;)V"),
                    8:("LGp0;","new","(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
                }[index]
        initial=("LGp0;","new","(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        resume=("LFp0;","invokeSuspend","(Ljava/lang/Object;)Ljava/lang/Object;")
        initial_ins=[
            (0,0x22,[0x0022,1]),(2,0x70,[0x0070,2,0]),
            (5,0x5b,[0x0600,3]),(7,0x54,[0x0154,9])
        ]
        resume_ins=[(0,0x71,[0x0071,8,0])]
        fields={
            3:("LFp0;","hiddenTrack","Lru/yandex/music/data/audio/o;"),
            9:("LFp0;","otherTrack","Lru/yandex/music/data/audio/o;")
        }
        with patch("audit_native_selected_item_handoff.instructions",
                   side_effect=lambda d,c: initial_ins if c==100 else resume_ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   side_effect=lambda d,i: fields[i]), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=lambda op,w:{2:[0,5,7],8:[2,0,3]}[w[1]]):
            result=trace_native_track_coroutine_continuation(
                FakeDex(),initial,0x8,100,resume,0,200
            )
        self.assertFalse(result["same_field_slot_store_to_resume_read_candidates"])
        self.assertFalse(result["original_track_parameter_to_continuation_field_candidate"])

    def test_renderer_field_census_marks_same_field_only_as_candidate(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5, 102:1}[offset]
            def method(self, index):
                if index == 0:
                    return ("LDecoder;","take","(I)Ljava/nio/ByteBuffer;")
                return ("LBase;","O","(Ljava/nio/ByteBuffer;)Z")
        target=("LBase;","O","(Ljava/nio/ByteBuffer;)Z")
        method=("LRenderer;","render","()Z")
        ins=[
            (0,0x6e,[0x006e,0]),
            (1,0x0c,[0x000c]),
            (2,0x5b,[0x405b,7]),
            (3,0x54,[0x4154,7]),
            (4,0x6e,[0x006e,1])
        ]
        with patch("audit_native_selected_item_handoff.instructions", return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LRenderer;","secretBuffer","Ljava/nio/ByteBuffer;")), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=[[2,1],[4,1]]):
            result=trace_renderer_buffer_field_candidates(
                FakeDex(),method,0,100,{target}
            )
        stores=result["codec_return_to_this_buffer_field_store_candidates"]
        self.assertEqual(len(stores),1)
        refs=result["audio_output_call_candidates"][0]["buffer_reference_candidates"]
        self.assertEqual(refs[0]["prior_codec_return_store_count"],1)
        self.assertFalse(refs[0]["same_runtime_buffer_proven"])
        self.assertFalse(result["same_codec_buffer_to_sink_proven"])
        self.assertNotIn("secretBuffer",str(result))

    def test_renderer_field_census_does_not_match_different_receiver_or_field(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5,102:1}[offset]
            def method(self, index):
                if index == 0:
                    return ("LDecoder;","take","(I)Ljava/nio/ByteBuffer;")
                return ("LBase;","O","(Ljava/nio/ByteBuffer;)Z")
        target=("LBase;","O","(Ljava/nio/ByteBuffer;)Z")
        method=("LRenderer;","render","()Z")
        ins=[
            (0,0x6e,[0x006e,0]),
            (1,0x0c,[0x000c]),
            (2,0x5b,[0x405b,7]),
            (3,0x54,[0x4154,8]),
            (4,0x6e,[0x006e,1])
        ]
        with patch("audit_native_selected_item_handoff.instructions", return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LRenderer;","secretBuffer","Ljava/nio/ByteBuffer;")), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=[[2,1],[4,1]]):
            result=trace_renderer_buffer_field_candidates(
                FakeDex(),method,0,100,{target}
            )
        refs=result["audio_output_call_candidates"][0]["buffer_reference_candidates"]
        self.assertEqual(refs[0]["prior_codec_return_store_count"],0)
        self.assertFalse(result["same_codec_buffer_to_sink_proven"])

    def test_owner_ancestry_profiles_include_parent_track_identity_types(self):
        profiles={
            "LRenderer;":{
                "static_types":set(),"instance_types":{"Landroid/media/MediaCodec;"},
                "interfaces":{"LRendererApi;"},"superclass":"LBaseRenderer;"
            },
            "LBaseRenderer;":{
                "static_types":set(),"instance_types":{MODEL, "Landroidx/media3/common/MediaItem;"},
                "interfaces":set(),"superclass":"Ljava/lang/Object;"
            },
            "LRendererApi;":{
                "static_types":set(),"instance_types":set(),
                "interfaces":set(),"superclass":"Ljava/lang/Object;"
            }
        }
        rows=owner_ancestry_profiles("LRenderer;",profiles)
        self.assertEqual({row["owner"] for row in rows},
                         {"LRenderer;","LBaseRenderer;","LRendererApi;"})
        parent=next(row for row in rows if row["owner"]=="LBaseRenderer;")
        self.assertTrue(parent["has_track_field"])
        self.assertTrue(parent["has_media_item_field"])

    def test_byte_buffer_return_from_decoder_can_reach_exact_audio_output_contract(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:3,102:1}[offset]
            def method(self, index):
                if index==0:
                    return ("Landroid/media/MediaCodec;","getOutputBuffer",
                            "(I)Ljava/nio/ByteBuffer;")
                return ("LAudioSink;","write",
                        "(Ljava/nio/ByteBuffer;)Z")
        method=("LRenderer;","render","()Z")
        target=("LAudioSink;","write","(Ljava/nio/ByteBuffer;)Z")
        ins=[
            (0,0x6e,[0x006e,0]),
            (1,0x0c,[0x000c]),
            (2,0x72,[0x0072,1])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=[[2,1],[2,0]]):
            trace=trace_byte_buffer_parameter(
                FakeDex(),method,0,100,sink_targets={target}
            )
        sink=next(row for row in trace["events"]
                  if row["kind"]=="AUDIO_BUFFER_SINK_CALL")
        self.assertTrue(sink["byte_buffer_object_proven"])
        self.assertEqual(
            sink["buffer_argument_origins"][0]["origins"],
            ["RETURNED_BYTEBUFFER_FROM_METHOD"]
        )
        self.assertEqual(
            trace["buffer_provenance_events"][0]["source_method"]["owner"],
            "Landroid/media/MediaCodec;"
        )

    def test_identity_method_trace_marks_exact_audio_output_dispatch_with_track_identity(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:3,102:1}[offset]
            def method(self, index):
                return ("LApi;","write",f"({MODEL})V")
        method=("LCaller;","render",f"({MODEL})V")
        target=("LApi;","write",f"({MODEL})V")
        ins=[(0,0x72,[0x0072,0])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[0,2]):
            trace=trace_identity_method(
                FakeDex(),method,0x8,100,focus_targets={target}
            )
        calls=[row for row in trace["events"]
               if row["kind"]=="CALL_WITH_TYPED_IDENTITY"]
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0]["role"],"AUDIO_OUTPUT_METHOD_DISPATCH")
        self.assertEqual(calls[0]["identity_arguments"][0]["identity_type"],"TRACK")
        self.assertEqual(calls[0]["identity_arguments"][0]["argument_position"],1)

    def test_identity_method_trace_clears_aliases_at_branch(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:1}[offset]
            def method(self, index):
                return ("LTarget;", "consume", f"({MODEL})V")
        method=("LCaller;", "run", "()V")
        ins=[
            (0,0x54,[0x3154,0]),
            (1,0x28,[0x0028]),
            (2,0x6e,[0x006e,0])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LCaller;","hidden",MODEL)), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   return_value=[0,1]):
            trace=trace_identity_method(FakeDex(),method,0,100)
        self.assertTrue(trace["branch_seen_aliases_cleared"])
        self.assertFalse(any(row["kind"]=="CALL_WITH_TYPED_IDENTITY"
                             for row in trace["events"]))

    def test_next_identity_hop_skips_already_traced_and_external_owners(self):
        from audit_native_selected_item_handoff import select_next_identity_method_refs
        traces=[{
            "events":[
                {
                    "kind":"CALL_WITH_TYPED_IDENTITY",
                    "callee":{"owner":"LNext;","method":"accept","signature":f"({MODEL})V"},
                    "identity_arguments":[{"identity_type":"TRACK"}]
                },
                {
                    "kind":"CALL_WITH_TYPED_IDENTITY",
                    "callee":{"owner":"Lkotlin/jvm/internal/Intrinsics;","method":"check","signature":"()V"},
                    "identity_arguments":[{"identity_type":"TRACK"}]
                }
            ]
        }]
        profiles={
            "LNext;":{"static_types":set(),"instance_types":set(),
                      "interfaces":set(),"superclass":None},
            "Lkotlin/jvm/internal/Intrinsics;":{"static_types":set(),
                "instance_types":set(),"interfaces":set(),"superclass":None}
        }
        refs=select_next_identity_method_refs(traces,{("LCurrent;","run","()V")},profiles)
        self.assertEqual(refs,[("LNext;","accept",f"({MODEL})V")])

    def test_edition_generation_markers_are_exact_and_bounded(self):
        self.assertIn("edition", EDITION_MARKERS)
        self.assertIn("playbackgeneration", GENERATION_MARKERS)
        self.assertNotIn("url", EDITION_MARKERS | GENERATION_MARKERS)
        self.assertNotIn("token", EDITION_MARKERS | GENERATION_MARKERS)

    def test_common_destination_registers_are_invalidated(self):
        self.assertEqual(written_register(0x0c, [0x030c]), 3)
        self.assertEqual(written_register(0x22, [0x0500, 0x0010]), 5)
        self.assertEqual(written_register(0x54, [0x0214, 0x0003]), 2)
        self.assertIsNone(written_register(0x1f, [0x021f, 0x0003]))

    def test_malformed_signatures_fail_closed(self):
        for signature in ("V", "(Ljava/lang/String)V", "(Q)V", "([)V"):
            with self.subTest(signature=signature):
                with self.assertRaises(ValueError):
                    parse_types(signature)

if __name__ == "__main__":
    unittest.main()
