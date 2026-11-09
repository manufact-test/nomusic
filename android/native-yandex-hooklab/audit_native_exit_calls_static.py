#!/usr/bin/env python3
"""Read-only diagnostic: explicit process termination callsites in signed original.

This does not identify a causal path or bypass any publisher control.
Only aggregate static bytecode statistics escape the disposable CI runner.
"""
from __future__ import annotations
import json
import os
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


def exit_target(method):
    return TARGETS.get(method)


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
    for caller, code_off in method_definitions(dex):
        scanned += 1
        try:
            for called, _, _ in invoked_method_indexes(dex, code_off):
                kind = method_indexes.get(called)
                if kind is None:
                    continue
                totals[kind] += 1
                klass = dex.method(caller)[0]
                if klass == YM_APPLICATION:
                    app_direct[kind] += 1
                if klass.startswith(("Lru/yandex/", "Lcom/yandex/")):
                    yandex_namespace[kind] += 1
        except DexError:
            anomalies += 1
    return {
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
        return {
            "verdict": "STATIC_EXIT_CALLSITE_EVIDENCE_ONLY",
            "original_dex_count": len(observations),
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
