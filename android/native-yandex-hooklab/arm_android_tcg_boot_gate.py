#!/usr/bin/env python3
"""No-APK ARM Android emulator TCG boot gate on GitHub macOS ARM runner.

Does not install APK, open proprietary apps, access accounts, or connect to a
phone. Host ARM64 macOS and guest Android AArch64 are checked independently.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys

class GateError(Exception):
    pass

def classify(host_machine: str, boot: str, is_emulator: str,
             isa: str, abis: str, abis32: str, sdk: str) -> dict:
    if host_machine not in {"arm64", "aarch64"}:
        raise GateError("MACOS_RUNNER_NOT_NATIVE_ARM64")
    if boot.strip() != "1":
        raise GateError("GUEST_ANDROID_NOT_BOOTED")
    if is_emulator.strip() != "1":
        raise GateError("GUEST_NOT_DISPOSABLE_EMULATOR")
    if isa.strip() not in {"aarch64", "arm64"}:
        raise GateError("GUEST_KERNEL_NOT_NATIVE_AARCH64")
    if sdk.strip() != "30":
        raise GateError("UNEXPECTED_ANDROID_API")
    abi = set(filter(None, abis.strip().split(",")))
    abi32 = set(filter(None, abis32.strip().split(",")))
    if "arm64-v8a" not in abi or abi.intersection({"x86", "x86_64"}):
        raise GateError("GUEST_ANDROID_ABI_NOT_NATIVE_ARM64")
    return {"result": "ANDROID_NATIVE_ARM64_TCG_BOOT_CONFIRMED",
            "host_arm64": True, "guest_kernel_aarch64": True,
            "guest_android_api": 30, "virtual_device": True,
            "armv7_32bit_userspace": "armeabi-v7a" in abi32,
            "ready_for_armv7_owned_loader": "armeabi-v7a" in abi32,
            "owner_phone_touched": False,
            "apk_installed": False, "vendor_code_accessed": False,
            "account_or_audio_tested": False}

def prop(name: str) -> str:
    if name not in {"sys.boot_completed", "ro.kernel.qemu", "ro.product.cpu.abilist",
                    "ro.product.cpu.abilist32", "ro.build.version.sdk"}:
        raise GateError("UNAPPROVED_DEVICE_PROPERTY")
    p = subprocess.run(["adb", "shell", "getprop", name],
                       capture_output=True, text=True, timeout=25)
    if p.returncode:
        raise GateError("ADB_PROPERTY_UNAVAILABLE")
    return p.stdout.strip()

def main() -> dict:
    if os.environ.get("GITHUB_ACTIONS") != "true" or \
            os.environ.get("ANDROID_I_WANT_MY_TCG") != "yes":
        raise GateError("CI_SOFTWARE_EMULATOR_ONLY")
    guest_uname = subprocess.run(["adb", "shell", "uname", "-m"],
                                 capture_output=True, text=True, timeout=25)
    if guest_uname.returncode:
        raise GateError("ADB_ANDROID_UNAME_UNAVAILABLE")
    return classify(platform.machine(), prop("sys.boot_completed"),
                    prop("ro.kernel.qemu"), guest_uname.stdout,
                    prop("ro.product.cpu.abilist"),
                    prop("ro.product.cpu.abilist32"), prop("ro.build.version.sdk"))

if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True))
    except (GateError, subprocess.TimeoutExpired) as exc:
        reason = str(exc) if isinstance(exc, GateError) else "ADB_PROBE_TIMEOUT"
        print(json.dumps({"result": "NATIVE_ARM_ANDROID_TCG_BOOT_NOT_VERIFIED",
                          "category": reason,
                          "owner_phone_touched": False, "apk_installed": False}),
              file=sys.stderr)
        sys.exit(2)
