#!/usr/bin/env python3
"""Ephemeral genuine ARM Android13 publisher-signed Yandex original control.

No account, no third-party APK artifact, no modification or LSPatch. Validate
all pinned five splits and issuer signature before any install. Owner phone
is NEVER contacted.
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import clone_native_splits_ephemeral as y

PACKAGE = "ru.yandex.music"


def fail(stage):
    raise ValueError(stage)


def adb(args, timeout=75, allow=False):
    """Execute ONLY in pinned disposable container; never talk to an ADB device."""
    if args[0] == "shell":
        command = ["docker", "exec", "celikom-native-arm-android13", *args[1:]]
    elif args[0] == "install-multiple":
        guest = []
        for index, path in enumerate(args[1:]):
            pathname = Path(path)
            if not pathname.is_file() or pathname.suffix != ".apk" or index >= 5:
                fail("ORIGINAL_UNVERIFIED_LOCAL_SPLIT_FILE")
            guest_path = "/data/local/tmp/celikom-signed-original-" + str(index) + ".apk"
            copied = subprocess.run(
                ["docker", "cp", str(pathname),
                 "celikom-native-arm-android13:" + guest_path],
                capture_output=True, text=True, timeout=90)
            if copied.returncode:
                fail("ORIGINAL_PRIVATE_GUEST_COPY_FAILED")
            guest.append(guest_path)
        command = ["docker", "exec", "celikom-native-arm-android13",
                   "pm", "install-multiple", "--user", "0", *guest]
    else:
        fail("UNSUPPORTED_ORIGINAL_GUEST_ACTION")
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode and args[0] == "install-multiple":
        # Only fixed PackageManager failure codes; no exception text/paths/URLs.
        private = result.stdout + result.stderr
        match = re.search(r"\\b(INSTALL_(?:FAILED|PARSE_FAILED)_[A-Z0-9_]{2,50})\\b",
                          private)
        return ("PRIVATE_PM_" + match.group(1)) if match else "PRIVATE_PM_OTHER_ERROR"
    if result.returncode and not allow:
        fail("ORIGINAL_PRIVATE_GUEST_COMMAND_FAILED")
    return result.stdout if result.returncode == 0 else ""


def check_guest_container():
    if os.getenv("GITHUB_ACTIONS") != "true" or os.uname().machine != "aarch64":
        fail("EPHEMERAL_ARM_HOST_CI_ONLY")
    p = subprocess.run(["docker", "inspect", "celikom-native-arm-android13",
                        "--format", "{{.State.Running}}"],
                       capture_output=True, text=True, timeout=20)
    if p.returncode or p.stdout.strip() != "true":
        fail("NATIVE_ARM_REDDROID_CONTAINER_NOT_RUNNING")



def run():
    check_guest_container()
    if adb(["shell", "getprop", "sys.boot_completed"]).strip() != "1":
        fail("NATIVE_ARM_ANDROID_BOOT_INCOMPLETE")
    sdk = adb(["shell", "getprop", "ro.build.version.sdk"]).strip()
    abi = set(adb(["shell", "getprop", "ro.product.cpu.abilist"]).strip().split(","))
    if sdk != "33" or not {"arm64-v8a", "armeabi-v7a"} <= abi or "x86" in abi:
        fail("NATIVE_ARM13_ARMV7_ABI_REQUIRED")
    if adb(["shell", "pm", "path", PACKAGE], allow=True).strip():
        fail("NATIVE_ARM_GUEST_NOT_EMPTY")
    play_services = bool(adb(["shell", "pm", "path", "com.google.android.gms"],
                             allow=True).strip())
    with tempfile.TemporaryDirectory(prefix="celikom-arm13-original-signed-") as folder:
        work = Path(folder)
        xapk = work / "signed.xapk"
        nbytes, sha = y.gpr.download(xapk)
        if nbytes != 60433885 or sha != y.ARCHIVE_SHA:
            fail("ORIGINAL_PINNED_XAPK_SHA_DRIFT")
        signed = y.gpr.split_apks(xapk, work)
        if len(signed) != 5:
            fail("ORIGINAL_SPLIT_COUNT_INVALID")
        with contextlib.redirect_stdout(io.StringIO()):
            y.gpr.inspect_publisher(signed)
        installed_result = adb(["install-multiple", *[str(x) for x in signed]],
                               timeout=200, allow=True)
        if "Success" not in installed_result:
            # Emit only fixed PackageManager code, not raw vendor logs or args.
            if installed_result.startswith("PRIVATE_PM_"):
                fail(installed_result[:95])
            fail("PUBLISHER_SIGNED_ORIGINAL_INSTALL_FAILED")
        paths = adb(["shell", "pm", "path", PACKAGE])
        count = sum(x.startswith("package:") for x in paths.splitlines())
        if count != 5:
            fail("PUBLISHER_SPLITS_NOT_ALL_INSTALLED")
        adb(["shell", "logcat", "-c"])
        start = adb(["shell", "am", "start", "-n",
                     PACKAGE + "/ru.yandex.music.main.MainScreenActivity"],
                    allow=True)
        time.sleep(8)
        main = adb(["shell", "pidof", PACKAGE], allow=True).strip()
        alive = bool(main) and all(x.isdigit() for x in main.split())
        activity = adb(["shell", "dumpsys", "activity", "activities"])
        window = adb(["shell", "dumpsys", "window", "windows"])
        resumed = any(PACKAGE + "/" in x and
                      ("mResumedActivity" in x or "topResumedActivity" in x)
                      for x in activity.splitlines())
        focused = any(PACKAGE + "/" in x and
                      ("mCurrentFocus" in x or "mFocusedApp" in x)
                      for x in window.splitlines())
        return {
            "result": "ORIGINAL_SIGNED_NATIVE_ARM13_MAIN_ALIVE" if alive and resumed
                      else "ORIGINAL_SIGNED_NATIVE_ARM13_MAIN_NOT_VERIFIED",
            "pinned_yandex_issuer_and_version_verified": True,
            "signed_original_five_splits": count,
            "original_code_modified": False, "lspatch_loaded": False,
            "main_alive": alive, "activity_resumed": resumed,
            "window_focused": focused, "launch_intent_accepted": "Starting:" in start,
            "android13_native_armv7": True,
            "google_play_services_present": play_services,
            "login_tested": False, "audio_tested": False,
            "play_protect_tested": False, "clone_tested": False,
            "publisher_apk_published": False, "owner_honor_touched": False,
        }


if __name__ == "__main__":
    try:
        verdict = run()
        print(json.dumps(verdict, sort_keys=True))
        if verdict["result"] != "ORIGINAL_SIGNED_NATIVE_ARM13_MAIN_ALIVE":
            sys.exit(2)
    except Exception as e:
        reason = str(e) if re.fullmatch(r"[A-Z][A-Z0-9_]{5,95}", str(e)) else \
                 "ORIGINAL_SIGNED_ARM13_PRIVATE_CONTROL_ERROR"
        print(json.dumps({"result": "ORIGINAL_NATIVE_ARM13_CONTROL_BLOCKED",
                          "reason": reason, "owner_honor_touched": False,
                          "publisher_apk_published": False}), file=sys.stderr)
        sys.exit(2)
