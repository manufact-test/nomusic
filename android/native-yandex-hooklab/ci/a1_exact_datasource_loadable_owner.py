#!/usr/bin/env python3
"""Find the exact signed-2025 caller that opens CELIKOM's hooked Exo DataSource.

This is one exact-method callsite trace over the pinned publisher-signed 2025
XAPK. It does not scan generic DataSource APIs, inspect media, or infer that a
DataSource is active merely because it was opened. Output is bounded to the
direct caller(s), finite type roles, and whether a caller is an Exo Loadable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import lft2_class_inspection as trusted

audit = trusted.audit

DATA_SOURCE = (
    "Lcom/yandex/music/shared/player/download2/exo/"
    "RetryingBalancingDataSource;"
)
DATA_SPEC = "LUC2;"
OPEN = (DATA_SOURCE, "if", "(" + DATA_SPEC + ")J")
READ = (DATA_SOURCE, "read", "([BII)I")
CLOSE = (DATA_SOURCE, "close", "()V")
LOADABLE = "Landroidx/media3/exoplayer/upstream/Loader$Loadable;"
PERIOD = "Lo96;"
MEDIA_PERIOD = "Lwh6;"
SOURCE = "LSl6;"

MAX_DEX_COUNT = 6
MAX_METHOD_DEFINITIONS = 400000
MAX_INSTRUCTIONS_PER_METHOD = 12000
MAX_TOTAL_INSTRUCTIONS = 12000000
MAX_OPEN_CALLERS = 24
MAX_CLASS_INTERFACES = 256
MAX_OWNER_FIELDS = 128
MAX_OWNER_CONSTRUCTORS = 24


def parse_hierarchy(dex):
    rows = {}
    if dex.class_count > 100000:
        raise ValueError("LOADABLE_CLASS_COUNT_LIMIT")
    for index in range(dex.class_count):
        base = dex.class_offset + index * 32
        owner = dex.descriptor(dex.u32(base))
        super_index = dex.u32(base + 8)
        superclass = (
            None if super_index == 0xFFFFFFFF
            else dex.descriptor(super_index)
        )
        interfaces_off = dex.u32(base + 12)
        interfaces = []
        if interfaces_off:
            count = dex.u32(interfaces_off)
            if count > MAX_CLASS_INTERFACES:
                raise ValueError("LOADABLE_INTERFACE_COUNT_LIMIT")
            dex.bounds(interfaces_off + 4, count * 2)
            interfaces = [
                dex.descriptor(dex.u16(interfaces_off + 4 + i * 2))
                for i in range(count)
            ]
        if owner in rows:
            raise ValueError("LOADABLE_DUPLICATE_CLASS")
        rows[owner] = (dex, superclass, interfaces)
    return rows


def implements(owner, target, classes, seen=None):
    if owner == target:
        return True
    if seen is None:
        seen = set()
    if owner in seen:
        return False
    seen.add(owner)
    row = classes.get(owner)
    if row is None:
        return False
    _dex, superclass, interfaces = row
    if target in interfaces:
        return True
    return any(implements(parent, target, classes, seen) for parent in interfaces) or (
        superclass is not None and implements(superclass, target, classes, seen)
    )


def inspect_owner_shape(owner, class_rows, methods_by_owner):
    row = class_rows.get(owner)
    if row is None:
        return {
            "class_defined": False,
            "nested_under_exact_Lo96": owner.startswith(PERIOD[:-1] + "$"),
            "implements_media3_loader_loadable": False,
            "owner_period_field_count": 0,
            "owner_source_field_count": 0,
            "owner_constructor_count": 0,
            "constructors_with_exact_Lo96_parameter": [],
            "loadable_load_method_defined": False,
        }
    dex, _superclass, _interfaces = row
    try:
        fields = audit.declared_fields_for_owner(dex, owner)
    except Exception as exc:
        raise ValueError("LOADABLE_OWNER_FIELD_INSPECTION_FAILED") from exc
    if len(fields) > MAX_OWNER_FIELDS:
        raise ValueError("LOADABLE_OWNER_FIELD_LIMIT")
    period_fields = sum(1 for _o, _n, typ in fields if typ == PERIOD)
    source_fields = sum(1 for _o, _n, typ in fields if typ == SOURCE)
    constructors = [
        method for method, _flags, _off in methods_by_owner.get(owner, ())
        if method[1] == "<init>"
    ]
    if len(constructors) > MAX_OWNER_CONSTRUCTORS:
        raise ValueError("LOADABLE_OWNER_CONSTRUCTOR_LIMIT")
    constructors_with_period = [
        list(method) for method in constructors if PERIOD in audit.parse_types(method[2])
    ]
    load_method = any(
        method[1] == "load" and method[2] == "()V" and code_off
        for method, _flags, code_off in methods_by_owner.get(owner, ())
    )
    return {
        "class_defined": True,
        "nested_under_exact_Lo96": owner.startswith(PERIOD[:-1] + "$"),
        "implements_media3_loader_loadable": implements(owner, LOADABLE, class_rows),
        "owner_period_field_count": period_fields,
        "owner_source_field_count": source_fields,
        "owner_constructor_count": len(constructors),
        "constructors_with_exact_Lo96_parameter": constructors_with_period,
        "loadable_load_method_defined": load_method,
    }


def scan_signed(apks):
    class_rows = {}
    methods_by_owner = {}
    dexes = []
    definitions = {}
    total_methods = 0

    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("LOADABLE_SIGNED_DEX_SIZE_LIMIT")
                dex = audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                local = parse_hierarchy(dex)
                if set(class_rows).intersection(local):
                    raise ValueError("LOADABLE_CROSS_DEX_DUPLICATE_CLASS")
                class_rows.update(local)

    if len(dexes) != MAX_DEX_COUNT:
        raise ValueError("LOADABLE_SIGNED_SIX_DEX_REQUIRED")

    for dex in dexes:
        for method, flags, code_off in audit.method_definitions_with_flags(dex):
            total_methods += 1
            if total_methods > MAX_METHOD_DEFINITIONS:
                raise ValueError("LOADABLE_METHOD_DEFINITION_LIMIT")
            methods_by_owner.setdefault(method[0], []).append(
                (method, flags, code_off)
            )
            if method in (OPEN, READ, CLOSE):
                if method in definitions:
                    raise ValueError("LOADABLE_EXACT_TARGET_DUPLICATE")
                definitions[method] = (dex, flags, code_off)

    if set(definitions) != {OPEN, READ, CLOSE}:
        raise ValueError("LOADABLE_EXACT_DATASOURCE_METHOD_SET_MISMATCH")
    if not definitions[OPEN][2]:
        raise ValueError("LOADABLE_EXACT_OPEN_METHOD_HAS_NO_BODY")

    open_callers = {}
    exact_read_callers = set()
    exact_close_callers = set()
    total_instructions = 0

    for dex in dexes:
        for method, _flags, code_off in audit.method_definitions_with_flags(dex):
            if not code_off:
                continue
            insns = audit.instructions(dex, code_off)
            method_instruction_count = 0
            open_sites = []
            read_count = 0
            close_count = 0
            for pc, opcode, words in insns:
                method_instruction_count += 1
                total_instructions += 1
                if method_instruction_count > MAX_INSTRUCTIONS_PER_METHOD:
                    raise ValueError("LOADABLE_METHOD_INSTRUCTION_LIMIT")
                if total_instructions > MAX_TOTAL_INSTRUCTIONS:
                    raise ValueError("LOADABLE_TOTAL_INSTRUCTION_LIMIT")
                if opcode not in audit.INVOKES or not 0x6E <= opcode <= 0x78:
                    continue
                callee = dex.method(words[1])
                if callee == READ:
                    read_count += 1
                elif callee == CLOSE:
                    close_count += 1
                if callee != OPEN:
                    continue
                registers = audit.invoke_registers(opcode, words)
                open_sites.append({
                    "pc": pc,
                    "invoke_opcode": opcode,
                    "receiver_register": registers[0] if registers else None,
                    "argument_register_count": max(0, len(registers) - 1),
                })
            if read_count:
                exact_read_callers.add(method)
            if close_count:
                exact_close_callers.add(method)
            if open_sites:
                row = open_callers.setdefault(method, {
                    "method": list(method),
                    "open_sites": [],
                    "same_method_exact_read_calls": 0,
                    "same_method_exact_close_calls": 0,
                })
                row["open_sites"].extend(open_sites)
                row["same_method_exact_read_calls"] = read_count
                row["same_method_exact_close_calls"] = close_count
                if len(open_callers) > MAX_OPEN_CALLERS:
                    raise ValueError("LOADABLE_EXACT_OPEN_CALLER_LIMIT")

    rows = []
    for method, row in sorted(open_callers.items()):
        owner_shape = inspect_owner_shape(method[0], class_rows, methods_by_owner)
        rows.append({
            **row,
            **owner_shape,
            "exact_open_and_read_same_method": row["same_method_exact_read_calls"] > 0,
            "exact_open_and_close_same_method": row["same_method_exact_close_calls"] > 0,
            "method_is_loadable_load": (
                owner_shape["implements_media3_loader_loadable"]
                and method[1] == "load" and method[2] == "()V"
            ),
        })

    loadable_rows = [row for row in rows if row["method_is_loadable_load"]]
    return {
        "verdict": (
            "ONE_EXACT_LOADABLE_OPENS_HOOKED_EXO_DATASOURCE"
            if len(loadable_rows) == 1
            else "EXACT_DATASOURCE_OPEN_CALLERS_REQUIRE_OWNER_REVIEW"
        ),
        "publisher_signed_2025_original_only": True,
        "signed_dex_count": len(dexes),
        "method_definitions_inspected": total_methods,
        "instructions_inspected": total_instructions,
        "exact_open_target_defined": OPEN in definitions,
        "exact_read_target_defined": READ in definitions,
        "exact_close_target_defined": CLOSE in definitions,
        "exact_open_direct_caller_count": len(rows),
        "exact_open_direct_callers": rows,
        "exact_read_direct_caller_count": len(exact_read_callers),
        "exact_close_direct_caller_count": len(exact_close_callers),
        "unique_loadable_load_caller_count": len(loadable_rows),
        "one_exact_loadable_owner_proven": len(loadable_rows) == 1,
        "loadable_owner_has_exact_Lo96_reference_proven": any(
            row["method_is_loadable_load"] and (
                row["nested_under_exact_Lo96"]
                or row["owner_period_field_count"] > 0
                or row["constructors_with_exact_Lo96_parameter"]
            )
            for row in rows
        ),
        "active_period_sample_stream_renderer_link_proven": False,
        "active_audio_or_replacement_playback_proven": False,
        "private_field_names_values_urls_ids_tokens_or_audio_exported": False,
    }


def run(xapk: Path):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("LOADABLE_EXACT_SIGNED_CI_ONLY")
    if os.environ.get("GITHUB_REPOSITORY") != "manufact-test/nomusic":
        raise RuntimeError("LOADABLE_EXPECTED_REPOSITORY_ONLY")
    if not xapk.is_file() or xapk.stat().st_size != trusted.PINNED_XAPK_BYTES:
        raise ValueError("LOADABLE_PINNED_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk) != trusted.PINNED_XAPK_SHA256:
        raise ValueError("LOADABLE_PINNED_XAPK_SHA_MISMATCH")

    with tempfile.TemporaryDirectory(prefix="celikom-loadable-owner-") as temp:
        splits = audit.unbundle_candidate(xapk, Path(temp))
        if len(splits) != 16:
            raise ValueError("LOADABLE_SIGNED_SPLITS_REQUIRED")
        verified = audit.verify_split_set(splits)
        if verified.get("verified_issuer_signed_splits") != 16:
            raise ValueError("LOADABLE_PUBLISHER_SIGNATURE_MISMATCH")
        bases = []
        for apk in splits:
            meta = trusted.package_metadata(apk)
            if (meta.get("name") != trusted.EXPECTED_PACKAGE
                    or meta.get("versionCode") != trusted.EXPECTED_VERSION_CODE):
                raise ValueError("LOADABLE_ORIGINAL_PACKAGE_VERSION_MISMATCH")
            if not meta.get("split"):
                bases.append(apk)
        if (len(bases) != 1
                or trusted.sha256_file(bases[0]) != trusted.PINNED_BASE_APK_SHA256):
            raise ValueError("LOADABLE_ORIGINAL_BASE_MISMATCH")
        return scan_signed(splits)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--xapk", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.xapk), sort_keys=True))
    except (RuntimeError, ValueError, audit.DexError, OSError, zipfile.BadZipFile) as exc:
        message = str(exc)
        safe_code = message if re.fullmatch(r"[A-Z0-9_]{1,90}", message) else None
        print(json.dumps({
            "verdict": "LOADABLE_EXACT_DATASOURCE_AUDIT_INCOMPLETE",
            "safe_error_code": safe_code,
            "active_period_sample_stream_renderer_link_proven": False,
        }))
        raise SystemExit(2)
