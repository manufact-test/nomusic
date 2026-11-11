#!/usr/bin/env python3
"""Disposably isolate LSPatch ARMv7 NativeBridge SIGSEGV from Yandex host code.

Only GitHub's clean Android 11 x86+ARMv7 emulator. Own, permissionless host
and pinned upstream LSPatch level=0, NO modules. Never access any Yandex APK,
account, phone, browser extension or production infrastructure.
All untrusted/raw adb data stay private to the ephemeral runner.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from build_owned_loader_host import APK, PACKAGE, apk_identity, check_host, signed_sha, sdk
from clone_lspatch_loader_zero import (
    mirror_x86_loader_resource_for_arm_bridge, verify_native_loader_elf_offsets,
)
from clone_main_crash_buffer import CLONE, classify_main_crash_buffer
from recover_stored_origin_crc import rewrite_only_if_origin_crc_mismatch

OWN = "pro.celikom.armv7loaderhost"
ACTIVITY = OWN + "/pro.celikom.armv7loaderhost.MainActivity"
PATCHED_NAME = "CELIKOM-ARMv7-LOADER-ONLY-Test.apk"


def execute(args: list[str], label: str, timeout: int = 70, check: bool = True) -> str:
    """Suppress raw output on failure, including APK, emulator and app data."""
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError("PRIVATE_" + label + "_FAILED")
    return result.stdout if result.returncode == 0 else ""


def owned_emulator_gate(abi: str, bridge: str, vm_isa: str, original_pm: str) -> dict:
    abis = set(abi.strip().split(","))
    if not {"x86", "armeabi-v7a"} <= abis or "x86_64" in abis:
        raise RuntimeError("OWN_CONTROL_NOT_PINNED_X86_ARMV7")
    if not bridge.strip() or bridge.strip() in ("0", "false"):
        raise RuntimeError("OWN_CONTROL_NATIVE_BRIDGE_MISSING")
    if vm_isa.strip() != "x86":
        raise RuntimeError("OWN_CONTROL_ARM_VM_TRANSLATION_DIFFERENT")
    if "package:" in original_pm:
        raise RuntimeError("OWN_CONTROL_ORIGINAL_VENDOR_INSTALLED")
    return {"x86_and_armv7": True, "native_bridge": True,
            "arm_virtual_machine_isa_x86": True, "vendor_package_installed": False}


def build_signed_mirror(patched: Path, working: Path) -> tuple[Path, dict]:
    recovered = working / "owned-origin-recovered-unsigned.apk"
    recovery = rewrite_only_if_origin_crc_mismatch(patched, recovered)
    source = recovered if recovery["layout_repacked"] else patched
    mirrored = working / "owned-armv7-mirror-unsigned.apk"
    report = mirror_x86_loader_resource_for_arm_bridge(source, mirrored)
    aligned = working / "owned-armv7-mirror-aligned.apk"
    execute([sdk("zipalign"), "-f", "-p", "4", str(mirrored), str(aligned)],
            "OWN_MIRROR_ZIPALIGN")
    keystore = working / "owned-bridge-only.keystore"
    execute(["keytool", "-genkeypair", "-noprompt", "-storetype", "JKS",
             "-keystore", str(keystore), "-storepass", "bridge-only-lab",
             "-keypass", "bridge-only-lab", "-alias", "bridge",
             "-keyalg", "RSA", "-keysize", "2048", "-validity", "2",
             "-dname", "CN=CELIKOM Disposable Own Bridge, O=CELIKOM, C=XX"],
            "OWN_MIRROR_KEY", 60)
    execute([sdk("apksigner"), "sign", "--ks", str(keystore),
             "--ks-pass", "pass:bridge-only-lab", "--ks-key-alias", "bridge",
             "--key-pass", "pass:bridge-only-lab", "--min-sdk-version", "28",
             "--v4-signing-enabled", "false", str(aligned)],
            "OWN_MIRROR_LAB_SIGNATURE", 60)
    if apk_identity(aligned) != (OWN, "1", "") or not signed_sha(aligned):
        raise RuntimeError("OWN_MIRROR_IDENTITY_OR_SIGNER_INVALID")
    layout = verify_native_loader_elf_offsets(aligned, expected_x86_machine=40)
    if not all(v["page_aligned_4096"] for v in layout.values()):
        raise RuntimeError("OWN_MIRROR_LOADER_ALIGNMENT_INVALID")
    with zipfile.ZipFile(aligned) as z:
        cfg = json.loads(z.read("assets/lspatch/config.json"))
        if type(cfg.get("sigBypassLevel")) is not int or cfg["sigBypassLevel"] != 0:
            raise RuntimeError("OWN_CONTROL_SIGNATURE_BYPASS_FORBIDDEN")
        if [x for x in z.namelist() if x.startswith("assets/lspatch/modules/")]:
            raise RuntimeError("OWN_CONTROL_MODULE_FORBIDDEN")
    return aligned, {"source_armv7": True, "mirrored_x86_resource_is_armv7": True,
                     "signed_page_alignment": True, "signature_bypass_level": 0,
                     "third_party_module_count": 0, "origin_layout_recovered":
                     bool(recovery["layout_repacked"]), "one_apk_only": True}


def launch_owned(apk: Path, label: str, package: str = OWN) -> dict:
    """Only own APK. Main PID, actual resumed/focused activity and safe crash labels."""
    if package not in (OWN, "pro.celikom.armv7loaderhost.x86control"):
        raise RuntimeError("OWN_UNRECOGNIZED_CONTROL_PACKAGE")
    if apk_identity(apk) != (package, "1", ""):
        raise RuntimeError("OWN_CONTROL_PACKAGE_OR_VERSION_CHANGED")
    install = execute(["adb", "install", str(apk)], "OWN_" + label + "_INSTALL", 120)
    if "Success" not in install:
        raise RuntimeError("OWN_" + label + "_INSTALL_NOT_CONFIRMED")
    paths = execute(["adb", "shell", "pm", "path", package], "OWN_PM_CHECK", 30)
    if sum(x.startswith("package:") for x in paths.splitlines()) != 1:
        raise RuntimeError("OWN_INSTALL_MULTISPLIT_UNEXPECTED")
    execute(["adb", "logcat", "-c"], "OWN_CLEAN_LOGCAT", 30)
    # Nonblocking: loader failures may block am start -W for a long time.
    execute(["adb", "shell", "am", "start", "--user", "0",
             "-n", package + "/pro.celikom.armv7loaderhost.MainActivity"], "OWN_" + label + "_MAIN_LAUNCH", 45)
    time.sleep(6)
    pidtext = execute(["adb", "shell", "pidof", package], "OWN_PID", 20, check=False)
    is_alive = bool(pidtext.strip()) and all(x.isdigit() for x in pidtext.split())
    activities = execute(["adb", "shell", "dumpsys", "activity", "activities"],
                         "OWN_ACTIVITY", 25)
    windows = execute(["adb", "shell", "dumpsys", "window", "windows"],
                      "OWN_WINDOW", 25)
    resumed = any(package + "/" in row and
                  ("mResumedActivity" in row or "topResumedActivity" in row)
                  for row in activities.splitlines())
    focused = any(package + "/" in row and "mCurrentFocus" in row
                  for row in windows.splitlines())
    exit_info = execute(["adb", "shell", "dumpsys", "activity", "exit-info", package],
                        "OWN_EXIT_INFO", 30)
    crash = execute(["adb", "logcat", "-d", "-b", "crash", "-v",
                     "threadtime", "-t", "3000"], "OWN_CRASH_BUFFER", 45)
    # Existing fixed-vocabulary classifier is intentionally tied to our private
    # clone name. Normalize only this OWN lab package in local process memory.
    safe = classify_main_crash_buffer(
        exit_info.replace(package, CLONE), crash.replace(package, CLONE))
    return {"label": label, "main_alive": is_alive, "activity_resumed": resumed,
            "window_focused": focused,
            "native_signal": safe["native_main_signal"],
            "native_first_frame_group": safe["native_backtrace_first_frame_group"],
            "native_bridge_in_first_12_frames":
                "NATIVE_BRIDGE" in safe["native_backtrace_frame_groups"],
            "dlopen_seen": safe["native_link_dlopen_failed"],
            "machine_mismatch": safe["native_link_machine_mismatch"],
            "other_crash_category": safe["fatal_category"],
            "raw_pid_or_logs_published": False}


def run() -> dict:
    if os.environ.get("GITHUB_ACTIONS") != "true" or \
            os.environ.get("CELIKOM_OWN_BRIDGE_CONTROL") != "1":
        raise RuntimeError("OWN_CONTROL_DISPOSABLE_CI_ONLY")
    if PACKAGE != OWN:
        raise RuntimeError("OWN_CONTROL_OTHER_VARIANT_FORBIDDEN")
    original = execute(["adb", "shell", "pm", "path", "ru.yandex.music"],
                       "OWN_VENDOR_ABSENT_CHECK", 30, check=False)
    control_env = owned_emulator_gate(
        execute(["adb", "shell", "getprop", "ro.product.cpu.abilist"], "OWN_ABIS", 30),
        execute(["adb", "shell", "getprop", "ro.dalvik.vm.native.bridge"],
                "OWN_BRIDGE", 30),
        execute(["adb", "shell", "getprop", "ro.dalvik.vm.isa.arm"], "OWN_ISA", 30),
        original)
    check_host(APK)
    raw_control = launch_owned(APK, "BASELINE_OWN_ARMV7")
    if not raw_control["main_alive"]:
        return {"result": "OWN_BASELINE_DID_NOT_BOOT", "control": raw_control,
                "environment": control_env, "clone_or_yandex_executed": False}
    # PackageManager uninstall ONLY this disposable unprivileged OWN lab ID.
    execute(["adb", "uninstall", OWN], "OWN_BASELINE_UNINSTALL", 60)
    with tempfile.TemporaryDirectory(prefix="celikom-owned-bridge-") as dirname:
        working = Path(dirname)
        patched = Path(os.environ["RUNNER_TEMP"]) / \
                  "celikom-owned-bridge-control" / PATCHED_NAME
        if not patched.is_file():
            raise RuntimeError("OWN_PATCHED_CONTROL_ARTIFACT_MISSING")
        mirrored, mirrored_meta = build_signed_mirror(patched, working)
        mirrored_result = launch_owned(mirrored, "LSPATCH_ZERO_ARMV7_RESOURCE_MIRROR")
        verdict = (
            "OWN_HOST_AND_LSPATCH_RUN" if mirrored_result["main_alive"]
            and mirrored_result["activity_resumed"] and mirrored_result["window_focused"]
            else "OWN_LSPATCH_NATIVE_BRIDGE_FAILED" if mirrored_result["native_signal"] != "NOT_OBSERVED"
            else "OWN_LSPATCH_UI_NOT_VERIFIED")
        return {"result": verdict, "baseline": raw_control,
                "mirrored": mirrored_result, "mirror": mirrored_meta,
                "environment": control_env,
                "clone_or_yandex_executed": False,
                "no_vendor_apks_or_account_data": True,
                "native_audio_swap_tested": False,
                "owner_honor_touched": False}


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        # Do not emit subprocess, paths, stack traces, Android logs or vendor data.
        reason = str(exc)
        label = reason if re.fullmatch(r"[A-Z][A-Z0-9_]{5,95}", reason) else \
                "OWN_CONTROL_UNEXPECTED_PRIVATE_FAILURE"
        print(json.dumps({"result": "OWN_CONTROL_BLOCKED", "category": label,
                          "owner_honor_touched": False,
                          "raw_logs_published": False}), file=sys.stderr)
        sys.exit(2)
