#!/usr/bin/env python3
"""Bounded read-only class-structure inspection for the exact signed 2025 LfT2 class."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT))
sys.path.insert(0, str(LAB_ROOT / "ci"))
import audit_native_selected_item_handoff as audit

TARGET = "LfT2;"
PINNED_XAPK_BYTES = 45961661
PINNED_XAPK_SHA256 = "8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053"
PINNED_BASE_APK_SHA256 = "1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56"
EXPECTED_PACKAGE = "ru.yandex.music"
EXPECTED_VERSION_CODE = "24025542"
EXPECTED_VERSION_NAME = "2025.10.4 #120.1gpr"

CLASS_FLAGS = (
    (0x0001, "PUBLIC"), (0x0010, "FINAL"), (0x0200, "INTERFACE"),
    (0x0400, "ABSTRACT"), (0x1000, "SYNTHETIC"),
    (0x2000, "ANNOTATION"), (0x4000, "ENUM"),
)
METHOD_FLAGS = (
    (0x0001, "PUBLIC"), (0x0002, "PRIVATE"), (0x0004, "PROTECTED"),
    (0x0008, "STATIC"), (0x0010, "FINAL"), (0x0020, "SYNCHRONIZED"),
    (0x0040, "BRIDGE"), (0x0080, "VARARGS"), (0x0100, "NATIVE"),
    (0x0400, "ABSTRACT"), (0x0800, "STRICT"), (0x1000, "SYNTHETIC"),
    (0x10000, "CONSTRUCTOR"), (0x20000, "DECLARED_SYNCHRONIZED"),
)
CONTINUATION_METHOD_NAMES = frozenset({"invokeSuspend", "resumeWith", "invoke", "create"})
OBJECT_TO_OBJECT = "(Ljava/lang/Object;)Ljava/lang/Object;"
EXTRA_IDENTITY_TYPES = {
    "Lxj8;": "LQJ8_SERVICE",
    "LOf6;": "MEDIA_ITEM",
    "LiLb;": "MEDIA_ITEM_HOLDER",
}


def flag_names(value: int, table) -> list[str]:
    return [name for bit, name in table if value & bit]


def parse_class_definition(dex, class_index: int) -> dict:
    base = dex.class_offset + class_index * 32
    owner = dex.descriptor(dex.u32(base))
    flags = dex.u32(base + 4)
    superclass_index = dex.u32(base + 8)
    superclass = None if superclass_index == 0xFFFFFFFF else dex.descriptor(superclass_index)
    interfaces_off = dex.u32(base + 12)
    interfaces = []
    if interfaces_off:
        count = dex.u32(interfaces_off)
        if count > 1024:
            raise ValueError("LFT2_INTERFACE_COUNT_LIMIT")
        dex.bounds(interfaces_off + 4, count * 2)
        interfaces = [
            dex.descriptor(dex.u16(interfaces_off + 4 + i * 2))
            for i in range(count)
        ]

    class_data_off = dex.u32(base + 24)
    static_fields = instance_fields = 0
    methods = []
    if class_data_off:
        static_fields, pos = audit.uleb(dex, class_data_off)
        instance_fields, pos = audit.uleb(dex, pos)
        direct_methods, pos = audit.uleb(dex, pos)
        virtual_methods, pos = audit.uleb(dex, pos)
        if max(static_fields, instance_fields, direct_methods, virtual_methods) > 100000:
            raise ValueError("LFT2_CLASS_DATA_COUNT_LIMIT")

        # Skip field IDs/flags without decoding or exporting field names or values.
        for count in (static_fields, instance_fields):
            previous = 0
            for _ in range(count):
                delta, pos = audit.uleb(dex, pos)
                previous += delta
                _, pos = audit.uleb(dex, pos)

        for kind, count in (("DIRECT", direct_methods), ("VIRTUAL", virtual_methods)):
            previous = 0
            for _ in range(count):
                delta, pos = audit.uleb(dex, pos)
                previous += delta
                method_flags, pos = audit.uleb(dex, pos)
                code_off, pos = audit.uleb(dex, pos)
                if previous >= dex.method_count:
                    raise ValueError("LFT2_METHOD_INDEX_OUT_OF_RANGE")
                method = dex.method(previous)
                if method[0] != owner:
                    raise ValueError("LFT2_METHOD_OWNER_MISMATCH")
                methods.append({
                    "kind": kind, "name": method[1], "descriptor": method[2],
                    "access_flags": method_flags,
                    "access_flag_names": flag_names(method_flags, METHOD_FLAGS),
                    "has_code": bool(code_off),
                    "_method": method, "_code_off": code_off,
                })

    return {
        "descriptor": owner, "access_flags": flags,
        "access_flag_names": flag_names(flags, CLASS_FLAGS),
        "is_abstract": bool(flags & 0x0400),
        "is_interface": bool(flags & 0x0200),
        "superclass": superclass, "interfaces": interfaces,
        "declared_static_field_count": static_fields,
        "declared_instance_field_count": instance_fields,
        "declared_method_count": len(methods),
        "declared_methods": methods,
    }


def public_class_row(row: dict, include_all_methods: bool) -> dict:
    methods = row["declared_methods"]
    if not include_all_methods:
        methods = [m for m in methods if m["name"] in CONTINUATION_METHOD_NAMES]
    return {
        "descriptor": row["descriptor"],
        "access_flags": row["access_flags"],
        "access_flag_names": row["access_flag_names"],
        "is_abstract": row["is_abstract"],
        "is_interface": row["is_interface"],
        "superclass": row["superclass"],
        "interfaces": row["interfaces"],
        "declared_static_field_count": row["declared_static_field_count"],
        "declared_instance_field_count": row["declared_instance_field_count"],
        "declared_method_count": row["declared_method_count"],
        "declared_methods": [{
            "kind": m["kind"], "name": m["name"], "descriptor": m["descriptor"],
            "access_flags": m["access_flags"],
            "access_flag_names": m["access_flag_names"],
            "has_code": m["has_code"],
        } for m in methods],
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_metadata(path: Path) -> dict:
    proc = subprocess.run(
        ["aapt", "dump", "badging", str(path)],
        check=True, capture_output=True, text=True, timeout=60,
    )
    line = next((x for x in proc.stdout.splitlines() if x.startswith("package:")), "")
    if not line:
        raise ValueError("LFT2_BASE_PACKAGE_METADATA_MISSING")
    return dict(re.findall(r"(\w+)='([^']*)'", line))



def scan_same_wrapper_calls_after_read(dex, method, code_off, read_event) -> dict:
    """Follow only the exact field-read result through moves in its current basic block."""
    instructions = list(audit.instructions(dex, code_off))
    read_pc = read_event.get("pc")
    read_index = next((
        i for i, (pc, op, words) in enumerate(instructions)
        if pc == read_pc and op == 0x54
        and audit.field_id(dex, words[1])[0] == TARGET
        and audit.field_id(dex, words[1])[2] == "LtCa;"
    ), None)
    if read_index is None:
        return {
            "read_pc": read_pc,
            "scan_complete": False,
            "stop_reason": "EXACT_FIELD_READ_INSTRUCTION_NOT_FOUND",
            "same_object_calls": [],
        }

    read_words = instructions[read_index][2]
    aliases = {(read_words[0] >> 8) & 15}
    calls = []
    stop_reason = "METHOD_END"
    branch_ops = {0x28, 0x29, 0x2A, 0x2B, 0x2C} | set(range(0x32, 0x3E))
    exit_ops = {0x0E, 0x0F, 0x10, 0x11, 0x27}
    safe_no_write_ops = (
        {0x00, 0x1D, 0x1E, 0x26}
        | set(range(0x59, 0x60))
        | set(range(0x66, 0x6E))
    )

    for pc, op, words in instructions[read_index + 1:read_index + 65]:
        if op in branch_ops:
            stop_reason = "BRANCH_BOUNDARY"
            break
        if op in exit_ops:
            stop_reason = "METHOD_EXIT"
            break

        move = audit.move_object_registers(op, words)
        if move:
            destination, source = move
            aliases.discard(destination)
            if source in aliases:
                aliases.add(destination)
            continue

        if op == 0x1F:  # check-cast preserves the object reference
            continue

        if 0x6E <= op <= 0x78:
            callee = dex.method(words[1])
            registers = audit.invoke_registers(op, words)
            is_static = op in (0x71, 0x77)
            declared = audit.expand_invoke_register_types(
                callee[0], audit.parse_types(callee[2]), is_static
            )
            if len(registers) != len(declared):
                stop_reason = "INVOKE_REGISTER_SHAPE_MISMATCH"
                break
            logical_position = -1
            for declared_type, register in zip(declared, registers):
                if declared_type is None:
                    continue
                logical_position += 1
                if register not in aliases:
                    continue
                call_role = (
                    "RECEIVER" if not is_static and logical_position == 0
                    else "ARGUMENT"
                )
                calls.append({
                    "call_pc": pc,
                    "call_role": call_role,
                    "argument_position": logical_position,
                    "declared_argument_type": declared_type,
                    "callee_owner": callee[0],
                    "callee_method": callee[1],
                    "callee_descriptor": callee[2],
                })
            continue

        if op in (0xFA, 0xFB, 0xFC, 0xFD):
            registers = audit.invoke_registers(op, words)
            if aliases.intersection(registers):
                calls.append({
                    "call_pc": pc,
                    "call_role": "UNRESOLVED_DYNAMIC_INVOKE",
                    "argument_position": None,
                    "declared_argument_type": None,
                    "callee_owner": None,
                    "callee_method": None,
                    "callee_descriptor": None,
                })
            stop_reason = "DYNAMIC_INVOKE_BOUNDARY"
            break

        if op == 0x0C:  # move-result-object overwrites its destination
            aliases.discard(words[0] >> 8)
            continue

        if op in safe_no_write_ops:
            continue

        written = audit.written_register(op, words)
        if written is not None:
            aliases.discard(written)
            continue

        stop_reason = "UNMODELED_OPCODE_BOUNDARY"
        break

    return {
        "read_pc": read_pc,
        "receiver_identity_origins": read_event.get("receiver_identity_origins"),
        "receiver_is_this_on_all_paths": read_event.get("receiver_is_this_on_all_paths"),
        "scan_complete": stop_reason == "METHOD_END",
        "stop_reason": stop_reason,
        "same_object_calls": calls,
    }

def trace_non_constructor_method(dex, method, flags: int, code_off: int) -> dict:
    try:
        trace = audit.trace_track_identity_method_cfg(
            dex, method, flags, code_off,
            extra_identity_types=EXTRA_IDENTITY_TYPES,
        )
    except Exception as exc:
        reason = str(exc)
        safe_code = reason if re.fullmatch(r"[A-Z0-9_]{1,80}", reason) else "LFT2_METHOD_TRACE_UNCLASSIFIED"
        return {
            "method": method[1], "descriptor": method[2],
            "trace_complete": False, "error_class": type(exc).__name__,
            "error_code": safe_code,
        }

    events = trace.get("events", ())
    wrapper_reads = [
        e for e in events
        if e.get("kind") == "FIELD_READ_TYPED_IDENTITY"
        and e.get("identity_type") == "TRACK_WRAPPER"
    ]

    def has_wrapper_identity(event):
        args = list(event.get("identity_arguments", ()))
        args += list(event.get("possible_identity_arguments", ()))
        return any(
            a.get("identity_type") == "TRACK_WRAPPER"
            and a.get("declared_argument_type") == "LtCa;"
            for a in args
        )

    typed_calls = [
        e for e in events
        if e.get("kind") == "CALL_WITH_TYPED_IDENTITY" and has_wrapper_identity(e)
    ]
    possible_calls = [
        e for e in events
        if e.get("kind") == "CALL_WITH_POSSIBLE_IDENTITY" and has_wrapper_identity(e)
    ]

    def targets(rows):
        result = []
        for event in rows:
            callee = event.get("callee") or {}
            row = {
                "ordinal": event.get("ordinal"),
                "owner": callee.get("owner"),
                "method": callee.get("method"),
                "descriptor": callee.get("signature"),
                "role": event.get("role"),
            }
            if row not in result:
                result.append(row)
        return result

    return {
        "method": method[1], "descriptor": method[2],
        "trace_complete": not trace.get("trace_failed", False),
        "wrapper_field_read_count": len(wrapper_reads),
        "wrapper_field_read_sites": [{
            "pc": e.get("pc"),
            "field_declaring_owner": e.get("field_declaring_owner"),
            "receiver_is_this_on_all_paths": e.get("receiver_is_this_on_all_paths"),
            "receiver_identity_origins": e.get("receiver_identity_origins"),
        } for e in wrapper_reads],
        "same_object_calls_after_each_wrapper_field_read": [
            scan_same_wrapper_calls_after_read(dex, method, code_off, e)
            for e in wrapper_reads
        ],
        "typed_same_wrapper_call_targets": targets(typed_calls),
        "possible_wrapper_call_targets": targets(possible_calls),
        "native_source_descriptor_call_targets": targets([
            e for e in typed_calls if e.get("role") == "NATIVE_SOURCE_DESCRIPTOR"
        ]),
        "player_call_targets": targets([
            e for e in typed_calls if e.get("role") == "PLAYER_SELECTION_OR_TRANSPORT"
        ]),
    }


def inspect_lft2(apks: list[Path]) -> dict:
    class_locations = {}
    dex_count = 0
    for split_index, apk in enumerate(apks):
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("LFT2_DEX_SIZE_LIMIT")
                dex_count += 1
                dex = audit.Dex(archive.read(entry.filename))
                for class_index in range(dex.class_count):
                    base = dex.class_offset + class_index * 32
                    descriptor = dex.descriptor(dex.u32(base))
                    if descriptor in class_locations:
                        raise ValueError("LFT2_DUPLICATE_CLASS_DEFINITION")
                    class_locations[descriptor] = (dex, class_index, split_index, entry.filename)

    if dex_count != 6:
        raise ValueError("LFT2_EXPECTED_SIX_SIGNED_DEX")
    target_location = class_locations.get(TARGET)
    if target_location is None:
        raise ValueError("LFT2_CLASS_NOT_DEFINED")
    target_dex, target_index, target_split, target_dex_entry = target_location
    target = parse_class_definition(target_dex, target_index)

    # Resolve only LfT2's exact superclass chain; no global method census.
    superclass_chain = []
    seen = {TARGET}
    current = target["superclass"]
    inherited_invoke_suspend = []
    external_superclass = None
    for _ in range(12):
        if current is None:
            break
        if current in seen:
            raise ValueError("LFT2_SUPERCLASS_CYCLE")
        seen.add(current)
        location = class_locations.get(current)
        if location is None:
            external_superclass = current
            superclass_chain.append({
                "descriptor": current,
                "defined_in_signed_vendor_dex": False,
            })
            break
        dex, class_index, _split_index, _dex_entry = location
        row = parse_class_definition(dex, class_index)
        relevant = [m for m in row["declared_methods"] if m["name"] in CONTINUATION_METHOD_NAMES]
        superclass_chain.append({
            "descriptor": row["descriptor"],
            "access_flags": row["access_flags"],
            "access_flag_names": row["access_flag_names"],
            "is_abstract": row["is_abstract"],
            "interfaces": row["interfaces"],
            "relevant_declared_methods": [{
                "name": m["name"], "descriptor": m["descriptor"],
                "access_flag_names": m["access_flag_names"], "has_code": m["has_code"],
            } for m in relevant],
        })
        inherited_invoke_suspend.extend(
            m for m in relevant if m["name"] == "invokeSuspend" and m["has_code"]
        )
        current = row["superclass"]
    else:
        raise ValueError("LFT2_SUPERCLASS_DEPTH_LIMIT")

    interface_definitions = []
    seen_interfaces = set()
    for interface in target["interfaces"]:
        if interface in seen_interfaces:
            continue
        seen_interfaces.add(interface)
        location = class_locations.get(interface)
        if location is None:
            interface_definitions.append({
                "descriptor": interface, "defined_in_signed_vendor_dex": False,
            })
            continue
        dex, class_index, _split_index, _dex_entry = location
        row = parse_class_definition(dex, class_index)
        interface_definitions.append({
            "descriptor": interface,
            "defined_in_signed_vendor_dex": True,
            "access_flags": row["access_flags"],
            "access_flag_names": row["access_flag_names"],
            "relevant_declared_methods": [{
                "name": m["name"], "descriptor": m["descriptor"],
                "access_flag_names": m["access_flag_names"], "has_code": m["has_code"],
            } for m in row["declared_methods"]
               if m["name"] in CONTINUATION_METHOD_NAMES],
        })

    declared = target["declared_methods"]
    declared_field_rows = audit.declared_fields_for_owner(target_dex, TARGET)
    field_type_counts = {}
    for _field_owner, _field_name, field_type in declared_field_rows:
        field_type_counts[field_type] = field_type_counts.get(field_type, 0) + 1
    exact_invoke_suspend = [
        m for m in declared
        if m["name"] == "invokeSuspend" and m["descriptor"] == OBJECT_TO_OBJECT
    ]
    any_invoke_suspend = [m for m in declared if m["name"] == "invokeSuspend"]
    object_to_object_methods = [
        m for m in declared
        if m["descriptor"] == OBJECT_TO_OBJECT and m["has_code"]
    ]
    method_traces = [
        trace_non_constructor_method(target_dex, m["_method"], m["access_flags"], m["_code_off"])
        for m in declared
        if m["has_code"] and m["name"] not in ("<init>", "<clinit>")
    ]

    type_markers = [TARGET, target["superclass"] or "", *target["interfaces"]]
    type_markers.extend(x.get("descriptor", "") for x in superclass_chain)
    kotlin_continuation_marker = any(
        "kotlin/coroutines" in x or "SuspendLambda" in x or "ContinuationImpl" in x
        for x in type_markers
    )
    function_interface_marker = any(
        "kotlin/jvm/functions/Function" in x or "kotlin/coroutines/jvm/internal" in x
        for x in type_markers
    )

    if any(m["has_code"] for m in exact_invoke_suspend):
        entry_status = "DECLARED_EXECUTABLE_INVOKE_SUSPEND"
    elif any_invoke_suspend:
        entry_status = "DECLARED_INVOKE_SUSPEND_WITHOUT_CODE"
    elif inherited_invoke_suspend:
        entry_status = "INHERITED_EXECUTABLE_INVOKE_SUSPEND_IN_VENDOR_DEX"
    elif object_to_object_methods:
        entry_status = "NO_INVOKE_SUSPEND; OBJECT_TO_OBJECT_METHODS_REQUIRE_REVIEW"
    else:
        entry_status = "NO_EXECUTABLE_CONTINUATION_ENTRY_IDENTIFIED_IN_LFT2"

    return {
        "publisher_version": EXPECTED_VERSION_NAME,
        "original_xapk_sha256": PINNED_XAPK_SHA256,
        "original_base_apk_sha256": PINNED_BASE_APK_SHA256,
        "verified_publisher_splits": len(apks),
        "signed_dex_count": dex_count,
        "target_class": public_class_row(target, include_all_methods=True),
        "declared_field_type_counts_without_names": field_type_counts,
        "target_split_index": target_split,
        "target_dex_entry": target_dex_entry,
        "superclass_chain": superclass_chain,
        "direct_interface_definitions": interface_definitions,
        "declares_exact_invoke_suspend": bool(exact_invoke_suspend),
        "declares_any_invoke_suspend": bool(any_invoke_suspend),
        "declared_executable_object_to_object_methods": [{
            "name": m["name"], "descriptor": m["descriptor"],
            "access_flag_names": m["access_flag_names"],
        } for m in object_to_object_methods],
        "inherited_executable_invoke_suspend_in_signed_vendor_dex": bool(inherited_invoke_suspend),
        "external_superclass_not_inspected": external_superclass,
        "kotlin_continuation_type_marker": kotlin_continuation_marker,
        "function_or_continuation_interface_marker": function_interface_marker,
        "continuation_entry_status": entry_status,
        "bounded_non_constructor_method_traces": method_traces,
        "field_names_or_values_disclosed": False,
        "track_album_ids_titles_urls_dataspec_tokens_account_or_audio_read": False,
        "original_binary_modified_or_exported": False,
    }


def run(xapk: Path) -> dict:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size != PINNED_XAPK_BYTES:
        raise ValueError("PINNED_2025_XAPK_SIZE_MISMATCH")
    if sha256_file(xapk) != PINNED_XAPK_SHA256:
        raise ValueError("PINNED_2025_XAPK_SHA_MISMATCH")

    with tempfile.TemporaryDirectory(prefix="celikom-lft2-class-readonly-") as temp:
        apks = audit.unbundle_candidate(xapk, Path(temp))
        if len(apks) != 16:
            raise ValueError("PINNED_2025_SPLIT_COUNT_MISMATCH")
        publisher = audit.verify_split_set(apks)
        if publisher.get("verified_issuer_signed_splits") != 16:
            raise ValueError("PINNED_2025_PUBLISHER_SIGNATURE_GATE_FAILED")
        base_rows = []
        for apk in apks:
            meta = package_metadata(apk)
            if meta.get("name") != EXPECTED_PACKAGE or meta.get("versionCode") != EXPECTED_VERSION_CODE:
                raise ValueError("PINNED_2025_SPLIT_IDENTITY_MISMATCH")
            if not meta.get("split"):
                base_rows.append(apk)
        if len(base_rows) != 1:
            raise ValueError("PINNED_2025_BASE_SPLIT_COUNT_MISMATCH")
        if sha256_file(base_rows[0]) != PINNED_BASE_APK_SHA256:
            raise ValueError("NAV17_EMBEDDED_ORIGIN_BASE_SHA_MISMATCH")
        report = inspect_lft2(apks)

    return {
        **report,
        "pinned_xapk_size_verified": True,
        "publisher_signature_verified": True,
        "embedded_nav17_origin_base_sha_reconfirmed": True,
        "read_only": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xapk", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.xapk), sort_keys=True, ensure_ascii=False))
    except (RuntimeError, ValueError, audit.DexError, OSError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        reason = str(exc)
        safe_code = reason if re.fullmatch(r"[A-Z0-9_]{1,80}", reason) else None
        print(json.dumps({
            "verdict": "LFT2_CLASS_INSPECTION_INCOMPLETE",
            "error_class_only": type(exc).__name__,
            "safe_error_code": safe_code,
            "original_binary_modified_or_exported": False,
        }))
        raise SystemExit(2)
