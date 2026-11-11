"""Disposable emulator-only Android ART startup trace: bounded evidence, no raw output.

An ActivityManager profiler is asked to trace only a short-lived lab-clone
launch. The trace is never published or retained; only fixed category flags
are printed. No method/stack listing, audio, requests, accounts, APK or PIDs.
"""
from __future__ import annotations
import re
import struct
import subprocess

TRACE_PATH = "/data/local/tmp/celikom-native-main-startup.trace"
MAX_TRACE_BYTES = 24 * 1024 * 1024
MAX_RECORDS = 1_000_000

# Public known method signatures verified by the signed, read-only DEX audit.
WATCH = {
    ("ru/yandex/music/YMApplication", "onCreate"): "ymapplication_oncreate",
    ("ck7", "uncaughtException"): "uncaught_handler",
    ("java/lang/System", "exit"): "system_exit",
    ("java/lang/Runtime", "exit"): "runtime_exit",
    ("android/os/Process", "killProcess"): "process_kill",
    ("java/lang/Thread", "setDefaultUncaughtExceptionHandler"): "handler_install",
}
KINDS = sorted(set(WATCH.values()))
CALLER_GROUPS = ("YANDEX_MUSIC", "YANDEX_PASSPORT", "APP_METRICA",
                 "ANDROID_RUNTIME", "LSPATCH", "OTHER_OR_UNKNOWN")


def _safe_caller_group(klass: str) -> str:
    """Only a fixed category leaves; no raw method/class names."""
    if klass.startswith(("ru/yandex/music/", "com/yandex/music/")):
        return "YANDEX_MUSIC"
    if klass.startswith(("com/yandex/passport/", "ru/yandex/passport/")):
        return "YANDEX_PASSPORT"
    if klass.startswith(("com/yandex/metrica/", "io/appmetrica/")):
        return "APP_METRICA"
    if klass.startswith(("android/", "java/", "javax/", "dalvik/", "kotlin/")):
        return "ANDROID_RUNTIME"
    if klass.startswith("org/lsposed/lspatch/"):
        return "LSPATCH"
    return "OTHER_OR_UNKNOWN"


def classify_art_trace(raw: bytes) -> dict:
    """Parse v1..v3 Android SLOW traces without exposing method names or data."""
    verdict = {"trace_format_verified": False, "trace_methods_section_seen": False,
               "trace_main_thread_mapped": False, "trace_records_observed": False,
               "trace_valid_record_count": 0,
               "raw_trace_exposed": False}
    for kind in KINDS:
        verdict[kind + "_entered_main"] = False
        verdict[kind + "_entered_any"] = False
    verdict["direct_exit_caller_groups"] = []
    verdict["system_exit_entry_count_bounded"] = 0
    verdict["runtime_exit_entry_count_bounded"] = 0
    verdict["process_kill_entry_count_bounded"] = 0
    verdict["stack_tracking_available"] = False
    if len(raw) > MAX_TRACE_BYTES or not raw.startswith(b"*version\n"):
        return verdict
    marker = b"*end\n"
    end = raw.find(marker, 0, min(len(raw), 2_000_000))
    if end < 0:
        return verdict
    head = raw[:end].decode("utf-8", errors="replace")
    if "*threads\n" not in head or "*methods\n" not in head:
        return verdict
    verdict["trace_methods_section_seen"] = True
    try:
        threads = head.split("*threads\n", 1)[1].split("*methods\n", 1)[0]
        main_tid = None
        for line in threads.splitlines():
            m = re.fullmatch(r"\s*(\d+)\s+main\s*", line)
            if m:
                main_tid = int(m.group(1))
                break
        verdict["trace_main_thread_mapped"] = main_tid is not None
        entries = head.split("*methods\n", 1)[1].splitlines()
        watch = {}
        grouped_methods = {}
        for line in entries[:350000]:
            parts = line.split()
            if len(parts) < 3 or not re.fullmatch(r"0x[0-9a-fA-F]{1,16}", parts[0]):
                continue
            klass = parts[1].removeprefix("L").removesuffix(";").replace(".", "/")
            method = parts[2]
            method_id = int(parts[0], 16) & ~3
            grouped_methods[method_id] = _safe_caller_group(klass)
            kind = WATCH.get((klass, method))
            if kind is not None:
                watch[method_id] = kind
        body = raw[end + len(marker):]
        if len(body) < 18 or body[:4] != b"SLOW":
            return verdict
        version, offset = struct.unpack_from("<HH", body, 4)
        if version not in (1, 2, 3) or offset < 16 or offset > 1024:
            return verdict
        if version == 1:
            rec_size = 9
        elif version == 2:
            rec_size = 10
        else:
            rec_size = struct.unpack_from("<H", body, 16)[0]
            if rec_size not in (10, 14):
                return verdict
        if offset > len(body):
            return verdict
        count = min((len(body) - offset) // rec_size, MAX_RECORDS)
        verdict["trace_format_verified"] = True
        verdict["trace_valid_record_count"] = count
        verdict["trace_records_observed"] = count > 0
        stacks: dict[int, list[int]] = {}
        direct_groups = set()
        for i in range(count):
            off = offset + i * rec_size
            if version == 1:
                tid = body[off]
                mid = struct.unpack_from("<I", body, off + 1)[0]
            else:
                tid = struct.unpack_from("<H", body, off)[0]
                mid = struct.unpack_from("<I", body, off + 2)[0]
            action, method_id = mid & 3, mid & ~3
            stack = stacks.setdefault(tid, [])
            if action == 0:
                kind = watch.get(method_id)
                if kind:
                    verdict[kind + "_entered_any"] = True
                    if tid == main_tid:
                        verdict[kind + "_entered_main"] = True
                    if kind in ("system_exit", "runtime_exit", "process_kill"):
                        count_field = kind + "_entry_count_bounded"
                        verdict[count_field] = min(100, verdict[count_field] + 1)
                        direct_groups.add(
                            grouped_methods.get(stack[-1], "OTHER_OR_UNKNOWN")
                            if stack else "OTHER_OR_UNKNOWN")
                if len(stack) < 2048:
                    stack.append(method_id)
            elif action in (1, 2):
                # Traces can start mid-call. Never invent a caller when stack
                # is missing or unbalanced.
                if stack and stack[-1] == method_id:
                    stack.pop()
                elif method_id in stack:
                    del stack[stack.index(method_id):]
                else:
                    stack.clear()
        verdict["stack_tracking_available"] = bool(grouped_methods) and count > 0
        verdict["direct_exit_caller_groups"] = sorted(direct_groups)[:len(CALLER_GROUPS)]
    except (ValueError, struct.error, IndexError, OverflowError):
        verdict["trace_format_verified"] = False
        verdict["trace_valid_record_count"] = 0
        verdict["trace_records_observed"] = False
    return verdict


def observe_disposable_trace():
    """Only called on a clean emulator from a gated GitHub Actions job."""
    report = {
        "profiler_requested": True, "trace_available": False,
        "trace_size_within_bound": False, "trace_read_error": False,
        "profiled_main_ui_unverified": True, "raw_trace_published": False,
    }
    try:
        stat = subprocess.run(
            ["adb", "shell", "stat", "-c", "%s", TRACE_PATH],
            capture_output=True, text=True, timeout=15)
        if stat.returncode != 0 or not stat.stdout.strip().isdigit():
            return report
        size = int(stat.stdout.strip())
        report["trace_available"] = size > 0
        if size <= 0 or size > MAX_TRACE_BYTES:
            return report
        report["trace_size_within_bound"] = True
        p = subprocess.run(
            ["adb", "exec-out", "cat", TRACE_PATH],
            capture_output=True, timeout=45)
        if p.returncode or len(p.stdout) > MAX_TRACE_BYTES or len(p.stdout) != size:
            report["trace_read_error"] = True
            return report
        report["trace_evidence"] = classify_art_trace(p.stdout)
        return report
    except (subprocess.TimeoutExpired, OSError, ValueError):
        report["trace_read_error"] = True
        return report
    finally:
        subprocess.run(
            ["adb", "shell", "rm", "-f", TRACE_PATH],
            capture_output=True, timeout=15)
