#!/usr/bin/env python3
"""Privacy-limited launch diagnostics for a fresh disposable Android emulator.

The emulator contains no account, private tracks or user data. Output only
package state, names of exception *classes*, and CELIKOM lifecycle categories.
No raw logcat, stack traces, URLs, tokens, Android IDs, audio or files.
"""
from __future__ import annotations
import re
import subprocess
import time

PACKAGE = "ru.yandex.music"
TAG = "CELIKOM-NativeLab"
EXPECTED = "observer: native file-info converter hooks armed; read-only"

def adb(*args, timeout=35):
    p = subprocess.run(["adb", *args], text=True, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr

def redact_type(text):
    # Exceptions only, no exception messages, hostnames, device IDs or paths.
    types = re.findall(r"(?:java|android|dalvik|kotlin|org\.lsposed|io\.github)[\w.$/]*(?:Exception|Error)", text)
    return list(dict.fromkeys(types))[:5]

def launch():
    code, out, err = adb("shell", "pm", "path", PACKAGE)
    count = sum(line.startswith("package:") for line in out.splitlines())
    print(f"INSTALL_STATE: package_present={bool(count)} split_apks={count}")
    if code or count != 5:
        print("NO_GO: expected five patched native Yandex APK parts not installed")
        return 2

    code, out, err = adb("shell", "cmd", "package", "resolve-activity", "--brief",
                          "-a", "android.intent.action.MAIN",
                          "-c", "android.intent.category.LAUNCHER", "-p", PACKAGE)
    resolved = bool(out.strip()) and "No activity found" not in out and "Unable to resolve" not in out
    print(f"LAUNCHER_RESOLVABLE: {resolved}")

    adb("logcat", "-c")
    code, out, err = adb("shell", "am", "start", "-W",
                         "-a", "android.intent.action.MAIN",
                         "-c", "android.intent.category.LAUNCHER", "-p", PACKAGE,
                         timeout=55)
    accepted = code == 0 and "Error:" not in out and "Error:" not in err
    print(f"ACTIVITY_START_REQUEST: accepted={accepted} exit={code}")
    if not accepted:
        # Keep only error categories without exposing runtime/URL data.
        print("ACTIVITY_START_ERROR_CLASSES:", redact_type(out + "\n" + err))
        adb("shell", "monkey", "-p", PACKAGE, "-c",
            "android.intent.category.LAUNCHER", "1", timeout=30)

    states = []
    for _ in range(5):
        time.sleep(3)
        c, p, _ = adb("shell", "pidof", PACKAGE)
        states.append(bool(p.strip()) if c == 0 else False)
    print(f"APP_PROCESS_SAMPLE: {states}")

    c, logs, err = adb("logcat", "-d", "-v", "brief", timeout=50)
    if c:
        print("LOGCAT_AVAIL: false")
        return 2

    events = []
    native_crash = []
    runtime_exceptions = []
    for line in logs.splitlines():
        if TAG in line and "observer:" in line:
            if "hooks armed" in line:
                events.append("HOOKS_ARMED")
            elif "unsupported host version" in line:
                events.append("UNSUPPORTED_HOST_VERSION")
            elif "no exact converter pair" in line:
                events.append("CONVERTER_NOT_FOUND")
            elif "cannot attach" in line:
                events.append("ATTACH_HOOK_FAILED")
            elif "context unavailable" in line:
                events.append("CONTEXT_UNAVAILABLE")
            elif "module loaded" in line:
                events.append("MODULE_LOADED")
            elif "package loaded" in line:
                events.append("PACKAGE_LOADED")
            elif "file-info conversion count" in line:
                events.append("CONVERSION_WITNESSED")
        if "AndroidRuntime" in line or "FATAL EXCEPTION" in line or "Caused by:" in line:
            runtime_exceptions.extend(redact_type(line))
            if "FATAL EXCEPTION" in line:
                native_crash.append("ANDROID_RUNTIME_FATAL")
        if "Fatal signal" in line and (PACKAGE in line or "liblspatch" in line):
            native_crash.append("NATIVE_FATAL_SIGNAL")
        if "dlopen failed" in line and (PACKAGE in line or "lspatch" in line.lower()):
            native_crash.append("NATIVE_LIBRARY_LOAD_FAILURE")
    events = list(dict.fromkeys(events))
    runtime_exceptions = list(dict.fromkeys(runtime_exceptions))[:12]
    native_crash = list(dict.fromkeys(native_crash))
    print(f"OBSERVER_LIFECYCLE: {events}")
    print(f"ANDROID_EXCEPTION_TYPES: {runtime_exceptions}")
    print(f"NATIVE_CRASH_MARKERS: {native_crash}")
    if "HOOKS_ARMED" in events:
        print("PASS: native FileInfo converter observer registered in an isolated emulator; playback and Play Protect NOT tested")
        return 0
    print("NO_GO: native FileInfo converter hook NOT witnessed; process or loader investigation needed")
    return 2

if __name__ == "__main__":
    raise SystemExit(launch())
