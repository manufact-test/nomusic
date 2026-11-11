"""Read-only, privacy-safe Android 13 native app startup differential observer.

This module never modifies any APK, interacts with an account, hooks an app,
or accesses private process state. The caller may feed public ADB event/main
log buffers from a disposable guest. Output is a finite diagnostic vocabulary.
An event-log difference cannot establish a vendor security check or root cause.
"""
from __future__ import annotations

import re

from clone_main_crash_buffer import CLONE, EXIT_BLOCK, LOG, main_exit_pids

ORIGINAL = "ru.yandex.music"
PACKAGES = frozenset((CLONE, ORIGINAL))
EVENT_TAGS = (
    "am_proc_start", "am_proc_died", "am_kill", "am_crash", "am_anr",
    "am_create_activity", "am_resume_activity", "am_pause_activity",
    "am_finish_activity", "am_destroy_activity",
)
EVENT_RE = re.compile(r"\b(" + "|".join(EVENT_TAGS) + r")\s*:")
PROCESS_RE = re.compile(r"\b(?:processName|process|process name)\s*[=:]\s*"
                        r"([A-Za-z0-9_.:]+)", re.I)
PID_RE = re.compile(r"\bpid\s*[=:]\s*(\d{1,8})\b")

# A list of known, coarse signals; never share exception class names or text.
THROWABLE_CLASSES = (
    ("SECURITY", r"\bSecurityException\b|\bPermission Denial\b"),
    ("APP_STATE", r"\bIllegalStateException\b|\bIllegalArgumentException\b"),
    ("CLASS_LOADING", r"\bClassNotFoundException\b|\bNoClassDefFoundError\b"
                      r"|\bVerifyError\b|\bLinkageError\b"),
    ("NATIVE_LINK", r"\bUnsatisfiedLinkError\b|\bdlopen failed\b"),
    ("NULL_STATE", r"\bNullPointerException\b"),
    ("OTHER_THROWABLE", r"\b[A-Z][A-Za-z0-9_$]*(?:Exception|Error)\b"),
)


def _exact_package_in_line(line: str, package: str) -> bool:
    if package not in PACKAGES:
        raise ValueError("UNAPPROVED_PACKAGE")
    return re.search(
        r"(?<![A-Za-z0-9_.$])" + re.escape(package) + r"(?![A-Za-z0-9_.$:])",
        line,
    ) is not None


def classify_startup_events(raw: str, package: str) -> dict:
    """Only event tag names for exact MAIN package, not helper ':process'.

    An Android event entry can mention a package as an activity component or
    as process name. Keep bounded event order but no PIDs, timestamps, reasons,
    class names, log messages, URLs, tokens, account data or process metadata.
    """
    if package not in PACKAGES:
        raise ValueError("UNAPPROVED_PACKAGE")
    tags = []
    auxiliary_seen = False
    for line in raw.splitlines()[-9000:]:
        if package not in line:
            continue
        auxiliary_seen |= re.search(
            re.escape(package) + r":[A-Za-z0-9_.$]+", line) is not None
        if not _exact_package_in_line(line, package):
            continue
        event = EVENT_RE.search(line)
        if event and len(tags) < 32:
            tags.append(event.group(1))
    return {
        "main_event_order": tags,
        "process_start_seen": "am_proc_start" in tags,
        "process_died_seen": "am_proc_died" in tags,
        "system_kill_event_seen": "am_kill" in tags,
        "system_crash_or_anr_event_seen": any(
            t in tags for t in ("am_crash", "am_anr")),
        "activity_created_seen": "am_create_activity" in tags,
        "activity_resumed_seen": "am_resume_activity" in tags,
        "activity_finish_seen": "am_finish_activity" in tags,
        "activity_destroyed_seen": "am_destroy_activity" in tags,
        "finish_event_before_death": (
            "am_finish_activity" in tags and "am_proc_died" in tags
            and tags.index("am_finish_activity") < tags.index("am_proc_died")),
        "auxiliary_process_events_seen": auxiliary_seen,
        "raw_event_log_exposed": False,
        "causality_not_proven": True,
    }


def only_new_main_exit_info(before: str, after: str) -> tuple[str, dict]:
    """Exclude historical exact-MAIN exit records before this cold launch.

    Android may retain prior exit records across repeated trials. A stale
    PID must not attribute old crashes or error messages to the new launch.
    Unknown/reused PIDs fail closed. No raw history is returned in the report.
    The filtered string is PRIVATE and must not be printed.
    """
    old = main_exit_pids(before)
    blocks = EXIT_BLOCK.split(after[:250000])
    if len(blocks) == 1:
        blocks = after[:250000].splitlines()
    selected = []
    old_discarded = 0
    for block in blocks[:100]:
        name = PROCESS_RE.search(block)
        pid = PID_RE.search(block)
        if name is None or name.group(1) != CLONE or pid is None:
            continue
        number = int(pid.group(1))
        if number in old:
            old_discarded += 1
        elif 1 <= number <= 99999999:
            selected.append(block)
    return "\n".join(selected), {
        "new_main_exit_record_seen": bool(selected),
        "historical_main_exit_records_ignored": min(old_discarded, 100),
        "raw_exit_history_exposed": False,
    }


def classify_new_main_log_signals(filtered_exit: str, main_log: str) -> dict:
    """Read only E/F/W log lines attributed to new exact-MAIN exit-info PID.

    No raw text, exception symbol, path, URL, thread ID or credential leaves.
    Cross-process Android framework messages are intentionally not attributed.
    """
    pids = main_exit_pids(filtered_exit)
    groups = []
    fatal_seen = False
    error_seen = False
    uncaught_seen = False
    matched = 0
    for line in main_log.splitlines()[-15000:]:
        event = LOG.match(line)
        if event is None or int(event.group(1)) not in pids:
            continue
        _, severity, tag, message = event.groups()
        if severity not in ("W", "E", "F"):
            continue
        matched += 1
        if severity in ("E", "F"):
            error_seen = True
        if tag.strip() == "AndroidRuntime" and "FATAL EXCEPTION" in message:
            fatal_seen = True
        if re.search(r"\buncaughtException\b", message, re.I):
            uncaught_seen = True
        for label, pattern in THROWABLE_CLASSES:
            if re.search(pattern, message) and label not in groups:
                groups.append(label)
                break
    return {
        "new_main_exit_pid_available": bool(pids),
        "main_scoped_warning_or_error_seen": matched > 0,
        "main_scoped_error_severity_seen": error_seen,
        "android_runtime_fatal_seen": fatal_seen,
        "uncaught_handler_marker_seen": uncaught_seen,
        "throwable_groups": groups[:6],
        "main_log_lines_examined_bounded": min(matched, 500),
        "raw_main_log_exposed": False,
        "causality_not_proven": True,
    }
