#!/usr/bin/env python3
"""Read-only signed #170gpr Kotlin coroutine j() CFG audit for observed xx0 case2.

The original, unmodified issuer-signed host DEX is downloaded and verified
inside an ephemeral CI runner. No vendor bytes, strings, exception texts,
credentials, signature controls or rewritten APKs leave the runner.
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
from inspect_android_host import Dex, DexError
from trace_native_callers import (
    OP_WIDTH, payload_width, method_definitions, invoked_method_indexes,
)

TARGET = ("Lhi2;", "j", "(Ljava/lang/Object;)Ljava/lang/Object;")
XX0_CTOR = ("Lxx0;", "<init>", "(Landroid/content/Context;I)V")
HANDLER_POST = ("Landroid/os/Handler;", "post", "(Ljava/lang/Runnable;)Z")
ILLEGAL_STATE = ("Ljava/lang/IllegalStateException;", "<init>",
                 "(Ljava/lang/String;)V")


def signed32(n: int) -> int:
    return n - (1 << 32) if n & (1 << 31) else n


def valid_cfg(dex, off: int):
    dex.bounds(off, 16)
    count = dex.u32(off + 12)
    if count > 100000:
        raise DexError("Oversize coroutine")
    start = off + 16
    dex.bounds(start, count * 2)
    opcodes, nexts, switches = {}, {}, []
    pc = 0
    while pc < count:
        word = dex.u16(start + pc * 2)
        op = word & 0xff
        width = (payload_width(dex, start, count, pc, word >> 8)
                 if op == 0 else OP_WIDTH.get(op))
        if width is None or width < 1 or pc + width > count:
            raise DexError("Invalid coroutine instruction")
        opcodes[pc] = op
        after = pc + width
        next_pc = [after] if after < count else []
        if 0x32 <= op <= 0x3D:
            n = dex.u16(start + (pc + 1) * 2)
            delta = n - 65536 if n & 0x8000 else n
            next_pc.append(pc + delta)
        elif op in (0x28, 0x29, 0x2A):
            if op == 0x28:
                n = (word >> 8) & 255
                delta = n - 256 if n & 128 else n
            elif op == 0x29:
                n = dex.u16(start + (pc + 1) * 2)
                delta = n - 65536 if n & 32768 else n
            else:
                delta = signed32(dex.u32(start + (pc + 1) * 2))
            next_pc = [pc + delta]
        elif op in (0x2B, 0x2C):
            payload = pc + signed32(dex.u32(start + (pc + 1) * 2))
            if payload < 0 or payload + 2 > count:
                raise DexError("Bad coroutine switch payload")
            marker = dex.u16(start + payload * 2)
            n = dex.u16(start + (payload + 1) * 2)
            if (marker != (0x0100 if op == 0x2B else 0x0200)
                    or n > 100):
                raise DexError("Invalid coroutine switch size")
            if op == 0x2B:
                startkey = signed32(dex.u32(start + (payload + 2) * 2))
                keys = [startkey + k for k in range(n)]
                target_base = payload + 4
            else:
                keys = [signed32(dex.u32(start + (payload + 2 + 2*k)*2))
                        for k in range(n)]
                target_base = payload + 2 + n*2
            arms = []
            for k, key in enumerate(keys):
                delta = signed32(dex.u32(start + (target_base + 2*k)*2))
                target = pc + delta
                next_pc.append(target)
                arms.append((key, target))
            switches.append({"at": pc, "default": next_pc[0], "arms": arms})
        elif 0x0E <= op <= 0x11 or op == 0x27 or op == 0:
            next_pc = []
        nexts[pc] = next_pc
        pc = after
    for links in nexts.values():
        for target in links:
            if target not in opcodes:
                raise DexError("Coroutine graph target not aligned")
    return opcodes, nexts, switches


def reachable(edges: dict[int, list[int]], start: int, goal: int,
              excluded: int | None = None) -> bool:
    if start not in edges or goal not in edges:
        return False
    seen = set()
    stack = [start]
    while stack:
        pc = stack.pop()
        if pc == excluded or pc in seen:
            continue
        if pc == goal:
            return True
        seen.add(pc)
        stack.extend(edges[pc])
    return False



def nearby_error_literal_categories(dex, off: int, exception_pc: int) -> dict:
    """Inspect only local const-string instructions, report predefined enums.

    No user/account/source literal can escape the signed-only temporary runner.
    This is lexical context only: DEX register flow / exception throwing
    cannot be inferred from nearby literal tokens.
    """
    code_units = dex.u32(off + 12)
    start = off + 16
    pc = 0
    hints = set()
    direct_literal_count = 0
    while pc < exception_pc and pc < code_units:
        word = dex.u16(start + pc*2)
        op = word & 255
        width = (payload_width(dex, start, code_units, pc, word >> 8)
                 if op == 0 else OP_WIDTH.get(op))
        if width is None or pc + width > code_units:
            raise DexError("Invalid literal instruction width")
        if exception_pc - pc <= 40 and op in (0x1A, 0x1B):
            idx = (dex.u16(start + (pc+1)*2) if op == 0x1A
                   else dex.u32(start + (pc+1)*2))
            value = dex.string(idx).casefold()[:500]
            direct_literal_count += 1
            groups = (
                ("SIGNATURE_OR_CERT", ("signature", "signing", "certificate", "sha256")),
                ("ACCOUNT_AUTH", ("passport", "auth", "account", "credential", "login", "token")),
                ("PACKAGE_OR_PROCESS", ("package", "process", "component", "restart")),
                ("LOCALE", ("locale", "language", "translation")),
                ("PERMISSION", ("permission", "denied", "grant")),
                ("INIT_FAILURE", ("initializ", "invalid state", "failed", "failure")),
            )
            for label, keys in groups:
                if any(key in value for key in keys):
                    hints.add(label)
        pc += width
    return {
        "direct_const_string_sites_near_exception_bounded":
            min(direct_literal_count, 20),
        "allowlisted_lexical_hints_only": sorted(hints),
        "string_contents_never_exported": True,
        "this_does_not_prove_exception_message": True,
    }


def inspect_one(dex, code_off: int) -> dict:
    opcodes, edges, switches = valid_cfg(dex, code_off)
    direct = [(pc, dex.method(index))
              for index, pc, _ in invoked_method_indexes(dex, code_off)]
    ctor_sites = [pc for pc, method in direct if method == XX0_CTOR]
    post_sites = [pc for pc, method in direct if method == HANDLER_POST]
    illegal_sites = [pc for pc, method in direct if method == ILLEGAL_STATE]
    if len(ctor_sites) != 1 or len(post_sites) < 1:
        raise DexError("Unexpected signed coroutine signature")
    target = ctor_sites[0]
    required = lambda pos: not reachable(edges, 0, target, excluded=pos)
    branches = [
        {"at": pc, "one_arm_reaches_ctor": True}
        for pc, op in opcodes.items()
        if pc < target and 0x32 <= op <= 0x3D
        and len(edges[pc]) == 2
        and reachable(edges, edges[pc][0], target)
            != reachable(edges, edges[pc][1], target)
    ]
    switch_report = []
    for sw in switches[:4]:
        switch_report.append({
            "code_unit_bounded": min(sw["at"], 100000),
            "default_can_reach_mode2_ctor":
                reachable(edges, sw["default"], target),
            "case_routes": [{
                "case": key if -16 <= key <= 16 else "OUT_OF_RANGE",
                "can_reach_mode2_ctor": reachable(edges, dest, target),
            } for key, dest in sw["arms"][:32]],
            "switch_args_not_exported": True,
        })
    categories = (
        ("handler_post", lambda v: v == HANDLER_POST),
        ("illegal_state_ctor", lambda v: v == ILLEGAL_STATE),
        ("package_name_read", lambda v: v[:2] == (
            "Landroid/content/Context;", "getPackageName")),
        ("androidx_locales", lambda v: v[0].startswith("Landroidx/core/app/")),
        ("yandex_plus_locale", lambda v: v[0].startswith(
            "Lcom/yandex/plus/core/locale/")),
        ("passport", lambda v: v[0].startswith("Lcom/yandex/passport/")),
    )
    call_kinds = {}
    for name, match in categories:
        sites = [pc for pc, method in direct if match(method)]
        call_kinds[name] = {
            "total_calls_bounded": min(len(sites), 200),
            "on_some_entry_to_mode2_path": any(
                pc <= target and reachable(edges, 0, pc)
                and reachable(edges, pc, target)
                for pc in sites),
            "must_pass_some_callsite_to_reach_ctor": any(
                pc < target and required(pc) for pc in sites),
            "immediately_before_ctor_bounded": any(
                0 <= target - pc <= 20 for pc in sites),
        }
    return {
        "method_code_units_bounded": min(dex.u32(code_off + 12), 100000),
        "has_exact_mode2_ctor": True,
        "handler_post_sites_bounded": min(len(post_sites), 10),
        "illegal_state_ctor_sites_bounded": min(len(illegal_sites), 10),
        "nearby_exception_literal_hints":
            nearby_error_literal_categories(dex, code_off, illegal_sites[0])
            if illegal_sites else {"none": True},
        "illegal_state_ctor_dominates_mode2_creation": any(
            pc < target and required(pc) for pc in illegal_sites),
        "guards_separating_mode2_creation_count_bounded": min(len(branches), 100),
        "switch_case_reachability": switch_report,
        "bounded_call_families": call_kinds,
        "CFG_ignores_catch_edges_and_register_values": True,
        "runtime_cause_not_inferred": True,
    }


def run() -> dict:
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise ValueError("CI_SIGNED_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-hi2-cfg-") as tmp:
        path = Path(tmp)
        archive = path / "original.xapk"
        size, sha = exact.gpr.download(archive)
        if size != 60433885 or sha != exact.ARCHIVE_SHA:
            raise ValueError("PUBLISHER_SIGNED_HOST_DRIFT")
        splits = exact.gpr.split_apks(archive, path)
        if len(splits) != 5:
            raise ValueError("SPLIT_COUNT_CHANGED")
        exact.gpr.inspect_publisher(splits)
        records, found, dex_count = [], 0, 0
        for apk in splits:
            with zipfile.ZipFile(apk) as z:
                for name in sorted(z.namelist()):
                    if name.startswith("classes") and name.endswith(".dex") and "/" not in name:
                        dex_count += 1
                        dex = Dex(z.read(name))
                        for idx, off in method_definitions(dex):
                            if dex.method(idx) == TARGET:
                                found += 1
                                records.append(inspect_one(dex, off))
        if dex_count != 6 or found != 1:
            raise ValueError("EXACT_SIGNED_METHOD_NOT_FOUND")
        return {
            "verdict": "SIGNED_HI2_MODE2_CFG_STATIC_ONLY",
            "signed_original_dex_count": dex_count,
            "exact_method_count": found,
            "mode2_creator_cfg": records[0],
            "native_runtime_mode2_already_confirmed_by_CI": 43040652116,
            "no_binary_or_private_strings_uploaded": True,
            "publisher_signed_app_untouched": True,
            "security_policies_unchanged": True,
            "consumer_application_released": False,
        }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except (DexError, ValueError, zipfile.BadZipFile, OSError):
        print(json.dumps({"verdict": "SIGNED_HI2_CFG_AUDIT_BLOCKED",
                          "no_original_uploaded": True}))
        sys.exit(2)
