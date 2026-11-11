#!/usr/bin/env python3
"""Actual OWN read-only libxposed in-process witness, Android 11 native x86.

Never contacts or installs Yandex, never tests audio replacement, never reads
credentials or writes any data except ephemeral own app installation.
"""
from __future__ import annotations
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from build_owned_loader_host import APK, PACKAGE, check_host
from own_lspatch_nativebridge_control import execute, launch_owned
from own_lspatch_x86_native_control import package_x86_loader

OWN = "pro.celikom.armv7loaderhost.x86control"
PATCHED_NAME = "CELIKOM-X86-HOOK-WITNESS-Test.apk"
RESULT = "RESULT=PASS CODE=OWN_MODULE_ACTIVITY_INTERCEPTED"

def classify_witness_log(content: str) -> dict:
    """Only enum evidence, never prints raw log lines."""
    passed = RESULT in content
    failed = "RESULT=FAIL CODE=OWN_MODULE_ACTIVITY_INTERCEPTED" in content
    return {"module_activity_intercepted": passed,
            "witness_marker_received": passed or failed,
            "witness_result": "PASS" if passed else "FAIL" if failed else "NOT_OBSERVED",
            "raw_log_exported": False}

def main() -> dict:
    if os.environ.get("GITHUB_ACTIONS") != "true" or \
            os.environ.get("CELIKOM_OWN_X86_WITNESS") != "1" or \
            os.environ.get("CELIKOM_OWN_X86_WITNESS_RUNTIME") != "1" or PACKAGE != OWN:
        raise RuntimeError("X86_WITNESS_EPHEMERAL_CI_ONLY")
    abis = execute(["adb", "shell", "getprop", "ro.product.cpu.abilist"],
                   "X86_WITNESS_ABI").strip().split(",")
    if "x86" not in abis or "x86_64" in abis:
        raise RuntimeError("X86_WITNESS_WRONG_EMULATOR")
    if "package:" in execute(["adb", "shell", "pm", "path", "ru.yandex.music"],
                            "X86_WITNESS_YANDEX_ABSENT", check=False):
        raise RuntimeError("X86_WITNESS_VENDOR_PACKAGE_PRESENT")
    check_host(APK)
    patched = Path(os.environ["RUNNER_TEMP"]) / "celikom-own-x86-witness" / PATCHED_NAME
    if not patched.is_file():
        raise RuntimeError("X86_WITNESS_PATCHER_ARTIFACT_MISSING")
    with tempfile.TemporaryDirectory(prefix="celikom-own-x86-module-") as dirname:
        normalized, metadata = package_x86_loader(
            patched, Path(dirname), expect_own_module=True)
        result = launch_owned(normalized, "X86_OWN_HOOK_WITNESS", package=OWN)
        # This is only the app's own fixed-format witness message. Raw log
        # lines are never printed or persisted, as with the existing crash gate.
        lines = execute(["adb", "logcat", "-d", "-s",
                         "CelikomOwnHookWitness:I", "*:S"],
                        "X86_OWN_READONLY_WITNESS_LOG", 35)
        marker = classify_witness_log(lines)
        actual_pass = (
            result["main_alive"] and result["activity_resumed"]
            and marker["module_activity_intercepted"])
        return {"result": "OWN_X86_NATIVE_LIBXPOSED_HOOK_ENTERED" if actual_pass
                else "OWN_X86_NATIVE_MODULE_WITNESS_NOT_VERIFIED",
                "native_app": result, "module": marker,
                "metadata": metadata,
                "native_audio_swap_tested": False, "vendor_package_installed": False,
                "owner_phone_touched": False, "play_protect_tested": False}

if __name__ == "__main__":
    try:
        outcome = main()
        print(json.dumps(outcome, sort_keys=True))
        if outcome["result"] != "OWN_X86_NATIVE_LIBXPOSED_HOOK_ENTERED":
            sys.exit(2)
    except Exception as exc:
        reason = str(exc)
        reason = reason if re.fullmatch(r"[A-Z][A-Z0-9_]{5,95}", reason) else \
                 "X86_WITNESS_PRIVATE_ERROR"
        print(json.dumps({"result":"OWN_X86_NATIVE_MODULE_WITNESS_BLOCKED",
                          "reason": reason, "owner_phone_touched":False}),
              file=sys.stderr)
        sys.exit(2)
