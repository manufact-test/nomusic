import unittest
from audit_native_selected_item_handoff import (
    parse_types, written_register, MODEL, WRAPPER, DESCRIPTOR_BUILDER,
    PLAYER_OWNERS, PLAYER_METHODS, MEDIA_SESSION_OWNER,
    MEDIA_SESSION_METADATA_METHODS, MEDIA_SESSION_STATE_METHODS,
    DECODER_BOUNDARY_METHODS, EDITION_MARKERS, GENERATION_MARKERS,
    classify_boundary_call, boundary_callsite_census,
    summarize_track_field_owner_inventory, summarize_boundary_callsite_census,
    candidate_owner_descriptors, typed_parameter_registers,
    trace_identity_method, inspect_exact_playlist_update_callers,
    inspect_exact_li_lb_handoff_callers, LI_LB_CONSTRUCTOR_TARGET,
    LI_LB_GETTER_TARGET,
    inspect_exact_playlist_update_method_handle_sites,
    inspect_exact_playlist_callback_contract,
    inspect_exact_playlist_runner_construction,
    select_next_identity_method_refs,
    build_dex_control_flow,
    summarize_boundary_callsite_owner_profiles, method_signature_type_profile,
    select_exact_interface_contracts, select_audio_output_focus_methods,
    trace_byte_buffer_parameter, expand_invoke_register_types,
    audio_output_dispatch_contracts, owner_ancestry_profiles,
    trace_renderer_buffer_field_candidates, collect_sink_buffer_field_refs,
    trace_renderer_buffer_field_identity_cfg,
    trace_renderer_buffer_field_writes, trace_native_track_coroutine_continuation,
    trace_track_value_to_exact_field_store,
    classify_native_track_coroutine_callsite,
    inspect_native_track_coroutine_callers,
    trace_coroutine_callsite_argument_origins,
    summarize_coroutine_new_instance_ancestry,
    classify_coroutine_entry_direct_upstream_call,
    class_instantiation_and_flow_collect_sites,
    summarize_flow_entry_class_profiles,
    logical_invoke_argument_rows,
    local_primitive_register_origin,
    constructor_int_parameter_field_store_census,
    summarize_flow_interface_implementers,
    privacy_safe_flow_class_profile, privacy_safe_focused_method_trace,
    summarize_current_track_flow_candidate,
    summarize_flow_mode_branch_census,
    exact_track_return_owner_scope,
    exact_parameter_field_store_refs, local_object_register_origin,
    dex_type_assignable_to, trace_exact_object_receiver_call_cfg,
    trace_exact_object_method_body, trace_track_identity_method_cfg,
    inspect_exact_track_wrapper_handoff, inspect_exact_lqj8_service_route
)

class SelectedItemAuditTests(unittest.TestCase):
    def test_selected_track_path_focus_stays_on_exact_low6_recipients(self):
        from audit_native_selected_item_handoff import SELECTED_TRACK_PATH_METHODS
        self.assertEqual(SELECTED_TRACK_PATH_METHODS, {
            ("LSW6;", "if", "(Lru/yandex/music/data/audio/o;Z)LvU6;"),
            ("LOW6;", "<init>",
             "(LSV6;Lru/yandex/music/data/audio/o;ZLkotlinx/coroutines/CoroutineScope;"
             "Landroid/content/Context;LGK1$a;LNW6$a;)V"),
            ("LTv9;", "if",
             "(LBK1;LGK1$a;Landroid/content/Context;Lkotlinx/coroutines/CoroutineScope;"
             "Lru/yandex/music/data/audio/o;Z)LJK1;"),
            ("LJK1;", "<init>",
             "(LBK1;LGK1$a;Landroid/content/Context;Lkotlinx/coroutines/CoroutineScope;"
             "Lru/yandex/music/data/audio/o;Z)V"),
            ("LBK1;", "try", "(Lru/yandex/music/data/audio/o;)LGl4;"),
            ("LBK1;", "this", "(Lru/yandex/music/data/audio/o;)LGl4;"),
            ("LBK1;", "for", "(Lru/yandex/music/data/audio/o;)LGl4;"),
            ("LBK1;", "new", "(Lru/yandex/music/data/audio/o;)LGl4;"),
            ("LGK1$a;", "try", "(Landroid/content/Context;Lru/yandex/music/data/audio/o;)V"),
            ("LGK1$a;", "case", "(Lru/yandex/music/data/audio/o;)V"),
            ("LGK1$a;", "else", "(Lru/yandex/music/data/audio/o;)V"),
            ("LGK1$a;", "goto", "(Lru/yandex/music/data/audio/o;)V"),
            ("LUJ5;", "return", "(Lru/yandex/music/data/audio/o;)LGl4;"),
            ("LHv4;", "if", "(Lru/yandex/music/data/audio/o;)Z"),
            ("LCK1$a;", "<init>", "(Lru/yandex/music/data/audio/o;Lkotlin/coroutines/Continuation;)V"),
            ("LCK1$c;", "<init>", "(LC3a;Lru/yandex/music/data/audio/o;)V"),
            ("LCK1$l;", "<init>", "(LD3a;Lru/yandex/music/data/audio/o;)V"),
            ("LCK1$c$a;", "<init>", "(LHl4;Lru/yandex/music/data/audio/o;)V"),
            ("LCK1$l$a;", "<init>", "(LHl4;Lru/yandex/music/data/audio/o;)V"),
            ("LaC7;", "if", "()Lru/yandex/music/data/audio/o;"),
            ("Lv3;", "throws", "(Lru/yandex/music/data/audio/o;Lru/yandex/music/data/audio/o;)Z"),
            ("LwEa;", "for", "(Lru/yandex/music/data/audio/o;)Z"),
            ("LSV6;", "else", "(Lru/yandex/music/data/audio/o;)LUV6;"),
            ("LBK1;", "break", "(Lru/yandex/music/data/audio/o;)LGl4;"),
        })

    def test_laC7_interface_scope_uses_only_direct_implementers_and_their_ancestry(self):
        owner = "LaC7;"
        implementer = "LImpl;"
        base = "LBase;"
        unrelated = "LOther;"
        profiles = {
            owner: {"is_interface": True, "is_abstract": True,
                    "superclass": None, "interfaces": set(),
                    "instance_types": set(), "static_types": set()},
            implementer: {"is_interface": False, "is_abstract": False,
                          "superclass": base, "interfaces": {owner},
                          "instance_types": set(), "static_types": set()},
            base: {"is_interface": False, "is_abstract": False,
                   "superclass": "Ljava/lang/Object;", "interfaces": set(),
                   "instance_types": set(), "static_types": set()},
            unrelated: {"is_interface": False, "is_abstract": False,
                        "superclass": "Ljava/lang/Object;", "interfaces": set(),
                        "instance_types": set(), "static_types": set()},
        }
        result = exact_track_return_owner_scope(profiles, owner)
        self.assertEqual(result["direct_implementers"], [implementer])
        self.assertEqual(result["direct_subclasses"], [])
        self.assertEqual(
            set(result["scan_owner_to_roots"]),
            {owner, implementer, base},
        )
        self.assertNotIn(unrelated, result["scan_owner_to_roots"])

    def test_laC7_abstract_class_scope_uses_only_direct_subclasses(self):
        owner = "LaC7;"
        child = "LChild;"
        unrelated = "LOther;"
        profiles = {
            owner: {"is_interface": False, "is_abstract": True,
                    "superclass": "Ljava/lang/Object;", "interfaces": set(),
                    "instance_types": set(), "static_types": set()},
            child: {"is_interface": False, "is_abstract": False,
                    "superclass": owner, "interfaces": set(),
                    "instance_types": set(), "static_types": set()},
            unrelated: {"is_interface": False, "is_abstract": False,
                        "superclass": "Ljava/lang/Object;", "interfaces": set(),
                        "instance_types": set(), "static_types": set()},
        }
        result = exact_track_return_owner_scope(profiles, owner)
        self.assertEqual(result["candidate_root_kind"], "DIRECT_CLASS_SUBCLASSES")
        self.assertEqual(result["candidate_roots"], [owner, child])
        self.assertIn(child, result["scan_owner_to_roots"])
        self.assertNotIn(unrelated, result["scan_owner_to_roots"])

    def test_laC7_missing_owner_scope_checks_only_signed_referenced_relations(self):
        owner = "LaC7;"
        implementer = "LImpl;"
        subclass = "LChild;"
        unrelated = "LOther;"
        profiles = {
            implementer: {"is_interface": False, "is_abstract": False,
                          "superclass": "Ljava/lang/Object;", "interfaces": {owner},
                          "instance_types": set(), "static_types": set()},
            subclass: {"is_interface": False, "is_abstract": False,
                       "superclass": owner, "interfaces": set(),
                       "instance_types": set(), "static_types": set()},
            unrelated: {"is_interface": False, "is_abstract": False,
                        "superclass": "Ljava/lang/Object;", "interfaces": set(),
                        "instance_types": set(), "static_types": set()},
        }
        result = exact_track_return_owner_scope(profiles, owner)
        self.assertFalse(result["owner_defined_in_signed_dex"])
        self.assertEqual(result["candidate_roots"], sorted([implementer, subclass]))
        self.assertIn(implementer, result["scan_owner_to_roots"])
        self.assertIn(subclass, result["scan_owner_to_roots"])
        self.assertNotIn(unrelated, result["scan_owner_to_roots"])

    def test_exact_parameter_field_store_refs_tracks_interface_parameter_to_this(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:2}[offset]
        method=("LWorker;","<init>","(LaC7;)V")
        target=("LWorker;","hiddenInterface", "LaC7;")
        ins=[
            (0,0x07,[0x3107]),  # move-object v1, v3
            (1,0x5b,[0x215b,0]),  # iput-object v1, v2
            (2,0x0e,[0x000e]),
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",return_value=[3]):
            refs=exact_parameter_field_store_refs(FakeDex(),method,0,100,"LaC7;")
        self.assertEqual(refs,[target])
        self.assertNotIn("hiddenInterface",str({"count":len(refs)}))

    def test_exact_parameter_field_store_refs_rejects_wrong_type_receiver_and_branch(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:2}[offset]
        method=("LWorker;","<init>","(LaC7;)V")
        wrong_type=("LWorker;","hiddenInterface","LyEa;")
        exact_type=("LWorker;","hiddenInterface","LaC7;")
        wrong_receiver=[(0,0x5b,[0x315b,0])]
        branched=[(0,0x28,[0x0028]),(1,0x5b,[0x235b,0])]
        with patch("audit_native_selected_item_handoff.typed_parameter_registers",return_value=[3]), \
             patch("audit_native_selected_item_handoff.instructions",side_effect=[[(0,0x5b,[0x215b,0])],wrong_receiver,branched]), \
             patch("audit_native_selected_item_handoff.field_id",side_effect=[wrong_type,exact_type,exact_type]):
            self.assertEqual(exact_parameter_field_store_refs(FakeDex(),method,0,100,"LaC7;"),[])
            self.assertEqual(exact_parameter_field_store_refs(FakeDex(),method,0,100,"LaC7;"),[])
            self.assertEqual(exact_parameter_field_store_refs(FakeDex(),method,0,100,"LaC7;"),[])

    def test_local_object_origin_can_report_exact_new_instance_site(self):
        class FakeDex:
            def descriptor(self, index):
                return "LyEa;"
        method=("LFactory;","create","()V")
        ins=[(0,0x22,[0x0122,0])]
        origin=local_object_register_origin(
            FakeDex(),method,0x8,100,ins,1,1,include_source_ordinal=True
        )
        self.assertEqual(origin,{
            "kind":"NEW_INSTANCE","type":"LyEa;","source_ordinal":0
        })


    def test_trace_identity_method_reports_declared_type_of_other_field_receiver(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:3, 102:1}[offset]
            def method(self, index):
                return ("LHolderFactory;", "currentHolder", "()LHolder;")
        method=("LTimelineChild;", "final", "()V")
        ins=[
            (0,0x71,[0x0071,0]),  # invoke-static {}, HolderFactory.currentHolder()
            (1,0x0c,[0x010c]),    # move-result-object v1
            (2,0x54,[0x1054,1]),  # iget-object v0, v1, MediaItem field
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",return_value=[]), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[]), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LHolder;","hidden","LOf6;")):
            trace=trace_identity_method(
                FakeDex(),method,0x0,100,
                extra_identity_types={"LOf6;"},
                track_fields_from_any_receiver=True,
            )
        field_read=next(
            event for event in trace["events"]
            if event["kind"]=="FIELD_READ_TYPED_IDENTITY"
        )
        self.assertEqual(field_read["receiver_register_type"],"LHolder;")
        self.assertFalse(field_read["receiver_is_this"])



    def test_trace_identity_method_propagates_generic_object_alias_through_check_cast(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5, 102:2}[offset]
            def descriptor(self, index):
                return "LOf6;"
            def method(self, index):
                return {
                    0: ("Ljava/util/List;", "get", "(I)Ljava/lang/Object;"),
                    1: ("LsO7;", "Z", "(ILOf6;)V"),
                }[index]
        method=("LQueueUpdater;", "update", "(LsO7;Ljava/util/List;)V")
        ins=[
            (0,0x6e,[0x026e,0]),  # List.get(index) -> Object
            (1,0x0c,[0x040c]),    # move-result-object v4
            (2,0x1f,[0x041f,2]),  # check-cast v4, MediaItem
            (3,0x6e,[0x006e,1]),  # Player.addMediaItem(index, same object)
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",
                   side_effect=lambda dex,m,flags,off,typ:
                   [0] if typ=="LsO7;" else [2] if typ=="Ljava/util/List;" else []), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=lambda op,words: [2,3] if words[1]==0 else [0,3,4]):
            trace=trace_identity_method(
                FakeDex(),method,0x8,100,
                extra_identity_types={"LsO7;","Ljava/util/List;","Ljava/lang/Object;","LOf6;"},
            )
        setter=next(
            event for event in trace["events"]
            if event.get("callee",{}).get("owner")=="LsO7;"
            and event.get("callee",{}).get("method")=="Z"
        )
        item_argument=next(
            argument for argument in setter["identity_arguments"]
            if argument["declared_argument_type"]=="LOf6;"
        )
        self.assertEqual(item_argument["identity_type"],"EXTRA_OBJECT:LOf6;")
        self.assertEqual(item_argument["origins"],["RETURNED_FROM_METHOD"])

    def test_trace_identity_method_carries_returned_reference_producer_to_window_field(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:1}[offset]
            def method(self, index):
                return {
                    0: ("LfH7;", "Y", "()LTva;"),
                    1: ("LTva;", "final", "()LTva$d;"),
                }[index]
        method=("LrD0;", "E", "()LOf6;")
        ins=[
            (0,0x72,[0x0072,0]),  # Player.currentTimeline()
            (1,0x0c,[0x010c]),    # move-result-object v1
            (2,0x6e,[0x016e,1]),  # Timeline.getWindow() -> Window
            (3,0x0c,[0x020c]),    # move-result-object v2
            (4,0x54,[0x2554,2]),  # iget-object v5, v2, MediaItem field
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",return_value=[]), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=lambda op,words: [3] if words[1]==0 else [1]), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LTva$d;","opaque","LOf6;")):
            trace=trace_identity_method(
                FakeDex(),method,0x0,100,
                capture_unproven_calls=True,
                extra_identity_types={"LTva;","LTva$d;","LOf6;"},
                track_fields_from_any_receiver=True,
            )
        window_call=next(
            event for event in trace["events"]
            if event.get("callee",{}).get("owner")=="LTva;"
            and event.get("callee",{}).get("method")=="final"
        )
        field_read=next(
            event for event in trace["events"]
            if event["kind"]=="FIELD_READ_TYPED_IDENTITY"
        )
        self.assertEqual(window_call["receiver_producer"]["method"],"Y")
        self.assertEqual(field_read["receiver_producer"]["method"],"final")
        self.assertEqual(field_read["receiver_producer"]["owner"],"LTva;")
        self.assertEqual(field_read["receiver_register_type"],"LTva$d;")

    def test_trace_identity_method_tracks_extra_instance_into_interface_typed_constructor(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:0}[offset]
            def descriptor(self, index):
                return "LyEa;"
            def method(self, index):
                return ("LCoroutine;","<init>","(LaC7;)V")
        method=("LFactory;","create","()V")
        ins=[
            (0,0x22,[0x0022,0]),  # new-instance v0, LyEa
            (1,0x70,[0x0170,1]),  # invoke-direct {v1,v0}, Coroutine.<init>(LaC7;)
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",return_value=[]), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[1,0]):
            trace=trace_identity_method(
                FakeDex(),method,0x8,100,
                extra_identity_types={"LyEa;"},
                capture_unproven_calls=True,
            )
        call=next(e for e in trace["events"] if e["kind"]=="CALL_WITH_TYPED_IDENTITY")
        self.assertEqual(call["identity_arguments"],[{
            "argument_position":1,
            "declared_argument_type":"LaC7;",
            "identity_type":"EXTRA_OBJECT:LyEa;",
            "origins":["NEW_INSTANCE_AT_0"],
        }])

    def test_trace_identity_method_tracks_extra_interface_field_into_call(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:1}[offset]
            def method(self, index):
                return ("LaC7;","if",f"(){MODEL}")
        method=("LCoroutine;","emit","()V")
        ins=[
            (0,0x54,[0x3154,0]),  # iget-object v1, v3, LaC7 field
            (1,0x72,[0x0072,0]),  # invoke-interface {v1}, LaC7.if()
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",return_value=[]), \
             patch("audit_native_selected_item_handoff.field_id",return_value=("LCoroutine;","hidden","LaC7;")), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[1]):
            trace=trace_identity_method(
                FakeDex(),method,0,100,
                extra_identity_types={"LaC7;"},
                capture_unproven_calls=True,
            )
        self.assertTrue(any(
            e["kind"]=="FIELD_READ_TYPED_IDENTITY"
            and e["identity_type"]=="EXTRA_OBJECT:LaC7;"
            and e["receiver_is_this"] is True
            for e in trace["events"]
        ))
        call=next(e for e in trace["events"] if e["kind"]=="CALL_WITH_TYPED_IDENTITY")
        self.assertEqual(call["identity_arguments"][0]["origins"],["FIELD_READ_FROM_THIS"])

    def test_trace_identity_method_can_trace_track_field_from_other_receiver(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:1}[offset]
        method=("LyEa;","set","(Ljava/lang/Object;)V")
        ins=[
            (0,0x54,[0x1054,0]),  # iget-object v0, v1, other Track field
            (1,0x5b,[0x305b,1]),  # iput-object v0, v3, this Track field
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",return_value=[]), \
             patch("audit_native_selected_item_handoff.field_id",side_effect=[
                 ("LOther;","source","Lru/yandex/music/data/audio/o;"),
                 ("LyEa;","target","Lru/yandex/music/data/audio/o;"),
             ]):
            trace=trace_identity_method(
                FakeDex(),method,0,100,
                track_fields_from_any_receiver=True,
                capture_unproven_calls=True,
            )
        self.assertTrue(any(
            e["kind"]=="FIELD_READ_TYPED_IDENTITY"
            and e["identity_type"]=="TRACK"
            and e["receiver_is_this"] is False
            for e in trace["events"]
        ))
        self.assertTrue(any(
            e["kind"]=="INSTANCE_FIELD_STORE_TYPED_IDENTITY"
            and e["identity_type"]=="TRACK"
            and "FIELD_READ_FROM_OTHER_RECEIVER" in e["origins"]
            for e in trace["events"]
        ))

    def test_media3_player_scope_follows_only_concrete_signed_ancestry(self):
        from audit_native_selected_item_handoff import (
            media3_player_implementation_scope, MEDIA3_PLAYER_OWNERS
        )
        player, exo = sorted(MEDIA3_PLAYER_OWNERS)
        profiles = {
            player: {"is_interface": True, "is_abstract": True,
                     "superclass": None, "interfaces": set()},
            exo: {"is_interface": True, "is_abstract": True,
                  "superclass": None, "interfaces": {player}},
            "LAbstractBase;": {"is_interface": False, "is_abstract": True,
                               "superclass": "Ljava/lang/Object;",
                               "interfaces": {exo}},
            "LConcretePlayer;": {"is_interface": False, "is_abstract": False,
                                 "superclass": "LAbstractBase;", "interfaces": set()},
            "LUnrelated;": {"is_interface": False, "is_abstract": False,
                            "superclass": "Ljava/lang/Object;", "interfaces": set()},
        }
        result = media3_player_implementation_scope(profiles)
        self.assertTrue(result["bounded"])
        self.assertEqual(result["implementors"], ["LConcretePlayer;"])
        self.assertIn("LAbstractBase;", result["scope_owners"])
        self.assertIn(exo, result["scope_owners"])
        self.assertIn(player, result["scope_owners"])
        self.assertNotIn("LUnrelated;", result["scope_owners"])

    def test_media3_player_scope_includes_full_superclass_and_interface_ancestry(self):
        from audit_native_selected_item_handoff import media3_player_implementation_scope
        exo = "Landroidx/media3/exoplayer/ExoPlayer;"
        player_contract = "LPlayerContract;"
        base = "LBasePlayer;"
        base_interface = "LBaseInterface;"
        concrete = "LConcretePlayer;"
        profiles = {
            exo: {"is_interface": True, "is_abstract": True,
                  "superclass": "Ljava/lang/Object;", "interfaces": {player_contract}},
            player_contract: {"is_interface": True, "is_abstract": True,
                              "superclass": "Ljava/lang/Object;", "interfaces": set()},
            concrete: {"is_interface": False, "is_abstract": False,
                       "superclass": base, "interfaces": {exo}},
            base: {"is_interface": False, "is_abstract": False,
                   "superclass": "Ljava/lang/Object;", "interfaces": {base_interface}},
            base_interface: {"is_interface": True, "is_abstract": True,
                             "superclass": "Ljava/lang/Object;", "interfaces": set()},
        }
        result = media3_player_implementation_scope(profiles)
        self.assertTrue(result["bounded"])
        self.assertEqual(result["implementors"], [concrete])
        for owner in (exo, player_contract, base, base_interface, concrete):
            self.assertIn(owner, result["scope_owners"])

    def test_media3_player_scope_handles_cycles_without_inventing_implementors(self):
        from audit_native_selected_item_handoff import media3_player_implementation_scope
        profiles = {
            "LCycleA;": {"is_interface": False, "is_abstract": False,
                         "superclass": "LCycleB;", "interfaces": set()},
            "LCycleB;": {"is_interface": False, "is_abstract": False,
                         "superclass": "LCycleA;", "interfaces": set()},
        }
        result = media3_player_implementation_scope(profiles)
        self.assertTrue(result["bounded"])
        self.assertEqual(result["concrete_implementor_count"], 0)
        self.assertEqual(result["scope_owners"], [])

    def test_media3_player_scope_stops_at_explicit_implementor_bound(self):
        from audit_native_selected_item_handoff import (
            media3_player_implementation_scope, MEDIA3_PLAYER_OWNERS
        )
        player = "Landroidx/media3/common/Player;"
        profiles = {
            player: {"is_interface": True, "is_abstract": True,
                     "superclass": None, "interfaces": set()}
        }
        for i in range(3):
            profiles[f"LPlayer{i};"] = {
                "is_interface": False, "is_abstract": False,
                "superclass": "Ljava/lang/Object;", "interfaces": {player}
            }
        result = media3_player_implementation_scope(profiles, max_implementors=2)
        self.assertFalse(result["bounded"])
        self.assertEqual(result["reason"], "PLAYER_IMPLEMENTOR_LIMIT")
        self.assertEqual(result["concrete_implementor_count"], 3)
        self.assertEqual(result["implementors"], [])


    def test_media3_timeline_method_scope_follows_only_signed_ancestry(self):
        from audit_native_selected_item_handoff import media3_timeline_method_owner_scope
        profiles = {
            "LTva;": {"is_interface": False, "is_abstract": True,
                      "superclass": "Ljava/lang/Object;", "interfaces": set()},
            "LTimelineBase;": {"is_interface": False, "is_abstract": True,
                               "superclass": "LTva;", "interfaces": set()},
            "LConcreteTimeline;": {"is_interface": False, "is_abstract": False,
                                   "superclass": "LTimelineBase;", "interfaces": set()},
            "LUnrelated;": {"is_interface": False, "is_abstract": False,
                            "superclass": "Ljava/lang/Object;", "interfaces": set()},
            "LTimelineInterface;": {"is_interface": True, "is_abstract": True,
                                    "superclass": "Ljava/lang/Object;",
                                    "interfaces": {"LTva;"}},
        }
        result = media3_timeline_method_owner_scope(profiles)
        self.assertTrue(result["bounded"])
        self.assertEqual(result["scope_owners"],
                         ["LConcreteTimeline;", "LTimelineBase;"])
        limited = media3_timeline_method_owner_scope(profiles, max_owners=1)
        self.assertFalse(limited["bounded"])
        self.assertEqual(limited["reason"], "MEDIA3_TIMELINE_OWNER_LIMIT")
        self.assertEqual(limited["scope_owners"], [])

    def test_media3_player_ancestry_contract_roles_detect_track_album_and_item_types(self):
        from audit_native_selected_item_handoff import (
            media3_player_contract_role, MODEL, ALBUM_MODEL,
            MEDIA3_MEDIA_ITEM, MEDIA3_MEDIA_SOURCE
        )
        owner = "Lhq2;"
        self.assertEqual(
            media3_player_contract_role((owner, "getX", f"(){MEDIA3_MEDIA_ITEM}")),
            "MEDIA_ITEM_TYPED_API"
        )
        self.assertEqual(
            media3_player_contract_role((owner, "setX", f"({MEDIA3_MEDIA_SOURCE})V")),
            "MEDIA_SOURCE_TYPED_API"
        )
        self.assertEqual(
            media3_player_contract_role((owner, "acceptX", f"({MODEL})V")),
            "TRACK_TYPED_API"
        )
        self.assertEqual(
            media3_player_contract_role((owner, "acceptX", f"({ALBUM_MODEL})V")),
            "ALBUM_TYPED_API"
        )

    def test_media3_player_api_roles_use_exact_item_and_source_signatures(self):
        from audit_native_selected_item_handoff import (
            media3_player_api_role, MEDIA3_PLAYER_OWNERS,
            MEDIA3_MEDIA_ITEM, MEDIA3_MEDIA_SOURCE
        )
        owner = "Landroidx/media3/common/Player;"
        self.assertIn(owner, MEDIA3_PLAYER_OWNERS)
        self.assertEqual(
            media3_player_api_role((owner, "getCurrentMediaItem",
                                    f"(){MEDIA3_MEDIA_ITEM}")),
            "CURRENT_MEDIA_ITEM_ACCESSOR"
        )
        self.assertEqual(
            media3_player_api_role((owner, "setMediaItem",
                                    f"({MEDIA3_MEDIA_ITEM})V")),
            "PLAYER_ITEM_MUTATION"
        )
        self.assertEqual(
            media3_player_api_role((owner, "setMediaSource",
                                    f"({MEDIA3_MEDIA_SOURCE})V")),
            "PLAYER_SOURCE_MUTATION"
        )
        self.assertIsNone(media3_player_api_role((owner, "unrelated", "()V")))

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
            (0,0x38,[0x0438,4]),
            (2,0x12,[0x0312]),
            (3,0x28,[0x0328]),
            (4,0x00,[0x0000]),
            (5,0x00,[0x0000]),
            (6,0x5b,[0x135b,7]),
            (8,0x0e,[0x000e])
        ]
        target=("LFp0;","hiddenTrack","Lru/yandex/music/data/audio/o;")
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target):
            result=trace_track_value_to_exact_field_store(
                FakeDex(),method,0x8,100,target
            )
        sites=result["field_store_sites"]
        self.assertTrue(result["branch_seen"])
        self.assertTrue(any(
            site["source_is_original_track_parameter"]
            and site["track_source_provenance"]=="SAME_TRACK_PARAMETER_REFERENCE"
            for site in sites
        ))
        self.assertTrue(any(
            not site["source_is_original_track_parameter"] for site in sites
        ))
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
            (0,0x71,[0x0071,9,0]),
            (3,0x0c,[0x020c]),
            (4,0x5b,[0x125b,7]),
            (6,0x0e,[0x000e])
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
            (2,0x5b,[0x345b,7]),
            (4,0x0e,[0x000e])
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
        ins=[(0,0x5b,[0x345b,7]),(2,0x0e,[0x000e])]
        target=("LFp0;","privateTrack","Lru/yandex/music/data/audio/o;")
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target):
            result=trace_track_value_to_exact_field_store(
                FakeDex(),method,0,100,target
            )
        self.assertFalse(result["field_store_sites"][0]["source_is_track_parameter_or_field"])
        self.assertTrue(result["field_store_sites"][0]["source_is_object_parameter_not_yet_cast"])
        self.assertNotIn("privateTrack",str(result))

    def test_coroutine_callsite_classifier_recognizes_resume_this_and_null_track(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:3,102:2}[offset]
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        caller=("LFp0;","invokeSuspend","(Ljava/lang/Object;)Ljava/lang/Object;")
        target=("LGp0;","new",
                "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        ins=[(0,0x12,[0x0212]),(1,0x71,[0x0071,9,0])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            with patch("audit_native_selected_item_handoff.invoke_registers",
                       return_value=[0,2,1]):
                result=classify_native_track_coroutine_callsite(
                    FakeDex(),caller,0,100,ins,1,target
                )
        self.assertEqual(result["track_argument_source"],"EXPLICIT_NULL")
        self.assertEqual(result["continuation_argument_source"],
                         "CALLER_THIS_REGISTER_CANDIDATE")
        self.assertTrue(result["exact_resume_callsite"])

    def test_coroutine_callsite_classifier_separates_initial_track_parameter(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:2}[offset]
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        caller=("LCaller;","call",
                "(Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        target=("LGp0;","new",
                "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        ins=[(0,0x71,[0x0071,9,0])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            with patch("audit_native_selected_item_handoff.invoke_registers",
                       return_value=[0,2,3]):
                result=classify_native_track_coroutine_callsite(
                    FakeDex(),caller,0x8,100,ins,0,target
                )
        self.assertEqual(
            result["track_argument_source"],
            "TRACK_PARAMETER_REGISTER_UNCHANGED_CANDIDATE"
        )
        self.assertEqual(result["continuation_argument_source"],
                         "TYPED_CONTINUATION_PARAMETER_REGISTER")
        self.assertFalse(result["exact_resume_callsite"])

    def test_coroutine_callsite_classifier_recognizes_kotlin_continuation_parameter(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:4,102:2}[offset]
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        caller=("LCaller;","call",
                "(Lru/yandex/music/data/audio/o;Lkotlin/coroutines/Continuation;)V")
        target=("LGp0;","new",
                "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        ins=[(0,0x71,[0x0071,9,0])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            with patch("audit_native_selected_item_handoff.invoke_registers",
                       return_value=[0,2,3]):
                result=classify_native_track_coroutine_callsite(
                    FakeDex(),caller,0x8,100,ins,0,target
                )
        self.assertEqual(
            result["continuation_argument_source"],
            "TYPED_CONTINUATION_PARAMETER_REGISTER"
        )
        self.assertEqual(
            result["argument_origin_trace"]["continuation_argument_origin_classification"],
            "SAME_CONTINUATION_PARAMETER_REFERENCE"
        )

    def test_coroutine_callsite_classifier_rejects_overwritten_track_parameter_register(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:2}[offset]
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        caller=("LCaller;","call",
                "(Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        target=("LGp0;","new",
                "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        ins=[
            (0,0x12,[0x0212]),
            (1,0x71,[0x0071,9,0])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            with patch("audit_native_selected_item_handoff.invoke_registers",
                       return_value=[0,2,3]):
                result=classify_native_track_coroutine_callsite(
                    FakeDex(),caller,0x8,100,ins,1,target
                )
        self.assertEqual(result["track_argument_source"],"EXPLICIT_NULL")
        self.assertTrue(result["track_argument_register_overwritten_before_call"])
        self.assertFalse(result["track_argument_register_is_track_parameter"] is False)
        self.assertFalse(result["exact_resume_callsite"])

    def test_callsite_origin_trace_preserves_track_parameter_through_move(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:5,102:2}[offset]
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        method=("LCaller;","call",
                "(Lru/yandex/music/data/audio/o;LOe2;)V")
        ins=[
            (0,0x07,[0x3107]),
            (1,0x71,[0x0071,9,0]),
            (4,0x0e,[0x000e])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            result=trace_coroutine_callsite_argument_origins(
                FakeDex(),method,0x8,100,1,1,4
            )
        self.assertEqual(
            result["track_argument_origin_classification"],
            "SAME_TRACK_PARAMETER_REFERENCE"
        )
        self.assertEqual(
            result["continuation_argument_origin_classification"],
            "SAME_CONTINUATION_PARAMETER_REFERENCE"
        )

    def test_callsite_origin_trace_recognizes_object_parameter_cast_to_track(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:4,102:2}[offset]
            def descriptor(self,index):
                return MODEL
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        method=("LCaller;","emit","(Ljava/lang/Object;LOe2;)V")
        ins=[
            (0,0x1f,[0x021f,1]),
            (2,0x71,[0x0071,9,0]),
            (5,0x0e,[0x000e])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            result=trace_coroutine_callsite_argument_origins(
                FakeDex(),method,0x8,100,2,2,3
            )
        self.assertEqual(
            result["track_argument_origin_classification"],
            "SAME_OBJECT_AS_OBJECT_PARAMETER_AFTER_CAST"
        )
        self.assertFalse(result["private_field_names_values_or_media_disclosed"])

    def test_callsite_origin_trace_preserves_kotlin_continuation_through_cast_and_move(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:4,102:2}[offset]
            def descriptor(self,index):
                return "LOe2;"
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        method=("LCaller;","if",
                "(Lru/yandex/music/data/audio/o;Lkotlin/coroutines/Continuation;)V")
        ins=[
            (0,0x1f,[0x031f,1]),
            (2,0x07,[0x3107]),
            (3,0x71,[0x0071,9,0]),
            (6,0x0e,[0x000e])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            result=trace_coroutine_callsite_argument_origins(
                FakeDex(),method,0x8,100,3,2,1
            )
        self.assertEqual(
            result["continuation_argument_origin_classification"],
            "SAME_CONTINUATION_PARAMETER_REFERENCE"
        )
        self.assertIn(
            "CONTINUATION_PARAMETER_CAST_TO_OE2",
            result["continuation_argument_origin_paths"][0]
        )

    def test_callsite_origin_trace_marks_track_field_read_as_candidate(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:4,102:2}[offset]
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        method=("LCaller;","call","(LOe2;)V")
        ins=[
            (0,0x54,[0x2154,7]),
            (2,0x71,[0x0071,9,0]),
            (5,0x0e,[0x000e])
        ]
        field=("LCaller;","privateTrack",MODEL)
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            with patch("audit_native_selected_item_handoff.field_id",return_value=field):
                result=trace_coroutine_callsite_argument_origins(
                    FakeDex(),method,0,100,2,1,3
                )
        self.assertEqual(
            result["track_argument_origin_classification"],
            "TRACK_FROM_THIS_FIELD_CANDIDATE"
        )
        self.assertNotIn("privateTrack",str(result))

    def test_flow_instantiation_census_invalidates_reused_register_on_new_instance(self):
        from unittest.mock import patch
        class FakeDex:
            def descriptor(self,index):
                return {1:"LDp0;",2:"LBC3;"}[index]
            def method(self,index):
                return {
                    10:("LDp0;","<init>","(LGp0;)V"),
                    11:("LBC3;","<init>","(LBy4;)V")
                }[index]
            def u16(self,offset):
                return {100:4,102:2}[offset]
        method=("LCaller;","start","()V")
        ins=[
            (0,0x22,[0x0122,1]),
            (1,0x70,[0x0070,10,1,2]),
            (2,0x22,[0x0122,2]),
            (3,0x70,[0x0070,11,1,2])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[1,2]):
            result=class_instantiation_and_flow_collect_sites(FakeDex(),method,0x8,100)
        ctor_rows=[x for x in result["flow_collect_or_emit_calls"]
                   if x["callee"]["method"]=="<init>"]
        self.assertEqual([x["class"] for x in ctor_rows],["LDp0;","LBC3;"])
        self.assertEqual(ctor_rows[0]["argument_positions"],[0])
        self.assertEqual(ctor_rows[1]["argument_positions"],[0])

    def test_cfg_packed_switch_exposes_exact_case_to_target_mapping(self):
        from unittest.mock import patch
        class FakeDex:
            pass
        # switch v1, payload at pc4; packed case 0 targets pc3 (return-void)
        ins=[
            (0,0x2b,[0x012b,4,0]),
            (3,0x0e,[0x000e]),
            (4,0x00,[0x0100,1,0,0,3,0])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            cfg=build_dex_control_flow(FakeDex(),100)
        self.assertEqual(cfg["branches"][0]["switch_cases"],
                         [{"key":0,"target_pc":3}])

    def test_flow_mode_branch_census_links_switch_to_default_field(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:4,102:2}[offset]
        method=("LBy4;","collect","(LHl4;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;")
        # iget v1, v0, field@1; packed-switch v1; case 0 -> return-void
        ins=[
            (0,0x54,[0x0154,1]),
            (2,0x2b,[0x012b,4,0]),
            (5,0x0e,[0x000e]),
            (6,0x00,[0x0100,1,0,0,3,0])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LBy4;","default","I")):
            result=summarize_flow_mode_branch_census(
                FakeDex(),method,0,100
            )
        branch=result["branch_sites"][0]
        self.assertEqual(branch["branch_kind"],"PACKED_SWITCH")
        self.assertEqual(branch["selector_register_origins"][0]["origin"],
                         {"kind":"INSTANCE_INT_FIELD_READ","owner":"LBy4;",
                          "field":"default","type":"I"})
        self.assertEqual(branch["switch_cases"],[{"key":0,"target_pc":5}])
        self.assertFalse(result["branch_feasibility_proven"])

    def test_selected_track_interface_implementation_owner_map_is_exact_and_bounded(self):
        from audit_native_selected_item_handoff import selected_track_interface_implementation_owners
        profiles={
            "LBK1;":{"is_interface":True,"is_abstract":True,"interfaces":set(),
                     "superclass":"Ljava/lang/Object;"},
            "LFlowImpl;":{"is_interface":False,"interfaces":{"LBK1;"},
                          "superclass":"LFlowBase;"},
            "LFlowBase;":{"is_interface":False,"interfaces":set(),
                          "superclass":"Ljava/lang/Object;"},
            "LGK1$a;":{"is_interface":False,"is_abstract":True,"interfaces":set(),
                       "superclass":"Ljava/lang/Object;"},
            "LCallbackImpl;":{"is_interface":False,"interfaces":set(),
                              "superclass":"LGK1$a;"},
        }
        result=selected_track_interface_implementation_owners(
            profiles,{"LBK1;","LGK1$a;"}
        )
        self.assertEqual(
            result["LBK1;"]["direct_implementers"],["LFlowImpl;"]
        )
        implementer_profile=next(
            row for row in result["LBK1;"]["implementer_profiles"]
            if row["owner"]=="LFlowImpl;"
        )
        self.assertEqual(implementer_profile["superclass"],"LFlowBase;")
        self.assertFalse(implementer_profile["is_abstract"])
        self.assertEqual(
            result["LBK1;"]["implementation_owners"],
            {"LFlowBase;":["LFlowImpl;"],"LFlowImpl;":["LFlowImpl;"]}
        )
        self.assertEqual(
            result["LGK1$a;"]["direct_subclasses"],["LCallbackImpl;"]
        )
        self.assertEqual(
            result["LGK1$a;"]["implementation_owners"],
            {
                "LGK1$a;":["LCallbackImpl;"],
                "LCallbackImpl;":["LCallbackImpl;"]
            }
        )

    def test_selected_track_exact_field_constructor_set_is_pinned(self):
        from audit_native_selected_item_handoff import (
            SELECTED_TRACK_PATH_TRACK_FIELD_CONSTRUCTORS,
            SELECTED_TRACK_PATH_METHODS
        )
        expected_owners={
            "LJK1;","LCK1$a;","LCK1$c;","LCK1$l;","LCK1$c$a;","LCK1$l$a;"
        }
        self.assertEqual(
            set(SELECTED_TRACK_PATH_TRACK_FIELD_CONSTRUCTORS),expected_owners
        )
        self.assertTrue(
            set(SELECTED_TRACK_PATH_TRACK_FIELD_CONSTRUCTORS.values())
            <= SELECTED_TRACK_PATH_METHODS
        )

    def test_flow_interface_implementer_census_is_direct_and_bounded(self):
        profiles={
            "LzD7;":{"interfaces":set(),"is_interface":True},
            "LImpl;":{"interfaces":{"LzD7;"},"is_interface":False},
            "LIndirect;":{"interfaces":{"LImpl;"},"is_interface":False},
            "LBK1;":{"interfaces":set(),"is_interface":True,"is_abstract":True},
            "LFlowImpl;":{"interfaces":{"LBK1;"},"is_interface":False,
                         "superclass":"Ljava/lang/Object;"},
            "LGK1$a;":{"interfaces":set(),"is_interface":False,"is_abstract":True},
            "LCallbackImpl;":{"interfaces":set(),"is_interface":False,
                              "superclass":"LGK1$a;"}
        }
        rows=summarize_flow_interface_implementers(profiles)
        row=next(x for x in rows if x["interface"]=="LzD7;")
        self.assertTrue(row["is_interface"])
        self.assertEqual(row["direct_implementers"],["LImpl;"])
        lbk=next(x for x in rows if x["interface"]=="LBK1;")
        self.assertEqual(lbk["direct_implementers"],["LFlowImpl;"])
        callback=next(x for x in rows if x["interface"]=="LGK1$a;")
        self.assertFalse(callback["is_interface"])
        self.assertEqual(callback["direct_subclasses"],["LCallbackImpl;"])

    def test_privacy_safe_flow_class_profile_converts_sets_to_type_only_lists(self):
        profile = {
            "superclass":"Ljava/lang/Object;",
            "interfaces":{"LGl4;","LzD7;"},
            "is_interface":False,
            "is_abstract":False,
            "instance_types":{"LD3a;","Liw9;"},
            "static_types":set(),
        }
        result = privacy_safe_flow_class_profile(profile)
        self.assertEqual(result["interfaces"],["LGl4;","LzD7;"])
        self.assertEqual(result["instance_field_type_descriptors"],["LD3a;","Liw9;"])
        self.assertEqual(result["static_field_type_descriptors"],[])
        self.assertNotIn("field_names",result)

    def test_privacy_safe_focused_flow_trace_omits_private_field_names_and_literals(self):
        trace = {
            "method": {"owner":"LImpl;","name":"if","signature":"()LC3a;"},
            "native_model_parameters": [{"index":0,"register":1}],
            "instructions": [
                {"ordinal":1,"op":"FIELD_READ","owner":"LImpl;",
                 "field":"privateTrackTitle","type":"Ljava/lang/String;",
                 "receiver_is_native_model":False},
                {"ordinal":2,"op":"INVOKE",
                 "callee":{"owner":"LPlayer;","method":"getCurrentTrack",
                           "signature":"()Lru/yandex/music/data/audio/o;"},
                 "native_track_argument_positions":[]},
                {"ordinal":3,"op":"CONST_STRING","destination_register":2,
                 "literal_disclosed":False},
                {"ordinal":4,"op":"FIELD_WRITE","owner":"LImpl;",
                 "field":"privateFlowField","type":"LD3a;",
                 "receiver_is_this":True,"value_is_native_track_parameter":False,
                 "value_origin":{"kind":"INSTANCE_FIELD_READ","owner":"LService;",
                                 "field":"privateSourceField","type":"LD3a;"}},
                {"ordinal":5,"op":"BRANCH_OR_SWITCH"},
            ],
        }
        result = privacy_safe_focused_method_trace(trace)
        rendered = str(result)
        self.assertNotIn("privateTrackTitle", rendered)
        self.assertNotIn("privateFlowField", rendered)
        self.assertNotIn("privateSourceField", rendered)
        self.assertEqual(result["native_track_parameter_count"],1)
        self.assertEqual(result["events"][2]["kind"],"FIELD_WRITE")
        self.assertEqual(result["events"][2]["value_origin"]["type"],"LD3a;")
        self.assertEqual(result["field_read_type_descriptors"],["Ljava/lang/String;"])
        self.assertEqual(result["field_write_type_descriptors"],["LD3a;"])
        self.assertFalse(result["private_field_names_or_values_disclosed"])
        self.assertEqual(result["events"][1]["callee"]["method"],"getCurrentTrack")

    def test_focused_method_trace_captures_object_field_writer_origin_privately(self):
        from unittest.mock import patch
        from audit_native_selected_item_handoff import focused_method_trace

        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:2}[offset]

        method = ("LMG7;", "<init>", "(LD3a;)V")
        instructions_fixture = [(0, 0x5b, [0x235b, 0])]
        with patch("audit_native_selected_item_handoff.instructions",
                   return_value=instructions_fixture), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LMG7;", "privateFlowField", "LD3a;")):
            trace = focused_method_trace(FakeDex(), method, 0, 100)

        result = privacy_safe_focused_method_trace(trace)
        write = next(event for event in result["events"]
                     if event["kind"] == "FIELD_WRITE")
        self.assertTrue(write["receiver_is_this"])
        self.assertFalse(write["value_is_native_track_parameter"])
        self.assertEqual(write["value_origin"], {
            "kind":"METHOD_PARAMETER", "index":0, "type":"LD3a;"
        })
        self.assertEqual(result["field_write_type_descriptors"], ["LD3a;"])
        self.assertNotIn("privateFlowField", str(result))

    def test_current_track_flow_candidate_is_exact_and_fail_closed(self):
        profiles = {
            "LzD7;":{"interfaces":set(),"is_interface":True,"is_abstract":True},
            "LMG7;":{"interfaces":{"LzD7;"},"is_interface":False},
            "LOther;":{"interfaces":set(),"is_interface":False},
        }
        traces = [
            {"method":{"owner":"LMG7;","name":"if","signature":"()LC3a;"},
             "native_model_parameters":[],
             "instructions":[
                 {"ordinal":1,"op":"INVOKE",
                  "callee":{"owner":sorted(PLAYER_OWNERS)[0],"method":sorted(PLAYER_METHODS)[0],
                            "signature":"()Lru/yandex/music/data/audio/o;"},
                  "native_track_argument_positions":[]}
             ]},
            {"method":{"owner":"LDp0;","name":"if",
                       "signature":"(Lru/yandex/music/data/audio/o;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;"},
             "native_model_parameters":[{"index":0,"register":1}],
             "instructions":[]},
        ]
        sites = [{
            "caller":{"owner":"Lru/yandex/music/YMApplication;","name":"onCreate"},
            "flow_collect_or_emit_calls":[{
                "class":"LDp0;",
                "callee":{"owner":"Ljm4;","method":"for",
                          "signature":"(LGl4;Lkotlinx/coroutines/CoroutineScope;LHl4;)Lk1a;"}
            }]
        }]
        result = summarize_current_track_flow_candidate(profiles,traces,sites)
        self.assertEqual(result["direct_implementers"],["LMG7;"])
        self.assertTrue(result["ym_application_on_create_subscribes_ldp0"])
        self.assertEqual(result["direct_player_api_call_count"],1)
        self.assertFalse(result["same_track_reference_from_flow_to_lgp0_new_proven"])
        self.assertFalse(result["current_selected_track_proven"])
        self.assertFalse(result["same_native_item_to_decoder_proven"])
        self.assertNotIn("privateTrackTitle",str(result))
        import json
        json.dumps(result, sort_keys=True)

    def test_primitive_flow_selector_origin_follows_move_and_decodes_const4(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:4,102:2}[offset]
        method=("LCaller;","run","()V")
        # const/4 v1, #1; move v2, v1
        ins=[(0,0x12,[0x1112]),(1,0x01,[0x1201])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            result=local_primitive_register_origin(
                FakeDex(),method,0x8,100,ins,2,2
            )
        self.assertEqual(result,{"kind":"CONST_INT","value":1})

    def test_constructor_int_parameter_store_reports_only_typed_field_identity(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:4,102:2}[offset]
        method=("LMode;","<init>","(I)V")
        # iput v1, v0, field@0; return-void
        ins=[(0,0x59,[0x2359,0]),(1,0x0e,[0x000e])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LMode;","default","I")):
            rows=constructor_int_parameter_field_store_census(
                FakeDex(),method,0,100
            )
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["source_int_parameter_indices"],[0])
        self.assertTrue(rows[0]["receiver_is_this"])

    def test_flow_argument_rows_can_skip_expensive_origins_without_losing_types(self):
        from unittest.mock import patch
        class FakeDex:
            def method(self,index):
                return ("LTarget;","for","(LGl4;Lkotlinx/coroutines/CoroutineScope;)V")
        ins=[(0,0x71,[0x0071,1,2,3])]
        with patch("audit_native_selected_item_handoff.invoke_registers",
                   return_value=[1,2]):
            rows=logical_invoke_argument_rows(
                FakeDex(),("LCaller;","run","()V"),0x8,100,ins,0,0x71,ins[0][2],
                trace_origins=False
            )
        self.assertEqual([row["type"] for row in rows],
                         ["LGl4;","Lkotlinx/coroutines/CoroutineScope;"])
        self.assertTrue(all("origin" not in row for row in rows))

    def test_flow_entry_class_profile_reports_exact_interfaces_without_inference(self):
        profiles={
            "LDp0;":{"superclass":"Ljava/lang/Object;","interfaces":{"LHl4;"},
                     "instance_types":{"LGp0;"},"static_types":set()},
            "Lwp0;":{"superclass":"Lyp0;","interfaces":set(),
                     "instance_types":{"LGp0;"},"static_types":set()}
        }
        rows=summarize_flow_entry_class_profiles(profiles)
        by_owner={row["owner"]:row for row in rows}
        self.assertTrue(by_owner["LDp0;"]["implements_flow_collector_directly"])
        self.assertFalse(by_owner["LDp0;"]["implements_flow_source_directly"])
        self.assertEqual(by_owner["Lwp0;"]["superclass"],"Lyp0;")
        self.assertFalse(by_owner["Lwp0;"]["defined_in_signed_dex"] is False)

    def test_coroutine_upstream_callsite_census_never_promotes_type_to_playback(self):
        caller=("LCaller;","load",
                "(Lru/yandex/music/data/audio/o;)Ljava/lang/Object;")
        direct=("LDp0;","if",
                "(Lru/yandex/music/data/audio/o;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;")
        row=classify_coroutine_entry_direct_upstream_call(caller,direct,7,0x71)
        self.assertTrue(row["caller_declares_track_parameter"])
        self.assertTrue(row["target_accepts_typed_track"])
        self.assertFalse(row["same_track_reference_or_active_playback_proven"])
        self.assertFalse(row["flow_interface_dispatch_proven"])
        flow=("Lwp0$a;","emit",
              "(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;")
        row=classify_coroutine_entry_direct_upstream_call(caller,flow,8,0x6e)
        self.assertTrue(row["target_accepts_object"])
        self.assertFalse(row["same_track_reference_or_active_playback_proven"])
        with self.assertRaises(ValueError):
            classify_coroutine_entry_direct_upstream_call(
                caller,("LWrong;","emit",flow[2]),9,0x6e
            )

    def test_coroutine_new_instance_ancestry_requires_declared_superclass_chain(self):
        census={"call_sites":[
            {"caller":{"owner":"LCaller;","method":"go","signature":"()V"},
             "ordinal":3,"argument_origin_trace":{
                 "continuation_argument_origin_paths":[
                     ["KOTLIN_CONTINUATION_PARAMETER"],
                     ["NEW_INSTANCE_TYPE:LDp0$a;","UNCLASSIFIED_NEW_INSTANCE_TYPE"]
                 ]}}
        ]}
        profiles={
            "LDp0$a;":{"superclass":"LOe2;"},
            "LOe2;":{"superclass":"Ljava/lang/Object;"}
        }
        result=summarize_coroutine_new_instance_ancestry(census,profiles)
        self.assertEqual(result["new_instance_class_count"],1)
        self.assertTrue(result["every_new_instance_derives_from_LOe2"])
        self.assertFalse(result["runtime_continuation_identity_proven"])
        self.assertFalse(result["new_instance_classes"][0][
            "constructor_receives_original_continuation_proven"
        ])
        profiles["LDp0$a;"]["superclass"]="LUnrelated;"
        result=summarize_coroutine_new_instance_ancestry(census,profiles)
        self.assertFalse(result["every_new_instance_derives_from_LOe2"])

    def test_callsite_origin_trace_labels_untracked_move_object_source(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:4,102:2}[offset]
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        method=("LCaller;","call",
                "(Lru/yandex/music/data/audio/o;LOe2;)V")
        ins=[
            (0,0x07,[0x0107]),
            (1,0x71,[0x0071,9,0]),
            (4,0x0e,[0x000e])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            result=trace_coroutine_callsite_argument_origins(
                FakeDex(),method,0x8,100,1,2,1
            )
        self.assertEqual(
            result["continuation_argument_origin_classification"],
            "PATH_DEPENDENT_OR_UNCLASSIFIED"
        )
        self.assertIn(
            "UNCLASSIFIED_MOVE_OBJECT_SOURCE",
            result["continuation_argument_origin_paths"][0]
        )

    def test_callsite_origin_trace_marks_continuation_field_read_as_candidate(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:4,102:2}[offset]
            def method(self,index):
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        method=("LCaller;","call","(Lkotlin/coroutines/Continuation;)V")
        ins=[
            (0,0x54,[0x2154,7]),
            (2,0x71,[0x0071,9,0]),
            (5,0x0e,[0x000e])
        ]
        field=("LCaller;","privateContinuation","Lkotlin/coroutines/Continuation;")
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            with patch("audit_native_selected_item_handoff.field_id",return_value=field):
                result=trace_coroutine_callsite_argument_origins(
                    FakeDex(),method,0,100,2,0,1
                )
        self.assertEqual(
            result["continuation_argument_origin_classification"],
            "CONTINUATION_FROM_FIELD_CANDIDATE"
        )
        self.assertNotIn("privateContinuation",str(result))

    def test_callsite_origin_trace_marks_continuation_return_as_unlinked(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:3,102:1}[offset]
            def method(self,index):
                if index==8:
                    return ("LHelper;","continuation",
                            "()Lkotlin/coroutines/Continuation;")
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        method=("LCaller;","call","(LOe2;)V")
        ins=[
            (0,0x71,[0x0071,8,0]),
            (3,0x0c,[0x010c]),
            (4,0x71,[0x0071,9,0]),
            (7,0x0e,[0x000e])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            result=trace_coroutine_callsite_argument_origins(
                FakeDex(),method,0x8,100,4,0,1
            )
        self.assertEqual(
            result["continuation_argument_origin_classification"],
            "UNLINKED_CONTINUATION_SOURCE_CANDIDATE"
        )

    def test_callsite_origin_trace_marks_returned_track_as_unlinked(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self,offset):
                return {100:3,102:1}[offset]
            def method(self,index):
                if index==8:
                    return ("LHelper;","load","()"+MODEL)
                return ("LGp0;","new",
                        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        method=("LCaller;","call","(LOe2;)V")
        ins=[
            (0,0x71,[0x0071,8,0]),
            (3,0x0c,[0x010c]),
            (4,0x71,[0x0071,9,0]),
            (7,0x0e,[0x000e])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            result=trace_coroutine_callsite_argument_origins(
                FakeDex(),method,0x8,100,4,1,2
            )
        self.assertEqual(
            result["track_argument_origin_classification"],
            "UNLINKED_TRACK_SOURCE_CANDIDATE"
        )

    def test_exact_continuation_field_writer_preserves_track_on_one_cfg_branch(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:3}[offset]
            def descriptor(self,index):
                return {1:"LFp0;"}[index]
        method=("LGp0;","new",
                "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)V")
        ins=[
            (0,0x22,[0x0022,1]),
            (2,0x38,[0x0338,4]),
            (4,0x5b,[0x025b,7]),
            (6,0x12,[0x0212]),
            (7,0x5b,[0x025b,7]),
            (9,0x0e,[0x000e])
        ]
        target=("LFp0;","hiddenTrack","Lru/yandex/music/data/audio/o;")
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins):
            with patch("audit_native_selected_item_handoff.field_id",return_value=target):
                result=trace_track_value_to_exact_field_store(
                    FakeDex(),method,0x8,100,target
                )
        self.assertTrue(result["control_flow_graph_built"])
        self.assertTrue(result["branch_seen"])
        self.assertTrue(result["same_track_parameter_store_candidate"])
        self.assertFalse(result["all_observed_store_paths_same_original_track_parameter"])
        self.assertTrue(any(
            row["source_is_original_track_parameter"]
            and row["receiver_is_target_field_owner"]
            for row in result["field_store_sites"]
        ))
        self.assertTrue(any(
            not row["source_is_original_track_parameter"]
            for row in result["field_store_sites"]
        ))
        self.assertFalse(result["control_flow_feasibility_proven"])
        self.assertFalse(result["exception_handler_edges_included"])
        self.assertNotIn("hiddenTrack",str(result))

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
        resume_ins=[(0,0x12,[0x0012]),(1,0x71,[0x0071,8,0])]
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
        self.assertTrue(result["resume_track_argument_explicit_null"])
        self.assertTrue(result["resume_continuation_call_sites"][0]["track_argument_is_explicit_null"])
        self.assertTrue(result["control_flow_graph_built"])
        self.assertTrue(result["wrapper_continuation_handoff_sites"][0]["wrapper_instance_passed"])
        self.assertFalse(result["coroutine_runtime_resume_dispatch_proven"])
        self.assertFalse(result["continuation_field_store_to_read_same_object_proven"])
        self.assertGreaterEqual(
            result["initial_entry_original_track_to_new_continuation_store_candidate_count"],1
        )
        self.assertTrue(any(
            row["same_new_continuation_object_argument"]
            and row["target"]["owner"]=="Lou3;"
            for row in result["continuation_argument_handoff_sites"]
        ))
        self.assertNotIn("hiddenTrack",str(result))
        self.assertNotIn("hiddenString",str(result))

    def test_fp0_resume_null_track_is_not_misreported_as_original_track(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:8,102:3,200:4,202:1}[offset]
            def descriptor(self,index):
                return {1:"LFp0;"}[index]
            def method(self,index):
                return {
                    8:("LGp0;","new","(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
                }[index]
        initial=("LGp0;","new","(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
        resume=("LFp0;","invokeSuspend","(Ljava/lang/Object;)Ljava/lang/Object;")
        initial_ins=[
            (0,0x1f,[0x071f,1]),
            (2,0x5b,[0x7600,3]),
            (4,0x0e,[0x000e])
        ]
        resume_ins=[(0,0x12,[0x0012]),(1,0x71,[0x0071,8,0])]
        target=("LFp0;","hiddenTrack","Lru/yandex/music/data/audio/o;")
        with patch("audit_native_selected_item_handoff.instructions",
                   side_effect=lambda d,c: initial_ins if c==100 else resume_ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   return_value=[2,0,3]):
            result=trace_native_track_coroutine_continuation(
                FakeDex(),initial,0x8,100,resume,0,200
            )
        self.assertTrue(result["resume_track_argument_explicit_null"])
        self.assertEqual(len(result["track_parameter_capture_store_candidates"]),1)
        store=result["track_parameter_capture_store_candidates"][0]
        self.assertIn("REUSED_LFp0_CONTINUATION",store["receiver_origins"])
        self.assertEqual(store["source_origins"],["NULL_TRACK_ARGUMENT_ON_EXACT_Fp0_RESUME"])
        self.assertFalse(store["same_original_track_parameter"])
        self.assertFalse(result["original_track_parameter_to_continuation_field_candidate"])
        self.assertNotIn("hiddenTrack",str(result))

    def test_coroutine_cfg_merge_drops_track_alias_when_one_branch_overwrites(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:8,102:3,200:4,202:1}[offset]
            def descriptor(self,index):
                return {1:"LFp0;"}[index]
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
        self.assertTrue(all(
            "NEW_LFp0_CONTINUATION" in row["receiver_origins"]
            for row in result["raw_track_field_store_sites"]
        ), repr(result["raw_track_field_store_sites"]))
        self.assertTrue(any(
            row["same_original_track_parameter"]
            for row in result["track_parameter_capture_store_candidates"]
        ))
        self.assertTrue(any(
            not row["same_original_track_parameter"]
            for row in result["track_parameter_capture_store_candidates"]
        ))
        self.assertTrue(result["original_track_parameter_to_continuation_field_candidate"])
        self.assertFalse(result["all_observed_store_paths_same_original_track_parameter"])
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

    def test_renderer_cfg_tracks_lad6_return_through_same_field_read_to_sink(self):
        from unittest.mock import patch

        class FakeDex:
            def u16(self, offset):
                return {100: 6, 102: 1}[offset]
            def method(self, index):
                return {
                    0: ("Lad6;", "final", "(I)Ljava/nio/ByteBuffer;"),
                    1: ("LBase;", "O", "(Ljava/nio/ByteBuffer;)Z"),
                }[index]

        field = ("LRenderer;", "privateBuffer", "Ljava/nio/ByteBuffer;")
        method = ("LRenderer;", "n", "()Z")
        target = ("LBase;", "O", "(Ljava/nio/ByteBuffer;)Z")
        by_pc = {
            0: (0x71, [0x0071, 0, 0]),
            1: (0x0c, [0x010c]),
            2: (0x5b, [0x515b, 7]),
            3: (0x54, [0x5254, 7]),
            4: (0x6e, [0x006e, 1]),
        }
        cfg = {
            "entry": 0,
            "by_pc": by_pc,
            "successors": {0:[1],1:[2],2:[3],3:[4],4:[]},
            "reachable": set(by_pc),
            "branches": [],
        }
        with patch("audit_native_selected_item_handoff.build_dex_control_flow",
                   return_value=cfg), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=field), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=lambda op, words: {0:[7],1:[5,2]}[words[1]]), \
             patch("audit_native_selected_item_handoff.written_register",
                   return_value=None), \
             patch("audit_native_selected_item_handoff.move_object_registers",
                   return_value=None):
            result = trace_renderer_buffer_field_identity_cfg(
                FakeDex(), method, 0, 100, {field}, {field: 2}, {target}
            )

        self.assertEqual(result["trace_status"], "CFG_TRACED")
        self.assertTrue(result["method_local_identity_proven"])
        sink = result["sink_calls"][0]
        self.assertEqual(sink["identity_paths"][0]["argument_position"], 1)
        self.assertEqual(sink["identity_paths"][0]["register_word_position"], 1)
        self.assertTrue(sink["same_lad6_final_field_reference_on_every_state"])
        self.assertEqual(sink["lad6_final_identity_state_count"], 1)
        self.assertEqual(sink["identity_paths"][0]["field_slot"], 2)
        self.assertEqual(sink["identity_paths"][0]["store_pc"], 2)
        self.assertEqual(sink["identity_paths"][0]["read_pc"], 3)
        self.assertEqual(sink["identity_paths"][0]["source_call_pc"], 0)
        self.assertFalse(result["runtime_virtual_dispatch_to_native_sink_proven"])
        self.assertNotIn("privateBuffer", str(result))

    def test_renderer_cfg_keeps_alternate_field_writer_branch_separate(self):
        from unittest.mock import patch

        class FakeDex:
            def u16(self, offset):
                return {100: 6, 102: 1}[offset]
            def method(self, index):
                return {
                    0: ("Lad6;", "final", "(I)Ljava/nio/ByteBuffer;"),
                    1: ("LBase;", "O", "(Ljava/nio/ByteBuffer;)Z"),
                    2: ("Lad6;", "class", "(I)Ljava/nio/ByteBuffer;"),
                }[index]

        field = ("LRenderer;", "privateBuffer", "Ljava/nio/ByteBuffer;")
        method = ("LRenderer;", "n", "()Z")
        target = ("LBase;", "O", "(Ljava/nio/ByteBuffer;)Z")
        by_pc = {
            0: (0x71, [0x0071, 0, 0]),
            1: (0x0c, [0x010c]),
            2: (0x5b, [0x515b, 7]),
            3: (0x38, [0x0638, 0]),
            4: (0x54, [0x5254, 7]),
            5: (0x00, [0x0000]),
            6: (0x71, [0x0071, 2, 0]),
            7: (0x0c, [0x030c]),
            8: (0x5b, [0x535b, 7]),
            9: (0x54, [0x5254, 7]),
            10: (0x6e, [0x006e, 1]),
        }
        cfg = {
            "entry": 0,
            "by_pc": by_pc,
            "successors": {
                0:[1],1:[2],2:[3],3:[4,6],4:[5],5:[10],
                6:[7],7:[8],8:[9],9:[10],10:[],
            },
            "reachable": set(by_pc),
            "branches": [{"pc":3}],
        }
        with patch("audit_native_selected_item_handoff.build_dex_control_flow",
                   return_value=cfg), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=field), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   side_effect=lambda op, words: {
                       0:[7],1:[5,2],2:[7]
                   }[words[1]]), \
             patch("audit_native_selected_item_handoff.written_register",
                   return_value=None), \
             patch("audit_native_selected_item_handoff.move_object_registers",
                   return_value=None):
            result = trace_renderer_buffer_field_identity_cfg(
                FakeDex(), method, 0, 100, {field}, {field: 2}, {target}
            )

        sink = result["sink_calls"][0]
        self.assertEqual(sink["distinct_incoming_identity_state_count"], 2)
        self.assertEqual(sink["lad6_final_identity_state_count"], 1)
        self.assertEqual(sink["other_or_unresolved_identity_state_count"], 1)
        self.assertFalse(sink["same_lad6_final_field_reference_on_every_state"])
        self.assertEqual(len(sink["identity_paths"]), 1)
        self.assertEqual(len(sink["unresolved_or_alternate_paths"]), 1)
        self.assertEqual(
            sink["unresolved_or_alternate_paths"][0]["status"],
            "ALTERNATE_BYTEBUFFER_RETURN"
        )
        self.assertFalse(result["all_sink_callsite_states_match"])
        self.assertNotIn("privateBuffer", str(result))

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

    def test_track_parameter_field_store_refs_match_exact_same_track_and_this(self):
        from unittest.mock import patch
        from audit_native_selected_item_handoff import track_parameter_field_store_refs
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:2}[offset]
        method=("LJK1;","<init>",f"({MODEL})V")
        target=("LJK1;","hiddenTrack",MODEL)
        ins=[
            (0,0x07,[0x3107]),  # move-object v1, v3
            (1,0x5b,[0x215b,0]),  # iput-object v1, v2
            (2,0x0e,[0x000e])
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target):
            refs=track_parameter_field_store_refs(FakeDex(),method,0,100)
        self.assertEqual(refs,[target])
        self.assertNotIn("hiddenTrack",str({"count":len(refs)}))

    def test_track_parameter_field_store_refs_reject_other_receiver_and_branch_alias(self):
        from unittest.mock import patch
        from audit_native_selected_item_handoff import track_parameter_field_store_refs
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:2}[offset]
        method=("LJK1;","<init>",f"({MODEL})V")
        target=("LJK1;","hiddenTrack",MODEL)
        wrong_receiver=[(0,0x5b,[0x315b,0])]
        branched=[(0,0x28,[0x0028]),(1,0x5b,[0x235b,0])]
        with patch("audit_native_selected_item_handoff.instructions",side_effect=[wrong_receiver,branched]), \
             patch("audit_native_selected_item_handoff.field_id",return_value=target):
            self.assertEqual(track_parameter_field_store_refs(FakeDex(),method,0,100),[])
            self.assertEqual(track_parameter_field_store_refs(FakeDex(),method,0,100),[])

    def test_cfg_track_field_alias_survives_branch_join_only_when_all_paths_preserve_it(self):
        from unittest.mock import patch
        from audit_native_selected_item_handoff import trace_exact_track_field_method_cfg

        class FakeDex:
            def u16(self, offset):
                return {100:6,102:3}[offset]
            def method(self, index):
                return ("LHl4;","emit",
                        "(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;")

        method=("LCK1$c$a;","emit",
                "(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;")
        field=("LCK1$c$a;","hiddenTrack",MODEL)
        ins=[
            (0,0x54,[0x3054,0]),  # iget-object v0, v3, exact Track field
            (1,0x38,[0x0038,0]),  # branch; both paths join at pc 4
            (2,0x00,[0x0000]),
            (3,0x00,[0x0000]),
            (4,0x72,[0x0072,0,0]),  # FlowCollector.emit(Object, Continuation)
            (5,0x0e,[0x000e]),
        ]
        by_pc={pc:(op,words) for pc,op,words in ins}
        cfg={
            "instructions":ins,"by_pc":by_pc,
            "successors":{0:[1],1:[2,3],2:[4],3:[4],4:[5],5:[]},
            "reachable":{0,1,2,3,4,5},"branches":[{"pc":1}],"entry":0
        }
        overwritten=list(ins)
        overwritten[2]=(2,0x12,[0x0012])  # one path overwrites Track register v0
        overwritten_by_pc={pc:(op,words) for pc,op,words in overwritten}
        overwritten_cfg={
            "instructions":overwritten,"by_pc":overwritten_by_pc,
            "successors":{0:[1],1:[2,3],2:[4],3:[4],4:[5],5:[]},
            "reachable":{0,1,2,3,4,5},"branches":[{"pc":1}],"entry":0
        }
        with patch("audit_native_selected_item_handoff.build_dex_control_flow",
                   side_effect=[cfg,overwritten_cfg]):
            with patch("audit_native_selected_item_handoff.field_id",
                       return_value=field):
                with patch("audit_native_selected_item_handoff.invoke_registers",
                           return_value=[1,0,2]):
                    preserved=trace_exact_track_field_method_cfg(
                        FakeDex(),method,0,100,{field}
                    )
                    lost=trace_exact_track_field_method_cfg(
                        FakeDex(),method,0,100,{field}
                    )
        proven=[row for row in preserved["events"]
                if row["kind"]=="CALL_WITH_TYPED_IDENTITY"]
        rejected=[row for row in lost["events"]
                  if row["kind"]=="CALL_WITH_TYPED_IDENTITY"]
        self.assertEqual(len(proven),1)
        self.assertEqual(proven[0]["callee"]["owner"],"LHl4;")
        self.assertTrue(proven[0]["identity_arguments"][0]["same_exact_track_field_identity"])
        self.assertEqual(rejected,[])
        self.assertGreaterEqual(preserved["branch_count"],1)

    def test_identity_method_trace_rejects_track_alias_in_primitive_argument(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:2,102:1}[offset]
            def method(self, index):
                return ("LApi;","accept","(I)V")
        method=("LWorker;","run",f"({MODEL})V")
        ins=[(0,0x71,[0x0171,0])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[1]):
            result=trace_identity_method(FakeDex(),method,0x8,100)
        self.assertFalse(any(
            row["kind"]=="CALL_WITH_TYPED_IDENTITY"
            for row in result["events"]
        ))

    def test_identity_method_trace_reads_only_the_exact_selected_track_field(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:1}[offset]
            def method(self, index):
                return ("LApi;","consume",f"({MODEL})V")
        method=("LJK1;","render","()V")
        exact=("LJK1;","hiddenTrack",MODEL)
        ins=[(0,0x54,[0x3254,0]),(1,0x71,[0x0071,0])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",return_value=exact), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[2]):
            accepted=trace_identity_method(
                FakeDex(),method,0,100,exact_track_field_refs={exact}
            )
            rejected=trace_identity_method(
                FakeDex(),method,0,100,
                exact_track_field_refs={("LJK1;","differentTrack",MODEL)}
            )
        self.assertTrue(any(
            row["kind"]=="FIELD_READ_TYPED_IDENTITY"
            for row in accepted["events"]
        ))
        self.assertTrue(any(
            row["kind"]=="CALL_WITH_TYPED_IDENTITY"
            for row in accepted["events"]
        ))
        self.assertFalse(any(
            row["kind"]=="CALL_WITH_TYPED_IDENTITY"
            for row in rejected["events"]
        ))
        self.assertNotIn("hiddenTrack",str(accepted))

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



    def test_receiver_cfg_proves_same_lya_allocation_across_both_branch_paths(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5, 102:1}[offset]
            def descriptor(self, index):
                return "LyEa;"
            def method(self, index):
                return ("LaC7;", "if", f"(){MODEL}")
        method=("LFlow;", "emit", "()V")
        target=("LaC7;", "if", f"(){MODEL}")
        ins=[
            (0,0x22,[0x0022,0]),       # new-instance v0, LyEa
            (2,0x38,[0x0138,4]),       # if-eqz v1, branch to pc 6
            (4,0x07,[0x0207]),         # move-object v2, v0
            (5,0x28,[0x0228]),         # goto pc 7
            (6,0x07,[0x0207]),         # move-object v2, v0
            (7,0x72,[0x0272,0,0]),     # invoke-interface {v2}, LaC7.if()
            (10,0x0e,[0x000e]),
        ]
        profiles={
            "LyEa;":{"superclass":"Ljava/lang/Object;","interfaces":{"LaC7;"}},
            "LaC7;":{"superclass":"Ljava/lang/Object;","interfaces":set()},
        }
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[2]):
            trace=trace_exact_object_receiver_call_cfg(
                FakeDex(),method,0,100,target,"LaC7;",profiles
            )
        self.assertEqual(trace["callsite_count"],1)
        call=trace["callsites"][0]
        self.assertTrue(call["receiver_identity_proven_on_all_paths"])
        self.assertTrue(call["exact_lya_instance_proven_on_all_paths"])
        self.assertIn("NEW_INSTANCE:LyEa;@0",
                      call["receiver_origins_common_to_all_paths"])
        self.assertFalse(call["runtime_dispatch_to_lya_proven"])

    def test_receiver_cfg_rejects_different_lya_allocations_at_branch_join(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:5, 102:1}[offset]
            def descriptor(self, index):
                return "LyEa;"
            def method(self, index):
                return ("LaC7;", "if", f"(){MODEL}")
        method=("LFlow;", "emit", "()V")
        target=("LaC7;", "if", f"(){MODEL}")
        ins=[
            (0,0x22,[0x0022,0]),       # new-instance v0, LyEa
            (2,0x38,[0x0138,4]),       # if-eqz v1, branch to pc 6
            (4,0x07,[0x0207]),         # first path keeps v0
            (5,0x28,[0x0528]),         # goto pc 10
            (6,0x22,[0x0322,0]),       # second path creates another LyEa
            (8,0x07,[0x3207]),         # move-object v2, v3
            (9,0x28,[0x0128]),         # goto pc 10
            (10,0x72,[0x0272,0,0]),    # invoke-interface {v2}, LaC7.if()
            (13,0x0e,[0x000e]),
        ]
        profiles={
            "LyEa;":{"superclass":"Ljava/lang/Object;","interfaces":{"LaC7;"}},
            "LaC7;":{"superclass":"Ljava/lang/Object;","interfaces":set()},
        }
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[2]):
            trace=trace_exact_object_receiver_call_cfg(
                FakeDex(),method,0,100,target,"LaC7;",profiles
            )
        call=trace["callsites"][0]
        self.assertFalse(call["receiver_identity_proven_on_all_paths"])
        self.assertFalse(call["exact_lya_instance_proven_on_all_paths"])
        self.assertIn("NEW_INSTANCE:LyEa;@0",str(call["receiver_origins_by_path"]))
        self.assertIn("NEW_INSTANCE:LyEa;@6",str(call["receiver_origins_by_path"]))

    def test_receiver_cfg_identifies_exact_provider_return_origin(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:4,102:1}[offset]
            def method(self, index):
                if index == 0:
                    return ("LzA9;", "if", "()LaC7;")
                return ("LaC7;", "if", f"(){MODEL}")
        method=("LFlow;", "emit", "()V")
        target=("LaC7;", "if", f"(){MODEL}")
        ins=[
            (0,0x6e,[0x006e,0,0]),     # invoke-virtual provider
            (3,0x0c,[0x000c]),         # move-result-object v0
            (4,0x72,[0x0072,1,0]),     # invoke-interface {v0}, LaC7.if()
            (7,0x0e,[0x000e]),
        ]
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[0]):
            trace=trace_exact_object_receiver_call_cfg(
                FakeDex(),method,0,100,target,"LaC7;",{}
            )
        call=trace["callsites"][0]
        self.assertTrue(call["receiver_identity_proven_on_all_paths"])
        self.assertEqual(
            call["receiver_origins_common_to_all_paths"],
            ["RETURNED_FROM_METHOD:LzA9;|if|()LaC7;@0"]
        )

    def test_dex_type_assignability_uses_only_declared_signed_ancestry(self):
        profiles={
            "LyEa;":{"superclass":"Ljava/lang/Object;","interfaces":{"LaC7;"}},
            "LaC7;":{"superclass":"Ljava/lang/Object;","interfaces":set()},
            "LOther;":{"superclass":"Ljava/lang/Object;","interfaces":set()},
        }
        self.assertTrue(dex_type_assignable_to("LyEa;","LaC7;",profiles))
        self.assertFalse(dex_type_assignable_to("LOther;","LaC7;",profiles))




    def test_receiver_cfg_tracks_untyped_parameter_through_exact_interface_cast(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100:2, 102:1}[offset]
            def descriptor(self, index):
                return "LaC7;"
            def method(self, index):
                return ("LaC7;", "if", f"(){MODEL}")
        method=("LFlow;", "emit", "(Ljava/lang/Object;)V")
        target=("LaC7;", "if", f"(){MODEL}")
        ins=[
            (0,0x1f,[0x011f,0]),       # check-cast v1, LaC7
            (2,0x72,[0x0172,0,0]),     # invoke-interface {v1}, LaC7.if()
            (5,0x0e,[0x000e]),
        ]
        profiles={"LaC7;":{"superclass":"Ljava/lang/Object;","interfaces":set()}}
        with patch("audit_native_selected_item_handoff.instructions",return_value=ins), \
             patch("audit_native_selected_item_handoff.invoke_registers",return_value=[1]):
            trace=trace_exact_object_receiver_call_cfg(
                FakeDex(),method,0x8,100,target,"LaC7;",profiles
            )
        call=trace["callsites"][0]
        self.assertTrue(call["receiver_identity_proven_on_all_paths"])
        self.assertTrue(call["receiver_type_proven_on_all_paths"])
        self.assertIn("UNREFINED_PARAMETER:Ljava/lang/Object;@0",
                      call["receiver_origins_common_to_all_paths"])
        self.assertIn("CHECK_CAST:LaC7;@0",
                      call["receiver_origins_common_to_all_paths"])


    def test_exact_object_method_trace_links_delegate_result_to_return(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100: 2, 102: 1}[offset]
            def method(self, index):
                return ("LfH7;", "else", "()LkD7;")
        method = ("Lp24;", "else", "()LkD7;")
        ins = [
            (0, 0x54, [0x1054, 0]),       # iget-object v0, this, Player delegate
            (2, 0x72, [0x0072, 0, 0]),   # invoke-interface {v0}, LfH7.else()
            (5, 0x0c, [0x000c]),         # move-result-object v0
            (6, 0x11, [0x0011]),         # return-object v0
        ]
        with patch("audit_native_selected_item_handoff.instructions", return_value=ins), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("Lp24;", "privateField", "LfH7;")), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   return_value=[0]):
            trace = trace_exact_object_method_body(FakeDex(), method, 0, 100)
        self.assertTrue(trace["calls"][0]["receiver_identity_proven"])
        self.assertIn("FIELD_READ_FROM_THIS:LfH7;@0",
                      trace["calls"][0]["receiver_origins"])
        self.assertTrue(trace["same_call_result_to_return_proven"])
        self.assertEqual(trace["returned_call"], {
            "owner": "LfH7;", "method": "else", "signature": "()LkD7;"
        })
        self.assertFalse(trace["private_field_names_or_values_disclosed"])

    def test_exact_object_method_trace_proves_same_this_field_return_and_fails_closed_on_branch(self):
        from unittest.mock import patch
        class FakeDex:
            def u16(self, offset):
                return {100: 2, 102: 1}[offset]
        method = ("Lp24;", "else", "()LkD7;")
        direct_field = [
            (0, 0x54, [0x1054, 0]),  # iget-object v0, this, LkD7 field
            (2, 0x11, [0x0011]),     # return-object v0
        ]
        branch_field = [
            (0, 0x28, [0x0028]),     # goto
            (1, 0x54, [0x1054, 0]),
            (3, 0x11, [0x0011]),
        ]
        with patch("audit_native_selected_item_handoff.instructions",
                   side_effect=[direct_field, branch_field]), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("Lp24;", "privateField", "LkD7;")):
            direct = trace_exact_object_method_body(FakeDex(), method, 0, 100)
            branched = trace_exact_object_method_body(FakeDex(), method, 0, 100)
        self.assertTrue(direct["same_this_field_object_to_return_proven"])
        self.assertFalse(direct["same_call_result_to_return_proven"])
        self.assertTrue(branched["branch_seen"])
        self.assertFalse(branched["same_this_field_object_to_return_proven"])


    def test_track_identity_cfg_keeps_only_common_parameter_alias_across_branches(self):
        from unittest.mock import patch

        class FakeDex:
            def u16(self, offset):
                return {100: 4, 102: 1}[offset]
            def method(self, index):
                return ("LPlayer;", "setItem", f"({MODEL})V")

        method = ("LFactory;", "suspendCall", f"({MODEL})V")
        instructions = [
            (0, 0x38, [0x0038, 0]),  # branch to two paths
            (1, 0x07, [0x0107]),     # path A: move Track parameter to v1
            (2, 0x07, [0x0107]),     # path B: same exact move
            (3, 0x71, [0x0071, 0]),  # invoke-static {v1}, Player.setItem(Track)
            (4, 0x0e, [0x000e]),
        ]
        overwritten = list(instructions)
        overwritten[2] = (2, 0x12, [0x0112])  # path B overwrites v1
        def cfg(rows):
            by_pc = {pc: (op, words) for pc, op, words in rows}
            return {
                "instructions": rows,
                "by_pc": by_pc,
                "successors": {
                    0: [1, 2], 1: [3], 2: [3], 3: [4], 4: []
                },
                "reachable": {0, 1, 2, 3, 4},
                "branches": [{"pc": 0}],
                "entry": 0,
            }

        def run(rows, cfg_result):
            with patch("audit_native_selected_item_handoff.build_dex_control_flow",
                       return_value=cfg_result), \
                 patch("audit_native_selected_item_handoff.typed_parameter_registers",
                       side_effect=lambda _d, _m, _f, _c, typ: [3] if typ == MODEL else []), \
                 patch("audit_native_selected_item_handoff.move_object_registers",
                       side_effect=lambda op, _w: (1, 3) if op == 0x07 else None), \
                 patch("audit_native_selected_item_handoff.written_register",
                       side_effect=lambda op, words: 1 if op == 0x12 else None), \
                 patch("audit_native_selected_item_handoff.invoke_registers",
                       return_value=[1]):
                return trace_track_identity_method_cfg(
                    FakeDex(), method, 0x8, 100
                )

        preserved = run(instructions, cfg(instructions))
        lost = run(overwritten, cfg(overwritten))
        proven = [
            row for row in preserved["events"]
            if row["kind"] == "CALL_WITH_TYPED_IDENTITY"
        ]
        possible = [
            row for row in lost["events"]
            if row["kind"] == "CALL_WITH_POSSIBLE_IDENTITY"
        ]
        self.assertEqual(len(proven), 1)
        self.assertEqual(proven[0]["identity_arguments"][0]["origins"], ["TRACK_PARAMETER"])
        self.assertTrue(proven[0]["identity_is_common_to_all_incoming_paths"])
        self.assertEqual(len(possible), 1)
        self.assertFalse(possible[0]["identity_is_common_to_all_incoming_paths"])


    def test_track_identity_cfg_does_not_cross_label_wrapper_as_track_or_album(self):
        from unittest.mock import patch

        class FakeDex:
            def u16(self, offset):
                return {100: 3, 102: 1}[offset]
            def method(self, index):
                return ("LWorker;", "acceptWrapper", f"({WRAPPER})V")

        method = ("LFactory;", "call", f"({WRAPPER})V")
        instructions = [
            (0, 0x71, [0x0071, 0]),  # invoke-static {v2}, acceptWrapper
            (1, 0x5b, [0x215b, 0]),  # unrelated Object field store must be ignored
            (2, 0x0e, [0x000e]),
        ]
        cfg = {
            "instructions": instructions,
            "by_pc": {pc: (op, words) for pc, op, words in instructions},
            "successors": {0: [1], 1: [2], 2: []},
            "reachable": {0, 1, 2},
            "branches": [],
            "entry": 0,
        }
        with patch("audit_native_selected_item_handoff.build_dex_control_flow",
                   return_value=cfg), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",
                   side_effect=lambda _d, _m, _f, _c, typ: [2] if typ == WRAPPER else []), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   return_value=[2]), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=("LFactory;", "hidden", "Ljava/lang/Object;")), \
             patch("audit_native_selected_item_handoff.written_register",
                   return_value=None):
            trace = trace_track_identity_method_cfg(FakeDex(), method, 0x8, 100)

        calls = [
            row for row in trace["events"]
            if row["kind"] == "CALL_WITH_TYPED_IDENTITY"
        ]
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(calls[0]["identity_arguments"]), 1)
        self.assertEqual(calls[0]["identity_arguments"][0]["identity_type"], "TRACK_WRAPPER")
        self.assertEqual(
            calls[0]["identity_arguments"][0]["origins"],
            ["TRACK_WRAPPER_PARAMETER"],
        )


    def test_trace_identity_method_reports_exact_playlist_list_argument_provenance(self):
        from unittest.mock import patch

        target = ("LXk6;", "if", "(LsO7;LXi6$e;Ljava/util/List;)V")

        class FakeDex:
            def u16(self, offset):
                return {100: 3, 102: 3}[offset]
            def method(self, index):
                return target

        caller = ("LQueueFactory;", "dispatch", "(LsO7;LXi6$e;Ljava/util/List;)V")
        instructions = [(0, 0x71, [0x0071, 0])]  # invoke-static exact target
        with patch("audit_native_selected_item_handoff.instructions", return_value=instructions), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",
                   side_effect=lambda _d, _m, _f, _c, typ:
                   [0] if typ == "LsO7;" else [1] if typ == "LXi6$e;" else [2] if typ == "Ljava/util/List;" else []), \
             patch("audit_native_selected_item_handoff.invoke_registers", return_value=[0, 1, 2]), \
             patch("audit_native_selected_item_handoff.expand_invoke_register_types",
                   return_value=["LsO7;", "LXi6$e;", "Ljava/util/List;"]):
            trace = trace_identity_method(
                FakeDex(), caller, 0x8, 100,
                extra_identity_types={"LsO7;", "LXi6$e;", "Ljava/util/List;"},
                capture_argument_provenance_targets={target},
            )

        event = next(row for row in trace["events"]
                     if row["kind"] == "CALL_ARGUMENT_PROVENANCE")
        list_argument = next(row for row in event["reference_arguments"]
                             if row["declared_argument_type"] == "Ljava/util/List;")
        self.assertEqual(list_argument["argument_position"], 2)
        self.assertEqual(list_argument["register_type_descriptor"], "Ljava/util/List;")
        self.assertEqual(
            list_argument["identity_origins"][0]["origins"],
            ["CALLER_TYPED_PARAMETER"],
        )
        self.assertIsNone(list_argument["producer"])

    def test_exact_playlist_update_census_finds_unfiltered_direct_callers(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from unittest.mock import patch

        target = ("LXk6;", "if", "(LsO7;LXi6$e;Ljava/util/List;)V")
        caller = ("LUnrelatedOwner;", "dispatch", "()V")

        class FakeDex:
            def __init__(self, _data):
                pass
            def method(self, index):
                return target if index == 9 else ("LOther;", "unrelated", "()V")

        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("classes.dex", b"fake-dex")
            with patch("audit_native_selected_item_handoff.Dex", FakeDex), \
                 patch("audit_native_selected_item_handoff.method_definitions_with_flags",
                       return_value=[(caller, 0x8, 100)]), \
                 patch("audit_native_selected_item_handoff.instructions",
                       return_value=[
                           (17, 0x71, [0x0071, 9]),
                           (18, 0x71, [0x0071, 10]),
                       ]), \
                 patch("audit_native_selected_item_handoff.trace_identity_method",
                       return_value={"method": {}, "events": []}) as trace, \
                 patch("audit_native_selected_item_handoff.inspect_exact_playlist_update_method_handle_sites",
                       return_value={"bounded": True, "matching_method_handle_count": 0,
                                     "matching_call_site_count": 0,
                                     "invoke_custom_reference_site_count": 0}) :
                result = inspect_exact_playlist_update_callers([apk])

        self.assertTrue(result["bounded"])
        self.assertEqual(result["direct_invoke_callsite_count"], 1)
        self.assertEqual(result["distinct_caller_method_count"], 1)
        self.assertEqual(result["callers"][0]["caller"]["owner"], "LUnrelatedOwner;")
        self.assertEqual(result["callers"][0]["ordinal"], 17)
        self.assertEqual(len(result["caller_identity_traces"]), 1)
        self.assertEqual(trace.call_count, 1)


    def test_exact_playlist_method_handle_scan_finds_invoke_custom_reference(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from unittest.mock import patch

        target = ("LXk6;", "if", "(LsO7;LXi6$e;Ljava/util/List;)V")
        caller = ("LFactory;", "makeCallback", "()V")
        data = bytearray(512)
        data[52:56] = (100).to_bytes(4, "little")
        data[100:104] = (2).to_bytes(4, "little")
        # map item: method_handle_item, one row at offset 200
        data[104:106] = (0x0008).to_bytes(2, "little")
        data[108:112] = (1).to_bytes(4, "little")
        data[112:116] = (200).to_bytes(4, "little")
        # map item: call_site_id_item, one row at offset 300
        data[116:118] = (0x0007).to_bytes(2, "little")
        data[120:124] = (1).to_bytes(4, "little")
        data[124:128] = (300).to_bytes(4, "little")
        # invoke-static method handle, member method index 7
        data[200:202] = (4).to_bytes(2, "little")
        data[204:206] = (7).to_bytes(2, "little")
        # call_site_id points at an encoded_array with one VALUE_METHOD_HANDLE(0)
        data[300:304] = (400).to_bytes(4, "little")
        data[400:403] = bytes([1, 0x16, 0])

        class FakeDex:
            def __init__(self, _bytes):
                self.data = memoryview(data)
            def bounds(self, offset, size):
                if offset < 0 or size < 0 or offset + size > len(self.data):
                    raise ValueError("bounds")
            def u16(self, offset):
                self.bounds(offset, 2)
                return int.from_bytes(self.data[offset:offset + 2], "little")
            def u32(self, offset):
                self.bounds(offset, 4)
                return int.from_bytes(self.data[offset:offset + 4], "little")
            def method(self, index):
                return target if index == 7 else ("LOther;", "other", "()V")

        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("classes.dex", b"fake-dex")
            with patch("audit_native_selected_item_handoff.Dex", FakeDex), \
                 patch("audit_native_selected_item_handoff.method_definitions_with_flags",
                       return_value=[(caller, 0x8, 1000)]), \
                 patch("audit_native_selected_item_handoff.instructions",
                       return_value=[(5, 0xfc, [0x00fc, 0, 0])]):
                result = inspect_exact_playlist_update_method_handle_sites([apk])

        self.assertEqual(result["matching_method_handle_count"], 1)
        self.assertEqual(result["matching_call_site_count"], 1)
        self.assertEqual(result["invoke_custom_reference_site_count"], 1)
        self.assertEqual(
            result["invoke_custom_reference_sites"][0]["caller"]["owner"],
            "LFactory;",
        )
        self.assertEqual(
            result["invoke_custom_reference_sites"][0]["call_site_index"],
            0,
        )


    def test_exact_playlist_callback_contract_traces_interface_callers_and_list_get(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from unittest.mock import patch

        signature = "(LsO7;LXi6$e;Ljava/util/List;)V"
        interface_method = ("LLl6$c;", "if", signature)
        implementation_method = ("LXk6;", "if", signature)
        caller = ("LCallbackDispatcher;", "dispatch", "()V")

        class FakeDex:
            def __init__(self, _data):
                pass
            def method(self, index):
                return interface_method if index == 9 else ("LOther;", "other", "()V")

        class_profiles = {
            "LLl6$c;": {
                "is_interface": True,
                "is_abstract": True,
                "superclass": None,
                "interfaces": set(),
            },
            "LXk6;": {
                "is_interface": False,
                "is_abstract": False,
                "superclass": "Ljava/lang/Object;",
                "interfaces": {"LLl6$c;"},
            },
        }

        def fake_instructions(_dex, code_off):
            if code_off == 200:
                return [(5, 0x72, [0x0072, 9])]  # invoke-interface LLl6$c.if(...)
            return []

        cfg_trace = {
            "method": {"owner": "LCallbackDispatcher;", "method": "dispatch", "signature": "()V"},
            "callsite_count": 1,
            "callsites": [{"receiver_identity_proven_on_all_paths": True}],
        }
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("classes.dex", b"fake-dex")
            with patch("audit_native_selected_item_handoff.Dex", FakeDex):
                with patch(
                    "audit_native_selected_item_handoff.method_definitions_with_flags",
                    return_value=[
                        (implementation_method, 0, 100),
                        (caller, 0, 200),
                    ],
                ):
                    with patch("audit_native_selected_item_handoff.instructions",
                               side_effect=fake_instructions):
                        with patch("audit_native_selected_item_handoff.trace_identity_method",
                                   return_value={"events": []}) as argument_trace:
                            with patch(
                                "audit_native_selected_item_handoff.trace_exact_object_receiver_call_cfg",
                                return_value=cfg_trace,
                            ) as receiver_trace:
                                result = inspect_exact_playlist_callback_contract(
                                    [apk], class_profiles
                                )

        self.assertTrue(result["bounded"])
        self.assertEqual(result["interface_method_code_body_count"], 0)
        self.assertTrue(result["interface_method_is_abstract"])
        self.assertTrue(result["interface_method_reference_observed"])
        self.assertEqual(result["concrete_implementers"], ["LXk6;"])
        self.assertEqual(result["implementation_method_code_body_count"], 1)
        self.assertEqual(result["direct_interface_callsite_count"], 1)
        self.assertEqual(result["callers"][0]["caller"]["owner"], "LCallbackDispatcher;")
        self.assertEqual(len(result["caller_traces"]), 1)
        self.assertEqual(len(result["list_get_receiver_traces"]), 1)
        self.assertEqual(argument_trace.call_count, 1)
        self.assertEqual(receiver_trace.call_count, 2)


    def test_exact_playlist_runner_construction_traces_field_writers_and_callers(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from unittest.mock import patch

        run_method = ("LKl6;", "run", "()V")
        constructor = ("LKl6;", "<init>", "(LLl6$c;LXi6$e;Lek6;Ljava/util/List;)V")
        caller = ("LPlaylistOwner;", "schedule", "()V")
        field_refs = {
            1: ("LKl6;", "callback", "LLl6$c;"),
            2: ("LKl6;", "entry", "LXi6$e;"),
            3: ("LKl6;", "items", "Ljava/util/List;"),
            4: ("LKl6;", "outer", "Lek6;"),
        }

        class FakeDex:
            def __init__(self, _data):
                pass
            def u16(self, offset):
                return {
                    100: 5, 102: 1,
                    200: 6, 202: 5,
                    300: 5, 302: 1,
                }[offset]
            def method(self, index):
                return constructor if index == 9 else ("LOther;", "other", "()V")

        class_profiles = {
            "LKl6;": {
                "is_interface": False,
                "is_abstract": False,
                "superclass": "Ljava/lang/Object;",
                "interfaces": set(),
                "instance_field_type_descriptors": [
                    "LLl6$c;", "LXi6$e;", "Lek6;", "Ljava/util/List;",
                ],
                "static_field_type_descriptors": [],
            }
        }

        def fake_instructions(_dex, code_off):
            if code_off == 100:
                return [
                    (8, 0x54, [0x4054, 4]),
                    (10, 0x54, [0x4054, 1]),
                    (12, 0x54, [0x4054, 2]),
                    (14, 0x54, [0x4054, 3]),
                ]
            if code_off == 200:
                return [
                    (1, 0x5b, [0x105b, 4]),
                    (2, 0x5b, [0x105b, 1]),
                    (3, 0x5b, [0x105b, 2]),
                    (4, 0x5b, [0x105b, 3]),
                ]
            if code_off == 300:
                return [(5, 0x70, [0x0070, 9])]
            return []

        def fake_trace(_dex, method, _flags, _code_off, **_kwargs):
            if method == constructor:
                return {
                    "events": [
                        {
                            "ordinal": 1,
                            "kind": "INSTANCE_FIELD_STORE_TYPED_IDENTITY",
                            "identity_type": "EXTRA_OBJECT:Lek6;",
                            "origins": ["CALLER_TYPED_PARAMETER"],
                        },
                        {
                            "ordinal": 2,
                            "kind": "INSTANCE_FIELD_STORE_TYPED_IDENTITY",
                            "identity_type": "EXTRA_OBJECT:LLl6$c;",
                            "origins": ["CALLER_TYPED_PARAMETER"],
                        },
                        {
                            "ordinal": 3,
                            "kind": "INSTANCE_FIELD_STORE_TYPED_IDENTITY",
                            "identity_type": "EXTRA_OBJECT:LXi6$e;",
                            "origins": ["CALLER_TYPED_PARAMETER"],
                        },
                        {
                            "ordinal": 4,
                            "kind": "INSTANCE_FIELD_STORE_TYPED_IDENTITY",
                            "identity_type": "EXTRA_OBJECT:Ljava/util/List;",
                            "origins": ["CALLER_TYPED_PARAMETER"],
                        },
                    ]
                }
            return {"events": []}

        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("classes.dex", b"fake-dex")
            with patch("audit_native_selected_item_handoff.Dex", FakeDex):
                with patch(
                    "audit_native_selected_item_handoff.method_definitions_with_flags",
                    side_effect=lambda _dex: iter([
                        (run_method, 0, 100),
                        (constructor, 0, 200),
                        (caller, 0, 300),
                    ]),
                ):
                    with patch("audit_native_selected_item_handoff.instructions",
                               side_effect=fake_instructions):
                        with patch("audit_native_selected_item_handoff.field_id",
                                   side_effect=lambda _dex, index: field_refs[index]):
                            with patch("audit_native_selected_item_handoff.trace_identity_method",
                                       side_effect=fake_trace) as trace:
                                result = inspect_exact_playlist_runner_construction(
                                    [apk], class_profiles
                                )

        self.assertTrue(result["run_method_found"])
        self.assertEqual(result["run_field_read_count"], 4)
        self.assertTrue(result["unique_list_field"])
        self.assertTrue(result["unique_callback_field"])
        self.assertEqual(result["run_field_type_counts"]["Lek6;"], 1)
        self.assertEqual(result["constructor_method_count"], 1)
        self.assertEqual(result["constructor_callsite_count"], 1)
        self.assertEqual(result["distinct_constructor_caller_count"], 1)
        self.assertEqual(
            len(result["constructor_traces"][0]["field_writers"]),
            4,
        )
        list_writer = next(
            row for row in result["constructor_traces"][0]["field_writers"]
            if row["field_type"] == "Ljava/util/List;"
        )
        self.assertEqual(
            list_writer["identity_store_events"][0]["origins"],
            ["CALLER_TYPED_PARAMETER"],
        )
        self.assertEqual(trace.call_count, 2)


    def test_exact_li_lb_handoff_scans_unfiltered_callers_and_matches_same_getter_result(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from unittest.mock import patch

        getter_caller = ("LPlainOwner;", "dispatch", "()V")
        constructor_caller = ("LFactory;", "create", "()V")
        mutator = ("LsO7;", "Z", "(ILOf6;)V")
        unrelated_mutator = ("LBs4;", "V", "(LOf6;)V")
        constructor_source = {
            "owner": "LOf6;", "method": "new",
            "signature": "(Landroid/net/Uri;)LOf6;", "ordinal": 3,
        }
        getter_source = {
            "owner": "LiLb;", "method": "for",
            "signature": "()LOf6;", "ordinal": 10,
        }

        class FakeDex:
            def __init__(self, _data):
                self.methods = {
                    1: LI_LB_GETTER_TARGET,
                    2: LI_LB_CONSTRUCTOR_TARGET,
                    3: mutator,
                    4: unrelated_mutator,
                }
            def method(self, index):
                return self.methods[index]

        def fake_instructions(_dex, code_off):
            if code_off == 100:
                return [
                    (10, 0x6e, [0x006e, 1]),
                    (20, 0x6e, [0x006e, 3]),
                    (30, 0x72, [0x0072, 4]),
                ]
            if code_off == 200:
                return [(7, 0x70, [0x0070, 2])]
            return []

        def provenance_event(ordinal, target, arguments):
            return {
                "ordinal": ordinal,
                "kind": "CALL_ARGUMENT_PROVENANCE",
                "callee": {
                    "owner": target[0], "method": target[1],
                    "signature": target[2],
                },
                "reference_arguments": arguments,
            }

        def fake_trace(_dex, method, _flags, _code_off, **_kwargs):
            if method == getter_caller:
                return {
                    "events": [
                        provenance_event(10, LI_LB_GETTER_TARGET, [{
                            "argument_position": 0,
                            "declared_argument_type": "LiLb;",
                            "identity_origins": [{
                                "identity_type": "EXTRA_OBJECT:LiLb;",
                                "origins": ["CALLER_TYPED_PARAMETER"],
                            }],
                            "producer": None,
                            "register_is_this": False,
                        }]),
                        provenance_event(20, mutator, [{
                            "argument_position": 2,
                            "declared_argument_type": "LOf6;",
                            "identity_origins": [{
                                "identity_type": "EXTRA_OBJECT:LOf6;",
                                "origins": ["RETURNED_FROM_METHOD"],
                            }],
                            "producer": getter_source,
                            "register_is_this": False,
                        }]),
                        provenance_event(30, unrelated_mutator, [{
                            "argument_position": 1,
                            "declared_argument_type": "LOf6;",
                            "identity_origins": [{
                                "identity_type": "EXTRA_OBJECT:LOf6;",
                                "origins": ["RETURNED_FROM_METHOD"],
                            }],
                            "producer": constructor_source,
                            "register_is_this": False,
                        }]),
                    ],
                    "branch_seen_aliases_cleared": False,
                }
            if method == constructor_caller:
                return {
                    "events": [
                        provenance_event(7, LI_LB_CONSTRUCTOR_TARGET, [
                            {
                                "argument_position": 0,
                                "declared_argument_type": "LiLb;",
                                "identity_origins": [{
                                    "identity_type": "EXTRA_OBJECT:LiLb;",
                                    "origins": ["NEW_INSTANCE_AT_5"],
                                }],
                                "producer": {"kind": "NEW_INSTANCE", "type": "LiLb;", "ordinal": 5},
                                "register_is_this": False,
                            },
                            {
                                "argument_position": 3,
                                "declared_argument_type": "LOf6;",
                                "identity_origins": [{
                                    "identity_type": "EXTRA_OBJECT:LOf6;",
                                    "origins": ["RETURNED_FROM_METHOD"],
                                }],
                                "producer": constructor_source,
                                "register_is_this": False,
                            },
                        ]),
                    ],
                    "branch_seen_aliases_cleared": False,
                }
            if method == LI_LB_CONSTRUCTOR_TARGET:
                return {
                    "events": [{
                        "kind": "INSTANCE_FIELD_STORE_TYPED_IDENTITY",
                        "identity_type": "EXTRA_OBJECT:LOf6;",
                        "receiver_is_this": True,
                        "origins": ["CALLER_TYPED_PARAMETER"],
                    }]
                }
            if method == LI_LB_GETTER_TARGET:
                return {
                    "events": [
                        {
                            "kind": "FIELD_READ_TYPED_IDENTITY",
                            "identity_type": "EXTRA_OBJECT:LOf6;",
                            "receiver_is_this": True,
                        },
                        {
                            "kind": "RETURN_TYPED_IDENTITY",
                            "identity_type": "EXTRA_OBJECT:LOf6;",
                            "origins": ["FIELD_READ_FROM_THIS"],
                        },
                    ]
                }
            return {"events": []}

        definitions = [
            (getter_caller, 0x8, 100),
            (constructor_caller, 0x8, 200),
            (LI_LB_CONSTRUCTOR_TARGET, 0, 300),
            (LI_LB_GETTER_TARGET, 0, 400),
        ]
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("classes.dex", b"fake-dex")
            with patch("audit_native_selected_item_handoff.Dex", FakeDex), \
                 patch("audit_native_selected_item_handoff.method_definitions_with_flags",
                       return_value=definitions), \
                 patch("audit_native_selected_item_handoff.instructions",
                       side_effect=fake_instructions), \
                 patch("audit_native_selected_item_handoff.trace_identity_method",
                       side_effect=fake_trace) as trace:
                result = inspect_exact_li_lb_handoff_callers([apk])

        self.assertTrue(result["bounded"])
        self.assertTrue(result["complete_for_absence_claim"])
        self.assertEqual(result["direct_constructor_callsite_count"], 1)
        self.assertEqual(result["direct_getter_callsite_count"], 1)
        self.assertEqual(result["distinct_direct_caller_method_count"], 2)
        self.assertEqual(
            {row["caller"]["owner"] for row in result["direct_callers"]},
            {"LPlainOwner;", "LFactory;"},
        )
        self.assertEqual(result["player_mutator_callsite_count_in_direct_callers"], 2)
        self.assertEqual(result["same_media_item_player_mutator_edges"], [{
            "caller": {
                "owner": "LPlainOwner;", "method": "dispatch", "signature": "()V"
            },
            "source_kind": "LI_LB_GETTER_RETURN",
            "source_call_ordinal": 10,
            "mutator_target": {
                "owner": "LsO7;", "method": "Z", "signature": "(ILOf6;)V"
            },
            "mutator_call_ordinal": 20,
            "same_media_item_object_proven": True,
        }])
        self.assertTrue(result["li_lb_constructor_media_item_parameter_stored_on_this"])
        self.assertTrue(result["li_lb_getter_returns_same_media_item_field"])
        self.assertEqual(trace.call_count, 4)

    def test_exact_li_lb_handoff_does_not_match_a_different_media_item_producer(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from unittest.mock import patch

        caller = ("LPlainOwner;", "dispatch", "()V")
        mutator = ("LsO7;", "V", "(LOf6;)V")
        other_source = {
            "owner": "LOf6;", "method": "new",
            "signature": "(Landroid/net/Uri;)LOf6;", "ordinal": 99,
        }
        getter_source = {
            "owner": "LiLb;", "method": "for",
            "signature": "()LOf6;", "ordinal": 10,
        }

        class FakeDex:
            def __init__(self, _data):
                pass
            def method(self, index):
                return {
                    1: LI_LB_GETTER_TARGET,
                    2: mutator,
                }[index]

        def fake_trace(_dex, method, _flags, _code_off, **_kwargs):
            if method == LI_LB_CONSTRUCTOR_TARGET:
                return {"events": [{
                    "kind": "INSTANCE_FIELD_STORE_TYPED_IDENTITY",
                    "identity_type": "EXTRA_OBJECT:LOf6;",
                    "receiver_is_this": True,
                    "origins": ["CALLER_TYPED_PARAMETER"],
                }]}
            if method == LI_LB_GETTER_TARGET:
                return {"events": [
                    {"kind": "FIELD_READ_TYPED_IDENTITY",
                     "identity_type": "EXTRA_OBJECT:LOf6;", "receiver_is_this": True},
                    {"kind": "RETURN_TYPED_IDENTITY",
                     "identity_type": "EXTRA_OBJECT:LOf6;",
                     "origins": ["FIELD_READ_FROM_THIS"]},
                ]}
            if method == caller:
                return {"events": [
                    {
                        "kind": "CALL_ARGUMENT_PROVENANCE", "ordinal": 10,
                        "callee": {
                            "owner": LI_LB_GETTER_TARGET[0],
                            "method": LI_LB_GETTER_TARGET[1],
                            "signature": LI_LB_GETTER_TARGET[2],
                        },
                        "reference_arguments": [{
                            "argument_position": 0,
                            "declared_argument_type": "LiLb;",
                            "identity_origins": [],
                            "producer": None,
                        }],
                    },
                    {
                        "kind": "CALL_ARGUMENT_PROVENANCE", "ordinal": 20,
                        "callee": {
                            "owner": mutator[0], "method": mutator[1],
                            "signature": mutator[2],
                        },
                        "reference_arguments": [{
                            "argument_position": 1,
                            "declared_argument_type": "LOf6;",
                            "identity_origins": [{
                                "identity_type": "EXTRA_OBJECT:LOf6;",
                                "origins": ["RETURNED_FROM_METHOD"],
                            }],
                            "producer": other_source,
                        }],
                    },
                ]}
            return {"events": []}

        def fake_instructions(_dex, code_off):
            if code_off == 100:
                return [
                    (10, 0x6e, [0x006e, 1]),
                    (20, 0x6e, [0x006e, 2]),
                ]
            return []

        definitions = [
            (caller, 0x8, 100),
            (LI_LB_CONSTRUCTOR_TARGET, 0, 300),
            (LI_LB_GETTER_TARGET, 0, 400),
        ]
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("classes.dex", b"fake-dex")
            with patch("audit_native_selected_item_handoff.Dex", FakeDex), \
                 patch("audit_native_selected_item_handoff.method_definitions_with_flags",
                       return_value=definitions), \
                 patch("audit_native_selected_item_handoff.instructions",
                       side_effect=fake_instructions), \
                 patch("audit_native_selected_item_handoff.trace_identity_method",
                       side_effect=fake_trace):
                result = inspect_exact_li_lb_handoff_callers([apk])

        self.assertTrue(result["complete_for_absence_claim"])
        self.assertEqual(result["direct_getter_callsite_count"], 1)
        self.assertEqual(result["player_mutator_callsite_count_in_direct_callers"], 1)
        self.assertEqual(result["same_media_item_player_mutator_edges"], [])
        self.assertFalse(result["same_media_item_to_player_mutator_proven"])


    def test_exact_track_wrapper_handoff_follows_only_same_wrapper_identity(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from unittest.mock import patch

        target = (
            "Lqj8;", "if",
            "(LtCa;ZLqj8$a;LLEa;)Ljava/lang/Object;",
        )
        caller = (
            "LIEa;", "new",
            "(LIEa;Lqj8;LtCa;Lru/yandex/music/data/audio/o;Lnk0;ZLOe2;)Ljava/lang/Object;",
        )
        descriptor = {
            "owner": DESCRIPTOR_BUILDER[0],
            "method": DESCRIPTOR_BUILDER[1],
            "signature": "(LtCa;)Ljava/lang/Object;",
        }

        class FakeDex:
            def __init__(self, data):
                self.data = data
            def method(self, index):
                return {1: target}[index]

        def fake_instructions(_dex, code_off):
            if code_off == 100:
                return [(12, 0x6e, [0x006e, 1])]
            return []

        def fake_trace(_dex, method, _flags, _code_off):
            if method == caller:
                return {
                    "method": {
                        "owner": caller[0], "method": caller[1],
                        "signature": caller[2],
                    },
                    "events": [{
                        "kind": "CALL_WITH_TYPED_IDENTITY",
                        "callee": {
                            "owner": target[0], "method": target[1],
                            "signature": target[2],
                        },
                        "identity_is_common_to_all_incoming_paths": True,
                        "identity_arguments": [{
                            "argument_position": 1,
                            "declared_argument_type": "LtCa;",
                            "identity_type": "TRACK_WRAPPER",
                            "origins": ["TRACK_WRAPPER_PARAMETER"],
                        }],
                    }],
                    "reachable_instruction_count": 90,
                    "branch_count": 12,
                    "path_state_count": 104,
                    "processed_state_count": 104,
                }
            if method == target:
                return {
                    "method": {
                        "owner": target[0], "method": target[1],
                        "signature": target[2],
                    },
                    "events": [
                        {
                            "kind": "CALL_WITH_TYPED_IDENTITY",
                            "callee": descriptor,
                            "identity_is_common_to_all_incoming_paths": True,
                            "identity_arguments": [{
                                "argument_position": 0,
                                "declared_argument_type": "LtCa;",
                                "identity_type": "TRACK_WRAPPER",
                                "origins": ["TRACK_WRAPPER_PARAMETER"],
                            }],
                            "role": "NATIVE_SOURCE_DESCRIPTOR",
                        },
                        {
                            "kind": "CALL_WITH_POSSIBLE_IDENTITY",
                            "callee": {
                                "owner": "LUnknown;", "method": "forward",
                                "signature": "(LtCa;)V",
                            },
                            "identity_is_common_to_all_incoming_paths": False,
                            "possible_identity_arguments": [{
                                "argument_position": 0,
                                "declared_argument_type": "LtCa;",
                                "identity_type": "TRACK_WRAPPER",
                                "possible_origins": ["TRACK_WRAPPER_PARAMETER"],
                            }],
                            "role": "OTHER_METHOD",
                        },
                    ],
                    "reachable_instruction_count": 74,
                    "branch_count": 12,
                    "path_state_count": 104,
                    "processed_state_count": 104,
                }
            raise AssertionError("unexpected trace target")

        definitions = [
            (caller, 0x8, 100),
            (target, 0x8, 200),
        ]
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                for index, name in enumerate((
                    "classes.dex", "classes2.dex", "classes3.dex",
                    "classes4.dex", "classes5.dex", "classes6.dex",
                )):
                    archive.writestr(name, bytes([index]))
            with patch("audit_native_selected_item_handoff.Dex", FakeDex), \
                 patch("audit_native_selected_item_handoff.method_definitions_with_flags",
                       side_effect=lambda dex: definitions if dex.data == bytes([0]) else []), \
                 patch("audit_native_selected_item_handoff.instructions",
                       side_effect=fake_instructions), \
                 patch("audit_native_selected_item_handoff.trace_track_identity_method_cfg",
                       side_effect=fake_trace) as trace:
                result = inspect_exact_track_wrapper_handoff([apk])

        self.assertTrue(result["bounded"])
        self.assertEqual(result["signed_dex_count"], 6)
        self.assertEqual(result["direct_callsite_count"], 1)
        self.assertEqual(result["distinct_direct_caller_count"], 1)
        self.assertTrue(result["same_track_wrapper_to_target_proven"])
        self.assertEqual(len(result["target_typed_wrapper_calls"]), 1)
        self.assertEqual(len(result["target_possible_wrapper_calls"]), 1)
        self.assertTrue(result["same_wrapper_to_native_source_descriptor_proven"])
        self.assertFalse(result["same_wrapper_to_player_api_proven"])
        self.assertTrue(result["complete_for_bounded_direct_caller_claim"])
        self.assertEqual(trace.call_count, 2)

    def test_exact_track_wrapper_handoff_does_not_promote_possible_aliases(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from unittest.mock import patch

        target = (
            "Lqj8;", "if",
            "(LtCa;ZLqj8$a;LLEa;)Ljava/lang/Object;",
        )
        caller = ("LCaller;", "run", "()V")

        class FakeDex:
            def __init__(self, data):
                self.data = data
            def method(self, index):
                return {1: target}[index]

        def fake_trace(_dex, method, _flags, _code_off):
            if method == target:
                return {
                    "method": {"owner": target[0], "method": target[1], "signature": target[2]},
                    "events": [{
                        "kind": "CALL_WITH_POSSIBLE_IDENTITY",
                        "callee": {"owner": "LUnknown;", "method": "forward", "signature": "(LtCa;)V"},
                        "identity_is_common_to_all_incoming_paths": False,
                        "possible_identity_arguments": [{
                            "argument_position": 0,
                            "declared_argument_type": "LtCa;",
                            "identity_type": "TRACK_WRAPPER",
                            "possible_origins": ["TRACK_WRAPPER_PARAMETER"],
                        }],
                        "role": "OTHER_METHOD",
                    }],
                    "reachable_instruction_count": 10,
                    "branch_count": 2,
                    "path_state_count": 4,
                    "processed_state_count": 4,
                }
            return {
                "method": {"owner": caller[0], "method": caller[1], "signature": caller[2]},
                "events": [{
                    "kind": "CALL_WITH_POSSIBLE_IDENTITY",
                    "callee": {"owner": target[0], "method": target[1], "signature": target[2]},
                    "identity_is_common_to_all_incoming_paths": False,
                    "possible_identity_arguments": [{
                        "argument_position": 1,
                        "declared_argument_type": "LtCa;",
                        "identity_type": "TRACK_WRAPPER",
                        "possible_origins": ["TRACK_WRAPPER_PARAMETER"],
                    }],
                }],
                "reachable_instruction_count": 10,
                "branch_count": 2,
                "path_state_count": 4,
                "processed_state_count": 4,
            }

        definitions = [(caller, 0x8, 100), (target, 0x8, 200)]
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                for index, name in enumerate((
                    "classes.dex", "classes2.dex", "classes3.dex",
                    "classes4.dex", "classes5.dex", "classes6.dex",
                )):
                    archive.writestr(name, bytes([index]))
            with patch("audit_native_selected_item_handoff.Dex", FakeDex), \
                 patch("audit_native_selected_item_handoff.method_definitions_with_flags",
                       side_effect=lambda dex: definitions if dex.data == bytes([0]) else []), \
                 patch("audit_native_selected_item_handoff.instructions",
                       return_value=[(3, 0x6e, [0x006e, 1])]), \
                 patch("audit_native_selected_item_handoff.trace_track_identity_method_cfg",
                       side_effect=fake_trace):
                result = inspect_exact_track_wrapper_handoff([apk])

        self.assertFalse(result["same_track_wrapper_to_target_proven"])
        self.assertEqual(result["target_typed_wrapper_calls"], [])
        self.assertEqual(len(result["target_possible_wrapper_calls"]), 1)
        self.assertTrue(result["complete_for_bounded_direct_caller_claim"])



    def test_track_identity_cfg_supports_exact_extra_service_type_labels(self):
        from unittest.mock import patch

        target = (
            "Lqj8;", "if",
            "(LtCa;ZLqj8$a;LLEa;)Ljava/lang/Object;",
        )
        method = ("LCaller;", "dispatch", "(LtCa;)V")

        class FakeDex:
            def u16(self, offset):
                return {100: 4, 102: 1}[offset]
            def method(self, _index):
                return target
            def descriptor(self, _index):
                return "LImpl;"

        cfg_instructions = [
            (0, 0x22, [0x0222, 2]),  # new-instance v2, LImpl
            (1, 0x72, [0x0072, 0]),  # invoke-interface {v2, v3, ...}
            (2, 0x0e, [0x000e]),
        ]
        cfg = {
            "instructions": cfg_instructions,
            "by_pc": {pc: (op, words) for pc, op, words in cfg_instructions},
            "successors": {0: [1], 1: [2], 2: []},
            "reachable": {0, 1, 2},
            "branches": [],
            "entry": 0,
        }
        with patch("audit_native_selected_item_handoff.build_dex_control_flow",
                   return_value=cfg), \
             patch("audit_native_selected_item_handoff.typed_parameter_registers",
                   side_effect=lambda _d, _m, _f, _c, typ: [3] if typ == WRAPPER else []), \
             patch("audit_native_selected_item_handoff.invoke_registers",
                   return_value=[2, 3, 4, 5, 6]), \
             patch("audit_native_selected_item_handoff.expand_invoke_register_types",
                   return_value=["Lqj8;", "LtCa;", "Z", "Lqj8$a;", "LLEa;"]):
            trace = trace_track_identity_method_cfg(
                FakeDex(), method, 0x8, 100,
                extra_identity_types={
                    "Lqj8;": "LQJ8_SERVICE",
                    "LImpl;": "LQJ8_SERVICE",
                },
            )

        event = next(
            row for row in trace["events"]
            if row["kind"] == "CALL_WITH_TYPED_IDENTITY"
        )
        self.assertEqual(len(event["identity_arguments"]), 2)
        self.assertEqual(
            [(arg["argument_position"], arg["identity_type"], arg["origins"])
             for arg in event["identity_arguments"]],
            [
                (0, "LQJ8_SERVICE", ["LQJ8_SERVICE_NEW_INSTANCE"]),
                (1, "TRACK_WRAPPER", ["TRACK_WRAPPER_PARAMETER"]),
            ],
        )

    def test_exact_lqj8_service_route_traces_only_exact_interface_and_entry(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from unittest.mock import patch

        liea = (
            "LIEa;", "new",
            "(LIEa;Lqj8;LtCa;Lru/yandex/music/data/audio/o;Lnk0;ZLOe2;)Ljava/lang/Object;",
        )
        interface_target = (
            "Lqj8;", "if",
            "(LtCa;ZLqj8$a;LLEa;)Ljava/lang/Object;",
        )
        caller = ("LKEa;", "invokeSuspend", "(Ljava/lang/Object;)Ljava/lang/Object;")
        implementation = ("LImpl;", "if", interface_target[2])
        descriptor = {
            "owner": DESCRIPTOR_BUILDER[0],
            "method": DESCRIPTOR_BUILDER[1],
            "signature": "(LtCa;)Ljava/lang/Object;",
        }

        class FakeDex:
            def __init__(self, data):
                self.data = data
            def method(self, index):
                return {1: liea}[index]

        def fake_instructions(_dex, code_off):
            if code_off == 100:
                return [(86, 0x71, [0x0071, 1])]
            return []

        def typed_event(target, args, pc=86, role="OTHER_METHOD"):
            return {
                "kind": "CALL_WITH_TYPED_IDENTITY",
                "callee": {
                    "owner": target[0], "method": target[1],
                    "signature": target[2],
                },
                "identity_is_common_to_all_incoming_paths": True,
                "identity_arguments": args,
                "pc": pc,
                "role": role,
            }

        def fake_trace(_dex, method, _flags, _code_off, **_kwargs):
            if method == caller:
                return {
                    "events": [typed_event(liea, [
                        {"argument_position": 1, "declared_argument_type": "Lqj8;",
                         "identity_type": "LQJ8_SERVICE",
                         "origins": ["LQJ8_SERVICE_FROM_THIS_FIELD"]},
                        {"argument_position": 2, "declared_argument_type": "LtCa;",
                         "identity_type": "TRACK_WRAPPER",
                         "origins": ["TRACK_WRAPPER_FROM_THIS_FIELD"]},
                    ])],
                    "reachable_instruction_count": 72,
                    "branch_count": 11,
                    "path_state_count": 96,
                    "processed_state_count": 96,
                }
            if method == liea:
                return {
                    "events": [typed_event(interface_target, [
                        {"argument_position": 0, "declared_argument_type": "Lqj8;",
                         "identity_type": "LQJ8_SERVICE",
                         "origins": ["LQJ8_SERVICE_PARAMETER"]},
                        {"argument_position": 1, "declared_argument_type": "LtCa;",
                         "identity_type": "TRACK_WRAPPER",
                         "origins": ["TRACK_WRAPPER_PARAMETER"]},
                    ])],
                    "reachable_instruction_count": 74,
                    "branch_count": 12,
                    "path_state_count": 104,
                    "processed_state_count": 104,
                }
            if method == implementation:
                return {
                    "events": [typed_event(descriptor, [
                        {"argument_position": 0, "declared_argument_type": "LtCa;",
                         "identity_type": "TRACK_WRAPPER",
                         "origins": ["TRACK_WRAPPER_PARAMETER"]},
                    ], pc=40, role="NATIVE_SOURCE_DESCRIPTOR")],
                    "reachable_instruction_count": 45,
                    "branch_count": 5,
                    "path_state_count": 32,
                    "processed_state_count": 32,
                }
            raise AssertionError("unexpected trace target")

        definitions = [
            (caller, 0x8, 100),
            (liea, 0x8, 200),
            (implementation, 0x1, 300),
        ]
        class_profiles = {
            "Lqj8;": {
                "is_interface": True, "is_abstract": True,
                "superclass": None, "interfaces": set(),
                "instance_types": set(), "static_types": set(),
            },
            "LImpl;": {
                "is_interface": False, "is_abstract": False,
                "superclass": "Ljava/lang/Object;", "interfaces": {"Lqj8;"},
                "instance_types": set(), "static_types": set(),
            },
        }
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                for index, name in enumerate((
                    "classes.dex", "classes2.dex", "classes3.dex",
                    "classes4.dex", "classes5.dex", "classes6.dex",
                )):
                    archive.writestr(name, bytes([index]))
            with patch("audit_native_selected_item_handoff.Dex", FakeDex), \
                 patch("audit_native_selected_item_handoff.method_definitions_with_flags",
                       side_effect=lambda dex: definitions if dex.data == bytes([0]) else []), \
                 patch("audit_native_selected_item_handoff.instructions",
                       side_effect=fake_instructions), \
                 patch("audit_native_selected_item_handoff.trace_track_identity_method_cfg",
                       side_effect=fake_trace) as trace:
                result = inspect_exact_lqj8_service_route([apk], class_profiles)

        self.assertTrue(result["bounded"])
        self.assertEqual(result["signed_dex_count"], 6)
        self.assertTrue(result["interface_owner_profile"]["is_interface"])
        self.assertEqual(result["interface_owner_profile"]["direct_implementer_count"], 1)
        self.assertEqual(result["liea_entry_direct_callsite_count"], 1)
        self.assertTrue(result["same_service_object_to_liea_entry_proven"])
        self.assertTrue(result["same_service_object_to_interface_invoke_proven"])
        self.assertTrue(result["same_wrapper_to_interface_invoke_proven"])
        self.assertEqual(result["interface_implementation_method_count"], 1)
        self.assertTrue(result["same_wrapper_to_native_source_descriptor_proven"])
        self.assertTrue(result["complete_for_bounded_interface_route_claim"])
        self.assertEqual(trace.call_count, 3)



if __name__ == "__main__":
    unittest.main()
