#!/usr/bin/env python3
"""Read-only signed #170gpr scheduler audit for native xx0.run process lifecycle.

Checks only who constructs/schedules the observed exit runnable. No APK patch,
signature bypass, account access, process blocking or data export.
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
from trace_native_callers import method_definitions, invoked_method_indexes, OP_WIDTH, payload_width

SCHEDULER_BODIES = frozenset((
    ("Lby0;", "a", "()V"),
    ("Lby0;", "p", "(Landroid/content/Context;)V"),
    ("Lhi2;", "j", "(Ljava/lang/Object;)Ljava/lang/Object;"),
))
EXIT_RUN = ("Lxx0;", "run", "()V")
EXPECTED_HOST_DEX = 6
MAX_SCHEDULED_METHODS = 30
INTERESTING = frozenset((
    "post", "postDelayed", "postAtTime", "execute", "submit", "schedule",
    "start", "run", "dispatch", "launch", "getMainLooper", "myLooper",
    "getPackageName", "getRunningAppProcesses", "setComponentEnabledSetting",
))


def safe_invocation(method: tuple[str, str, str], code_units: int) -> dict | None:
    """Return fixed bounded method metadata, never string or code operands."""
    meta = safe_method_meta(method)
    if meta is None:
        return None
    return {**meta, "code_units_bounded": min(code_units, 500000),
            "scheduler_api_by_name": method[1] in INTERESTING}




def constructor_mode_nearby_constant(dex, code_off: int, call_pc: int,
                                     op: int) -> dict:
    """Conservative local basic-block const witness, not global data flow.

    Only the *integer mode register* of invoke-direct(Context,int) is sampled.
    Resets knowledge on jumps / branches and unknown register overwrites.
    No string values, private fields or opcode bytes are returned.
    """
    count = dex.u32(code_off + 12)
    start = code_off + 16
    if count > 500000 or call_pc >= count or op not in (0x70, 0x76):
        return {"mode": "NOT_PROVEN", "reason": "UNSUPPORTED"}
    first = dex.u16(start + call_pc * 2)
    last = dex.u16(start + (call_pc + 2) * 2)
    if first & 255 != op:
        return {"mode": "NOT_PROVEN", "reason": "CALLSITE_MISMATCH"}
    argc = (first >> 12) if op == 0x70 else (first >> 8)
    if argc != 3:
        return {"mode": "NOT_PROVEN", "reason": "NOT_THREE_REGISTERS"}
    register = ((last >> 8) & 15) if op == 0x70 else last + 2
    recent_const = None
    pc = 0
    while pc < call_pc:
        word = dex.u16(start + pc * 2)
        opcode = word & 255
        width = (payload_width(dex, start, count, pc, word >> 8)
                 if opcode == 0 else OP_WIDTH.get(opcode))
        if width is None or width < 1 or pc + width > call_pc:
            return {"mode": "NOT_PROVEN", "reason": "INVALID_INSTRUCTION_WIDTH"}
        if opcode in tuple(range(0x28, 0x2D)) + tuple(range(0x32, 0x3E)):
            recent_const = None
        elif opcode in (0x12, 0x13, 0x14, 0x15):
            dest = (word >> 8) & 15 if opcode == 0x12 else (word >> 8)
            if dest == register:
                if opcode == 0x12:
                    val = (word >> 12) & 15
                    val = val - 16 if val >= 8 else val
                elif opcode == 0x13:
                    val = dex.u16(start + (pc + 1) * 2)
                    val = val - 65536 if val >= 32768 else val
                elif opcode == 0x14:
                    val = (dex.u16(start + (pc + 1) * 2)
                           | (dex.u16(start + (pc + 2) * 2) << 16))
                    val = val - 0x100000000 if val >= 0x80000000 else val
                else:
                    val = dex.u16(start + (pc + 1) * 2) << 16
                recent_const = val
        else:
            # Invalidate on common register writes to the mode register.
            # Unrecognised writers mean this is only a local-nearby witness.
            dest = (word >> 8) & 15 if opcode in (
                0x01, 0x04, 0x07, 0x20, 0x21, 0x23) else (word >> 8)
            if (dest == register and opcode in (
                    0x02, 0x03, 0x05, 0x06, 0x08, 0x09,
                    0x0A, 0x0B, 0x0C, 0x0D, 0x1A, 0x1B,
                    0x1C, 0x20, 0x21, 0x22, 0x23)
                or dest == register and opcode in range(0x44, 0x69)):
                recent_const = None
        pc += width
    if recent_const is None:
        return {"mode": "NOT_PROVEN", "reason": "NO_LOCAL_CONST"}
    if recent_const not in range(0, 8):
        return {"mode": "OTHER", "reason": "NEARBY_CONST_ONLY"}
    return {"mode": recent_const, "reason": "NEARBY_CONST_ONLY"}

def inspect_dex(data: bytes) -> dict:
    dex = Dex(data)
    known_targets = {i: dex.method(i) for i in range(dex.method_count)
                     if dex.method(i) in SCHEDULER_BODIES}
    xx0_ctor = {i for i in range(dex.method_count)
                if dex.method(i)[0] == "Lxx0;" and
                dex.method(i)[1] == "<init>"}
    coroutine_ctor = {i for i in range(dex.method_count)
                      if dex.method(i)[0] == "Lhi2;" and
                      dex.method(i)[1] == "<init>"}
    bodies = []
    caller_refs = []
    constructor_mode_sites = []
    coroutine_constructor_callers = []
    own_class_definitions = []
    for index in range(dex.class_count):
        pos = dex.class_offset + index * 32
        klass = dex.descriptor(dex.u32(pos))
        if klass not in ("Lxx0;", "Lby0;", "Lhi2;"):
            continue
        superclass = dex.descriptor(dex.u32(pos + 8))
        interfaces = []
        ref = dex.u32(pos + 12)
        if ref:
            count = dex.u32(ref)
            if count > 128:
                raise DexError("Unexpected interface count")
            interfaces = [dex.descriptor(dex.u16(ref + 4 + n * 2))
                          for n in range(count)]
        own_class_definitions.append({
            "class": klass, "superclass": superclass,
            "implements_runnable": "Ljava/lang/Runnable;" in interfaces,
            "implements_callable": "Ljava/util/concurrent/Callable;" in interfaces,
            "interfaces_count_bounded": min(len(interfaces), 50),
        })
    scanned = 0
    for idx, off in method_definitions(dex):
        scanned += 1
        method = dex.method(idx)
        owned = method in SCHEDULER_BODIES
        xx0_init = method[0] == "Lxx0;" and method[1] == "<init>"
        invokes = []
        relevant_incoming = []
        for invoked, pc, opcode in invoked_method_indexes(dex, off):
            callee = dex.method(invoked)
            if (owned or xx0_init) and len(invokes) < 80:
                metadata = safe_invocation(callee, pc)
                if metadata:
                    invokes.append(metadata)
            if callee in SCHEDULER_BODIES:
                relevant_incoming.append(callee)
            if invoked in coroutine_ctor and len(coroutine_constructor_callers) < 40:
                source_owner = safe_method_meta(method)
                if source_owner:
                    coroutine_constructor_callers.append({
                        "caller": source_owner,
                        "constructor_prototype": callee[2],
                        "caller_is_ymapplication": method[0] ==
                            "Lru/yandex/music/YMApplication;",
                    })
            if invoked in xx0_ctor:
                relevant_incoming.append(("Lxx0;", "<init>", "()NOT_EXACT"))
                if len(constructor_mode_sites) < 12:
                    caller = safe_method_meta(method)
                    if caller:
                        constructor_mode_sites.append({
                            "caller": caller,
                            "case": constructor_mode_nearby_constant(
                                dex, off, pc, opcode),
                            "only_local_const_not_global_dataflow": True,
                        })
        if owned or xx0_init:
            bodies.append({
                "method": safe_method_meta(method),
                "calls": invokes,
                "xx0_constructor": xx0_init,
                "body_contains_scheduler_like_method": any(
                    x["scheduler_api_by_name"] for x in invokes),
                "body_contains_xx0_constructor": any(
                    x["owner"] == "Lxx0;" and x["method"] == "<init>"
                    for x in invokes),
                "body_contains_exit_run_direct": any(
                    x["owner"] == EXIT_RUN[0] and x["method"] == EXIT_RUN[1]
                    for x in invokes),
            })
        if relevant_incoming and len(caller_refs) < 100:
            meta = safe_method_meta(method)
            if meta:
                for target in relevant_incoming[:12]:
                    if len(caller_refs) < 100:
                        caller_refs.append({
                            "invoked": list(target), "caller": meta,
                            "caller_is_ymapplication": method[0] ==
                                "Lru/yandex/music/YMApplication;",
                        })
    return {
        "signed_class_info": own_class_definitions,
        "constructor_mode_sites": constructor_mode_sites,
        "coroutine_constructor_callers": coroutine_constructor_callers,
        "signed_scheduler_bodies": bodies[:12],
        "bounded_incoming_method_refs": caller_refs[:75],
        "method_bodies_scanned_bounded": min(scanned, 500000),
        "all_bodies_returned": len(bodies) <= 12,
        "no_vendor_strings_or_invoke_registers_exposed": True,
    }


def summarize(segments: list[dict]) -> dict:
    bodies = [b for s in segments for b in s["signed_scheduler_bodies"]]
    distinct_scheduler = {(
        b["method"]["owner"], b["method"]["method"],
        b["method"]["prototype"]) for b in bodies if not b["xx0_constructor"]}
    if distinct_scheduler != SCHEDULER_BODIES:
        raise ValueError("SIGNED_SCHEDULER_BODIES_MISMATCH")
    classes = [c for s in segments for c in s["signed_class_info"]]
    callers = [r for s in segments for r in s["bounded_incoming_method_refs"]]
    unique_callers = []
    seen = set()
    for item in callers:
        key = (tuple(item["invoked"]), item["caller"]["owner"],
               item["caller"]["method"], item["caller"]["prototype"])
        if key not in seen:
            seen.add(key)
            unique_callers.append(item)
    return {
        "verdict": "SIGNED_NATIVE_EXIT_RUN_SCHEDULER_STATIC_ONLY",
        "known_runtime_exit_owner": "Lxx0;.run()V",
        "own_sched_lookups": len(distinct_scheduler),
        "direct_bodies": bodies[:12],
        "constructor_mode_site_evidence": [x for s in segments for x in s["constructor_mode_sites"]][:12],
        "passport_coroutine_constructor_callers": [
            x for s in segments for x in s["coroutine_constructor_callers"]][:40],
        "runnable_class_info": classes,
        "incoming_callers": unique_callers[:60],
        "inbound_ctor_and_scheduler_site_count_bounded": min(len(unique_callers), 100),
        "explicit_direct_run_calls_verified_elsewhere": 0,
        "vendor_signed_host_untouched": True,
        "no_strings_or_credentials_exposed": True,
        "no_runtime_causality_proven": True,
        "no_publisher_protection_bypassed": True,
        "binary_uploaded": False,
    }


def run() -> dict:
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise ValueError("SIGNED_SCHEDULE_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-a1-exit-scheduler-") as temp:
        directory = Path(temp)
        archive = directory / "original.xapk"
        size, digest = exact.gpr.download(archive)
        if size != 60433885 or digest != exact.ARCHIVE_SHA:
            raise ValueError("PINNED_SOURCE_HOST_DIGEST_CHANGED")
        parts = exact.gpr.split_apks(archive, directory)
        if len(parts) != 5:
            raise ValueError("PUBLISHER_SPLIT_COUNT_CHANGED")
        exact.gpr.inspect_publisher(parts)
        segments = []
        for apk in parts:
            with zipfile.ZipFile(apk) as z:
                for name in sorted(z.namelist()):
                    if name.startswith("classes") and name.endswith(".dex") and "/" not in name:
                        segments.append(inspect_dex(z.read(name)))
        if len(segments) != EXPECTED_HOST_DEX:
            raise ValueError("SIGNED_HOST_DEX_COUNT_CHANGED")
        result = summarize(segments)
        result["publisher_signed_dex_count"] = len(segments)
        return result


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except (ValueError, DexError, OSError, zipfile.BadZipFile) as error:
        detail = str(error)
        allowed = {"SIGNED_SCHEDULE_CI_ONLY", "PINNED_SOURCE_HOST_DIGEST_CHANGED",
                   "PUBLISHER_SPLIT_COUNT_CHANGED", "SIGNED_HOST_DEX_COUNT_CHANGED",
                   "SIGNED_SCHEDULER_BODIES_MISMATCH"}
        print(json.dumps({"verdict": "SIGNED_SCHEDULER_AUDIT_BLOCKED",
                          "reason": detail if detail in allowed else "UNKNOWN_STATIC_AUDIT_ERROR",
                          "third_party_binary_exposed": False}))
        sys.exit(2)
