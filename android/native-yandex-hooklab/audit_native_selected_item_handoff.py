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
            })
        if callee[0] == MODEL:
            track_model_method_call = True
        elif callee[0] == ALBUM_MODEL:
            album_model_method_call = True
    return rows


def summarize_boundary_callsite_census(rows):
    summary = {}
    flags = (
        "track_parameter_present", "album_parameter_present",
        "track_field_read_on_this_before", "album_field_read_on_this_before",
        "numeric_field_read_on_this_before", "track_model_method_call_before",
        "album_model_method_call_before"
    )
    for row in rows:
        bucket = summary.setdefault(row["kind"], {
            "call_site_count": 0,
            "distinct_caller_method_count": 0,
            **{key + "_call_site_count": 0 for key in flags}
        })
        bucket["call_site_count"] += 1
        for key in flags:
            if row[key]:
                bucket[key + "_call_site_count"] += 1
    for kind, bucket in summary.items():
        bucket["distinct_caller_method_count"] = len({
            row["caller_key"] for row in rows if row["kind"] == kind
        })
    return summary
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
    boundary_callsite_rows = []
    model_flow_candidates = []
    wrapper_methods = set()
    flow_source_interface_methods = set()
    target_callers = []
    focused_method_traces = []
    flow_dispatcher_instantiation_sites = []
    flow_dispatcher_class_fields = {}
    fp0_resume_null_track_arg = False
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
                                target_callers.append({
                                    "caller": {"owner": method[0], "name": method[1],
                                               "signature": method[2]},
                                    "target": {"owner": callee[0], "name": callee[1],
                                               "signature": callee[2]},
                                    "argument_registers": regs,
                                    "invoke_kind": "STATIC" if is_static else "INSTANCE_OR_OTHER",
                                    "argument_types": target_types,
                                    "native_track_argument_positions": [
                                        i for i, register in enumerate(regs)
                                        if register in model_regs
                                    ],
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
        "boundary_callsite_identity_census":
            summarize_boundary_callsite_census(boundary_callsite_rows),
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
