#!/usr/bin/env python3
"""Read-only device suitability gate for the isolated CELIKOM native Yandex lab.

Never installs/uninstalls/launches APKs, enables adb root, reads logs, or inspects
private app data. Deliberately refuses the owner's known HONOR 50 and devices
with an existing official Yandex installation. Play Protect requires an actual
on-device manual verification and is NEVER inferred from an installed Play Store.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable

TARGET = "ru.yandex.music"
PLAY_STORE = "com.android.vending"


@dataclass(frozen=True)
class Snapshot:
    api_level: str
    abis: str
    emulator: str
    boot_emulator: str
    model: str
    device: str
    yandex_installed: bool
    play_store_installed: bool


def _shell(adb: Callable[..., tuple[int, str]], *args: str) -> str:
    code, output = adb("shell", *args)
    if code:
        raise RuntimeError("READ_ONLY_ADB_COMMAND_FAILED")
    return output.strip()


def collect(adb: Callable[..., tuple[int, str]]) -> Snapshot:
    # All commands are intentionally read-only: no mount, pm install, am start,
    # Play Protect configuration, root, logcat, or secret-bearing app probes.
    def prop(name: str) -> str:
        return _shell(adb, "getprop", name)

    def present(package: str) -> bool:
        output = _shell(adb, "pm", "path", package)
        if output and not all(line.startswith("package:") for line in output.splitlines()):
            raise RuntimeError("PACKAGE_QUERY_INDETERMINATE")
        return bool(output)

    return Snapshot(
        api_level=prop("ro.build.version.sdk"),
        abis=prop("ro.product.cpu.abilist"),
        emulator=prop("ro.kernel.qemu"),
        boot_emulator=prop("ro.boot.qemu"),
        model=prop("ro.product.model"),
        device=prop("ro.product.device"),
        yandex_installed=present(TARGET),
        play_store_installed=present(PLAY_STORE),
    )


def evaluate(s: Snapshot) -> dict:
    issues = []
    try:
        api = int(s.api_level)
    except (ValueError, TypeError):
        api = None
        issues.append("UNKNOWN_ANDROID_API")
    if api is not None and api < 33:
        issues.append("REQUIRES_ANDROID_13_PLUS")

    abis = {x.strip().lower() for x in s.abis.split(",") if x.strip()}
    if "armeabi-v7a" not in abis:
        issues.append("NO_ARMV7_32BIT_APP_SUPPORT")
    if "arm64-v8a" not in abis and "armeabi-v7a" not in abis:
        issues.append("NOT_NATIVE_ARM")
    if s.emulator == "1" or s.boot_emulator == "1":
        issues.append("EMULATOR_NOT_PHYSICAL_DEVICE")

    # Never target the known owner primary HONOR 50, even if the original app
    # was previously uninstalled. This is a guard, not proof of another phone.
    identity = (s.model + " " + s.device).upper().replace("_", "-")
    if "NTH-NX9" in identity or "HONOR 50" in identity:
        issues.append("OWNER_PRIMARY_MODEL_BLOCKED")
    if s.yandex_installed:
        issues.append("YANDEX_ALREADY_INSTALLED_NO_OVERWRITE")
    if not s.play_store_installed:
        issues.append("GOOGLE_PLAY_MISSING_PROTECTION_UNVERIFIABLE")

    return {
        "purpose": "READ_ONLY_SPARE_ARM_DEVICE_ELIGIBILITY",
        "android_api": api,
        "has_required_armv7_app_abi": "armeabi-v7a" in abis,
        "google_play_package_present": s.play_store_installed,
        "yandex_package_already_present": s.yandex_installed,
        "blocked": bool(issues),
        "blockers": issues,
        "play_protect": "UNVERIFIED_ON_DEVICE_MANUAL_CHECK_REQUIRED",
        "physical_spare_device": "NOT_ATTESTED_BY_ADB",
        "installation_performed": False,
        "source_replacement_tested": False,
        "next_gate": "HUMAN_CONFIRM_SPARE_DEVICE_AND_PLAY_PROTECT_ON",
    }


def _adb(*args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(["adb", *args], text=True, capture_output=True, timeout=15,
                           check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("ADB_UNAVAILABLE_OR_TIMED_OUT") from exc
    return p.returncode, p.stdout


def main() -> int:
    try:
        code, devices = _adb("devices")
        if code != 0 or sum(line.endswith("\tdevice") for line in devices.splitlines()) != 1:
            raise RuntimeError("REQUIRE_EXACTLY_ONE_AUTHORIZED_SPARE_ADB_DEVICE")
        result = evaluate(collect(_adb))
    except RuntimeError as exc:
        result = {
            "purpose": "READ_ONLY_SPARE_ARM_DEVICE_ELIGIBILITY",
            "blocked": True,
            "blockers": [str(exc)],
            "play_protect": "UNVERIFIED_ON_DEVICE_MANUAL_CHECK_REQUIRED",
            "installation_performed": False,
        }
    # No serial number, device fingerprint, full package list, credentials or
    # file paths appear in stdout, including error cases.
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if result["blocked"] else 0


if __name__ == "__main__":
    sys.exit(main())
