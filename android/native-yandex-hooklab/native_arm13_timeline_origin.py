"""Private native ARM13 Android main/events timeline, bounded diagnostic only.

This uses a SINGLE merged read-only 'logcat -b main -b events -v threadtime'
stream from a disposable guest, so event and exception ordering share the
same source timeline. Never emit raw messages, PIDs, tag names, timestamps,
stack traces, account data or source code. A correlation is not causation.
"""
from __future__ import annotations

import re

from clone_main_crash_buffer import CLONE, LOG, main_exit_pids
from native_arm13_startup_observer import (
    ORIGINAL, PROCESS_FIELD_POSITION, _event_fields,
)

TSTAMP = re.compile(r"^\s*(\d\d-\d\d\s+\d\d:\d\d:\d\d\.\d+)\s+")
MARKER = re.compile(r"\bIllegalStateException\b")
FAMILIES = (
    "ANDROID_RUNTIME", "SYSTEM_ERR", "ANDROID_FRAMEWORK",
    "MUSIC_LOGGER", "METRICA_LOGGER", "OTHER_OR_UNKNOWN",
)


def _exact_live_pid(value: str) -> set[int]:
    if type(value) is not str:
        raise ValueError("INVALID_ORIGINAL_PID_TYPE")
    candidate = value.strip()
    return {int(candidate)} if re.fullmatch(r"[1-9][0-9]{0,7}", candidate) else set()


def _safe_logger_family(tag: str) -> str:
    """Fixed six-value category, never an arbitrary publisher tag."""
    if tag == "AndroidRuntime":
        return "ANDROID_RUNTIME"
    if tag == "System.err":
        return "SYSTEM_ERR"
    if tag in ("ActivityManager", "ActivityTaskManager", "PackageManager",
               "AndroidRuntimeInit", "libc", "DEBUG"):
        return "ANDROID_FRAMEWORK"
    name = tag.lower()
    if name.startswith(("yandexmusic", "ymusic", "musicapp", "musicplayer",
                        "ru.yandex.music")):
        return "MUSIC_LOGGER"
    if name.startswith(("appmetrica", "metrica", "io.appmetrica")):
        return "METRICA_LOGGER"
    return "OTHER_OR_UNKNOWN"


def classify_merged_startup_timeline(raw: str, package: str, *,
                                     fresh_main_exit: str = "",
                                     original_live_pid: str = "") -> dict:
    """Categorize real cross-buffer ordering for exact MAIN PID only.

    For clone: source PIDs exclusively from fresh exact-MAIN exit records.
    For original: caller must attest publisher-signed installed, alive,
    Activity resumed and pass EXACTLY one live PID from shell pidof.
    The merged buffer is read once; no concatenated independent dumps can
    masquerade as a chronological sequence.
    """
    if package == CLONE:
        if original_live_pid:
            raise ValueError("ORIGINAL_PID_NOT_VALID_FOR_CLONE")
        targets = main_exit_pids(fresh_main_exit)
    elif package == ORIGINAL:
        if fresh_main_exit:
            raise ValueError("CLONE_EXIT_INFO_NOT_VALID_FOR_ORIGINAL")
        targets = _exact_live_pid(original_live_pid)
    else:
        raise ValueError("UNAPPROVED_PACKAGE")
    timeline = {pid: {"start": [], "died": [], "illegal": [],
                      "families": set(), "warnings": 0} for pid in targets}
    last_stamp = ""
    sorted_witness = True
    valid_lines = 0
    relevant_lines = 0
    for index, line in enumerate(raw.splitlines()[-20000:]):
        event = LOG.match(line)
        tm = TSTAMP.match(line)
        if event is None or tm is None:
            continue
        stamp = tm.group(1)
        if last_stamp and stamp < last_stamp:
            sorted_witness = False
        last_stamp = stamp
        valid_lines += 1
        emitter_pid, severity, tag, message = event.groups()
        tag = tag.strip()
        if tag in ("am_proc_start", "am_proc_died"):
            fields = _event_fields(line)
            position = PROCESS_FIELD_POSITION[tag]
            if (len(fields) <= position or fields[position] != package
                    or len(fields) <= 1 or
                    not re.fullmatch(r"[1-9][0-9]{0,7}", fields[1])):
                continue
            victim = int(fields[1])
            if victim in targets:
                timeline[victim]["start" if tag == "am_proc_start"
                                 else "died"].append(index)
                relevant_lines += 1
            continue
        pid = int(emitter_pid)
        if pid not in targets or severity not in ("W", "E", "F"):
            continue
        relevant_lines += 1
        if MARKER.search(message):
            if severity == "W":
                timeline[pid]["warnings"] += 1
            else:
                timeline[pid]["illegal"].append(index)
                timeline[pid]["families"].add(_safe_logger_family(tag))

    # An app-reported marker before the system death event is more informative
    # than a marker in an arbitrary log dump, but not proof of thrown exception.
    before_death = 0
    after_death_only = 0
    no_start_or_death = 0
    unique_start_death = 0
    marker_count = 0
    families = set()
    for witness in timeline.values():
        starts, deaths, markers = (witness[k] for k in ("start", "died", "illegal"))
        families |= witness["families"]
        if markers:
            marker_count += 1
        if len(starts) == 1 and len(deaths) == 1 and starts[0] < deaths[0]:
            unique_start_death += 1
            if sorted_witness and any(starts[0] < m < deaths[0] for m in markers):
                before_death += 1
            elif sorted_witness and markers and all(m > deaths[0] for m in markers):
                after_death_only += 1
        else:
            no_start_or_death += 1

    return {
        "target_exact_main_process_count_bounded": min(len(targets), 100),
        "merged_buffer_valid_lines_bounded": min(valid_lines, 20000),
        "merged_buffer_relevant_lines_bounded": min(relevant_lines, 20000),
        "merged_threadtime_non_decreasing": bool(valid_lines) and sorted_witness,
        "exact_main_single_start_death_count": min(unique_start_death, 100),
        "main_with_illegal_state_error_count": min(marker_count, 100),
        "illegal_state_between_start_death_count": min(before_death, 100),
        "illegal_state_only_after_death_count": min(after_death_only, 100),
        "missing_unique_lifecycle_count": min(no_start_or_death, 100),
        "illegal_state_logger_families": sorted(families)[:len(FAMILIES)],
        "all_main_illegal_state_precedes_death":
            bool(targets) and sorted_witness
            and before_death == len(targets)
            and unique_start_death == len(targets),
        "raw_main_events_log_exposed": False,
        "raw_logger_or_pid_exposed": False,
        "causation_not_established": True,
    }
