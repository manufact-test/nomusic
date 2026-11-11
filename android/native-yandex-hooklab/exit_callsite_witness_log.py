"""Scoped and redacted MAIN-PID LibXposed exit witness classifier (lab only)."""
from __future__ import annotations

from clone_main_crash_buffer import LOG, main_exit_pids

TAG = "CELIKOM_A1_EXIT_WITNESS"
EVENTS = frozenset(("ARMED", "UNCAUGHT", "SYSTEM_EXIT", "RUNTIME_EXIT", "PROCESS_KILL"))
ORIGINS = frozenset(("REGISTERED", "NO_HOOK", "VENDOR_UNCAUGHT_HANDLER",
                      "STATIC_HANDLER", "STATIC_RUN_A", "STATIC_RUN_B",
                      "STATIC_INVOKER", "VENDOR", "PLATFORM", "UNKNOWN", "NONE"))
ERRORS = frozenset(("ILLEGAL_STATE", "SECURITY", "LINK", "OTHER_THROWABLE", "NONE"))
THREADS = frozenset(("MAIN", "OTHER"))


def classify_exit_witness(exit_dump: str, main_log: str) -> dict:
    """Never prints or returns PIDs, vendor classes, raw messages or secrets.

    Events must be the exact tag, exact MAIN PID in ApplicationExitInfo,
    strictly formatted enum-only payload. A missing event cannot prove the
    absence of a termination call.
    """
    pids = main_exit_pids(exit_dump)
    kinds: set[str] = set()
    origins: set[str] = set()
    errors: set[str] = set()
    main_events = 0
    armed = False
    untrusted = 0
    for line in main_log.splitlines()[-18000:]:
        match = LOG.match(line)
        if not match:
            continue
        pid, level, tag, raw = match.groups()
        if level != "I" or tag != TAG or int(pid) not in pids:
            continue
        if len(raw) > 150 or raw.count(";") != 3:
            untrusted += 1
            continue
        fields = raw.split(";")
        parts = []
        for field in fields:
            if field.count("=") != 1:
                break
            parts.append(field.split("=", 1))
        if len(parts) != 4 or [p[0] for p in parts] != [
                "event", "origin", "error", "thread"]:
            untrusted += 1
            continue
        event, origin, error, thread = (p[1] for p in parts)
        if (event not in EVENTS or origin not in ORIGINS
                or error not in ERRORS or thread not in THREADS):
            untrusted += 1
            continue
        kinds.add(event)
        origins.add(origin)
        errors.add(error)
        main_events += thread == "MAIN"
        armed |= event == "ARMED" and origin == "REGISTERED"
    return {
        "scoped_fresh_main_pid_available": bool(pids),
        "module_armed_on_main": armed,
        "observed_events": sorted(kinds),
        "caller_groups": sorted(origins),
        "exception_categories": sorted(errors),
        "main_thread_event_count_bounded": min(main_events, 20),
        "ignored_untrusted_lines_bounded": min(untrusted, 100),
        "raw_log_or_pid_exposed": False,
        "runtime_cause_not_assumed": True,
    }
