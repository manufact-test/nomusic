"""Disposable emulator-only Android ART startup trace: bounded evidence, no raw output.

An ActivityManager profiler is asked to trace only a short-lived lab-clone
launch. The trace is never published or retained; only fixed category flags
are printed. No method/stack listing, audio, requests, accounts, APK or PIDs.
"""
from __future__ import annotations
import os
import re
import struct
import subprocess

TRACE_PATH = "/data/local/tmp/celikom-native-main-startup.trace"
MAX_TRACE_BYTES = 24 * 1024 * 1024
MAX_RECORDS = 1_000_000

# Public known method signatures verified by the signed, read-only DEX audit.
WATCH = {
    ("ru/yandex/music/YMApplication", "onCreate"): "ymapplication_oncreate",
    ("ru/yandex/music/YMApplication", "attachBaseContext"):
        "ymapplication_attachbasecontext",
    ("ru/yandex/music/main/MainScreenActivity", "onCreate"):
        "mainscreen_oncreate",
    ("ru/yandex/music/main/MainScreenActivity", "onResume"):
        "mainscreen_onresume",
    ("java/lang/IllegalStateException", "<init>"): "illegalstate_constructor",
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


def likely_default_art_trace_capacity_reached(record_count: int,
                                             record_size: int,
                                             header_offset: int) -> bool:
    """8 MiB ART default buffer signature, only a heuristic.

    AOSP ART explicitly reports data-file-overflow in the trace header.
    This secondary check catches absent/unknown overflow metadata and stops
    interpreting missing events as proof of method non-execution.
    """
    if record_count < 0 or record_size not in (9, 10, 14):
        return False
    bytes_used = record_count * record_size + max(header_offset, 32)
    return 8 * 1024 * 1024 - 256 <= bytes_used <= 8 * 1024 * 1024


def classify_art_trace(raw: bytes) -> dict:
    """Parse v1..v3 Android SLOW traces without exposing method names or data."""
    verdict = {"trace_format_verified": False, "trace_methods_section_seen": False,
               "trace_main_thread_mapped": False, "trace_records_observed": False,
               "trace_valid_record_count": 0,
               "trace_overflow_header_status": "NOT_DECLARED",
               "default_8mib_capacity_likely_reached": False,
               "negative_method_observations_unreliable": True,
               "raw_trace_exposed": False}
    for kind in KINDS:
        verdict[kind + "_entered_main"] = False
        verdict[kind + "_entered_any"] = False
        verdict[kind + "_returned_main"] = False
        verdict[kind + "_unwound_main"] = False
    verdict["illegalstate_constructor_caller_groups"] = []
    verdict["illegalstate_constructor_ancestor_groups"] = []
    verdict["illegalstate_constructor_entries_bounded"] = 0
    verdict["constructor_trace_may_start_mid_call"] = True
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
    # ART intentionally stops recording following method events once its
    # non-streaming trace buffer fills, so absence of an entry is NOT proof
    # that the method was never called (Android ART Trace::FinishTracing).
    overflow = re.search(r"(?m)^data-file-overflow=(true|false)\s*$", head)
    if overflow:
        verdict["trace_overflow_header_status"] = (
            "CONFIRMED_OVERFLOW" if overflow.group(1) == "true"
            else "NO_OVERFLOW_REPORTED")
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
        capacity_likely_full = likely_default_art_trace_capacity_reached(
            count, rec_size, offset)
        verdict["default_8mib_capacity_likely_reached"] = capacity_likely_full
        verdict["negative_method_observations_unreliable"] = (
            verdict["trace_overflow_header_status"] != "NO_OVERFLOW_REPORTED"
            or capacity_likely_full)
        stacks: dict[int, list[int]] = {}
        direct_groups = set()
        exception_caller_groups = set()
        exception_ancestor_groups = set()
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
                    if kind == "illegalstate_constructor":
                        verdict["illegalstate_constructor_entries_bounded"] = min(
                            100, verdict["illegalstate_constructor_entries_bounded"] + 1)
                        exception_caller_groups.add(
                            grouped_methods.get(stack[-1], "OTHER_OR_UNKNOWN")
                            if stack else "OTHER_OR_UNKNOWN")
                        # Allow only finite coarse family labels. The ART
                        # trace may start inside an active stack, so ancestry
                        # is a hint, not proven causal source of exceptions.
                        for ancestor in stack[-24:]:
                            exception_ancestor_groups.add(
                                grouped_methods.get(ancestor, "OTHER_OR_UNKNOWN"))
                    if kind in ("system_exit", "runtime_exit", "process_kill"):
                        count_field = kind + "_entry_count_bounded"
                        verdict[count_field] = min(100, verdict[count_field] + 1)
                        direct_groups.add(
                            grouped_methods.get(stack[-1], "OTHER_OR_UNKNOWN")
                            if stack else "OTHER_OR_UNKNOWN")
                if len(stack) < 2048:
                    stack.append(method_id)
            elif action in (1, 2):
                kind = watch.get(method_id)
                if kind and tid == main_tid:
                    verdict[kind + (
                        "_returned_main" if action == 1 else
                        "_unwound_main")] = True
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
        verdict["illegalstate_constructor_caller_groups"] = (
            sorted(exception_caller_groups)[:len(CALLER_GROUPS)])
        verdict["illegalstate_constructor_ancestor_groups"] = (
            sorted(exception_ancestor_groups)[:len(CALLER_GROUPS)])
    except (ValueError, struct.error, IndexError, OverflowError):
        verdict["trace_format_verified"] = False
        verdict["trace_valid_record_count"] = 0
        verdict["trace_records_observed"] = False
    return verdict



def classify_sampled_art_trace(raw: bytes) -> dict:
    """Never equate ART --sampling stack observations with actual calls.

    With sampling, synthetic ART ENTER/EXIT transitions approximate sampled
    stack changes. Only report fixed whitelisted observation markers and
    capacity metadata; never claim exact Java invocation, return, unwind,
    thrown exception or deliberate process exit from these transitions.
    """
    full = classify_art_trace(raw)
    named = sorted(kind for kind in KINDS
                   if full.get(kind + "_entered_any", False))
    named_main = sorted(kind for kind in KINDS
                        if full.get(kind + "_entered_main", False))
    return {
        "trace_format_verified": full["trace_format_verified"],
        "trace_records_observed": full["trace_records_observed"],
        "trace_valid_record_count": full["trace_valid_record_count"],
        "trace_main_thread_mapped": full["trace_main_thread_mapped"],
        "trace_overflow_header_status": full["trace_overflow_header_status"],
        "default_8mib_capacity_likely_reached":
            full["default_8mib_capacity_likely_reached"],
        "sampling_interval_us": 10000,
        "sampled_watch_names_any_thread": named,
        "sampled_watch_names_main_thread": named_main,
        "sampled_stacks_not_exact_method_calls": True,
        "causation_not_established": True,
        "raw_trace_exposed": False,
    }


CONTAINER = "celikom-native-arm-android13"


def should_stop_owned_profile_early(package: str, main_alive: bool,
                                    already_stopped: bool) -> bool:
    """Legacy early-stop test; no publisher-original interaction."""
    return (package == "pro.celikom.yandex.nativeclonelab"
            and bool(main_alive) and not bool(already_stopped))


def choose_owned_profile_stop_stage(package: str, *,
                                    main_alive: bool, activity_resumed: bool,
                                    live_sample_count: int, already_stopped: bool) -> str:
    """Controlled later ART flush: wait for two verified alive observations.

    Earlier first-alive flush captured the pre-onCreate stage; this alternate
    observation checks a later window. Never wait for login, account data or
    perform extra actions in the publisher-signed original.
    """
    if (package != "pro.celikom.yandex.nativeclonelab"
            or not main_alive or already_stopped):
        return "NOT_ELIGIBLE"
    if live_sample_count < 2:
        return "WAIT_FOR_SECOND_ALIVE"
    return ("SECOND_ALIVE_ACTIVITY_RESUMED" if activity_resumed
            else "SECOND_ALIVE_NO_RESUME")


def classify_profiler_launch(raw: str) -> str:
    """Android ActivityManager command response, no free-text disclosure."""
    normalized = raw.lower()
    if "unknown option" in normalized or "unknown argument" in normalized:
        return "PROFILER_OPTION_UNSUPPORTED"
    if "not profileable" in normalized or "not debuggable" in normalized:
        return "PROFILER_ACCESS_REJECTED"
    if "permission denied" in normalized or "securityexception" in normalized:
        return "PROFILER_PERMISSION_REJECTED"
    if "starting:" in normalized or "warning: activity not started" in normalized:
        return "ACTIVITY_START_COMMAND_ACCEPTED"
    return "ACTIVITY_START_UNCLASSIFIED"


def observe_disposable_trace(*, owned_arm_container: bool = False,
                             sampling_mode: bool = False):
    """Only fixed-category evidence, never an ART file, symbol, path or PID.

    ARM13 Redroid runs inside Docker; an adb binary is NOT installed on
    the GitHub ARM host. Use fixed docker-exec commands, no host file copy,
    no host trace file. Existing x86 emulators can still use the old ADB
    code path. Both paths always try to wipe the exact ephemeral trace.
    """
    report = {
        "profiler_requested": True, "trace_available": False,
        "trace_size_within_bound": False, "trace_read_error": False,
        "profiled_main_ui_unverified": True, "raw_trace_published": False,
        "trace_transport": "PRIVATE_DOCKER_EXEC" if owned_arm_container else
                           "PRIVATE_ADB",
        "trace_stat_category": "NOT_CHECKED",
    }
    if sampling_mode and (not owned_arm_container or
                          os.environ.get("CELIKOM_OWN_ART_SAMPLING_10000US") != "1"):
        report["trace_read_error"] = True
        report["trace_transport_guard_rejected"] = True
        return report
    if owned_arm_container:
        if (os.environ.get("GITHUB_ACTIONS") != "true"
                or os.environ.get("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1"
                or os.environ.get("CELIKOM_NATIVE_ARM13_OWN_CLONE_ART_TRACE") != "1"):
            report["trace_read_error"] = True
            report["trace_transport_guard_rejected"] = True
            return report
        stat_args = ["docker", "exec", CONTAINER, "stat", "-c", "%s", TRACE_PATH]
        read_args = ["docker", "exec", CONTAINER, "cat", TRACE_PATH]
        delete_args = ["docker", "exec", CONTAINER, "rm", "-f", TRACE_PATH]
    else:
        stat_args = ["adb", "shell", "stat", "-c", "%s", TRACE_PATH]
        read_args = ["adb", "exec-out", "cat", TRACE_PATH]
        delete_args = ["adb", "shell", "rm", "-f", TRACE_PATH]
    try:
        stat = subprocess.run(stat_args, capture_output=True,
                              text=True, timeout=15)
        if stat.returncode != 0:
            err = (stat.stderr or "").lower()
            report["trace_stat_category"] = (
                "FILE_ABSENT" if "no such file" in err or "not found" in err else
                "PERMISSION_DENIED" if "permission denied" in err else
                "OTHER_STAT_FAILURE")
            return report
        if not stat.stdout.strip().isdigit():
            report["trace_stat_category"] = "STAT_OUTPUT_UNRECOGNIZED"
            return report
        report["trace_stat_category"] = "SIZE_OBSERVED"
        size = int(stat.stdout.strip())
        report["trace_available"] = size > 0
        if size <= 0 or size > MAX_TRACE_BYTES:
            return report
        report["trace_size_within_bound"] = True
        data = subprocess.run(read_args, capture_output=True, timeout=45)
        if (data.returncode or len(data.stdout) > MAX_TRACE_BYTES
                or len(data.stdout) != size):
            report["trace_read_error"] = True
            return report
        report["trace_evidence"] = (
            classify_sampled_art_trace(data.stdout) if sampling_mode else
            classify_art_trace(data.stdout))
        return report
    except (subprocess.TimeoutExpired, OSError, ValueError):
        report["trace_read_error"] = True
        return report
    finally:
        try:
            subprocess.run(delete_args, capture_output=True, timeout=15)
        except (subprocess.TimeoutExpired, OSError):
            report["trace_cleanup_observation_unavailable"] = True
