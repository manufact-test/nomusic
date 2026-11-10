#!/usr/bin/env python3
"""Privacy-limited launch diagnostics for a fresh disposable Android emulator.

The emulator contains no account, private tracks or user data. Output only
package state, names of exception *classes*, and CELIKOM lifecycle categories.
No raw logcat, stack traces, URLs, tokens, Android IDs, audio or files.
"""
from __future__ import annotations
import re
import sys
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

def observer_event_category(line: str) -> str | None:
    """Redacted event-type decoder. Never return raw metadata, IDs or log lines."""
    if TAG not in line or "observer:" not in line:
        return None
    if "native file-info converter hooks armed" in line:
        return "HOOKS_ARMED"
    if "unsupported host version" in line:
        return "UNSUPPORTED_HOST_VERSION"
    if "no exact converter pair" in line:
        return "CONVERTER_NOT_FOUND"
    if "cannot attach" in line:
        return "ATTACH_HOOK_FAILED"
    if "context unavailable" in line:
        return "CONTEXT_UNAVAILABLE"
    if "module loaded" in line:
        return "MODULE_LOADED"
    if "package loaded" in line:
        return "PACKAGE_LOADED"
    if "platform metadata witness armed" in line:
        return "METADATA_HOOK_ARMED"
    if "metadata update count" in line:
        return "METADATA_WITNESSED"
    if "file-info conversion count" in line:
        return "CONVERSION_WITNESSED"
    if "temporal-only aggregate" in line:
        return "TEMPORAL_ORDER_AGGREGATE"
    return None


def launch(original_baseline: bool = False, patched_without_module: bool = False):
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
    library_basename_candidates = []
    loader_failure_categories = []
    for line in logs.splitlines():
        event = observer_event_category(line)
        if event is not None:
            events.append(event)
        if "AndroidRuntime" in line or "FATAL EXCEPTION" in line or "Caused by:" in line:
            runtime_exceptions.extend(redact_type(line))
            if "FATAL EXCEPTION" in line:
                native_crash.append("ANDROID_RUNTIME_FATAL")
        if "Fatal signal" in line and (PACKAGE in line or "liblspatch" in line):
            native_crash.append("NATIVE_FATAL_SIGNAL")
        # Only names like libname.so, not full linker messages or paths.
        if ("dlopen failed" in line or "UnsatisfiedLinkError" in line
                or "couldn't find" in line.lower() or "linker" in line.lower()):
            for basename in re.findall(r"lib[A-Za-z0-9_.+-]{1,90}\.so", line):
                if len(library_basename_candidates) < 24:
                    library_basename_candidates.append(basename)
            lower = line.lower()
            if "dlopen failed" in lower:
                loader_failure_categories.append("DLOPEN_FAILED")
            if "wrong elf" in lower or "elfclass" in lower:
                loader_failure_categories.append("WRONG_ELF_CLASS")
            if "not found" in lower or "couldn't find" in lower:
                loader_failure_categories.append("LIBRARY_NOT_FOUND")
            if "is 64-bit" in lower or "is 32-bit" in lower:
                loader_failure_categories.append("ABI_WIDTH_CONFLICT")
            if "namespace" in lower:
                loader_failure_categories.append("NATIVE_LINKER_NAMESPACE")
        if "dlopen failed" in line and (PACKAGE in line or "lspatch" in line.lower()):
            native_crash.append("NATIVE_LIBRARY_LOAD_FAILURE")
    events = list(dict.fromkeys(events))
    runtime_exceptions = list(dict.fromkeys(runtime_exceptions))[:12]
    native_crash = list(dict.fromkeys(native_crash))
    print(f"OBSERVER_LIFECYCLE: {events}")
    print(f"ANDROID_EXCEPTION_TYPES: {runtime_exceptions}")
    print(f"NATIVE_CRASH_MARKERS: {native_crash}")
    print(f"NATIVE_LOADER_LIBRARIES: {list(dict.fromkeys(library_basename_candidates))[:20]}")
    print(f"NATIVE_LOADER_REASONS: {list(dict.fromkeys(loader_failure_categories))[:10]}")
    if original_baseline:
        if states[-1] and states[-2]:
            print("PASS: untouched publisher-signed native Yandex stays running in isolated Android 11; no account, playback or Play Protect verdict")
            return 0
        print("BASELINE_NO_GO: ORIGINAL, UNMODIFIED Yandex did not remain alive; do not blame CELIKOM injection yet")
        return 2
    if patched_without_module:
        if states[-1] and states[-2]:
            print("PASS: LSPatch-modified native Yandex stays running WITHOUT any CELIKOM module; no audio, login or Play Protect verdict")
            return 0
        print("PATCHER_NO_MODULE_NO_GO: LSPatch native host does not remain running even without a CELIKOM module")
        return 2
    if "HOOKS_ARMED" in events:
        print("PASS: native FileInfo converter observer registered in an isolated emulator; playback and Play Protect NOT tested")
        return 0
    print("NO_GO: native FileInfo converter hook NOT witnessed; process or loader investigation needed")
    return 2

if __name__ == "__main__":
    raise SystemExit(launch(original_baseline="--original-baseline" in sys.argv,
                            patched_without_module="--patched-without-module" in sys.argv))
