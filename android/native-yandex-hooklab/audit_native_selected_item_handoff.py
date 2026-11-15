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
        access_flags=dex.u32(base+4)
        profiles[owner] = {
            "static_types": set(static_types),
            "instance_types": set(instance_types),
            "superclass": superclass,
            "interfaces": interfaces,
            "access_flags":access_flags,
            "is_interface":bool(access_flags&0x200),
            "is_abstract":bool(access_flags&0x400),
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
    capture_unproven_calls=False, focus_targets=None,
    exact_track_field_refs=None, extra_identity_types=None,
    track_fields_from_any_receiver=False
):
    """Trace only typed Track/Album/wrapper aliases and exact focus callsites."""
    candidate_owners = candidate_owners or set()
    focus_targets = set(focus_targets or ())
    tracked_types = {
        MODEL: "TRACK",
        ALBUM_MODEL: "ALBUM",
        WRAPPER: "TRACK_WRAPPER",
    }
    for extra_type in sorted(set(extra_identity_types or ())):
        if not isinstance(extra_type, str) or not extra_type.startswith(("L", "[")):
            raise ValueError("EXTRA_IDENTITY_TYPE_INVALID")
        tracked_types.setdefault(extra_type, f"EXTRA_OBJECT:{extra_type}")
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
                        # Object identity cannot flow into a primitive DEX parameter.
                        # Rejecting primitive targets prevents stale-register false positives.
                        if origins and (
                            declared_type.startswith("L")
                            or declared_type.startswith("[")
                        ):
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
        if op == 0x22:  # new-instance: retain exact object identity, never inspect contents
            dest = words[0] >> 8
            object_type = dex.descriptor(words[1])
            clear_register(dest)
            if object_type in tracked_types:
                aliases[object_type][dest] = {f"NEW_INSTANCE_AT_{ordinal}"}
                add_event({
                    "ordinal": ordinal,
                    "kind": "NEW_INSTANCE_TYPED_IDENTITY",
                    "identity_type": tracked_types[object_type],
                })
            continue

        if op == 0x62:  # sget-object: type-only static object origin
            dest = words[0] >> 8
            field_ref = field_id(dex, words[1])
            field_type = field_ref[2]
            clear_register(dest)
            if (
                field_type in tracked_types
                and (
                    exact_track_field_refs is None
                    or field_ref in exact_track_field_refs
                )
            ):
                aliases[field_type][dest] = {"STATIC_FIELD_READ"}
                add_event({
                    "ordinal": ordinal,
                    "kind": "STATIC_FIELD_READ_TYPED_IDENTITY",
                    "identity_type": tracked_types[field_type],
                })
            continue

        if op == 0x54:  # iget-object: inspect type and receiver, never field value
            dest = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            field_ref = field_id(dex, words[1])
            _field_owner, _field_name, field_type = field_ref
            clear_register(dest)
            if (
                field_type in tracked_types
                and (receiver == this_register or track_fields_from_any_receiver)
                and (
                    exact_track_field_refs is None
                    or field_ref in exact_track_field_refs
                )
            ):
                origin = (
                    "FIELD_READ_FROM_THIS"
                    if receiver == this_register
                    else "FIELD_READ_FROM_OTHER_RECEIVER"
                )
                aliases[field_type][dest] = {origin}
                add_event({
                    "ordinal": ordinal,
                    "kind": "FIELD_READ_TYPED_IDENTITY",
                    "identity_type": tracked_types[field_type],
                    "receiver_is_this": receiver == this_register,
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


def trace_exact_track_field_method_cfg(
    dex, method, flags, code_off, exact_track_field_refs
):
    """Branch-sensitive must-alias trace from one exact Track field to method calls."""
    cfg = build_dex_control_flow(dex, code_off)
    by_pc = cfg["by_pc"]
    successors = cfg["successors"]
    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        raise DexError("EXACT_TRACK_CFG_INVALID_INS_SIZE")
    initial_registers = {}
    if not (flags & ACC_STATIC):
        initial_registers[registers_size - ins_size] = frozenset({"OWNER_THIS"})
    for register in typed_parameter_registers(
        dex, method, flags, code_off, MODEL
    ):
        initial_registers[register] = frozenset({"TRACK_PARAMETER"})
    initial_state = {"registers": initial_registers, "pending_return": None}

    def state_key(state):
        return (
            tuple(
                (register, tuple(sorted(origins)))
                for register, origins in sorted(state["registers"].items())
            ),
            state["pending_return"],
        )

    incoming = {
        cfg["entry"]: {state_key(initial_state): initial_state}
    }
    work = [(cfg["entry"], state_key(initial_state))]
    processed = 0
    wide_ops = (
        {0x04,0x05,0x06,0x0b,0x16,0x17,0x18,0x19,0x45,0x53,0x61,
         0x7d,0x7e,0x80,0x82,0x85,0x87,0x88,0x8a}
        | set(range(0x9b,0xa6)) | set(range(0xab,0xb0))
        | set(range(0xbb,0xc6)) | set(range(0xcb,0xd0))
    )

    def transfer(state, op, words):
        registers = {
            register: set(origins)
            for register, origins in state["registers"].items()
        }
        pending_return = None

        def clear(register):
            registers.pop(register, None)

        if op in INVOKES:
            callee = dex.method(words[1])
            result_type = callee[2].split(")", 1)[1]
            pending_return = result_type if result_type == MODEL else None
        elif op == 0x0c:  # move-result-object
            destination = words[0] >> 8
            clear(destination)
            if state["pending_return"] == MODEL:
                registers[destination] = {"TRACK_RETURNED_FROM_METHOD"}
        elif op == 0x54:  # iget-object
            destination = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            field_ref = field_id(dex, words[1])
            receiver_origins = registers.get(receiver, set())
            clear(destination)
            if (
                field_ref in exact_track_field_refs
                and "OWNER_THIS" in receiver_origins
            ):
                registers[destination] = {"TRACK_FROM_EXACT_FIELD"}
        elif op in (0x5b, 0x67):  # iput-object / sput-object
            owner, _field_name, typ = field_id(dex, words[1])
            value_register = (
                (words[0] >> 8) & 15 if op == 0x5b
                else (words[0] >> 8) & 0xff
            )
            receiver_register = (
                (words[0] >> 12) & 15 if op == 0x5b else None
            )
            this_register = (
                None if flags & ACC_STATIC
                else dex.u16(code_off) - dex.u16(code_off + 2)
            )
            origin = local_object_register_origin(
                dex, method, flags, code_off, ins, ordinal,
                value_register, include_source_ordinal=True
            )
            origin.pop("field", None)
            rows.append({
                "ordinal": ordinal, "op": "FIELD_WRITE",
                "owner": owner, "type": typ,
                "receiver_is_this": receiver_register == this_register
                    if receiver_register is not None else False,
                "value_is_native_track_parameter": value_register in aliases,
                "value_origin": origin,
            })
        elif op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            if move is not None:
                destination, source = move
                origins = set(registers.get(source, set()))
                clear(destination)
                if origins:
                    registers[destination] = origins
        elif op == 0x1f:  # check-cast preserves object identity
            pass
        elif op == 0x5b:  # iput-object does not mutate the source register
            pass
        else:
            destination = written_register(op, words)
            if destination is not None:
                clear(destination)
                if op in wide_ops:
                    clear(destination + 1)

        return {
            "registers": {
                register: frozenset(origins)
                for register, origins in registers.items() if origins
            },
            "pending_return": pending_return,
        }

    while work:
        pc, key = work.pop()
        processed += 1
        if processed > 200000:
            raise ValueError("EXACT_TRACK_CFG_DATAFLOW_LIMIT")
        state = incoming[pc][key]
        op, words = by_pc[pc]
        output = transfer(state, op, words)
        output_key = state_key(output)
        for target in successors.get(pc, ()):
            bucket = incoming.setdefault(target, {})
            if output_key in bucket:
                continue
            if len(bucket) >= 128:
                raise ValueError("EXACT_TRACK_CFG_PATH_STATE_LIMIT")
            bucket[output_key] = output
            work.append((target, output_key))

    def common_origins(states, register):
        if not states:
            return set()
        common = set(states[0]["registers"].get(register, ()))
        for state in states[1:]:
            common.intersection_update(state["registers"].get(register, ()))
        return common

    events = []
    seen_events = set()

    def add_event(event):
        key = json.dumps(event, sort_keys=True)
        if key in seen_events:
            return
        if len(events) >= 256:
            raise ValueError("EXACT_TRACK_CFG_EVENT_LIMIT")
        seen_events.add(key)
        events.append(event)

    tracked_labels = {
        "TRACK_FROM_EXACT_FIELD": "TRACK",
        "TRACK_PARAMETER": "TRACK",
        "TRACK_RETURNED_FROM_METHOD": "TRACK_RETURNED_FROM_METHOD",
    }
    for pc in sorted(cfg["reachable"]):
        op, words = by_pc[pc]
        states = list(incoming.get(pc, {}).values())
        if not states:
            continue
        if op == 0x54:
            destination = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            field_ref = field_id(dex, words[1])
            if (
                field_ref in exact_track_field_refs
                and "OWNER_THIS" in common_origins(states, receiver)
            ):
                add_event({
                    "pc": pc,
                    "kind": "FIELD_READ_TYPED_IDENTITY",
                    "identity_type": "TRACK",
                    "receiver_is_this_on_all_paths": True,
                })
            continue
        if op not in INVOKES:
            continue
        callee = dex.method(words[1])
        registers = invoke_registers(op, words)
        params = parse_types(callee[2])
        is_static = op in (0x71, 0x77)
        target_types = expand_invoke_register_types(
            callee[0], params, is_static
        )
        identity_arguments = []
        if len(registers) == len(target_types):
            logical_position = -1
            for declared_type, register in zip(target_types, registers):
                if declared_type is None:
                    continue
                logical_position += 1
                if not (declared_type.startswith("L") or declared_type.startswith("[")):
                    continue
                origins = common_origins(states, register)
                for origin, label in tracked_labels.items():
                    if origin in origins:
                        identity_arguments.append({
                            "argument_position": logical_position,
                            "declared_argument_type": declared_type,
                            "identity_type": label,
                            "origins": [origin],
                            "same_exact_track_field_identity": (
                                origin == "TRACK_FROM_EXACT_FIELD"
                            ),
                        })
        role = None
        if callee == DESCRIPTOR_BUILDER:
            role = "NATIVE_SOURCE_DESCRIPTOR"
        elif (callee[0], callee[1]) in SOURCE_METHODS:
            role = "NATIVE_SOURCE_OR_DOWNLOAD_METHOD"
        elif callee[0] in PLAYER_OWNERS and callee[1] in PLAYER_METHODS:
            role = "PLAYER_SELECTION_OR_TRANSPORT"
        else:
            role = classify_boundary_call(callee)
            if not role and callee[1] in ("collect", "collectLatest", "launchIn", "emit"):
                role = "FLOW_COLLECT_OR_EMIT"
        if identity_arguments:
            add_event({
                "pc": pc,
                "kind": "CALL_WITH_TYPED_IDENTITY",
                "callee": {
                    "owner": callee[0],
                    "method": callee[1],
                    "signature": callee[2],
                },
                "identity_arguments": identity_arguments,
                "role": role or "OTHER_METHOD",
                "identity_is_common_to_all_incoming_paths": True,
            })
        elif role:
            add_event({
                "pc": pc,
                "kind": "CALL_TARGET_ROLE_WITHOUT_IDENTITY",
                "callee": {
                    "owner": callee[0],
                    "method": callee[1],
                    "signature": callee[2],
                },
                "role": role,
                "identity_proven": False,
            })
        result_type = callee[2].split(")", 1)[1]
        if result_type == MODEL:
            add_event({
                "pc": pc,
                "kind": "CALL_RETURNING_TYPED_IDENTITY",
                "identity_type": "TRACK",
                "callee": {
                    "owner": callee[0],
                    "method": callee[1],
                    "signature": callee[2],
                },
            })

    return {
        "method": {
            "owner": method[0],
            "method": method[1],
            "signature": method[2],
        },
        "events": events,
        "reachable_instruction_count": len(cfg["reachable"]),
        "branch_count": len(cfg["branches"]),
        "path_state_count": sum(len(states) for states in incoming.values()),
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


def trace_renderer_buffer_field_identity_cfg(
    dex, method, flags, code_off, target_fields, field_slots, sink_targets
):
    """Trace one exact Lad6.final ByteBuffer through a same-instance field to dispatch.

    This is path-sensitive method-local object identity. Different CFG states and
    alternate stores remain separate. It does not model external writes,
    re-entrant calls, exception edges, or runtime virtual dispatch.
    """
    byte_buffer = "Ljava/nio/ByteBuffer;"
    lad6_final = ("Lad6;", "final", "(I)Ljava/nio/ByteBuffer;")
    target_fields = set(target_fields)
    sink_targets = set(sink_targets)
    if not target_fields:
        return {
            "trace_status": "NO_TARGET_FIELDS",
            "method_local_identity_proven": False,
            "private_field_names_or_values_disclosed": False,
        }

    try:
        cfg = build_dex_control_flow(dex, code_off)
    except (DexError, ValueError):
        return {
            "trace_status": "CFG_UNAVAILABLE",
            "method_local_identity_proven": False,
            "private_field_names_or_values_disclosed": False,
        }

    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        return {
            "trace_status": "INVALID_REGISTER_LAYOUT",
            "method_local_identity_proven": False,
            "private_field_names_or_values_disclosed": False,
        }
    if flags & ACC_STATIC:
        return {
            "trace_status": "NO_INSTANCE_RECEIVER",
            "method_local_identity_proven": False,
            "private_field_names_or_values_disclosed": False,
        }

    this_register = registers_size - ins_size
    initial_state = {
        "registers": {this_register: ("THIS",)},
        "fields": {},
        "pending_return": None,
    }

    def state_key(state):
        register_key = tuple(sorted(
            (register, repr(alias))
            for register, alias in state["registers"].items()
        ))
        field_key = tuple(sorted(
            (field_slots[field_ref], repr(value))
            for field_ref, value in state["fields"].items()
        ))
        return register_key, field_key, repr(state["pending_return"])

    def buffer_origin(alias):
        if not alias:
            return None
        if alias[0] == "BUFFER_RETURN":
            return alias[1]
        if alias[0] == "FIELD_READ":
            return alias[4]
        return None

    def origin_kind(origin):
        if origin and origin[0] == "LAD6_FINAL":
            return "LAD6_FINAL"
        if origin and origin[0] == "OTHER_BYTEBUFFER_RETURN":
            return "OTHER_BYTEBUFFER_RETURN"
        return "UNKNOWN"

    store_events = {}
    read_events = {}

    def remember(bucket, row):
        bucket[json.dumps(row, sort_keys=True)] = row

    wide_destination_ops = (
        {0x04, 0x05, 0x06, 0x0b, 0x16, 0x17, 0x18, 0x19,
         0x45, 0x53, 0x61, 0x7d, 0x7e, 0x80, 0x82, 0x85, 0x87,
         0x88, 0x8a}
        | set(range(0x9b, 0xa6))
        | set(range(0xab, 0xb0))
        | set(range(0xbb, 0xc6))
        | set(range(0xcb, 0xd0))
    )

    def transfer(state, pc, op, words):
        registers = dict(state["registers"])
        fields = dict(state["fields"])
        pending_return = None

        if op in INVOKES:
            callee = dex.method(words[1])
            if callee[2].split(")", 1)[1] == byte_buffer:
                origin = (
                    ("LAD6_FINAL", pc)
                    if callee == lad6_final
                    else ("OTHER_BYTEBUFFER_RETURN", pc)
                )
                pending_return = ("BUFFER_RETURN", origin)
        elif op == 0x0c:  # move-result-object
            destination = words[0] >> 8
            registers.pop(destination, None)
            if state["pending_return"] is not None:
                registers[destination] = state["pending_return"]
        elif op == 0x22:  # new-instance; distinct from this
            destination = (words[0] >> 8) & 0xff
            registers[destination] = ("NEW_INSTANCE", pc)
        elif op == 0x54:  # iget-object
            destination = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            field_ref = field_id(dex, words[1])
            registers.pop(destination, None)
            if field_ref in target_fields and field_ref[2] == byte_buffer:
                receiver_alias = registers.get(receiver)
                if receiver_alias == ("THIS",):
                    stored = fields.get(field_ref)
                    if stored is None:
                        origin, store_pc = None, None
                    else:
                        origin, store_pc = stored
                    registers[destination] = (
                        "FIELD_READ", field_ref, store_pc, pc, origin
                    )
                    remember(read_events, {
                        "pc": pc,
                        "field_slot": field_slots[field_ref],
                        "receiver_kind": "THIS",
                        "store_pc": store_pc,
                        "value_origin": origin_kind(origin),
                        "source_call_pc": origin[1] if origin else None,
                    })
                else:
                    receiver_kind = (
                        "OTHER_NEW_INSTANCE"
                        if receiver_alias and receiver_alias[0] == "NEW_INSTANCE"
                        else "UNKNOWN_MAY_ALIAS"
                    )
                    registers[destination] = (
                        "FIELD_READ_UNKNOWN_RECEIVER", field_ref, None, pc, None
                    )
                    remember(read_events, {
                        "pc": pc,
                        "field_slot": field_slots[field_ref],
                        "receiver_kind": receiver_kind,
                        "store_pc": None,
                        "value_origin": "UNKNOWN",
                        "source_call_pc": None,
                    })
        elif op == 0x5b:  # iput-object; field identifiers remain internal
            value_register = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            field_ref = field_id(dex, words[1])
            if field_ref in target_fields and field_ref[2] == byte_buffer:
                receiver_alias = registers.get(receiver)
                value_origin = buffer_origin(registers.get(value_register))
                if receiver_alias == ("THIS",):
                    fields[field_ref] = (value_origin, pc)
                    receiver_kind = "THIS"
                elif receiver_alias and receiver_alias[0] == "NEW_INSTANCE":
                    receiver_kind = "OTHER_NEW_INSTANCE"
                else:
                    # An unresolved receiver may alias this; invalidate the
                    # current field value rather than carrying a false proof.
                    fields[field_ref] = (None, pc)
                    receiver_kind = "UNKNOWN_MAY_ALIAS"
                remember(store_events, {
                    "pc": pc,
                    "field_slot": field_slots[field_ref],
                    "receiver_kind": receiver_kind,
                    "value_origin": origin_kind(value_origin),
                    "source_call_pc": (
                        value_origin[1] if value_origin else None
                    ),
                })
        elif op in (0x07, 0x08, 0x09):  # move-object
            move = move_object_registers(op, words)
            if move:
                destination, source = move
                origin = registers.get(source)
                registers.pop(destination, None)
                if origin is not None:
                    registers[destination] = origin
        elif op == 0x1f:  # check-cast preserves identity
            pass
        else:
            destination = written_register(op, words)
            if destination is not None:
                registers.pop(destination, None)
                if op in wide_destination_ops:
                    registers.pop(destination + 1, None)

        return {
            "registers": registers,
            "fields": fields,
            "pending_return": pending_return,
        }

    incoming = {
        cfg["entry"]: {state_key(initial_state): initial_state}
    }
    work = [(cfg["entry"], state_key(initial_state))]
    processed = 0
    while work:
        pc, key = work.pop()
        processed += 1
        if processed > 200000:
            raise ValueError("RENDERER_BUFFER_CFG_DATAFLOW_LIMIT")
        state = incoming[pc][key]
        op, words = cfg["by_pc"][pc]
        output = transfer(state, pc, op, words)
        output_key = state_key(output)
        for next_pc in cfg["successors"].get(pc, ()):
            bucket = incoming.setdefault(next_pc, {})
            if output_key in bucket:
                continue
            if len(bucket) >= 128:
                raise ValueError("RENDERER_BUFFER_CFG_PATH_STATE_LIMIT")
            bucket[output_key] = output
            work.append((next_pc, output_key))

    sink_calls = []
    for pc in sorted(cfg["reachable"]):
        op, words = cfg["by_pc"][pc]
        if op not in INVOKES:
            continue
        callee = dex.method(words[1])
        if callee not in sink_targets:
            continue
        registers = invoke_registers(op, words)
        argument_types = expand_invoke_register_types(
            callee[0], parse_types(callee[2]), op in (0x71, 0x77)
        )
        states = sorted(
            incoming.get(pc, {}).values(),
            key=state_key,
        )
        path_rows = []
        matched_state_count = 0
        if len(registers) == len(argument_types):
            for state_index, state in enumerate(states):
                state_matched = False
                logical_argument_position = -1
                for register_word_position, (argument_type, register) in enumerate(
                    zip(argument_types, registers)
                ):
                    if argument_type is None:
                        continue
                    logical_argument_position += 1
                    if argument_type != byte_buffer:
                        continue
                    alias = state["registers"].get(register)
                    row = {
                        "state_index": state_index,
                        "argument_position": logical_argument_position,
                        "register_word_position": register_word_position,
                        "status": "UNRESOLVED",
                        "field_slot": None,
                        "source_call_pc": None,
                        "store_pc": None,
                        "read_pc": None,
                        "sink_pc": pc,
                    }
                    if alias and alias[0] == "FIELD_READ":
                        field_ref, store_pc, read_pc, origin = (
                            alias[1], alias[2], alias[3], alias[4]
                        )
                        row["field_slot"] = field_slots[field_ref]
                        row["store_pc"] = store_pc
                        row["read_pc"] = read_pc
                        if origin:
                            row["source_call_pc"] = origin[1]
                            row["status"] = (
                                "LAD6_FINAL_FIELD_REFERENCE"
                                if origin[0] == "LAD6_FINAL"
                                else "ALTERNATE_BYTEBUFFER_RETURN"
                            )
                        else:
                            row["status"] = "UNKNOWN_OR_OVERWRITTEN_FIELD_VALUE"
                    elif alias and alias[0] == "FIELD_READ_UNKNOWN_RECEIVER":
                        row["status"] = "FIELD_READ_RECEIVER_UNRESOLVED"
                        row["field_slot"] = field_slots.get(alias[1])
                        row["read_pc"] = alias[3]
                    elif alias and alias[0] == "BUFFER_RETURN":
                        row["status"] = "DIRECT_RETURN_NOT_FIELD_BRIDGE"
                        origin = alias[1]
                        row["source_call_pc"] = origin[1]
                    path_rows.append(row)
                    if row["status"] == "LAD6_FINAL_FIELD_REFERENCE":
                        state_matched = True
                if state_matched:
                    matched_state_count += 1
        else:
            path_rows = [{
                "state_index": index,
                "status": "INVOKE_REGISTER_MAP_UNRESOLVED",
                "sink_pc": pc,
            } for index, _state in enumerate(states)]

        unmatched_state_count = max(0, len(states) - matched_state_count)
        matching_rows = [
            row for row in path_rows
            if row.get("status") == "LAD6_FINAL_FIELD_REFERENCE"
        ]
        source_call_pcs = sorted({
            row["source_call_pc"] for row in matching_rows
            if row.get("source_call_pc") is not None
        })
        field_slots_seen = sorted({
            row["field_slot"] for row in matching_rows
            if row.get("field_slot") is not None
        })
        sink_calls.append({
            "sink_pc": pc,
            "target": {
                "owner": callee[0],
                "method": callee[1],
                "signature": callee[2],
            },
            "invoke_kind": invoke_kind_name(op),
            "distinct_incoming_identity_state_count": len(states),
            "lad6_final_identity_state_count": matched_state_count,
            "other_or_unresolved_identity_state_count": unmatched_state_count,
            "same_lad6_final_field_reference_on_every_state": (
                bool(states) and matched_state_count == len(states)
            ),
            "same_source_callsite_pc_on_every_matching_state": (
                bool(matching_rows) and len(source_call_pcs) == 1
            ),
            "field_slots_on_matching_states": field_slots_seen,
            "identity_paths": matching_rows[:64],
            "unresolved_or_alternate_paths": [
                row for row in path_rows
                if row.get("status") != "LAD6_FINAL_FIELD_REFERENCE"
            ][:64],
            "path_details_truncated": len(path_rows) > 128,
        })

    return {
        "trace_status": "CFG_TRACED",
        "method": {
            "owner": method[0],
            "method": method[1],
            "signature": method[2],
        },
        "tracked_source_method": {
            "owner": lad6_final[0],
            "method": lad6_final[1],
            "signature": lad6_final[2],
        },
        "branch_count": len(cfg["branches"]),
        "reachable_instruction_count": len(cfg["reachable"]),
        "processed_identity_states": processed,
        "field_store_sites": sorted(
            store_events.values(),
            key=lambda row: (row["pc"], row["field_slot"], row["receiver_kind"])
        ),
        "field_read_sites": sorted(
            read_events.values(),
            key=lambda row: (row["pc"], row["field_slot"], row["receiver_kind"])
        ),
        "sink_callsite_count": len(sink_calls),
        "sink_calls": sink_calls,
        "method_local_identity_proven": any(
            row["lad6_final_identity_state_count"] > 0 for row in sink_calls
        ),
        "all_sink_callsite_states_match": (
            bool(sink_calls)
            and all(
                row["same_lad6_final_field_reference_on_every_state"]
                for row in sink_calls
            )
        ),
        "exception_handler_edges_included": False,
        "external_field_mutation_or_reentrant_calls_modeled": False,
        "runtime_virtual_dispatch_to_native_sink_proven": False,
        "active_selected_item_proven": False,
        "same_native_item_to_decoder_proven": False,
        "private_field_names_or_values_disclosed": False,
        "audio_bytes_read": False,
    }


def inspect_renderer_buffer_field_writers(apks, caller_definitions, sink_targets):
    """Find exact xrefs to renderer ByteBuffer fields across bounded methods.

    Distinguishes same declared field from same runtime object; only the two
    requested renderer methods receive the branch-sensitive CFG identity trace.
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
    cfg_traces = []
    cfg_methods = {
        ("LcC0;", "n", "(JJ)Z"),
        ("Lkd6;", "n", "(JJ)Z"),
    }
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("RENDERER_BUFFER_WRITER_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                for method, flags, code_off in method_definitions_with_flags(dex):
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
                    if method in cfg_methods:
                        cfg_traces.append(
                            trace_renderer_buffer_field_identity_cfg(
                                dex, method, flags, code_off,
                                reader_fields, slots, sink_targets
                            )
                        )
    return {
        "reader_field_slot_count": len(reader_fields),
        "exact_field_writer_method_count": len(rows),
        "exact_field_writer_methods": rows,
        "exact_lad6_final_cfg_identity_traces": cfg_traces,
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
        switch_cases=[]
        if op==0x28:
            fallthrough=[]
            targets=[pc+signed_branch_offset((words[0]>>8)&0xff,8)]
        elif op==0x29:
            fallthrough=[]
            targets=[pc+signed_branch_offset(words[1],16)]
        elif op==0x2a:
            fallthrough=[]
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
                first_key=payload_words[2]|(payload_words[3]<<16)
                if first_key&0x80000000:
                    first_key-=0x100000000
                keys=[first_key+n for n in range(count)]
            elif tag==2:
                target_start=2+2*count
                keys=[]
                for n in range(count):
                    raw_key=payload_words[2+2*n]|(payload_words[3+2*n]<<16)
                    if raw_key&0x80000000:
                        raw_key-=0x100000000
                    keys.append(raw_key)
            else:
                raise ValueError("TRACK_COROUTINE_CFG_SWITCH_PAYLOAD_TYPE")
            for n in range(count):
                at=target_start+2*n
                raw_target=payload_words[at]|(payload_words[at+1]<<16)
                target_pc=pc+signed_branch_offset(raw_target,32)
                targets.append(target_pc)
                switch_cases.append({"key":keys[n],"target_pc":target_pc})
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
                "fallthrough_pcs":fallthrough,
                "switch_cases":switch_cases
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

    resume_ins=list(instructions(dex,resume_code_off))
    resume_null_track_callsite=False
    resume_call_witnesses=[]
    for resume_index,(_resume_pc,resume_op,resume_words) in enumerate(resume_ins):
        if resume_op not in INVOKES or dex.method(resume_words[1])!=(
            "LGp0;","new",
            "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;"
        ):
            continue
        resume_args=invoke_registers(resume_op,resume_words)
        track_arg_register=resume_args[1] if len(resume_args)==3 else None
        explicit_null=(
            track_arg_register is not None and resume_index>0
            and const4_zero_to_register(
                resume_ins[resume_index-1][1],
                resume_ins[resume_index-1][2],
                track_arg_register
            )
        )
        resume_call_witnesses.append({
            "ordinal":resume_index,
            "track_argument_register":track_arg_register,
            "track_argument_is_explicit_null":explicit_null
        })
    resume_null_track_callsite=bool(resume_call_witnesses) and all(
        row["track_argument_is_explicit_null"] for row in resume_call_witnesses
    )

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
                if resume_null_track_callsite:
                    for alias_register,track_origins in regs.items():
                        if "ORIGINAL_TRACK_PARAMETER" in track_origins:
                            track_origins.discard("ORIGINAL_TRACK_PARAMETER")
                            track_origins.add("NULL_TRACK_ARGUMENT_ON_EXACT_Fp0_RESUME")
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
    raw_track_field_store_sites=[]
    reads=[]
    string_reads=[]
    wrapper_ctors=[]
    wrapper_handoffs=[]
    continuation_handoffs=[]
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
    seen_continuation_handoff_events=set()
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
            if field_type==MODEL:
                raw_row={
                    "pc":pc,"field_slot":words[1],
                    "field_owner":field_owner,
                    "receiver_register":receiver,
                    "receiver_origins":sorted(receiver_origins),
                    "source_register":value,
                    "source_origins":sorted(value_origins),
                    "register_origin_state":{
                        str(reg):sorted(origins)
                        for reg,origins in sorted(state.items())
                    }
                }
                if raw_row not in raw_track_field_store_sites:
                    raw_track_field_store_sites.append(raw_row)
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
            params=parse_types(callee[2])
            target_types=expand_invoke_register_types(
                callee[0],params,op in (0x71,0x77)
            )
            for argument_position,argument_type in enumerate(target_types):
                if argument_type not in (continuation_owner,continuation_type):
                    continue
                argument_origins=state.get(args[argument_position],frozenset())
                is_new="NEW_LFp0_CONTINUATION" in argument_origins
                is_reused="REUSED_LFp0_CONTINUATION" in argument_origins
                if not (is_new or is_reused):
                    continue
                row={
                    "pc":pc,
                    "target":{"owner":callee[0],"method":callee[1],"signature":callee[2]},
                    "argument_position":argument_position,
                    "argument_type":argument_type,
                    "argument_origins":sorted(argument_origins),
                    "same_new_continuation_object_argument":is_new,
                    "same_reused_continuation_object_argument":is_reused
                }
                key=(pc,callee,argument_position,tuple(row["argument_origins"]))
                if key not in seen_continuation_handoff_events:
                    if len(continuation_handoffs)>=64:
                        raise ValueError("TRACK_COROUTINE_CONTINUATION_HANDOFF_LIMIT")
                    seen_continuation_handoff_events.add(key)
                    continuation_handoffs.append(row)

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
    for ordinal,(_pc,op,words) in enumerate(resume_ins):
        if op not in INVOKES or dex.method(words[1])!=coroutine_resume_call:
            continue
        regs=invoke_registers(op,words)
        null_witness=next(
            (row for row in resume_call_witnesses if row["ordinal"]==ordinal),None
        )
        resume_calls.append({
            "ordinal":ordinal,"this_register":resume_this,
            "continuation_argument_register":regs[2] if len(regs)==3 else None,
            "track_argument_register":regs[1] if len(regs)==3 else None,
            "track_argument_is_explicit_null":bool(
                null_witness and null_witness["track_argument_is_explicit_null"]
            ),
            "invokeSuspend_this_passed_as_continuation":(
                len(regs)==3 and regs[2]==resume_this
            )
        })

    direct_capture=any(x["same_original_track_parameter"] for x in stores)
    continuation_self_write=any(x["same_continuation_field_track"] for x in stores)
    owner_field_capture=any(x["same_capture_owner_track_field"] for x in stores)
    original_wrapper=any(
        "ORIGINAL_TRACK_PARAMETER_STRING" in x["string_argument_origins"]
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
    initial_capture_store_count=sum(
        row["same_original_track_parameter"]
        and "NEW_LFp0_CONTINUATION" in row["receiver_origins"]
        for row in stores
    )
    resumed_null_store_count=sum(
        "NULL_TRACK_ARGUMENT_ON_EXACT_Fp0_RESUME" in row["source_origins"]
        and "REUSED_LFp0_CONTINUATION" in row["receiver_origins"]
        for row in stores
    )
    resumed_saved_track_store_count=sum(
        row["same_continuation_field_track"]
        and "REUSED_LFp0_CONTINUATION" in row["receiver_origins"]
        for row in stores
    )

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
        "raw_track_field_store_sites":raw_track_field_store_sites,
        "continuation_track_field_reads":reads,
        "same_field_slot_store_to_resume_read_candidates":matching_reads,
        "track_string_field_read_sites":string_reads,
        "opaque_wrapper_constructor_sites":wrapper_ctors,
        "wrapper_continuation_handoff_sites":wrapper_handoffs,
        "continuation_argument_handoff_sites":continuation_handoffs,
        "initial_entry_original_track_to_new_continuation_store_candidate_count":initial_capture_store_count,
        "resumed_entry_null_track_to_reused_continuation_store_candidate_count":resumed_null_store_count,
        "resumed_entry_saved_track_to_reused_continuation_store_candidate_count":resumed_saved_track_store_count,
        "continuation_field_store_to_read_same_object_proven":False,
        "resume_continuation_call_sites":resume_calls,
        "resume_track_argument_explicit_null":resume_null_track_callsite,
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
    """Trace exact Track aliases to one field write across bounded CFG paths."""
    track_parameter_aliases=set(typed_parameter_registers(
        dex,method,flags,code_off,MODEL
    ))
    object_parameter_aliases=set(typed_parameter_registers(
        dex,method,flags,code_off,"Ljava/lang/Object;"
    ))
    continuation_parameter_aliases=set(typed_parameter_registers(
        dex,method,flags,code_off,"LOe2;"
    ))
    this_register=None if flags&ACC_STATIC else (
        dex.u16(code_off)-dex.u16(code_off+2)
    )
    cfg=build_dex_control_flow(dex,code_off)
    by_pc=cfg["by_pc"]
    successors=cfg["successors"]
    initial_registers={}
    for reg in track_parameter_aliases:
        initial_registers[reg]=frozenset({"ORIGINAL_TRACK_PARAMETER"})
    for reg in object_parameter_aliases:
        initial_registers[reg]=frozenset({"OBJECT_PARAMETER_UNREFINED"})
    for reg in continuation_parameter_aliases:
        initial_registers.setdefault(reg,frozenset())
        initial_registers[reg]=frozenset(
            set(initial_registers[reg])|{"INPUT_CONTINUATION_PARAMETER"}
        )
    if this_register is not None:
        initial_registers[this_register]=frozenset({"THIS_OBJECT"})
    initial_state={"registers":initial_registers,"pending_return":None}

    def state_key(state):
        return (
            tuple((reg,tuple(sorted(origins)))
                  for reg,origins in sorted(state["registers"].items())),
            state["pending_return"]
        )

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
            result_type=callee[2].split(")",1)[1]
            pending_return=result_type if result_type==MODEL else None
            return {
                "registers":{r:frozenset(v) for r,v in regs.items() if v},
                "pending_return":pending_return
            }

        if op==0x0c:  # move-result-object; returned Track is never same as an input by assumption
            dest=words[0]>>8
            clear(dest)
            if pending_return==MODEL:
                regs[dest]={"UNLINKED_TRACK_RETURN_CANDIDATE"}
            pending_return=None
            return {
                "registers":{r:frozenset(v) for r,v in regs.items() if v},
                "pending_return":None
            }

        pending_return=None
        if op in (0x07,0x08,0x09):  # move-object preserves exact reference identity
            move=move_object_registers(op,words)
            if move:
                dest,source=move
                origins=set(regs.get(source,set()))
                clear(dest)
                if origins:
                    regs[dest]=origins
        elif op==0x22:  # new-instance of the exact field owner
            dest=(words[0]>>8)&0xff
            typ=dex.descriptor(words[1])
            clear(dest)
            if typ==target_field[0]:
                regs[dest]={"NEW_TARGET_FIELD_OWNER"}
        elif op==0x1f:  # check-cast preserves the same reference
            reg=(words[0]>>8)&0xff
            typ=dex.descriptor(words[1])
            origins=regs.get(reg,set())
            if typ==MODEL and "OBJECT_PARAMETER_UNREFINED" in origins:
                origins.add("CAST_OBJECT_PARAMETER_REFERENCE")
            if typ==target_field[0] and "INPUT_CONTINUATION_PARAMETER" in origins:
                origins.add("REUSED_TARGET_FIELD_OWNER")
        elif op==0x54:  # iget-object; record only type/identity category, never value
            dest=(words[0]>>8)&15
            receiver=(words[0]>>12)&15
            owner,name,field_type=field_id(dex,words[1])
            receiver_origins=regs.get(receiver,set())
            clear(dest)
            if field_type==MODEL:
                if (owner,name,field_type)==target_field and (
                    "NEW_TARGET_FIELD_OWNER" in receiver_origins
                    or "REUSED_TARGET_FIELD_OWNER" in receiver_origins
                    or "THIS_OBJECT" in receiver_origins
                ):
                    regs[dest]={"TARGET_FIELD_TRACK_READ_CANDIDATE"}
                elif receiver==this_register:
                    regs[dest]={"TRACK_FIELD_READ_FROM_THIS"}
        elif op==0x5b:  # iput-object does not change source-register identity
            pass
        else:
            dest=written_register(op,words)
            if dest is not None:
                clear(dest)
                if op in wide_ops:
                    clear(dest+1)
        return {
            "registers":{r:frozenset(v) for r,v in regs.items() if v},
            "pending_return":pending_return
        }

    incoming={cfg["entry"]:{state_key(initial_state):initial_state}}
    work=[(cfg["entry"],state_key(initial_state))]
    processed=0
    while work:
        pc,key=work.pop()
        processed+=1
        if processed>200000:
            raise ValueError("TRACK_FIELD_WRITER_CFG_DATAFLOW_LIMIT")
        state=incoming[pc][key]
        op,words=by_pc[pc]
        out=transfer(state,op,words)
        out_key=state_key(out)
        for target in successors.get(pc,()):
            bucket=incoming.setdefault(target,{})
            if out_key in bucket:
                continue
            if len(bucket)>=128:
                raise ValueError("TRACK_FIELD_WRITER_CFG_PATH_STATE_LIMIT")
            bucket[out_key]=out
            work.append((target,out_key))

    ordinal_by_pc={pc:index for index,(pc,_op,_words) in enumerate(cfg["instructions"])}
    stores=[]
    seen=set()
    for pc in sorted(cfg["reachable"]):
        op,words=by_pc[pc]
        if op!=0x5b or field_id(dex,words[1])!=target_field:
            continue
        value=(words[0]>>8)&15
        receiver=(words[0]>>12)&15
        for path_state in incoming.get(pc,{}).values():
            state=path_state["registers"]
            source_origins=state.get(value,frozenset())
            receiver_origins=state.get(receiver,frozenset())
            from_parameter="ORIGINAL_TRACK_PARAMETER" in source_origins
            from_field="TRACK_FIELD_READ_FROM_THIS" in source_origins
            from_cast="CAST_OBJECT_PARAMETER_REFERENCE" in source_origins
            from_target_field="TARGET_FIELD_TRACK_READ_CANDIDATE" in source_origins
            from_return="UNLINKED_TRACK_RETURN_CANDIDATE" in source_origins
            from_object="OBJECT_PARAMETER_UNREFINED" in source_origins
            row={
                "pc":pc,
                "ordinal":ordinal_by_pc.get(pc),
                "source_is_original_track_parameter":from_parameter,
                "source_is_track_field_read_from_this":from_field,
                "source_is_track_parameter_or_field":from_parameter or from_field or from_cast,
                "source_is_object_parameter_not_yet_cast":from_object,
                "source_is_unlinked_track_return_candidate":from_return,
                "source_is_target_field_track_read_candidate":from_target_field,
                "receiver_is_this":receiver==this_register,
                "receiver_is_target_field_owner":(
                    "NEW_TARGET_FIELD_OWNER" in receiver_origins
                    or "REUSED_TARGET_FIELD_OWNER" in receiver_origins
                ),
                "source_origins":sorted(source_origins),
                "receiver_origins":sorted(receiver_origins),
                "track_source_provenance":(
                    "SAME_TRACK_PARAMETER_REFERENCE" if from_parameter else
                    "TRACK_FIELD_REFERENCE" if from_field else
                    "CAST_OBJECT_PARAMETER_REFERENCE" if from_cast else
                    "TARGET_FIELD_TRACK_READ_CANDIDATE" if from_target_field else
                    "UNLINKED_TRACK_RETURN_CANDIDATE" if from_return else
                    "OBJECT_PARAMETER_UNREFINED" if from_object else
                    "UNTRACED"
                )
            }
            key=(pc,tuple(row["source_origins"]),tuple(row["receiver_origins"]))
            if key not in seen:
                seen.add(key)
                stores.append(row)

    return {
        "method":{"owner":method[0],"method":method[1],"signature":method[2]},
        "track_parameter_count":len(track_parameter_aliases),
        "object_parameter_count":len(object_parameter_aliases),
        "field_store_sites":stores,
        "same_track_parameter_store_candidate":any(
            row["source_is_original_track_parameter"] for row in stores
        ),
        "all_observed_store_paths_same_original_track_parameter":(
            bool(stores) and all(row["source_is_original_track_parameter"] for row in stores)
        ),
        "branch_seen":bool(cfg["branches"]),
        "control_flow_graph_built":True,
        "reachable_instruction_count":len(cfg["reachable"]),
        "dataflow_instruction_visits":processed,
        "max_path_states_at_instruction":max(
            (len(states) for states in incoming.values()),default=0
        ),
        "exception_handler_edges_included":False,
        "branch_path_predicates_evaluated":False,
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


def trace_coroutine_callsite_argument_origins(
    dex, method, flags, code_off, callsite_pc, track_register, continuation_register
):
    """Trace only object-reference categories reaching one exact coroutine callsite."""
    continuation_owner="LFp0;"
    continuation_type="LOe2;"
    track_parameters=set(typed_parameter_registers(
        dex,method,flags,code_off,MODEL
    ))
    object_parameters=set(typed_parameter_registers(
        dex,method,flags,code_off,"Ljava/lang/Object;"
    ))
    continuation_parameters=set(typed_parameter_registers(
        dex,method,flags,code_off,continuation_type
    ))
    kotlin_continuation_parameters=set(typed_parameter_registers(
        dex,method,flags,code_off,"Lkotlin/coroutines/Continuation;"
    ))
    this_register=None if flags&ACC_STATIC else (
        dex.u16(code_off)-dex.u16(code_off+2)
    )
    target_registers={track_register,continuation_register}
    initial_registers={}
    for reg in track_parameters:
        initial_registers[reg]=frozenset({"ORIGINAL_TRACK_PARAMETER"})
    for reg in object_parameters:
        initial_registers[reg]=frozenset(
            set(initial_registers.get(reg,frozenset()))|{"OBJECT_PARAMETER"}
        )
    for reg in continuation_parameters:
        initial_registers[reg]=frozenset(
            set(initial_registers.get(reg,frozenset()))|{"INPUT_CONTINUATION_PARAMETER"}
        )
    for reg in kotlin_continuation_parameters:
        initial_registers[reg]=frozenset(
            set(initial_registers.get(reg,frozenset()))|{"KOTLIN_CONTINUATION_PARAMETER"}
        )
    if this_register is not None:
        initial_registers[this_register]=frozenset(
            set(initial_registers.get(this_register,frozenset()))|{"THIS_OBJECT"}
        )
    initial_state={"registers":initial_registers,"pending_return":None}
    cfg=build_dex_control_flow(dex,code_off)
    by_pc=cfg["by_pc"]
    successors=cfg["successors"]

    def state_key(state):
        return (
            tuple((reg,tuple(sorted(origins)))
                  for reg,origins in sorted(state["registers"].items())),
            state["pending_return"]
        )

    wide_ops=(
        {0x04,0x05,0x06,0x0b,0x16,0x17,0x18,0x19,0x45,0x53,0x61,
         0x7d,0x7e,0x80,0x82,0x85,0x87,0x88,0x8a}
        |set(range(0x9b,0xa6))|set(range(0xab,0xb0))
        |set(range(0xbb,0xc6))|set(range(0xcb,0xd0))
    )

    def const_zero_register(op,words):
        if op==0x12:
            literal=(words[0]>>12)&15
            if literal&8:
                literal-=16
            return ((words[0]>>8)&15) if literal==0 else None
        if op==0x13:
            literal=words[1]
            if literal&0x8000:
                literal-=0x10000
            return ((words[0]>>8)&0xff) if literal==0 else None
        if op==0x14:
            literal=words[1]|(words[2]<<16)
            return ((words[0]>>8)&0xff) if literal==0 else None
        if op==0x15:
            return ((words[0]>>8)&0xff) if words[1]==0 else None
        return None

    def transfer(state,op,words):
        regs={r:set(v) for r,v in state["registers"].items()}
        pending=state["pending_return"]

        def clear(reg):
            regs.pop(reg,None)

        if op in INVOKES:
            callee=dex.method(words[1])
            result_type=callee[2].split(")",1)[1]
            pending=(
                result_type if result_type in (
                    MODEL,"Ljava/lang/Object;",continuation_owner,continuation_type,
                    "Lkotlin/coroutines/Continuation;"
                ) else None
            )
            return {
                "registers":{r:frozenset(v) for r,v in regs.items() if v},
                "pending_return":pending
            }

        if op==0x0c:  # move-result-object
            dest=(words[0]>>8)&0xff
            clear(dest)
            if pending==MODEL:
                regs[dest]={"UNLINKED_TRACK_RETURN_CANDIDATE"}
            elif pending=="Ljava/lang/Object;":
                regs[dest]={"UNLINKED_OBJECT_RETURN_CANDIDATE"}
            elif pending in (
                continuation_owner,continuation_type,"Lkotlin/coroutines/Continuation;"
            ):
                regs[dest]={"UNLINKED_CONTINUATION_RETURN_CANDIDATE"}
            elif dest in target_registers:
                regs[dest]={"UNCLASSIFIED_MOVE_RESULT_OBJECT_RETURN"}
            pending=None
        elif op in (0x07,0x08,0x09):  # move-object keeps Java reference identity
            move=move_object_registers(op,words)
            if move:
                dest,source=move
                origins=set(regs.get(source,set()))
                clear(dest)
                if origins:
                    regs[dest]=origins
                elif dest in target_registers:
                    regs[dest]={"UNCLASSIFIED_MOVE_OBJECT_SOURCE"}
            pending=None
        elif op==0x22:  # new-instance
            dest=(words[0]>>8)&0xff
            typ=dex.descriptor(words[1])
            clear(dest)
            if typ==MODEL:
                regs[dest]={"NEW_TRACK_OBJECT"}
            elif typ==continuation_owner:
                regs[dest]={"NEW_LFp0_CONTINUATION"}
            elif dest in target_registers:
                if not typ.startswith("L") or len(typ)>256:
                    raise ValueError("COROUTINE_CALLSITE_NEW_INSTANCE_TYPE_INVALID")
                regs[dest]={"UNCLASSIFIED_NEW_INSTANCE_TYPE","NEW_INSTANCE_TYPE:"+typ}
            pending=None
        elif op==0x1f:  # check-cast preserves exact object identity
            reg=(words[0]>>8)&0xff
            typ=dex.descriptor(words[1])
            origins=regs.get(reg,set())
            if typ==MODEL:
                if "OBJECT_PARAMETER" in origins:
                    origins.add("OBJECT_PARAMETER_CAST_TO_TRACK")
                if "UNLINKED_OBJECT_RETURN_CANDIDATE" in origins:
                    origins.add("UNLINKED_OBJECT_RETURN_CAST_TO_TRACK")
                if "UNLINKED_COLLECTION_OBJECT_READ_CANDIDATE" in origins:
                    origins.add("COLLECTION_ELEMENT_CAST_TO_TRACK")
            elif typ==continuation_owner and (
                "INPUT_CONTINUATION_PARAMETER" in origins
                or "KOTLIN_CONTINUATION_PARAMETER" in origins
            ):
                origins.add("REUSED_LFp0_CONTINUATION")
            elif typ==continuation_type and "KOTLIN_CONTINUATION_PARAMETER" in origins:
                origins.add("CONTINUATION_PARAMETER_CAST_TO_OE2")
            elif typ in (continuation_type,"Lkotlin/coroutines/Continuation;"):
                if "OBJECT_PARAMETER" in origins:
                    origins.add("OBJECT_PARAMETER_CAST_TO_CONTINUATION")
                if "UNLINKED_OBJECT_RETURN_CANDIDATE" in origins:
                    origins.add("UNLINKED_OBJECT_RETURN_CAST_TO_CONTINUATION")
            if not origins and reg in target_registers:
                origins.add("UNCLASSIFIED_CHECK_CAST_SOURCE")
                regs[reg]=origins
            pending=None
        elif op==0x54:  # iget-object; only type and receiver identity are inspected
            dest=(words[0]>>8)&15
            receiver=(words[0]>>12)&15
            _owner,_name,field_type=field_id(dex,words[1])
            receiver_origins=regs.get(receiver,set())
            clear(dest)
            if field_type==MODEL:
                if "THIS_OBJECT" in receiver_origins:
                    regs[dest]={"TRACK_FROM_THIS_FIELD"}
                elif (
                    "INPUT_CONTINUATION_PARAMETER" in receiver_origins
                    or "REUSED_LFp0_CONTINUATION" in receiver_origins
                    or "NEW_LFp0_CONTINUATION" in receiver_origins
                ):
                    regs[dest]={"TRACK_FROM_CONTINUATION_FIELD"}
                elif "OBJECT_PARAMETER" in receiver_origins:
                    regs[dest]={"TRACK_FROM_OBJECT_PARAMETER_FIELD"}
                else:
                    regs[dest]={"TRACK_FROM_OTHER_FIELD"}
            elif field_type in (
                continuation_owner,continuation_type,"Lkotlin/coroutines/Continuation;"
            ):
                regs[dest]={"CONTINUATION_FROM_FIELD"}
            elif dest in target_registers:
                regs[dest]={"UNCLASSIFIED_TYPED_FIELD_READ"}
            pending=None
        elif op==0x62:  # sget-object
            dest=(words[0]>>8)&0xff
            _owner,_name,field_type=field_id(dex,words[1])
            clear(dest)
            if field_type==MODEL:
                regs[dest]={"TRACK_FROM_STATIC_FIELD"}
            elif field_type in (
                continuation_owner,continuation_type,"Lkotlin/coroutines/Continuation;"
            ):
                regs[dest]={"CONTINUATION_FROM_STATIC_FIELD"}
            elif dest in target_registers:
                regs[dest]={"UNCLASSIFIED_STATIC_FIELD_READ"}
            pending=None
        elif op==0x46:  # aget-object is a collection element, not Track identity proof
            dest=(words[0]>>8)&0xff
            clear(dest)
            regs[dest]={"UNLINKED_COLLECTION_OBJECT_READ_CANDIDATE"}
            pending=None
        elif op in (0x12,0x13,0x14,0x15):
            dest=const_zero_register(op,words)
            if dest is not None:
                clear(dest)
                regs[dest]={"NULL_CONSTANT"}
            else:
                dest=written_register(op,words)
                if dest is not None:
                    clear(dest)
                    if dest in target_registers:
                        regs[dest]={"UNCLASSIFIED_NONZERO_CONSTANT"}
            pending=None
        elif op in (0x5b,0x67):  # field stores do not change source-register identity
            pending=None
        else:
            dest=written_register(op,words)
            if dest is not None:
                clear(dest)
                if dest in target_registers:
                    regs[dest]={f"UNCLASSIFIED_REGISTER_WRITE_OPCODE_{op:02x}"}
                if op in wide_ops:
                    clear(dest+1)
                    if dest+1 in target_registers:
                        regs[dest+1]={f"UNCLASSIFIED_WIDE_REGISTER_WRITE_OPCODE_{op:02x}"}
            pending=None
        return {
            "registers":{r:frozenset(v) for r,v in regs.items() if v},
            "pending_return":pending
        }

    incoming={cfg["entry"]:{state_key(initial_state):initial_state}}
    work=[(cfg["entry"],state_key(initial_state))]
    processed=0
    while work:
        pc,key=work.pop()
        processed+=1
        if processed>200000:
            raise ValueError("COROUTINE_CALLSITE_ORIGIN_VISIT_LIMIT")
        state=incoming[pc][key]
        op,words=by_pc[pc]
        out=transfer(state,op,words)
        out_key=state_key(out)
        for target in successors.get(pc,()):
            bucket=incoming.setdefault(target,{})
            if out_key in bucket:
                continue
            if len(bucket)>=128:
                raise ValueError("COROUTINE_CALLSITE_ORIGIN_PATH_STATE_LIMIT")
            bucket[out_key]=out
            work.append((target,out_key))

    states=incoming.get(callsite_pc,{})
    track_paths=sorted({
        tuple(sorted(state["registers"].get(track_register,frozenset({"UNCLASSIFIED"}))))
        for state in states.values()
    })
    continuation_paths=sorted({
        tuple(sorted(state["registers"].get(
            continuation_register,frozenset({"UNCLASSIFIED"})
        )))
        for state in states.values()
    })

    def all_paths_have(paths,tag):
        return bool(paths) and all(tag in path for path in paths)

    if not states:
        track_class="UNREACHABLE_CALLSITE"
    elif all_paths_have(track_paths,"ORIGINAL_TRACK_PARAMETER"):
        track_class="SAME_TRACK_PARAMETER_REFERENCE"
    elif all_paths_have(track_paths,"OBJECT_PARAMETER_CAST_TO_TRACK"):
        track_class="SAME_OBJECT_AS_OBJECT_PARAMETER_AFTER_CAST"
    elif all_paths_have(track_paths,"TRACK_FROM_THIS_FIELD"):
        track_class="TRACK_FROM_THIS_FIELD_CANDIDATE"
    elif all_paths_have(track_paths,"TRACK_FROM_CONTINUATION_FIELD"):
        track_class="TRACK_FROM_CONTINUATION_FIELD_CANDIDATE"
    elif all_paths_have(track_paths,"TRACK_FROM_OBJECT_PARAMETER_FIELD"):
        track_class="TRACK_FROM_OBJECT_PARAMETER_FIELD_CANDIDATE"
    elif all_paths_have(track_paths,"TRACK_FROM_STATIC_FIELD"):
        track_class="TRACK_FROM_STATIC_FIELD_CANDIDATE"
    elif all_paths_have(track_paths,"UNLINKED_TRACK_RETURN_CANDIDATE") or all_paths_have(
        track_paths,"UNLINKED_OBJECT_RETURN_CAST_TO_TRACK"
    ) or all_paths_have(track_paths,"COLLECTION_ELEMENT_CAST_TO_TRACK"):
        track_class="UNLINKED_TRACK_SOURCE_CANDIDATE"
    elif all_paths_have(track_paths,"NULL_CONSTANT"):
        track_class="EXPLICIT_NULL"
    elif all_paths_have(track_paths,"NEW_TRACK_OBJECT"):
        track_class="NEW_TRACK_OBJECT"
    else:
        track_class="PATH_DEPENDENT_OR_UNCLASSIFIED"

    if not states:
        continuation_class="UNREACHABLE_CALLSITE"
    elif (
        all_paths_have(continuation_paths,"INPUT_CONTINUATION_PARAMETER")
        or all_paths_have(continuation_paths,"KOTLIN_CONTINUATION_PARAMETER")
        or all_paths_have(continuation_paths,"CONTINUATION_PARAMETER_CAST_TO_OE2")
    ):
        continuation_class="SAME_CONTINUATION_PARAMETER_REFERENCE"
    elif all_paths_have(continuation_paths,"THIS_OBJECT"):
        continuation_class="CALLER_THIS_REFERENCE"
    elif all_paths_have(continuation_paths,"REUSED_LFp0_CONTINUATION"):
        continuation_class="REUSED_CONTINUATION_OBJECT_CANDIDATE"
    elif all_paths_have(continuation_paths,"NEW_LFp0_CONTINUATION"):
        continuation_class="NEW_CONTINUATION_OBJECT"
    elif all_paths_have(continuation_paths,"CONTINUATION_FROM_FIELD"):
        continuation_class="CONTINUATION_FROM_FIELD_CANDIDATE"
    elif all_paths_have(continuation_paths,"CONTINUATION_FROM_STATIC_FIELD"):
        continuation_class="CONTINUATION_FROM_STATIC_FIELD_CANDIDATE"
    elif all_paths_have(continuation_paths,"CONTINUATION_FROM_FIELD"):
        continuation_class="CONTINUATION_FROM_FIELD_CANDIDATE"
    elif all_paths_have(continuation_paths,"CONTINUATION_FROM_STATIC_FIELD"):
        continuation_class="CONTINUATION_FROM_STATIC_FIELD_CANDIDATE"
    elif all_paths_have(continuation_paths,"OBJECT_PARAMETER_CAST_TO_CONTINUATION"):
        continuation_class="SAME_OBJECT_AS_OBJECT_PARAMETER_AFTER_CAST_TO_CONTINUATION"
    elif (
        all_paths_have(continuation_paths,"UNLINKED_CONTINUATION_RETURN_CANDIDATE")
        or all_paths_have(continuation_paths,"UNLINKED_OBJECT_RETURN_CAST_TO_CONTINUATION")
    ):
        continuation_class="UNLINKED_CONTINUATION_SOURCE_CANDIDATE"
    elif all_paths_have(continuation_paths,"NULL_CONSTANT"):
        continuation_class="EXPLICIT_NULL"
    else:
        continuation_class="PATH_DEPENDENT_OR_UNCLASSIFIED"

    return {
        "callsite_reachable":bool(states),
        "path_state_count":len(states),
        "track_argument_origin_classification":track_class,
        "track_argument_origin_paths":[list(path) for path in track_paths],
        "continuation_argument_origin_classification":continuation_class,
        "continuation_argument_origin_paths":[list(path) for path in continuation_paths],
        "reachable_instruction_count":len(cfg["reachable"]),
        "dataflow_instruction_visits":processed,
        "max_path_states_at_instruction":max(
            (len(bucket) for bucket in incoming.values()),default=0
        ),
        "branch_path_predicates_evaluated":False,
        "exception_handler_edges_included":False,
        "private_field_names_values_or_media_disclosed":False
    }


def classify_native_track_coroutine_callsite(
    dex, caller, flags, code_off, ins, ordinal, target_method
):
    """Classify exact typed Track/Continuation argument registers at one direct call."""
    if ordinal<0 or ordinal>=len(ins):
        raise ValueError("TRACK_COROUTINE_CALLSITE_ORDINAL")
    _pc,op,words=ins[ordinal]
    if op not in INVOKES or dex.method(words[1])!=target_method:
        raise ValueError("TRACK_COROUTINE_CALLSITE_TARGET_MISMATCH")
    args=invoke_registers(op,words)
    params=parse_types(target_method[2])
    target_types=expand_invoke_register_types(
        target_method[0],params,op in (0x71,0x77)
    )
    if len(args)!=len(target_types):
        raise ValueError("TRACK_COROUTINE_CALLSITE_REGISTER_MAP")
    track_positions=[i for i,typ in enumerate(target_types) if typ==MODEL]
    continuation_positions=[i for i,typ in enumerate(target_types) if typ=="LOe2;"]
    if len(track_positions)!=1 or len(continuation_positions)!=1:
        raise ValueError("TRACK_COROUTINE_CALLSITE_TYPED_ARGUMENT_SHAPE")
    track_reg=args[track_positions[0]]
    continuation_reg=args[continuation_positions[0]]
    track_parameters=typed_parameter_registers(
        dex,caller,flags,code_off,MODEL
    )
    continuation_parameters=set(typed_parameter_registers(
        dex,caller,flags,code_off,"LOe2;"
    ))|set(typed_parameter_registers(
        dex,caller,flags,code_off,"Lkotlin/coroutines/Continuation;"
    ))
    this_register=None if flags&ACC_STATIC else (
        dex.u16(code_off)-dex.u16(code_off+2)
    )
    wide_ops=(
        {0x04,0x05,0x06,0x0b,0x16,0x17,0x18,0x19,0x45,0x53,0x61,
         0x7d,0x7e,0x80,0x82,0x85,0x87,0x88,0x8a}
        |set(range(0x9b,0xa6))|set(range(0xab,0xb0))
        |set(range(0xbb,0xc6))|set(range(0xcb,0xd0))
    )

    def written_before(register):
        for _prior_pc,prior_op,prior_words in ins[:ordinal]:
            dest=written_register(prior_op,prior_words)
            if dest==register or (
                dest is not None and prior_op in wide_ops and dest+1==register
            ):
                return True
        return False

    track_register_is_parameter=track_reg in track_parameters
    track_register_overwritten=written_before(track_reg)
    continuation_is_this=(
        this_register is not None and continuation_reg==this_register
    )
    continuation_is_parameter=continuation_reg in continuation_parameters
    continuation_register_overwritten=written_before(continuation_reg)
    previous=ins[ordinal-1] if ordinal>0 else None
    explicit_null=bool(
        previous and const4_zero_to_register(previous[1],previous[2],track_reg)
    )
    track_source=(
        "EXPLICIT_NULL" if explicit_null else
        "TRACK_PARAMETER_REGISTER_OVERWRITTEN"
        if track_register_is_parameter and track_register_overwritten else
        "TRACK_PARAMETER_REGISTER_UNCHANGED_CANDIDATE"
        if track_register_is_parameter else
        "UNCLASSIFIED"
    )
    continuation_source=(
        "CALLER_THIS_REGISTER_OVERWRITTEN"
        if continuation_is_this and continuation_register_overwritten else
        "CALLER_THIS_REGISTER_CANDIDATE"
        if continuation_is_this else
        "TYPED_CONTINUATION_PARAMETER_REGISTER_OVERWRITTEN"
        if continuation_is_parameter and continuation_register_overwritten else
        "TYPED_CONTINUATION_PARAMETER_REGISTER"
        if continuation_is_parameter else
        "UNCLASSIFIED"
    )
    exact_resume=(
        caller==("LFp0;","invokeSuspend","(Ljava/lang/Object;)Ljava/lang/Object;")
        and continuation_is_this
        and not continuation_register_overwritten
        and explicit_null
    )
    argument_origin_trace=trace_coroutine_callsite_argument_origins(
        dex,caller,flags,code_off,_pc,track_reg,continuation_reg
    )
    return {
        "caller":{"owner":caller[0],"method":caller[1],"signature":caller[2]},
        "ordinal":ordinal,
        "track_argument_source":track_source,
        "track_argument_is_explicit_null":explicit_null,
        "track_argument_register_is_track_parameter":track_register_is_parameter,
        "track_argument_register_overwritten_before_call":track_register_overwritten,
        "continuation_argument_source":continuation_source,
        "continuation_argument_is_caller_this":continuation_is_this,
        "continuation_argument_is_typed_parameter":continuation_is_parameter,
        "continuation_argument_register_overwritten_before_call":continuation_register_overwritten,
        "exact_resume_callsite":exact_resume,
        "argument_origin_trace":argument_origin_trace
    }


def summarize_coroutine_new_instance_ancestry(callsite_census, class_profiles):
    """Verify declared class inheritance of callsite-constructed continuations."""
    prefix="NEW_INSTANCE_TYPE:"
    candidates={}
    for row in callsite_census.get("call_sites",[]):
        caller=row["caller"]
        for path in row["argument_origin_trace"]["continuation_argument_origin_paths"]:
            for origin in path:
                if not origin.startswith(prefix):
                    continue
                descriptor=origin[len(prefix):]
                if not descriptor.startswith("L") or len(descriptor)>256:
                    raise ValueError("COROUTINE_NEW_INSTANCE_DESCRIPTOR_INVALID")
                candidates.setdefault(descriptor,[]).append({
                    "caller":caller,
                    "ordinal":row["ordinal"]
                })
    if len(candidates)>32:
        raise ValueError("COROUTINE_NEW_INSTANCE_CLASS_LIMIT")
    rows=[]
    for descriptor in sorted(candidates):
        chain=[]
        current=descriptor
        visited={current}
        for _ in range(16):
            profile=class_profiles.get(current)
            if profile is None:
                break
            parent=profile.get("superclass")
            if parent is None:
                break
            if parent in visited:
                raise ValueError("COROUTINE_NEW_INSTANCE_HIERARCHY_CYCLE")
            chain.append(parent)
            visited.add(parent)
            current=parent
        else:
            raise ValueError("COROUTINE_NEW_INSTANCE_HIERARCHY_LIMIT")
        rows.append({
            "new_instance_type":descriptor,
            "class_defined_in_signed_dex":descriptor in class_profiles,
            "superclass_chain":chain,
            "derives_from_LFp0_base_continuation":("LFp0;" in chain),
            "derives_from_LOe2_continuation":("LOe2;" in chain),
            "observed_call_sites":candidates[descriptor],
            "constructor_receives_original_continuation_proven":False,
            "same_active_selected_track_proven":False
        })
    return {
        "new_instance_class_count":len(rows),
        "new_instance_classes":rows,
        "every_new_instance_derives_from_LOe2":(
            bool(rows) and all(row["derives_from_LOe2_continuation"] for row in rows)
        ),
        "runtime_continuation_identity_proven":False,
        "private_fields_values_or_media_disclosed":False
    }


def classify_coroutine_entry_direct_upstream_call(caller, callee, ordinal, op):
    """Record exact inbound references, not a virtual/Flow runtime dispatch claim."""
    targets={
        ("LDp0;","if",
         "(Lru/yandex/music/data/audio/o;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;"),
        ("Lwp0$a;","emit",
         "(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;")
    }
    if callee not in targets:
        raise ValueError("COROUTINE_ENTRY_UPSTREAM_TARGET_MISMATCH")
    target_params=parse_types(callee[2])
    caller_params=parse_types(caller[2])
    return {
        "caller":{"owner":caller[0],"method":caller[1],"signature":caller[2]},
        "target":{"owner":callee[0],"method":callee[1],"signature":callee[2]},
        "ordinal":ordinal,
        "invoke_kind":invoke_kind_name(op),
        "caller_declares_track_parameter":MODEL in caller_params,
        "caller_declares_object_parameter":"Ljava/lang/Object;" in caller_params,
        "target_accepts_typed_track":MODEL in target_params,
        "target_accepts_object":"Ljava/lang/Object;" in target_params,
        "same_track_reference_or_active_playback_proven":False,
        "flow_interface_dispatch_proven":False
    }


def inspect_native_track_coroutine_callers(apks, target_method):
    """Census every direct signed-DEX caller of the exact coroutine method."""
    call_sites=[]
    upstream_direct_sites=[]
    upstream_targets={
        ("LDp0;","if",
         "(Lru/yandex/music/data/audio/o;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;"),
        ("Lwp0$a;","emit",
         "(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;")
    }
    scanned_method_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>DEX_MAX:
                    raise ValueError("TRACK_COROUTINE_CALLER_DEX_LIMIT")
                dex=Dex(archive.read(entry.filename))
                for caller,flags,code_off in method_definitions_with_flags(dex):
                    scanned_method_count+=1
                    if scanned_method_count>500000:
                        raise ValueError("TRACK_COROUTINE_CALLER_METHOD_LIMIT")
                    ins=list(instructions(dex,code_off))
                    for ordinal,(_pc,op,words) in enumerate(ins):
                        if op not in INVOKES:
                            continue
                        callee=dex.method(words[1])
                        if callee in upstream_targets:
                            if len(upstream_direct_sites)>=128:
                                raise ValueError("COROUTINE_ENTRY_UPSTREAM_DIRECT_SITE_LIMIT")
                            upstream_direct_sites.append(
                                classify_coroutine_entry_direct_upstream_call(
                                    caller,callee,ordinal,op
                                )
                            )
                        if callee!=target_method:
                            continue
                        if len(call_sites)>=128:
                            raise ValueError("TRACK_COROUTINE_CALLER_SITE_LIMIT")
                        call_sites.append(classify_native_track_coroutine_callsite(
                            dex,caller,flags,code_off,ins,ordinal,target_method
                        ))
    this_calls=[
        row for row in call_sites
        if row["continuation_argument_is_caller_this"]
    ]
    return {
        "scanned_method_count":scanned_method_count,
        "direct_callsite_count":len(call_sites),
        "upstream_entry_direct_callsite_count":len(upstream_direct_sites),
        "upstream_entry_direct_call_sites":upstream_direct_sites,
        "upstream_entry_virtual_or_flow_dispatch_proven":False,
        "exact_resume_callsite_count":sum(
            row["exact_resume_callsite"] for row in call_sites
        ),
        "track_parameter_register_candidate_callsite_count":sum(
            row["track_argument_source"]=="TRACK_PARAMETER_REGISTER_UNCHANGED_CANDIDATE"
            for row in call_sites
        ),
        "same_track_parameter_dataflow_callsite_count":sum(
            row["argument_origin_trace"]["track_argument_origin_classification"]
            =="SAME_TRACK_PARAMETER_REFERENCE" for row in call_sites
        ),
        "object_parameter_cast_to_track_callsite_count":sum(
            row["argument_origin_trace"]["track_argument_origin_classification"]
            =="SAME_OBJECT_AS_OBJECT_PARAMETER_AFTER_CAST" for row in call_sites
        ),
        "track_field_origin_candidate_callsite_count":sum(
            "TRACK_FROM_" in row["argument_origin_trace"]["track_argument_origin_classification"]
            for row in call_sites
        ),
        "explicit_null_track_callsite_count":sum(
            row["track_argument_is_explicit_null"] for row in call_sites
        ),
        "continuation_this_callsite_count":len(this_calls),
        "continuation_typed_parameter_callsite_count":sum(
            row["continuation_argument_is_typed_parameter"] for row in call_sites
        ),
        "unclassified_track_argument_callsite_count":sum(
            row["track_argument_source"]=="UNCLASSIFIED" for row in call_sites
        ),
        "unclassified_continuation_argument_callsite_count":sum(
            row["continuation_argument_source"]=="UNCLASSIFIED"
            for row in call_sites
        ),
        "only_direct_this_continuation_callsite_is_exact_resume":(
            bool(this_calls) and all(row["exact_resume_callsite"] for row in this_calls)
        ),
        "call_sites":call_sites,
        "track_values_or_private_fields_disclosed":False
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


def track_parameter_field_store_refs(dex, method, flags: int, code_off: int):
    """Return exact Track-typed fields receiving the original Track parameter on this.

    Field identifiers stay internal to the audit. Callers may use the returned
    refs to constrain later reads, but must not disclose field names or values.
    """
    aliases = set(typed_parameter_registers(
        dex, method, flags, code_off, MODEL
    ))
    if not aliases:
        return []
    this_register = (
        None if flags & ACC_STATIC
        else dex.u16(code_off) - dex.u16(code_off + 2)
    )
    if this_register is None:
        return []
    field_refs = set()
    for _ordinal, op, words in instructions(dex, code_off):
        if op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            if move is not None:
                dest, source = move
                had_alias = source in aliases
                aliases.discard(dest)
                if had_alias:
                    aliases.add(dest)
            continue
        if op == 0x5b:  # iput-object: exact Track parameter into an instance field
            value_register = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            field_ref = field_id(dex, words[1])
            if (
                receiver == this_register
                and field_ref[2] == MODEL
                and value_register in aliases
            ):
                field_refs.add(field_ref)
            continue
        if op == 0x1f:  # check-cast preserves object identity
            continue
        destination = written_register(op, words)
        if destination is not None:
            aliases.discard(destination)
        if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
            aliases.clear()
    return sorted(field_refs)


def exact_instance_field_read_refs(dex, method, flags, code_off, field_type):
    """Return exact typed instance fields read from this; field identifiers stay internal."""
    if not isinstance(field_type, str) or not field_type.startswith(("L", "[")):
        raise ValueError("EXACT_INSTANCE_FIELD_TYPE_INVALID")
    if flags & ACC_STATIC:
        return []
    this_register = dex.u16(code_off) - dex.u16(code_off + 2)
    field_refs = set()
    for _ordinal, op, words in instructions(dex, code_off):
        if op != 0x54:
            continue
        receiver = (words[0] >> 12) & 15
        if receiver != this_register:
            continue
        field_ref = field_id(dex, words[1])
        if field_ref[2] == field_type:
            field_refs.add(field_ref)
    return sorted(field_refs)


def exact_parameter_field_store_refs(dex, method, flags, code_off, parameter_type):
    """Return exact fields receiving one typed object parameter on this; names stay internal."""
    if not isinstance(parameter_type, str) or not parameter_type.startswith(("L", "[")):
        raise ValueError("EXACT_PARAMETER_FIELD_TYPE_INVALID")
    aliases = set(typed_parameter_registers(
        dex, method, flags, code_off, parameter_type
    ))
    if not aliases:
        return []
    this_register = (
        None if flags & ACC_STATIC
        else dex.u16(code_off) - dex.u16(code_off + 2)
    )
    if this_register is None:
        return []
    field_refs = set()
    for _ordinal, op, words in instructions(dex, code_off):
        if op in (0x07, 0x08, 0x09):
            move = move_object_registers(op, words)
            if move is not None:
                dest, source = move
                had_alias = source in aliases
                aliases.discard(dest)
                if had_alias:
                    aliases.add(dest)
            continue
        if op == 0x5b:
            value_register = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            field_ref = field_id(dex, words[1])
            if (
                receiver == this_register
                and field_ref[2] == parameter_type
                and value_register in aliases
            ):
                field_refs.add(field_ref)
            continue
        if op == 0x1f:
            continue
        destination = written_register(op, words)
        if destination is not None:
            aliases.discard(destination)
        if op in (0x28, 0x29, 0x2a, 0x2b, 0x2c) or 0x32 <= op <= 0x3d:
            aliases.clear()
    return sorted(field_refs)


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
    ins = list(instructions(dex, code_off))
    for ordinal, (pc, op, words) in enumerate(ins):
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
        elif op in (0x5b, 0x67):  # iput-object / sput-object
            owner, _field_name, typ = field_id(dex, words[1])
            value_register = (
                (words[0] >> 8) & 15 if op == 0x5b
                else (words[0] >> 8) & 0xff
            )
            receiver_register = (
                (words[0] >> 12) & 15 if op == 0x5b else None
            )
            this_register = (
                None if flags & ACC_STATIC
                else dex.u16(code_off) - dex.u16(code_off + 2)
            )
            origin = local_object_register_origin(
                dex, method, flags, code_off, ins, ordinal,
                value_register, include_source_ordinal=True
            )
            origin.pop("field", None)
            rows.append({
                "ordinal": ordinal, "op": "FIELD_WRITE",
                "owner": owner, "type": typ,
                "receiver_is_this": receiver_register == this_register
                    if receiver_register is not None else False,
                "value_is_native_track_parameter": value_register in aliases,
                "value_origin": origin,
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





def privacy_safe_flow_class_profile(profile):
    """Convert a signed-Dex class profile to JSON-safe type-only metadata."""
    if not profile:
        return {"defined_in_signed_dex": False}
    return {
        "defined_in_signed_dex": True,
        "superclass": profile.get("superclass"),
        "interfaces": sorted(profile.get("interfaces", ())),
        "is_interface": bool(profile.get("is_interface")),
        "is_abstract": bool(profile.get("is_abstract")),
        "instance_field_type_descriptors": sorted(profile.get("instance_types", ())),
        "static_field_type_descriptors": sorted(profile.get("static_types", ())),
    }

def privacy_safe_focused_method_trace(trace):
    """Keep exact call/branch/type evidence while omitting private field names and literals."""
    events = []
    field_read_types = set()
    field_write_types = set()
    for row in trace.get("instructions", ()):
        op = row.get("op")
        if op == "INVOKE":
            events.append({
                "ordinal": row.get("ordinal"),
                "kind": "CALL",
                "callee": row.get("callee"),
                "native_track_argument_positions":
                    row.get("native_track_argument_positions", []),
            })
        elif op == "FIELD_READ":
            field_type = row.get("type")
            if field_type:
                field_read_types.add(field_type)
            events.append({
                "ordinal": row.get("ordinal"),
                "kind": "FIELD_READ",
                "owner": row.get("owner"),
                "type": field_type,
                "receiver_is_native_track": row.get("receiver_is_native_model", False),
            })
        elif op == "FIELD_WRITE":
            field_type = row.get("type")
            if field_type:
                field_write_types.add(field_type)
            origin = row.get("value_origin", {})
            events.append({
                "ordinal": row.get("ordinal"),
                "kind": "FIELD_WRITE",
                "owner": row.get("owner"),
                "type": field_type,
                "receiver_is_this": row.get("receiver_is_this", False),
                "value_is_native_track_parameter":
                    row.get("value_is_native_track_parameter", False),
                "value_origin": {
                    key: value for key, value in origin.items()
                    if key != "field"
                },
            })
        elif op == "BRANCH_OR_SWITCH":
            events.append({
                "ordinal": row.get("ordinal"),
                "kind": "BRANCH_OR_SWITCH",
            })
        elif op == "RETURN_OBJECT":
            events.append({
                "ordinal": row.get("ordinal"),
                "kind": "RETURN_OBJECT",
                "source_is_native_track": row.get("source_is_native_track", False),
            })
    return {
        "method": trace.get("method"),
        "native_track_parameter_count": len(trace.get("native_model_parameters", ())),
        "field_read_type_descriptors": sorted(field_read_types),
        "field_write_type_descriptors": sorted(field_write_types),
        "events": events,
        "private_field_names_or_values_disclosed": False,
    }


def summarize_current_track_flow_candidate(class_profiles, focused_method_traces,
                                           flow_dispatcher_sites):
    """Inspect only the exact LzD7 -> LBy4 -> LDp0 Track-flow candidate."""
    interface = "LzD7;"
    implementers = sorted(
        owner for owner, profile in class_profiles.items()
        if interface in profile.get("interfaces", ())
    )
    if len(implementers) > 8:
        raise ValueError("CURRENT_TRACK_FLOW_IMPLEMENTER_LIMIT")
    owners = {"LzD7;", "LBD7;", "LMG7;", "LMG7$a;", "LC3a;", "LD3a;",
              "LAF7;", "LWM7;", "LyG7;", "LBy4;", "LBC3;", "LzC3;",
              "LAC3;", "LDp0;", "LGp0;"}
    traces = [
        privacy_safe_focused_method_trace(trace)
        for trace in focused_method_traces
        if trace.get("method", {}).get("owner") in owners
    ]
    if len(traces) > 64:
        raise ValueError("CURRENT_TRACK_FLOW_METHOD_TRACE_LIMIT")
    app_subscribes_ldp0 = False
    for site in flow_dispatcher_sites:
        caller = site.get("caller", {})
        if caller.get("owner") != "Lru/yandex/music/YMApplication;" or \
                caller.get("name") != "onCreate":
            continue
        for call in site.get("flow_collect_or_emit_calls", ()):
            callee = call.get("callee", {})
            if (call.get("class") == "LDp0;"
                    and callee.get("owner") == "Ljm4;"
                    and callee.get("method") == "for"):
                app_subscribes_ldp0 = True
                break
        if app_subscribes_ldp0:
            break

    call_targets = [
        event.get("callee")
        for trace in traces for event in trace.get("events", ())
        if event.get("kind") == "CALL" and event.get("callee")
    ]
    player_calls = [
        target for target in call_targets
        if target.get("owner") in PLAYER_OWNERS
        and target.get("method") in PLAYER_METHODS
    ]
    media_session_calls = [
        target for target in call_targets
        if classify_boundary_call((target.get("owner"), target.get("method"), target.get("signature"))) in (
            "MEDIA_SESSION_METADATA", "MEDIA_SESSION_STATE"
        )
    ]
    decoder_calls = [
        target for target in call_targets
        if classify_boundary_call((target.get("owner"), target.get("method"), target.get("signature"))) == "DECODER_BOUNDARY"
    ]
    source_calls = [
        target for target in call_targets
        if (target.get("owner"), target.get("method")) in SOURCE_METHODS
    ]
    return {
        "scope": "LzD7 interface, its direct implementers, and the exact LBy4/LDp0 Track-flow path",
        "source_interface": interface,
        "source_interface_is_abstract": bool(
            class_profiles.get(interface, {}).get("is_abstract")
        ),
        "direct_implementers": implementers,
        "flow_object_profile": privacy_safe_flow_class_profile(
            class_profiles.get("LD3a;")
        ),
        "implementation_dependency_profiles": {
            owner: privacy_safe_flow_class_profile(class_profiles.get(owner))
            for owner in ("LAF7;", "LWM7;", "LyG7;", "LMG7;", "LMG7$a;")
        },
        "ym_application_on_create_subscribes_ldp0": app_subscribes_ldp0,
        "flow_path": [
            "LzD7.if() -> LC3a Flow",
            "LBD7.if(LzD7) -> LBy4 Flow",
            "LBC3 -> LzC3 -> LAC3 -> LO6.native",
            "Ljm4.for(Flow, CoroutineScope, LDp0 collector)",
            "LDp0.if(Track) -> LGp0.new(Track)",
        ],
        "focused_method_traces": traces,
        "direct_player_api_call_count": len(player_calls),
        "direct_media_session_call_count": len(media_session_calls),
        "direct_decoder_boundary_call_count": len(decoder_calls),
        "direct_source_descriptor_call_count": len(source_calls),
        "same_track_reference_from_flow_to_lgp0_new_proven": False,
        "current_selected_track_proven": False,
        "same_native_item_to_decoder_proven": False,
        "branch_and_coroutine_resumption_inferred": False,
        "private_field_names_or_values_disclosed": False,
        "runtime_state_or_media_read": False,
    }

def local_object_register_origin(dex, method, flags, code_off, ins, before_ordinal, register, include_source_ordinal=False):
    """Bounded local origin for one object argument; no values or runtime inference."""
    current=register
    lower=max(-1,before_ordinal-33)
    for index in range(before_ordinal-1,lower,-1):
        _pc,op,words=ins[index]
        if op in (0x07,0x08,0x09):
            dest,source=move_object_registers(op,words)
            if dest==current:
                current=source
                continue
        if op==0x22:
            dest=words[0]>>8
            if dest==current:
                row={"kind":"NEW_INSTANCE","type":dex.descriptor(words[1])}
                if include_source_ordinal:
                    row["source_ordinal"]=index
                return row
        if op==0x54:
            dest=(words[0]>>8)&15
            if dest==current:
                owner,name,typ=field_id(dex,words[1])
                receiver=(words[0]>>12)&15
                return {"kind":"INSTANCE_FIELD_READ","owner":owner,
                        "field":name,"type":typ,
                        "receiver_is_this":receiver==(
                            dex.u16(code_off)-dex.u16(code_off+2)
                            if not flags&ACC_STATIC else -1
                        )}
        if op==0x62:
            dest=words[0]>>8
            if dest==current:
                owner,name,typ=field_id(dex,words[1])
                return {"kind":"STATIC_FIELD_READ","owner":owner,
                        "field":name,"type":typ}
        if op==0x0c:
            dest=words[0]>>8
            if dest==current:
                if index>0 and ins[index-1][1] in INVOKES:
                    callee=dex.method(ins[index-1][2][1])
                    return {"kind":"INVOKE_RESULT","owner":callee[0],
                            "method":callee[1],"signature":callee[2],
                            "return_type":callee[2].split(")",1)[1]}
                return {"kind":"MOVE_RESULT_OBJECT_UNRESOLVED"}
        if op in (0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=op<=0x3d:
            return {"kind":"BRANCH_BOUNDARY"}
        if written_register(op,words)==current:
            return {"kind":"OTHER_WRITE"}
    registers_size=dex.u16(code_off)
    ins_size=dex.u16(code_off+2)
    if ins_size>registers_size:
        raise DexError("FLOW_ARGUMENT_ORIGIN_INS_SIZE")
    param_reg=registers_size-ins_size
    this_reg=None
    if not flags&ACC_STATIC:
        this_reg=param_reg
        param_reg+=1
    if current==this_reg and this_reg is not None:
        return {"kind":"THIS_PARAMETER","type":method[0]}
    for position,typ in enumerate(parse_types(method[2])):
        if current==param_reg:
            return {"kind":"METHOD_PARAMETER","index":position,"type":typ}
        param_reg+=2 if typ in ("J","D") else 1
    return {"kind":"UNRESOLVED_LOCAL_REGISTER"}


def local_primitive_register_origin(dex, method, flags, code_off, ins, before_ordinal, register):
    """Bounded origin for primitive integer branch selectors; values are code constants only."""
    current=register
    lower=max(-1,before_ordinal-33)
    for index in range(before_ordinal-1,lower,-1):
        _pc,op,words=ins[index]
        if op in (0x01,0x02,0x03):
            if op==0x01:
                dest=(words[0]>>8)&15
                source=(words[0]>>12)&15
            elif op==0x02:
                dest=(words[0]>>8)&0xff
                source=words[1]
            else:
                dest=words[1]
                source=words[2]
            if dest==current:
                current=source
                continue
        if op in (0x12,0x13,0x14,0x15):
            if op==0x12:
                dest=(words[0]>>8)&15
                value=(words[0]>>12)&15
                if value&8:
                    value-=16
            elif op==0x13:
                dest=(words[0]>>8)&0xff
                value=words[1]
                if value&0x8000:
                    value-=0x10000
            elif op==0x14:
                dest=(words[0]>>8)&0xff
                value=words[1]|(words[2]<<16)
                if value&0x80000000:
                    value-=0x100000000
            else:
                dest=(words[0]>>8)&0xff
                value=words[1]<<16
                if value&0x80000000:
                    value-=0x100000000
            if dest==current:
                return {"kind":"CONST_INT","value":value}
        if 0x52<=op<=0x58:
            dest=(words[0]>>8)&15
            if dest==current:
                owner,name,typ=field_id(dex,words[1])
                if typ=="I":
                    return {"kind":"INSTANCE_INT_FIELD_READ","owner":owner,
                            "field":name,"type":typ}
                return {"kind":"OTHER_WRITE"}
        if 0x60<=op<=0x66:
            dest=(words[0]>>8)&0xff
            if dest==current:
                owner,name,typ=field_id(dex,words[1])
                if typ=="I":
                    return {"kind":"STATIC_INT_FIELD_READ","owner":owner,
                            "field":name,"type":typ}
                return {"kind":"OTHER_WRITE"}
        if op==0x0a:
            dest=(words[0]>>8)&0xff
            if dest==current:
                if index>0 and ins[index-1][1] in INVOKES:
                    callee=dex.method(ins[index-1][2][1])
                    return {"kind":"INVOKE_INT_RESULT","owner":callee[0],
                            "method":callee[1],"signature":callee[2]}
                return {"kind":"MOVE_RESULT_INT_UNRESOLVED"}
        if op in (0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=op<=0x3d:
            return {"kind":"BRANCH_BOUNDARY"}
        if written_register(op,words)==current:
            return {"kind":"OTHER_WRITE"}
    registers_size=dex.u16(code_off)
    ins_size=dex.u16(code_off+2)
    if ins_size>registers_size:
        raise DexError("FLOW_INT_ARGUMENT_ORIGIN_INS_SIZE")
    param_reg=registers_size-ins_size
    if not flags&ACC_STATIC:
        if current==param_reg:
            return {"kind":"THIS_PARAMETER","type":method[0]}
        param_reg+=1
    for position,typ in enumerate(parse_types(method[2])):
        if current==param_reg:
            return {"kind":"METHOD_PARAMETER","index":position,"type":typ}
        param_reg+=2 if typ in ("J","D") else 1
    return {"kind":"UNRESOLVED_LOCAL_REGISTER"}


def constructor_int_parameter_field_store_census(dex, method, flags, code_off):
    """Find constructor int parameters stored into int fields by bounded register moves."""
    if method[1]!="<init>":
        return []
    registers_size=dex.u16(code_off)
    ins_size=dex.u16(code_off+2)
    if ins_size>registers_size:
        raise DexError("FLOW_MODE_CTOR_INS_SIZE")
    param_reg=registers_size-ins_size
    if not flags&ACC_STATIC:
        param_reg+=1
    aliases={}
    for index,typ in enumerate(parse_types(method[2])):
        if typ=="I":
            aliases[param_reg]={index}
        param_reg+=2 if typ in ("J","D") else 1
    rows=[]
    for ordinal,(_pc,op,words) in enumerate(instructions(dex,code_off)):
        if op in (0x01,0x02,0x03):
            if op==0x01:
                dest=(words[0]>>8)&15
                source=(words[0]>>12)&15
            elif op==0x02:
                dest=(words[0]>>8)&0xff
                source=words[1]
            else:
                dest=words[1]
                source=words[2]
            if source in aliases:
                aliases[dest]=set(aliases[source])
            else:
                aliases.pop(dest,None)
            continue
        if op==0x59:
            value=(words[0]>>8)&15
            receiver=(words[0]>>12)&15
            owner,name,typ=field_id(dex,words[1])
            if typ=="I" and value in aliases:
                rows.append({"field_owner":owner,"field":name,"field_type":typ,
                             "source_int_parameter_indices":sorted(aliases[value]),
                             "receiver_is_this":receiver==(
                                 registers_size-ins_size if not flags&ACC_STATIC else -1
                             ),"ordinal":ordinal})
        elif op==0x67:
            value=words[0]>>8
            owner,name,typ=field_id(dex,words[1])
            if typ=="I" and value in aliases:
                rows.append({"field_owner":owner,"field":name,"field_type":typ,
                             "source_int_parameter_indices":sorted(aliases[value]),
                             "static_field":True,"ordinal":ordinal})
        else:
            dest=written_register(op,words)
            if dest is not None:
                aliases.pop(dest,None)
        if len(rows)>16:
            raise ValueError("FLOW_MODE_CTOR_FIELD_STORE_LIMIT")
    return rows


def logical_invoke_argument_rows(
    dex, method, flags, code_off, ins, ordinal, op, words, trace_origins=True
):
    """Describe logical argument positions and bounded object origins at one invoke."""
    callee=dex.method(words[1])
    registers=invoke_registers(op,words)
    is_static=op in (0x71,0x77)
    logical_types=(
        list(parse_types(callee[2])) if is_static
        else [callee[0]]+list(parse_types(callee[2]))
    )
    expanded=expand_invoke_register_types(
        callee[0],parse_types(callee[2]),is_static
    )
    if len(expanded)!=len(registers):
        raise DexError("FLOW_ARGUMENT_REGISTER_ARITY_MISMATCH")
    rows=[]
    word_index=0
    for logical_position,typ in enumerate(logical_types):
        register=registers[word_index]
        row={"logical_position":logical_position,"type":typ,"register":register}
        if trace_origins and typ.startswith(("L","[")):
            row["origin"]=local_object_register_origin(
                dex,method,flags,code_off,ins,ordinal,register
            )
        elif trace_origins and typ=="I":
            row["origin"]=local_primitive_register_origin(
                dex,method,flags,code_off,ins,ordinal,register
            )
        rows.append(row)
        word_index+=2 if typ in ("J","D") else 1
    return rows


def summarize_flow_entry_class_profiles(class_profiles):
    """Expose exact signed class relations/types only; do not infer active playback."""
    targets=(
        "LDp0;","LDp0$a;","Lwp0;","Lwp0$a;","Lyp0;","LGp0;",
        "LGl4;","LHl4;","Ljm4;","Lam4;","LzC3;","LAC3;",
        "LBC3;","LO6;","LBy4;","Lvp0;","LzD7;","LBD7;",
        "LAp0;","Lxp0;","LUK6;","LDb1;","LC3a;","LgE6;",
        "LDw8;","LAD7;","LzE7;","Lnn4;","Lhw9;","LcE6;",
        "LAE7;","Lup0;","LAy4;","LMG7;","LD3a;","LAF7;","LWM7;","LyG7;","LMG7$a;","LJw4;","LPG1;","Lur1;",
        "Lkh;","Lrm4;","LBC3$a;","LAC3$a;","LsF4;","LyC3;",
        "Liw9;","LAg1;","LMG7;","LD3a;","LAF7;","LWM7;","LyG7;","LMG7$a;","YMApplication;"
    )
    rows=[]
    for owner in targets:
        profile=class_profiles.get(owner)
        if profile is None:
            rows.append({"owner":owner,"defined_in_signed_dex":False})
            continue
        interfaces=sorted(profile.get("interfaces",()))
        rows.append({
            "owner":owner,
            "defined_in_signed_dex":True,
            "superclass":profile.get("superclass"),
            "interfaces":interfaces,
            "is_interface":profile.get("is_interface",False),
            "is_abstract":profile.get("is_abstract",False),
            "implements_flow_source_directly":"LGl4;" in interfaces,
            "implements_flow_collector_directly":"LHl4;" in interfaces,
            "instance_field_type_descriptors":sorted(profile.get("instance_types",())),
            "static_field_type_descriptors":sorted(profile.get("static_types",()))
        })
    return rows


def summarize_flow_interface_implementers(class_profiles):
    """List exact direct implementers of selected source/collector interfaces."""
    targets=("LzD7;","LC3a;","Lhw9;","LcE6;","LAg1;","Liw9;","LGl4;","LHl4;","LBK1;","LGK1$a;")
    rows=[]
    for interface in targets:
        profile=class_profiles.get(interface)
        implementers=sorted(
            owner for owner,entry in class_profiles.items()
            if interface in entry.get("interfaces",())
        )
        subclasses=sorted(
            owner for owner,entry in class_profiles.items()
            if entry.get("superclass")==interface
        )
        rows.append({
            "interface":interface,
            "defined_in_signed_dex":profile is not None,
            "is_interface":bool(profile and profile.get("is_interface")),
            "is_abstract":bool(profile and profile.get("is_abstract")),
            "superinterfaces":sorted(profile.get("interfaces",())) if profile else [],
            "direct_implementer_count":len(implementers),
            "direct_implementers":implementers[:64],
            "direct_subclass_count":len(subclasses),
            "direct_subclasses":subclasses[:64]
        })
    return rows


def selected_track_interface_implementation_owners(class_profiles, interface_owners):
    """Resolve only direct implementers/subclasses and their superclass method owners."""
    result = {}
    total_implementers = 0
    total_method_owners = 0
    for interface in sorted(set(interface_owners)):
        profile = class_profiles.get(interface)
        direct_implementers = sorted(
            owner for owner, entry in class_profiles.items()
            if interface in entry.get("interfaces", ())
        )
        direct_subclasses = sorted(
            owner for owner, entry in class_profiles.items()
            if entry.get("superclass") == interface
        )
        implementers = direct_implementers if profile and profile.get("is_interface") else direct_subclasses
        total_implementers += len(implementers)
        if total_implementers > 64:
            raise ValueError("SELECTED_TRACK_INTERFACE_IMPLEMENTER_LIMIT")
        owner_to_implementers = {}
        for implementer in implementers:
            current = implementer
            seen = set()
            depth = 0
            while current and current in class_profiles and current not in seen:
                seen.add(current)
                owner_to_implementers.setdefault(current, set()).add(implementer)
                depth += 1
                if depth > 16:
                    raise ValueError("SELECTED_TRACK_INTERFACE_SUPERCLASS_DEPTH")
                current = class_profiles.get(current, {}).get("superclass")
            total_method_owners += len(seen)
            if total_method_owners > 128:
                raise ValueError("SELECTED_TRACK_INTERFACE_METHOD_OWNER_LIMIT")
        result[interface] = {
            "defined_in_signed_dex": profile is not None,
            "is_interface": bool(profile and profile.get("is_interface")),
            "is_abstract": bool(profile and profile.get("is_abstract")),
            "direct_implementers": direct_implementers,
            "direct_subclasses": direct_subclasses,
            "implementer_profiles": [
                {
                    "owner": implementer,
                    "is_interface": bool(class_profiles.get(implementer, {}).get("is_interface")),
                    "is_abstract": bool(class_profiles.get(implementer, {}).get("is_abstract")),
                    "superclass": class_profiles.get(implementer, {}).get("superclass"),
                    "interfaces": sorted(class_profiles.get(implementer, {}).get("interfaces", ())),
                }
                for implementer in implementers
            ],
            "implementation_owners": {
                owner: sorted(owners)
                for owner, owners in sorted(owner_to_implementers.items())
            },
        }
    return result


def inspect_selected_track_interface_implementations(apks, class_profiles, contract_refs):
    """Trace only exact Track callback/Flow contracts on direct implementers and superclasses."""
    interface_owners = {"LBK1;", "LGK1$a;"}
    owner_map = selected_track_interface_implementation_owners(
        class_profiles, interface_owners
    )
    contract_shapes = {
        owner: {
            (method[1], method[2])
            for method in contract_refs if method[0] == owner
        }
        for owner in interface_owners
    }
    scan_owner_to_interfaces = {}
    scan_owner_to_implementers = {}
    for interface, row in owner_map.items():
        for owner, implementers in row["implementation_owners"].items():
            scan_owner_to_interfaces.setdefault(owner, set()).add(interface)
            scan_owner_to_implementers.setdefault((interface, owner), set()).update(implementers)
    implementation_traces = []
    if scan_owner_to_interfaces:
        for apk in apks:
            with zipfile.ZipFile(apk) as archive:
                for entry in archive.infolist():
                    if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                        continue
                    if entry.file_size > DEX_MAX:
                        raise ValueError("SELECTED_TRACK_INTERFACE_DEX_LIMIT")
                    dex = Dex(archive.read(entry.filename))
                    for method, flags, code_off in method_definitions_with_flags(dex):
                        matching_interfaces = [
                            interface for interface in scan_owner_to_interfaces.get(method[0], ())
                            if (method[1], method[2]) in contract_shapes[interface]
                        ]
                        if not matching_interfaces:
                            continue
                        if not (flags & 0x1):  # interface implementations must be public
                            continue
                        for interface in sorted(matching_interfaces):
                            if len(implementation_traces) >= 128:
                                raise ValueError("SELECTED_TRACK_INTERFACE_TRACE_LIMIT")
                            implementation_traces.append({
                                "interface": interface,
                                "implementer_classes": sorted(
                                    scan_owner_to_implementers.get((interface, method[0]), ())
                                ),
                                "method": {
                                    "owner": method[0],
                                    "name": method[1],
                                    "signature": method[2],
                                },
                                "trace": trace_identity_method(
                                    dex, method, flags, code_off,
                                    candidate_owners=set()
                                ),
                            })
    return {
        "interface_contracts": [
            {
                "owner": owner,
                "method_count": len(contract_shapes[owner]),
                "methods": [
                    {"name": name, "signature": signature}
                    for name, signature in sorted(contract_shapes[owner])
                ],
            }
            for owner in sorted(interface_owners)
        ],
        "owner_map": owner_map,
        "implementation_trace_count": len(implementation_traces),
        "implementation_traces": implementation_traces,
        "only_exact_track_contract_shapes_scanned": True,
    }


def exact_track_return_owner_scope(class_profiles, owner="LaC7;"):
    """Resolve only the exact Track-return owner, direct implementers/subclasses and their ancestry."""
    profile = class_profiles.get(owner)
    direct_implementers = sorted(
        candidate for candidate, entry in class_profiles.items()
        if owner in entry.get("interfaces", ())
    )
    direct_subclasses = sorted(
        candidate for candidate, entry in class_profiles.items()
        if entry.get("superclass") == owner
    )
    if len(direct_implementers) + len(direct_subclasses) > 64:
        raise ValueError("TRACK_RETURN_OWNER_DIRECT_RELATION_LIMIT")

    if profile and profile.get("is_interface"):
        candidate_roots = direct_implementers
        candidate_root_kind = "DIRECT_INTERFACE_IMPLEMENTERS"
    elif profile:
        candidate_roots = direct_subclasses
        candidate_root_kind = "DIRECT_CLASS_SUBCLASSES"
    else:
        candidate_roots = sorted(set(direct_implementers + direct_subclasses))
        candidate_root_kind = "OWNER_UNDEFINED_REFERENCED_RELATIONS"

    roots = ([owner] if profile else []) + candidate_roots
    scan_owner_to_roots = {}
    ancestry_by_owner = {}
    for root in roots:
        for row in owner_ancestry_profiles(root, class_profiles):
            ancestry_by_owner[row["owner"]] = row
            scan_owner_to_roots.setdefault(row["owner"], set()).add(root)
    if len(scan_owner_to_roots) > 128:
        raise ValueError("TRACK_RETURN_OWNER_METHOD_OWNER_LIMIT")

    return {
        "owner": owner,
        "owner_defined_in_signed_dex": profile is not None,
        "owner_is_interface": bool(profile and profile.get("is_interface")),
        "owner_is_abstract": bool(profile and profile.get("is_abstract")),
        "owner_superclass": profile.get("superclass") if profile else None,
        "owner_interfaces": sorted(profile.get("interfaces", ())) if profile else [],
        "direct_implementer_count": len(direct_implementers),
        "direct_implementers": direct_implementers,
        "direct_subclass_count": len(direct_subclasses),
        "direct_subclasses": direct_subclasses,
        "candidate_root_kind": candidate_root_kind,
        "candidate_roots": roots,
        "ancestry_profiles": [
            ancestry_by_owner[key] for key in sorted(ancestry_by_owner)
        ],
        "scan_owner_to_roots": {
            key: sorted(value) for key, value in sorted(scan_owner_to_roots.items())
        },
    }


def inspect_exact_track_return_owner_implementations(apks, class_profiles):
    """Trace only concrete if():Track bodies on LaC7, its ancestry and direct implementations."""
    owner = "LaC7;"
    method_name = "if"
    signature = f"(){MODEL}"
    scope = exact_track_return_owner_scope(class_profiles, owner)
    scan_owners = set(scope["scan_owner_to_roots"])
    method_bodies = []
    if scan_owners:
        for apk in apks:
            with zipfile.ZipFile(apk) as archive:
                for entry in archive.infolist():
                    if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                        continue
                    if entry.file_size > DEX_MAX:
                        raise ValueError("TRACK_RETURN_OWNER_DEX_LIMIT")
                    dex = Dex(archive.read(entry.filename))
                    for method, flags, code_off in method_definitions_with_flags(dex):
                        if (
                            method[0] not in scan_owners
                            or method[1] != method_name
                            or method[2] != signature
                        ):
                            continue
                        if len(method_bodies) >= 64:
                            raise ValueError("TRACK_RETURN_OWNER_METHOD_BODY_LIMIT")
                        method_bodies.append({
                            "method": {
                                "owner": method[0],
                                "name": method[1],
                                "signature": method[2],
                            },
                            "candidate_roots": scope["scan_owner_to_roots"][method[0]],
                            "trace": trace_identity_method(
                                dex, method, flags, code_off,
                                candidate_owners=set(),
                                capture_unproven_calls=True,
                            ),
                        })
    return {
        **scope,
        "exact_method_signature": signature,
        "concrete_method_body_count": len(method_bodies),
        "concrete_method_bodies": method_bodies,
        "concrete_body_declared_on_owner": any(
            row["method"]["owner"] == owner for row in method_bodies
        ),
        "concrete_body_found_in_scoped_signed_owners": bool(method_bodies),
        "only_exact_if_return_track_signature_scanned": True,
        "runtime_dispatch_proven": False,
    }


def safe_object_register_origin(origin):
    """Expose only safe origin categories/types; never disclose field identifiers or values."""
    if not origin:
        return None
    allowed = (
        "kind", "type", "return_type", "receiver_is_this",
        "index", "source_ordinal", "owner", "method", "signature"
    )
    return {key: origin[key] for key in allowed if key in origin}




def dex_type_assignable_to(actual_type, expected_type, class_profiles):
    """Resolve only signed class/interface ancestry for one exact type pair."""
    if actual_type == expected_type:
        return True
    if not isinstance(actual_type, str) or not actual_type.startswith("L"):
        return False
    pending = [actual_type]
    visited = set()
    while pending:
        current = pending.pop()
        if current == expected_type:
            return True
        if current in visited:
            continue
        visited.add(current)
        if len(visited) > 128:
            raise ValueError("DEX_TYPE_ASSIGNABILITY_LIMIT")
        profile = class_profiles.get(current, {})
        superclass = profile.get("superclass")
        if superclass and superclass != "Ljava/lang/Object;":
            pending.append(superclass)
        pending.extend(profile.get("interfaces", ()))
    return False


def trace_exact_object_receiver_call_cfg(
    dex, method, flags, code_off, target_method, tracked_type, class_profiles
):
    """Must-alias trace to one exact invoke receiver across all reachable CFG paths.

    Tracks only object references assignable to tracked_type. It never reads
    field values, media, strings, URLs, account state, or audio. Different
    allocations retain different instruction-site identities.
    """
    if not isinstance(tracked_type, str) or not tracked_type.startswith("L"):
        raise ValueError("RECEIVER_TRACE_TYPE_INVALID")
    cfg = build_dex_control_flow(dex, code_off)
    by_pc = cfg["by_pc"]
    successors = cfg["successors"]
    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        raise DexError("RECEIVER_TRACE_INVALID_INS_SIZE")
    initial_registers = {}
    parameter_register = registers_size - ins_size
    if not (flags & ACC_STATIC):
        this_kind = (
            "TYPED_THIS" if dex_type_assignable_to(method[0], tracked_type, class_profiles)
            else "UNREFINED_THIS"
        )
        initial_registers[parameter_register] = frozenset({
            f"{this_kind}:{method[0]}"
        })
        parameter_register += 1
    for index, parameter_type in enumerate(parse_types(method[2])):
        if parameter_type.startswith(("L", "[")):
            parameter_kind = (
                "TYPED_PARAMETER"
                if dex_type_assignable_to(parameter_type, tracked_type, class_profiles)
                else "UNREFINED_PARAMETER"
            )
            initial_registers[parameter_register] = frozenset({
                f"{parameter_kind}:{parameter_type}@{index}"
            })
        parameter_register += 2 if parameter_type in ("J", "D") else 1
    initial_state = {
        "registers": initial_registers,
        "pending_return": None,
    }

    def state_key(state):
        return (
            tuple(
                (register, tuple(sorted(origins)))
                for register, origins in sorted(state["registers"].items())
            ),
            state["pending_return"],
        )

    incoming = {cfg["entry"]: {state_key(initial_state): initial_state}}
    work = [(cfg["entry"], state_key(initial_state))]
    processed = 0
    wide_ops = (
        {0x04, 0x05, 0x06, 0x0b, 0x16, 0x17, 0x18, 0x19,
         0x45, 0x53, 0x61, 0x7d, 0x7e, 0x80, 0x82, 0x85, 0x87,
         0x88, 0x8a}
        | set(range(0x9b, 0xa6))
        | set(range(0xab, 0xb0))
        | set(range(0xbb, 0xc6))
        | set(range(0xcb, 0xd0))
    )

    def transfer(state, pc, op, words):
        registers = {
            register: set(origins)
            for register, origins in state["registers"].items()
        }
        pending_return = None

        def clear(register):
            registers.pop(register, None)

        if op in INVOKES:
            callee = dex.method(words[1])
            result_type = callee[2].split(")", 1)[1]
            if result_type.startswith(("L", "[")):
                return_kind = (
                    "RETURNED_FROM_METHOD"
                    if dex_type_assignable_to(result_type, tracked_type, class_profiles)
                    else "UNREFINED_OBJECT_RETURN"
                )
                pending_return = (
                    return_kind + ":"
                    + callee[0] + "|" + callee[1] + "|" + callee[2]
                    + "@" + str(pc)
                )
            return {
                "registers": {
                    register: frozenset(origins)
                    for register, origins in registers.items() if origins
                },
                "pending_return": pending_return,
            }

        if op == 0x0c:  # move-result-object
            destination = words[0] >> 8
            clear(destination)
            if state["pending_return"]:
                registers[destination] = {state["pending_return"]}
            return {
                "registers": {
                    register: frozenset(origins)
                    for register, origins in registers.items() if origins
                },
                "pending_return": None,
            }

        if op == 0x22:  # new-instance
            destination = (words[0] >> 8) & 0xff
            object_type = dex.descriptor(words[1])
            clear(destination)
            instance_kind = (
                "NEW_INSTANCE"
                if dex_type_assignable_to(object_type, tracked_type, class_profiles)
                else "UNREFINED_NEW_INSTANCE"
            )
            registers[destination] = {
                f"{instance_kind}:{object_type}@{pc}"
            }
        elif op == 0x54:  # iget-object; type and receiver only
            destination = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            _field_owner, _field_name, field_type = field_id(dex, words[1])
            receiver_origins = registers.get(receiver, set())
            clear(destination)
            if field_type.startswith(("L", "[")):
                receiver_is_this = any(
                    origin.startswith(("TYPED_THIS:", "UNREFINED_THIS:"))
                    for origin in receiver_origins
                )
                category = (
                    "FIELD_READ_FROM_THIS" if receiver_is_this else
                    "FIELD_READ_FROM_TYPED_RECEIVER" if receiver_origins else
                    "FIELD_READ_FROM_UNKNOWN_RECEIVER"
                )
                if not dex_type_assignable_to(field_type, tracked_type, class_profiles):
                    category = "UNREFINED_" + category
                registers[destination] = {
                    f"{category}:{field_type}@{pc}"
                }
        elif op == 0x62:  # sget-object; type only
            destination = (words[0] >> 8) & 0xff
            _field_owner, _field_name, field_type = field_id(dex, words[1])
            clear(destination)
            if field_type.startswith(("L", "[")):
                category = (
                    "STATIC_FIELD_READ"
                    if dex_type_assignable_to(field_type, tracked_type, class_profiles)
                    else "UNREFINED_STATIC_FIELD_READ"
                )
                registers[destination] = {
                    f"{category}:{field_type}@{pc}"
                }
        elif op in (0x07, 0x08, 0x09):  # move-object
            move = move_object_registers(op, words)
            if move:
                destination, source = move
                origins = set(registers.get(source, ()))
                clear(destination)
                if origins:
                    registers[destination] = origins
        elif op == 0x1f:  # check-cast preserves object identity
            register = (words[0] >> 8) & 0xff
            cast_type = dex.descriptor(words[1])
            if (
                register in registers
                and dex_type_assignable_to(cast_type, tracked_type, class_profiles)
            ):
                registers[register].add(f"CHECK_CAST:{cast_type}@{pc}")
        elif op == 0x5b:  # iput-object does not mutate source identity
            pass
        else:
            destination = written_register(op, words)
            if destination is not None:
                clear(destination)
                if op in wide_ops:
                    clear(destination + 1)
        return {
            "registers": {
                register: frozenset(origins)
                for register, origins in registers.items() if origins
            },
            "pending_return": None,
        }

    while work:
        pc, key = work.pop()
        processed += 1
        if processed > 200000:
            raise ValueError("RECEIVER_TRACE_CFG_DATAFLOW_LIMIT")
        state = incoming[pc][key]
        op, words = by_pc[pc]
        output = transfer(state, pc, op, words)
        output_key = state_key(output)
        for next_pc in successors.get(pc, ()):
            bucket = incoming.setdefault(next_pc, {})
            if output_key in bucket:
                continue
            if len(bucket) >= 128:
                raise ValueError("RECEIVER_TRACE_CFG_PATH_STATE_LIMIT")
            bucket[output_key] = output
            work.append((next_pc, output_key))

    callsites = []
    for pc in sorted(cfg["reachable"]):
        op, words = by_pc[pc]
        if op not in INVOKES or dex.method(words[1]) != target_method:
            continue
        registers = invoke_registers(op, words)
        states = list(incoming.get(pc, {}).values())
        if not registers or not states:
            continue
        receiver_register = registers[0]
        path_origins = [
            sorted(state["registers"].get(receiver_register, ()))
            for state in states
        ]
        common = set(path_origins[0]) if path_origins else set()
        for origins in path_origins[1:]:
            common.intersection_update(origins)
        common_rows = sorted(common)
        receiver_type_proven = any(
            origin.startswith(("TYPED_THIS:", "TYPED_PARAMETER:",
                               "NEW_INSTANCE:", "RETURNED_FROM_METHOD:",
                               "FIELD_READ_FROM_THIS:", "FIELD_READ_FROM_TYPED_RECEIVER:",
                               "FIELD_READ_FROM_UNKNOWN_RECEIVER:",
                               "STATIC_FIELD_READ:", "CHECK_CAST:"))
            for origin in common_rows
        )
        callsites.append({
            "pc": pc,
            "invoke_kind": invoke_kind_name(op),
            "receiver_register": receiver_register,
            "declared_receiver_type": target_method[0],
            "receiver_origins_common_to_all_paths": common_rows,
            "receiver_origins_by_path": path_origins[:32],
            "incoming_path_state_count": len(states),
            "receiver_identity_proven_on_all_paths": bool(common),
            "receiver_type_proven_on_all_paths": receiver_type_proven,
            "exact_lya_instance_proven_on_all_paths": any(
                origin.startswith("NEW_INSTANCE:LyEa;@") for origin in common_rows
            ),
            "runtime_dispatch_to_lya_proven": False,
        })
        if len(callsites) > 8:
            raise ValueError("RECEIVER_TRACE_CALLSITE_LIMIT")

    return {
        "method": {
            "owner": method[0],
            "method": method[1],
            "signature": method[2],
        },
        "target": {
            "owner": target_method[0],
            "method": target_method[1],
            "signature": target_method[2],
        },
        "tracked_type": tracked_type,
        "callsite_count": len(callsites),
        "callsites": callsites,
        "reachable_instruction_count": len(cfg["reachable"]),
        "branch_count": len(cfg["branches"]),
        "dataflow_instruction_visits": processed,
        "runtime_dispatch_or_active_selected_item_inferred": False,
        "private_field_names_or_values_disclosed": False,
        "field_values_or_media_read": False,
    }



def inspect_lya_track_holder(apks, class_profiles):
    """Trace only LyEa's Track field and the two LCK1 LaC7.if() coroutine callsites."""
    owner = "LyEa;"
    lya_if_method = (owner, "if", f"(){MODEL}")
    interface_method = ("LaC7;", "if", f"(){MODEL}")
    provider_method = ("LzA9;", "if", "()LaC7;")
    lck1_owners = {"LCK1$c$a;", "LCK1$h$a;"}

    track_field_refs = set()
    lya_if_traces = []
    provider_traces = []
    lya_constructor_refs = set()
    lya_constructor_track_field_store_traces = []

    # Find the exact Track field read by LyEa.if(), plus the one known LaC7 provider.
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("LYA_FOCUS_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                for method, flags, code_off in method_definitions_with_flags(dex):
                    if method == lya_if_method:
                        refs = exact_instance_field_read_refs(
                            dex, method, flags, code_off, MODEL
                        )
                        track_field_refs.update(refs)
                        lya_if_traces.append({
                            "method": {"owner": method[0], "name": method[1],
                                       "signature": method[2]},
                            "exact_track_field_read_count": len(refs),
                            "trace": trace_identity_method(
                                dex, method, flags, code_off,
                                candidate_owners=set(),
                                capture_unproven_calls=True,
                                exact_track_field_refs=set(refs),
                            ),
                        })
                    if method == provider_method:
                        provider_traces.append({
                            "method": {"owner": method[0], "name": method[1],
                                       "signature": method[2]},
                            "trace": trace_identity_method(
                                dex, method, flags, code_off,
                                candidate_owners=set(),
                                capture_unproven_calls=True,
                                extra_identity_types={"LaC7;", owner},
                            ),
                        })
                        if len(provider_traces) > 4:
                            raise ValueError("LA_C7_PROVIDER_TRACE_LIMIT")

    # Find every write to that one Track field, regardless of which signed class owns the writer.
    field_writer_rows = []
    writer_method_refs = set()
    lck1_interface_call_sites = []
    lck1_constructor_refs = set()
    lck1_constructor_field_links = []

    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > DEX_MAX:
                    raise ValueError("LYA_WRITER_SCAN_DEX_LIMIT")
                dex = Dex(archive.read(entry.filename))
                definitions = list(method_definitions_with_flags(dex))
                for method, flags, code_off in definitions:
                    exact_writes = []
                    exact_interface_calls = []
                    for ordinal, (_pc, op, words) in enumerate(instructions(dex, code_off)):
                        if op == 0x5b and track_field_refs:
                            if field_id(dex, words[1]) in track_field_refs:
                                exact_writes.append((ordinal, words))
                        if method[0] in lck1_owners and op in INVOKES:
                            if dex.method(words[1]) == interface_method:
                                exact_interface_calls.append(ordinal)

                    if exact_writes:
                        if len(field_writer_rows) >= 32:
                            raise ValueError("LYA_TRACK_FIELD_WRITER_METHOD_LIMIT")
                        writer_method_refs.add(method)
                        if method[0] == owner and method[1] == "<init>" and MODEL in parse_types(method[2]):
                            lya_constructor_refs.add(method)
                            for target_field in sorted(track_field_refs):
                                store_trace = trace_track_value_to_exact_field_store(
                                    dex, method, flags, code_off, target_field
                                )
                                lya_constructor_track_field_store_traces.append({
                                    "method": {
                                        "owner": method[0], "name": method[1],
                                        "signature": method[2],
                                    },
                                    "target_field_type": target_field[2],
                                    "trace": store_trace,
                                })
                                if len(lya_constructor_track_field_store_traces) > 8:
                                    raise ValueError("LYA_CONSTRUCTOR_FIELD_TRACE_LIMIT")
                        trace = trace_identity_method(
                            dex, method, flags, code_off,
                            candidate_owners=set(),
                            capture_unproven_calls=True,
                            track_fields_from_any_receiver=True,
                        )
                        write_ordinals = {ordinal for ordinal, _words in exact_writes}
                        field_writer_rows.append({
                            "method": {"owner": method[0], "name": method[1],
                                       "signature": method[2]},
                            "exact_track_field_write_count": len(exact_writes),
                            "track_identity_store_events": [
                                {
                                    "ordinal": event.get("ordinal"),
                                    "kind": event.get("kind"),
                                    "identity_type": event.get("identity_type"),
                                    "receiver_is_this": event.get("receiver_is_this"),
                                    "origins": event.get("origins"),
                                }
                                for event in trace.get("events", [])
                                if event.get("ordinal") in write_ordinals
                                and event.get("kind") == "INSTANCE_FIELD_STORE_TYPED_IDENTITY"
                            ],
                        })

                    if exact_interface_calls:
                        if len(lck1_interface_call_sites) >= 4:
                            raise ValueError("LCK1_LAC7_CALLSITE_LIMIT")
                        trace = trace_identity_method(
                            dex, method, flags, code_off,
                            candidate_owners=set(),
                            capture_unproven_calls=True,
                            extra_identity_types={"LaC7;"},
                        )
                        ins = list(instructions(dex, code_off))
                        receiver_argument_origins = []
                        for call_ordinal in exact_interface_calls:
                            _call_pc, call_op, call_words = ins[call_ordinal]
                            argument_rows = logical_invoke_argument_rows(
                                dex, method, flags, code_off, ins,
                                call_ordinal, call_op, call_words,
                                trace_origins=True,
                            )
                            if argument_rows:
                                receiver_row = argument_rows[0]
                                receiver_argument_origins.append({
                                    "callsite_ordinal": call_ordinal,
                                    "receiver_register": receiver_row["register"],
                                    "declared_receiver_type": receiver_row["type"],
                                    "local_origin": safe_object_register_origin(
                                        receiver_row.get("origin")
                                    ),
                                })
                        receiver_cfg_trace = trace_exact_object_receiver_call_cfg(
                            dex, method, flags, code_off,
                            interface_method, "LaC7;", class_profiles
                        )
                        receiver_field_refs = set(exact_instance_field_read_refs(
                            dex, method, flags, code_off, "LaC7;"
                        ))
                        call_events = [
                            event for event in trace.get("events", [])
                            if event.get("callee") == {
                                "owner": interface_method[0],
                                "method": interface_method[1],
                                "signature": interface_method[2],
                            }
                        ]
                        # The interface receiver field is accepted only when the same field
                        # is populated from a LaC7-typed constructor parameter.
                        ancestry = []
                        current = method[0]
                        seen = set()
                        while current and current not in seen and len(ancestry) < 16:
                            seen.add(current)
                            ancestry.append(current)
                            profile = class_profiles.get(current)
                            current = profile.get("superclass") if profile else None
                        constructor_links = []
                        for ctor_method, ctor_flags, ctor_code_off in definitions:
                            if ctor_method[0] not in ancestry or ctor_method[1] != "<init>":
                                continue
                            stored_refs = set(exact_parameter_field_store_refs(
                                dex, ctor_method, ctor_flags, ctor_code_off, "LaC7;"
                            ))
                            matched_refs = stored_refs.intersection(receiver_field_refs)
                            if matched_refs:
                                if len(lck1_constructor_refs) >= 32:
                                    raise ValueError("LCK1_CONSTRUCTOR_REF_LIMIT")
                                lck1_constructor_refs.add(ctor_method)
                                link = {
                                    "constructor": {
                                        "owner": ctor_method[0], "name": ctor_method[1],
                                        "signature": ctor_method[2],
                                    },
                                    "same_receiver_field_store_count": len(matched_refs),
                                }
                                constructor_links.append(link)
                                lck1_constructor_field_links.append(link)
                        lck1_interface_call_sites.append({
                            "caller": {"owner": method[0], "name": method[1],
                                       "signature": method[2]},
                            "target": {"owner": interface_method[0],
                                       "name": interface_method[1],
                                       "signature": interface_method[2]},
                            "callsite_ordinals": exact_interface_calls,
                            "receiver_field_read_count": len(receiver_field_refs),
                            "receiver_argument_origins": receiver_argument_origins,
                            "receiver_cfg_trace": receiver_cfg_trace,
                            "receiver_identity_call_events": [
                                {
                                    "ordinal": event.get("ordinal"),
                                    "kind": event.get("kind"),
                                    "identity_arguments": event.get("identity_arguments", []),
                                }
                                for event in call_events
                            ],
                            "matching_constructor_field_links": constructor_links,
                        })

    # Trace only constructor callsites that populate the exact receiver field used by LCK1.
    lck1_constructor_call_sites = []
    if lck1_constructor_refs:
        for apk in apks:
            with zipfile.ZipFile(apk) as archive:
                for entry in archive.infolist():
                    if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                        continue
                    dex = Dex(archive.read(entry.filename))
                    for method, flags, code_off in method_definitions_with_flags(dex):
                        candidate_calls = []
                        for ordinal, (_pc, op, words) in enumerate(instructions(dex, code_off)):
                            if op in INVOKES and dex.method(words[1]) in lck1_constructor_refs:
                                candidate_calls.append((ordinal, op, words, dex.method(words[1])))
                        if not candidate_calls:
                            continue
                        if len(lck1_constructor_call_sites) + len(candidate_calls) > 32:
                            raise ValueError("LCK1_CONSTRUCTOR_CALLSITE_LIMIT")
                        ins = list(instructions(dex, code_off))
                        trace = trace_identity_method(
                            dex, method, flags, code_off,
                            candidate_owners=set(),
                            capture_unproven_calls=True,
                            extra_identity_types={"LaC7;", owner},
                        )
                        for ordinal, op, words, callee in candidate_calls:
                            argument_rows = logical_invoke_argument_rows(
                                dex, method, flags, code_off, ins, ordinal, op, words,
                                trace_origins=False,
                            )
                            interface_args = [
                                row for row in argument_rows if row["type"] == "LaC7;"
                            ]
                            matching_event = next((
                                event for event in trace.get("events", [])
                                if event.get("ordinal") == ordinal
                                and event.get("callee") == {
                                    "owner": callee[0], "method": callee[1],
                                    "signature": callee[2],
                                }
                            ), None)
                            origins = []
                            for argument in interface_args:
                                raw_origin = local_object_register_origin(
                                    dex, method, flags, code_off, ins, ordinal,
                                    argument["register"], include_source_ordinal=True
                                )
                                origins.append(safe_object_register_origin(raw_origin))
                            lck1_constructor_call_sites.append({
                                "caller": {"owner": method[0], "name": method[1],
                                           "signature": method[2]},
                                "target": {"owner": callee[0], "name": callee[1],
                                           "signature": callee[2]},
                                "ordinal": ordinal,
                                "interface_argument_origins": origins,
                                "constructor_identity_arguments": (
                                    matching_event.get("identity_arguments", [])
                                    if matching_event else []
                                ),
                            })

    # Inspect only direct constructor calls for the exact LyEa constructor
    # that writes the Track field returned by LyEa.if().
    lya_constructor_call_sites = []
    if lya_constructor_refs:
        for apk in apks:
            with zipfile.ZipFile(apk) as archive:
                for entry in archive.infolist():
                    if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                        continue
                    if entry.file_size > DEX_MAX:
                        raise ValueError("LYA_CONSTRUCTOR_CALLSITE_DEX_LIMIT")
                    dex = Dex(archive.read(entry.filename))
                    for caller, caller_flags, caller_code_off in method_definitions_with_flags(dex):
                        ins = list(instructions(dex, caller_code_off))
                        for ordinal, (pc, op, words) in enumerate(ins):
                            if op not in INVOKES:
                                continue
                            callee = dex.method(words[1])
                            if callee not in lya_constructor_refs:
                                continue
                            argument_rows = logical_invoke_argument_rows(
                                dex, caller, caller_flags, caller_code_off,
                                ins, ordinal, op, words, trace_origins=True
                            )
                            receiver_row = argument_rows[0] if argument_rows else None
                            track_row = next((
                                row for row in argument_rows if row["type"] == MODEL
                            ), None)
                            lya_constructor_call_sites.append({
                                "caller": {
                                    "owner": caller[0], "name": caller[1],
                                    "signature": caller[2],
                                },
                                "target": {
                                    "owner": callee[0], "name": callee[1],
                                    "signature": callee[2],
                                },
                                "pc": pc,
                                "invoke_kind": invoke_kind_name(op),
                                "receiver_origin": safe_object_register_origin(
                                    receiver_row.get("origin") if receiver_row else None
                                ),
                                "track_argument_origin": safe_object_register_origin(
                                    track_row.get("origin") if track_row else None
                                ),
                                "track_argument_is_caller_track_parameter": bool(
                                    track_row
                                    and track_row.get("origin", {}).get("kind") == "METHOD_PARAMETER"
                                    and track_row.get("origin", {}).get("type") == MODEL
                                ),
                            })
                            if len(lya_constructor_call_sites) > 64:
                                raise ValueError("LYA_CONSTRUCTOR_CALLSITE_LIMIT")

    return {
        "owner": owner,
        "owner_defined_in_signed_dex": owner in class_profiles,
        "owner_has_track_field": bool(
            owner in class_profiles
            and classify_track_owner_profile(class_profiles[owner])["has_track_field"]
        ),
        "lya_if_exact_track_field_count": len(track_field_refs),
        "lya_if_method_traces": lya_if_traces,
        "exact_track_field_writer_method_count": len(field_writer_rows),
        "exact_track_field_writers": field_writer_rows,
        "lya_constructor_track_field_store_traces": lya_constructor_track_field_store_traces,
        "lya_constructor_callsite_count": len(lya_constructor_call_sites),
        "lya_constructor_call_sites": lya_constructor_call_sites,
        "provider_owner_defined_in_signed_dex": "LzA9;" in class_profiles,
        "provider_owner_profile": ({
            "is_interface": bool(class_profiles["LzA9;"].get("is_interface")),
            "is_abstract": bool(class_profiles["LzA9;"].get("is_abstract")),
            "superclass": class_profiles["LzA9;"].get("superclass"),
            "interfaces": sorted(class_profiles["LzA9;"].get("interfaces", ())),
        } if "LzA9;" in class_profiles else None),
        "provider_method_body_count": len(provider_traces),
        "lck1_interface_callsite_count": len(lck1_interface_call_sites),
        "lck1_interface_call_sites": lck1_interface_call_sites,
        "lck1_constructor_field_link_count": len(lck1_constructor_field_links),
        "lck1_constructor_field_links": lck1_constructor_field_links,
        "lck1_constructor_callsite_count": len(lck1_constructor_call_sites),
        "lck1_constructor_call_sites": lck1_constructor_call_sites,
        "lza9_provider_method_traces": provider_traces,
        "only_exact_lya_track_field_lck1_calls_and_lza9_provider_scanned": True,
        "active_selected_item_proven": False,
        "same_native_item_to_decoder_proven": False,
        "runtime_dispatch_to_lya_proven": False,
    }


def summarize_flow_mode_branch_census(dex, method, flags, code_off):
    """Map DEX branch selectors to field/parameter origins and exact branch targets."""
    cfg=build_dex_control_flow(dex,code_off)
    ins=cfg["instructions"]
    pc_to_ordinal={pc:i for i,(pc,_op,_words) in enumerate(ins)}
    rows=[]
    branch_names={
        0x2b:"PACKED_SWITCH",0x2c:"SPARSE_SWITCH",
        0x32:"IF_EQ",0x33:"IF_NE",0x34:"IF_LT",0x35:"IF_GE",
        0x36:"IF_GT",0x37:"IF_LE",0x38:"IF_EQZ",0x39:"IF_NEZ",
        0x3a:"IF_LTZ",0x3b:"IF_GEZ",0x3c:"IF_GTZ",0x3d:"IF_LEZ"
    }
    for branch in cfg["branches"]:
        pc=branch["pc"]
        ordinal=pc_to_ordinal[pc]
        op,words=cfg["by_pc"][pc]
        if op in (0x2b,0x2c):
            registers=[(words[0]>>8)&0xff]
        elif 0x32<=op<=0x37:
            registers=[(words[0]>>8)&15,(words[0]>>12)&15]
        elif 0x38<=op<=0x3d:
            registers=[(words[0]>>8)&15]
        else:
            registers=[]
        origins=[
            {"register":reg,"origin":local_primitive_register_origin(
                dex,method,flags,code_off,ins,ordinal,reg
            )}
            for reg in registers
        ]
        target_pcs=sorted(set(branch["target_pcs"]+branch["fallthrough_pcs"]))
        target_blocks=[]
        for target_pc in target_pcs:
            target_ordinal=pc_to_ordinal[target_pc]
            events=[]
            for n in range(target_ordinal,min(len(ins),target_ordinal+10)):
                _target_ins_pc,target_op,target_words=ins[n]
                if target_op==0x22:
                    events.append({"kind":"NEW_INSTANCE","type":dex.descriptor(target_words[1])})
                elif target_op in INVOKES:
                    callee=dex.method(target_words[1])
                    events.append({"kind":"INVOKE","owner":callee[0],
                                   "method":callee[1],"signature":callee[2]})
                elif target_op in (0x54,0x62):
                    owner,name,typ=field_id(dex,target_words[1])
                    events.append({"kind":"FIELD_READ","owner":owner,
                                   "field":name,"type":typ})
                elif target_op==0x1f:
                    events.append({"kind":"CHECK_CAST","type":dex.descriptor(target_words[1])})
                if target_op in (0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=target_op<=0x3d:
                    if n>target_ordinal:
                        break
            target_blocks.append({
                "target_pc":target_pc,"target_ordinal":target_ordinal,
                "leading_events":events[:6]
            })
        rows.append({
            "ordinal":ordinal,"pc":pc,"op":op,
            "branch_kind":branch_names.get(op,"OTHER_BRANCH"),
            "selector_register_origins":origins,
            "switch_cases":branch.get("switch_cases",[]),
            "target_blocks":target_blocks
        })
    return {
        "control_flow_graph_built":True,
        "branch_count":len(rows),
        "branch_sites":rows,
        "branch_feasibility_proven":False
    }


FLOW_RESEARCH_METHOD_REF_OWNERS = {
    "LDp0;","Lwp0;","Lyp0;","LBy4;","Lvp0;","LBD7;","LzD7;",
    "LC3a;","LgE6;","Lhw9;","LcE6;","LzE7;","Lnn4;",
    "LDw8;","LAD7;","LAE7;","Lup0;","LAy4;","LAp0;",
    "Lxp0;","LUK6;","LDb1;","LBC3;","LzC3;","LAC3;",
    "LJw4;","LPG1;","Lur1;","Lkh;","Lrm4;","LBC3$a;","LAC3$a;",
    "LsF4;","LyC3;","Liw9;","LAg1;"
}
FLOW_MODE_BRANCH_AUDIT_OWNERS = {
    "LBy4;","Lvp0;","Lyp0;","LzC3;","LBC3;","LAC3;","Lnn4;","LzE7;"
}


FLOW_MODE_CONSTRUCTOR_OWNERS = {"LBy4;","Lvp0;","Lyp0;","LzC3;"}

SELECTED_TRACK_PATH_METHODS = {
    # LSW6 is retained as an optional candidate; it is not defined in the pinned DEX.
    ("LSW6;", "if", "(Lru/yandex/music/data/audio/o;Z)LvU6;"),
    ("LOW6;", "<init>",
     "(LSV6;Lru/yandex/music/data/audio/o;ZLkotlinx/coroutines/CoroutineScope;"
     "Landroid/content/Context;LGK1$a;LNW6$a;)V"),
    # Exact Track recipients observed in LOW6.<init>; one bounded hop only.
    ("LTv9;", "if",
     "(LBK1;LGK1$a;Landroid/content/Context;Lkotlinx/coroutines/CoroutineScope;"
     "Lru/yandex/music/data/audio/o;Z)LJK1;"),
    ("LJK1;", "<init>",
     "(LBK1;LGK1$a;Landroid/content/Context;Lkotlinx/coroutines/CoroutineScope;"
     "Lru/yandex/music/data/audio/o;Z)V"),
    # Exact Track recipients called by LJK1.<init>; trace only these references.
    ("LBK1;", "try", "(Lru/yandex/music/data/audio/o;)LGl4;"),
    ("LBK1;", "this", "(Lru/yandex/music/data/audio/o;)LGl4;"),
    ("LBK1;", "for", "(Lru/yandex/music/data/audio/o;)LGl4;"),
    ("LBK1;", "new", "(Lru/yandex/music/data/audio/o;)LGl4;"),
    # Exact Track callbacks read from the retained LJK1 Track field.
    ("LGK1$a;", "try", "(Landroid/content/Context;Lru/yandex/music/data/audio/o;)V"),
    ("LGK1$a;", "case", "(Lru/yandex/music/data/audio/o;)V"),
    ("LGK1$a;", "else", "(Lru/yandex/music/data/audio/o;)V"),
    ("LGK1$a;", "goto", "(Lru/yandex/music/data/audio/o;)V"),
    # Exact LCK1 Flow branches and their Track-bearing coroutine constructors.
    ("LUJ5;", "return", "(Lru/yandex/music/data/audio/o;)LGl4;"),
    ("LHv4;", "if", "(Lru/yandex/music/data/audio/o;)Z"),
    ("LCK1$a;", "<init>", "(Lru/yandex/music/data/audio/o;Lkotlin/coroutines/Continuation;)V"),
    ("LCK1$c;", "<init>", "(LC3a;Lru/yandex/music/data/audio/o;)V"),
    ("LCK1$l;", "<init>", "(LD3a;Lru/yandex/music/data/audio/o;)V"),
    # Exact inner Flow coroutine constructors receiving the retained Track.
    ("LCK1$c$a;", "<init>", "(LHl4;Lru/yandex/music/data/audio/o;)V"),
    ("LCK1$l$a;", "<init>", "(LHl4;Lru/yandex/music/data/audio/o;)V"),
    # Exact Track predicates and the second Track source used by the filter branch.
    ("LaC7;", "if", "()Lru/yandex/music/data/audio/o;"),
    ("Lv3;", "throws", "(Lru/yandex/music/data/audio/o;Lru/yandex/music/data/audio/o;)Z"),
    ("LwEa;", "for", "(Lru/yandex/music/data/audio/o;)Z"),
    ("LSV6;", "else", "(Lru/yandex/music/data/audio/o;)LUV6;"),
    ("LBK1;", "break", "(Lru/yandex/music/data/audio/o;)LGl4;"),
}

TRACK_FIELD_READ_SCAN_OWNERS = {
    "LJK1;", "LCK1$a;", "LCK1$c;", "LCK1$l;", "LCK1$c$a;", "LCK1$l$a;"
}

SELECTED_TRACK_PATH_TRACK_FIELD_CONSTRUCTORS = {
    "LJK1;": (
        "LJK1;", "<init>",
        "(LBK1;LGK1$a;Landroid/content/Context;Lkotlinx/coroutines/CoroutineScope;"
        "Lru/yandex/music/data/audio/o;Z)V"
    ),
    "LCK1$a;": (
        "LCK1$a;", "<init>",
        "(Lru/yandex/music/data/audio/o;Lkotlin/coroutines/Continuation;)V"
    ),
    "LCK1$c;": (
        "LCK1$c;", "<init>",
        "(LC3a;Lru/yandex/music/data/audio/o;)V"
    ),
    "LCK1$l;": (
        "LCK1$l;", "<init>",
        "(LD3a;Lru/yandex/music/data/audio/o;)V"
    ),
    "LCK1$c$a;": (
        "LCK1$c$a;", "<init>",
        "(LHl4;Lru/yandex/music/data/audio/o;)V"
    ),
    "LCK1$l$a;": (
        "LCK1$l$a;", "<init>",
        "(LHl4;Lru/yandex/music/data/audio/o;)V"
    ),
}


FLOW_ARGUMENT_ORIGIN_TARGETS = {
    ("Ljm4;","for"), ("Lwp0;","<init>"), ("Lwp0;","collect"),
    ("Lyp0;","<init>"), ("Lyp0;","collect"), ("Lwp0$a;","<init>"),
    ("LDp0;","<init>"), ("LDp0;","if"), ("LDp0;","emit"),
    ("LBC3;","<init>"), ("LzC3;","<init>"), ("LAC3;","<init>"),
    ("LBy4;","<init>"), ("LBy4;","collect"),
    ("Lvp0;","<init>"), ("Lvp0;","collect"),
    ("Lyp0;","<init>"), ("LzC3;","<init>"),
    ("Lnn4;","<init>"),
    ("LzD7;","if"), ("LBD7;","if"),
    ("LDw8;","emit"), ("LAD7;","emit"),
    ("LUK6;","emit"), ("LDb1;","emit"), ("Lxp0;","emit"),
    ("LAp0;","emit"), ("LO6;","native")
}


def class_instantiation_and_flow_collect_sites(dex: Dex, method, flags: int, code_off: int):

    targets = {"LDp0;", "Lwp0$a;", "LGp0;", "Lou3;", "LGl4;", "Ljm4;", "Lk1a;", "Lam4;",
               "Lwp0;", "Lyp0;", "LzC3;", "LAC3;", "LBC3;", "LO6;", "LBy4;",
               "Lvp0;", "LzD7;", "LAp0;", "Lxp0;", "LUK6;", "LDb1;",
               "LC3a;", "LgE6;", "LDw8;", "LAD7;",
               "LzE7;", "Lnn4;", "LAE7;", "Lup0;", "LAy4;", "LMG7;"}
    aliases = {name: set() for name in targets}
    instantiated = []
    collected = []
    ins = list(instructions(dex, code_off))
    for ordinal, (pc, op, words) in enumerate(ins):
        if op == 0x22:  # new-instance; invalidate every old type alias in the destination
            target = dex.descriptor(words[1])
            dest = words[0] >> 8
            for known in targets:
                aliases[known].discard(dest)
            if target in targets:
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
                        "argument_rows": logical_invoke_argument_rows(
                            dex,method,flags,code_off,ins,ordinal,op,words,
                            trace_origins=(callee[0],callee[1]) in FLOW_ARGUMENT_ORIGIN_TARGETS
                        ),
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
    # One exact, read-only hop from LDp0.if(Track); keep outside the broad Flow trace.
    lou3_else_ref = ("Lou3;", "else", "(Lru/yandex/music/data/audio/o;)V")
    lou3_else_exact_trace = None
    lou3_else_instruction_count = None
    flow_dispatcher_instantiation_sites = []
    flow_dispatcher_class_fields = {}
    flow_related_method_refs = set()
    flow_mode_constructor_store_rows = []
    flow_mode_branch_census = []
    selected_track_path_method_definitions = {}
    selected_track_path_owner_method_definitions = {}
    fp0_resume_null_track_arg = False
    fp0_coroutine_method_definitions = {}
    raa_resume_same_continuation = False
    raa_resume_null_wrapper = False
    exo_source_defined = False
    exo_source_close_void_declared = False
    trace_targets = {
        (MODEL, "super"), (ALBUM_MODEL, "if"), ("LGp0;", "new"),
        ("LDp0;", "if"), ("LDp0;", "emit"), ("LDp0;", "<init>"),
        ("Lwp0;", "collect"), ("Lwp0;", "<init>"), ("Lyp0;", "collect"),
        ("Lwp0$a;", "emit"), ("Lwp0$a;", "<init>"), ("Ljm4;", "for"),
        ("LzC3;", "<init>"), ("LzC3;", "collect"),
        ("LAC3;", "<init>"), ("LAC3;", "collect"),
        ("LBC3;", "<init>"), ("LBC3;", "collect"),
        ("LBC3$a;", "emit"), ("LAC3$a;", "emit"),
        ("LsF4;", "emit"), ("LyC3;", "emit"),
        ("LBy4;", "<init>"), ("LBy4;", "collect"),
        ("Lvp0;", "<init>"), ("Lvp0;", "collect"),
        ("LzD7;", "<init>"), ("LzD7;", "if"),
        ("LC3a;", "collect"), ("LgE6;", "collect"),
        ("Lnn4;", "<init>"), ("Lnn4;", "collect"),
        ("LJw4;", "<init>"), ("LPG1;", "if"),
        ("Lur1;", "case"), ("Lkh;", "invoke"), ("Lrm4;", "invoke"),
        ("LDw8;", "<init>"), ("LDw8;", "emit"),
        ("LAD7;", "<init>"), ("LAD7;", "emit"),
        ("LUK6;", "emit"), ("LDb1;", "emit"), ("Lxp0;", "emit"),
        ("LzE7;", "collect"), ("Lnn4;", "collect"),
        ("LAE7;", "emit"), ("Lup0;", "emit"), ("LAy4;", "emit"),
        ("LBD7;", "if"), ("LAp0;", "<init>"), ("LAp0;", "emit"),
        ("LO6;", "native"),
        ("Lam4;", "invokeSuspend"), ("Lam4;", "<init>"),
        ("LFp0;", "invokeSuspend"), ("LFp0;", "<init>"),
        ("Lou3;", "new"),
        ("Lcom/yandex/music/shared/player/download2/o;", "for"),
        ("Lcom/yandex/music/shared/player/download2/o$c;", "invokeSuspend"),
        ("Lcom/yandex/music/shared/player/download2/o$c;", "<init>"),
        ("LRAa;", "invokeSuspend"), ("LRAa;", "<init>"),
        ("LDT0;", "<init>")
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
                for target_class in ("LDp0;", "LDp0$a;", "Lwp0;", "Lwp0$a;",
                                     "Lyp0;", "LGp0;", "Lou3;", "LGl4;", "LHl4;",
                                     "Ljm4;", "Lk1a;", "Lam4;", "LFp0;", "LzC3;",
                                     "LAC3;", "LBC3;", "LO6;", "LBy4;", "Lvp0;",
                                     "LzD7;", "LBD7;", "LAp0;", "Lxp0;", "LUK6;", "LDb1;",
                                     "LC3a;", "LgE6;", "LDw8;", "LAD7;",
                                     "LzE7;", "Lnn4;", "Lhw9;", "LcE6;",
                                     "LAE7;", "Lup0;", "LAy4;",
                                     "Lcom/yandex/music/shared/player/download2/o$c;",
                                     "LRAa;"):
                    if target_class in defined:
                        flow_dispatcher_class_fields[target_class] = [
                            {"field": name, "type": typ}
                            for _, name, typ in declared_fields_for_owner(dex, target_class)
                        ]
                for i in range(dex.method_count):
                    method = dex.method(i)
                    if method[0] in FLOW_RESEARCH_METHOD_REF_OWNERS:
                        flow_related_method_refs.add(method)
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
                    if method[0] in FLOW_MODE_CONSTRUCTOR_OWNERS and method[1]=="<init>":
                        mode_stores=constructor_int_parameter_field_store_census(
                            dex,method,flags,code_off
                        )
                        if mode_stores:
                            flow_mode_constructor_store_rows.append({
                                "method":{"owner":method[0],"name":method[1],
                                          "signature":method[2]},
                                "int_parameter_field_stores":mode_stores
                            })
                    if method[0] in FLOW_MODE_BRANCH_AUDIT_OWNERS and method[1]=="collect":
                        flow_mode_branch_census.append({
                            "method":{"owner":method[0],"name":method[1],
                                      "signature":method[2]},
                            **summarize_flow_mode_branch_census(
                                dex,method,flags,code_off
                            )
                        })
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
                    if method == lou3_else_ref:
                        if lou3_else_exact_trace is not None:
                            raise ValueError("LOU3_ELSE_EXACT_DUPLICATE_DEFINITION")
                        lou3_else_instruction_count = sum(
                            1 for _ in instructions(dex, code_off)
                        )
                        lou3_else_exact_trace = privacy_safe_focused_method_trace(
                            focused_method_trace(dex, method, flags, code_off)
                        )
                    if method[0] in ("LMG7;", "LMG7$a;", "LC3a;", "LD3a;") or (method[0] in ("LAF7;", "LWM7;", "LyG7;") and (method[1] == "<init>" or any(t in method[2] for t in ("LD3a;", "Liw9;", "Lru/yandex/music/data/audio/o;")))) or (method[0], method[1]) in trace_targets:
                        focused_method_traces.append(
                            focused_method_trace(dex, method, flags, code_off))
                    if method in SELECTED_TRACK_PATH_METHODS:
                        selected_track_path_method_definitions[method] = (
                            dex, flags, code_off
                        )
                    if method[0] in TRACK_FIELD_READ_SCAN_OWNERS:
                        if method in selected_track_path_owner_method_definitions:
                            raise ValueError("DUPLICATE_TRACK_FIELD_READ_METHOD_DEFINITION")
                        if len(selected_track_path_owner_method_definitions) >= 128:
                            raise ValueError("TRACK_FIELD_READ_METHOD_SCAN_LIMIT")
                        selected_track_path_owner_method_definitions[method] = (
                            dex, flags, code_off
                        )
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
                        dex, method, flags, code_off)
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
                                if (
                                    method == (
                                        "LDT0;", "<init>",
                                        "(Lru/yandex/music/data/audio/Album;"
                                        "Lru/yandex/music/data/audio/o;ILNn;Lze2;"
                                        "Landroid/content/Context;LvF6;LgH6;LmH6;)V"
                                    )
                                    and callee == (
                                        "Ljm4;", "for",
                                        "(LGl4;Lkotlinx/coroutines/CoroutineScope;"
                                        "LHl4;)Lk1a;"
                                    )
                                ):
                                    target_callers[-1]["flow_argument_origin_rows"] = (
                                        logical_invoke_argument_rows(
                                            dex, method, flags, code_off, ins,
                                            ordinal, op, words
                                        )
                                    )
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
    selected_track_path_identity_traces = [
        trace_identity_method(
            dex, method, flags, code_off, candidate_owners=set()
        )
        for method, (dex, flags, code_off)
        in sorted(selected_track_path_method_definitions.items())
    ]
    selected_track_path_missing_method_refs = sorted(
        SELECTED_TRACK_PATH_METHODS
        - set(selected_track_path_method_definitions)
    )
    selected_track_path_exact_field_read_census = []
    selected_track_path_exact_field_refs_by_owner = {}
    for owner, constructor_ref in sorted(
        SELECTED_TRACK_PATH_TRACK_FIELD_CONSTRUCTORS.items()
    ):
        constructor_definition = selected_track_path_method_definitions.get(
            constructor_ref
        )
        field_refs = (
            track_parameter_field_store_refs(
                constructor_definition[0], constructor_ref,
                constructor_definition[1], constructor_definition[2]
            )
            if constructor_definition else []
        )
        if len(field_refs) > 8:
            raise ValueError("TRACK_FIELD_READ_OWNER_FIELD_REF_LIMIT")
        selected_track_path_exact_field_refs_by_owner[owner] = set(field_refs)
        field_read_traces = []
        if field_refs:
            exact_fields = set(field_refs)
            for method, (dex, flags, code_off) in sorted(
                selected_track_path_owner_method_definitions.items()
            ):
                if method[0] != owner:
                    continue
                trace = trace_identity_method(
                    dex, method, flags, code_off, candidate_owners=set(),
                    exact_track_field_refs=exact_fields
                )
                if any(
                    event.get("kind") == "FIELD_READ_TYPED_IDENTITY"
                    and event.get("identity_type") == "TRACK"
                    for event in trace.get("events", [])
                ):
                    field_read_traces.append(trace)
            if len(field_read_traces) > 64:
                raise ValueError("TRACK_FIELD_READ_OWNER_TRACE_LIMIT")
        selected_track_path_exact_field_read_census.append({
            "owner": owner,
            "constructor_defined": constructor_definition is not None,
            "constructor_track_field_store_count": len(field_refs),
            "field_read_method_count": len(field_read_traces),
            "field_read_traces": field_read_traces,
        })
    selected_track_path_inner_flow_cfg_traces = []
    for owner in ("LCK1$c$a;", "LCK1$l$a;"):
        exact_fields = selected_track_path_exact_field_refs_by_owner.get(owner, set())
        if not exact_fields:
            continue
        for method, (dex, flags, code_off) in sorted(
            selected_track_path_owner_method_definitions.items()
        ):
            if (
                method[0] == owner
                and method[1] == "emit"
                and method[2] == "(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;"
            ):
                selected_track_path_inner_flow_cfg_traces.append(
                    trace_exact_track_field_method_cfg(
                        dex, method, flags, code_off, exact_fields
                    )
                )
    ljk1_field_read_row = next(
        row for row in selected_track_path_exact_field_read_census
        if row["owner"] == "LJK1;"
    )
    ljk1_track_field_refs_count = ljk1_field_read_row[
        "constructor_track_field_store_count"
    ]
    selected_track_path_field_read_traces = ljk1_field_read_row[
        "field_read_traces"
    ]
    selected_track_path_interface_implementation_census = (
        inspect_selected_track_interface_implementations(
            apks, class_profiles, SELECTED_TRACK_PATH_METHODS
        )
    )
    laC7_track_return_owner_audit = (
        inspect_exact_track_return_owner_implementations(apks, class_profiles)
    )
    lya_track_holder_audit = inspect_lya_track_holder(apks, class_profiles)
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
    native_track_coroutine_callsite_census=inspect_native_track_coroutine_callers(
        apks,initial_ref
    )
    native_track_coroutine_new_instance_ancestry=summarize_coroutine_new_instance_ancestry(
        native_track_coroutine_callsite_census,class_profiles
    )
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
        "flow_entry_class_profiles":summarize_flow_entry_class_profiles(class_profiles),
        "flow_related_method_refs":[
            {"owner":x[0],"method":x[1],"signature":x[2]}
            for x in sorted(flow_related_method_refs)[:MAX_METHODS]
        ],
        "flow_interface_implementer_census":summarize_flow_interface_implementers(class_profiles),
        "current_track_flow_candidate": summarize_current_track_flow_candidate(
            class_profiles, focused_method_traces, flow_dispatcher_instantiation_sites
        ),
        "lou3_else_exact_method": {
            "target": {"owner": lou3_else_ref[0], "method": lou3_else_ref[1],
                       "signature": lou3_else_ref[2]},
            "body_found": lou3_else_exact_trace is not None,
            "instruction_count": lou3_else_instruction_count,
            # The existing tracer stops after 180 relevant rows. Never declare
            # absence of downstream calls when the exact body exceeds that bound.
            "complete_for_absence_claim": (
                lou3_else_instruction_count is not None
                and lou3_else_instruction_count <= 180
            ),
            "trace": lou3_else_exact_trace,
            "current_player_identity_proven": False,
            "same_native_item_to_decoder_proven": False,
            "original_media_or_private_values_read": False,
        },
        "flow_mode_constructor_int_field_stores":flow_mode_constructor_store_rows,
        "flow_mode_branch_census":flow_mode_branch_census,
        "selected_track_path_identity_traces": selected_track_path_identity_traces,
        "selected_track_path_constructor_track_field_store_count": ljk1_track_field_refs_count,
        "selected_track_path_field_read_method_count": len(selected_track_path_field_read_traces),
        "selected_track_path_field_read_traces": selected_track_path_field_read_traces,
        "selected_track_path_exact_field_read_census": selected_track_path_exact_field_read_census,
        "selected_track_path_inner_flow_cfg_traces": selected_track_path_inner_flow_cfg_traces,
        "selected_track_path_interface_implementation_census": selected_track_path_interface_implementation_census,
        "laC7_track_return_owner_audit": laC7_track_return_owner_audit,
        "lya_track_holder_audit": lya_track_holder_audit,
        "selected_track_path_missing_method_refs": [
            {"owner":x[0],"method":x[1],"signature":x[2]}
            for x in selected_track_path_missing_method_refs
        ],
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
        "native_track_coroutine_callsite_census": native_track_coroutine_callsite_census,
        "native_track_coroutine_new_instance_ancestry":native_track_coroutine_new_instance_ancestry,
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
