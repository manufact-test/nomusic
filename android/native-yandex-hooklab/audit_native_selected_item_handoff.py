#!/usr/bin/env python3
"""Read-only signed-Dex audit of native selected-item identity handoff.

Finds exact model fields/accessors and bounded same-basic-block object flow
from that model to native source descriptor/player APIs. This is static code
evidence only: it never reads account data, media, URLs, or a live player.
The publisher-signed APK is downloaded and inspected only in ephemeral CI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys_path = HERE.parents[1] / "tools" / "android-native-gate1"
import sys
sys.path.insert(0, str(sys_path))
sys.path.insert(0, str(HERE / "ci"))

from inspect_android_host import Dex, DexError, DEX_MAX
from uptodown_2025_gpr_ephemeral_verify import (
    unbundle_candidate, verify_split_set
)
from trace_native_callers import uleb, INVOKES
from audit_native_register_bridge import (
    instructions, invoke_registers, move_object_registers
)
PINNED_XAPK_BYTES = 45961661
PINNED_XAPK_SHA256 = "8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053"
PUBLISHER_VERSION = "2025.10.4 #120.1gpr"

MODEL = "Lru/yandex/music/data/audio/o;"
ALBUM_MODEL = "Lru/yandex/music/data/audio/Album;"
WRAPPER = "LtCa;"
DESCRIPTOR_BUILDER = (
    "Lcom/yandex/music/shared/player/download2/o;", "while"
)
PLAYER_OWNERS = {
    "Landroidx/media3/common/Player;",
    "Landroidx/media3/exoplayer/ExoPlayer;",
    "Lcom/google/android/exoplayer2/Player;",
    "Lcom/google/android/exoplayer2/ExoPlayer;",
}
PLAYER_METHODS = {
    "setMediaItem", "setMediaItems", "setMediaSource", "setMediaSources",
    "prepare", "getCurrentMediaItem", "getCurrentTimeline",
    "getCurrentMediaItemIndex", "getCurrentWindowIndex",
    "addMediaItem", "addMediaItems", "replaceMediaItem",
    "removeMediaItem", "clearMediaItems", "seekTo", "play", "pause",
}
MEDIA_SESSION_OWNER = "Landroid/media/session/MediaSession;"
MEDIA_SESSION_METADATA_METHODS = frozenset({"setMetadata"})
MEDIA_SESSION_STATE_METHODS = frozenset({
    "setPlaybackState", "setQueue", "setQueueTitle", "setActive"
})
DECODER_BOUNDARY_METHODS = {
    "Landroid/media/MediaExtractor;": frozenset({
        "setDataSource", "readSampleData", "advance", "selectTrack",
        "getTrackCount", "getTrackFormat"
    }),
    "Landroid/media/MediaCodec;": frozenset({
        "configure", "start", "queueInputBuffer", "queueSecureInputBuffer",
        "releaseOutputBuffer"
    }),
    "Landroid/media/AudioTrack;": frozenset({"write", "play", "pause"}),
    "Landroid/media/MediaPlayer;": frozenset({
        "setDataSource", "prepare", "prepareAsync", "start"
    }),
}
EDITION_MARKERS = frozenset({"edition", "editionid", "edition_id"})
GENERATION_MARKERS = frozenset({
    "generation", "playbackgeneration", "playback_generation",
    "queuegeneration", "queue_generation"
})
SEMANTIC_IDENTITY_MARKERS = EDITION_MARKERS | GENERATION_MARKERS


def classify_boundary_call(callee):
    """Return only a fixed public boundary category; never inspect arguments."""
    if callee[0] == MEDIA_SESSION_OWNER:
        if callee[1] in MEDIA_SESSION_METADATA_METHODS:
            return "MEDIA_SESSION_METADATA"
        if callee[1] in MEDIA_SESSION_STATE_METHODS:
            return "MEDIA_SESSION_STATE"
    if (callee[0] in DECODER_BOUNDARY_METHODS
            and callee[1] in DECODER_BOUNDARY_METHODS[callee[0]]):
        return "DECODER_BOUNDARY"
    return None


def boundary_callsite_census(dex, method, flags, code_off, ins=None):
    """Count typed Track/Album state projections before exact public callsites.

    This is method-local structure only. It never reads a field value and does
    not infer branch, coroutine, virtual receiver, or runtime selection.
    """
    if ins is None:
        ins = list(instructions(dex, code_off))
    params = parse_types(method[2])
    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        raise DexError("BOUNDARY_CALLSITE_INS_SIZE")
    this_register = None if (flags & ACC_STATIC) else registers_size - ins_size
    has_track_parameter = MODEL in params
    has_album_parameter = ALBUM_MODEL in params
    track_field_reads = 0
    album_field_reads = 0
    track_field_read_on_this = False
    album_field_read_on_this = False
    numeric_field_read_on_this = False
    track_model_method_call = False
    album_model_method_call = False
    track_returning_method_call = False
    album_returning_method_call = False
    rows = []
    for ordinal, (_pc, op, words) in enumerate(ins):
        if 0x52 <= op <= 0x58:
            owner, _name, typ = field_id(dex, words[1])
            receiver = (words[0] >> 12) & 15
            if typ == MODEL:
                track_field_reads += 1
                if receiver == this_register:
                    track_field_read_on_this = True
            elif typ == ALBUM_MODEL:
                album_field_reads += 1
                if receiver == this_register:
                    album_field_read_on_this = True
            elif typ in ("I", "J") and receiver == this_register:
                numeric_field_read_on_this = True
        if op not in INVOKES:
            continue
        callee = dex.method(words[1])
        kind = classify_boundary_call(callee)
        if kind:
            rows.append({
                "kind": kind,
                "caller_key": method,
                "target_key": callee,
                "ordinal": ordinal,
                "track_parameter_present": has_track_parameter,
                "album_parameter_present": has_album_parameter,
                "track_field_reads_before": track_field_reads,
                "album_field_reads_before": album_field_reads,
                "track_field_read_on_this_before": track_field_read_on_this,
                "album_field_read_on_this_before": album_field_read_on_this,
                "numeric_field_read_on_this_before": numeric_field_read_on_this,
                "track_model_method_call_before": track_model_method_call,
                "album_model_method_call_before": album_model_method_call,
                "track_returning_method_call_before": track_returning_method_call,
                "album_returning_method_call_before": album_returning_method_call,
            })
        return_type = callee[2].split(")", 1)[1]
        if return_type == MODEL:
            track_returning_method_call = True
        elif return_type == ALBUM_MODEL:
            album_returning_method_call = True
        if callee[0] == MODEL:
            track_model_method_call = True
        elif callee[0] == ALBUM_MODEL:
            album_model_method_call = True
    return rows


def declared_field_inventory(dex: Dex):
    """Read declared field *types* and class relations; never read field values."""
    profiles = {}
    for class_index in range(dex.class_count):
        base = dex.class_offset + class_index * 32
        owner = dex.descriptor(dex.u32(base))
        data_off = dex.u32(base + 24)
        static_types = []
        instance_types = []
        if data_off:
            static_fields, pos = uleb(dex, data_off)
            instance_fields, pos = uleb(dex, pos)
            direct_methods, pos = uleb(dex, pos)
            virtual_methods, pos = uleb(dex, pos)
            if max(static_fields, instance_fields, direct_methods, virtual_methods) > 100000:
                raise ValueError("CLASS_FIELD_INVENTORY_LIMIT")
            for count, target in ((static_fields, static_types),
                                  (instance_fields, instance_types)):
                previous = 0
                for _ in range(count):
                    delta, pos = uleb(dex, pos)
                    previous += delta
                    _access_flags, pos = uleb(dex, pos)
                    field_owner, _field_name, field_type = field_id(dex, previous)
                    if field_owner != owner:
                        raise DexError("FIELD_INVENTORY_OWNER_MISMATCH")
                    target.append(field_type)
        superclass_index = dex.u32(base + 8)
        superclass = (
            None if superclass_index == 0xffffffff
            else dex.descriptor(superclass_index)
        )
        interfaces = set()
        interfaces_off = dex.u32(base + 12)
        if interfaces_off:
            interface_count = dex.u32(interfaces_off)
            if interface_count > 256:
                raise ValueError("CLASS_INTERFACE_LIMIT")
            for index in range(interface_count):
                interfaces.add(dex.descriptor(dex.u16(interfaces_off + 4 + index * 2)))
        profiles[owner] = {
            "static_types": set(static_types),
            "instance_types": set(instance_types),
            "superclass": superclass,
            "interfaces": interfaces,
        }
    return profiles


def classify_track_owner_profile(profile):
    instance = set(profile.get("instance_types", ()))
    interfaces = set(profile.get("interfaces", ()))
    superclass = profile.get("superclass")
    all_types = instance | set(profile.get("static_types", ()))
    collection_types = {
        "Ljava/util/List;", "Ljava/util/Collection;", "Ljava/util/Set;",
        "Ljava/util/Queue;", "Ljava/util/Deque;", "Ljava/util/Map;",
        "Ljava/util/ArrayList;", "Ljava/util/LinkedList;"
    }
    lowered_types = [typ.lower() for typ in all_types]
    source_like = any(
        "datasource" in typ or "mediasource" in typ or "/source/" in typ
        for typ in lowered_types
    )
    has_media_item = any(
        "mediaitem" in typ or "playeritem" in typ
        or "trackitem" in typ or "queueitem" in typ
        for typ in lowered_types
    )
    has_media_source = any("mediasource" in typ for typ in lowered_types)
    has_media_metadata = any("mediametadata" in typ for typ in lowered_types)
    has_playback_state = any("playbackstate" in typ for typ in lowered_types)
    has_audio_track = any("audiotrack" in typ for typ in lowered_types)
    has_media_codec = any("mediacodec" in typ for typ in lowered_types)
    has_media_extractor = any("mediaextractor" in typ for typ in lowered_types)
    return {
        "has_track_field": MODEL in instance,
        "has_album_field": ALBUM_MODEL in instance,
        "has_wrapper_field": WRAPPER in instance,
        "has_numeric_field": bool(all_types & {
            "I", "J", "Ljava/lang/Integer;", "Ljava/lang/Long;"
        }),
        "has_collection_field": any(
            typ in collection_types or typ.startswith("[")
            for typ in all_types
        ),
        "has_player_api_field": bool(all_types & PLAYER_OWNERS),
        "implements_player_api": bool(
            interfaces & PLAYER_OWNERS or superclass in PLAYER_OWNERS
        ),
        "has_media_session_field": MEDIA_SESSION_OWNER in all_types,
        "has_media_item_field": has_media_item,
        "has_media_source_field": has_media_source,
        "has_media_metadata_field": has_media_metadata,
        "has_playback_state_field": has_playback_state,
        "has_audio_track_field": has_audio_track,
        "has_media_codec_field": has_media_codec,
        "has_media_extractor_field": has_media_extractor,
        "has_decoder_field": (
            any(typ in DECODER_BOUNDARY_METHODS for typ in all_types)
            or has_audio_track or has_media_codec or has_media_extractor
        ),
        "has_source_like_field": source_like,
        "has_kotlin_flow_field": any(
            typ.startswith("Lkotlinx/coroutines/flow/") for typ in all_types
        ),
    }


def summarize_track_field_owner_inventory(class_profiles):
    classified = [
        classify_track_owner_profile(profile)
        for profile in class_profiles.values()
    ]
    track = [profile for profile in classified if profile["has_track_field"]]
    album = [profile for profile in classified if profile["has_album_field"]]
    return {
        "track_instance_field_owner_count": len(track),
        "album_instance_field_owner_count": len(album),
        "track_and_album_same_owner_count": sum(
            p["has_track_field"] and p["has_album_field"] for p in classified
        ),
        "track_and_wrapper_same_owner_count": sum(
            p["has_track_field"] and p["has_wrapper_field"] for p in classified
        ),
        "track_owner_with_numeric_field_count": sum(p["has_numeric_field"] for p in track),
        "track_owner_with_collection_field_count": sum(p["has_collection_field"] for p in track),
        "track_owner_with_player_api_field_count": sum(p["has_player_api_field"] for p in track),
        "track_owner_implements_player_api_count": sum(p["implements_player_api"] for p in track),
        "track_owner_with_media_session_field_count": sum(p["has_media_session_field"] for p in track),
        "track_owner_with_decoder_field_count": sum(p["has_decoder_field"] for p in track),
        "track_owner_with_media_item_field_count": sum(p["has_media_item_field"] for p in track),
        "track_owner_with_media_source_field_count": sum(p["has_media_source_field"] for p in track),
        "track_owner_with_media_metadata_field_count": sum(p["has_media_metadata_field"] for p in track),
        "track_owner_with_playback_state_field_count": sum(p["has_playback_state_field"] for p in track),
        "track_owner_with_source_like_field_count": sum(p["has_source_like_field"] for p in track),
        "track_owner_with_kotlin_flow_field_count": sum(p["has_kotlin_flow_field"] for p in track),
        "album_owner_with_numeric_field_count": sum(p["has_numeric_field"] for p in album),
        "album_owner_with_collection_field_count": sum(p["has_collection_field"] for p in album),
    }


def candidate_owner_descriptors(class_profiles):
    """Return only Track+Album / Track+wrapper class owners, with type shape."""
    rows = []
    for owner, profile in sorted(class_profiles.items()):
        shape = classify_track_owner_profile(profile)
        if not shape["has_track_field"] or not (
            shape["has_album_field"] or shape["has_wrapper_field"]
        ):
            continue
        rows.append({
            "owner": owner,
            "has_album_field": shape["has_album_field"],
            "has_wrapper_field": shape["has_wrapper_field"],
            "has_collection_field": shape["has_collection_field"],
            "has_numeric_field": shape["has_numeric_field"],
            "has_player_api_field": shape["has_player_api_field"],
            "implements_player_api": shape["implements_player_api"],
            "has_source_like_field": shape["has_source_like_field"],
            "has_media_item_field": shape["has_media_item_field"],
            "has_media_source_field": shape["has_media_source_field"],
            "has_media_metadata_field": shape["has_media_metadata_field"],
            "has_playback_state_field": shape["has_playback_state_field"],
            "has_decoder_field": shape["has_decoder_field"],
            "instance_field_type_count": len(profile.get("instance_types", ())),
        })
    if len(rows) > 32:
        raise ValueError("TRACK_SHARED_OWNER_CANDIDATE_LIMIT")
    return rows


def typed_parameter_registers(dex, method, flags, code_off, target_type):
    """Return exact registers for a typed receiver/parameter, no values."""
    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        raise DexError("TYPED_PARAMETER_INS_SIZE")
    register = registers_size - ins_size
    found = set()
    if not (flags & ACC_STATIC):
        if method[0] == target_type:
            found.add(register)
        register += 1
    for typ in parse_types(method[2]):
        if typ == target_type:
            found.add(register)
        register += 2 if typ in ("J", "D") else 1
    return found


def inspect_candidate_owner_methods(apks, candidate_owners, class_profiles):
    """Inspect one bounded method/caller edge for shared Track owner classes.

    Only signatures, type descriptors, invoke categories and typed field
    projections are counted. No field values, strings, URLs, media or account
    state are read or emitted.
    """
    summaries = {
        owner: {
            "defined_method_count": 0,
            "methods_accepting_track": 0,
            "methods_accepting_album": 0,
            "methods_accepting_wrapper": 0,
            "methods_returning_track": 0,
            "methods_returning_album": 0,
            "methods_returning_wrapper": 0,
            "methods_with_track_field_read_on_this": 0,
            "methods_with_album_field_read_on_this": 0,
            "methods_with_wrapper_field_read_on_this": 0,
            "methods_calling_track_model": 0,
            "methods_calling_album_model": 0,
            "methods_calling_player_api": 0,
            "methods_calling_media_session": 0,
            "methods_calling_decoder_boundary": 0,
            "methods_calling_source_descriptor": 0,
            "methods_calling_flow_collect_or_emit": 0,
            "method_names_disclosed": False,
        }
        for owner in sorted(candidate_owners)
    }
    inbound = {
        owner: {
            "call_site_count": 0,
            "distinct_caller_method_count": 0,
            "caller_accepts_track_parameter_call_site_count": 0,
            "caller_accepts_album_parameter_call_site_count": 0,
            "caller_accepts_wrapper_parameter_call_site_count": 0,
            "target_accepts_track_parameter_call_site_count": 0,
            "target_accepts_album_parameter_call_site_count": 0,
            "target_accepts_wrapper_parameter_call_site_count": 0,
            "same_track_parameter_alias_to_target_track_parameter_count": 0,
            "same_track_field_alias_to_target_track_parameter_count": 0,
            "same_album_parameter_alias_to_target_album_parameter_count": 0,
            "same_album_field_alias_to_target_album_parameter_count": 0,
            "same_wrapper_parameter_alias_to_target_wrapper_parameter_count": 0,
            "same_wrapper_field_alias_to_target_wrapper_parameter_count": 0,
            "caller_owner_has_track_field_call_site_count": 0,
            "caller_owner_has_album_field_call_site_count": 0,
            "caller_owner_has_wrapper_field_call_site_count": 0,
            "caller_owner_has_collection_field_call_site_count": 0,
            "caller_owner_has_numeric_field_call_site_count": 0,
            "caller_owner_has_player_api_field_call_site_count": 0,
            "caller_owner_implements_player_api_call_site_count": 0,
            "caller_owner_has_media_session_field_call_site_count": 0,
            "caller_owner_has_decoder_field_call_site_count": 0,
            "caller_owner_has_source_like_field_call_site_count": 0,
            "caller_owner_has_kotlin_flow_field_call_site_count": 0,
            "caller_method_keys": set(),
        }
        for owner in sorted(candidate_owners)
    }
    candidate_method_evidence = []
    identity_link_sites = []
    track_return_call_sites = []
    if not candidate_owners:
        return {
            "candidate_owners": [],
            "owner_method_summary": [],
            "inbound_call_census": [],
            "candidate_method_evidence": [],
            "identity_link_sites": [],
            "track_return_call_sites": [],
        }
    if len(candidate_owners) > 32:
        raise ValueError("TRACK_SHARED_OWNER_METHOD_LIMIT")
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("TRACK_SHARED_OWNER_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                for method, flags, code_off in method_definitions_with_flags(dex):
                    ins = list(instructions(dex, code_off))
                    owner = method[0]
                    if owner in candidate_owners:
                        summary = summaries[owner]
                        summary["defined_method_count"] += 1
                        params = parse_types(method[2])
                        result_type = method[2].split(")", 1)[1]
                        summary["methods_accepting_track"] += MODEL in params
                        summary["methods_accepting_album"] += ALBUM_MODEL in params
                        summary["methods_accepting_wrapper"] += WRAPPER in params
                        summary["methods_returning_track"] += result_type == MODEL
                        summary["methods_returning_album"] += result_type == ALBUM_MODEL
                        summary["methods_returning_wrapper"] += result_type == WRAPPER
                        this_register = (
                            None if flags & ACC_STATIC
                            else dex.u16(code_off) - dex.u16(code_off + 2)
                        )
                        method_roles = set()
                        for _ordinal, op, words in ins:
                            if op == 0x54:  # iget-object: inspect only the declared type
                                _field_owner, _field_name, field_type = field_id(dex, words[1])
                                receiver = (words[0] >> 12) & 15
                                if receiver == this_register:
                                    if field_type == MODEL:
                                        method_roles.add("read_track_field")
                                    elif field_type == ALBUM_MODEL:
                                        method_roles.add("read_album_field")
                                    elif field_type == WRAPPER:
                                        method_roles.add("read_wrapper_field")
                            if op not in INVOKES:
                                continue
                            callee = dex.method(words[1])
                            if callee[0] == MODEL:
                                method_roles.add("track_model")
                            elif callee[0] == ALBUM_MODEL:
                                method_roles.add("album_model")
                            if callee[0] in PLAYER_OWNERS and callee[1] in PLAYER_METHODS:
                                method_roles.add("player")
                            boundary = classify_boundary_call(callee)
                            if boundary in ("MEDIA_SESSION_METADATA", "MEDIA_SESSION_STATE"):
                                method_roles.add("media_session")
                            elif boundary == "DECODER_BOUNDARY":
                                method_roles.add("decoder")
                            if (callee[0], callee[1]) == DESCRIPTOR_BUILDER:
                                method_roles.add("source_descriptor")
                            if callee[1] in ("collect", "collectLatest", "launchIn", "emit"):
                                method_roles.add("flow")
                        role_keys = {
                            "read_track_field": "methods_with_track_field_read_on_this",
                            "read_album_field": "methods_with_album_field_read_on_this",
                            "read_wrapper_field": "methods_with_wrapper_field_read_on_this",
                            "track_model": "methods_calling_track_model",
                            "album_model": "methods_calling_album_model",
                            "player": "methods_calling_player_api",
                            "media_session": "methods_calling_media_session",
                            "decoder": "methods_calling_decoder_boundary",
                            "source_descriptor": "methods_calling_source_descriptor",
                            "flow": "methods_calling_flow_collect_or_emit",
                        }
                        for role in method_roles:
                            summary[role_keys[role]] += 1
                        if (
                            MODEL in params or ALBUM_MODEL in params or WRAPPER in params
                            or result_type in (MODEL, ALBUM_MODEL, WRAPPER)
                            or method_roles
                        ):
                            if len(candidate_method_evidence) >= 128:
                                raise ValueError("TRACK_SHARED_OWNER_METHOD_EVIDENCE_LIMIT")
                            candidate_method_evidence.append({
                                "owner": owner,
                                "method": method[1],
                                "signature": method[2],
                                "accepts_track": MODEL in params,
                                "accepts_album": ALBUM_MODEL in params,
                                "accepts_wrapper": WRAPPER in params,
                                "returns_track": result_type == MODEL,
                                "returns_album": result_type == ALBUM_MODEL,
                                "returns_wrapper": result_type == WRAPPER,
                                "reads_track_album_wrapper_on_this": sorted(
                                    role for role in method_roles
                                    if role in (
                                        "read_track_field", "read_album_field",
                                        "read_wrapper_field"
                                    )
                                ),
                                "calls": sorted(
                                    role for role in method_roles
                                    if role not in (
                                        "read_track_field", "read_album_field",
                                        "read_wrapper_field"
                                    )
                                ),
                            })

                    # Bounded straight-line aliases from typed parameters and
                    # typed fields on this. Branches clear all provenance.
                    track_param_aliases = typed_parameter_registers(
                        dex, method, flags, code_off, MODEL
                    )
                    album_param_aliases = typed_parameter_registers(
                        dex, method, flags, code_off, ALBUM_MODEL
                    )
                    wrapper_param_aliases = typed_parameter_registers(
                        dex, method, flags, code_off, WRAPPER
                    )
                    track_field_aliases = set()
                    album_field_aliases = set()
                    wrapper_field_aliases = set()
                    caller_profile = classify_track_owner_profile(
                        class_profiles.get(owner, {})
                    )
                    for _ordinal, op, words in ins:
                        if op in INVOKES:
                            callee = dex.method(words[1])
                            target_owner = callee[0]
                            if target_owner in candidate_owners:
                                target_params = parse_types(callee[2])
                                is_static = op in (0x71, 0x77)
                                target_types = expand_invoke_register_types(
                                    target_owner, target_params, is_static
                                )
                                regs = invoke_registers(op, words)
                                row = inbound[target_owner]
                                row["call_site_count"] += 1
                                row["caller_method_keys"].add(method)
                                row["caller_accepts_track_parameter_call_site_count"] += (
                                    MODEL in parse_types(method[2])
                                )
                                row["caller_accepts_album_parameter_call_site_count"] += (
                                    ALBUM_MODEL in parse_types(method[2])
                                )
                                row["caller_accepts_wrapper_parameter_call_site_count"] += (
                                    WRAPPER in parse_types(method[2])
                                )
                                row["target_accepts_track_parameter_call_site_count"] += (
                                    MODEL in target_params
                                )
                                row["target_accepts_album_parameter_call_site_count"] += (
                                    ALBUM_MODEL in target_params
                                )
                                row["target_accepts_wrapper_parameter_call_site_count"] += (
                                    WRAPPER in target_params
                                )
                                row["caller_owner_has_track_field_call_site_count"] += (
                                    caller_profile["has_track_field"]
                                )
                                row["caller_owner_has_album_field_call_site_count"] += (
                                    caller_profile["has_album_field"]
                                )
                                row["caller_owner_has_wrapper_field_call_site_count"] += (
                                    caller_profile["has_wrapper_field"]
                                )
                                row["caller_owner_has_collection_field_call_site_count"] += (
                                    caller_profile["has_collection_field"]
                                )
                                row["caller_owner_has_numeric_field_call_site_count"] += (
                                    caller_profile["has_numeric_field"]
                                )
                                row["caller_owner_has_player_api_field_call_site_count"] += (
                                    caller_profile["has_player_api_field"]
                                )
                                row["caller_owner_implements_player_api_call_site_count"] += (
                                    caller_profile["implements_player_api"]
                                )
                                row["caller_owner_has_media_session_field_call_site_count"] += (
                                    caller_profile["has_media_session_field"]
                                )
                                row["caller_owner_has_decoder_field_call_site_count"] += (
                                    caller_profile["has_decoder_field"]
                                )
                                row["caller_owner_has_source_like_field_call_site_count"] += (
                                    caller_profile["has_source_like_field"]
                                )
                                row["caller_owner_has_kotlin_flow_field_call_site_count"] += (
                                    caller_profile["has_kotlin_flow_field"]
                                )
                                if len(regs) == len(target_types):
                                    identity_origins = []
                                    logical_position = -1
                                    for register_word_position, typ in enumerate(target_types):
                                        if typ is None:
                                            continue
                                        logical_position += 1
                                        register = regs[register_word_position]
                                        if typ == MODEL:
                                            if register in track_param_aliases:
                                                row["same_track_parameter_alias_to_target_track_parameter_count"] += 1
                                                identity_origins.append({
                                                    "argument_position": logical_position,
                                                    "type": "TRACK",
                                                    "origin": "CALLER_TRACK_PARAMETER"
                                                })
                                            if register in track_field_aliases:
                                                row["same_track_field_alias_to_target_track_parameter_count"] += 1
                                                identity_origins.append({
                                                    "argument_position": logical_position,
                                                    "type": "TRACK",
                                                    "origin": "CALLER_TRACK_FIELD_ON_THIS"
                                                })
                                        elif typ == ALBUM_MODEL:
                                            if register in album_param_aliases:
                                                row["same_album_parameter_alias_to_target_album_parameter_count"] += 1
                                                identity_origins.append({
                                                    "argument_position": logical_position,
                                                    "type": "ALBUM",
                                                    "origin": "CALLER_ALBUM_PARAMETER"
                                                })
                                            if register in album_field_aliases:
                                                row["same_album_field_alias_to_target_album_parameter_count"] += 1
                                                identity_origins.append({
                                                    "argument_position": logical_position,
                                                    "type": "ALBUM",
                                                    "origin": "CALLER_ALBUM_FIELD_ON_THIS"
                                                })
                                        elif typ == WRAPPER:
                                            if register in wrapper_param_aliases:
                                                row["same_wrapper_parameter_alias_to_target_wrapper_parameter_count"] += 1
                                                identity_origins.append({
                                                    "argument_position": logical_position,
                                                    "type": "TRACK_WRAPPER",
                                                    "origin": "CALLER_WRAPPER_PARAMETER"
                                                })
                                            if register in wrapper_field_aliases:
                                                row["same_wrapper_field_alias_to_target_wrapper_parameter_count"] += 1
                                                identity_origins.append({
                                                    "argument_position": logical_position,
                                                    "type": "TRACK_WRAPPER",
                                                    "origin": "CALLER_WRAPPER_FIELD_ON_THIS"
                                                })
                                    if identity_origins:
                                        if len(identity_link_sites) >= 128:
                                            raise ValueError("TRACK_SHARED_OWNER_IDENTITY_SITE_LIMIT")
                                        identity_link_sites.append({
                                            "caller": {
                                                "owner": method[0],
                                                "method": method[1],
                                                "signature": method[2]
                                            },
                                            "target": {
                                                "owner": callee[0],
                                                "method": callee[1],
                                                "signature": callee[2]
                                            },
                                            "identity_arguments": identity_origins,
                                            "branch_and_indirect_dispatch_inferred": False
                                        })
                            if (
                                target_owner in candidate_owners
                                and callee[2].split(")", 1)[1] == MODEL
                            ):
                                if len(track_return_call_sites) >= 128:
                                    raise ValueError("TRACK_RETURN_CALLSITE_LIMIT")
                                track_return_call_sites.append({
                                    "caller": {
                                        "owner": method[0],
                                        "method": method[1],
                                        "signature": method[2]
                                    },
                                    "target": {
                                        "owner": callee[0],
                                        "method": callee[1],
                                        "signature": callee[2]
                                    },
                                    "returned_type": "NATIVE_TRACK",
                                    "same_returned_object_to_downstream_not_yet_traced": True
                                })
                            continue
                        if op == 0x54:  # typed iget-object; never inspect its value
                            dest = (words[0] >> 8) & 15
                            receiver = (words[0] >> 12) & 15
                            _field_owner, _field_name, field_type = field_id(dex, words[1])
                            for aliases in (
                                track_param_aliases, album_param_aliases,
                                wrapper_param_aliases, track_field_aliases,
                                album_field_aliases, wrapper_field_aliases
                            ):
                                aliases.discard(dest)
                            this_register = (
                                None if flags & ACC_STATIC
                                else dex.u16(code_off) - dex.u16(code_off + 2)
                            )
                            if receiver == this_register:
                                if field_type == MODEL:
                                    track_field_aliases.add(dest)
                                elif field_type == ALBUM_MODEL:
                                    album_field_aliases.add(dest)
                                elif field_type == WRAPPER:
                                    wrapper_field_aliases.add(dest)
                        elif op in (0x07, 0x08, 0x09):
                            move = move_object_registers(op, words)
                            if move:
                                dest, source = move
                                for aliases in (
                                    track_param_aliases, album_param_aliases,
                                    wrapper_param_aliases, track_field_aliases,
                                    album_field_aliases, wrapper_field_aliases
                                ):
                                    was_alias = source in aliases
                                    aliases.discard(dest)
                                    if was_alias:
                                        aliases.add(dest)
                        elif op == 0x1f:  # check-cast preserves the reference
                            pass
                        else:
                            dest = written_register(op, words)
                            if dest is not None:
                                for aliases in (
                                    track_param_aliases, album_param_aliases,
                                    wrapper_param_aliases, track_field_aliases,
                                    album_field_aliases, wrapper_field_aliases
                                ):
                                    aliases.discard(dest)
                            if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
                                for aliases in (
                                    track_param_aliases, album_param_aliases,
                                    wrapper_param_aliases, track_field_aliases,
                                    album_field_aliases, wrapper_field_aliases
                                ):
                                    aliases.clear()
    for owner, row in inbound.items():
        row["distinct_caller_method_count"] = len(row.pop("caller_method_keys"))
    return {
        "candidate_owners": sorted(candidate_owners),
        "owner_method_summary": [
            {"owner": owner, **summaries[owner]} for owner in sorted(candidate_owners)
        ],
        "inbound_call_census": [
            {"owner": owner, **inbound[owner]} for owner in sorted(candidate_owners)
        ],
        "candidate_method_evidence": candidate_method_evidence,
        "identity_link_sites": identity_link_sites,
        "track_return_call_sites": track_return_call_sites,
        "method_names_disclosed": True,
        "field_names_and_values_disclosed": False,
        "runtime_state_or_media_read": False,
    }

def select_candidate_identity_focus_refs(census):
    refs = set()
    for site in census.get("identity_link_sites", []):
        for side in ("caller", "target"):
            row = site[side]
            refs.add((row["owner"], row["method"], row["signature"]))
    for row in census.get("candidate_method_evidence", []):
        if row["returns_track"] or (
            row["method"] in ("create", "invokeSuspend")
            and row["reads_track_album_wrapper_on_this"]
        ):
            refs.add((row["owner"], row["method"], row["signature"]))
    if len(refs) > 64:
        raise ValueError("TRACK_IDENTITY_FOCUS_METHOD_LIMIT")
    return sorted(refs)


def trace_identity_method(
    dex, method, flags, code_off, candidate_owners=None,
    capture_unproven_calls=False, focus_targets=None
):
    """Trace only typed Track/Album/wrapper aliases and exact focus callsites."""
    candidate_owners = candidate_owners or set()
    focus_targets = set(focus_targets or ())
    tracked_types = {
        MODEL: "TRACK",
        ALBUM_MODEL: "ALBUM",
        WRAPPER: "TRACK_WRAPPER",
    }
    aliases = {
        typ: {
            register: {"CALLER_TYPED_PARAMETER"}
            for register in typed_parameter_registers(
                dex, method, flags, code_off, typ
            )
        }
        for typ in tracked_types
    }
    this_register = (
        None if flags & ACC_STATIC
        else dex.u16(code_off) - dex.u16(code_off + 2)
    )
    events = []
    pending_return_type = None
    branch_seen = False

    def clear_register(register):
        for values in aliases.values():
            values.pop(register, None)

    def add_event(row):
        if len(events) >= 128:
            raise ValueError("TRACK_IDENTITY_METHOD_EVENT_LIMIT")
        events.append(row)

    for ordinal, op, words in instructions(dex, code_off):
        if op in INVOKES:
            callee = dex.method(words[1])
            regs = invoke_registers(op, words)
            params = parse_types(callee[2])
            is_static = op in (0x71, 0x77)
            target_types = expand_invoke_register_types(
                callee[0], params, is_static
            )
            identity_arguments = []
            if len(regs) == len(target_types):
                logical_position = -1
                for register_word_position, (declared_type, register) in enumerate(
                    zip(target_types, regs)
                ):
                    if declared_type is None:
                        continue
                    logical_position += 1
                    for tracked_type, label in tracked_types.items():
                        origins = aliases[tracked_type].get(register)
                        if origins:
                            identity_arguments.append({
                                "argument_position": logical_position,
                                "declared_argument_type": declared_type,
                                "identity_type": label,
                                "origins": sorted(origins),
                            })
            role = None
            if callee in focus_targets:
                role = "AUDIO_OUTPUT_METHOD_DISPATCH"
            elif (callee[0], callee[1]) == DESCRIPTOR_BUILDER:
                role = "NATIVE_SOURCE_DESCRIPTOR"
            elif (callee[0], callee[1]) in SOURCE_METHODS:
                role = "NATIVE_SOURCE_OR_DOWNLOAD_METHOD"
            elif callee[0] in PLAYER_OWNERS and callee[1] in PLAYER_METHODS:
                role = "PLAYER_SELECTION_OR_TRANSPORT"
            else:
                boundary = classify_boundary_call(callee)
                if boundary:
                    role = boundary
                elif callee[0] in candidate_owners:
                    role = "SHARED_TRACK_OWNER_METHOD"
                elif callee[1] in ("collect", "collectLatest", "launchIn", "emit"):
                    role = "FLOW_COLLECT_OR_EMIT"
                elif (
                    callee[0] in {
                        "Ljava/util/List;", "Ljava/util/Collection;",
                        "Ljava/util/Queue;", "Ljava/util/Deque;",
                        "Ljava/util/Set;"
                    }
                    and callee[1] in ("add", "addAll", "offer", "put", "set", "remove")
                ):
                    role = "COLLECTION_MUTATION_CANDIDATE"
            if identity_arguments:
                add_event({
                    "ordinal": ordinal,
                    "kind": "CALL_WITH_TYPED_IDENTITY",
                    "role": role or "OTHER_METHOD",
                    "callee": {
                        "owner": callee[0],
                        "method": callee[1],
                        "signature": callee[2],
                    },
                    "identity_arguments": identity_arguments,
                })
            elif role:
                add_event({
                    "ordinal": ordinal,
                    "kind": "CALL_TARGET_ROLE_WITHOUT_IDENTITY",
                    "role": role,
                    "callee": {
                        "owner": callee[0],
                        "method": callee[1],
                        "signature": callee[2],
                    },
                    "target_accepts_track_parameter": MODEL in params,
                    "target_accepts_album_parameter": ALBUM_MODEL in params,
                    "target_accepts_wrapper_parameter": WRAPPER in params,
                    "identity_proven": False,
                })
            elif capture_unproven_calls:
                add_event({
                    "ordinal": ordinal,
                    "kind": "CALL_TARGET_WITHOUT_IDENTITY",
                    "role": "OTHER_METHOD",
                    "callee": {
                        "owner": callee[0],
                        "method": callee[1],
                        "signature": callee[2],
                    },
                    "target_accepts_track_parameter": MODEL in params,
                    "target_accepts_album_parameter": ALBUM_MODEL in params,
                    "target_accepts_wrapper_parameter": WRAPPER in params,
                    "identity_proven": False,
                })
            result_type = callee[2].split(")", 1)[1]
            pending_return_type = result_type if result_type in tracked_types else None
            continue

        if op == 0x0c:  # move-result-object, only the immediately preceding invoke
            dest = words[0] >> 8
            clear_register(dest)
            if pending_return_type:
                aliases[pending_return_type][dest] = {"RETURNED_FROM_METHOD"}
                add_event({
                    "ordinal": ordinal,
                    "kind": "MOVE_RESULT_TYPED_IDENTITY",
                    "identity_type": tracked_types[pending_return_type],
                })
            pending_return_type = None
            continue

        pending_return_type = None
        if op == 0x54:  # iget-object: inspect type and receiver, never field value
            dest = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            _field_owner, _field_name, field_type = field_id(dex, words[1])
            clear_register(dest)
            if receiver == this_register and field_type in tracked_types:
                aliases[field_type][dest] = {"FIELD_READ_FROM_THIS"}
                add_event({
                    "ordinal": ordinal,
                    "kind": "FIELD_READ_TYPED_IDENTITY",
                    "identity_type": tracked_types[field_type],
                    "receiver_is_this": True,
                })
            continue

        if op == 0x5b:  # iput-object: record type-only storage of a tracked alias
            value_register = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            field_owner, _field_name, field_type = field_id(dex, words[1])
            origins = aliases.get(field_type, {}).get(value_register)
            if origins:
                add_event({
                    "ordinal": ordinal,
                    "kind": "INSTANCE_FIELD_STORE_TYPED_IDENTITY",
                    "identity_type": tracked_types[field_type],
                    "destination_owner": field_owner,
                    "receiver_is_this": receiver == this_register,
                    "origins": sorted(origins),
                })
            continue

        if op == 0x67:  # sput-object
            value_register = words[0] >> 8
            field_owner, _field_name, field_type = field_id(dex, words[1])
            origins = aliases.get(field_type, {}).get(value_register)
            if origins:
                add_event({
                    "ordinal": ordinal,
                    "kind": "STATIC_FIELD_STORE_TYPED_IDENTITY",
                    "identity_type": tracked_types[field_type],
                    "destination_owner": field_owner,
                    "origins": sorted(origins),
                })
            continue

        if op == 0x11:  # return-object: prove exact returned alias, not just signature
            source_register = words[0] >> 8
            for tracked_type, label in tracked_types.items():
                origins = aliases[tracked_type].get(source_register)
                if origins:
                    add_event({
                        "ordinal": ordinal,
                        "kind": "RETURN_TYPED_IDENTITY",
                        "identity_type": label,
                        "origins": sorted(origins),
                    })
            continue

        if op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            if move:
                dest, source = move
                copied = {
                    typ: set(values[source])
                    for typ, values in aliases.items()
                    if source in values
                }
                clear_register(dest)
                for typ, origins in copied.items():
                    aliases[typ][dest] = origins
            continue

        if op == 0x1f:  # check-cast preserves the reference
            continue

        dest = written_register(op, words)
        if dest is not None:
            clear_register(dest)
        if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
            branch_seen = True
            for values in aliases.values():
                values.clear()

    return {
        "method": {
            "owner": method[0],
            "method": method[1],
            "signature": method[2],
        },
        "events": events,
        "branch_seen_aliases_cleared": branch_seen,
        "field_names_or_values_disclosed": False,
        "strings_urls_dataspec_account_or_audio_read": False,
    }


def inspect_candidate_identity_method_traces(
    apks, focus_refs, candidate_owners, require_all=True,
    capture_unproven_calls=False
):
    focus = set(focus_refs)
    traces = []
    found = set()
    if len(focus) > 64:
        raise ValueError("TRACK_IDENTITY_TRACE_METHOD_LIMIT")
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("TRACK_IDENTITY_TRACE_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                for method, flags, code_off in method_definitions_with_flags(dex):
                    if method not in focus:
                        continue
                    found.add(method)
                    traces.append(trace_identity_method(
                        dex, method, flags, code_off, candidate_owners,
                        capture_unproven_calls
                    ))
    missing = sorted(focus - found)
    if missing and require_all:
        raise ValueError("TRACK_IDENTITY_FOCUS_METHODS_NOT_ALL_DEFINED")
    return {"traces": traces, "missing_method_refs": missing}


def select_next_identity_method_refs(traces, already_traced, class_profiles):
    known = set(already_traced)
    refs = set()
    for trace in traces:
        for event in trace.get("events", []):
            if event.get("kind") != "CALL_WITH_TYPED_IDENTITY":
                continue
            if not any(
                arg.get("identity_type") in ("TRACK", "TRACK_WRAPPER", "ALBUM")
                for arg in event.get("identity_arguments", [])
            ):
                continue
            callee = event["callee"]
            target = (callee["owner"], callee["method"], callee["signature"])
            if target in known or callee["owner"] not in class_profiles:
                continue
            if callee["owner"].startswith((
                "Ljava/", "Ljavax/", "Lkotlin/", "Lkotlinx/",
                "Landroid/", "Landroidx/", "Lorg/"
            )):
                continue
            refs.add(target)
    if len(refs) > 64:
        raise ValueError("TRACK_IDENTITY_NEXT_HOP_METHOD_LIMIT")
    return sorted(refs)


def summarize_boundary_callsite_owner_profiles(rows, class_profiles=None):
    class_profiles = class_profiles or {}
    grouped = {}
    for row in rows:
        owner = row["caller_key"][0]
        bucket = grouped.setdefault(row["kind"], {})
        entry = bucket.setdefault(owner, {
            "call_site_count": 0, "methods": set(), "call_sites": []
        })
        entry["call_site_count"] += 1
        entry["methods"].add(row["caller_key"])
        entry["call_sites"].append({
            "caller": {
                "owner": row["caller_key"][0],
                "method": row["caller_key"][1],
                "signature": row["caller_key"][2],
            },
            "target": {
                "owner": row["target_key"][0],
                "method": row["target_key"][1],
                "signature": row["target_key"][2],
            },
            "ordinal": row["ordinal"],
        })
    result = {}
    for kind, owners in grouped.items():
        if len(owners) > 64:
            raise ValueError("BOUNDARY_CALLER_OWNER_LIMIT")
        rows_out = []
        for owner, entry in sorted(owners.items()):
            profile = classify_track_owner_profile(class_profiles.get(owner, {}))
            rows_out.append({
                "owner": owner,
                "call_site_count": entry["call_site_count"],
                "distinct_caller_method_count": len(entry["methods"]),
                "call_sites": entry["call_sites"],
                "has_track_field": profile["has_track_field"],
                "has_album_field": profile["has_album_field"],
                "has_wrapper_field": profile["has_wrapper_field"],
                "has_collection_field": profile["has_collection_field"],
                "has_numeric_field": profile["has_numeric_field"],
                "has_player_api_field": profile["has_player_api_field"],
                "implements_player_api": profile["implements_player_api"],
                "has_media_session_field": profile["has_media_session_field"],
                "has_media_item_field": profile["has_media_item_field"],
                "has_media_source_field": profile["has_media_source_field"],
                "has_media_metadata_field": profile["has_media_metadata_field"],
                "has_playback_state_field": profile["has_playback_state_field"],
                "has_audio_track_field": profile["has_audio_track_field"],
                "has_media_codec_field": profile["has_media_codec_field"],
                "has_media_extractor_field": profile["has_media_extractor_field"],
                "has_decoder_field": profile["has_decoder_field"],
                "has_source_like_field": profile["has_source_like_field"],
                "has_kotlin_flow_field": profile["has_kotlin_flow_field"],
            })
        result[kind] = rows_out
    return result


def summarize_boundary_callsite_census(rows, class_profiles=None):
    class_profiles = class_profiles or {}
    summary = {}
    flags = (
        "track_parameter_present", "album_parameter_present",
        "track_field_read_on_this_before", "album_field_read_on_this_before",
        "numeric_field_read_on_this_before", "track_model_method_call_before",
        "album_model_method_call_before", "track_returning_method_call_before",
        "album_returning_method_call_before"
    )
    owner_flags = (
        "has_track_field", "has_album_field", "has_wrapper_field",
        "has_player_api_field", "implements_player_api",
        "has_media_session_field", "has_media_item_field",
        "has_media_source_field", "has_media_metadata_field",
        "has_playback_state_field", "has_audio_track_field",
        "has_media_codec_field", "has_media_extractor_field",
        "has_decoder_field", "has_source_like_field",
        "has_kotlin_flow_field", "has_collection_field", "has_numeric_field"
    )
    for row in rows:
        bucket = summary.setdefault(row["kind"], {
            "call_site_count": 0,
            "distinct_caller_method_count": 0,
            "track_field_read_before_call_site_count": 0,
            "album_field_read_before_call_site_count": 0,
            **{key + "_call_site_count": 0 for key in flags},
            **{"caller_owner_" + key + "_call_site_count": 0 for key in owner_flags}
        })
        bucket["call_site_count"] += 1
        for key in flags:
            if row[key]:
                bucket[key + "_call_site_count"] += 1
        if row["track_field_reads_before"]:
            bucket["track_field_read_before_call_site_count"] += 1
        if row["album_field_reads_before"]:
            bucket["album_field_read_before_call_site_count"] += 1
        owner_profile = classify_track_owner_profile(
            class_profiles.get(row["caller_key"][0], {})
        )
        for key in owner_flags:
            if owner_profile[key]:
                bucket["caller_owner_" + key + "_call_site_count"] += 1
    for kind, bucket in summary.items():
        bucket["distinct_caller_method_count"] = len({
            row["caller_key"] for row in rows if row["kind"] == kind
        })
    return summary
def method_signature_type_profile(method):
    params = parse_types(method[2])
    result = method[2].split(")", 1)[1]
    lowered_params = [typ.lower() for typ in params]
    lowered_result = result.lower()
    def has_marker(values, markers):
        return any(marker in value for value in values for marker in markers)
    return {
        "accepts_track": MODEL in params,
        "accepts_album": ALBUM_MODEL in params,
        "accepts_track_wrapper": WRAPPER in params,
        "returns_track": result == MODEL,
        "returns_album": result == ALBUM_MODEL,
        "accepts_media_item": has_marker(lowered_params, ("mediaitem", "playeritem", "trackitem", "queueitem")),
        "returns_media_item": has_marker((lowered_result,), ("mediaitem", "playeritem", "trackitem", "queueitem")),
        "accepts_media_source": has_marker(lowered_params, ("mediasource",)),
        "returns_media_source": has_marker((lowered_result,), ("mediasource",)),
        "accepts_media_metadata": has_marker(lowered_params, ("mediametadata",)),
        "returns_media_metadata": has_marker((lowered_result,), ("mediametadata",)),
        "accepts_playback_state": has_marker(lowered_params, ("playbackstate",)),
        "returns_playback_state": has_marker((lowered_result,), ("playbackstate",)),
        "accepts_data_source": has_marker(lowered_params, ("datasource", "mediadatasource")),
        "returns_data_source": has_marker((lowered_result,), ("datasource", "mediadatasource")),
        "accepts_uri": has_marker(lowered_params, ("landroid/net/uri;", "ljava/net/uri;")),
        "returns_uri": has_marker((lowered_result,), ("landroid/net/uri;", "ljava/net/uri;")),
        "accepts_byte_buffer": "ljava/nio/bytebuffer;" in lowered_params,
        "accepts_media_format": has_marker(lowered_params, ("mediaformat",)),
        "accepts_surface": has_marker(lowered_params, ("landroid/view/surface;",)),
    }


def inspect_boundary_caller_inbound_methods(apks, boundary_rows, class_profiles):
    focus = {row["caller_key"] for row in boundary_rows}
    if len(focus) > 64:
        raise ValueError("BOUNDARY_FOCUS_METHOD_LIMIT")
    inbound = []
    caller_methods = set()
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("BOUNDARY_INBOUND_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                for method, _flags, code_off in method_definitions_with_flags(dex):
                    caller_profile = classify_track_owner_profile(
                        class_profiles.get(method[0], {})
                    )
                    caller_signature = method_signature_type_profile(method)
                    for _ordinal, op, words in instructions(dex, code_off):
                        if op not in INVOKES:
                            continue
                        callee = dex.method(words[1])
                        if callee not in focus:
                            continue
                        if len(inbound) >= 256:
                            raise ValueError("BOUNDARY_INBOUND_CALLSITE_LIMIT")
                        caller_methods.add(method)
                        inbound.append({
                            "caller": {
                                "owner": method[0],
                                "method": method[1],
                                "signature": method[2],
                            },
                            "target": {
                                "owner": callee[0],
                                "method": callee[1],
                                "signature": callee[2],
                            },
                            "caller_signature_types": caller_signature,
                            "target_signature_types": method_signature_type_profile(callee),
                            "caller_owner_shape": {
                                key: caller_profile[key] for key in (
                                    "has_track_field", "has_album_field",
                                    "has_wrapper_field", "has_collection_field",
                                    "has_numeric_field", "has_player_api_field",
                                    "implements_player_api", "has_media_session_field",
                                    "has_media_item_field", "has_media_source_field",
                                    "has_media_metadata_field", "has_playback_state_field",
                                    "has_audio_track_field", "has_media_codec_field",
                                    "has_media_extractor_field", "has_decoder_field",
                                    "has_source_like_field", "has_kotlin_flow_field"
                                )
                            },
                        })
    relevant = [
        row for row in inbound
        if (
            row["caller_signature_types"]["accepts_track"]
            or row["caller_signature_types"]["accepts_album"]
            or row["caller_signature_types"]["accepts_track_wrapper"]
            or row["caller_signature_types"]["accepts_media_item"]
            or row["caller_signature_types"]["accepts_media_source"]
            or row["caller_signature_types"]["accepts_data_source"]
            or row["caller_signature_types"]["accepts_uri"]
            or any(row["caller_owner_shape"].values())
        )
    ]
    return {
        "boundary_focus_method_count": len(focus),
        "inbound_callsite_count": len(inbound),
        "distinct_inbound_caller_method_count": len(caller_methods),
        "inbound_callers_with_relevant_typed_state": relevant,
        "inbound_callers_all": inbound,
        "field_values_or_media_values_read": False,
        "urls_dataspec_account_or_audio_read": False,
        "virtual_dispatch_or_branch_inferred": False,
    }


def select_exact_interface_contracts(owner, owner_methods, interfaces, interface_method_refs):
    method_shapes = {(row[1], row[2]) for row in owner_methods}
    return sorted(
        (interface, name, signature)
        for interface in interfaces
        for name, signature in method_shapes
        if (interface, name, signature) in interface_method_refs
    )


def select_audio_output_focus_methods(owner, methods, field_types):
    if (
        "Landroid/media/AudioTrack;" not in set(field_types)
        or owner.startswith("Lru/yandex/speechkit/")
    ):
        return []
    rows = []
    for method in methods:
        params = parse_types(method[2])
        result_type = method[2].split(")", 1)[1]
        reason = None
        if method[1] == "<init>":
            reason = "AUDIO_OUTPUT_CONSTRUCTOR"
        elif "Ljava/nio/ByteBuffer;" in params:
            reason = "AUDIO_BUFFER_ENTRY"
        elif (
            "Landroid/media/AudioTrack;" in params
            or result_type == "Landroid/media/AudioTrack;"
        ):
            reason = "AUDIO_TRACK_FACTORY_OR_ADAPTER"
        if reason:
            rows.append((method, reason))
    return sorted(rows)


def inspect_decoder_owner_dispatch_contracts(apks, boundary_rows, class_profiles):
    owners = sorted({
        row["caller_key"][0]
        for row in boundary_rows if row["kind"] == "DECODER_BOUNDARY"
    })
    if len(owners) > 16:
        raise ValueError("DECODER_OWNER_CONTRACT_LIMIT")
    focus_methods = {owner: set() for owner in owners}
    for row in boundary_rows:
        if row["kind"] == "DECODER_BOUNDARY":
            focus_methods[row["caller_key"][0]].add(row["caller_key"])
    owner_declared_methods = {owner: set() for owner in owners}
    interface_owners = {
        interface
        for owner in owners
        for interface in class_profiles.get(owner, {}).get("interfaces", ())
    }
    if len(interface_owners) > 64:
        raise ValueError("DECODER_INTERFACE_OWNER_LIMIT")
    interface_method_refs = set()
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("DECODER_CONTRACT_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                for method, _flags, _code_off in method_definitions_with_flags(dex):
                    if method[0] in owner_declared_methods:
                        owner_declared_methods[method[0]].add(method)
                        if method in focus_methods[method[0]]:
                            focus_methods[method[0]].add(method)
                for index in range(dex.method_count):
                    method = dex.method(index)
                    if method[0] in interface_owners:
                        interface_method_refs.add(method)
    focus_reasons = {
        owner: {
            method: "DECODER_BOUNDARY" for method in focus_methods[owner]
        }
        for owner in owners
    }
    for owner in owners:
        profile = class_profiles.get(owner, {})
        field_types = set(profile.get("instance_types", ())) | set(
            profile.get("static_types", ())
        )
        for method, reason in select_audio_output_focus_methods(
            owner, owner_declared_methods[owner], field_types
        ):
            focus_methods[owner].add(method)
            focus_reasons[owner][method] = reason
    contracts = {
        owner: select_exact_interface_contracts(
            owner, focus_methods[owner],
            class_profiles.get(owner, {}).get("interfaces", ()),
            interface_method_refs
        )
        for owner in owners
    }
    direct_targets = {
        method for methods in focus_methods.values() for method in methods
    }
    interface_target_owners = {}
    for owner, rows in contracts.items():
        for contract in rows:
            interface_target_owners.setdefault(contract, set()).add(owner)
    incoming = {owner: [] for owner in owners}
    total_callsites = 0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                dex = Dex(archive.read(entry.filename))
                for caller, _flags, code_off in method_definitions_with_flags(dex):
                    for ordinal, op, words in instructions(dex, code_off):
                        if op not in INVOKES:
                            continue
                        target = dex.method(words[1])
                        matched = []
                        if target in direct_targets:
                            matched.append((target[0], "DIRECT_CLASS_METHOD_REFERENCE"))
                        for owner in interface_target_owners.get(target, ()):
                            matched.append((owner, "EXACT_INTERFACE_METHOD_REFERENCE"))
                        for owner, dispatch_kind in matched:
                            total_callsites += 1
                            if total_callsites > 512:
                                raise ValueError("DECODER_OWNER_INBOUND_CALLSITE_LIMIT")
                            incoming[owner].append({
                                "caller": {
                                    "owner": caller[0],
                                    "method": caller[1],
                                    "signature": caller[2],
                                },
                                "target": {
                                    "owner": target[0],
                                    "method": target[1],
                                    "signature": target[2],
                                },
                                "ordinal": ordinal,
                                "dispatch_kind": dispatch_kind,
                            })
    result = []
    for owner in owners:
        profile = class_profiles.get(owner, {})
        field_types = set(profile.get("instance_types", ())) | set(
            profile.get("static_types", ())
        )
        relevant_fields = sorted(
            typ for typ in field_types
            if any(marker in typ.lower() for marker in (
                "audio", "media", "buffer", "format", "surface",
                "track", "album", "data", "source", "codec",
                "extractor", "collection", "list", "queue",
                "byte", "long", "integer"
            ))
        )
        methods = sorted(owner_declared_methods[owner])
        focus = sorted(focus_methods[owner])
        if len(methods) > 64:
            raise ValueError("DECODER_OWNER_METHOD_LIMIT")
        result.append({
            "owner": owner,
            "superclass": profile.get("superclass"),
            "interfaces": sorted(profile.get("interfaces", ())),
            "relevant_declared_field_types": relevant_fields,
            "declared_code_method_count": len(methods),
            "declared_code_methods": [
                {
                    "method": method[1],
                    "signature": method[2],
                    "signature_types": method_signature_type_profile(method),
                }
                for method in methods
            ],
            "dispatch_focus_methods": [
                {
                    "method": method[1],
                    "signature": method[2],
                    "reason": focus_reasons[owner].get(method, "DECODER_BOUNDARY"),
                }
                for method in focus
            ],
            "exact_interface_contracts": [
                {"owner": row[0], "method": row[1], "signature": row[2]}
                for row in contracts[owner]
            ],
            "incoming_callsite_count": len(incoming[owner]),
            "incoming_callsites": incoming[owner],
            "runtime_dispatch_proven": False,
        })
    return {
        "decoder_owner_count": len(owners),
        "owners": result,
        "field_values_or_media_values_read": False,
        "runtime_dispatch_inferred": False,
    }


def trace_byte_buffer_parameter(dex, method, flags, code_off, ins=None, sink_targets=None):
    sink_targets = set(sink_targets or ())
    byte_buffer = "Ljava/nio/ByteBuffer;"
    byte_buffer_array = "[Ljava/nio/ByteBuffer;"
    parameter_registers = typed_parameter_registers(
        dex, method, flags, code_off, byte_buffer
    )
    aliases = {
        register: {"CALLER_TYPED_PARAMETER"}
        for register in parameter_registers
    }
    array_aliases = set()
    events = []
    provenance_events = []
    pending_object_return_kind = None
    pending_object_return_method = None
    branch_seen = False
    backward_branch_aliases_cleared = False
    switch_branch_aliases_cleared = False
    branch_aliases_pruned = False
    branch_preserved_parameter_registers = set()
    if ins is None:
        ins = list(instructions(dex, code_off))
    else:
        ins = list(ins)

    # A parameter alias can safely survive an arbitrary branch only if its
    # original register is never written anywhere in this method. Wide writes
    # also occupy the following register. This deliberately prefers false
    # negatives over path-insensitive identity claims.
    wide_destination_ops = (
        {0x04, 0x05, 0x06, 0x0b, 0x16, 0x17, 0x18, 0x19,
         0x45, 0x53, 0x61, 0x7d, 0x7e, 0x80, 0x82, 0x85, 0x87,
         0x88, 0x8a}
        | set(range(0x9b, 0xa6))
        | set(range(0xab, 0xb0))
        | set(range(0xbb, 0xc6))
        | set(range(0xcb, 0xd0))
    )
    potentially_written_registers = set()
    for _pc, candidate_op, candidate_words in ins:
        candidate_dest = written_register(candidate_op, candidate_words)
        if candidate_dest is not None:
            potentially_written_registers.add(candidate_dest)
            if candidate_op in wide_destination_ops:
                potentially_written_registers.add(candidate_dest + 1)
    stable_parameter_registers = parameter_registers - potentially_written_registers

    for ordinal, op, words in ins:
        if op in INVOKES:
            callee = dex.method(words[1])
            regs = invoke_registers(op, words)
            params = parse_types(callee[2])
            is_static = op in (0x71, 0x77)
            target_types = expand_invoke_register_types(
                callee[0], params, is_static
            )
            if (
                (callee[0] in ("LbJ2;", "Lpk0;") and callee[1] == "native")
                or callee in sink_targets
            ):
                origins = []
                argument_register_map = []
                if len(regs) == len(target_types):
                    logical_position = -1
                    for register_word_position, (typ, register) in enumerate(
                        zip(target_types, regs)
                    ):
                        if typ is None:
                            continue
                        logical_position += 1
                        argument_register_map.append({
                            "argument_position": logical_position,
                            "register_word_position": register_word_position,
                            "type": typ,
                            "register": register,
                        })
                        if typ == byte_buffer and register in aliases:
                            origins.append({
                                "argument_position": logical_position,
                                "origins": sorted(aliases[register]),
                            })
                events.append({
                    "ordinal": ordinal,
                    "kind": "AUDIO_BUFFER_SINK_CALL",
                    "target": {
                        "owner": callee[0],
                        "method": callee[1],
                        "signature": callee[2],
                    },
                    "invoke_kind": "STATIC" if is_static else "INSTANCE_OR_INTERFACE",
                    "argument_registers": regs,
                    "argument_register_types": target_types,
                    "argument_register_map": argument_register_map,
                    "buffer_argument_origins": origins,
                    "same_byte_buffer_parameter_passed": any(
                        "CALLER_TYPED_PARAMETER" in row["origins"]
                        for row in origins
                    ),
                    "byte_buffer_object_proven": bool(origins),
                })
            result_type = callee[2].split(")", 1)[1]
            if result_type == byte_buffer:
                pending_object_return_kind = "RETURNED_BYTEBUFFER_FROM_METHOD"
                pending_object_return_method = {
                    "owner": callee[0], "method": callee[1], "signature": callee[2]
                }
            elif result_type.startswith(("L", "[")):
                pending_object_return_kind = "UNKNOWN_OBJECT_RETURN"
                pending_object_return_method = None
            else:
                pending_object_return_kind = None
                pending_object_return_method = None
            continue

        if op == 0x0c:  # move-result-object
            dest = words[0] >> 8
            aliases.pop(dest, None)
            array_aliases.discard(dest)
            if pending_object_return_kind == "RETURNED_BYTEBUFFER_FROM_METHOD":
                aliases[dest] = {pending_object_return_kind}
                provenance_events.append({
                    "ordinal": ordinal,
                    "kind": "BYTEBUFFER_RETURNED_FROM_METHOD",
                    "source_method": pending_object_return_method,
                })
            elif pending_object_return_kind == "UNKNOWN_OBJECT_RETURN":
                aliases[dest] = {pending_object_return_kind}
            pending_object_return_kind = None
            pending_object_return_method = None
            continue

        pending_object_return_kind = None
        if op == 0x54:  # iget-object: field type only, any receiver
            dest = (words[0] >> 8) & 15
            field_owner, _field_name, field_type = field_id(dex, words[1])
            aliases.pop(dest, None)
            array_aliases.discard(dest)
            if field_type == byte_buffer:
                aliases[dest] = {"BYTEBUFFER_FIELD_READ"}
                provenance_events.append({
                    "ordinal": ordinal,
                    "kind": "BYTEBUFFER_FIELD_READ",
                    "field_owner": field_owner,
                    "field_type": field_type,
                })
            elif field_type == byte_buffer_array:
                array_aliases.add(dest)
            continue

        if op == 0x62:  # sget-object
            dest = (words[0] >> 8) & 15
            field_owner, _field_name, field_type = field_id(dex, words[1])
            aliases.pop(dest, None)
            array_aliases.discard(dest)
            if field_type == byte_buffer:
                aliases[dest] = {"BYTEBUFFER_STATIC_FIELD_READ"}
                provenance_events.append({
                    "ordinal": ordinal,
                    "kind": "BYTEBUFFER_STATIC_FIELD_READ",
                    "field_owner": field_owner,
                    "field_type": field_type,
                })
            elif field_type == byte_buffer_array:
                array_aliases.add(dest)
            continue

        if op == 0x46:  # aget-object from a declared ByteBuffer array
            dest = (words[0] >> 8) & 15
            array_register = (words[0] >> 12) & 15
            aliases.pop(dest, None)
            array_aliases.discard(dest)
            if array_register in array_aliases:
                aliases[dest] = {"BYTEBUFFER_ARRAY_ELEMENT_READ"}
                provenance_events.append({
                    "ordinal": ordinal,
                    "kind": "BYTEBUFFER_ARRAY_ELEMENT_READ",
                })
            continue

        if op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            if move:
                dest, source = move
                origins = set(aliases.get(source, ()))
                is_array_alias = source in array_aliases
                aliases.pop(dest, None)
                array_aliases.discard(dest)
                if origins:
                    aliases[dest] = origins
                if is_array_alias:
                    array_aliases.add(dest)
            continue

        if op == 0x1f:  # check-cast can refine an Object return to ByteBuffer
            dest = (words[0] >> 8) & 15
            cast_type = dex.descriptor(words[1])
            if cast_type == byte_buffer:
                origins = set(aliases.get(dest, ()))
                origins.add("CHECK_CAST_TO_BYTEBUFFER")
                aliases[dest] = origins
                provenance_events.append({
                    "ordinal": ordinal,
                    "kind": "CHECK_CAST_TO_BYTEBUFFER",
                })
            elif cast_type == byte_buffer_array:
                array_aliases.add(dest)
            continue

        dest = written_register(op, words)
        if dest is not None:
            aliases.pop(dest, None)
            array_aliases.discard(dest)
        if op in (0x28, 0x29, 0x2a) or 0x32 <= op <= 0x3d:
            branch_seen = True
            before_count = len(aliases) + len(array_aliases)
            aliases = {
                register: origins
                for register, origins in aliases.items()
                if register in stable_parameter_registers
                and origins == {"CALLER_TYPED_PARAMETER"}
            }
            array_aliases.clear()
            pruned_here = before_count > len(aliases)
            branch_aliases_pruned = branch_aliases_pruned or pruned_here
            if op == 0x28:  # goto/8
                raw_offset = (words[0] >> 8) & 0xff
                offset = raw_offset - 0x100 if raw_offset & 0x80 else raw_offset
            elif op == 0x29:  # goto/16
                raw_offset = words[1] & 0xffff
                offset = raw_offset - 0x10000 if raw_offset & 0x8000 else raw_offset
            elif op == 0x2a:  # goto/32
                raw_offset = (words[1] & 0xffff) | ((words[2] & 0xffff) << 16)
                offset = raw_offset - 0x100000000 if raw_offset & 0x80000000 else raw_offset
            else:  # if-* 22t
                raw_offset = words[1] & 0xffff
                offset = raw_offset - 0x10000 if raw_offset & 0x8000 else raw_offset
            if offset < 0 and pruned_here:
                backward_branch_aliases_cleared = True
            branch_preserved_parameter_registers.update(aliases)
        elif op in (0x2b, 0x2c):  # switch payload targets are not linear
            branch_seen = True
            before_count = len(aliases) + len(array_aliases)
            aliases = {
                register: origins
                for register, origins in aliases.items()
                if register in stable_parameter_registers
                and origins == {"CALLER_TYPED_PARAMETER"}
            }
            array_aliases.clear()
            pruned_here = before_count > len(aliases)
            branch_aliases_pruned = branch_aliases_pruned or pruned_here
            if pruned_here:
                switch_branch_aliases_cleared = True
            branch_preserved_parameter_registers.update(aliases)

    return {
        "method": {
            "owner": method[0],
            "method": method[1],
            "signature": method[2],
        },
        "byte_buffer_parameter_present": bool(parameter_registers),
        "byte_buffer_parameter_registers": sorted(parameter_registers),
        "parameter_registers_written": sorted(
            parameter_registers & potentially_written_registers
        ),
        "stable_parameter_registers_across_branches": sorted(stable_parameter_registers),
        "events": events,
        "buffer_provenance_events": provenance_events,
        "same_byte_buffer_parameter_to_audio_sink_proven": any(
            row["same_byte_buffer_parameter_passed"] for row in events
        ),
        "byte_buffer_object_to_audio_sink_proven": any(
            row["byte_buffer_object_proven"] for row in events
        ),
        "branch_seen": branch_seen,
        "branch_preserved_parameter_registers": sorted(
            branch_preserved_parameter_registers
        ),
        "backward_branch_aliases_cleared": backward_branch_aliases_cleared,
        "switch_branch_aliases_cleared": switch_branch_aliases_cleared,
        "branch_seen_aliases_cleared": branch_aliases_pruned,
        "field_names_or_values_disclosed": False,
        "media_values_or_audio_read": False,
    }



def inspect_audio_buffer_sink_caller_traces(apks, dispatch_report, class_profiles):
    focus = set()
    for owner_row in dispatch_report.get("owners", []):
        if owner_row.get("owner") != "LbJ2;":
            continue
        for callsite in owner_row.get("incoming_callsites", []):
            target = callsite.get("target", {})
            if target.get("method") != "native" or target.get("owner") not in (
                "LbJ2;", "Lpk0;"
            ):
                continue
            caller = callsite["caller"]
            focus.add((caller["owner"], caller["method"], caller["signature"]))
    if len(focus) > 16:
        raise ValueError("AUDIO_BUFFER_SINK_CALLER_FOCUS_LIMIT")
    traces = []
    found = set()
    upstream = []
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("AUDIO_BUFFER_SINK_CALLER_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                for method, flags, code_off in method_definitions_with_flags(dex):
                    ins = list(instructions(dex, code_off))
                    if method in focus:
                        found.add(method)
                        traces.append(trace_byte_buffer_parameter(
                            dex, method, flags, code_off, ins
                        ))
                    for ordinal, op, words in ins:
                        if op not in INVOKES:
                            continue
                        target = dex.method(words[1])
                        if target not in focus:
                            continue
                        if len(upstream) >= 256:
                            raise ValueError("AUDIO_BUFFER_SINK_UPSTREAM_CALLSITE_LIMIT")
                        profile = classify_track_owner_profile(
                            class_profiles.get(method[0], {})
                        )
                        upstream.append({
                            "caller": {
                                "owner": method[0],
                                "method": method[1],
                                "signature": method[2],
                            },
                            "target": {
                                "owner": target[0],
                                "method": target[1],
                                "signature": target[2],
                            },
                            "ordinal": ordinal,
                            "caller_signature_types": method_signature_type_profile(method),
                            "caller_owner_shape": {
                                key: profile[key] for key in (
                                    "has_track_field", "has_album_field",
                                    "has_wrapper_field", "has_media_item_field",
                                    "has_media_source_field", "has_media_metadata_field",
                                    "has_playback_state_field", "has_player_api_field",
                                    "implements_player_api", "has_media_session_field",
                                    "has_audio_track_field", "has_media_codec_field",
                                    "has_decoder_field", "has_source_like_field",
                                    "has_kotlin_flow_field", "has_collection_field",
                                )
                            },
                        })
    missing = sorted(focus - found)
    if missing:
        raise ValueError("AUDIO_BUFFER_SINK_CALLER_METHODS_NOT_ALL_DEFINED")
    owner_profiles = {}
    for row in upstream:
        owner = row["caller"]["owner"]
        if owner in owner_profiles:
            continue
        profile = class_profiles.get(owner, {})
        types = set(profile.get("instance_types", ())) | set(
            profile.get("static_types", ())
        )
        owner_profiles[owner] = {
            "owner": owner,
            "superclass": profile.get("superclass"),
            "interfaces": sorted(profile.get("interfaces", ())),
            "relevant_field_types": sorted(
                typ for typ in types
                if any(marker in typ.lower() for marker in (
                    "track", "album", "wrapper", "media", "source",
                    "data", "audio", "codec", "buffer", "uri",
                    "player", "flow", "collection", "list", "queue"
                ))
            ),
        }
    return {
        "focus_method_count": len(focus),
        "focus_methods": [
            {"owner": row[0], "method": row[1], "signature": row[2]}
            for row in sorted(focus)
        ],
        "buffer_identity_traces": traces,
        "upstream_callsite_count": len(upstream),
        "upstream_callers": upstream,
        "upstream_caller_owner_profiles": [
            owner_profiles[key] for key in sorted(owner_profiles)
        ],
        "runtime_dispatch_or_current_item_inferred": False,
        "media_values_or_audio_read": False,
    }


def audio_output_dispatch_contracts(focus_methods, class_profiles):
    """Build exact direct/interface/superclass method references for sink methods.

    This is a bounded static dispatch census. It does not infer the runtime
    receiver or claim that any caller is the active playback path.
    """
    focus_methods = sorted(set(focus_methods))
    if len(focus_methods) > 16:
        raise ValueError("AUDIO_OUTPUT_DISPATCH_FOCUS_LIMIT")
    contracts = {}
    owner_profiles = []

    def add_contract(target, kind, implementation):
        row = contracts.setdefault(target, {
            "contract_kinds": set(),
            "possible_implementations": set(),
        })
        row["contract_kinds"].add(kind)
        row["possible_implementations"].add(implementation)

    for implementation in focus_methods:
        owner, name, signature = implementation
        pending = [owner]
        visited = set()
        interface_owners = set()
        superclass_owners = set()
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            if len(visited) > 128:
                raise ValueError("AUDIO_OUTPUT_DISPATCH_HIERARCHY_LIMIT")
            profile = class_profiles.get(current)
            if not profile:
                continue
            for interface in profile.get("interfaces", ()):
                if interface not in interface_owners:
                    interface_owners.add(interface)
                    pending.append(interface)
            superclass = profile.get("superclass")
            if superclass and superclass != "Ljava/lang/Object;":
                if superclass not in superclass_owners:
                    superclass_owners.add(superclass)
                    pending.append(superclass)

        add_contract(
            implementation, "DIRECT_CLASS_METHOD_REFERENCE", implementation
        )
        for interface in interface_owners:
            add_contract(
                (interface, name, signature),
                "INTERFACE_METHOD_CONTRACT",
                implementation,
            )
        for superclass in superclass_owners:
            add_contract(
                (superclass, name, signature),
                "SUPERCLASS_VIRTUAL_CANDIDATE",
                implementation,
            )

        profile = class_profiles.get(owner, {})
        shape = classify_track_owner_profile(profile)
        all_types = set(profile.get("instance_types", ())) | set(
            profile.get("static_types", ())
        )
        relevant_types = sorted(
            typ for typ in all_types
            if any(marker in typ.lower() for marker in (
                "track", "album", "wrapper", "media", "source", "data",
                "audio", "codec", "buffer", "uri", "player", "flow",
                "collection", "list", "queue"
            ))
        )
        owner_profiles.append({
            "owner": owner,
            "profile_present": bool(profile),
            "superclass": profile.get("superclass"),
            "interfaces": sorted(profile.get("interfaces", ())),
            "relevant_field_types": relevant_types,
            "has_track_field": shape["has_track_field"],
            "has_album_field": shape["has_album_field"],
            "has_wrapper_field": shape["has_wrapper_field"],
            "has_audio_track_field": shape["has_audio_track_field"],
            "has_media_codec_field": shape["has_media_codec_field"],
            "has_decoder_field": shape["has_decoder_field"],
            "has_source_like_field": shape["has_source_like_field"],
            "has_kotlin_flow_field": shape["has_kotlin_flow_field"],
            "has_collection_field": shape["has_collection_field"],
            "has_playback_state_field": shape["has_playback_state_field"],
            "has_player_api_field": shape["has_player_api_field"],
            "implements_player_api": shape["implements_player_api"],
        })
    if len(contracts) > 128:
        raise ValueError("AUDIO_OUTPUT_DISPATCH_CONTRACT_LIMIT")
    return contracts, owner_profiles


def invoke_kind_name(op):
    if op in (0x71, 0x77):
        return "STATIC"
    if op in (0x6f, 0x75):
        return "SUPER"
    if op in (0x70, 0x76):
        return "DIRECT"
    if op in (0x72, 0x78):
        return "INTERFACE"
    if op in (0x6e, 0x74):
        return "VIRTUAL"
    return "OTHER_INVOKE"



def owner_ancestry_profiles(owner, class_profiles):
    """Return bounded type-only field profiles for one owner and its ancestors."""
    pending = [owner]
    visited = set()
    rows = []
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        if len(visited) > 128:
            raise ValueError("AUDIO_OUTPUT_OWNER_ANCESTRY_LIMIT")
        profile = class_profiles.get(current)
        if not profile:
            continue
        shape = classify_track_owner_profile(profile)
        all_types = set(profile.get("instance_types", ())) | set(
            profile.get("static_types", ())
        )
        relevant_types = sorted(
            typ for typ in all_types
            if any(marker in typ.lower() for marker in (
                "track", "album", "wrapper", "media", "source", "data",
                "audio", "codec", "buffer", "uri", "player", "flow",
                "collection", "list", "queue"
            ))
        )
        rows.append({
            "owner": current,
            "superclass": profile.get("superclass"),
            "interfaces": sorted(profile.get("interfaces", ())),
            "relevant_field_types": relevant_types,
            "has_track_field": shape["has_track_field"],
            "has_album_field": shape["has_album_field"],
            "has_wrapper_field": shape["has_wrapper_field"],
            "has_media_item_field": shape["has_media_item_field"],
            "has_media_source_field": shape["has_media_source_field"],
            "has_media_metadata_field": shape["has_media_metadata_field"],
            "has_playback_state_field": shape["has_playback_state_field"],
            "has_audio_track_field": shape["has_audio_track_field"],
            "has_media_codec_field": shape["has_media_codec_field"],
            "has_decoder_field": shape["has_decoder_field"],
            "has_player_api_field": shape["has_player_api_field"],
            "implements_player_api": shape["implements_player_api"],
        })
        for interface in profile.get("interfaces", ()):
            pending.append(interface)
        superclass = profile.get("superclass")
        if superclass and superclass != "Ljava/lang/Object;":
            pending.append(superclass)
    return rows


def trace_renderer_buffer_field_candidates(dex, method, flags, code_off, sink_targets):
    """Record same-method ByteBuffer field references, not runtime identity.

    A codec-return -> field store -> field read -> sink pattern is a structural
    candidate only. Branches, external writes, and active renderer selection
    are deliberately NOT modeled. Never read field values or report names.
    """
    byte_buffer = "Ljava/nio/ByteBuffer;"
    targets = set(sink_targets)
    ins = list(instructions(dex, code_off))
    if len(ins) > 20000:
        raise ValueError("RENDERER_BUFFER_METHOD_INSTRUCTION_LIMIT")
    register_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > register_size:
        raise ValueError("RENDERER_BUFFER_BAD_REGISTER_SIZE")
    this_reg = None if (flags & ACC_STATIC) else register_size - ins_size
    values = {}
    stores = []
    calls = []
    pending = None
    branch_seen = False

    def put(reg, value=None):
        values.pop(reg, None)
        if value is not None:
            values[reg] = value

    for ordinal, (_pc, op, words) in enumerate(ins):
        if op in INVOKES:
            callee = dex.method(words[1])
            if callee in targets:
                regs = invoke_registers(op, words)
                types = expand_invoke_register_types(
                    callee[0], parse_types(callee[2]), op in (0x71, 0x77)
                )
                refs = []
                if len(regs) == len(types):
                    for typ, reg in zip(types, regs):
                        if typ != byte_buffer:
                            continue
                        origin = values.get(reg)
                        if origin and origin[0] == "FIELD_READ":
                            _, field_index, read_receiver, read_ordinal = origin
                            matching_stores = [
                                item for item in stores
                                if item["field_index"] == field_index
                                and item["receiver_is_this"] and read_receiver
                                and item["ordinal"] < read_ordinal < ordinal
                            ]
                            refs.append({
                                "kind": "SAME_THIS_FIELD_REFERENCE_CANDIDATE",
                                "read_ordinal": read_ordinal,
                                "prior_codec_return_store_count": len(
                                    matching_stores
                                ),
                                "source_methods": sorted({
                                    (
                                        item["source_method"]["owner"],
                                        item["source_method"]["method"],
                                        item["source_method"]["signature"]
                                    )
                                    for item in matching_stores
                                }),
                                "same_runtime_buffer_proven": False,
                            })
                        elif origin:
                            refs.append({
                                "kind": origin[0],
                                "same_runtime_buffer_proven": False,
                            })
                calls.append({
                    "ordinal": ordinal,
                    "target": {
                        "owner": callee[0], "method": callee[1],
                        "signature": callee[2],
                    },
                    "buffer_reference_candidates": refs,
                    "same_codec_buffer_to_sink_proven": False,
                })
            return_type = callee[2].split(")", 1)[1]
            pending = (
                {"owner": callee[0], "method": callee[1],
                 "signature": callee[2]}
                if return_type == byte_buffer else None
            )
            continue
        if op == 0x0c:  # move-result-object
            put(words[0] >> 8, ("CODEC_BUFFER_RETURN", pending) if pending else None)
            pending = None
            continue
        pending = None
        if op == 0x5b:  # iput-object, record only exact typed buffer fields
            val = (words[0] >> 8) & 15
            recv = (words[0] >> 12) & 15
            field_owner, _private_name, field_type = field_id(dex, words[1])
            origin = values.get(val)
            if (field_type == byte_buffer and recv == this_reg
                    and origin and origin[0] == "CODEC_BUFFER_RETURN"):
                if len(stores) >= 128:
                    raise ValueError("RENDERER_BUFFER_FIELD_STORE_LIMIT")
                stores.append({
                    "field_index": words[1],
                    "ordinal": ordinal,
                    "field_owner": field_owner,
                    "receiver_is_this": True,
                    "source_method": origin[1],
                })
            continue
        if op == 0x54:  # iget-object
            dest = (words[0] >> 8) & 15
            recv = (words[0] >> 12) & 15
            _owner, _private_name, field_type = field_id(dex, words[1])
            put(
                dest,
                ("FIELD_READ", words[1], recv == this_reg, ordinal)
                if field_type == byte_buffer else None
            )
            continue
        if op in (0x07, 0x08, 0x09):  # move-object
            move = move_object_registers(op, words)
            if move:
                dest, src = move
                put(dest, values.get(src))
            continue
        if op == 0x1f:  # check-cast does not change object identity
            continue
        dest = written_register(op, words)
        if dest is not None:
            put(dest)
        if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
            branch_seen = True
            # A linear pass cannot carry aliases across possible paths.
            # Preserve structural field STORE rows only as candidates.
            values.clear()

    return {
        "method": {
            "owner": method[0], "method": method[1], "signature": method[2]
        },
        "codec_return_to_this_buffer_field_store_candidates": [
            {
                "ordinal": item["ordinal"],
                "field_owner": item["field_owner"],
                "field_type": byte_buffer,
                "source_method": item["source_method"],
            }
            for item in stores
        ],
        "audio_output_call_candidates": calls,
        "branches_unresolved": branch_seen,
        "same_codec_buffer_to_sink_proven": False,
        "same_selected_track_to_decoder_proven": False,
        "private_field_names_or_values_disclosed": False,
        "audio_bytes_read": False,
    }



def collect_sink_buffer_field_refs(dex, method, flags, code_off, sink_targets):
    """Collect exact ByteBuffer field refs handed to a sink, in memory only."""
    byte_buffer = "Ljava/nio/ByteBuffer;"
    aliases = {}
    refs = set()
    for _ordinal, (_pc, op, words) in enumerate(instructions(dex, code_off)):
        if op in INVOKES:
            callee = dex.method(words[1])
            if callee in sink_targets:
                regs = invoke_registers(op, words)
                types = expand_invoke_register_types(
                    callee[0], parse_types(callee[2]), op in (0x71, 0x77)
                )
                if len(regs) == len(types):
                    refs.update(
                        aliases[reg] for typ, reg in zip(types, regs)
                        if typ == byte_buffer and reg in aliases
                    )
            continue
        if op == 0x54:  # iget-object
            dest = (words[0] >> 8) & 15
            field_ref = field_id(dex, words[1])
            aliases.pop(dest, None)
            if field_ref[2] == byte_buffer:
                aliases[dest] = field_ref
            continue
        if op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            if move:
                dest, source = move
                old = aliases.get(source)
                aliases.pop(dest, None)
                if old:
                    aliases[dest] = old
            continue
        if op == 0x1f:
            continue
        dest = written_register(op, words)
        if dest is not None:
            aliases.pop(dest, None)
        if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
            aliases.clear()
    return refs


def trace_renderer_buffer_field_writes(dex, method, flags, code_off, target_fields):
    """Same-basic-block ByteBuffer provenance at exact iput-object sites."""
    aliases = {}
    pending_source = None
    events = []
    branch_seen = False
    for ordinal, (_pc, op, words) in enumerate(instructions(dex, code_off)):
        if op in INVOKES:
            callee = dex.method(words[1])
            return_type = callee[2].split(")", 1)[1]
            pending_source = {
                "owner": callee[0], "method": callee[1], "signature": callee[2]
            } if return_type == "Ljava/nio/ByteBuffer;" else None
            continue
        if op == 0x0c:
            dest = words[0] >> 8
            aliases.pop(dest, None)
            if pending_source:
                aliases[dest] = pending_source
            pending_source = None
            continue
        pending_source = None
        if op == 0x5b:
            source_reg = (words[0] >> 8) & 15
            ref = field_id(dex, words[1])
            if ref in target_fields:
                if len(events) >= 128:
                    raise ValueError("RENDERER_BUFFER_WRITER_METHOD_LIMIT")
                events.append({
                    "ordinal": ordinal,
                    "target_field_ref": ref,
                    "same_basic_block_buffer_return_source": aliases.get(source_reg),
                    "same_runtime_object_to_sink_proven": False,
                })
            continue
        if op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            if move:
                dest, src = move
                origin = aliases.get(src)
                aliases.pop(dest, None)
                if origin:
                    aliases[dest] = origin
            continue
        if op == 0x1f:
            continue
        dest = written_register(op, words)
        if dest is not None:
            aliases.pop(dest, None)
        if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
            branch_seen = True
            aliases.clear()
    return events, branch_seen


def inspect_renderer_buffer_field_writers(apks, caller_definitions, sink_targets):
    """Find exact xrefs to renderer ByteBuffer fields across bounded methods.

    Distinguishes same declared field from same runtime object; the latter
    cannot be established by field xrefs, so it remains explicitly false.
    """
    reader_fields = set()
    for method, (dex, flags, code_off) in caller_definitions.items():
        reader_fields.update(
            collect_sink_buffer_field_refs(
                dex, method, flags, code_off, sink_targets
            )
        )
    if len(reader_fields) > 32:
        raise ValueError("RENDERER_BUFFER_READER_FIELD_LIMIT")
    slots = {
        field_ref: index + 1 for index, field_ref in
        enumerate(sorted(reader_fields))
    }
    rows = []
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("RENDERER_BUFFER_WRITER_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                for method, flags, code_off in method_definitions_with_flags(dex):
                    # Bounded exact reference scan: skip methods with no
                    # matching ByteBuffer field writes without tracing values.
                    matching = False
                    for _pc, op, words in instructions(dex, code_off):
                        if op == 0x5b and field_id(dex, words[1]) in reader_fields:
                            matching = True
                            break
                    if not matching:
                        continue
                    if len(rows) >= 128:
                        raise ValueError("RENDERER_BUFFER_WRITER_OWNER_LIMIT")
                    events, branch_seen = trace_renderer_buffer_field_writes(
                        dex, method, flags, code_off, reader_fields
                    )
                    rows.append({
                        "method": {
                            "owner": method[0], "method": method[1],
                            "signature": method[2],
                        },
                        "field_store_sites": [
                            {
                                "ordinal": event["ordinal"],
                                "same_declared_buffer_field_slot":
                                    slots[event["target_field_ref"]],
                                "same_basic_block_buffer_return_source":
                                    event["same_basic_block_buffer_return_source"],
                                "same_runtime_object_to_sink_proven": False,
                            }
                            for event in events
                        ],
                        "branch_or_switch_seen": branch_seen,
                        "is_active_playback_writer_proven": False,
                    })
    return {
        "reader_field_slot_count": len(reader_fields),
        "exact_field_writer_method_count": len(rows),
        "exact_field_writer_methods": rows,
        "same_field_reference_is_not_same_java_object": True,
        "active_selected_item_proven": False,
        "same_native_item_to_decoder_proven": False,
        "private_field_names_or_values_disclosed": False,
        "media_bytes_read": False,
    }



def signed_branch_offset(value, bits):
    sign=1 << (bits-1)
    return value-(1 << bits) if value&sign else value


def build_dex_control_flow(dex, code_off):
    """Build bounded DEX instruction successors, including switch payload targets."""
    ins=list(instructions(dex,code_off))
    if not ins or len(ins)>20000:
        raise ValueError("TRACK_COROUTINE_CFG_INSTRUCTION_LIMIT")
    by_pc={pc:(op,words) for pc,op,words in ins}
    if len(by_pc)!=len(ins):
        raise ValueError("TRACK_COROUTINE_CFG_DUPLICATE_PC")
    real_pcs={
        pc for pc,(op,words) in by_pc.items()
        if not (op==0 and ((words[0]>>8)&0xff) in (1,2,3))
    }
    successors={}
    branches=[]
    exits={0x0e,0x0f,0x10,0x11,0x27}
    for pc in sorted(real_pcs):
        op,words=by_pc[pc]
        next_pc=pc+len(words)
        fallthrough=[next_pc] if next_pc in real_pcs else []
        targets=[]
        if op==0x28:
            targets=[pc+signed_branch_offset((words[0]>>8)&0xff,8)]
        elif op==0x29:
            targets=[pc+signed_branch_offset(words[1],16)]
        elif op==0x2a:
            raw=words[1]|(words[2]<<16)
            targets=[pc+signed_branch_offset(raw,32)]
        elif 0x32<=op<=0x3d:
            targets=[pc+signed_branch_offset(words[1],16)]
        elif op in (0x2b,0x2c):
            raw=words[1]|(words[2]<<16)
            payload_pc=pc+signed_branch_offset(raw,32)
            payload=by_pc.get(payload_pc)
            if payload is None or payload[0]!=0:
                raise ValueError("TRACK_COROUTINE_CFG_SWITCH_PAYLOAD_MISSING")
            payload_words=payload[1]
            tag=(payload_words[0]>>8)&0xff
            count=payload_words[1]
            if tag==1:
                target_start=4
            elif tag==2:
                target_start=2+2*count
            else:
                raise ValueError("TRACK_COROUTINE_CFG_SWITCH_PAYLOAD_TYPE")
            for n in range(count):
                at=target_start+2*n
                raw_target=payload_words[at]|(payload_words[at+1]<<16)
                targets.append(pc+signed_branch_offset(raw_target,32))
        elif op in exits:
            successors[pc]=[]
            continue
        all_targets=fallthrough+targets
        if any(target not in real_pcs for target in all_targets):
            raise ValueError("TRACK_COROUTINE_CFG_TARGET_INVALID")
        successors[pc]=sorted(set(all_targets))
        if op in (0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=op<=0x3d:
            branches.append({
                "pc":pc,"op":op,"target_pcs":sorted(set(targets)),
                "fallthrough_pcs":fallthrough
            })
    entry=min(real_pcs)
    reachable=set()
    pending=[entry]
    while pending:
        pc=pending.pop()
        if pc in reachable:
            continue
        reachable.add(pc)
        pending.extend(successors.get(pc,()))
        if len(reachable)>20000:
            raise ValueError("TRACK_COROUTINE_CFG_REACHABLE_LIMIT")
    return {
        "instructions":ins,
        "by_pc":by_pc,
        "successors":successors,
        "reachable":reachable,
        "branches":branches,
        "entry":entry
    }


def merge_coroutine_states(left, right):
    """Keep only aliases that are identical on every incoming CFG path."""
    merged={}
    for reg in left["registers"].keys() & right["registers"].keys():
        common=left["registers"][reg] & right["registers"][reg]
        if common:
            merged[reg]=frozenset(common)
    pending=left["pending_return"] if left["pending_return"]==right["pending_return"] else None
    return {"registers":merged,"pending_return":pending}


def trace_native_track_coroutine_continuation(
    dex, initial_method, initial_flags, initial_code_off,
    resume_method, resume_flags, resume_code_off
):
    """Branch-sensitive identity trace for the exact coroutine method."""
    continuation_owner="LFp0;"
    continuation_type="LOe2;"
    string_type="Ljava/lang/String;"
    wrapper_ctor=(WRAPPER,"<init>","(Ljava/lang/String;)V")
    coroutine_resume_call=(
        "LGp0;","new",
        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;"
    )
    track_regs=typed_parameter_registers(
        dex,initial_method,initial_flags,initial_code_off,MODEL
    )
    continuation_regs=typed_parameter_registers(
        dex,initial_method,initial_flags,initial_code_off,continuation_type
    )
    owner_regs=typed_parameter_registers(
        dex,initial_method,initial_flags,initial_code_off,initial_method[0]
    )
    if len(track_regs)!=1 or len(continuation_regs)!=1 or len(owner_regs)!=1:
        raise ValueError("TRACK_COROUTINE_PARAMETER_SHAPE")

    cfg=build_dex_control_flow(dex,initial_code_off)
    by_pc=cfg["by_pc"]
    successors=cfg["successors"]
    initial_registers={
        next(iter(track_regs)):frozenset({"ORIGINAL_TRACK_PARAMETER"}),
        next(iter(continuation_regs)):frozenset({"INPUT_CONTINUATION_PARAMETER"}),
        next(iter(owner_regs)):frozenset({"CAPTURE_OWNER_PARAMETER"})
    }
    initial_state={
        "registers":initial_registers,
        "pending_return":None
    }
    def state_key(state):
        return (
            tuple((reg,tuple(sorted(origins)))
                  for reg,origins in sorted(state["registers"].items())),
            state["pending_return"]
        )
    incoming={cfg["entry"]:{state_key(initial_state):initial_state}}
    work=[(cfg["entry"],state_key(initial_state))]
    processed=0
    wide_ops=(
        {0x04,0x05,0x06,0x0b,0x16,0x17,0x18,0x19,0x45,0x53,0x61,
         0x7d,0x7e,0x80,0x82,0x85,0x87,0x88,0x8a}
        |set(range(0x9b,0xa6))|set(range(0xab,0xb0))
        |set(range(0xbb,0xc6))|set(range(0xcb,0xd0))
    )

    def transfer(state,op,words):
        regs={r:set(v) for r,v in state["registers"].items()}
        pending_return=state["pending_return"]

        def clear(reg):
            regs.pop(reg,None)

        if op in INVOKES:
            callee=dex.method(words[1])
            args=invoke_registers(op,words)
            if callee==wrapper_ctor and len(args)==2:
                receiver,string_reg=args
                string_origins=regs.get(string_reg,set())
                wrapper_origins=set()
                if "ORIGINAL_TRACK_PARAMETER_STRING" in string_origins:
                    wrapper_origins.add("WRAPPER_FROM_ORIGINAL_TRACK_PARAMETER")
                for origin in string_origins:
                    if origin.startswith("CONTINUATION_FIELD_TRACK_STRING_SLOT:"):
                        wrapper_origins.add(
                            "WRAPPER_FROM_CONTINUATION_FIELD_TRACK_SLOT:"+origin.split(":",1)[1]
                        )
                if "CAPTURE_OWNER_TRACK_FIELD_STRING" in string_origins:
                    wrapper_origins.add("WRAPPER_FROM_CAPTURE_OWNER_TRACK_FIELD")
                if wrapper_origins:
                    regs.setdefault(receiver,set()).update(wrapper_origins)
            result_type=callee[2].split(")",1)[1]
            pending_return=(
                result_type if result_type in (
                    MODEL,WRAPPER,continuation_type,string_type
                ) else None
            )
            return {"registers":{r:frozenset(v) for r,v in regs.items() if v},
                    "pending_return":pending_return}

        if op==0x0c:  # move-result-object
            dest=words[0]>>8
            clear(dest)
            if pending_return==MODEL:
                regs[dest]={"UNLINKED_TRACK_RETURN"}
            elif pending_return==WRAPPER:
                regs[dest]={"UNLINKED_WRAPPER_RETURN"}
            elif pending_return==continuation_type:
                regs[dest]={"UNLINKED_CONTINUATION_RETURN"}
            elif pending_return==string_type:
                regs[dest]={"UNLINKED_STRING_RETURN"}
            pending_return=None
            return {"registers":{r:frozenset(v) for r,v in regs.items() if v},
                    "pending_return":None}

        pending_return=None
        if op==0x22:  # new-instance
            dest=(words[0]>>8)&0xff
            clear(dest)
            typ=dex.descriptor(words[1])
            if typ==continuation_owner:
                regs[dest]={"NEW_LFp0_CONTINUATION"}
            elif typ==WRAPPER:
                regs[dest]={"NEW_TRACK_WRAPPER"}
        elif op in (0x07,0x08,0x09):
            move=move_object_registers(op,words)
            if move:
                dest,source=move
                origins=set(regs.get(source,set()))
                clear(dest)
                if origins:
                    regs[dest]=origins
        elif op==0x1f:  # check-cast preserves the exact reference
            reg=words[0]>>8
            typ=dex.descriptor(words[1])
            origins=regs.get(reg,set())
            if typ==continuation_owner and "INPUT_CONTINUATION_PARAMETER" in origins:
                regs.setdefault(reg,set()).add("REUSED_LFp0_CONTINUATION")
        elif op==0x54:  # iget-object; never read the field value
            dest=(words[0]>>8)&15
            receiver=(words[0]>>12)&15
            field_owner,_field_name,field_type=field_id(dex,words[1])
            receiver_origins=regs.get(receiver,set())
            clear(dest)
            if field_type==MODEL:
                if field_owner==continuation_owner and (
                    "NEW_LFp0_CONTINUATION" in receiver_origins
                    or "REUSED_LFp0_CONTINUATION" in receiver_origins
                ):
                    regs[dest]={
                        "CONTINUATION_FIELD_TRACK",
                        "CONTINUATION_FIELD_TRACK_SLOT:"+str(words[1])
                    }
                elif "CAPTURE_OWNER_PARAMETER" in receiver_origins:
                    regs[dest]={"CAPTURE_OWNER_TRACK_FIELD"}
                elif "ORIGINAL_TRACK_PARAMETER" in receiver_origins:
                    regs[dest]={"TRACK_MEMBER_FIELD_VALUE"}
                elif "CONTINUATION_FIELD_TRACK" in receiver_origins:
                    regs[dest]={"CONTINUATION_TRACK_MEMBER_FIELD_VALUE"}
                elif "UNLINKED_TRACK_RETURN" in receiver_origins:
                    regs[dest]={"UNLINKED_TRACK_MEMBER_FIELD_VALUE"}
            elif field_type==string_type:
                if "ORIGINAL_TRACK_PARAMETER" in receiver_origins:
                    regs[dest]={"ORIGINAL_TRACK_PARAMETER_STRING"}
                elif "CONTINUATION_FIELD_TRACK" in receiver_origins:
                    slots={
                        origin.split(":",1)[1]
                        for origin in receiver_origins
                        if origin.startswith("CONTINUATION_FIELD_TRACK_SLOT:")
                    }
                    regs[dest]={
                        "CONTINUATION_FIELD_TRACK_STRING_SLOT:"+slot
                        for slot in slots
                    }
                elif "CAPTURE_OWNER_TRACK_FIELD" in receiver_origins:
                    regs[dest]={"CAPTURE_OWNER_TRACK_FIELD_STRING"}
        elif op==0x5b:  # iput-object; no mutation to register identity
            pass
        else:
            dest=written_register(op,words)
            if dest is not None:
                clear(dest)
                if op in wide_ops:
                    clear(dest+1)
        return {"registers":{r:frozenset(v) for r,v in regs.items() if v},
                "pending_return":pending_return}

    # Monotone must-alias dataflow. At a join, a register survives only if
    # every reachable predecessor carries the same exact origin category.
    while work:
        pc,key=work.pop()
        processed+=1
        if processed>200000:
            raise ValueError("TRACK_COROUTINE_CFG_DATAFLOW_LIMIT")
        state=incoming[pc][key]
        op,words=by_pc[pc]
        out=transfer(state,op,words)
        out_key=state_key(out)
        for target in successors.get(pc,()):
            bucket=incoming.setdefault(target,{})
            if out_key in bucket:
                continue
            if len(bucket)>=128:
                raise ValueError("TRACK_COROUTINE_CFG_PATH_STATE_LIMIT")
            bucket[out_key]=out
            work.append((target,out_key))

    stores=[]
    reads=[]
    string_reads=[]
    wrapper_ctors=[]
    wrapper_handoffs=[]
    parameter_writes=[]
    reachable_branches=[
        row for row in cfg["branches"]
        if row["pc"] in cfg["reachable"]
    ]
    seen_store_events=set()
    seen_read_events=set()
    seen_string_events=set()
    seen_wrapper_ctor_events=set()
    seen_wrapper_handoff_events=set()
    for pc in sorted(cfg["reachable"]):
      op,words=by_pc[pc]
      for path_state in incoming.get(pc,{}).values():
        state=path_state["registers"]
        if op==0x5b:
            value=(words[0]>>8)&15
            receiver=(words[0]>>12)&15
            field_owner,_field_name,field_type=field_id(dex,words[1])
            receiver_origins=state.get(receiver,frozenset())
            value_origins=state.get(value,frozenset())
            if field_owner==continuation_owner and field_type==MODEL and (
                "NEW_LFp0_CONTINUATION" in receiver_origins
                or "REUSED_LFp0_CONTINUATION" in receiver_origins
            ):
                row={
                    "pc":pc,"field_slot":words[1],
                    "source_origins":sorted(value_origins),
                    "receiver_origins":sorted(receiver_origins),
                    "same_original_track_parameter":(
                        "ORIGINAL_TRACK_PARAMETER" in value_origins
                    ),
                    "same_continuation_field_track":(
                        "CONTINUATION_FIELD_TRACK" in value_origins
                        or any(x.startswith("CONTINUATION_FIELD_TRACK_SLOT:")
                               for x in value_origins)
                    ),
                    "same_capture_owner_track_field":(
                        "CAPTURE_OWNER_TRACK_FIELD" in value_origins
                    ),
                    "source_is_unlinked_track_return":(
                        "UNLINKED_TRACK_RETURN" in value_origins
                    )
                }
                key=(pc,words[1],tuple(row["source_origins"]),tuple(row["receiver_origins"]))
                if key not in seen_store_events:
                    seen_store_events.add(key); stores.append(row)
        elif op==0x54:
            dest=(words[0]>>8)&15
            receiver=(words[0]>>12)&15
            field_owner,_field_name,field_type=field_id(dex,words[1])
            receiver_origins=state.get(receiver,frozenset())
            if field_owner==continuation_owner and field_type==MODEL and (
                "NEW_LFp0_CONTINUATION" in receiver_origins
                or "REUSED_LFp0_CONTINUATION" in receiver_origins
            ):
                row={
                    "pc":pc,"field_slot":words[1],
                    "value_register":dest,
                    "receiver_origins":sorted(receiver_origins)
                }
                key=(pc,words[1],tuple(row["receiver_origins"]))
                if key not in seen_read_events:
                    seen_read_events.add(key); reads.append(row)
            elif field_type==string_type:
                string_origins=[]
                if "ORIGINAL_TRACK_PARAMETER" in receiver_origins:
                    string_origins.append("ORIGINAL_TRACK_PARAMETER_STRING")
                string_origins.extend(
                    x.replace("CONTINUATION_FIELD_TRACK_SLOT:",
                              "CONTINUATION_FIELD_TRACK_STRING_SLOT:")
                    for x in receiver_origins
                    if x.startswith("CONTINUATION_FIELD_TRACK_SLOT:")
                )
                if "CAPTURE_OWNER_TRACK_FIELD" in receiver_origins:
                    string_origins.append("CAPTURE_OWNER_TRACK_FIELD_STRING")
                for string_origin in string_origins:
                    row={
                        "pc":pc,"field_slot":words[1],
                        "receiver_origins":sorted(receiver_origins),
                        "string_origin":string_origin,
                        "field_value_disclosed":False
                    }
                    key=(pc,words[1],tuple(row["receiver_origins"]),string_origin)
                    if key not in seen_string_events:
                        seen_string_events.add(key); string_reads.append(row)
        elif op in INVOKES:
            callee=dex.method(words[1])
            args=invoke_registers(op,words)
            if callee==wrapper_ctor and len(args)==2:
                row={
                    "pc":pc,
                    "wrapper_receiver_origins":sorted(state.get(args[0],frozenset())),
                    "string_argument_origins":sorted(state.get(args[1],frozenset()))
                }
                key=(pc,tuple(row["wrapper_receiver_origins"]),tuple(row["string_argument_origins"]))
                if key not in seen_wrapper_ctor_events:
                    seen_wrapper_ctor_events.add(key); wrapper_ctors.append(row)
            if callee[0]=="Lou3;" and callee[1]=="new":
                params=parse_types(callee[2])
                target_types=expand_invoke_register_types(
                    callee[0],params,op in (0x71,0x77)
                )
                origins=[
                    state.get(reg,frozenset())
                    for reg in args
                ]
                row={
                    "pc":pc,
                    "target":{"owner":callee[0],"method":callee[1],"signature":callee[2]},
                    "wrapper_argument_origins":sorted(
                        set().union(*(origins[i] for i,t in enumerate(target_types) if t==WRAPPER))
                    ),
                    "wrapper_instance_passed":any(
                        any(tag.startswith("WRAPPER_") or tag=="NEW_TRACK_WRAPPER"
                            for tag in origins[i])
                        for i,t in enumerate(target_types) if t==WRAPPER
                    ),
                    "continuation_argument_origins":sorted(
                        set().union(*(origins[i] for i,t in enumerate(target_types) if t==continuation_owner))
                    ),
                    "original_track_parameter_derived_wrapper_passed":any(
                        "WRAPPER_FROM_ORIGINAL_TRACK_PARAMETER" in origins[i]
                        for i,t in enumerate(target_types) if t==WRAPPER
                    ),
                    "continuation_field_derived_wrapper_passed":any(
                        any(x.startswith("WRAPPER_FROM_CONTINUATION_FIELD_TRACK_SLOT:")
                            for x in origins[i])
                        for i,t in enumerate(target_types) if t==WRAPPER
                    ),
                    "continuation_field_wrapper_source_slots":sorted({
                        x.split(":",1)[1]
                        for i,t in enumerate(target_types) if t==WRAPPER
                        for x in origins[i]
                        if x.startswith("WRAPPER_FROM_CONTINUATION_FIELD_TRACK_SLOT:")
                    }),
                    "capture_owner_field_derived_wrapper_passed":any(
                        "WRAPPER_FROM_CAPTURE_OWNER_TRACK_FIELD" in origins[i]
                        for i,t in enumerate(target_types) if t==WRAPPER
                    ),
                    "same_continuation_passed":any(
                        "NEW_LFp0_CONTINUATION" in origins[i]
                        or "REUSED_LFp0_CONTINUATION" in origins[i]
                        for i,t in enumerate(target_types) if t==continuation_owner
                    )
                }
                key=(pc,tuple(row["wrapper_argument_origins"]),
                     tuple(row["continuation_argument_origins"]))
                if key not in seen_wrapper_handoff_events:
                    seen_wrapper_handoff_events.add(key); wrapper_handoffs.append(row)

        dest=written_register(op,words)
        if dest is not None and dest in track_regs:
            row={
                "pc":pc,"op":op,
                "wide_second_register":op in wide_ops and dest+1 in track_regs
            }
            if row not in parameter_writes:
                parameter_writes.append(row)
      # end path-state loop

    matching_reads=[
        read for read in reads
        if any(store["field_slot"]==read["field_slot"] for store in stores)
    ]
    resume_this=None if resume_flags&ACC_STATIC else (
        dex.u16(resume_code_off)-dex.u16(resume_code_off+2)
    )
    resume_calls=[]
    for ordinal,(_pc,op,words) in enumerate(instructions(dex,resume_code_off)):
        if op not in INVOKES or dex.method(words[1])!=coroutine_resume_call:
            continue
        regs=invoke_registers(op,words)
        resume_calls.append({
            "ordinal":ordinal,"this_register":resume_this,
            "continuation_argument_register":regs[2] if len(regs)==3 else None,
            "invokeSuspend_this_passed_as_continuation":(
                len(regs)==3 and regs[2]==resume_this
            )
        })

    direct_capture=any(x["same_original_track_parameter"] for x in stores)
    continuation_self_write=any(x["same_continuation_field_track"] for x in stores)
    owner_field_capture=any(x["same_capture_owner_track_field"] for x in stores)
    original_wrapper=any(
        "WRAPPER_FROM_ORIGINAL_TRACK_PARAMETER" in x["wrapper_receiver_origins"]
        for x in wrapper_ctors
    ) and any(x["original_track_parameter_derived_wrapper_passed"] for x in wrapper_handoffs)
    continuation_wrapper_slots={
        origin.split(":",1)[1]
        for ctor in wrapper_ctors
        for origin in ctor["string_argument_origins"]
        if origin.startswith("CONTINUATION_FIELD_TRACK_STRING_SLOT:")
    } & {
        slot
        for handoff in wrapper_handoffs
        for slot in handoff["continuation_field_wrapper_source_slots"]
    }
    continuation_wrapper=bool(continuation_wrapper_slots)
    owner_wrapper=any(
        "CAPTURE_OWNER_TRACK_FIELD_STRING" in x["string_argument_origins"]
        for x in wrapper_ctors
    ) and any(x["capture_owner_field_derived_wrapper_passed"] for x in wrapper_handoffs)

    return {
        "initial_method":{"owner":initial_method[0],"method":initial_method[1],"signature":initial_method[2]},
        "resume_method":{"owner":resume_method[0],"method":resume_method[1],"signature":resume_method[2]},
        "track_parameter_registers":sorted(track_regs),
        "track_parameter_register_write_sites":parameter_writes,
        "control_flow_graph_built":True,
        "reachable_instruction_count":len(cfg["reachable"]),
        "dataflow_instruction_visits":processed,
        "max_path_states_at_instruction":max(
            (len(states) for states in incoming.values()),default=0
        ),
        "exception_handler_edges_included":False,
        "branch_sites":reachable_branches,
        "track_parameter_capture_store_candidates":stores,
        "continuation_track_field_reads":reads,
        "same_field_slot_store_to_resume_read_candidates":matching_reads,
        "track_string_field_read_sites":string_reads,
        "opaque_wrapper_constructor_sites":wrapper_ctors,
        "wrapper_continuation_handoff_sites":wrapper_handoffs,
        "resume_continuation_call_sites":resume_calls,
        "original_track_parameter_to_continuation_field_candidate":direct_capture,
        "all_observed_store_paths_same_original_track_parameter":(
            bool(stores) and all(x["same_original_track_parameter"] for x in stores)
        ),
        "continuation_field_self_write_candidate":continuation_self_write and bool(matching_reads),
        "capture_owner_track_field_to_continuation_candidate":owner_field_capture,
        "original_track_parameter_to_opaque_wrapper_candidate":original_wrapper,
        "continuation_field_track_to_opaque_wrapper_candidate":continuation_wrapper,
        "continuation_field_track_to_opaque_wrapper_slots":sorted(continuation_wrapper_slots),
        "capture_owner_track_field_to_opaque_wrapper_candidate":owner_wrapper,
        "branches_seen":bool(reachable_branches),
        "branch_path_predicates_evaluated":False,
        "coroutine_runtime_resume_dispatch_proven":False,
        "private_field_names_or_values_disclosed":False,
        "track_field_values_or_media_read":False
    }



def trace_track_value_to_exact_field_store(dex, method, flags, code_off, target_field):
    """Trace exact Track-parameter/field aliases to one private field write."""
    track_parameter_aliases=set(typed_parameter_registers(
        dex,method,flags,code_off,MODEL
    ))
    track_aliases=set(track_parameter_aliases)
    track_field_aliases=set()
    cast_object_aliases=set()
    object_aliases=set(typed_parameter_registers(
        dex,method,flags,code_off,"Ljava/lang/Object;"
    ))
    returned_track_aliases=set()
    this_register=None if flags&ACC_STATIC else (
        dex.u16(code_off)-dex.u16(code_off+2)
    )
    ins=list(instructions(dex,code_off))
    wide_ops=(
        {0x04,0x05,0x06,0x0b,0x16,0x17,0x18,0x19,0x45,0x53,0x61,
         0x7d,0x7e,0x80,0x82,0x85,0x87,0x88,0x8a}
        |set(range(0x9b,0xa6))|set(range(0xab,0xb0))
        |set(range(0xbb,0xc6))|set(range(0xcb,0xd0))
    )
    stores=[]
    pending_track_return=False
    branch_seen=False

    def clear(reg):
        for aliases in (
            track_aliases,track_parameter_aliases,track_field_aliases,
            cast_object_aliases,object_aliases,returned_track_aliases
        ):
            aliases.discard(reg)

    for ordinal,(_pc,op,words) in enumerate(ins):
        if op in INVOKES:
            callee=dex.method(words[1])
            # A Track-returning call is not assumed to return the same Track
            # as any parameter. Preserve it only as an unlinked candidate.
            pending_track_return=callee[2].split(")",1)[1]==MODEL
            continue
        if op==0x0c:  # move-result-object
            dest=words[0]>>8
            clear(dest)
            if pending_track_return:
                returned_track_aliases.add(dest)
            pending_track_return=False
            continue
        pending_track_return=False

        if op==0x54:  # iget-object; field values are never disclosed
            dest=(words[0]>>8)&15
            receiver=(words[0]>>12)&15
            _owner,_name,typ=field_id(dex,words[1])
            clear(dest)
            if typ==MODEL and receiver==this_register:
                track_aliases.add(dest)
                track_field_aliases.add(dest)
            continue

        if op==0x5b:  # iput-object
            value=(words[0]>>8)&15
            receiver=(words[0]>>12)&15
            if field_id(dex,words[1])==target_field:
                from_parameter=value in track_parameter_aliases
                from_field=value in track_field_aliases
                from_cast=value in cast_object_aliases
                from_unlinked_return=value in returned_track_aliases
                stores.append({
                    "ordinal":ordinal,
                    "value_register":value,
                    "receiver_register":receiver,
                    "source_is_original_track_parameter":from_parameter,
                    "source_is_track_field_read_from_this":from_field,
                    "source_is_track_parameter_or_field":(
                        value in track_aliases or from_cast
                    ),
                    "source_is_object_parameter_not_yet_cast":value in object_aliases,
                    "source_is_unlinked_track_return_candidate":from_unlinked_return,
                    "receiver_is_this":receiver==this_register,
                    "track_source_provenance":(
                        "SAME_TRACK_PARAMETER_REFERENCE" if from_parameter else
                        "TRACK_FIELD_REFERENCE" if from_field else
                        "CAST_OBJECT_PARAMETER_REFERENCE" if from_cast else
                        "UNLINKED_TRACK_RETURN_CANDIDATE" if from_unlinked_return else
                        "OBJECT_PARAMETER_UNREFINED" if value in object_aliases else
                        "UNTRACED"
                    )
                })
            continue

        if op in (0x07,0x08,0x09):  # move-object preserves reference identity
            move=move_object_registers(op,words)
            if move:
                dest,source=move
                origins={
                    "track":source in track_aliases,
                    "parameter":source in track_parameter_aliases,
                    "field":source in track_field_aliases,
                    "cast":source in cast_object_aliases,
                    "object":source in object_aliases,
                    "returned":source in returned_track_aliases
                }
                clear(dest)
                if origins["track"]: track_aliases.add(dest)
                if origins["parameter"]:
                    track_parameter_aliases.add(dest); track_aliases.add(dest)
                if origins["field"]:
                    track_field_aliases.add(dest); track_aliases.add(dest)
                if origins["cast"]: cast_object_aliases.add(dest)
                if origins["object"]: object_aliases.add(dest)
                if origins["returned"]: returned_track_aliases.add(dest)
            continue

        if op==0x1f:  # Object -> Track cast retains the same object, not an arbitrary Track return
            dest=(words[0]>>8)&0xff
            if dex.descriptor(words[1])==MODEL and dest in object_aliases:
                object_aliases.discard(dest)
                cast_object_aliases.add(dest)
            continue

        dest=written_register(op,words)
        if dest is not None:
            clear(dest)
            if op in wide_ops:
                clear(dest+1)
        if op in (0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=op<=0x3d:
            # Branches do not mutate registers; retain aliases until actual writes.
            branch_seen=True

    return {
        "method":{"owner":method[0],"method":method[1],"signature":method[2]},
        "track_parameter_count":len(typed_parameter_registers(
            dex,method,flags,code_off,MODEL
        )),
        "object_parameter_count":len(typed_parameter_registers(
            dex,method,flags,code_off,"Ljava/lang/Object;"
        )),
        "field_store_sites":stores,
        "branch_seen":branch_seen,
        "control_flow_feasibility_proven":False,
        "private_field_name_or_value_disclosed":False
    }



def inspect_continuation_track_field_writers(apks, reference_dex, reference_field_slot):
    """Find exact writers and callers in two bounded passes without retaining DEX methods."""
    target_field=field_id(reference_dex,reference_field_slot)
    if target_field[0]!="LFp0;" or target_field[2]!=MODEL:
        raise ValueError("CONTINUATION_TRACK_FIELD_CONTRACT_MISMATCH")
    writers=[]

    # Pass 1: retain only exact writer summaries and method references.
    scanned_method_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>DEX_MAX:
                    raise ValueError("CONTINUATION_TRACK_WRITER_DEX_LIMIT")
                dex=Dex(archive.read(entry.filename))
                for method,flags,code_off in method_definitions_with_flags(dex):
                    scanned_method_count+=1
                    if scanned_method_count>500000:
                        raise ValueError("CONTINUATION_TRACK_WRITER_METHOD_LIMIT")
                    sites=[]
                    for ordinal,(_pc,op,words) in enumerate(instructions(dex,code_off)):
                        if op!=0x5b:
                            continue
                        if field_id(dex,words[1])!=target_field:
                            continue
                        sites.append({
                            "ordinal":ordinal,
                            "value_register":(words[0]>>8)&15,
                            "receiver_register":(words[0]>>12)&15
                        })
                    if sites:
                        if len(writers)>=256:
                            raise ValueError("CONTINUATION_TRACK_WRITER_OWNER_LIMIT")
                        trace=trace_track_value_to_exact_field_store(
                            dex,method,flags,code_off,target_field
                        )
                        writers.append({
                            "method":trace["method"],
                            "field_store_sites":trace["field_store_sites"],
                            "track_parameter_count":trace["track_parameter_count"],
                            "object_parameter_count":trace["object_parameter_count"],
                            "branch_seen":trace["branch_seen"]
                        })

    writer_refs={
        (row["method"]["owner"],row["method"]["method"],row["method"]["signature"])
        for row in writers
    }
    callsites=[]

    # Pass 2: reopen the same signed DEX inputs and trace only callers that
    # actually invoke one of the exact writer methods discovered above.
    if writer_refs:
        for apk in apks:
            with zipfile.ZipFile(apk) as archive:
                for entry in archive.infolist():
                    if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                        continue
                    if entry.file_size>DEX_MAX:
                        raise ValueError("CONTINUATION_TRACK_WRITER_DEX_LIMIT")
                    dex=Dex(archive.read(entry.filename))
                    for caller,flags,code_off in method_definitions_with_flags(dex):
                        if caller in writer_refs:
                            continue
                        has_writer_call=False
                        for _pc,op,words in instructions(dex,code_off):
                            if op in INVOKES and dex.method(words[1]) in writer_refs:
                                has_writer_call=True
                                break
                        if not has_writer_call:
                            continue
                        trace=trace_identity_method(
                            dex,caller,flags,code_off,focus_targets=writer_refs,
                            capture_unproven_calls=True
                        )
                        for event in trace["events"]:
                            if event.get("kind")!="CALL_WITH_TYPED_IDENTITY":
                                continue
                            callee=event.get("callee",{})
                            target=(callee.get("owner"),callee.get("method"),callee.get("signature"))
                            if target not in writer_refs:
                                continue
                            if len(callsites)>=256:
                                raise ValueError("CONTINUATION_TRACK_WRITER_CALLSITE_LIMIT")
                            callsites.append({
                                "caller":{"owner":caller[0],"method":caller[1],"signature":caller[2]},
                                "target":callee,
                                "track_identity_arguments":event.get("identity_arguments",[])
                            })
    return {
        "target_is_LFp0_track_typed_field":True,
        "scanned_method_count":scanned_method_count,
        "writer_method_count":len(writers),
        "writer_methods":writers,
        "track_identity_callsite_count":len(callsites),
        "track_identity_callsites":callsites,
        "same_track_parameter_store_candidate":any(
            site["source_is_original_track_parameter"]
            for writer in writers for site in writer["field_store_sites"]
        ),
        "same_track_object_capture_into_continuation_field_proven":False,
        "control_flow_feasibility_proven":False,
        "field_names_values_track_ids_or_media_disclosed":False
    }

def inspect_audio_output_dispatch_callers(apks, sink_report, class_profiles):
    focus_methods = [
        (row["owner"], row["method"], row["signature"])
        for row in sink_report.get("focus_methods", [])
    ]
    contracts, owner_profiles = audio_output_dispatch_contracts(
        focus_methods, class_profiles
    )
    target_refs = set(contracts)
    callsites = []
    caller_definitions = {}
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("AUDIO_OUTPUT_DISPATCH_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                for caller, flags, code_off in method_definitions_with_flags(dex):
                    for ordinal, op, words in instructions(dex, code_off):
                        if op not in INVOKES:
                            continue
                        target = dex.method(words[1])
                        contract = contracts.get(target)
                        if not contract:
                            continue
                        kinds = contract["contract_kinds"]
                        eligible = []
                        if "DIRECT_CLASS_METHOD_REFERENCE" in kinds:
                            eligible.append("DIRECT_CLASS_METHOD_REFERENCE")
                        if (
                            "INTERFACE_METHOD_CONTRACT" in kinds
                            and op in (0x72, 0x78)
                        ):
                            eligible.append("INTERFACE_METHOD_CONTRACT")
                        if (
                            "SUPERCLASS_VIRTUAL_CANDIDATE" in kinds
                            and op in (0x6e, 0x74)
                        ):
                            eligible.append("SUPERCLASS_VIRTUAL_CANDIDATE")
                        if not eligible:
                            continue
                        if len(callsites) >= 512:
                            raise ValueError("AUDIO_OUTPUT_DISPATCH_CALLSITE_LIMIT")
                        regs = invoke_registers(op, words)
                        params = parse_types(target[2])
                        is_static = op in (0x71, 0x77)
                        register_types = expand_invoke_register_types(
                            target[0], params, is_static
                        )
                        caller_shape = classify_track_owner_profile(
                            class_profiles.get(caller[0], {})
                        )
                        caller_signature = method_signature_type_profile(caller)
                        if (
                            caller_signature["accepts_track"]
                            or caller_signature["accepts_album"]
                            or caller_signature["accepts_track_wrapper"]
                            or caller_shape["has_track_field"]
                            or caller_shape["has_album_field"]
                            or caller_shape["has_wrapper_field"]
                        ):
                            caller_role = "TRACK_IDENTITY_BEARING_METHOD_CANDIDATE"
                        elif "download2" in caller[0].lower() or "download2" in caller[2].lower():
                            caller_role = "DOWNLOAD_PACKAGE_METHOD_CANDIDATE"
                        elif (
                            caller_shape["has_decoder_field"]
                            or caller_shape["has_media_codec_field"]
                            or caller_shape["has_audio_track_field"]
                        ):
                            caller_role = "DECODER_OR_AUDIO_RENDERER_METHOD_CANDIDATE"
                        elif (
                            caller_shape["has_player_api_field"]
                            or caller_shape["implements_player_api"]
                        ):
                            caller_role = "PLAYER_API_METHOD_CANDIDATE"
                        else:
                            caller_role = "UNCLASSIFIED_METHOD"
                        all_types = set(
                            class_profiles.get(caller[0], {}).get("instance_types", ())
                        ) | set(
                            class_profiles.get(caller[0], {}).get("static_types", ())
                        )
                        relevant_types = sorted(
                            typ for typ in all_types
                            if any(marker in typ.lower() for marker in (
                                "track", "album", "wrapper", "media", "source",
                                "data", "audio", "codec", "buffer", "uri",
                                "player", "flow", "collection", "list", "queue"
                            ))
                        )
                        callsites.append({
                            "caller": {
                                "owner": caller[0],
                                "method": caller[1],
                                "signature": caller[2],
                            },
                            "target_reference": {
                                "owner": target[0],
                                "method": target[1],
                                "signature": target[2],
                            },
                            "contract_match_kinds": sorted(eligible),
                            "possible_sink_implementations": [
                                {"owner": row[0], "method": row[1], "signature": row[2]}
                                for row in sorted(contract["possible_implementations"])
                            ],
                            "ordinal": ordinal,
                            "invoke_kind": invoke_kind_name(op),
                            "argument_registers": regs,
                            "argument_register_types": register_types,
                            "caller_signature_types": caller_signature,
                            "caller_role_candidate": caller_role,
                            "caller_owner_profile": {
                                "superclass": class_profiles.get(caller[0], {}).get("superclass"),
                                "interfaces": sorted(
                                    class_profiles.get(caller[0], {}).get("interfaces", ())
                                ),
                                "relevant_field_types": relevant_types,
                                "has_track_field": caller_shape["has_track_field"],
                                "has_album_field": caller_shape["has_album_field"],
                                "has_wrapper_field": caller_shape["has_wrapper_field"],
                                "has_audio_track_field": caller_shape["has_audio_track_field"],
                                "has_media_codec_field": caller_shape["has_media_codec_field"],
                                "has_decoder_field": caller_shape["has_decoder_field"],
                                "has_source_like_field": caller_shape["has_source_like_field"],
                                "has_kotlin_flow_field": caller_shape["has_kotlin_flow_field"],
                                "has_collection_field": caller_shape["has_collection_field"],
                                "has_playback_state_field": caller_shape["has_playback_state_field"],
                                "has_player_api_field": caller_shape["has_player_api_field"],
                                "implements_player_api": caller_shape["implements_player_api"],
                            },
                        })
                        caller_definitions[caller] = (dex, flags, code_off)
                        if len(caller_definitions) > 256:
                            raise ValueError("AUDIO_OUTPUT_DISPATCH_CALLER_METHOD_LIMIT")

    traces = {}
    buffer_traces = {}
    renderer_field_traces = {}
    for caller, (dex, flags, code_off) in caller_definitions.items():
        traces[caller] = trace_identity_method(
            dex, caller, flags, code_off,
            candidate_owners=set(),
            focus_targets=target_refs,
        )
        buffer_traces[caller] = trace_byte_buffer_parameter(
            dex, caller, flags, code_off, sink_targets=target_refs
        )
        renderer_field_traces[caller] = trace_renderer_buffer_field_candidates(
            dex, caller, flags, code_off, target_refs
        )

    renderer_field_writer_census = inspect_renderer_buffer_field_writers(
        apks, caller_definitions, target_refs
    )
    identity_flow_count = 0
    byte_buffer_flow_count = 0
    for row in callsites:
        caller = (
            row["caller"]["owner"],
            row["caller"]["method"],
            row["caller"]["signature"],
        )
        trace = traces[caller]
        call_event = next((
            event for event in trace["events"]
            if event.get("ordinal") == row["ordinal"]
            and event.get("role") == "AUDIO_OUTPUT_METHOD_DISPATCH"
        ), None)
        identity_arguments = (
            call_event.get("identity_arguments", []) if call_event else []
        )
        if identity_arguments:
            identity_flow_count += 1
        prior_identity_events = [
            {
                "kind": event["kind"],
                "ordinal": event["ordinal"],
                "identity_type": event.get("identity_type"),
                "origins": event.get("origins"),
                "receiver_is_this": event.get("receiver_is_this"),
            }
            for event in trace["events"]
            if event.get("ordinal", -1) < row["ordinal"]
            and event.get("kind") in (
                "FIELD_READ_TYPED_IDENTITY",
                "MOVE_RESULT_TYPED_IDENTITY",
                "INSTANCE_FIELD_STORE_TYPED_IDENTITY",
                "STATIC_FIELD_STORE_TYPED_IDENTITY",
                "RETURN_TYPED_IDENTITY",
            )
        ]
        row["track_album_wrapper_identity_passed_to_audio_sink"] = bool(
            identity_arguments
        )
        row["identity_arguments_to_audio_sink"] = identity_arguments
        row["typed_identity_events_before_call"] = prior_identity_events
        row["branch_aliases_cleared_in_caller"] = trace[
            "branch_seen_aliases_cleared"
        ]
        buffer_trace = buffer_traces[caller]
        buffer_event = next((
            event for event in buffer_trace["events"]
            if event.get("ordinal") == row["ordinal"]
            and event.get("kind") == "AUDIO_BUFFER_SINK_CALL"
        ), None)
        buffer_origins = (
            buffer_event.get("buffer_argument_origins", [])
            if buffer_event else []
        )
        if buffer_event and buffer_event.get("byte_buffer_object_proven"):
            byte_buffer_flow_count += 1
        row["byte_buffer_object_proven_to_audio_output"] = bool(
            buffer_event and buffer_event.get("byte_buffer_object_proven")
        )
        row["buffer_argument_origins_to_audio_output"] = [
            {
                "argument_position": item["argument_position"],
                "origins": item["origins"],
            }
            for item in buffer_origins
        ]
        row["byte_buffer_provenance_events_before_call"] = [
            event for event in buffer_trace["buffer_provenance_events"]
            if event.get("ordinal", -1) < row["ordinal"]
        ]
        row["byte_buffer_branch_seen_in_caller"] = buffer_trace["branch_seen"]
        renderer_trace = renderer_field_traces[caller]
        field_event = next((
            event for event in renderer_trace["audio_output_call_candidates"]
            if event["ordinal"] == row["ordinal"]
        ), None)
        row["renderer_field_identity_candidates"] = (
            field_event["buffer_reference_candidates"] if field_event else []
        )
        row["same_codec_buffer_to_audio_output_proven"] = False

    caller_owner_profiles = []
    caller_owners = sorted({row["caller"]["owner"] for row in callsites})
    ancestry_track_owners = set()
    ancestry_album_owners = set()
    ancestry_wrapper_owners = set()
    for caller_owner in caller_owners:
        ancestry = owner_ancestry_profiles(caller_owner, class_profiles)
        ancestry_track_owners.update(
            row["owner"] for row in ancestry if row["has_track_field"]
        )
        ancestry_album_owners.update(
            row["owner"] for row in ancestry if row["has_album_field"]
        )
        ancestry_wrapper_owners.update(
            row["owner"] for row in ancestry if row["has_wrapper_field"]
        )
        caller_owner_profiles.append({
            "caller_owner": caller_owner,
            "ancestry": ancestry,
        })

    return {
        "focus_methods": [
            {"owner": row[0], "method": row[1], "signature": row[2]}
            for row in focus_methods
        ],
        "focus_owner_profiles": owner_profiles,
        "dispatch_contract_target_count": len(contracts),
        "dispatch_contract_targets": [
            {
                "owner": target[0],
                "method": target[1],
                "signature": target[2],
                "contract_kinds": sorted(contract["contract_kinds"]),
                "possible_sink_implementations": [
                    {"owner": row[0], "method": row[1], "signature": row[2]}
                    for row in sorted(contract["possible_implementations"])
                ],
            }
            for target, contract in sorted(contracts.items())
        ],
        "callsite_count": len(callsites),
        "distinct_caller_method_count": len(caller_definitions),
        "identity_flow_to_audio_sink_callsite_count": identity_flow_count,
        "byte_buffer_object_flow_to_audio_output_callsite_count": byte_buffer_flow_count,
        "caller_owner_ancestry_profiles": caller_owner_profiles,
        "renderer_field_candidate_traces": [
            renderer_field_traces[caller] for caller in sorted(renderer_field_traces)
        ],
        "renderer_field_writer_census": renderer_field_writer_census,
        "codec_output_object_to_audio_sink_proven": False,
        "ancestry_track_field_owner_count": len(ancestry_track_owners),
        "ancestry_album_field_owner_count": len(ancestry_album_owners),
        "ancestry_wrapper_field_owner_count": len(ancestry_wrapper_owners),
        "callsites": callsites,
        "runtime_receiver_dispatch_proven": False,
        "active_selected_item_proven": False,
        "same_native_item_to_decoder_proven": False,
        "field_names_or_values_disclosed": False,
        "media_values_or_audio_read": False,
    }


SOURCE_METHODS = {
    ("Lcom/yandex/music/shared/player/download2/o;", "while"),
    ("Lcom/yandex/music/shared/player/download2/o;", "for"),
    ("Lcom/yandex/music/shared/player/download2/o;", "if"),
    ("LGp0;", "new"), ("Lou3;", "new"),
    ("LDp0;", "if"), ("LDp0;", "emit"), ("LDp0;", "<init>"),
    ("Lwp0$a;", "emit"), ("Lwp0$a;", "<init>"),
    ("Lcq7;", "i0"), ("Lga4;", "d"), ("Ljm4;", "for"),
    ("Lam4;", "invokeSuspend"), ("Lam4;", "<init>"),
}
MAX_DEX = 6
MAX_FIELDS = 80
MAX_METHODS = 160
MAX_EVENTS = 36
ACC_STATIC = 0x8


def parse_types(signature: str) -> list[str]:
    if not signature.startswith("(") or ")" not in signature:
        raise ValueError("BAD_METHOD_SIGNATURE")
    text = signature[1:signature.index(")")]
    result = []
    i = 0
    while i < len(text):
        start = i
        while i < len(text) and text[i] == "[":
            i += 1
        if i >= len(text):
            raise ValueError("BAD_TYPE_DESCRIPTOR")
        if text[i] == "L":
            end = text.find(";", i)
            if end < 0:
                raise ValueError("BAD_OBJECT_DESCRIPTOR")
            i = end + 1
        elif text[i] in "ZBSCIJFD":
            i += 1
        else:
            raise ValueError("BAD_PRIMITIVE_DESCRIPTOR")
        result.append(text[start:i])
        if len(result) > 128:
            raise ValueError("METHOD_PARAMETER_LIMIT")
    return result


def expand_invoke_register_types(owner, params, is_static):
    """Expand logical invoke parameters to DEX register words (J/D use two)."""
    logical_types = list(params) if is_static else [owner] + list(params)
    register_types = []
    for typ in logical_types:
        register_types.append(typ)
        if typ in ("J", "D"):
            register_types.append(None)
    return register_types


def method_definitions_with_flags(dex: Dex):
    """Yield (method triple, access flags, code offset) from DEX class_data."""
    seen = 0
    for class_index in range(dex.class_count):
        base = dex.class_offset + class_index * 32
        owner = dex.descriptor(dex.u32(base))
        data_off = dex.u32(base + 24)
        if not data_off:
            continue
        static_fields, pos = uleb(dex, data_off)
        instance_fields, pos = uleb(dex, pos)
        direct_methods, pos = uleb(dex, pos)
        virtual_methods, pos = uleb(dex, pos)
        if max(static_fields, instance_fields, direct_methods, virtual_methods) > 100000:
            raise ValueError("CLASS_DATA_LIMIT")
        for count in (static_fields, instance_fields):
            previous = 0
            for _ in range(count):
                delta, pos = uleb(dex, pos)
                previous += delta
                _, pos = uleb(dex, pos)
        for count in (direct_methods, virtual_methods):
            previous = 0
            for _ in range(count):
                delta, pos = uleb(dex, pos)
                previous += delta
                flags, pos = uleb(dex, pos)
                code_off, pos = uleb(dex, pos)
                if previous >= dex.method_count:
                    raise DexError("METHOD_INDEX_OOB")
                method = dex.method(previous)
                if method[0] != owner:
                    raise DexError("METHOD_OWNER_MISMATCH")
                if code_off:
                    seen += 1
                    if seen > 1000000:
                        raise ValueError("METHOD_DEFINITION_LIMIT")
                    yield method, flags, code_off


def field_id(dex: Dex, index: int):
    count, table = dex.table(80, 8)
    if index < 0 or index >= count:
        raise DexError("FIELD_INDEX_OOB")
    pos = table + index * 8
    owner = dex.descriptor(dex.u16(pos))
    typ = dex.descriptor(dex.u16(pos + 2))
    name = dex.string(dex.u32(pos + 4))
    return owner, name, typ


def declared_fields_for_owner(dex: Dex, target: str):
    """Return only field IDs declared in the exact target class_data."""
    rows = []
    for class_index in range(dex.class_count):
        base = dex.class_offset + class_index * 32
        owner = dex.descriptor(dex.u32(base))
        if owner != target:
            continue
        data_off = dex.u32(base + 24)
        if not data_off:
            return rows
        static_fields, pos = uleb(dex, data_off)
        instance_fields, pos = uleb(dex, pos)
        _, pos = uleb(dex, pos)
        _, pos = uleb(dex, pos)
        for count in (static_fields, instance_fields):
            previous = 0
            for _ in range(count):
                delta, pos = uleb(dex, pos)
                previous += delta
                _, pos = uleb(dex, pos)
                rows.append(field_id(dex, previous))
        return rows
    return rows


def written_register(op: int, words):
    """Conservative destination register for common DEX value-writing ops."""
    if op in (0x01, 0x04, 0x07):
        return (words[0] >> 8) & 15
    if op in (0x02, 0x05, 0x08, 0x0a, 0x0b, 0x0c, 0x0d,
              0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19,
              0x1a, 0x1b, 0x1c, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25):
        return words[0] >> 8
    if op in (0x03, 0x06, 0x09):
        return words[1]
    if (0x2d <= op <= 0x31 or 0x44 <= op <= 0x4a
            or 0x52 <= op <= 0x58 or 0x60 <= op <= 0x66
            or 0x7b <= op <= 0x8f or 0x90 <= op <= 0xcf
            or 0xd0 <= op <= 0xe2):
        return (words[0] >> 8) & 15
    return None


def model_parameter_registers(dex: Dex, method, flags: int, code_off: int):
    params = parse_types(method[2])
    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        raise DexError("INVALID_INS_SIZE")
    reg = registers_size - ins_size
    found = []
    if not (flags & ACC_STATIC):
        if method[0] in (MODEL, ALBUM_MODEL):
            found.append((-1, reg))  # exact native Track or Album instance is "this"
        reg += 1
    for index, typ in enumerate(params):
        if typ == MODEL:
            found.append((index, reg))
        reg += 2 if typ in ("J", "D") else 1
    return found


def is_native_track_album_copy_method(method) -> bool:
    """Exact signed Track copy shape: Track + Album inputs, Track result."""
    if method[0] != MODEL or method[1] != "new":
        return False
    params = parse_types(method[2])
    result = method[2].split(")",1)[1]
    return (
        result == MODEL
        and params.count(MODEL) == 1
        and params.count(ALBUM_MODEL) == 1
    )


def track_album_copy_flow(dex: Dex, method, flags: int, code_off: int):
    """Trace Album argument/source-Album references into a new Track result."""
    if not is_native_track_album_copy_method(method):
        return None
    params = parse_types(method[2])
    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        raise DexError("ALBUM_COPY_INS_SIZE")
    register = registers_size - ins_size
    if not (flags & ACC_STATIC):
        register += 1
    track_register = None
    album_register = None
    for typ in params:
        if typ == MODEL:
            track_register = register
        if typ == ALBUM_MODEL:
            album_register = register
        register += 2 if typ in ("J", "D") else 1
    if track_register is None or album_register is None:
        return None
    track_aliases = {track_register}
    album_arg_aliases = {album_register}
    source_album_aliases = set()
    new_track_aliases = set()
    out = {
        "new_track_constructor_calls": 0,
        "album_argument_passed_to_new_track_constructor": False,
        "source_track_album_passed_to_new_track_constructor": False,
        "album_argument_stored_on_new_track": False,
        "source_track_album_stored_on_new_track": False,
        "returns_new_track": False,
        "reads_album_field_from_source_track": False,
    }
    for _pc, op, words in instructions(dex, code_off):
        if op == 0x22:  # new-instance
            dest = words[0] >> 8
            desc = dex.descriptor(words[1])
            for aliases in (track_aliases, album_arg_aliases,
                            source_album_aliases, new_track_aliases):
                aliases.discard(dest)
            if desc == MODEL:
                new_track_aliases.add(dest)
        elif op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            if move is not None:
                dest, source = move
                for aliases in (track_aliases, album_arg_aliases,
                                source_album_aliases, new_track_aliases):
                    aliases.discard(dest)
                    if source in aliases:
                        aliases.add(dest)
        elif 0x52 <= op <= 0x58:
            dest = written_register(op, words)
            receiver = (words[0] >> 12) & 15
            owner, _name, typ = field_id(dex, words[1])
            for aliases in (track_aliases, album_arg_aliases,
                            source_album_aliases, new_track_aliases):
                aliases.discard(dest)
            if owner == MODEL and typ == ALBUM_MODEL and receiver in track_aliases:
                source_album_aliases.add(dest)
                out["reads_album_field_from_source_track"] = True
        elif op == 0x5b:  # iput-object
            value = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            owner, _name, typ = field_id(dex, words[1])
            if owner == MODEL and typ == ALBUM_MODEL and receiver in new_track_aliases:
                if value in album_arg_aliases:
                    out["album_argument_stored_on_new_track"] = True
                if value in source_album_aliases:
                    out["source_track_album_stored_on_new_track"] = True
        elif op in INVOKES:
            callee = dex.method(words[1])
            regs = invoke_registers(op, words)
            if callee[0] == MODEL and callee[1] == "<init>" and regs:
                if regs[0] in new_track_aliases:
                    out["new_track_constructor_calls"] += 1
                    if any(reg in album_arg_aliases for reg in regs[1:]):
                        out["album_argument_passed_to_new_track_constructor"] = True
                    if any(reg in source_album_aliases for reg in regs[1:]):
                        out["source_track_album_passed_to_new_track_constructor"] = True
        elif op == 0x11:  # return-object
            if (words[0] >> 8) in new_track_aliases:
                out["returns_new_track"] = True
        elif op == 0x1f:  # check-cast preserves reference identity
            pass
        else:
            dest = written_register(op, words)
            if dest is not None:
                for aliases in (track_aliases, album_arg_aliases,
                                source_album_aliases, new_track_aliases):
                    aliases.discard(dest)
    return out


def album_constructor_argument_store(dex: Dex, method, flags: int, code_off: int):
    """Summarize Track-constructor Album-argument usage without exposing symbols."""
    if method[0] != MODEL or method[1] != "<init>" or flags & ACC_STATIC:
        return None
    params = parse_types(method[2])
    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        raise DexError("ALBUM_CTOR_INS_SIZE")
    this_register = registers_size - ins_size
    register = this_register + 1
    album_params = []
    for index, typ in enumerate(params):
        if typ == ALBUM_MODEL:
            album_params.append((index, register))
        register += 2 if typ in ("J", "D") else 1
    if len(album_params) != 1:
        return None
    album_index, album_register = album_params[0]
    aliases = {album_register}
    out = {
        "album_parameter_index": album_index,
        "stores_same_album_argument_on_track": False,
        "album_argument_invoke_count": 0,
        "album_argument_passed_to_track_method_count": 0,
        "album_argument_passed_to_other_method_count": 0,
        "album_typed_field_write_count": 0,
        "album_typed_field_write_on_this_count": 0,
        "album_argument_field_write_receiver_alias_count": 0,
        "album_argument_returned": False,
    }
    for _pc, op, words in instructions(dex, code_off):
        if op in INVOKES:
            callee = dex.method(words[1])
            regs = invoke_registers(op, words)
            if any(reg in aliases for reg in regs):
                out["album_argument_invoke_count"] += 1
                if callee[0] == MODEL:
                    out["album_argument_passed_to_track_method_count"] += 1
                else:
                    out["album_argument_passed_to_other_method_count"] += 1
        elif op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            if move is not None:
                dest, source = move
                if source in aliases:
                    aliases.add(dest)
                else:
                    aliases.discard(dest)
        elif op == 0x5b:
            value_register = (words[0] >> 8) & 15
            receiver_register = (words[0] >> 12) & 15
            owner, _name, typ = field_id(dex, words[1])
            if typ == ALBUM_MODEL:
                out["album_typed_field_write_count"] += 1
                if receiver_register == this_register:
                    out["album_typed_field_write_on_this_count"] += 1
                if value_register in aliases:
                    out["album_argument_field_write_receiver_alias_count"] += 1
                    if owner == MODEL and receiver_register == this_register:
                        out["stores_same_album_argument_on_track"] = True
        elif op == 0x11:
            if (words[0] >> 8) in aliases:
                out["album_argument_returned"] = True
        elif op == 0x1f:
            pass
        else:
            dest = written_register(op, words)
            if dest is not None:
                aliases.discard(dest)
            if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
                aliases.clear()
    return out


def straight_line_model_flow(dex: Dex, method, flags: int, code_off: int):
    model_params = model_parameter_registers(dex, method, flags, code_off)
    if not model_params:
        return None
    ins = list(instructions(dex, code_off))
    aliases = {reg for _, reg in model_params}
    events = []
    for ordinal, (pc, op, words) in enumerate(ins):
        if op in INVOKES:
            callee = dex.method(words[1])
            regs = invoke_registers(op, words)
            aliased_args = [i for i, reg in enumerate(regs) if reg in aliases]
            if aliased_args:
                role = None
                if (callee[0], callee[1]) == DESCRIPTOR_BUILDER:
                    role = "NATIVE_DESCRIPTOR_BUILDER"
                elif callee[0] in PLAYER_OWNERS and callee[1] in PLAYER_METHODS:
                    role = "PLAYER_SELECTION_OR_TRANSPORT"
                elif classify_boundary_call(callee) == "MEDIA_SESSION_METADATA":
                    role = "MEDIA_SESSION_METADATA_PUBLISH"
                elif classify_boundary_call(callee) == "MEDIA_SESSION_STATE":
                    role = "MEDIA_SESSION_STATE_PUBLISH"
                elif classify_boundary_call(callee) == "DECODER_BOUNDARY":
                    role = "DECODER_INPUT_OR_RENDERER_BOUNDARY"
                elif callee[0] == MODEL:
                    role = "MODEL_ACCESSOR_OR_METHOD"
                elif callee[0] == WRAPPER:
                    role = "TRACK_ID_WRAPPER_CONSTRUCTOR"
                elif callee[1] == "<init>":
                    role = "OBJECT_CONSTRUCTOR"
                if role:
                    events.append({
                        "ordinal": ordinal,
                        "role": role,
                        "callee": {
                            "owner": callee[0],
                            "method": callee[1],
                            "signature": callee[2],
                        },
                        "model_argument_words": aliased_args,
                    })
        if op in (0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58,
                  0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66):
            owner, name, typ = field_id(dex, words[1])
            if owner == MODEL:
                receiver = ((words[0] >> 12) & 15) if op < 0x60 else None
                if receiver is not None and receiver in aliases:
                    events.append({
                        "ordinal": ordinal,
                        "role": "MODEL_FIELD_READ",
                        "field": name,
                        "field_type": typ,
                    })
        move = move_object_registers(op, words)
        if move:
            dest, source = move
            was_alias = source in aliases
            aliases.discard(dest)
            if was_alias:
                aliases.add(dest)
        elif op == 0x1f:  # check-cast preserves the reference in vAA
            pass
        else:
            dest = written_register(op, words)
            if dest is not None:
                aliases.discard(dest)
            if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
                # Do not claim flow across branches or switch dispatch.
                aliases.clear()
        if len(events) >= MAX_EVENTS:
            break
    return {
        "method": {"owner": method[0], "name": method[1], "signature": method[2]},
        "model_parameters": [{"index": i, "register": r} for i, r in model_params],
        "straight_line_events": events,
        "branch_flow_not_inferred": True,
    }



def class_member_field_reads(dex: Dex, target: str):
    """Read only declared target-class methods and their own field projections."""
    methods = []
    reads = []
    for method, flags, code_off in method_definitions_with_flags(dex):
        if method[0] != target:
            continue
        methods.append(method)
        for ordinal, (pc, op, words) in enumerate(instructions(dex, code_off)):
            if op not in (0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58,
                          0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66):
                continue
            owner, name, typ = field_id(dex, words[1])
            if owner == target:
                reads.append({
                    "method": method[1],
                    "signature": method[2],
                    "field": name,
                    "field_type": typ,
                    "ordinal": ordinal,
                })
    return sorted(set(methods)), reads[:MAX_METHODS]


def wrapper_constructor_input_flow(dex: Dex, method, flags: int, code_off: int):
    """Track only same-block String provenance into LtCa(String) constructors."""
    model_params = model_parameter_registers(dex, method, flags, code_off)
    model_aliases = {reg for _, reg in model_params}
    provenance = {}
    pending_result = None
    events = []
    for ordinal, (pc, op, words) in enumerate(instructions(dex, code_off)):
        if op in INVOKES:
            callee = dex.method(words[1])
            regs = invoke_registers(op, words)
            if callee[0] == WRAPPER and callee[1] == "<init>" and len(regs) >= 2:
                origin = provenance.get(regs[1], {"kind": "UNTRACED_STRING"})
                events.append({
                    "ordinal": ordinal,
                    "constructor": {"owner": callee[0], "method": callee[1],
                                    "signature": callee[2]},
                    "string_argument_origin": origin,
                    "model_receiver_in_same_method": bool(
                        origin.get("model_receiver_in_same_method", False)),
                })
            pending_result = None
            if callee[2].endswith(")Ljava/lang/String;"):
                model_arg_positions = [
                    index for index, register in enumerate(regs)
                    if register in model_aliases
                ]
                inputs = [provenance[r] for r in regs if r in provenance]
                if model_arg_positions:
                    pending_result = {
                        "kind": "NATIVE_TRACK_MODEL_DERIVED_STRING",
                        "producer_owner": callee[0],
                        "producer_method": callee[1],
                        "model_argument_positions": model_arg_positions,
                        "input_kinds": sorted({v.get("kind", "UNKNOWN") for v in inputs}),
                        "model_receiver_in_same_method": True,
                    }
                elif inputs:
                    pending_result = {
                        "kind": "DERIVED_STRING",
                        "producer_owner": callee[0],
                        "producer_method": callee[1],
                        "input_kinds": sorted({v.get("kind", "UNKNOWN") for v in inputs}),
                        "model_receiver_in_same_method": any(
                            v.get("model_receiver_in_same_method", False) for v in inputs),
                    }
        elif op == 0x0c:  # move-result-object
            dest = words[0] >> 8
            if pending_result is not None:
                provenance[dest] = pending_result
            else:
                provenance.pop(dest, None)
            pending_result = None
        elif op in (0x54,):  # iget-object
            dest = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            owner, name, typ = field_id(dex, words[1])
            if owner == MODEL and typ == "Ljava/lang/String;" and receiver in model_aliases:
                provenance[dest] = {
                    "kind": "NATIVE_TRACK_STRING_FIELD",
                    "field": name,
                    "model_receiver_in_same_method": True,
                }
            else:
                provenance.pop(dest, None)
            pending_result = None
        elif op in (0x1a, 0x1b):  # const-string; do not export the literal
            provenance[words[0] >> 8] = {"kind": "CONSTANT_STRING"}
            pending_result = None
        else:
            move = move_object_registers(op, words)
            if move:
                dest, source = move
                if source in model_aliases:
                    model_aliases.add(dest)
                else:
                    model_aliases.discard(dest)
                if source in provenance:
                    provenance[dest] = provenance[source]
                else:
                    provenance.pop(dest, None)
            elif op == 0x1f:  # check-cast preserves the reference
                pass
            else:
                dest = written_register(op, words)
                if dest is not None:
                    model_aliases.discard(dest)
                    provenance.pop(dest, None)
                if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
                    model_aliases.clear()
                    provenance.clear()
            pending_result = None
        if len(events) >= MAX_EVENTS:
            break
    if not events:
        return None
    return {
        "caller": {"owner": method[0], "name": method[1], "signature": method[2]},
        "model_parameters": [{"index": i, "register": r} for i, r in model_params],
        "wrapper_constructors": events,
        "branch_flow_not_inferred": True,
    }



def const4_zero_to_register(op: int, words, register: int) -> bool:
    """Exact 11n opcode, dest nibble and *zero* signed nibble, never values."""
    return (op == 0x12 and len(words) == 1
            and ((words[0] >> 8) & 0x0f) == register
            and ((words[0] >> 12) & 0x0f) == 0)


def focused_method_trace(dex: Dex, method, flags: int, code_off: int):
    """Bounded opcode-shape trace; never emits literals, values or media data."""
    model_params = model_parameter_registers(dex, method, flags, code_off)
    aliases = {reg for _, reg in model_params}
    rows = []
    for ordinal, (pc, op, words) in enumerate(instructions(dex, code_off)):
        if op in INVOKES:
            callee = dex.method(words[1])
            regs = invoke_registers(op, words)
            rows.append({
                "ordinal": ordinal, "op": "INVOKE",
                "callee": {"owner": callee[0], "method": callee[1],
                           "signature": callee[2]},
                "argument_registers": regs,
                "native_track_argument_positions": [
                    i for i, reg in enumerate(regs) if reg in aliases
                ],
            })
        elif op in (0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58,
                    0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66):
            owner, name, typ = field_id(dex, words[1])
            dest = ((words[0] >> 8) & 15) if op < 0x60 else None
            receiver = ((words[0] >> 12) & 15) if op < 0x60 else None
            rows.append({
                "ordinal": ordinal, "op": "FIELD_READ",
                "owner": owner, "field": name, "type": typ,
                "destination_register": dest,
                "receiver_is_native_model": receiver in aliases if receiver is not None else False,
            })
        elif op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            dest, source = move
            rows.append({"ordinal": ordinal, "op": "MOVE_OBJECT",
                         "destination_register": dest, "source_register": source,
                         "source_is_native_track": source in aliases})
            if source in aliases:
                aliases.add(dest)
            else:
                aliases.discard(dest)
        elif op == 0x0c:
            rows.append({"ordinal": ordinal, "op": "MOVE_RESULT_OBJECT",
                         "destination_register": words[0] >> 8})
        elif op in (0x1a, 0x1b):
            rows.append({"ordinal": ordinal, "op": "CONST_STRING",
                         "destination_register": words[0] >> 8,
                         "literal_disclosed": False})
        elif op == 0x11:
            rows.append({"ordinal": ordinal, "op": "RETURN_OBJECT",
                         "source_register": words[0] >> 8,
                         "source_is_native_track": (words[0] >> 8) in aliases})
        elif op == 0x1f:
            rows.append({"ordinal": ordinal, "op": "CHECK_CAST",
                         "type": dex.descriptor(words[1]),
                         "register": words[0] >> 8})
        else:
            dest = written_register(op, words)
            if dest is not None:
                aliases.discard(dest)
            if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
                rows.append({"ordinal": ordinal, "op": "BRANCH_OR_SWITCH"})
                aliases.clear()
        if len(rows) >= 180:
            break
    return {
        "method": {"owner": method[0], "name": method[1], "signature": method[2]},
        "this_register": (
            None if flags & ACC_STATIC
            else dex.u16(code_off) - dex.u16(code_off + 2)
        ),
        "native_model_parameters": [{"index": i, "register": r} for i, r in model_params],
        "instructions": rows,
        "literals_or_runtime_values_disclosed": False,
    }



def class_instantiation_and_flow_collect_sites(dex: Dex, method, code_off: int):
    targets = {"LDp0;", "Lwp0$a;", "LGp0;", "Lou3;", "LGl4;", "Ljm4;", "Lk1a;", "Lam4;"}
    aliases = {name: set() for name in targets}
    instantiated = []
    collected = []
    for ordinal, (pc, op, words) in enumerate(instructions(dex, code_off)):
        if op == 0x22:  # new-instance
            target = dex.descriptor(words[1])
            if target in targets:
                dest = words[0] >> 8
                aliases[target].add(dest)
                instantiated.append({"class": target, "register": dest, "ordinal": ordinal})
        elif op in (0x07, 0x08, 0x09):
            dest, source = move_object_registers(op, words)
            for target in targets:
                if source in aliases[target]:
                    aliases[target].add(dest)
                else:
                    aliases[target].discard(dest)
        elif op in INVOKES:
            callee = dex.method(words[1])
            regs = invoke_registers(op, words)
            for target in targets:
                positions = [i for i, reg in enumerate(regs) if reg in aliases[target]]
                if positions:
                    collected.append({
                        "class": target,
                        "call_kind": "FLOW_COLLECT_OR_EMIT" if callee[1] in (
                            "collect", "collectLatest", "launchIn", "emit") else "OBJECT_PASSED_TO_METHOD",
                        "callee": {"owner": callee[0], "method": callee[1],
                                   "signature": callee[2]},
                        "argument_positions": positions,
                        "ordinal": ordinal,
                    })
        elif 0x59 <= op <= 0x5f:  # iput*: capture only the destination field identity
            value_register = (words[0] >> 8) & 15
            owner, name, typ = field_id(dex, words[1])
            for target in targets:
                if value_register in aliases[target]:
                    collected.append({
                        "class": target, "call_kind": "OBJECT_STORED_IN_INSTANCE_FIELD",
                        "destination_owner": owner, "destination_field": name,
                        "destination_type": typ, "ordinal": ordinal,
                    })
        elif 0x67 <= op <= 0x6d:  # sput*: capture only static destination field
            value_register = words[0] >> 8
            owner, name, typ = field_id(dex, words[1])
            for target in targets:
                if value_register in aliases[target]:
                    collected.append({
                        "class": target, "call_kind": "OBJECT_STORED_IN_STATIC_FIELD",
                        "destination_owner": owner, "destination_field": name,
                        "destination_type": typ, "ordinal": ordinal,
                    })
        elif op == 0x1f:
            pass
        else:
            dest = written_register(op, words)
            if dest is not None:
                for target in targets:
                    aliases[target].discard(dest)
            if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
                for target in targets:
                    aliases[target].clear()
        if len(instantiated) + len(collected) >= MAX_EVENTS:
            break
    if not instantiated and not collected:
        return None
    return {
        "caller": {"owner": method[0], "name": method[1], "signature": method[2]},
        "instantiations": instantiated,
        "flow_collect_or_emit_calls": collected,
        "branch_flow_not_inferred": True,
    }


def inspect_signed(apks):
    dex_count = 0
    model_defined = False
    album_defined = False
    model_fields = {}
    album_fields = {}
    model_methods = []
    album_methods = []
    model_accessor_field_reads = []
    album_accessor_field_reads = []
    track_album_constructor_rows = []
    track_album_copy_flow_rows = []
    model_method_definitions = []
    wrapper_constructor_callsites = []
    model_referenced_methods = []
    descriptor_builder_callers = []
    player_method_refs = set()
    media_session_method_refs = set()
    decoder_boundary_method_refs = set()
    semantic_marker_counts = {marker: 0 for marker in SEMANTIC_IDENTITY_MARKERS}
    class_profiles = {}
    boundary_callsite_rows = []
    model_flow_candidates = []
    wrapper_methods = set()
    flow_source_interface_methods = set()
    target_callers = []
    focused_method_traces = []
    flow_dispatcher_instantiation_sites = []
    flow_dispatcher_class_fields = {}
    fp0_resume_null_track_arg = False
    fp0_coroutine_method_definitions = {}
    raa_resume_same_continuation = False
    raa_resume_null_wrapper = False
    exo_source_defined = False
    exo_source_close_void_declared = False
    trace_targets = {
        (MODEL, "super"), (ALBUM_MODEL, "if"), ("LGp0;", "new"),
        ("LDp0;", "if"), ("LDp0;", "emit"), ("LDp0;", "<init>"),
        ("Lwp0$a;", "emit"), ("Lwp0$a;", "<init>"), ("Ljm4;", "for"),
        ("Lam4;", "invokeSuspend"), ("Lam4;", "<init>"),
        ("LFp0;", "invokeSuspend"), ("LFp0;", "<init>"),
        ("Lou3;", "new"),
        ("Lcom/yandex/music/shared/player/download2/o;", "for"),
        ("Lcom/yandex/music/shared/player/download2/o$c;", "invokeSuspend"),
        ("Lcom/yandex/music/shared/player/download2/o$c;", "<init>"),
        ("LRAa;", "invokeSuspend"), ("LRAa;", "<init>")
    }
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("SIGNED_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                dex_count += 1
                defined = dex.defined_classes()
                for owner, profile in declared_field_inventory(dex).items():
                    if owner in class_profiles:
                        raise ValueError("DUPLICATE_CLASS_FIELD_INVENTORY")
                    class_profiles[owner] = profile
                for descriptor in defined:
                    lowered = descriptor.lower()
                    if "edition" in lowered:
                        semantic_marker_counts["edition"] += 1
                    if "generation" in lowered:
                        semantic_marker_counts["generation"] += 1
                if ("Lcom/yandex/music/shared/player/download2/exo/"
                        "RetryingBalancingDataSource;" in defined):
                    exo_source_defined = True
                if MODEL in defined:
                    if model_defined:
                        raise ValueError("DUPLICATE_NATIVE_TRACK_MODEL")
                    model_defined = True
                    for owner, name, typ in declared_fields_for_owner(dex, MODEL):
                        model_fields[name] = typ
                        if len(model_fields) > MAX_FIELDS:
                            raise ValueError("MODEL_FIELD_LIMIT")
                    model_methods, reads = class_member_field_reads(dex, MODEL)
                    model_accessor_field_reads.extend(reads)
                if ALBUM_MODEL in defined:
                    if album_defined:
                        raise ValueError("DUPLICATE_NATIVE_ALBUM_MODEL")
                    album_defined = True
                    for owner, name, typ in declared_fields_for_owner(dex, ALBUM_MODEL):
                        album_fields[name] = typ
                        if len(album_fields) > MAX_FIELDS:
                            raise ValueError("ALBUM_FIELD_LIMIT")
                    album_methods, reads = class_member_field_reads(dex, ALBUM_MODEL)
                    album_accessor_field_reads.extend(reads)
                for target_class in ("LDp0;", "Lwp0$a;", "LGp0;", "Lou3;",
                                     "LGl4;", "Ljm4;", "Lk1a;", "Lam4;", "LFp0;",
                                     "Lcom/yandex/music/shared/player/download2/o$c;",
                                     "LRAa;"):
                    if target_class in defined:
                        flow_dispatcher_class_fields[target_class] = [
                            {"field": name, "type": typ}
                            for _, name, typ in declared_fields_for_owner(dex, target_class)
                        ]
                for i in range(dex.method_count):
                    method = dex.method(i)
                    if method[0] == MODEL:
                        model_referenced_methods.append(method)
                    if method[0] == WRAPPER:
                        wrapper_methods.add(method)
                    if method[0] in PLAYER_OWNERS and method[1] in PLAYER_METHODS:
                        player_method_refs.add(method)
                    if method[0] == MEDIA_SESSION_OWNER and (
                        method[1] in MEDIA_SESSION_METADATA_METHODS
                        or method[1] in MEDIA_SESSION_STATE_METHODS
                    ):
                        media_session_method_refs.add(method)
                    if method[0] in DECODER_BOUNDARY_METHODS and (
                        method[1] in DECODER_BOUNDARY_METHODS[method[0]]
                    ):
                        decoder_boundary_method_refs.add(method)
                    if method[0] == "LGl4;":
                        flow_source_interface_methods.add(method)
                for method, flags, code_off in method_definitions_with_flags(dex):
                    if method in (
                        ("LGp0;", "new",
                         "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;"),
                        ("LFp0;", "invokeSuspend",
                         "(Ljava/lang/Object;)Ljava/lang/Object;")
                    ):
                        fp0_coroutine_method_definitions[method] = (dex, flags, code_off)
                    if method[0] == MODEL:
                        model_method_definitions.append((method,flags,code_off))
                        if is_native_track_album_copy_method(method):
                            if len(track_album_copy_flow_rows)>=4:
                                raise ValueError("TRACK_ALBUM_COPY_BOUND")
                            track_album_copy_flow_rows.append(
                                track_album_copy_flow(dex,method,flags,code_off))
                    if method[0] == MODEL and method[1] == "<init>":
                        album_row = album_constructor_argument_store(
                            dex, method, flags, code_off)
                        if album_row is not None:
                            if len(track_album_constructor_rows) >= 8:
                                raise ValueError("TRACK_ALBUM_CTOR_BOUND")
                            track_album_constructor_rows.append(album_row)
                    if method == (
                        "Lcom/yandex/music/shared/player/download2/exo/"
                        "RetryingBalancingDataSource;", "close", "()V"
                    ):
                        exo_source_close_void_declared = True
                    if (method[0], method[1]) in trace_targets:
                        focused_method_traces.append(
                            focused_method_trace(dex, method, flags, code_off))
                    if (method[0], method[1]) == ("LFp0;", "invokeSuspend"):
                        # Inspect only the instruction immediately before the
                        # known exact Gp0.new call. No branch-sensitive taint.
                        fp0_ins = list(instructions(dex, code_off))
                        for n, (_, opcode, words) in enumerate(fp0_ins):
                            if opcode not in INVOKES or n == 0:
                                continue
                            callee = dex.method(words[1])
                            if callee != (
                                    "LGp0;", "new",
                                    "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;"):
                                continue
                            registers = invoke_registers(opcode, words)
                            if (len(registers) == 3
                                    and const4_zero_to_register(
                                        fp0_ins[n-1][1], fp0_ins[n-1][2], registers[1])):
                                fp0_resume_null_track_arg = True
                    if (method[0], method[1]) == ("LRAa;", "invokeSuspend"):
                        # Signed Kotlin continuation replay of download2.o.for.
                        # The receiver may be copied by an exact move-object.
                        ins_resume = list(instructions(dex, code_off))
                        this_reg = dex.u16(code_off) - dex.u16(code_off + 2)
                        expected = (
                            "Lcom/yandex/music/shared/player/download2/o;", "for",
                            "(Lcom/yandex/music/shared/player/download2/o;LqX8$d;"
                            "LtCa;Lf6a;Ln26;LOe2;)Ljava/lang/Object;"
                        )
                        for n, (_, op, words) in enumerate(ins_resume):
                            if op not in INVOKES or n == 0 or dex.method(words[1]) != expected:
                                continue
                            args = invoke_registers(op, words)
                            prev_move = move_object_registers(
                                ins_resume[n-1][1], ins_resume[n-1][2])
                            if (len(args) != 6 or prev_move != (args[5], this_reg)):
                                continue
                            raa_resume_same_continuation = True
                            for k in range(n-2, -1, -1):
                                prior_op, prior_words = ins_resume[k][1:]
                                dest = ((prior_words[0] >> 8) & 15
                                        if prior_op == 0x12
                                        else written_register(prior_op, prior_words))
                                if dest != args[2]:
                                    continue
                                if (const4_zero_to_register(
                                        prior_op, prior_words, args[2])
                                        and not any(
                                            x[1] in (0x28,0x29,0x2a,0x2b,0x2c)
                                            or 0x32 <= x[1] <= 0x3d
                                            for x in ins_resume[k+1:n])):
                                    raa_resume_null_wrapper = True
                                break
                    if method[0] not in (MODEL, WRAPPER) and (
                        MODEL in method[2] or WRAPPER in method[2]
                    ):
                        if len(model_flow_candidates) < MAX_METHODS:
                            flow = straight_line_model_flow(dex, method, flags, code_off)
                            if flow and flow["straight_line_events"]:
                                model_flow_candidates.append(flow)
                    if method[0] == MODEL or MODEL in method[2]:
                        wrapper_flow = wrapper_constructor_input_flow(
                            dex, method, flags, code_off)
                        if wrapper_flow and len(wrapper_constructor_callsites) < MAX_METHODS:
                            wrapper_constructor_callsites.append(wrapper_flow)
                    collector_flow = class_instantiation_and_flow_collect_sites(
                        dex, method, code_off)
                    if collector_flow and len(flow_dispatcher_instantiation_sites) < MAX_METHODS:
                        flow_dispatcher_instantiation_sites.append(collector_flow)
                    ins = list(instructions(dex, code_off))
                    boundary_callsite_rows.extend(
                        boundary_callsite_census(dex, method, flags, code_off, ins)
                    )
                    model_regs = {r for _, r in model_parameter_registers(
                        dex, method, flags, code_off)}
                    for ordinal, (pc, op, words) in enumerate(ins):
                        if op not in INVOKES:
                            continue
                        callee = dex.method(words[1])
                        if (callee[0], callee[1]) in SOURCE_METHODS:
                            if len(target_callers) < MAX_METHODS:
                                regs = invoke_registers(op, words)
                                params = parse_types(callee[2])
                                is_static = op in (0x71, 0x77)
                                target_types = params if is_static else [callee[0]] + params
                                register_types = expand_invoke_register_types(
                                    callee[0], params, is_static
                                )
                                native_track_argument_positions = []
                                if len(regs) == len(register_types):
                                    logical_position = -1
                                    for word_position, typ in enumerate(register_types):
                                        if typ is None:
                                            continue
                                        logical_position += 1
                                        if regs[word_position] in model_regs:
                                            native_track_argument_positions.append(
                                                logical_position
                                            )
                                target_callers.append({
                                    "caller": {"owner": method[0], "name": method[1],
                                               "signature": method[2]},
                                    "target": {"owner": callee[0], "name": callee[1],
                                               "signature": callee[2]},
                                    "argument_registers": regs,
                                    "invoke_kind": "STATIC" if is_static else "INSTANCE_OR_OTHER",
                                    "argument_types": target_types,
                                    "argument_register_types": register_types,
                                    "native_track_argument_positions":
                                        native_track_argument_positions,
                                    "track_id_wrapper_argument_positions": [
                                        i for i, typ in enumerate(target_types) if typ == WRAPPER
                                    ],
                                })
                        if (callee[0], callee[1]) == DESCRIPTOR_BUILDER:
                            if len(descriptor_builder_callers) < MAX_METHODS:
                                descriptor_builder_callers.append({
                                    "caller": {
                                        "owner": method[0],
                                        "name": method[1],
                                        "signature": method[2],
                                    },
                                    "ordinal": ordinal,
                                    "argument_word_count": len(invoke_registers(op, words)),
                                })
    candidate_owner_rows = candidate_owner_descriptors(class_profiles)
    candidate_owner_set = {row["owner"] for row in candidate_owner_rows}
    candidate_owner_method_census = inspect_candidate_owner_methods(
        apks, candidate_owner_set, class_profiles
    )
    candidate_identity_focus_refs = select_candidate_identity_focus_refs(
        candidate_owner_method_census
    )
    candidate_identity_trace_result = inspect_candidate_identity_method_traces(
        apks, candidate_identity_focus_refs, candidate_owner_set, require_all=True
    )
    candidate_identity_method_traces = candidate_identity_trace_result["traces"]
    next_identity_hop_focus_refs = select_next_identity_method_refs(
        candidate_identity_method_traces,
        candidate_identity_focus_refs,
        class_profiles
    )
    next_identity_hop_trace_result = inspect_candidate_identity_method_traces(
        apks, next_identity_hop_focus_refs, candidate_owner_set,
        require_all=False, capture_unproven_calls=True
    )
    next_identity_hop_owner_profiles = [
        {"owner": owner, **classify_track_owner_profile(class_profiles.get(owner, {}))}
        for owner in sorted({row[0] for row in next_identity_hop_focus_refs})
    ]
    coroutine_refs = {
        ("LGp0;", "new",
         "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;"),
        ("LFp0;", "invokeSuspend",
         "(Ljava/lang/Object;)Ljava/lang/Object;")
    }
    if set(fp0_coroutine_method_definitions) != coroutine_refs:
        raise ValueError("TRACK_COROUTINE_CONTINUATION_METHODS_NOT_DEFINED")
    if len({id(row[0]) for row in fp0_coroutine_method_definitions.values()}) != 1:
        raise ValueError("TRACK_COROUTINE_CONTINUATION_CROSS_DEX_UNPROVEN")
    initial_ref=("LGp0;", "new",
        "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;")
    resume_ref=("LFp0;", "invokeSuspend",
        "(Ljava/lang/Object;)Ljava/lang/Object;")
    initial_def=fp0_coroutine_method_definitions[initial_ref]
    resume_def=fp0_coroutine_method_definitions[resume_ref]
    native_track_coroutine_continuity=trace_native_track_coroutine_continuation(
        initial_def[0],initial_ref,initial_def[1],initial_def[2],
        resume_ref,resume_def[1],resume_def[2]
    )
    continuation_field_slots=sorted({
        row["field_slot"]
        for row in native_track_coroutine_continuity["continuation_track_field_reads"]
    })
    if not continuation_field_slots or len(continuation_field_slots)>8:
        raise ValueError("CONTINUATION_TRACK_FIELD_SLOT_SET_INVALID")
    continuation_field_writer_reports=[
        {
            "field_slot":slot,
            "report":inspect_continuation_track_field_writers(
                apks,initial_def[0],slot
            )
        }
        for slot in continuation_field_slots
    ]
    continuation_track_field_writer_census={
        "target_is_LFp0_track_typed_field":all(
            row["report"]["target_is_LFp0_track_typed_field"]
            for row in continuation_field_writer_reports
        ),
        "field_slot_count":len(continuation_field_writer_reports),
        "field_slot_reports":continuation_field_writer_reports,
        "writer_method_count":sum(
            row["report"]["writer_method_count"]
            for row in continuation_field_writer_reports
        ),
        "track_identity_callsite_count":sum(
            row["report"]["track_identity_callsite_count"]
            for row in continuation_field_writer_reports
        ),
        "same_track_parameter_store_candidate":any(
            row["report"].get("same_track_parameter_store_candidate",False)
            for row in continuation_field_writer_reports
        ),
        "same_track_object_capture_into_continuation_field_proven":False,
        "control_flow_feasibility_proven":False,
        "field_names_values_track_ids_or_media_disclosed":False
    }
    if dex_count != 6:
        raise ValueError("SIGNED_SIX_DEX_REQUIRED")
    if not model_defined:
        raise ValueError("NATIVE_TRACK_MODEL_NOT_DEFINED")
    fp0_ctor = [
        t for t in focused_method_traces
        if t["method"] == {
            "owner": "LFp0;", "name": "<init>",
            "signature": "(LGp0;LOe2;)V"
        }
    ]
    fp0_resumes = [
        t for t in focused_method_traces
        if t["method"] == {
            "owner": "LFp0;", "name": "invokeSuspend",
            "signature": "(Ljava/lang/Object;)Ljava/lang/Object;"
        }
    ]
    if len(fp0_ctor) != 1 or len(fp0_resumes) != 1:
        raise ValueError("SIGNED_FP0_COROUTINE_SHAPE_UNPROVEN")
    gp0_resume_calls = [
        i for i in fp0_resumes[0]["instructions"]
        if i["op"] == "INVOKE" and i["callee"] == {
            "owner": "LGp0;", "method": "new",
            "signature": "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;"
        }
    ]
    if (fp0_resumes[0]["this_register"] is None
            or len(gp0_resume_calls) != 1
            or len(gp0_resume_calls[0]["argument_registers"]) != 3
            or gp0_resume_calls[0]["argument_registers"][2]
               != fp0_resumes[0]["this_register"]):
        raise ValueError("SIGNED_FP0_SAME_CONTINUATION_RESUME_UNPROVEN")
    model_methods = sorted(set(model_methods))[:MAX_METHODS]
    album_methods = sorted(set(album_methods))[:MAX_METHODS]
    model_referenced_methods = sorted(set(model_referenced_methods))[:MAX_METHODS]
    wrapper_methods = sorted(wrapper_methods)[:MAX_METHODS]
    player_method_refs = sorted(player_method_refs)[:MAX_METHODS]
    media_session_method_refs = sorted(set(media_session_method_refs))[:MAX_METHODS]
    decoder_boundary_method_refs = sorted(set(decoder_boundary_method_refs))[:MAX_METHODS]
    track_parameter_boundary_roles = {}
    for flow in model_flow_candidates:
        for event in flow.get("straight_line_events", []):
            role = event.get("role", "UNKNOWN")
            track_parameter_boundary_roles[role] = (
                track_parameter_boundary_roles.get(role, 0) + 1
            )
    decoder_owner_dispatch_contracts = inspect_decoder_owner_dispatch_contracts(
        apks, boundary_callsite_rows, class_profiles
    )
    audio_buffer_sink_caller_traces = inspect_audio_buffer_sink_caller_traces(
        apks, decoder_owner_dispatch_contracts, class_profiles
    )
    audio_output_dispatch_census = inspect_audio_output_dispatch_callers(
        apks, audio_buffer_sink_caller_traces, class_profiles
    )
    return {
        "verdict": "SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY",
        "signed_dex_count": dex_count,
        "native_track_model": MODEL,
        "native_track_model_field_names_and_types": [
            {"field": name, "type": typ}
            for name, typ in sorted(model_fields.items())
        ],
        "native_track_model_defined_method_count": len(model_methods),
        "native_track_model_method_examples": [
            {"owner": x[0], "method": x[1], "signature": x[2]}
            for x in model_methods
        ],
        "native_track_model_method_reference_count": len(model_referenced_methods),
        "native_track_model_method_reference_examples": [
            {"owner": x[0], "method": x[1], "signature": x[2]}
            for x in model_referenced_methods
        ],
        "native_track_model_accessor_field_reads": model_accessor_field_reads[:MAX_METHODS],
        "native_album_model": ALBUM_MODEL if album_defined else None,
        "native_track_album_copy_method_static": {
            "copy_methods_with_track_and_album_inputs_and_track_result": sum(
                is_native_track_album_copy_method(method) for method in model_methods),
            "copy_methods_reading_track_album_field": sum(
                is_native_track_album_copy_method(method)
                and any(row["signature"] == method[2]
                        and row["field_type"] == ALBUM_MODEL
                        for row in model_accessor_field_reads)
                for method in model_methods),
            "copy_methods_passing_album_argument_to_track_constructor": sum(
                bool(row and row["album_argument_passed_to_new_track_constructor"])
                for row in track_album_copy_flow_rows),
            "copy_methods_passing_source_track_album_to_track_constructor": sum(
                bool(row and row["source_track_album_passed_to_new_track_constructor"])
                for row in track_album_copy_flow_rows),
            "copy_methods_storing_album_argument_on_new_track": sum(
                bool(row and row["album_argument_stored_on_new_track"])
                for row in track_album_copy_flow_rows),
            "copy_methods_storing_source_track_album_on_new_track": sum(
                bool(row and row["source_track_album_stored_on_new_track"])
                for row in track_album_copy_flow_rows),
            "copy_methods_returning_new_track": sum(
                bool(row and row["returns_new_track"])
                for row in track_album_copy_flow_rows),
            "copy_methods_reading_album_field_from_source_track": sum(
                bool(row and row["reads_album_field_from_source_track"])
                for row in track_album_copy_flow_rows),
            "album_argument_to_returned_track_flow_candidate": (
                len(track_album_copy_flow_rows) == 1
                and bool(track_album_copy_flow_rows[0])
                and (
                    track_album_copy_flow_rows[0]["album_argument_passed_to_new_track_constructor"]
                    or track_album_copy_flow_rows[0]["album_argument_stored_on_new_track"]
                )
                and track_album_copy_flow_rows[0]["returns_new_track"]
            ),
            "private_method_and_field_names_disclosed": False,
        },
        "native_track_album_reference_static": {
            "track_album_typed_field_count": sum(
                typ == ALBUM_MODEL for typ in model_fields.values()),
            "constructors_with_one_album_argument": len(track_album_constructor_rows),
            "constructors_storing_same_album_argument_on_track": sum(
                row["stores_same_album_argument_on_track"]
                for row in track_album_constructor_rows),
            "constructors_passing_album_argument_to_track_methods": sum(
                row["album_argument_passed_to_track_method_count"] > 0
                for row in track_album_constructor_rows),
            "constructors_passing_album_argument_to_other_methods": sum(
                row["album_argument_passed_to_other_method_count"] > 0
                for row in track_album_constructor_rows),
            "constructors_with_album_typed_field_write_on_this": sum(
                row["album_typed_field_write_on_this_count"] > 0
                for row in track_album_constructor_rows),
            "constructors_returning_album_argument": sum(
                row["album_argument_returned"] for row in track_album_constructor_rows),
            "total_album_argument_method_passes": sum(
                row["album_argument_invoke_count"] for row in track_album_constructor_rows),
            "total_album_typed_field_writes": sum(
                row["album_typed_field_write_count"] for row in track_album_constructor_rows),
            "total_album_argument_field_write_receiver_aliases": sum(
                row["album_argument_field_write_receiver_alias_count"]
                for row in track_album_constructor_rows),
            "proven": (
                sum(typ == ALBUM_MODEL for typ in model_fields.values()) == 1
                and len(track_album_constructor_rows) == 2
                and all(row["stores_same_album_argument_on_track"]
                        for row in track_album_constructor_rows)
            ),
            "private_field_names_disclosed": False,
        },
        "native_album_model_field_names_and_types": [
            {"field": name, "type": typ}
            for name, typ in sorted(album_fields.items())
        ],
        "native_album_model_defined_methods": [
            {"owner": x[0], "method": x[1], "signature": x[2]}
            for x in album_methods
        ],
        "native_album_model_accessor_field_reads": album_accessor_field_reads[:MAX_METHODS],
        "track_id_wrapper_method_examples": [
            {"owner": x[0], "method": x[1], "signature": x[2]}
            for x in wrapper_methods
        ],
        "track_id_wrapper_constructor_callsites": wrapper_constructor_callsites,
        "selected_item_source_target_callers": target_callers,
        "flow_dispatcher_class_fields": flow_dispatcher_class_fields,
        "flow_source_interface_methods": [
            {"owner": x[0], "method": x[1], "signature": x[2]}
            for x in sorted(flow_source_interface_methods)[:MAX_METHODS]
        ],
        "flow_dispatcher_instantiation_and_collect_sites": flow_dispatcher_instantiation_sites,
        "focused_native_model_to_wrapper_method_traces": focused_method_traces,
        "coroutine_fp0_trace_candidates_only": [
            t for t in focused_method_traces
            if t["method"]["owner"] == "LFp0;"
        ],
        "fp0_resume_exact_same_continuation_static_proven": True,
        "fp0_resume_explicit_null_track_argument_static_proven": fp0_resume_null_track_arg,
        "fp0_resume_track_binding_runtime_proven": False,
        "native_track_coroutine_continuity": native_track_coroutine_continuity,
        "continuation_track_field_writer_census": continuation_track_field_writer_census,
        "raa_resume_exact_same_continuation_static_proven": raa_resume_same_continuation,
        "raa_resume_explicit_null_wrapper_argument_static_proven": raa_resume_null_wrapper,
        "raa_resume_wrapper_binding_runtime_proven": False,
        "exo_source_class_present_in_signed_2025": exo_source_defined,
        "exo_source_close_void_declared_in_signed_2025":
            exo_source_close_void_declared,
        "download2_main_source_coroutine_candidates_only": [
            t for t in focused_method_traces
            if t["method"]["owner"] in (
                "Lcom/yandex/music/shared/player/download2/o;",
                "Lcom/yandex/music/shared/player/download2/o$c;",
                "LRAa;"
            ) and t["method"]["name"] in ("for", "invokeSuspend", "<init>")
        ],
        "descriptor_builder_callers": descriptor_builder_callers,
        "public_player_selection_method_refs": [
            {"owner": x[0], "method": x[1], "signature": x[2]}
            for x in player_method_refs
        ],
        "selected_state_static_summary": {
            "media_session_metadata_method_reference_count": sum(
                x[1] in MEDIA_SESSION_METADATA_METHODS
                for x in media_session_method_refs
            ),
            "media_session_state_method_reference_count": sum(
                x[1] in MEDIA_SESSION_STATE_METHODS
                for x in media_session_method_refs
            ),
            "decoder_boundary_method_reference_count": len(decoder_boundary_method_refs),
            "track_parameter_to_player_selection_call_count":
                track_parameter_boundary_roles.get("PLAYER_SELECTION_OR_TRANSPORT", 0),
            "track_parameter_to_media_session_metadata_call_count":
                track_parameter_boundary_roles.get("MEDIA_SESSION_METADATA_PUBLISH", 0),
            "track_parameter_to_media_session_state_call_count":
                track_parameter_boundary_roles.get("MEDIA_SESSION_STATE_PUBLISH", 0),
            "track_parameter_to_decoder_boundary_call_count":
                track_parameter_boundary_roles.get("DECODER_INPUT_OR_RENDERER_BOUNDARY", 0),
            "track_parameter_to_native_descriptor_call_count":
                track_parameter_boundary_roles.get("NATIVE_DESCRIPTOR_BUILDER", 0),
            "edition_type_descriptor_count": semantic_marker_counts.get("edition", 0),
            "generation_type_descriptor_count": semantic_marker_counts.get("generation", 0),
            "track_model_edition_typed_field_count": sum(
                "edition" in typ.lower() for typ in model_fields.values()
            ),
            "album_model_edition_typed_field_count": sum(
                "edition" in typ.lower() for typ in album_fields.values()
            ),
            "track_model_edition_named_field_count": sum(
                name.lower() in EDITION_MARKERS for name in model_fields
            ),
            "album_model_edition_named_field_count": sum(
                name.lower() in EDITION_MARKERS for name in album_fields
            ),
            "track_model_generation_named_field_count": sum(
                name.lower() in GENERATION_MARKERS for name in model_fields
            ),
            "album_model_generation_named_field_count": sum(
                name.lower() in GENERATION_MARKERS for name in album_fields
            ),
            "same_track_album_edition_generation_owner_proven": False,
            "active_selected_item_proven": False,
            "same_native_item_to_decoder_proven": False,
            "branch_and_indirect_dispatch_inferred": False,
        },
        "native_track_field_owner_inventory":
            summarize_track_field_owner_inventory(class_profiles),
        "track_album_shared_owner_candidates": candidate_owner_rows,
        "track_shared_owner_method_census": candidate_owner_method_census,
        "candidate_identity_focus_method_traces": candidate_identity_method_traces,
        "next_identity_hop_focus_method_refs": [
            {"owner": x[0], "method": x[1], "signature": x[2]}
            for x in next_identity_hop_focus_refs
        ],
        "next_identity_hop_method_traces": next_identity_hop_trace_result["traces"],
        "next_identity_hop_missing_method_refs":
            next_identity_hop_trace_result["missing_method_refs"],
        "next_identity_hop_owner_profiles": next_identity_hop_owner_profiles,
        "boundary_callsite_identity_census":
            summarize_boundary_callsite_census(boundary_callsite_rows, class_profiles),
        "boundary_callsite_owner_profiles":
            summarize_boundary_callsite_owner_profiles(boundary_callsite_rows, class_profiles),
        "boundary_caller_inbound_methods":
            inspect_boundary_caller_inbound_methods(apks, boundary_callsite_rows, class_profiles),
        "decoder_owner_dispatch_contracts": decoder_owner_dispatch_contracts,
        "audio_buffer_sink_caller_traces": audio_buffer_sink_caller_traces,
        "audio_output_dispatch_census": audio_output_dispatch_census,
        "same_basic_block_model_parameter_flows": model_flow_candidates,
        "active_selected_item_proven": False,
        "same_native_item_to_decoder_proven": False,
        "current_song_or_audio_accessed": False,
        "original_apk_modified_or_exported": False,
    }


def run(xapk: Path):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size != PINNED_XAPK_BYTES:
        raise ValueError("PINNED_2025_XAPK_SIZE_MISMATCH")
    digest = hashlib.sha256(xapk.read_bytes()).hexdigest()
    if digest != PINNED_XAPK_SHA256:
        raise ValueError("PINNED_2025_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-native-selected-item-audit-") as temp:
        folder = Path(temp)
        apks = unbundle_candidate(xapk, folder)
        if not 1 <= len(apks) <= 20:
            raise ValueError("2025_SIGNED_SPLIT_COUNT_OUT_OF_RANGE")
        publisher = verify_split_set(apks)
        report = inspect_signed(apks)
    return {
        **report,
        "publisher_version": PUBLISHER_VERSION,
        "signed_split_count": len(apks),
        "publisher_signature_verification": publisher,
        "pinned_archive_sha256_verified": True,
        "no_login_no_user_media_no_decoder_mutation": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xapk", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.xapk), sort_keys=True, ensure_ascii=False))
    except (RuntimeError, ValueError, DexError, OSError, zipfile.BadZipFile) as exc:
        reason = str(exc)
        safe_code = reason if re.fullmatch(r"[A-Z0-9_]{1,80}", reason) else None
        print(json.dumps({
            "verdict": "SIGNED_NATIVE_SELECTED_ITEM_AUDIT_INCOMPLETE",
            "error_class_only": type(exc).__name__,
            "safe_error_code": safe_code,
            "active_selected_item_proven": False,
            "no_vendor_binary_exported": True,
        }))
        raise SystemExit(2)
