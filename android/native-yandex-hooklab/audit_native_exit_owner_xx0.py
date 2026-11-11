#!/usr/bin/env python3
"""CI-only read-only signed Yandex #170gpr DEX audit of native MAIN exit owner.

After native ARM13 pass-through hook observed STATIC_RUN_B -> Lxx0.run,
inspect ONLY this method and its direct incoming/outgoing references. No
vendor runtime hooks, caller bypass, code rewriting, accounts or raw APKs.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "android-native-gate1"))
import clone_native_splits_ephemeral as exact
from audit_native_exit_calls_static import safe_method_meta
from inspect_android_host import Dex, DexError
from trace_native_callers import OP_WIDTH, invoked_method_indexes, method_definitions, payload_width

TARGET = ("Lxx0;", "run", "()V")
MAX_CODE_UNITS = 500_000
EXIT_TARGETS = frozenset((
    ("Ljava/lang/System;", "exit", "(I)V"),
    ("Ljava/lang/Runtime;", "exit", "(I)V"),
    ("Landroid/os/Process;", "killProcess", "(I)V"),
))


def control_flow_shape(dex, code_off: int) -> dict:
    """Bounded instruction decoding, no extraction of literals or code bytes."""
    dex.bounds(code_off, 16)
    units = dex.u32(code_off + 12)
    if units > MAX_CODE_UNITS:
        raise DexError("Target method too large")
    start = code_off + 16
    dex.bounds(start, units * 2)
    pc = 0
    if_count = goto_count = switch_count = return_count = 0
    while pc < units:
        word = dex.u16(start + pc * 2)
        op = word & 0xFF
        width = (payload_width(dex, start, units, pc, word >> 8)
                 if op == 0 else OP_WIDTH.get(op))
        if width is None or pc + width > units:
            raise DexError("Invalid instruction width")
        if 0x32 <= op <= 0x3D:
            if_count += 1
        elif 0x28 <= op <= 0x2A:
            goto_count += 1
        elif op in (0x2B, 0x2C):
            switch_count += 1
        elif 0x0E <= op <= 0x11:
            return_count += 1
        pc += width
    return {
        "instruction_code_units_bounded": min(units, MAX_CODE_UNITS),
        "if_branch_count_bounded": min(if_count, 100),
        "goto_count_bounded": min(goto_count, 100),
        "switch_count_bounded": min(switch_count, 100),
        "return_count_bounded": min(return_count, 100),
        "try_region_count_bounded": min(dex.u16(code_off + 6), 100),
        "scan_complete": pc == units,
        "no_literal_values_exposed": True,
        "absence_of_branches_not_proof_of_unconditional_execution": True,
    }


def audit_dex(data: bytes) -> dict:
    dex = Dex(data)
    target_idx = {i for i in range(dex.method_count) if dex.method(i) == TARGET}
    constructor_idx = {i for i in range(dex.method_count)
                       if dex.method(i)[0] == TARGET[0]
                       and dex.method(i)[1] == "<init>"}
    report = {
        "target_definitions": 0,
        "target_invocations": [],
        "target_control_flow": [],
        "incoming_constructor_sites": [],
        "incoming_direct_run_sites": [],
        "other_xx0_method_defs_bounded": 0,
        "methods_scanned_bounded": 0,
        "scan_complete": True,
    }
    for idx, code in method_definitions(dex):
        meta = dex.method(idx)
        report["methods_scanned_bounded"] += 1
        is_target = meta == TARGET
        if meta[0] == TARGET[0] and not is_target:
            report["other_xx0_method_defs_bounded"] += 1
        if is_target:
            report["target_definitions"] += 1
            report["target_control_flow"].append(control_flow_shape(dex, code))
        for called, pc, op in invoked_method_indexes(dex, code):
            callee = dex.method(called)
            if is_target and len(report["target_invocations"]) < 55:
                safe = safe_method_meta(callee)
                if safe is not None:
                    report["target_invocations"].append({
                        **safe,
                        "direct_exit_target": callee in EXIT_TARGETS,
                        "code_unit_offset_bounded": min(pc, MAX_CODE_UNITS),
                    })
            if (called in constructor_idx
                    and len(report["incoming_constructor_sites"]) < 35):
                safe = safe_method_meta(meta)
                if safe:
                    report["incoming_constructor_sites"].append(safe)
            if (called in target_idx
                    and len(report["incoming_direct_run_sites"]) < 35):
                safe = safe_method_meta(meta)
                if safe:
                    report["incoming_direct_run_sites"].append(safe)
    report["methods_scanned_bounded"] = min(report["methods_scanned_bounded"], 500000)
    report["other_xx0_method_defs_bounded"] = min(report["other_xx0_method_defs_bounded"], 100)
    report["scan_complete"] = True
    return report


def run() -> dict:
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise ValueError("SIGNED_XX0_AUDIT_EPHEMERAL_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-xx0-signed-audit-") as temp:
        directory = Path(temp)
        archive = directory / "original.xapk"
        size, digest = exact.gpr.download(archive)
        if size != 60433885 or digest != exact.ARCHIVE_SHA:
            raise ValueError("PINNED_SIGNED_HOST_DIGEST_CHANGED")
        parts = exact.gpr.split_apks(archive, directory)
        if len(parts) != 5:
            raise ValueError("PUBLISHER_SPLIT_COUNT_INVALID")
        exact.gpr.inspect_publisher(parts)
        segments = []
        dex_count = 0
        for apk in parts:
            with zipfile.ZipFile(apk) as z:
                for name in sorted(z.namelist()):
                    if (name.startswith("classes") and name.endswith(".dex")
                            and "/" not in name):
                        dex_count += 1
                        segments.append(audit_dex(z.read(name)))
        if dex_count != 6 or sum(s["target_definitions"] for s in segments) != 1:
            raise ValueError("SIGNED_XX0_EXACT_ONE_BODY_EXPECTED")
        target = next(s for s in segments if s["target_definitions"])
        return {
            "verdict": "SIGNED_XX0_RUN_CONTROL_FLOW_AUDITED_NOT_RUNTIME_CAUSE",
            "signed_host": "2026.10.3 #170gpr",
            "original_signed_dex_count": dex_count,
            "exact_xx0_run_definition_count": 1,
            "xx0_run_control_flow": target["target_control_flow"][0],
            "xx0_run_direct_invokes": target["target_invocations"],
            "xx0_constructor_callers": [x for s in segments
                                       for x in s["incoming_constructor_sites"]][:35],
            "xx0_run_direct_callers": [x for s in segments
                                     for x in s["incoming_direct_run_sites"]][:35],
            "direct_xx0_constructors_bounded": min(
                sum(len(s["incoming_constructor_sites"]) for s in segments), 100),
            "direct_xx0_run_calls_bounded": min(
                sum(len(s["incoming_direct_run_sites"]) for s in segments), 100),
            "no_private_method_values_or_literals_exposed": True,
            "publisher_issuer_signature_touched": False,
            "clone_runtime_modified": False,
            "lspatch_sigbypass_or_passthrough_changed": False,
            "third_party_apk_or_dex_uploaded": False,
            "user_phone_touched": False,
            "runtime_exit_caller_independently_observed": "STATIC_RUN_B",
            "runtime_failure_condition_not_proven": True,
        }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except (ValueError, DexError, OSError, zipfile.BadZipFile) as err:
        label = str(err)
        if label not in (
                "SIGNED_XX0_AUDIT_EPHEMERAL_CI_ONLY",
                "PINNED_SIGNED_HOST_DIGEST_CHANGED",
                "PUBLISHER_SPLIT_COUNT_INVALID",
                "SIGNED_XX0_EXACT_ONE_BODY_EXPECTED"):
            label = "SIGNED_XX0_UNKNOWN_LAB_FAILURE"
        print(json.dumps({"verdict": "SIGNED_XX0_AUDIT_BLOCKED", "reason": label,
                          "vendor_artifact_uploaded": False}))
        sys.exit(2)
