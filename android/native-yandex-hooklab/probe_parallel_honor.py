#!/usr/bin/env python3
"""Read-only parallel installation preflight on the owner's HONOR 50.

DOES NOT install, uninstall, clear, launch, connect, patch, sign, read account,
query passwords, toggle permissions, or modify original Yandex / Play Protect.
It does not treat an existing app as evidence that a new clone will launch.
"""
from __future__ import annotations

import json
import sys
from probe_arm_device import _adb, collect, Snapshot

ORIGINAL = "ru.yandex.music"
CLONE = "pro.celikom.yandex.nativeclonelab"


def is_honor(s: Snapshot) -> bool:
    model = (s.model + " " + s.device).upper().replace("_", "-")
    return "HONOR 50" in model or "NTH-NX9" in model


def evaluate(s: Snapshot, clone_present: bool) -> dict:
    blockers = []
    try:
        api = int(s.api_level)
    except (TypeError, ValueError):
        api = 0
    if api < 33:
        blockers.append("ANDROID_13_OR_HIGHER_REQUIRED")
    if "armeabi-v7a" not in set(s.abis.split(",")):
        blockers.append("ARMV7_APP_ABI_UNAVAILABLE")
    if s.emulator == "1" or s.boot_emulator == "1":
        blockers.append("EMULATOR_NOT_OWNER_HONOR")
    if not is_honor(s):
        blockers.append("NOT_CONFIRMED_HONOR_50")
    if not s.yandex_installed:
        blockers.append("ORIGINAL_YANDEX_ABSENT_DO_NOT_INSTALL_RESEARCH_BUILD")
    if clone_present:
        blockers.append("PARALLEL_TEST_PACKAGE_ALREADY_PRESENT_NO_AUTOMATIC_OVERWRITE")
    if not s.play_store_installed:
        blockers.append("GOOGLE_PLAY_COMPONENT_NOT_DETECTED_PLAY_PROTECT_UNVERIFIED")
    return {
        "purpose": "READ_ONLY_OWNER_HONOR_PARALLEL_INSTALL_PRECHECK",
        "ready_for_FUTURE_manual_package_review": not blockers,
        "blockers": blockers,
        "official_yandex_still_installed": s.yandex_installed,
        "separate_clone_package_already_installed": clone_present,
        "armv7_32bit_supported": "armeabi-v7a" in set(s.abis.split(",")),
        "android_api": api,
        "play_protect": "MUST_BE_CHECKED_MANUALLY_ON_DEVICE",
        "native_clone_launch_tested": False,
        "native_audio_replacement_tested": False,
        "device_mutation": False,
        "user_login_data_read": False,
    }


def _pm_present(adb, package: str) -> bool:
    status, data = adb("shell", "pm", "path", package)
    if status != 0:
        raise RuntimeError("PACKAGE_MANAGER_QUERY_FAILED")
    if data.strip() and not all(
            line.startswith("package:") for line in data.splitlines()):
        raise RuntimeError("UNEXPECTED_PACKAGE_QUERY_FORMAT")
    return bool(data.strip())


def main() -> int:
    result = {"purpose": "READ_ONLY_OWNER_HONOR_PARALLEL_INSTALL_PRECHECK",
              "ready_for_FUTURE_manual_package_review": False,
              "blockers": ["ADB_PREFLIGHT_UNAVAILABLE"],
              "device_mutation": False}
    try:
        code, devices = _adb("devices")
        if code or sum(line.endswith("\tdevice") for line in devices.splitlines()) != 1:
            raise RuntimeError("EXACTLY_ONE_AUTHORIZED_HONOR_DEVICE_REQUIRED")
        snapshot = collect(_adb)
        # No adb commands that alter system state, install APK, open logs or read secrets.
        clone_present = _pm_present(_adb, CLONE)
        result = evaluate(snapshot, clone_present)
    except RuntimeError as exc:
        result["blockers"] = [str(exc)]
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["ready_for_FUTURE_manual_package_review"] else 2


if __name__ == "__main__":
    sys.exit(main())
