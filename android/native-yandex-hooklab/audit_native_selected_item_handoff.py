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
    found = []
    if not (flags & ACC_STATIC):
        if method[0] == MODEL:
            found.append((-1, reg))  # the exact Track instance is "this"
        reg += 1
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
                if callee[0] == MODEL and regs and regs[0] in model_aliases:
                    pending_result = {
                        "kind": "NATIVE_TRACK_ACCESSOR",
                        "method": callee[1],
                        "model_receiver_in_same_method": True,
                    }
                else:
                    inputs = [provenance[r] for r in regs if r in provenance]
                    if inputs:
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
    wrapper_constructor_callsites = []
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
                for i in range(dex.method_count):
                    method = dex.method(i)
                    if method[0] == MODEL:
                        model_referenced_methods.append(method)
                    if method[0] == WRAPPER:
                        wrapper_methods.add(method)
                    if method[0] in PLAYER_OWNERS and method[1] in PLAYER_METHODS:
                        player_method_refs.add(method)
                for method, flags, code_off in method_definitions_with_flags(dex):
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
    album_methods = sorted(set(album_methods))[:MAX_METHODS]
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
        "native_track_model_accessor_field_reads": model_accessor_field_reads[:MAX_METHODS],
        "native_album_model": ALBUM_MODEL if album_defined else None,
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
