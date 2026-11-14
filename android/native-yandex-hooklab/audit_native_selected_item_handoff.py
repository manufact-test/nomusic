#!/usr/bin/env python3
"""Read-only signed-Dex audit of native selected-item identity handoff.

Finds exact model fields/accessors and bounded same-basic-block object flow
from that model to native source descriptor/player APIs. This is static code
evidence only: it never reads account data, media, URLs, or a live player.
The publisher-signed APK is downloaded and inspected only in ephemeral CI.
"""
from __future__ import annotations

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

from inspect_android_host import Dex, DexError, DEX_MAX
from trace_native_callers import uleb, INVOKES
from audit_native_register_bridge import (
    instructions, invoke_registers, move_object_registers
)
import clone_native_splits_ephemeral as exact

MODEL = "Lru/yandex/music/data/audio/o;"
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
SOURCE_METHODS = {
    ("Lcom/yandex/music/shared/player/download2/o;", "while"),
    ("Lcq7;", "i0"), ("Lga4;", "d"),
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
    if not (flags & ACC_STATIC):
        reg += 1
    found = []
    for index, typ in enumerate(params):
        if typ == MODEL:
            found.append((index, reg))
        reg += 2 if typ in ("J", "D") else 1
    return found


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
                elif callee[0] == MODEL:
                    role = "MODEL_ACCESSOR_OR_METHOD"
                elif callee[1] == "<init>":
                    role = "OBJECT_CONSTRUCTOR"
                elif callee[0] == WRAPPER:
                    role = "TRACK_ID_WRAPPER_CONSTRUCTOR"
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


def inspect_signed(apks):
    dex_count = 0
    model_defined = False
    model_fields = {}
    model_methods = []
    model_referenced_methods = []
    descriptor_builder_callers = []
    player_method_refs = set()
    model_flow_candidates = []
    wrapper_methods = set()
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
                if MODEL in defined:
                    if model_defined:
                        raise ValueError("DUPLICATE_NATIVE_TRACK_MODEL")
                    model_defined = True
                    for owner, name, typ in declared_fields_for_owner(dex, MODEL):
                        model_fields[name] = typ
                        if len(model_fields) > MAX_FIELDS:
                            raise ValueError("MODEL_FIELD_LIMIT")
                for i in range(dex.method_count):
                    method = dex.method(i)
                    if method[0] == MODEL:
                        model_referenced_methods.append(method)
                    if method[0] == WRAPPER:
                        wrapper_methods.add(method)
                    if method[0] in PLAYER_OWNERS and method[1] in PLAYER_METHODS:
                        player_method_refs.add(method)
                for method, flags, code_off in method_definitions_with_flags(dex):
                    if method[0] == MODEL:
                        model_methods.append(method)
                    if method[0] not in (MODEL, WRAPPER) and (
                        MODEL in method[2] or WRAPPER in method[2]
                    ):
                        if len(model_flow_candidates) < MAX_METHODS:
                            flow = straight_line_model_flow(dex, method, flags, code_off)
                            if flow and flow["straight_line_events"]:
                                model_flow_candidates.append(flow)
                    ins = list(instructions(dex, code_off))
                    for ordinal, (pc, op, words) in enumerate(ins):
                        if op not in INVOKES:
                            continue
                        callee = dex.method(words[1])
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
    model_methods = sorted(set(model_methods))[:MAX_METHODS]
    model_referenced_methods = sorted(set(model_referenced_methods))[:MAX_METHODS]
    wrapper_methods = sorted(wrapper_methods)[:MAX_METHODS]
    player_method_refs = sorted(player_method_refs)[:MAX_METHODS]
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
        "track_id_wrapper_method_examples": [
            {"owner": x[0], "method": x[1], "signature": x[2]}
            for x in wrapper_methods
        ],
        "descriptor_builder_callers": descriptor_builder_callers,
        "public_player_selection_method_refs": [
            {"owner": x[0], "method": x[1], "signature": x[2]}
            for x in player_method_refs
        ],
        "same_basic_block_model_parameter_flows": model_flow_candidates,
        "active_selected_item_proven": False,
        "same_native_item_to_decoder_proven": False,
        "current_song_or_audio_accessed": False,
        "original_apk_modified_or_exported": False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-native-selected-item-audit-") as temp:
        folder = Path(temp)
        archive = folder / "publisher-original.xapk"
        size, digest = exact.gpr.download(archive)
        if size != 60433885 or digest != exact.ARCHIVE_SHA:
            raise ValueError("PINNED_PUBLISHER_ARCHIVE_MISMATCH")
        apks = exact.gpr.split_apks(archive, folder)
        if len(apks) != 5:
            raise ValueError("FIVE_SIGNED_SPLITS_REQUIRED")
        exact.gpr.inspect_publisher(apks)
        report = inspect_signed(apks)
    return {
        **report,
        "publisher_version": "2026.10.3 #170gpr",
        "no_login_no_user_media_no_decoder_mutation": True,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True, ensure_ascii=False))
    except (RuntimeError, ValueError, DexError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({
            "verdict": "SIGNED_NATIVE_SELECTED_ITEM_AUDIT_INCOMPLETE",
            "error_class_only": type(exc).__name__,
            "active_selected_item_proven": False,
            "no_vendor_binary_exported": True,
        }))
        raise SystemExit(2)
