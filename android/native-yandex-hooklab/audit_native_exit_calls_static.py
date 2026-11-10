#!/usr/bin/env python3
"""Read-only diagnostic: explicit process termination callsites in signed original.

This does not identify a causal path or bypass any publisher control.
Only bounded public DEX class/method identifiers and aggregate counts escape CI;
no binary, stack trace, account, URL, key or user data.
"""
from __future__ import annotations
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools" / "android-native-gate1"))
import clone_native_splits_ephemeral as exact
from inspect_android_host import Dex, DexError
from trace_native_callers import invoked_method_indexes, method_definitions

TARGETS = {
    ("Ljava/lang/System;", "exit", "(I)V"): "system_exit",
    ("Ljava/lang/Runtime;", "exit", "(I)V"): "runtime_exit",
    ("Ljava/lang/Runtime;", "halt", "(I)V"): "runtime_halt",
    ("Landroid/os/Process;", "killProcess", "(I)V"): "android_kill_process",
}
YM_APPLICATION = "Lru/yandex/music/YMApplication;"
UNCAUGHT_HANDLER_CLASS = "Lck7;"
UNCAUGHT_HANDLER_INTERFACE = "Ljava/lang/Thread$UncaughtExceptionHandler;"
EXCEPTION_HANDLER_SETTERS = {
    ("Ljava/lang/Thread;", "setDefaultUncaughtExceptionHandler",
     "(Ljava/lang/Thread$UncaughtExceptionHandler;)V"): "default",
    ("Ljava/lang/Thread;", "setUncaughtExceptionHandler",
     "(Ljava/lang/Thread$UncaughtExceptionHandler;)V"): "per_thread",
}


def exit_target(method):
    return TARGETS.get(method)


def safe_method_meta(method):
    """Allow only bounded compiled public class/method tokens; no literals."""
    clazz, name, proto = method
    if (len(clazz) > 150 or len(name) > 64 or len(proto) > 150 or
            not re.fullmatch(r"L[A-Za-z0-9_/$]+;", clazz) or
            not re.fullmatch(r"(?:[A-Za-z0-9_$]+|<init>|<clinit>)", name) or
            not re.fullmatch(r"[A-Za-z0-9_/$;()[\]]+", proto)):
        return None
    return {"owner": clazz, "method": name, "prototype": proto}


def classify_uncaught_handler_definition(dex):
    """Only public DEX inheritance metadata; no app code or literals exported."""
    for i in range(dex.class_count):
        class_off = dex.class_offset + i * 32
        if dex.descriptor(dex.u32(class_off)) != UNCAUGHT_HANDLER_CLASS:
            continue
        superclass = dex.descriptor(dex.u32(class_off + 8))
        interfaces_offset = dex.u32(class_off + 12)
        interfaces = []
        if interfaces_offset:
            n = dex.u32(interfaces_offset)
            if n > 100:
                raise DexError("Unexpected handler interface count")
            dex.bounds(interfaces_offset + 4, n * 2)
            interfaces = [
                dex.descriptor(dex.u16(interfaces_offset + 4 + k * 2))
                for k in range(n)
            ]
        return {
            "class_defined": True,
            "implements_uncaught_handler": UNCAUGHT_HANDLER_INTERFACE in interfaces,
            "superclass_object": superclass == "Ljava/lang/Object;",
            "superclass_is_uncaught_handler": superclass == UNCAUGHT_HANDLER_INTERFACE,
        }
    return {"class_defined": False, "implements_uncaught_handler": False,
            "superclass_object": False, "superclass_is_uncaught_handler": False}



def immediate_int_before_exit(dex, code_off, pc, opcode):
    """Prove ONLY adjacent single-register literal at callsite; no value flow.

    An instruction-boundary walk prevents treating a multicodeunit operand as
    a fake preceding const. A nonadjacent or dynamic value is NOT_PROVEN.
    """
    from trace_native_callers import OP_WIDTH, payload_width
    if opcode not in (0x71, 0x77):
        return "NOT_PROVEN"
    count = dex.u32(code_off + 12)
    if count > 3_000_000 or pc >= count:
        raise DexError("Invalid DEX exit-call code unit offset")
    start = code_off + 16
    first = dex.u16(start + pc * 2)
    if first & 0xff != opcode:
        raise DexError("Exit-call opcode not aligned")
    arg_count = (first >> 12) if opcode == 0x71 else (first >> 8)
    if arg_count != 1:
        return "NOT_PROVEN"
    last = dex.u16(start + (pc + 2) * 2)
    register = (last & 0xF) if opcode == 0x71 else last
    cur = 0
    previous = None
    while cur < pc:
        word = dex.u16(start + cur * 2)
        op = word & 0xff
        width = payload_width(dex, start, count, cur, word >> 8) if op == 0 else OP_WIDTH.get(op)
        if width is None or cur + width > pc:
            raise DexError("Invalid instruction boundary before exit call")
        previous = (cur, width, op, word)
        cur += width
    if previous is None:
        return "NOT_PROVEN"
    pos, width, op, word = previous
    literal = None
    if op == 0x12 and width == 1 and ((word >> 8) & 0xF) == register:
        nibble = (word >> 12) & 0xF
        literal = nibble - 16 if nibble >= 8 else nibble
    elif op in (0x13, 0x15) and width == 2 and (word >> 8) == register:
        n = dex.u16(start + (pos + 1) * 2)
        literal = n - 65536 if n >= 32768 else n
        if op == 0x15:
            literal <<= 16
    elif op == 0x14 and width == 3 and (word >> 8) == register:
        lo = dex.u16(start + (pos + 1) * 2)
        hi = dex.u16(start + (pos + 2) * 2)
        n = lo | hi << 16
        literal = n - (1 << 32) if n & (1 << 31) else n
    if literal is None:
        return "NOT_PROVEN"
    return "IMMEDIATE_CONST_ZERO" if literal == 0 else "IMMEDIATE_CONST_NONZERO"


def inspect_dex(raw):
    dex = Dex(raw)
    method_indexes = {
        i: exit_target(dex.method(i)) for i in range(dex.method_count)
        if exit_target(dex.method(i)) is not None
    }
    totals = {name: 0 for name in TARGETS.values()}
    app_direct = {name: 0 for name in TARGETS.values()}
    yandex_namespace = {name: 0 for name in TARGETS.values()}
    anomalies = 0
    scanned = 0
    bounded_callers = []
    app_invoke_targets = []
    installer_invocations = []
    uncaught_handler_invoke_order = []
    handler_definition = classify_uncaught_handler_definition(dex)
    for caller, code_off in method_definitions(dex):
        scanned += 1
        caller_method = dex.method(caller)
        try:
            for called, pc, opcode in invoked_method_indexes(dex, code_off):
                called_method = dex.method(called)
                if (caller_method[0] == UNCAUGHT_HANDLER_CLASS and
                        caller_method[1] == "uncaughtException"):
                    safe_target = safe_method_meta(called_method)
                    if safe_target and len(uncaught_handler_invoke_order) < 80:
                        uncaught_handler_invoke_order.append(safe_target)
                setter = EXCEPTION_HANDLER_SETTERS.get(called_method)
                if setter is not None:
                    meta = safe_method_meta(caller_method)
                    if meta and len(installer_invocations) < 20:
                        installer_invocations.append({"setter": setter, **meta})
                if caller_method[0] == YM_APPLICATION:
                    # Keep direct-invoke method IDENTITY only in memory, not output.
                    app_invoke_targets.append(dex.method(called))
                kind = method_indexes.get(called)
                if kind is None:
                    continue
                totals[kind] += 1
                klass = caller_method[0]
                if klass == YM_APPLICATION:
                    app_direct[kind] += 1
                if klass.startswith(("Lru/yandex/", "Lcom/yandex/")):
                    yandex_namespace[kind] += 1
                meta = safe_method_meta(caller_method)
                if meta and len(bounded_callers) < 24:
                    evidence = immediate_int_before_exit(dex, code_off, pc, opcode)
                    bounded_callers.append({
                        "exit_api": kind,
                        "immediate_integer_argument_evidence": evidence,
                        **meta
                    })
        except DexError:
            anomalies += 1
    return {
        "bounded_callers": bounded_callers,
        "handler_definition": handler_definition,
        "uncaught_handler_invoke_order": uncaught_handler_invoke_order,
        "uncaught_handler_install_sites": installer_invocations,
        "ym_application_invoke_targets": app_invoke_targets,
        "exit_target_references": len(method_indexes),
        "method_bodies_scanned": scanned,
        "known_exit_callsites": totals,
        "direct_ymapplication_callsites": app_direct,
        "yandex_namespace_callsites": yandex_namespace,
        "methods_not_fully_decoded": anomalies,
        "bytecode_scan_complete": anomalies == 0,
        "sensitive_content_exposed": False,
    }


def run():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-static-exit-") as temp:
        folder = Path(temp)
        archive = folder / "signed-original.xapk"
        size, digest = exact.gpr.download(archive)
        if size != 60433885 or digest != exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_ARCHIVE_PIN_CHANGED")
        apks = exact.gpr.split_apks(archive, folder)
        if len(apks) != 5:
            raise ValueError("SIGNED_SPLIT_SET_CHANGED")
        exact.gpr.inspect_publisher(apks)
        observations = []
        for apk in apks:
            with zipfile.ZipFile(apk) as source_zip:
                for name in sorted(source_zip.namelist()):
                    if not (name.startswith("classes") and name.endswith(".dex") and "/" not in name):
                        continue
                    observations.append(inspect_dex(source_zip.read(name)))
        if len(observations) != 6:
            raise ValueError("SIGNED_DEX_COUNT_DRIFT")
        caller_details = [c for d in observations for c in d["bounded_callers"]]
        if len(caller_details) > 24:
            raise ValueError("UNEXPECTED_MANY_EXIT_CALLSITES")
        app_calls = {tuple(x) for d in observations
                     for x in d["ym_application_invoke_targets"]}
        direct_ymapp_neighbors = [c for c in caller_details
                                  if (c["owner"], c["method"], c["prototype"]) in app_calls]
        definitions = [d["handler_definition"] for d in observations
                       if d["handler_definition"]["class_defined"]]
        installers = [i for d in observations
                      for i in d["uncaught_handler_install_sites"]]
        handler_invocations = [i for d in observations
                               for i in d["uncaught_handler_invoke_order"]]
        return {
            "verdict": "STATIC_EXIT_CALLSITE_EVIDENCE_ONLY",
            "uncaught_exit_handler_definitions": definitions,
            "uncaught_handler_bounded_call_order": handler_invocations[:80],
            "uncaught_handler_install_sites": installers[:20],
            "uncaught_handler_install_sites_total": len(installers),
            "original_dex_count": len(observations),
            "bounded_explicit_exit_callsite_owners": caller_details,
            "ymapplication_directly_invokes_exit_callers": direct_ymapp_neighbors,
            "signed_original_only": True,
            "scan_complete": all(d["bytecode_scan_complete"] for d in observations),
            "known_exit_callsites": {kind: sum(d["known_exit_callsites"][kind] for d in observations)
                                     for kind in TARGETS.values()},
            "direct_ymapplication_callsites": {kind: sum(d["direct_ymapplication_callsites"][kind] for d in observations)
                                               for kind in TARGETS.values()},
            "yandex_namespace_callsites": {kind: sum(d["yandex_namespace_callsites"][kind] for d in observations)
                                           for kind in TARGETS.values()},
            "undecodable_methods": sum(d["methods_not_fully_decoded"] for d in observations),
            "important": "Static callsites alone cannot attribute REASON_EXIT_SELF to a specific runtime caller.",
            "apk_or_keys_published": False,
            "owner_phone_touched": False,
            "login_or_audio_tested": False,
        }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"verdict": "STATIC_EXIT_CALLSITE_BLOCKED",
                          "error_type": type(exc).__name__, "apk_or_keys_published": False}))
        sys.exit(2)
