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
# logcat -v brief: "I/am_proc_start( 1234): [...]"; some tests and
# Android formats use "I am_proc_start: [...]" instead. Both are tags.
EVENT_RE = re.compile(r"\b(" + "|".join(EVENT_TAGS) +
                      r")(?:\s*\(\s*\d{1,8}\s*\))?\s*:")
PROCESS_RE = re.compile(r"\b(?:processName|process|process name)\s*[=:]\s*"
                        r"([A-Za-z0-9_.:]+)", re.I)
PID_RE = re.compile(r"\bpid\s*[=:]\s*(\d{1,8})\b")

# A list of known, coarse signals; never share exception class names or text.
THROWABLE_CLASSES = (
    ("SECURITY", r"\bSecurityException\b|\bPermission Denial\b"),
    ("ILLEGAL_STATE", r"\bIllegalStateException\b"),
    ("ILLEGAL_ARGUMENT", r"\bIllegalArgumentException\b"),
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


# Public Android EventLogTags specify process name field positions.
# AOSP am_proc_start: [User,PID,UID,ProcessName,Type,Component]
# AOSP am_proc_died / am_kill / am_crash: [User,PID,ProcessName,...]
# Match by the *process name*, never another occurrence of package in the
# component / hosting field (helpers share the same package in that field).
PROCESS_FIELD_POSITION = {
    "am_proc_start": 3, "am_proc_died": 2,
    "am_kill": 2, "am_crash": 2,
}
# am_anr contains a package field, not an exact process identity: skip it
# rather than misattribute a helper ANR to the MAIN process.
ACTIVITY_TAGS = frozenset({
    "am_create_activity", "am_resume_activity", "am_pause_activity",
    "am_finish_activity", "am_destroy_activity",
})


def _event_fields(line: str) -> list[str]:
    """Private bounded Android -v brief '[...]' fields; never returned."""
    left, right = line.find("["), line.rfind("]")
    if left < 0 or right <= left or right - left > 4000:
        return []
    return [x.strip() for x in line[left + 1:right].split(",", 10)]


def classify_startup_events(raw: str, package: str) -> dict:
    """Read-only finite lifecycle events scoped to exact MAIN process.

    A full package name anywhere in a line is NOT sufficient. App process
    creation/death must use AOSP structured ProcessName fields; an Activity
    event must contain an exact package/component. This avoids treating a
    :helper process with a package-name hosting field as MAIN.

    Only fixed event tags, booleans and bounded counts leave this module.
    """
    if package not in PACKAGES:
        raise ValueError("UNAPPROVED_PACKAGE")
    tags = []
    auxiliary_seen = False
    seen_exact_token = False
    recognized_unscoped = False
    skipped_ambiguous = 0
    lines = raw.splitlines()[-9000:]
    for line in lines:
        marker = EVENT_RE.search(line[:180])
        if marker is None:
            continue
        recognized_unscoped = True
        fields = _event_fields(line)
        if not fields:
            continue
        tag = marker.group(1)
        # Auxiliary processes may be mentioned without a main-process entry.
        auxiliary_seen |= any(
            x.startswith(package + ":") and bool(x[len(package) + 1:])
            for x in fields[:6]
        )
        seen_exact_token |= any(x == package or x.startswith(package + "/")
                                for x in fields[:6])
        is_main = False
        if tag in PROCESS_FIELD_POSITION:
            index = PROCESS_FIELD_POSITION[tag]
            is_main = len(fields) > index and fields[index] == package
        elif tag in ACTIVITY_TAGS:
            # ActivityManager on some Android versions has TaskID,
            # older variants don't. Activity component starts package+"/".
            is_main = any(
                x.startswith(package + "/") and len(x) > len(package) + 1
                for x in fields[2:7]
            )
        else:
            skipped_ambiguous += 1
        if is_main and len(tags) < 32:
            tags.append(tag)
    return {
        "main_event_order": tags,
        "buffer_entry_count_bounded": min(len(lines), 9000),
        "known_event_tag_seen_any_package": recognized_unscoped,
        "exact_main_package_token_seen": seen_exact_token,
        "ambiguous_event_count_bounded": min(skipped_ambiguous, 100),
        "strict_aosp_process_field_scoping": True,
        "process_start_seen": "am_proc_start" in tags,
        "process_died_seen": "am_proc_died" in tags,
        "system_kill_event_seen": "am_kill" in tags,
        "system_crash_or_anr_event_seen": "am_crash" in tags,
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



def classify_main_cycle_correlation(filtered_exit: str, event_log: str,
                                    main_log: str) -> dict:
    """Privately correlate *each* new exact clone MAIN PID across three buffers.

    ActivityExitInfo + AOSP EventLog structured process fields + Android main
    logcat are read-only evidence. Do not leak PID, timestamps, stack, paths,
    class details or message. A correlation is not proof of what called exit.
    """
    relevant = main_exit_pids(filtered_exit)
    zero_exits = set()
    entries = EXIT_BLOCK.split(filtered_exit[:250000])
    if len(entries) == 1:
        entries = filtered_exit[:250000].splitlines()
    for block in entries[:100]:
        name, pid = PROCESS_RE.search(block), PID_RE.search(block)
        if name is None or name.group(1) != CLONE or pid is None:
            continue
        value = int(pid.group(1))
        if value not in relevant:
            continue
        reason = re.search(r"\breason\s*[=:]\s*(\d{1,2})\b", block, re.I)
        status = re.search(r"\bstatus\s*[=:]\s*(-?\d{1,6})\b", block, re.I)
        if reason and status and reason.group(1) == "1" and int(status.group(1)) == 0:
            zero_exits.add(value)

    process_start = set()
    process_died = set()
    for line in event_log.splitlines()[-9000:]:
        marker = EVENT_RE.search(line[:180])
        if marker is None or marker.group(1) not in ("am_proc_start", "am_proc_died"):
            continue
        tag = marker.group(1)
        fields = _event_fields(line)
        index = PROCESS_FIELD_POSITION[tag]
        if len(fields) <= index or fields[index] != CLONE or len(fields) <= 1:
            continue
        pid_text = fields[1]
        if not re.fullmatch(r"[1-9][0-9]{0,7}", pid_text):
            continue
        pid = int(pid_text)
        if pid not in relevant:
            continue
        (process_start if tag == "am_proc_start" else process_died).add(pid)

    illegal_state = set()
    for line in main_log.splitlines()[-15000:]:
        match = LOG.match(line)
        if match is None:
            continue
        raw_pid, severity, tag, message = match.groups()
        pid = int(raw_pid)
        if pid not in relevant or severity not in ("E", "F"):
            continue
        if re.search(r"\bIllegalStateException\b", message):
            illegal_state.add(pid)

    complete = process_start & process_died
    return {
        "exact_new_main_exit_pids_bounded": min(len(relevant), 100),
        "main_exit_self_zero_pids_bounded": min(len(zero_exits), 100),
        "event_start_correlated_pids_bounded": min(len(process_start), 100),
        "event_died_correlated_pids_bounded": min(len(process_died), 100),
        "start_and_died_correlated_pids_bounded": min(len(complete), 100),
        "illegal_state_error_correlated_pids_bounded": min(len(illegal_state), 100),
        "all_new_main_exits_self_zero": bool(relevant) and relevant <= zero_exits,
        "all_new_main_exits_start_and_die": bool(relevant) and relevant <= complete,
        "all_new_main_exits_with_illegal_state_log": bool(relevant)
            and relevant <= illegal_state,
        "raw_process_ids_or_log_exposed": False,
        "correlation_is_not_causation": True,
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
    """Only E/F/W log lines matching fresh exited clone MAIN PID(s)."""
    return _classify_scoped_main_log(main_exit_pids(filtered_exit), main_log)


def classify_live_main_log_signals(pidof_output: str, main_log: str) -> dict:
    """Read-only working ORIGINAL MAIN control from public 'pidof' output.

    Exactly one numeric PID is accepted (no shell or arbitrary process input);
    the caller must check the publisher-signed original MAIN is alive and
    Activity resumed. Both buffers are private; report contains only categories.
    A PID alone is not an attestation of the publisher app identity.
    """
    if type(pidof_output) is not str:
        raise ValueError("INVALID_READ_ONLY_PROCESS_WITNESS")
    candidate = pidof_output.strip()
    pids = {int(candidate)} if re.fullmatch(r"[1-9][0-9]{0,7}", candidate) else set()
    return _classify_scoped_main_log(pids, main_log)


def _classify_scoped_main_log(pids: set[int], main_log: str) -> dict:
    """Shared exact-PID parser for departed clone and surviving original.

    No raw text, class names, stack frames, paths, URLs, PIDs or account
    data leave this function. Missing PID means no attributed observation.
    """
    groups = []
    stack_subsystems = []
    fatal_seen = False
    error_seen = False
    uncaught_seen = False
    matched = 0
    stack_frames = 0
    exception_window = 0
    system_err_tag_seen = False
    android_runtime_tag_seen = False
    illegal_state_error_severity_seen = False
    illegal_state_warning_severity_seen = False
    for line in main_log.splitlines()[-15000:]:
        event = LOG.match(line)
        if event is None or int(event.group(1)) not in pids:
            continue
        _, severity, tag, message = event.groups()
        if severity not in ("W", "E", "F"):
            continue
        tag = tag.strip()
        system_err_tag_seen |= tag == "System.err"
        android_runtime_tag_seen |= tag == "AndroidRuntime"
        matched += 1
        if severity in ("E", "F"):
            error_seen = True
        if re.search(r"\bIllegalStateException\b", message):
            illegal_state_error_severity_seen |= severity in ("E", "F")
            illegal_state_warning_severity_seen |= severity == "W"
        if tag.strip() == "AndroidRuntime" and "FATAL EXCEPTION" in message:
            fatal_seen = True
        if re.search(r"\buncaughtException\b", message, re.I):
            uncaught_seen = True
        throwable_found = False
        for label, pattern in THROWABLE_CLASSES:
            if re.search(pattern, message):
                throwable_found = True
                if label not in groups:
                    groups.append(label)
                break
        if throwable_found and severity in ("E", "F"):
            exception_window = 14
        if exception_window > 0:
            frame = re.match(
                r"^\s*at\s+([A-Za-z_$][A-Za-z0-9_.$]{4,180})\s*\(",
                message,
            )
            if frame:
                symbol = frame.group(1)
                if symbol.startswith(("com.yandex.passport.", "ru.yandex.passport.")):
                    subsystem = "YANDEX_PASSPORT"
                elif symbol.startswith(("ru.yandex.music.", "com.yandex.music.")):
                    subsystem = "YANDEX_MUSIC"
                elif symbol.startswith(("com.yandex.metrica.", "io.appmetrica.")):
                    subsystem = "APP_METRICA"
                elif symbol.startswith(("com.google.android.gms.", "com.google.android.play.")):
                    subsystem = "GOOGLE_SERVICES"
                elif symbol.startswith(("android.", "java.", "javax.", "dalvik.", "kotlin.")):
                    subsystem = "ANDROID_RUNTIME"
                else:
                    subsystem = "OTHER_OR_UNKNOWN"
                stack_frames += 1
                if subsystem not in stack_subsystems:
                    stack_subsystems.append(subsystem)
            else:
                exception_window -= 1
    return {
        "new_main_exit_pid_available": bool(pids),
        "main_scoped_warning_or_error_seen": matched > 0,
        "main_scoped_error_severity_seen": error_seen,
        "android_runtime_fatal_seen": fatal_seen,
        "uncaught_handler_marker_seen": uncaught_seen,
        "throwable_groups": groups[:7],
        "illegal_state_error_severity_seen": illegal_state_error_severity_seen,
        "illegal_state_warning_severity_seen": illegal_state_warning_severity_seen,
        "exception_stack_subsystems": stack_subsystems[:6],
        "exception_stack_frames_seen_bounded": min(stack_frames, 50),
        "system_err_tag_seen": system_err_tag_seen,
        "android_runtime_tag_seen": android_runtime_tag_seen,
        "main_log_lines_examined_bounded": min(matched, 500),
        "raw_main_log_exposed": False,
        "causality_not_proven": True,
    }
