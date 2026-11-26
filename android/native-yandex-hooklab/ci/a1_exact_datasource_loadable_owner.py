#!/usr/bin/env python3
"""Find the exact signed-2025 caller that opens CELIKOM's hooked Exo DataSource.

This is one exact-method callsite trace over the pinned publisher-signed 2025
XAPK. It does not scan generic DataSource APIs, inspect media, or infer that a
DataSource is active merely because it was opened. Output is bounded to the
direct caller(s), finite type roles, and whether a caller is an Exo Loadable.
"""
from __future__ import annotations

import argparse
from collections import deque
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
PERIOD = "Lo96;"
MEDIA_PERIOD = "Lwh6;"
SOURCE = "LSl6;"

MAX_DEX_COUNT = 6
MAX_METHOD_DEFINITIONS = 400000
MAX_INSTRUCTIONS_PER_METHOD = 12000
MAX_TOTAL_INSTRUCTIONS = 12000000
MAX_OPEN_CALLERS = 24
MAX_CLASS_INTERFACES = 256
MAX_CALL_GRAPH_EDGES = 1000000
MAX_UPSTREAM_DEPTH = 8
MAX_UPSTREAM_NODES_PER_TARGET = 512
MAX_OWNER_FIELDS = 128
MAX_OWNER_CONSTRUCTORS = 24


def is_exact_datasource_target(method):
    return method in (OPEN, READ, CLOSE)


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
        access_flags = dex.u32(base + 4)
        rows[owner] = (dex, superclass, interfaces, access_flags)
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
    _dex, superclass, interfaces, _access_flags = row
    if target in interfaces:
        return True
    return any(implements(parent, target, classes, seen) for parent in interfaces) or (
        superclass is not None and implements(superclass, target, classes, seen)
    )


def hierarchy_owners(owner, classes, seen=None):
    if seen is None:
        seen = set()
    if owner in seen:
        return set()
    seen.add(owner)
    result = {owner}
    row = classes.get(owner)
    if row is None:
        return result
    _dex, superclass, interfaces, _access_flags = row
    if superclass is not None:
        result.update(hierarchy_owners(superclass, classes, seen))
    for interface in interfaces:
        result.update(hierarchy_owners(interface, classes, seen))
    return result


def collect_dispatch_targets(dexes, classes, owner_scope, descriptor, exact_target):
    # Only signed interface/abstract-base contracts plus the exact concrete
    # hook target. A same-signature private helper is not a dispatch contract.
    dispatch_owners = {
        owner for owner in owner_scope
        if classes.get(owner) is not None
        and (classes[owner][3] & (0x200 | 0x400))
    }
    targets = {exact_target}
    for dex in dexes:
        for index in range(dex.method_count):
            method = dex.method(index)
            if method[0] in dispatch_owners and method[2] == descriptor:
                targets.add(method)
                if len(targets) > 16:
                    raise ValueError("LOADABLE_DISPATCH_TARGET_LIMIT")
    return targets


def loader_contract_for_method(owner, method, class_rows, methods_by_owner):
    ancestors = hierarchy_owners(owner, class_rows)
    matches = []
    for interface in ancestors:
        if not interface.startswith("Landroidx/media3/exoplayer/upstream/Loader$"):
            continue
        row = class_rows.get(interface)
        if row is None or not (row[3] & 0x200):
            continue
        if any(
            candidate[1] == method[1] and candidate[2] == method[2]
            for candidate, _flags, _off in methods_by_owner.get(interface, ())
        ):
            matches.append(interface)
    if len(matches) > 4:
        raise ValueError("LOADABLE_LOADER_INTERFACE_MATCH_LIMIT")
    return sorted(matches)


def scan_candidate_constructor_callers(dexes, candidate_owners, media_period_owners):
    rows = []
    inspected_methods = 0
    inspected_instructions = 0
    for dex in dexes:
        for method, _flags, code_off in audit.method_definitions_with_flags(dex):
            inspected_methods += 1
            if inspected_methods > MAX_METHOD_DEFINITIONS:
                raise ValueError("LOADABLE_CTOR_SCAN_METHOD_LIMIT")
            if not code_off:
                continue
            for pc, opcode, words in audit.instructions(dex, code_off):
                inspected_instructions += 1
                if inspected_instructions > MAX_TOTAL_INSTRUCTIONS:
                    raise ValueError("LOADABLE_CTOR_SCAN_INSTRUCTION_LIMIT")
                if opcode not in audit.INVOKES or not 0x6E <= opcode <= 0x78:
                    continue
                callee = dex.method(words[1])
                if callee[1] != "<init>" or callee[0] not in candidate_owners:
                    continue
                registers = audit.invoke_registers(opcode, words)
                rows.append({
                    "constructed_owner": callee[0],
                    "constructor_signature": callee[2],
                    "caller_method": list(method),
                    "pc": pc,
                    "caller_is_exact_Lo96_method": method[0] == PERIOD,
                    "caller_is_signed_MediaPeriod_implementer": method[0] in media_period_owners,
                    "receiver_register": registers[0] if registers else None,
                    "argument_register_count": max(0, len(registers) - 1),
                })
                if len(rows) > 64:
                    raise ValueError("LOADABLE_CTOR_CALLER_LIMIT")
    return {
        "candidate_constructor_callsite_count": len(rows),
        "candidate_constructor_callsites": rows,
        "constructor_callsite_scan_methods": inspected_methods,
        "constructor_callsite_scan_instructions": inspected_instructions,
    }


def inspect_owner_shape(owner, class_rows, methods_by_owner):
    row = class_rows.get(owner)
    if row is None:
        return {
            "class_defined": False,
            "nested_under_exact_Lo96": owner.startswith(PERIOD[:-1] + "$"),
            "class_superclass": None,
            "class_interfaces": [],
            "implements_exact_loader_inner_contract": False,
            "loader_inner_contracts": [],
            "owner_period_field_count": 0,
            "owner_source_field_count": 0,
            "owner_constructor_count": 0,
            "constructors_with_exact_Lo96_parameter": [],
            "loadable_load_method_defined": False,
        }
    dex, superclass, interfaces, _access_flags = row
    try:
        fields = audit.declared_fields_for_owner(dex, owner)
    except Exception as exc:
        raise ValueError("LOADABLE_OWNER_FIELD_INSPECTION_FAILED") from exc
    if len(fields) > MAX_OWNER_FIELDS:
        raise ValueError("LOADABLE_OWNER_FIELD_LIMIT")
    period_fields = sum(1 for _o, _n, typ in fields if typ == PERIOD)
    source_fields = sum(1 for _o, _n, typ in fields if typ == SOURCE)
    wrapper_fields = sum(1 for _o, _n, typ in fields if typ == "Lup1;")
    media_period_fields = sum(1 for _o, _n, typ in fields if typ == MEDIA_PERIOD)
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
        "class_superclass": superclass,
        "class_interfaces": interfaces,
        "implements_exact_loader_inner_contract": False,
        "loader_inner_contracts": [],
        "owner_period_field_count": period_fields,
        "owner_source_field_count": source_fields,
        "owner_wrapper_field_count": wrapper_fields,
        "owner_media_period_field_count": media_period_fields,
        "owner_constructor_count": len(constructors),
        "constructors_with_exact_Lo96_parameter": constructors_with_period,
        "loadable_load_method_defined": load_method,
    }


def method_aliases(method, classes, methods_by_owner):
    """Return exact virtual/interface declarations that may dispatch to method."""
    owner, name, descriptor = method
    aliases = {method}
    for ancestor in hierarchy_owners(owner, classes):
        if ancestor == owner:
            continue
        for candidate, flags, _code_off in methods_by_owner.get(ancestor, []):
            if (candidate[1] == name and candidate[2] == descriptor
                    and not (flags & 0x2) and not (flags & 0x8)):
                aliases.add(candidate)
    return aliases


def trace_upstream_methods(target_methods, reverse_calls, aliases_for_method,
                           max_depth=MAX_UPSTREAM_DEPTH,
                           max_nodes=MAX_UPSTREAM_NODES_PER_TARGET):
    """Bounded reverse call-graph walk from direct DataSource.open callers."""
    if len(target_methods) > MAX_OPEN_CALLERS:
        raise ValueError("LOADABLE_UPSTREAM_TARGET_LIMIT")
    result = {}
    for target in target_methods:
        distances = {target: 0}
        queue = deque([target])
        while queue:
            current = queue.popleft()
            depth = distances[current]
            if depth >= max_depth:
                continue
            for alias in aliases_for_method(current):
                for caller in reverse_calls.get(alias, ()):
                    if caller in distances:
                        continue
                    distances[caller] = depth + 1
                    if len(distances) > max_nodes:
                        raise ValueError("LOADABLE_UPSTREAM_NODE_LIMIT")
                    queue.append(caller)
        result[target] = distances
    return result


def scan_signed(apks):
    class_rows = {}
    methods_by_owner = {}
    dexes = []
    definitions = {}
    total_methods = 0

    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
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
            if is_exact_datasource_target(method):
                if method in definitions:
                    raise ValueError("LOADABLE_EXACT_TARGET_DUPLICATE")
                definitions[method] = (dex, flags, code_off)

    if set(definitions) != {OPEN, READ, CLOSE}:
        raise ValueError("LOADABLE_EXACT_DATASOURCE_METHOD_SET_MISMATCH")
    if not definitions[OPEN][2]:
        raise ValueError("LOADABLE_EXACT_OPEN_METHOD_HAS_NO_BODY")
    if DATA_SOURCE not in class_rows:
        raise ValueError("LOADABLE_EXACT_SOURCE_CLASS_HIERARCHY_MISSING")

    source_contract_scope = hierarchy_owners(DATA_SOURCE, class_rows)
    open_dispatch_targets = collect_dispatch_targets(
        dexes, class_rows, source_contract_scope, OPEN[2], OPEN
    )
    read_dispatch_targets = collect_dispatch_targets(
        dexes, class_rows, source_contract_scope, READ[2], READ
    )
    close_dispatch_targets = collect_dispatch_targets(
        dexes, class_rows, source_contract_scope, CLOSE[2], CLOSE
    )
    media_period_owners = {
        owner for owner in class_rows
        if implements(owner, MEDIA_PERIOD, class_rows)
    }
    open_callers = {}
    exact_read_callers = set()
    exact_close_callers = set()
    reverse_calls = {}
    call_edge_count = 0
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
                reverse_calls.setdefault(callee, set()).add(method)
                call_edge_count += 1
                if call_edge_count > MAX_CALL_GRAPH_EDGES:
                    raise ValueError("LOADABLE_CALL_GRAPH_EDGE_LIMIT")
                if callee in read_dispatch_targets:
                    read_count += 1
                elif callee in close_dispatch_targets:
                    close_count += 1
                if callee not in open_dispatch_targets:
                    continue
                registers = audit.invoke_registers(opcode, words)
                open_sites.append({
                    "pc": pc,
                    "invoke_opcode": opcode,
                    "callee": list(callee),
                    "concrete_hook_target": callee == OPEN,
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
        loader_contracts = loader_contract_for_method(
            method[0], method, class_rows, methods_by_owner
        )
        owner_shape["loader_inner_contracts"] = loader_contracts
        owner_shape["implements_exact_loader_inner_contract"] = bool(loader_contracts)
        rows.append({
            **row,
            **owner_shape,
            "exact_open_and_read_same_method": row["same_method_exact_read_calls"] > 0,
            "exact_open_and_close_same_method": row["same_method_exact_close_calls"] > 0,
            "method_matches_exact_loader_contract": bool(loader_contracts),
        })

    loadable_rows = [row for row in rows if row["method_matches_exact_loader_contract"]]
    candidate_owners = {row["method"][0] for row in rows}
    constructor_evidence = scan_candidate_constructor_callers(
        dexes, candidate_owners, media_period_owners
    )
    upstream_by_target = trace_upstream_methods(
        [tuple(row["method"]) for row in rows], reverse_calls,
        lambda method: method_aliases(method, class_rows, methods_by_owner)
    )
    upstream_loadable_methods = set()
    upstream_open_callers_with_loadable = 0
    upstream_open_callers_with_lo96 = 0
    upstream_open_callers_with_media_period = 0
    upstream_method_union = set()
    upstream_open_caller_summaries = []
    for index, distances in enumerate(upstream_by_target.values(), 1):
        upstream_method_union.update(distances)
        loadable_for_target = {
            method for method in distances
            if loader_contract_for_method(method[0], method, class_rows, methods_by_owner)
        }
        lo96_for_target = {method for method in distances if method[0] == PERIOD}
        media_for_target = {method for method in distances if method[0] in media_period_owners}
        upstream_loadable_methods.update(loadable_for_target)
        upstream_open_callers_with_loadable += bool(loadable_for_target)
        upstream_open_callers_with_lo96 += bool(lo96_for_target)
        upstream_open_callers_with_media_period += bool(media_for_target)
        upstream_open_caller_summaries.append({
            "index": index,
            "reachable_method_count": len(distances),
            "max_depth": max(distances.values(), default=0),
            "loadable_method_count": len(loadable_for_target),
            "exact_Lo96_ancestor_count": len(lo96_for_target),
            "media_period_ancestor_count": len(media_for_target),
        })
    upstream_loadable_owners = {method[0] for method in upstream_loadable_methods}
    if len(upstream_loadable_owners) > MAX_OPEN_CALLERS:
        raise ValueError("LOADABLE_UPSTREAM_OWNER_LIMIT")
    upstream_loadable_constructor_evidence = scan_candidate_constructor_callers(
        dexes, upstream_loadable_owners, media_period_owners
    ) if upstream_loadable_owners else {"candidate_constructor_callsites": []}
    upstream_loadable_shapes = [
        inspect_owner_shape(owner, class_rows, methods_by_owner)
        for owner in sorted(upstream_loadable_owners)
    ]
    upstream_loadable_has_exact_Lo96_reference = any(
        shape.get("nested_under_exact_Lo96")
        or shape.get("owner_period_field_count", 0) > 0
        or bool(shape.get("constructors_with_exact_Lo96_parameter"))
        for shape in upstream_loadable_shapes
    )
    upstream_loadable_constructed_inside_exact_Lo96 = any(
        item.get("constructed_owner") in upstream_loadable_owners
        and item.get("caller_is_exact_Lo96_method")
        for item in upstream_loadable_constructor_evidence.get("candidate_constructor_callsites", [])
    )
    upstream_loadable_constructed_inside_any_media_period = any(
        item.get("constructed_owner") in upstream_loadable_owners
        and item.get("caller_is_signed_MediaPeriod_implementer")
        for item in upstream_loadable_constructor_evidence.get("candidate_constructor_callsites", [])
    )
    upstream_loadable_exact_Lo96_constructor_site_count = sum(
        1 for item in upstream_loadable_constructor_evidence.get("candidate_constructor_callsites", [])
        if item.get("constructed_owner") in upstream_loadable_owners
        and item.get("caller_is_exact_Lo96_method")
    )
    if len(upstream_loadable_owners) == 1 and (
            upstream_loadable_has_exact_Lo96_reference
            or upstream_loadable_constructed_inside_exact_Lo96):
        upstream_verdict = "ONE_UPSTREAM_LOADABLE_BOUND_TO_EXACT_LO96"
    elif len(upstream_loadable_owners) == 1:
        upstream_verdict = "ONE_UPSTREAM_LOADABLE_PERIOD_BINDING_UNPROVEN"
    elif len(upstream_loadable_owners) > 1:
        upstream_verdict = "MULTIPLE_UPSTREAM_LOADABLE_OWNERS_REVIEW"
    elif upstream_open_callers_with_lo96 or upstream_open_callers_with_media_period:
        upstream_verdict = "MEDIA_PERIOD_UPSTREAM_WITHOUT_UNIQUE_LOADABLE"
    else:
        upstream_verdict = "NO_MEDIA_PERIOD_UPSTREAM_CALLER_PROVEN"
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
        "data_source_contract_hierarchy_owner_count": len(source_contract_scope),
        "data_source_contract_hierarchy_owners": sorted(source_contract_scope),
        "open_dispatch_target_count": len(open_dispatch_targets),
        "open_dispatch_targets": [list(x) for x in sorted(open_dispatch_targets)],
        "read_dispatch_target_count": len(read_dispatch_targets),
        "read_dispatch_targets": [list(x) for x in sorted(read_dispatch_targets)],
        "close_dispatch_target_count": len(close_dispatch_targets),
        "close_dispatch_targets": [list(x) for x in sorted(close_dispatch_targets)],
        "signed_media_period_implementer_count": len(media_period_owners),
        "signed_media_period_implementers": sorted(media_period_owners),
        "exact_open_direct_caller_count": len(rows),
        "exact_open_direct_callers": rows,
        "exact_read_direct_caller_count": len(exact_read_callers),
        "exact_close_direct_caller_count": len(exact_close_callers),
        "unique_loadable_load_caller_count": len(loadable_rows),
        "one_exact_loadable_owner_proven": len(loadable_rows) == 1,
        "loadable_owner_has_exact_Lo96_reference_proven": any(
            row["method_matches_exact_loader_contract"] and (
                row["nested_under_exact_Lo96"]
                or row["owner_period_field_count"] > 0
                or row["constructors_with_exact_Lo96_parameter"]
            )
            for row in rows
        ),
        "loadable_owner_nested_under_any_signed_media_period": any(
            row["method_matches_exact_loader_contract"] and any(
                row["method"][0].startswith(period[:-1] + "$")
                for period in media_period_owners
            )
            for row in rows
        ),
        **constructor_evidence,
        "loadable_owner_constructed_inside_exact_Lo96_method": any(
            row["method_matches_exact_loader_contract"] and any(
                item["constructed_owner"] == row["method"][0]
                and item["caller_is_exact_Lo96_method"]
                for item in constructor_evidence["candidate_constructor_callsites"]
            )
            for row in rows
        ),
        "loadable_owner_constructed_inside_any_signed_media_period": any(
            row["method_matches_exact_loader_contract"] and any(
                item["constructed_owner"] == row["method"][0]
                and item["caller_is_signed_MediaPeriod_implementer"]
                for item in constructor_evidence["candidate_constructor_callsites"]
            )
            for row in rows
        ),
        "active_period_sample_stream_renderer_link_proven": False,
        "upstream_call_graph_edge_count": call_edge_count,
        "upstream_method_count": len(upstream_method_union),
        "upstream_open_callers_with_loadable_count": upstream_open_callers_with_loadable,
        "upstream_open_callers_with_exact_Lo96_ancestor_count": upstream_open_callers_with_lo96,
        "upstream_open_callers_with_media_period_ancestor_count": upstream_open_callers_with_media_period,
        "upstream_loadable_method_count": len(upstream_loadable_methods),
        "upstream_loadable_owner_count": len(upstream_loadable_owners),
        "upstream_loadable_owner_has_exact_Lo96_reference_proven": upstream_loadable_has_exact_Lo96_reference,
        "upstream_loadable_owner_constructed_inside_exact_Lo96_method": upstream_loadable_constructed_inside_exact_Lo96,
        "upstream_loadable_owner_constructed_inside_any_signed_MediaPeriod": upstream_loadable_constructed_inside_any_media_period,
        "upstream_loadable_exact_Lo96_constructor_site_count": upstream_loadable_exact_Lo96_constructor_site_count,
        "upstream_loadable_owner_shapes": upstream_loadable_shapes,
        "upstream_loadable_constructor_callsites": upstream_loadable_constructor_evidence.get("candidate_constructor_callsites", []),
        "upstream_open_caller_summaries": upstream_open_caller_summaries,
        "upstream_verdict": upstream_verdict,
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
