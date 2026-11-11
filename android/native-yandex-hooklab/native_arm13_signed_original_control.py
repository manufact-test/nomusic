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


CONTAINER = "celikom-native-arm-android13"


def pm_category(output):
    """Fixed Android package error category, never raw text or paths."""
    hit = re.search(r"(INSTALL_(?:FAILED|PARSE_FAILED)_[A-Z0-9_]{2,50})", output)
    if hit:
        return hit.group(1)
    for needle, category in (
        ("unknown option", "UNKNOWN_OPTION"),
        ("unknown command", "UNKNOWN_COMMAND"),
        ("permission denied", "PERMISSION_DENIED"),
        ("can't open", "GUEST_CANNOT_OPEN"),
        ("no such file", "GUEST_FILE_NOT_FOUND"),
        ("failed to stat", "GUEST_STAT_FAILED"),
        ("insufficient", "LOW_SPACE"),
        ("exception occurred", "JAVA_EXCEPTION"),
        ("failure", "GENERIC_FAILURE"),
        ("error", "GENERIC_ERROR"),
    ):
        if needle in output.lower():
            return category
    return "EMPTY_OUTPUT" if not output.strip() else "UNCLASSIFIED_OUTPUT"


def private_process(args, timeout=75):
    """Capture errors privately, without printing proprietary resources."""
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def pm_session_install(apks: list[str]) -> str:
    """Native AOSP install-create/write/commit for 5 signed split APKs.

    install-multiple belongs to the ADB *host*, not to Android shell 'pm'.
    Never spoof signatures or bypass PackageManager enforcement.
    """
    if len(apks) != 5:
        fail("ORIGINAL_PM_SESSION_MUST_HAVE_FIVE_APKS")
    uploads = []
    base_count = 0
    split_names = set()
    for i, item in enumerate(apks):
        path = Path(item)
        if not path.is_file() or path.suffix != ".apk":
            fail("ORIGINAL_SESSION_SPLIT_MISSING")
        meta = y.apkmeta(path)
        if meta.get("name") != PACKAGE or meta.get("versionCode") != "24026531":
            fail("ORIGINAL_SESSION_VENDOR_IDENTITY_CHANGED")
        name = meta.get("split", "") or "base"
        if name == "base":
            base_count += 1
        if name in split_names:
            fail("ORIGINAL_SESSION_DUPLICATE_SPLIT_NAME")
        split_names.add(name)
        guest = "/data/local/tmp/own-pinned-publisher-" + str(i) + ".apk"
        copy = private_process(["docker", "cp", str(path), CONTAINER + ":" + guest],
                               timeout=90)
        if copy.returncode:
            fail("ORIGINAL_GUEST_SPLIT_COPY_FAILED")
        uploads.append((name, guest, path.stat().st_size))
    if base_count != 1:
        fail("ORIGINAL_SESSION_NOT_ONE_BASE")
    total = sum(size for _, _, size in uploads)
    created = private_process(["docker", "exec", CONTAINER, "pm", "install-create",
                               "--user", "0", "-S", str(total)], timeout=90)
    created_raw = created.stdout + created.stderr
    match = re.search(r"Success:.*\[([0-9]{1,12})\]", created.stdout)
    if created.returncode or not match:
        return "PRIVATE_PM_SESSION_CREATE_" + pm_category(created_raw)
    session = match.group(1)
    committed = False
    try:
        for name, guest, size in uploads:
            write = private_process(["docker", "exec", CONTAINER, "pm", "install-write",
                                     "-S", str(size), session, name, guest],
                                    timeout=90)
            if write.returncode or not write.stdout.strip().startswith("Success"):
                return "PRIVATE_PM_SESSION_WRITE_" + pm_category(write.stdout + write.stderr)
        commit = private_process(["docker", "exec", CONTAINER, "pm",
                                  "install-commit", session], timeout=180)
        if commit.returncode or not commit.stdout.strip().startswith("Success"):
            return "PRIVATE_PM_SESSION_COMMIT_" + pm_category(commit.stdout + commit.stderr)
        committed = True
        return "Success"
    finally:
        if not committed:
            # Only abandon our own session; never touch installed apps.
            private_process(["docker", "exec", CONTAINER,
                             "pm", "install-abandon", session], timeout=40)


def adb(args, timeout=75, allow=False):
    """Shell inside pinned OWN CI Android only; no physical ADB device."""
    if args[0] == "install-multiple":
        return pm_session_install(args[1:])
    if args[0] != "shell":
        fail("UNSUPPORTED_ORIGINAL_GUEST_ACTION")
    p = private_process(["docker", "exec", CONTAINER, *args[1:]], timeout=timeout)
    if p.returncode and not allow:
        fail("ORIGINAL_PRIVATE_GUEST_COMMAND_FAILED")
    return p.stdout if p.returncode == 0 else ""


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
