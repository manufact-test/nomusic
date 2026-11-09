#!/usr/bin/env python3
"""CI-only: verify unmodified publisher-signed 5-split Yandex host on clean ARM emulator.

NEVER patch, inject, log accounts, authenticate, upload APKs, or touch owner HONOR.
This tests an original clean Yandex app launch only; no native CELIKOM audio test.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import clone_native_splits_ephemeral as gate


class Blocked(Exception):
    pass


def cmd(argv, name, timeout=120):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise Blocked(name + "_FAILED")
    return p.stdout


def main():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise Blocked("CI_ONLY")
    abi = cmd(["adb", "shell", "getprop", "ro.product.cpu.abilist"],
              "EMULATOR_ABI", 25).strip()
    if not ("arm64-v8a" in abi or "armeabi-v7a" in abi):
        raise Blocked("NO_ARM_EMULATOR_ABI")
    with tempfile.TemporaryDirectory(prefix="celikom-original-emulator-") as dirname:
        work = Path(dirname)
        archive = work / "pinned-original.xapk"
        size, sha256 = gate.gpr.download(archive)
        if size != 60433885 or sha256 != gate.ARCHIVE_SHA:
            raise Blocked("ORIGINAL_ARCHIVE_PIN_MISMATCH")
        apks = gate.gpr.split_apks(archive, work)
        if len(apks) != 5:
            raise Blocked("ORIGINAL_SPLIT_COUNT_DRIFT")
        gate.gpr.inspect_publisher(apks)
        original_names = set()
        for apk in apks:
            meta = gate.apkmeta(apk)
            if meta.get("name") != gate.SOURCE or meta.get("versionCode") != "24026531":
                raise Blocked("ORIGINAL_SPLIT_METADATA_DRIFT")
            original_names.add(meta.get("split", ""))
        if len(original_names) != 5:
            raise Blocked("ORIGINAL_SPLIT_SET_DRIFT")
        # Only original, publisher-signed APKs; clean emulator with no owner account.
        # Installation is confined to the ephemeral emulator, not HONOR or a real user.
        cmd(["adb", "install-multiple", *[str(x) for x in apks]],
            "ORIGINAL_ARM_INSTALL", 240)
        installed = cmd(["adb", "shell", "pm", "path", gate.SOURCE],
                        "ORIGINAL_PM_PATH", 35)
        installed_count = len([line for line in installed.splitlines()
                               if line.startswith("package:")])
        if installed_count != 5:
            raise Blocked("EMULATOR_SPLIT_SET_INCOMPLETE")
        # Do not sign in or play music. Confirm only native host initialization.
        cmd(["adb", "shell", "monkey", "-p", gate.SOURCE,
             "-c", "android.intent.category.LAUNCHER", "1"],
            "ORIGINAL_LAUNCH_INTENT", 40)
        import time
        time.sleep(5)
        process = cmd(["adb", "shell", "pidof", gate.SOURCE],
                      "ORIGINAL_PROCESS_CHECK", 30).strip()
        if not process:
            raise Blocked("ORIGINAL_PROCESS_NOT_RUNNING")
        output = {
            "verdict": "ORIGINAL_NATIVE_YANDEX_ARM_EMULATOR_LAUNCH_PASS_NOT_AUDIO",
            "emulator_abi": abi,
            "original_signed_splits_installed": installed_count,
            "original_publisher_verified": True,
            "native_yandex_process_running": True,
            "local_honor_touched": False,
            "clone_created": False,
            "patched_yandex_tested": False,
            "auth_tested": False,
            "fileinfo_hook_tested": False,
            "audio_tested": False,
            "play_protect_tested": False,
            "third_party_apks_published": False
        }
    return output


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True))
    except Exception as exc:
        stage = str(exc) if isinstance(exc, Blocked) else "EMULATOR_"+type(exc).__name__.upper()+"_BLOCKED"
        print(json.dumps({"verdict":"ORIGINAL_ARM_EMULATOR_BLOCKED", "stage":stage,
                          "third_party_apks_published":False, "owner_phone_touched":False}))
        sys.exit(2)
