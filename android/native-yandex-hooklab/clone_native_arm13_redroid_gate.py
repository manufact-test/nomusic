#!/usr/bin/env python3
"""Private true ARM Android13 A/B for a separately signed native Yandex clone.

The original publisher-signed 5 APKs remain byte-identical. The one-APK clone
uses own disposable lab signer and upstream LSPatch sigbypass=0, module_count=0.
No Passport/DRM/signature circumvention, credentials, audio, device, release APK,
or persistent third-party artifact. NEVER use the owner's HONOR.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import zipfile
from pathlib import Path

import clone_native_splits_ephemeral as source
from clone_main_crash_buffer import classify_main_crash_buffer, classify_main_exit_status
from native_arm13_signed_original_control import (
    adb, check_guest_container, pm_category, private_process
)

CONTAINER = "celikom-native-arm-android13"
CLONE = source.DEST
ORIGINAL = source.SOURCE
MAIN_CLASS = "ru.yandex.music.main.MainScreenActivity"


def fail(name: str):
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{6,96}", name):
        raise ValueError("NATIVE_ARM13_PRIVATE_GATE_FAILURE")
    raise ValueError(name)


def require_native_arm() -> dict:
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1"
            or os.environ.get("CELIKOM_NATIVE_ARM13_REDDROID_CLONE") != "1"
            or os.environ.get("CELIKOM_MANIFEST_ONLY_ORIGINAL_DEX") != "1"
            or os.environ.get("CELIKOM_OMIT_SHADOWED_SIGNATURE_DECLS") != "1"
            or os.environ.get("CELIKOM_MERGE_PARALLEL_SINGLE_APK") != "1"
            or os.environ.get("CELIKOM_CLONE_FIRST_AB") != "1"
            or os.environ.get("CELIKOM_ORIGINAL_CONTROL_LAUNCH") != "1"
            or os.environ.get("CELIKOM_LAB_CLONE_PROFILEABLE_SHELL") == "1"
            or os.environ.get("CELIKOM_BRIDGE_X86_RESOURCE_ARMV7") == "1"
            or os.uname().machine != "aarch64"):
        fail("NATIVE_ARM13_CLONE_CI_MODE_UNAUTHORIZED")
    check_guest_container()
    sdk = adb(["shell", "getprop", "ro.build.version.sdk"]).strip()
    boot = adb(["shell", "getprop", "sys.boot_completed"]).strip()
    abis = set(adb(["shell", "getprop", "ro.product.cpu.abilist"]).strip().split(","))
    native_bridge = adb(["shell", "getprop", "ro.dalvik.vm.native.bridge"]).strip()
    if boot != "1" or sdk != "33" or \
            not {"arm64-v8a", "armeabi-v7a"} <= abis or {"x86", "x86_64"} & abis:
        fail("NATIVE_ARM13_CLONE_ENVIRONMENT_UNSUPPORTED")
    if native_bridge and native_bridge not in ("0", "false"):
        fail("NATIVE_ARM13_CLONE_NATIVEBRIDGE_MUST_BE_ABSENT")
    for package in (ORIGINAL, CLONE):
        if adb(["shell", "pm", "path", package], allow=True).strip():
            fail("NATIVE_ARM13_CLONE_GUEST_MUST_START_EMPTY")
    return {"native_arm_linux": True, "android13": True,
            "32bit_armv7_enabled": True, "cpu_translation": False,
            "no_other_device": True, "owner_honor_touched": False}


def verify_lab_clone(apk: Path, signer: str, loader_zero: bool) -> None:
    if not apk.is_file():
        fail("NATIVE_ARM13_CLONE_APK_MISSING")
    meta = source.apkmeta(apk)
    if (meta.get("name") != CLONE or meta.get("versionCode") != "24026531"
            or meta.get("split")):
        fail("NATIVE_ARM13_CLONE_SINGLE_PACKAGE_IDENTITY_CHANGED")
    if not re.fullmatch(r"[0-9a-f]{64}", signer) or signer == source.RUSTORE_SHA256_CERT:
        fail("NATIVE_ARM13_CLONE_SIGNER_NOT_INDEPENDENT")
    with zipfile.ZipFile(apk) as z:
        names = set(z.namelist())
        lspatch_config = "assets/lspatch/config.json"
        if loader_zero:
            if lspatch_config not in names:
                fail("NATIVE_ARM13_CLONE_NO_LSPATCH_CONFIG")
            config = json.loads(z.read(lspatch_config))
            if type(config.get("sigBypassLevel")) is not int or \
                    config["sigBypassLevel"] != 0:
                fail("NATIVE_ARM13_CLONE_SIGBYPASS_PROHIBITED")
            if any(x.startswith("assets/lspatch/modules/") for x in names):
                fail("NATIVE_ARM13_CLONE_MODULES_MUST_BE_ZERO")
        elif lspatch_config in names:
            fail("NATIVE_ARM13_CLONE_UNEXPECTED_LOADER")
    # The clone is already signed and structurally validated by existing
    # clone_native_identity_phase2_ephemeral.py + pinned upstream wrapper.
    # No ZIP rewriting, DEX modification or new signer here.


def install_own_one_apk(apk: Path):
    guest = "/data/local/tmp/celikom-standalone-private-native-clone.apk"
    copied = private_process(["docker", "cp", str(apk), CONTAINER + ":" + guest], 90)
    if copied.returncode:
        fail("NATIVE_ARM13_PRIVATE_CLONE_COPY_FAILED")
    result = private_process(["docker", "exec", CONTAINER, "pm",
                              "install", "--user", "0", guest], 120)
    if result.returncode or not result.stdout.strip().startswith("Success"):
        code = pm_category(result.stdout + result.stderr)
        fail("NATIVE_ARM13_PRIVATE_CLONE_PM_" + code)
    installed = adb(["shell", "pm", "path", CLONE])
    if sum(x.startswith("package:") for x in installed.splitlines()) != 1:
        fail("NATIVE_ARM13_CLONE_SINGLE_INSTALLED_APK_NOT_FOUND")


def snapshot(package: str) -> dict:
    if package not in (CLONE, ORIGINAL):
        fail("NATIVE_ARM13_SNAPSHOT_UNAPPROVED_PACKAGE")
    pid = adb(["shell", "pidof", package], allow=True).strip()
    alive = bool(pid) and all(x.isdigit() for x in pid.split())
    activities = adb(["shell", "dumpsys", "activity", "activities"], timeout=35)
    window = adb(["shell", "dumpsys", "window", "windows"], timeout=35)
    resumed = any(package + "/" in x and
                  ("mResumedActivity" in x or "topResumedActivity" in x)
                  for x in activities.splitlines())
    focused = any(package + "/" in x and
                  ("mCurrentFocus" in x or "mFocusedApp" in x)
                  for x in window.splitlines())
    return {"main_alive": alive, "activity_resumed": resumed,
            "window_focus": focused, "raw_pid_or_window_logged": False}


def start(package: str) -> tuple[dict, dict]:
    """Launch a genuine guest MAIN and sample its lifecycle at bounded intervals.

    Only report enum categories from ActivityExitInfo & scoped crash buffer.
    No log line, component class, account content, PID or file retained.
    """
    adb(["shell", "logcat", "-c"])
    launch = adb(["shell", "am", "start", "--user", "0",
                  "-n", package + "/" + MAIN_CLASS], timeout=60, allow=True)
    observations = []
    for delay in (0.25, 0.75, 1.5, 4.0):
        time.sleep(delay)
        observations.append(snapshot(package))
    status = observations[-1]
    status["process_temporarily_alive"] = any(x["main_alive"] for x in observations)
    status["activity_temporarily_resumed"] = any(x["activity_resumed"] for x in observations)
    status["launch_intent_accepted"] = ("Starting:" in launch
                                        or "Warning: Activity not started" in launch)
    exit_info = adb(["shell", "dumpsys", "activity", "exit-info", package],
                    timeout=35, allow=True)
    safe_exit = classify_main_exit_status(exit_info) if package == CLONE else {
        "latest_main_exit_reason": "NOT_APPLICABLE",
        "latest_main_exit_status": "NOT_APPLICABLE",
        "exact_main_exit_record_seen": False,
        "raw_exit_info_exposed": False}
    if status["main_alive"] and status["activity_resumed"]:
        return status, {**safe_exit, "fatal_category": "NOT_OBSERVED",
                        "signal": "NOT_OBSERVED", "java_dlopen_failed": False,
                        "original_crash_buffer_dumped": False}
    buffer = adb(["shell", "logcat", "-d", "-b", "crash",
                  "-v", "threadtime", "-t", "3000"],
                 timeout=45, allow=True)
    safe = classify_main_crash_buffer(exit_info, buffer) if package == CLONE else {}
    return status, {**safe_exit,
                    "fatal_category": safe.get("fatal_category", "NOT_ATTRIBUTED"),
                    "signal": safe.get("native_main_signal", "NOT_ATTRIBUTED"),
                    "native_first_frame_group": safe.get(
                        "native_backtrace_first_frame_group", "NOT_OBSERVED"),
                    "java_dlopen_failed": safe.get("native_link_dlopen_failed", False),
                    "application_component_factory_failure": safe.get(
                        "application_component_factory_failure", False),
                    "application_create_failure": safe.get(
                        "application_create_failure", False),
                    "original_crash_buffer_dumped": False}

def test_independent_clone_and_original(clone: Path, original_splits: list[Path],
                                        signer: str, loader_zero: bool,
                                        direct_clone: Path | None = None) -> dict:
    env = require_native_arm()
    if not loader_zero:
        fail("NATIVE_ARM13_CLONE_LSPATCH_ZERO_REQUIRED")
    verify_lab_clone(clone, signer, loader_zero)
    if len(original_splits) != 5:
        fail("NATIVE_ARM13_ORIGINAL_CONTROL_FIVE_SPLITS_REQUIRED")
    # Match identical signed host DEX/native payload with and without
    # the upstream LSPatch loader. Run each only in a clean ephemeral CI app
    # state and never rewrite the original publisher-signed five APKs.
    if direct_clone is None:
        fail("NATIVE_ARM13_DIRECT_CLONE_CONTROL_REQUIRED")
    verify_lab_clone(direct_clone, signer, loader_zero=False)
    install_own_one_apk(direct_clone)
    direct_alone, direct_exit = start(CLONE)
    uninstall = private_process(
        ["docker", "exec", CONTAINER, "pm", "uninstall", "--user", "0", CLONE],
        timeout=95)
    if uninstall.returncode or "Success" not in uninstall.stdout:
        fail("NATIVE_ARM13_DIRECT_CLONE_CLEAN_UNINSTALL_REQUIRED")
    if adb(["shell", "pm", "path", CLONE], allow=True).strip():
        fail("NATIVE_ARM13_DIRECT_CLONE_NOT_REMOVED")
    install_own_one_apk(clone)
    clone_alone, clone_crash = start(CLONE)

    # Independently and originally signed Yandex source, untouched: verify
    # all 5 issuer certs/version upstream before this test helper is invoked.
    original_install = adb(["install-multiple", *[str(x) for x in original_splits]],
                           timeout=240, allow=True)
    if original_install != "Success":
        fail("NATIVE_ARM13_ORIGINAL_SIGNED_CONTROL_" +
             (original_install[:60] if original_install.startswith("PRIVATE_PM_")
              else "INSTALL_FAILURE"))
    original_packages = adb(["shell", "pm", "path", ORIGINAL], timeout=35)
    if sum(x.startswith("package:") for x in original_packages.splitlines()) != 5:
        fail("NATIVE_ARM13_ORIGINAL_SIGNED_SPLIT_COUNT_CHANGED")
    original_main, original_crash = start(ORIGINAL)
    clone_after = snapshot(CLONE)
    result = ("NATIVE_ARM13_CLONE_MAIN_LIFECYCLE_AND_ORIGINAL_COEXIST"
              if clone_alone["main_alive"] and clone_alone["activity_resumed"]
              and original_main["main_alive"] and original_main["activity_resumed"]
              and clone_after["main_alive"]
              else "NATIVE_ARM13_CLONE_MAIN_OR_COEXISTENCE_NO_GO")
    report = {"result": result, "runtime": env,
              "direct_clone_before_original": direct_alone,
              "direct_clone_exit_category": direct_exit,
              "lspatch_zero_clone_before_original": clone_alone,
              "clone_before_original": clone_alone,
              "clone_crash_category": clone_crash,
              "original_publisher_signed_five_splits": True,
              "original_main": original_main, "original_crash_category": original_crash,
              "clone_after_original": clone_after,
              "one_independent_lab_clone_apk": True,
              "sigBypassLevel": 0, "lspatch_modules_embedded": 0,
              "vendor_original_bytes_modified": False,
              "login_or_passport_tested": False,
              "audio_or_decoder_tested": False,
              "play_protect_tested": False,
              "vendor_binary_or_cloned_apk_artifact_uploaded": False,
              "owner_phone_touched": False}
    print(json.dumps({"native_arm13_clone_runtime_comparison": report}, sort_keys=True))
    if result != "NATIVE_ARM13_CLONE_MAIN_LIFECYCLE_AND_ORIGINAL_COEXIST":
        fail("NATIVE_ARM13_CLONE_MAIN_OR_COEXISTENCE_NO_GO")
    return report
