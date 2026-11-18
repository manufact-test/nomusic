#!/usr/bin/env python3
"""Read-only signed-DEX trace of the exact LtCa object entering LcA9.extends.

The scan is bounded to the direct LcA9 source-setter caller(s), plus one
upstream caller hop only when the wrapper is a typed parameter. Private DEX
symbols and field names stay in ephemeral CI; output is finite categories.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
sys_path = HERE.parent
import sys
sys.path.insert(0, str(sys_path))
import audit_native_selected_item_handoff as audit
import lft2_class_inspection as trusted

TARGET = (
    "LcA9;", "extends",
    "(LcA9;LA14;LtCa;Ljava/lang/Long;JJZLn26;Lnk0;Ljava/lang/String;)V",
)
WRAPPER = "LtCa;"
WRAPPER_CTOR = ("LtCa;", "<init>", "(Ljava/lang/String;)V")
INITIAL = (
    "LGp0;", "new",
    "(LGp0;Lru/yandex/music/data/audio/o;LOe2;)Ljava/lang/Object;",
)
RESUME = ("LFp0;", "invokeSuspend", "(Ljava/lang/Object;)Ljava/lang/Object;")
TARGET_WRAPPER_POSITION = 2
MAX_DIRECT_CALLS = 128
MAX_DIRECT_CALLERS = 64
MAX_UPSTREAM_CALLS = 128
MAX_UPSTREAM_CALLERS = 64
WIDE_OPS = (
    {0x04, 0x05, 0x06, 0x0b, 0x16, 0x17, 0x18, 0x19, 0x45, 0x53,
     0x61, 0x7d, 0x7e, 0x80, 0x82, 0x85, 0x87, 0x88, 0x8a}
    | set(range(0x9b, 0xa6)) | set(range(0xab, 0xb0))
    | set(range(0xbb, 0xc6)) | set(range(0xcb, 0xd0))
)


def wrapper_origin_categories(event: dict, position: int) -> tuple[str, ...]:
    """Return fixed categories for one exact logical LtCa argument."""
    if not isinstance(event, dict):
        return ("NO_EVENT",)
    rows = []
    common = event.get("kind") == "CALL_WITH_TYPED_IDENTITY"
    source = event.get("identity_arguments", ()) if common else (
        event.get("possible_identity_arguments", ())
        if event.get("kind") == "CALL_WITH_POSSIBLE_IDENTITY" else ()
    )
    for row in source:
        if (row.get("argument_position") != position
                or row.get("declared_argument_type") != WRAPPER
                or row.get("identity_type") != "TRACK_WRAPPER"):
            continue
        origins = row.get("origins", ()) if common else row.get("possible_origins", ())
        mapping = (
            ("TRACK_WRAPPER_NEW_INSTANCE", "NEW_INSTANCE"),
            ("TRACK_WRAPPER_PARAMETER", "PARAMETER"),
            ("TRACK_WRAPPER_FROM_THIS_FIELD", "THIS_FIELD"),
            ("TRACK_WRAPPER_FROM_TRACKED_RECEIVER_FIELD", "TRACKED_RECEIVER_FIELD"),
            ("TRACK_WRAPPER_FROM_STATIC_FIELD", "STATIC_FIELD"),
            ("TRACK_WRAPPER_RETURNED_FROM_METHOD", "RETURNED_FROM_METHOD"),
        )
        found = [label for token, label in mapping if token in origins]
        if found:
            rows.extend(found)
        else:
            rows.append("UNCLASSIFIED_ORIGIN")
    if not rows:
        return ("NO_IDENTITY",)
    prefix = "COMMON_" if common else "POSSIBLE_"
    return tuple(sorted({prefix + value for value in rows}))


def logical_parameter_positions(method, flags: int, target_type: str) -> list[int]:
    is_static = bool(flags & audit.ACC_STATIC)
    types = audit.expand_invoke_register_types(
        method[0], audit.parse_types(method[2]), is_static
    )
    result = []
    logical = -1
    for typ in types:
        if typ is None:
            continue
        logical += 1
        if typ == target_type:
            result.append(logical)
    return result


def _argument_register(
    dex, op: int, words, target_method, logical_position: int,
    expected_type: str | None = None
):
    is_static = op in (0x71, 0x77)
    types = audit.expand_invoke_register_types(
        target_method[0], audit.parse_types(target_method[2]), is_static
    )
    registers = audit.invoke_registers(op, words)
    if len(registers) != len(types):
        raise ValueError("TCA_TARGET_INVOKE_REGISTER_MAP")
    logical = -1
    for word_position, typ in enumerate(types):
        if typ is None:
            continue
        logical += 1
        if logical == logical_position:
            if not typ.startswith(("L", "[")):
                return None
            if expected_type is not None and typ != expected_type:
                return None
            return registers[word_position]
    return None


def logical_parameter_type(method, flags: int, logical_position: int):
    types = audit.expand_invoke_register_types(
        method[0], audit.parse_types(method[2]),
        bool(flags & audit.ACC_STATIC)
    )
    logical = -1
    for typ in types:
        if typ is None:
            continue
        logical += 1
        if logical == logical_position:
            return typ
    return None


def logical_position_for_parameter_register(
    dex, method, flags: int, code_off: int, register: int
):
    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        raise ValueError("TCA_PARAMETER_REGISTER_LAYOUT")
    current = registers_size - ins_size
    logical = 0
    if not (flags & audit.ACC_STATIC):
        if current == register:
            return 0
        current += 1
        logical = 1
    for typ in audit.parse_types(method[2]):
        if current == register:
            return logical
        current += 2 if typ in ("J", "D") else 1
        logical += 1
    return None


def tca_origin_category(token: str | None) -> str:
    if not isinstance(token, str):
        return "AMBIGUOUS_OR_UNRESOLVED"
    if token.startswith("TCA_INIT@"):
        return "CONSTRUCTED_IN_SAME_METHOD"
    if token.startswith("TCA_PARAMETER@") or token == "TCA_THIS":
        return "TYPED_PARAMETER"
    if token.startswith("TCA_FIELD@"):
        return "TYPED_FIELD"
    if token.startswith("TCA_STATIC_FIELD@"):
        return "TYPED_STATIC_FIELD"
    if token.startswith("TCA_RETURN@"):
        return "TYPED_METHOD_RETURN"
    if token.startswith("TCA_CAST@REF_PARAMETER@"):
        return "CAST_FROM_REFERENCE_PARAMETER"
    if token.startswith("TCA_CAST@REF_THIS_FIELD@"):
        return "CAST_FROM_THIS_FIELD"
    if token.startswith("TCA_CAST@REF_FIELD@"):
        return "CAST_FROM_REFERENCE_FIELD"
    if token.startswith("TCA_CAST@REF_STATIC_FIELD@"):
        return "CAST_FROM_STATIC_FIELD"
    if token.startswith("TCA_CAST@REF_RETURN@"):
        return "CAST_FROM_METHOD_RETURN"
    if token.startswith("TCA_CAST@REF_ARRAY_ELEMENT@"):
        return "CAST_FROM_ARRAY_ELEMENT"
    if token.startswith("TCA_CAST@REF_NEW_INSTANCE@"):
        return "CAST_FROM_NEW_INSTANCE"
    if token.startswith("TCA_CAST@"):
        return "CAST_FROM_UNKNOWN_REFERENCE"
    if token.startswith("REF_PARAMETER@"):
        return "REFERENCE_PARAMETER"
    if token.startswith("REF_THIS_FIELD@"):
        return "REFERENCE_FROM_THIS_FIELD"
    if token.startswith("REF_FIELD@"):
        return "REFERENCE_FROM_FIELD"
    if token.startswith("REF_STATIC_FIELD@"):
        return "REFERENCE_FROM_STATIC_FIELD"
    if token.startswith("REF_RETURN@"):
        return "REFERENCE_FROM_METHOD_RETURN"
    if token.startswith("REF_ARRAY_ELEMENT@"):
        return "REFERENCE_FROM_ARRAY_ELEMENT"
    if token.startswith("REF_NEW_INSTANCE@"):
        return "REFERENCE_NEW_INSTANCE"
    if token.startswith("REF_THIS@"):
        return "REFERENCE_THIS"
    if token.startswith("TCA_NULL@"):
        return "EXPLICIT_NULL"
    return "AMBIGUOUS_OR_UNRESOLVED"


def _parameter_register_from_tca_token(token: str | None):
    if not isinstance(token, str):
        return None
    match = re.search(r"(?:TCA_PARAMETER|REF_PARAMETER)@([0-9]+)", token)
    return int(match.group(1)) if match else None


def trace_exact_tca_constructor_to_callsites(
    dex, method, flags: int, code_off: int, target_method,
    callsite_pcs: list[int], wrapper_position: int,
    target_argument_type: str | None = WRAPPER,
    target_field_ref=None
) -> dict:
    """Trace a tCa reference through typed or Object-then-check-cast aliases."""
    cfg = audit.build_dex_control_flow(dex, code_off)
    by_pc, successors = cfg["by_pc"], cfg["successors"]
    registers_size = dex.u16(code_off)
    ins_size = dex.u16(code_off + 2)
    if ins_size > registers_size:
        raise ValueError("TCA_TRACE_INVALID_INS_SIZE")

    initial_registers = {}
    current = registers_size - ins_size
    this_register = None
    if not (flags & audit.ACC_STATIC):
        this_register = current
        initial_registers[current] = (
            "TCA_THIS" if method[0] == WRAPPER else f"REF_THIS@{current}"
        )
        current += 1
    for typ in audit.parse_types(method[2]):
        if typ.startswith(("L", "[")):
            initial_registers[current] = (
                f"TCA_PARAMETER@{current}" if typ == WRAPPER
                else f"REF_PARAMETER@{current}"
            )
        current += 2 if typ in ("J", "D") else 1

    initial = {"registers": initial_registers, "pending_return": None}

    def state_key(state):
        return (
            tuple(sorted(state["registers"].items())),
            state["pending_return"],
        )

    incoming = {cfg["entry"]: {state_key(initial): initial}}
    work = [(cfg["entry"], state_key(initial))]
    processed = 0
    field_read_metadata = {}

    def transfer(state, pc, op, words):
        regs = dict(state["registers"])
        pending = None

        def clear(reg):
            regs.pop(reg, None)

        if op in audit.INVOKES:
            callee = dex.method(words[1])
            args = audit.invoke_registers(op, words)
            if callee == WRAPPER_CTOR and args:
                token = regs.get(args[0])
                if token and token.startswith("TCA_ALLOC@"):
                    initialized = "TCA_INIT@" + token
                    for reg, value in list(regs.items()):
                        if value == token:
                            regs[reg] = initialized
            result_type = callee[2].split(")", 1)[1]
            if result_type == WRAPPER:
                pending = f"TCA_RETURN@{pc}"
            elif result_type.startswith(("L", "[")):
                pending = f"REF_RETURN@{pc}"
        elif op == 0x0c:  # move-result-object
            dest = (words[0] >> 8) & 0xff
            clear(dest)
            if state["pending_return"]:
                regs[dest] = state["pending_return"]
        elif op == 0x22:  # new-instance
            dest = (words[0] >> 8) & 0xff
            clear(dest)
            object_type = dex.descriptor(words[1])
            if object_type == WRAPPER:
                regs[dest] = f"TCA_ALLOC@{pc}"
            elif object_type.startswith(("L", "[")):
                regs[dest] = f"REF_NEW_INSTANCE@{pc}"
        elif op in (0x07, 0x08, 0x09):
            move = audit.move_object_registers(op, words)
            if move is not None:
                dest, source = move
                value = regs.get(source)
                clear(dest)
                if value is not None:
                    regs[dest] = value
        elif op == 0x1f:  # check-cast preserves the exact Java reference
            reg = (words[0] >> 8) & 0xff
            cast_type = dex.descriptor(words[1])
            token = regs.get(reg)
            if cast_type == WRAPPER:
                if token and token.startswith("REF_"):
                    regs[reg] = "TCA_CAST@" + token
                elif not token:
                    regs[reg] = f"TCA_CAST@REF_UNKNOWN@{pc}"
        elif op == 0x54:  # iget-object; type and receiver class only
            dest = (words[0] >> 8) & 15
            receiver = (words[0] >> 12) & 15
            field_ref = audit.field_id(dex, words[1])
            field_type = field_ref[2]
            receiver_token = regs.get(receiver)
            field_read_metadata[pc] = (field_ref, receiver_token, False)
            clear(dest)
            if field_type == WRAPPER:
                regs[dest] = f"TCA_FIELD@{pc}"
            elif field_type.startswith(("L", "[")):
                category = "REF_THIS_FIELD" if receiver == this_register else "REF_FIELD"
                regs[dest] = f"{category}@{pc}"
        elif op == 0x62:  # sget-object
            dest = words[0] >> 8
            field_ref = audit.field_id(dex, words[1])
            field_type = field_ref[2]
            field_read_metadata[pc] = (field_ref, None, True)
            clear(dest)
            if field_type == WRAPPER:
                regs[dest] = f"TCA_STATIC_FIELD@{pc}"
            elif field_type.startswith(("L", "[")):
                regs[dest] = f"REF_STATIC_FIELD@{pc}"
        elif op == 0x46:  # aget-object
            dest = (words[0] >> 8) & 0xff
            clear(dest)
            regs[dest] = f"REF_ARRAY_ELEMENT@{pc}"
        elif op in (0x12, 0x13, 0x14, 0x15):
            dest = audit.written_register(op, words)
            if dest is not None:
                literal = None
                if op == 0x12:
                    literal = (words[0] >> 12) & 15
                    if literal & 8:
                        literal -= 16
                elif op == 0x13:
                    literal = words[1]
                    if literal & 0x8000:
                        literal -= 0x10000
                elif op == 0x14:
                    literal = words[1] | (words[2] << 16)
                elif op == 0x15:
                    literal = words[1]
                clear(dest)
                if literal == 0:
                    regs[dest] = f"TCA_NULL@{pc}"
        else:
            dest = audit.written_register(op, words)
            if dest is not None:
                clear(dest)
                if op in WIDE_OPS:
                    clear(dest + 1)
        return {"registers": regs, "pending_return": pending}

    while work:
        pc, key = work.pop()
        processed += 1
        if processed > 200000:
            raise ValueError("TCA_TRACE_DATAFLOW_LIMIT")
        state = incoming[pc][key]
        op, words = by_pc[pc]
        output = transfer(state, pc, op, words)
        output_key = state_key(output)
        for target in successors.get(pc, ()):
            bucket = incoming.setdefault(target, {})
            if output_key in bucket:
                continue
            if len(bucket) >= 128:
                raise ValueError("TCA_TRACE_PATH_STATE_LIMIT")
            bucket[output_key] = output
            work.append((target, output_key))

    site_results = []
    for pc in sorted(set(callsite_pcs)):
        instruction = by_pc.get(pc)
        states = list(incoming.get(pc, {}).values())
        if instruction is None or not states:
            site_results.append({
                "reachable": False,
                "same_constructed_tca_on_all_paths": False,
                "same_tca_reference_on_all_paths": False,
                "same_receiver_reference_on_all_paths": False,
                "origin_category": "UNREACHABLE_OR_UNMAPPED",
                "origin_parameter_position": None,
                "origin_field_ref": None,
                "origin_field_receiver_category": None,
                "receiver_origin_category": None,
            })
            continue
        op, words = instruction
        receiver_tokens = []
        if target_field_ref is None:
            if op not in audit.INVOKES or dex.method(words[1]) != target_method:
                raise ValueError("TCA_TRACE_CALLSITE_TARGET_MISMATCH")
            register = _argument_register(
                dex, op, words, target_method, wrapper_position,
                expected_type=target_argument_type
            )
            value_tokens = [state["registers"].get(register) for state in states]
            receiver_register = None
        else:
            if op not in (0x5b, 0x67) or audit.field_id(dex, words[1]) != target_field_ref:
                raise ValueError("TCA_TRACE_FIELD_STORE_TARGET_MISMATCH")
            if op == 0x5b:  # iput-object value, instance receiver
                register = (words[0] >> 8) & 15
                receiver_register = (words[0] >> 12) & 15
            else:  # sput-object value
                register = (words[0] >> 8) & 0xff
                receiver_register = None
            value_tokens = [state["registers"].get(register) for state in states]
            if receiver_register is not None:
                receiver_tokens = [
                    state["registers"].get(receiver_register) for state in states
                ]

        same = (
            register is not None and bool(value_tokens)
            and len(set(value_tokens)) == 1
            and isinstance(value_tokens[0], str)
            and value_tokens[0].startswith("TCA_INIT@")
        )
        same_reference = (
            register is not None and bool(value_tokens)
            and len(set(value_tokens)) == 1
            and isinstance(value_tokens[0], str)
            and value_tokens[0].startswith(("TCA_", "REF_"))
            and not value_tokens[0].startswith("TCA_NULL@")
        )
        value_token = (
            value_tokens[0]
            if value_tokens and len(set(value_tokens)) == 1 else None
        )
        parameter_register = _parameter_register_from_tca_token(value_token)
        parameter_position = (
            logical_position_for_parameter_register(
                dex, method, flags, code_off, parameter_register
            ) if parameter_register is not None else None
        )
        receiver_token = (
            receiver_tokens[0]
            if receiver_tokens and len(set(receiver_tokens)) == 1 else None
        )
        same_receiver = (
            bool(receiver_tokens) and len(set(receiver_tokens)) == 1
            and isinstance(receiver_token, str)
            and receiver_token.startswith(("TCA_", "REF_"))
        )
        receiver_category = (
            "THIS" if receiver_token == "TCA_THIS"
                or (isinstance(receiver_token, str) and receiver_token.startswith("REF_THIS@"))
            else "PARAMETER" if isinstance(receiver_token, str)
                and receiver_token.startswith("REF_PARAMETER@")
            else "STATIC_FIELD" if isinstance(receiver_token, str)
                and receiver_token.startswith("REF_STATIC_FIELD@")
            else "FIELD" if isinstance(receiver_token, str)
                and ("FIELD@" in receiver_token)
            else "UNKNOWN" if receiver_register is not None else "STATIC"
        )

        field_ref = None
        field_receiver_category = None
        field_pc = None
        if isinstance(value_token, str):
            match = re.search(
                r"(?:TCA_FIELD|TCA_STATIC_FIELD)@([0-9]+)", value_token
            )
            if match:
                field_pc = int(match.group(1))
            else:
                match = re.search(
                    r"REF_(?:THIS_)?FIELD@([0-9]+)|REF_STATIC_FIELD@([0-9]+)",
                    value_token
                )
                if match:
                    field_pc = int(match.group(1) or match.group(2))
        if field_pc is not None and field_pc in field_read_metadata:
            field_ref, field_receiver_token, field_is_static = field_read_metadata[field_pc]
            if field_is_static:
                field_receiver_category = "STATIC"
            elif field_receiver_token == "TCA_THIS" or (
                isinstance(field_receiver_token, str)
                and field_receiver_token.startswith("REF_THIS@")
            ):
                field_receiver_category = "THIS"
            elif isinstance(field_receiver_token, str) and field_receiver_token.startswith("REF_PARAMETER@"):
                field_receiver_category = "PARAMETER"
            elif isinstance(field_receiver_token, str) and field_receiver_token.startswith("REF_STATIC_FIELD@"):
                field_receiver_category = "STATIC_FIELD"
            elif isinstance(field_receiver_token, str) and "FIELD@" in field_receiver_token:
                field_receiver_category = "FIELD"
            else:
                field_receiver_category = "UNKNOWN"

        site_results.append({
            "reachable": True,
            "same_constructed_tca_on_all_paths": same,
            "same_tca_reference_on_all_paths": same_reference,
            "same_receiver_reference_on_all_paths": same_receiver,
            "origin_category": tca_origin_category(value_token),
            "origin_parameter_position": parameter_position,
            "origin_field_ref": field_ref,
            "origin_field_receiver_category": field_receiver_category,
            "receiver_origin_category": receiver_category,
        })

    instructions = cfg["instructions"]
    allocation_count = sum(
        op == 0x22 and dex.descriptor(words[1]) == WRAPPER
        for _pc, op, words in instructions
    )
    constructor_call_count = sum(
        op in audit.INVOKES and dex.method(words[1]) == WRAPPER_CTOR
        for _pc, op, words in instructions
    )
    return {
        "site_count": len(site_results),
        "same_constructed_tca_on_all_sites": (
            bool(site_results) and all(x["same_constructed_tca_on_all_paths"]
                                       for x in site_results)
        ),
        "same_tca_reference_on_all_sites": (
            bool(site_results) and all(x["same_tca_reference_on_all_paths"]
                                       for x in site_results)
        ),
        "same_receiver_reference_on_all_sites": (
            bool(site_results) and all(x["same_receiver_reference_on_all_paths"]
                                       for x in site_results)
        ),
        "site_results": site_results,
        "wrapper_allocation_count": allocation_count,
        "wrapper_constructor_call_count": constructor_call_count,
        "processed_state_count": processed,
        "path_state_count": sum(len(states) for states in incoming.values()),
        "exception_handler_edges_included": False,
    }

def _trace_events_for_callsites(dex, method, flags, code_off, target, callsite_pcs):
    try:
        trace = audit.trace_track_identity_method_cfg(
            dex, method, flags, code_off
        )
    except (ValueError, audit.DexError) as exc:
        return None, type(exc).__name__
    rows = [
        event for event in trace.get("events", ())
        if event.get("callee") == {
            "owner": target[0], "method": target[1], "signature": target[2]
        } and event.get("pc") in set(callsite_pcs)
    ]
    return rows, None


def scan_direct_callers(apks):
    target_definition = None
    caller_definitions = {}
    caller_sites = {}
    dex_count = 0
    scanned_methods = 0
    direct_site_count = 0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("TCA_DIRECT_DEX_LIMIT")
                dex_count += 1
                dex = audit.Dex(archive.read(entry.filename))
                for method, flags, code_off in audit.method_definitions_with_flags(dex):
                    scanned_methods += 1
                    key = (method[0], method[1], method[2])
                    if method == TARGET:
                        if target_definition is not None:
                            raise ValueError("TCA_TARGET_DUPLICATE_DEFINITION")
                        target_definition = (dex, method, flags, code_off)
                    sites = []
                    for pc, op, words in audit.instructions(dex, code_off):
                        if op in audit.INVOKES and dex.method(words[1]) == TARGET:
                            sites.append(pc)
                    if not sites:
                        continue
                    direct_site_count += len(sites)
                    if direct_site_count > MAX_DIRECT_CALLS:
                        raise ValueError("TCA_DIRECT_CALLSITE_LIMIT")
                    if key not in caller_definitions:
                        if len(caller_definitions) >= MAX_DIRECT_CALLERS:
                            raise ValueError("TCA_DIRECT_CALLER_LIMIT")
                        caller_definitions[key] = (dex, method, flags, code_off)
                        caller_sites[key] = []
                    caller_sites[key].extend(sites)

    if dex_count != 6:
        raise ValueError("TCA_SIGNED_SIX_DEX_REQUIRED")
    if target_definition is None:
        raise ValueError("TCA_EXACT_LCA9_METHOD_NOT_DEFINED")
    if not (target_definition[2] & audit.ACC_STATIC):
        raise ValueError("TCA_TARGET_NOT_STATIC")
    positions = logical_parameter_positions(
        TARGET, target_definition[2], WRAPPER
    )
    if positions != [TARGET_WRAPPER_POSITION]:
        raise ValueError("TCA_TARGET_WRAPPER_PARAMETER_SHAPE")

    direct_rows = []
    upstream_targets = {}
    field_read_targets = {}
    for key, (dex, method, flags, code_off) in sorted(caller_definitions.items()):
        pcs = caller_sites[key]
        try:
            direct_trace = trace_exact_tca_constructor_to_callsites(
                dex, method, flags, code_off, TARGET, pcs,
                TARGET_WRAPPER_POSITION, target_argument_type=WRAPPER
            )
        except (ValueError, audit.DexError):
            direct_rows.append({
                "trace_complete": False,
                "wrapper_origin_categories": ["TRACE_FAILED"],
                "constructor_to_lca9_same_object": False,
                "same_tca_reference_to_lca9": False,
            })
            continue

        categories = {
            row["origin_category"] for row in direct_trace["site_results"]
        }
        categories = sorted(categories or {"NO_IDENTITY"})
        direct_rows.append({
            "trace_complete": True,
            "callsite_count": len(pcs),
            "wrapper_origin_categories": categories,
            "constructor_to_lca9_same_object": direct_trace[
                "same_constructed_tca_on_all_sites"
            ],
            "same_tca_reference_to_lca9": direct_trace[
                "same_tca_reference_on_all_sites"
            ],
            "constructor_trace": direct_trace,
        })

        for site in direct_trace["site_results"]:
            field_ref = site.get("origin_field_ref")
            if field_ref is not None:
                field_read_targets.setdefault(tuple(field_ref), []).append({
                    "reader_owner": method[0],
                    "receiver_category": site.get("origin_field_receiver_category"),
                    "same_tca_reference": site.get("same_tca_reference_on_all_paths", False),
                })

        parameter_positions = {
            row.get("origin_parameter_position")
            for row in direct_trace["site_results"]
        }
        if len(parameter_positions) == 1 and None not in parameter_positions:
            upstream_targets[key] = next(iter(parameter_positions))

    return {
        "dex_count": dex_count,
        "scanned_method_count": scanned_methods,
        "target_body_found": bool(target_definition[3]),
        "direct_callsite_count": direct_site_count,
        "direct_caller_count": len(caller_definitions),
        "direct_rows": direct_rows,
        "upstream_targets": upstream_targets,
        "field_read_targets": field_read_targets,
        "caller_definitions": caller_definitions,
        "caller_sites": caller_sites,
        "target_definition": target_definition,
    }


def scan_upstream_callers(apks, direct):
    targets = direct["upstream_targets"]
    if not targets:
        return {
            "upstream_callsite_count": 0,
            "upstream_caller_count": 0,
            "upstream_rows": [],
            "complete": True,
        }

    caller_definitions = {}
    caller_sites = {}
    call_count = 0
    dex_count = 0
    scanned_methods = 0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("TCA_UPSTREAM_DEX_LIMIT")
                dex_count += 1
                dex = audit.Dex(archive.read(entry.filename))
                for method, flags, code_off in audit.method_definitions_with_flags(dex):
                    scanned_methods += 1
                    key = (method[0], method[1], method[2])
                    sites = []
                    for pc, op, words in audit.instructions(dex, code_off):
                        if op in audit.INVOKES and dex.method(words[1]) in targets:
                            sites.append((pc, dex.method(words[1])))
                    if not sites:
                        continue
                    call_count += len(sites)
                    if call_count > MAX_UPSTREAM_CALLS:
                        raise ValueError("TCA_UPSTREAM_CALLSITE_LIMIT")
                    if key not in caller_definitions:
                        if len(caller_definitions) >= MAX_UPSTREAM_CALLERS:
                            raise ValueError("TCA_UPSTREAM_CALLER_LIMIT")
                        caller_definitions[key] = (dex, method, flags, code_off)
                        caller_sites[key] = []
                    caller_sites[key].extend(sites)

    if dex_count != 6:
        raise ValueError("TCA_UPSTREAM_SIGNED_SIX_DEX_REQUIRED")

    upstream_rows = []
    trace_complete_all = True
    for key, (dex, method, flags, code_off) in sorted(caller_definitions.items()):
        targets_here = {}
        for pc, target in caller_sites[key]:
            targets_here.setdefault(target, []).append(pc)

        for target, pcs in sorted(targets_here.items()):
            position = targets[target]
            target_def = direct["caller_definitions"][target]
            target_type = logical_parameter_type(
                target_def[1], target_def[2], position
            )
            if not target_type or not target_type.startswith(("L", "[")):
                raise ValueError("TCA_UPSTREAM_TARGET_ARGUMENT_NOT_REFERENCE")
            try:
                constructor_trace = trace_exact_tca_constructor_to_callsites(
                    dex, method, flags, code_off, target, pcs, position,
                    target_argument_type=target_type
                )
            except (ValueError, audit.DexError):
                constructor_trace = None
                trace_complete_all = False

            categories = set(
                row["origin_category"]
                for row in (constructor_trace or {}).get("site_results", ())
            )
            categories = sorted(categories or {
                "TRACE_FAILED" if constructor_trace is None else "NO_IDENTITY"
            })

            fp0_summary = None
            if method == INITIAL:
                resume_def = None
                for candidate, candidate_flags, candidate_code in (
                        audit.method_definitions_with_flags(dex)):
                    if candidate == RESUME:
                        resume_def = (dex, candidate, candidate_flags, candidate_code)
                        break
                if resume_def is not None:
                    try:
                        cont = audit.trace_native_track_coroutine_continuation(
                            dex, method, flags, code_off,
                            resume_def[1], resume_def[2], resume_def[3]
                        )
                        fp0_summary = {
                            "resume_track_argument_explicit_null":
                                cont.get("resume_track_argument_explicit_null", False),
                            "continuation_field_track_to_opaque_wrapper_candidate":
                                cont.get("continuation_field_track_to_opaque_wrapper_candidate", False),
                            "original_track_parameter_to_opaque_wrapper_candidate":
                                cont.get("original_track_parameter_to_opaque_wrapper_candidate", False),
                            "continuation_field_store_to_read_same_object_proven":
                                cont.get("continuation_field_store_to_read_same_object_proven", False),
                            "branch_path_predicates_evaluated":
                                cont.get("branch_path_predicates_evaluated", False),
                            "wrapper_continuation_handoff_site_count":
                                len(cont.get("wrapper_continuation_handoff_sites", ())),
                        }
                    except (ValueError, audit.DexError):
                        fp0_summary = {"trace_complete": False}

            upstream_rows.append({
                "trace_complete": constructor_trace is not None,
                "wrapper_origin_categories": categories,
                "constructor_to_direct_caller_same_object": (
                    constructor_trace["same_constructed_tca_on_all_sites"]
                    if constructor_trace else False
                ),
                "same_reference_to_direct_caller": (
                    constructor_trace["same_tca_reference_on_all_sites"]
                    if constructor_trace else False
                ),
                "constructor_trace": constructor_trace,
                "is_gpo_new": method == INITIAL,
                "fp0_continuation_summary": fp0_summary,
            })

    return {
        "upstream_callsite_count": call_count,
        "upstream_caller_count": len(caller_definitions),
        "upstream_rows": upstream_rows,
        "complete": trace_complete_all,
    }



def scan_field_writers(apks, direct):
    targets = direct["field_read_targets"]
    if not targets:
        return {
            "field_count": 0,
            "reader_site_count": 0,
            "writer_site_count": 0,
            "writer_method_count": 0,
            "writer_value_origin_categories": [],
            "writer_receiver_categories": [],
            "owner_constructor_write_proven_count": 0,
            "field_chain_proven_count": 0,
            "all_direct_call_sites_field_backed": False,
            "tca_constructor_to_lca9_via_field_proven": False,
        }

    writer_definitions = {}
    writer_sites = {}
    writer_traces = {}
    dex_count = 0
    scanned_methods = 0
    writer_site_count = 0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("TCA_FIELD_WRITER_DEX_LIMIT")
                dex_count += 1
                dex = audit.Dex(archive.read(entry.filename))
                for method, flags, code_off in audit.method_definitions_with_flags(dex):
                    scanned_methods += 1
                    method_key = (method[0], method[1], method[2])
                    for pc, op, words in audit.instructions(dex, code_off):
                        if op not in (0x5b, 0x67):  # iput-object / sput-object
                            continue
                        field_ref = audit.field_id(dex, words[1])
                        if field_ref not in targets:
                            continue
                        writer_site_count += 1
                        if writer_site_count > 512:
                            raise ValueError("TCA_FIELD_WRITER_SITE_LIMIT")
                        if method_key not in writer_definitions:
                            writer_definitions[method_key] = (
                                dex, method, flags, code_off
                            )
                        writer_sites.setdefault(field_ref, {}).setdefault(
                            method_key, []
                        ).append(pc)

    if dex_count != 6:
        raise ValueError("TCA_FIELD_WRITER_SIGNED_SIX_DEX_REQUIRED")

    field_rows = []
    all_field_chains_proven = True
    total_reader_sites = 0
    for field_ref, readers in targets.items():
        reader_site_count = len(readers)
        total_reader_sites += reader_site_count
        reader_this_owner = all(
            row.get("reader_owner") == field_ref[0]
            and row.get("receiver_category") == "THIS"
            for row in readers
        )
        reader_same_reference = all(
            row.get("same_tca_reference", False) for row in readers
        )

        field_writers = writer_sites.get(field_ref, {})
        field_writer_sites = sum(len(pcs) for pcs in field_writers.values())
        writer_origin_categories = set()
        writer_receiver_categories = set()
        owner_constructor_proven = False
        owner_clinit_proven = False
        writer_method_count = len(field_writers)

        for method_key, pcs in field_writers.items():
            dex, method, flags, code_off = writer_definitions[method_key]
            try:
                trace = trace_exact_tca_constructor_to_callsites(
                    dex, method, flags, code_off, None, pcs, 0,
                    target_argument_type=None, target_field_ref=field_ref
                )
            except (ValueError, audit.DexError):
                continue
            writer_traces.setdefault(method_key, []).extend(trace["site_results"])
            writer_origin_categories.update(
                site["origin_category"] for site in trace["site_results"]
            )
            writer_receiver_categories.update(
                site["receiver_origin_category"] for site in trace["site_results"]
            )

            owner_constructor = method[1] == "<init>" and method[0] == field_ref[0]
            owner_clinit = method[1] == "<clinit>" and method[0] == field_ref[0]
            if (owner_constructor and field_writer_sites == 1
                    and writer_method_count == 1
                    and trace["same_constructed_tca_on_all_sites"]
                    and trace["same_receiver_reference_on_all_sites"]
                    and all(site["receiver_origin_category"] == "THIS"
                            for site in trace["site_results"])):
                owner_constructor_proven = True
            if (owner_clinit and field_writer_sites == 1
                    and writer_method_count == 1
                    and trace["same_constructed_tca_on_all_sites"]):
                owner_clinit_proven = True

        instance_chain = (
            reader_this_owner and reader_same_reference
            and owner_constructor_proven
        )
        static_chain = (
            all(row.get("receiver_category") == "STATIC" for row in readers)
            and reader_same_reference and owner_clinit_proven
        )
        field_chain = instance_chain or static_chain
        if not field_chain:
            all_field_chains_proven = False
        field_rows.append({
            "reader_site_count": reader_site_count,
            "reader_this_owner_match": reader_this_owner,
            "reader_same_reference": reader_same_reference,
            "writer_site_count": field_writer_sites,
            "writer_method_count": writer_method_count,
            "writer_value_origin_categories": sorted(writer_origin_categories),
            "writer_receiver_categories": sorted(writer_receiver_categories),
            "owner_constructor_write_proven": owner_constructor_proven,
            "owner_static_initializer_write_proven": owner_clinit_proven,
            "field_chain_proven": field_chain,
        })

    all_direct_call_sites_field_backed = (
        total_reader_sites == direct["direct_callsite_count"]
        and total_reader_sites > 0
    )
    writer_upstream_targets = {}
    for method_key, site_rows in writer_traces.items():
        positions = {
            row.get("origin_parameter_position") for row in site_rows
        }
        if len(positions) == 1 and None not in positions:
            writer_upstream_targets[method_key] = next(iter(positions))

    return {
        "field_count": len(targets),
        "reader_site_count": total_reader_sites,
        "writer_site_count": writer_site_count,
        "writer_method_count": len(writer_definitions),
        "writer_definitions": writer_definitions,
        "writer_upstream_targets": writer_upstream_targets,
        "writer_value_origin_categories": sorted({
            category for row in field_rows
            for category in row["writer_value_origin_categories"]
        }),
        "writer_receiver_categories": sorted({
            category for row in field_rows
            for category in row["writer_receiver_categories"]
        }),
        "owner_constructor_write_proven_count": sum(
            row["owner_constructor_write_proven"] for row in field_rows
        ),
        "owner_static_initializer_write_proven_count": sum(
            row["owner_static_initializer_write_proven"] for row in field_rows
        ),
        "field_chain_proven_count": sum(
            row["field_chain_proven"] for row in field_rows
        ),
        "all_direct_call_sites_field_backed": all_direct_call_sites_field_backed,
        "tca_constructor_to_lca9_via_field_proven": (
            all_direct_call_sites_field_backed
            and bool(field_rows)
            and all_field_chains_proven
        ),
    }



def scan_field_writer_upstream_callers(apks, fields):
    targets = fields["writer_upstream_targets"]
    if not targets:
        return {
            "callsite_count": 0,
            "caller_count": 0,
            "origin_categories": [],
            "constructor_to_writer_same_object_count": 0,
            "same_reference_to_writer_count": 0,
            "fp0_resume_track_argument_explicit_null": False,
            "fp0_continuation_field_track_to_wrapper_candidate": False,
            "complete": True,
        }

    caller_definitions = {}
    caller_sites = {}
    call_count = 0
    dex_count = 0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("TCA_WRITER_UPSTREAM_DEX_LIMIT")
                dex_count += 1
                dex = audit.Dex(archive.read(entry.filename))
                for method, flags, code_off in audit.method_definitions_with_flags(dex):
                    key = (method[0], method[1], method[2])
                    sites = []
                    for pc, op, words in audit.instructions(dex, code_off):
                        if op in audit.INVOKES and dex.method(words[1]) in targets:
                            sites.append((pc, dex.method(words[1])))
                    if not sites:
                        continue
                    call_count += len(sites)
                    if call_count > MAX_UPSTREAM_CALLS:
                        raise ValueError("TCA_WRITER_UPSTREAM_CALLSITE_LIMIT")
                    if key not in caller_definitions:
                        if len(caller_definitions) >= MAX_UPSTREAM_CALLERS:
                            raise ValueError("TCA_WRITER_UPSTREAM_CALLER_LIMIT")
                        caller_definitions[key] = (dex, method, flags, code_off)
                        caller_sites[key] = []
                    caller_sites[key].extend(sites)

    if dex_count != 6:
        raise ValueError("TCA_WRITER_UPSTREAM_SIGNED_SIX_DEX_REQUIRED")

    rows = []
    complete = True
    for key, (dex, method, flags, code_off) in sorted(caller_definitions.items()):
        targets_here = {}
        for pc, target in caller_sites[key]:
            targets_here.setdefault(target, []).append(pc)
        for target, pcs in sorted(targets_here.items()):
            position = targets[target]
            target_def = fields["writer_definitions"][target]
            target_type = logical_parameter_type(
                target_def[1], target_def[2], position
            )
            if not target_type or not target_type.startswith(("L", "[")):
                raise ValueError("TCA_WRITER_UPSTREAM_ARGUMENT_NOT_REFERENCE")
            try:
                trace = trace_exact_tca_constructor_to_callsites(
                    dex, method, flags, code_off, target, pcs, position,
                    target_argument_type=target_type
                )
            except (ValueError, audit.DexError):
                trace = None
                complete = False

            fp0_summary = None
            if method == INITIAL:
                resume_def = None
                for candidate, candidate_flags, candidate_code in (
                        audit.method_definitions_with_flags(dex)):
                    if candidate == RESUME:
                        resume_def = (candidate, candidate_flags, candidate_code)
                        break
                if resume_def is not None:
                    try:
                        cont = audit.trace_native_track_coroutine_continuation(
                            dex, method, flags, code_off,
                            resume_def[0], resume_def[1], resume_def[2]
                        )
                        fp0_summary = {
                            "resume_track_argument_explicit_null":
                                cont.get("resume_track_argument_explicit_null", False),
                            "continuation_field_track_to_opaque_wrapper_candidate":
                                cont.get("continuation_field_track_to_opaque_wrapper_candidate", False),
                            "continuation_field_store_to_read_same_object_proven":
                                cont.get("continuation_field_store_to_read_same_object_proven", False),
                            "branch_path_predicates_evaluated":
                                cont.get("branch_path_predicates_evaluated", False),
                        }
                    except (ValueError, audit.DexError):
                        fp0_summary = {"trace_complete": False}

            rows.append({
                "origin_categories": sorted({
                    site["origin_category"]
                    for site in (trace or {}).get("site_results", ())
                }),
                "constructor_to_writer_same_object": (
                    trace["same_constructed_tca_on_all_sites"] if trace else False
                ),
                "same_reference_to_writer": (
                    trace["same_tca_reference_on_all_sites"] if trace else False
                ),
                "fp0_continuation_summary": fp0_summary,
            })

    fp0 = [
        row["fp0_continuation_summary"]
        for row in rows if row.get("fp0_continuation_summary")
    ]
    return {
        "callsite_count": call_count,
        "caller_count": len(caller_definitions),
        "origin_categories": sorted({
            category for row in rows for category in row["origin_categories"]
        }),
        "constructor_to_writer_same_object_count": sum(
            row["constructor_to_writer_same_object"] for row in rows
        ),
        "same_reference_to_writer_count": sum(
            row["same_reference_to_writer"] for row in rows
        ),
        "fp0_resume_track_argument_explicit_null": any(
            row.get("resume_track_argument_explicit_null", False) for row in fp0
        ),
        "fp0_continuation_field_track_to_wrapper_candidate": any(
            row.get("continuation_field_track_to_opaque_wrapper_candidate", False)
            for row in fp0
        ),
        "complete": complete,
    }


def safe_summary(direct, upstream, fields):
    direct_rows = direct["direct_rows"]
    upstream_rows = upstream["upstream_rows"]
    direct_constructor = sum(
        row.get("constructor_to_lca9_same_object", False) for row in direct_rows
    )
    upstream_constructor = sum(
        row.get("constructor_to_direct_caller_same_object", False)
        for row in upstream_rows
    )
    fp0 = [
        row["fp0_continuation_summary"]
        for row in upstream_rows if row.get("fp0_continuation_summary")
    ]
    return {
        "verdict": "SIGNED_LCA9_TCA_BIRTH_ORIGIN_READONLY",
        "signed_dex_count": direct["dex_count"],
        "scanned_method_count": direct["scanned_method_count"],
        "target_body_found": direct["target_body_found"],
        "direct_callsite_count": direct["direct_callsite_count"],
        "direct_caller_count": direct["direct_caller_count"],
        "direct_caller_trace_complete_count": sum(
            row.get("trace_complete", False) for row in direct_rows
        ),
        "direct_wrapper_origin_categories": sorted({
            category for row in direct_rows
            for category in row.get("wrapper_origin_categories", ())
        }),
        "direct_constructor_to_lca9_same_object_count": direct_constructor,
        "direct_same_tca_reference_to_lca9_count": sum(
            row.get("same_tca_reference_to_lca9", False) for row in direct_rows
        ),
        "upstream_callsite_count": upstream["upstream_callsite_count"],
        "upstream_caller_count": upstream["upstream_caller_count"],
        "upstream_wrapper_origin_categories": sorted({
            category for row in upstream_rows
            for category in row.get("wrapper_origin_categories", ())
        }),
        "upstream_constructor_to_direct_caller_same_object_count": upstream_constructor,
        "upstream_same_reference_to_direct_caller_count": sum(
            row.get("same_reference_to_direct_caller", False) for row in upstream_rows
        ),
        "direct_tca_field_count": fields["field_count"],
        "direct_tca_field_reader_site_count": fields["reader_site_count"],
        "direct_field_reader_receiver_categories": sorted({
            row.get("receiver_category")
            for readers in direct["field_read_targets"].values()
            for row in readers
        }),
        "tca_field_writer_site_count": fields["writer_site_count"],
        "tca_field_writer_method_count": fields["writer_method_count"],
        "tca_field_writer_value_origin_categories": fields["writer_value_origin_categories"],
        "tca_field_writer_receiver_categories": fields["writer_receiver_categories"],
        "tca_owner_constructor_field_write_proven_count": fields["owner_constructor_write_proven_count"],
        "tca_field_chain_proven_count": fields["field_chain_proven_count"],
        "tca_constructor_to_lca9_via_field_proven": fields["tca_constructor_to_lca9_via_field_proven"],
        "exact_tca_constructor_to_lca9_same_object_proven": bool(
            direct_constructor or upstream_constructor
            or fields["tca_constructor_to_lca9_via_field_proven"]
        ),
        "fp0_resume_track_argument_explicit_null": any(
            row.get("resume_track_argument_explicit_null", False) for row in fp0
        ),
        "fp0_continuation_field_track_to_wrapper_candidate": any(
            row.get("continuation_field_track_to_opaque_wrapper_candidate", False)
            for row in fp0
        ),
        "fp0_continuation_field_store_to_read_same_object_proven": any(
            row.get("continuation_field_store_to_read_same_object_proven", False)
            for row in fp0
        ),
        "fp0_branch_path_predicates_evaluated": any(
            row.get("branch_path_predicates_evaluated", False) for row in fp0
        ),
        "fp0_wrapper_continuation_handoff_site_count": sum(
            row.get("wrapper_continuation_handoff_site_count", 0) for row in fp0
        ),
        "bounded_upstream_scan_complete": upstream["complete"],
        "virtual_or_interface_runtime_dispatch_proven": False,
        "current_selected_track_or_queue_generation_proven": False,
        "active_audible_decoder_source_proven": False,
        "replacement_audio_connected_or_audible": False,
        "private_method_symbols_field_names_or_values_disclosed": False,
        "track_album_ids_titles_urls_tokens_account_or_audio_read": False,
    }


def run(xapk: Path):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size != audit.PINNED_XAPK_BYTES:
        raise ValueError("TCA_PINNED_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk) != audit.PINNED_XAPK_SHA256:
        raise ValueError("TCA_PINNED_XAPK_SHA_MISMATCH")

    with tempfile.TemporaryDirectory(prefix="celikom-lca9-tca-birth-") as tmp:
        splits = audit.unbundle_candidate(xapk, Path(tmp))
        if len(splits) != 16:
            raise ValueError("TCA_SIGNED_SPLIT_COUNT_MISMATCH")
        signer = audit.verify_split_set(splits)
        if signer.get("verified_issuer_signed_splits") != 16:
            raise ValueError("TCA_ISSUER_SIGNER_MISMATCH")
        bases = []
        for apk in splits:
            meta = trusted.package_metadata(apk)
            if (meta.get("name") != "ru.yandex.music"
                    or meta.get("versionCode") != "24025542"):
                raise ValueError("TCA_ORIGINAL_PACKAGE_VERSION_MISMATCH")
            if not meta.get("split"):
                bases.append(apk)
        if len(bases) != 1 or trusted.sha256_file(bases[0]) != trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("TCA_ORIGINAL_BASE_APK_SHA_MISMATCH")
        direct = scan_direct_callers(splits)
        upstream = scan_upstream_callers(splits, direct)
        fields = scan_field_writers(splits, direct)
        return safe_summary(direct, upstream, fields)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xapk", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.xapk), ensure_ascii=False, sort_keys=True))
    except (RuntimeError, ValueError, audit.DexError, OSError,
            zipfile.BadZipFile, KeyError, IndexError) as exc:
        code = str(exc)
        print(json.dumps({
            "verdict": "SIGNED_LCA9_TCA_BIRTH_ORIGIN_INCOMPLETE",
            "error_code": code if re.fullmatch(r"[A-Z0-9_]{1,80}", code) else None,
            "replacement_audio_connected_or_audible": False,
        }, sort_keys=True))
        raise SystemExit(2)
