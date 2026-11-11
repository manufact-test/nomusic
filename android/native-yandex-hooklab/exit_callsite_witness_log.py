"""Scoped and redacted MAIN-PID LibXposed exit witness classifier (lab only)."""
from __future__ import annotations

from clone_main_crash_buffer import LOG, main_exit_pids

TAG = "CELIKOM_A1_EXIT_WITNESS"
EVENTS = frozenset(("ARMED", "UNCAUGHT", "SYSTEM_EXIT", "RUNTIME_EXIT",
                    "PROCESS_KILL", "PREFIX_CHECK", "PREFIX_HOOK",
                    "RUN_CTOR", "RUN_ENTER", "RUN_HOOK",
                    "HI2_EXCEPTION"))
ORIGINS = frozenset(("REGISTERED", "NO_HOOK", "VENDOR_UNCAUGHT_HANDLER",
                      "STATIC_HANDLER", "STATIC_RUN_A", "STATIC_RUN_B",
                      "STATIC_INVOKER", "VENDOR", "PLATFORM", "UNKNOWN", "NONE",
                      "OWN_MAIN", "OWN_AUX", "ORIGINAL_MAIN", "ORIGINAL_AUX",
                      "UNCLASSIFIED", "STATIC_COROUTINE"))
ERRORS = frozenset(("ILLEGAL_STATE", "SECURITY", "LINK", "OTHER_THROWABLE",
                    "NONE", "MATCH_TRUE", "MATCH_FALSE",
                    "KILL_TARGET_SELF", "KILL_TARGET_OTHER",
                    "KILL_TARGET_UNKNOWN", "CASE_0", "CASE_1", "CASE_2",
                    "CASE_3", "CASE_4", "CASE_5", "CASE_6", "CASE_7",
                    "CASE_OTHER", "CASE_UNKNOWN",
                    "EXC_UNKNOWN", "EXC_SIGN_AND_AUTH", "EXC_SIGNATURE",
                    "EXC_AUTH", "EXC_PERMISSION", "EXC_LOCALE",
                    "EXC_LIFECYCLE", "EXC_OTHER"))
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
    # Kept strictly private: these keys are exact exited MAIN PIDs. Never
    # serialize a PID or raw log text. Correlation is per MAIN thread only.
    last_main_prefix_by_pid: dict[int, tuple[str, str]] = {}
    first_exit_prefix_by_pid: dict[int, tuple[str, str]] = {}
    first_exit_seen: set[int] = set()
    first_kill_target_by_pid: dict[int, str] = {}
    last_main_run_case_by_pid: dict[int, str] = {}
    first_exit_run_case_by_pid: dict[int, str] = {}
    hi2_exception_categories: set[str] = set()
    sig_error_seen_by_pid: set[int] = set()
    signature_before_mode2_by_pid: set[int] = set()
    full_ordered_chain_main_pids: set[int] = set()
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
        number = int(pid)
        if (event == "HI2_EXCEPTION" and origin == "STATIC_COROUTINE"
                and error.startswith("EXC_")):
            hi2_exception_categories.add(error)
            if error in ("EXC_SIGNATURE", "EXC_SIGN_AND_AUTH"):
                sig_error_seen_by_pid.add(number)
        origins.add(origin)
        errors.add(error)
        main_events += thread == "MAIN"
        armed |= event == "ARMED" and origin == "REGISTERED"
        if thread == "MAIN":
            if (event == "RUN_ENTER" and error == "CASE_2"
                    and number in sig_error_seen_by_pid):
                signature_before_mode2_by_pid.add(number)
            if (event == "PROCESS_KILL" and error.startswith("KILL_TARGET_")
                    and number in signature_before_mode2_by_pid
                    and last_main_prefix_by_pid.get(number) == ("OWN_AUX", "MATCH_TRUE")):
                full_ordered_chain_main_pids.add(number)
            if event == "RUN_ENTER" and error.startswith("CASE_"):
                last_main_run_case_by_pid[number] = error
            if (event in ("PROCESS_KILL", "SYSTEM_EXIT")
                    and number not in first_exit_run_case_by_pid
                    and number in last_main_run_case_by_pid):
                first_exit_run_case_by_pid[number] = last_main_run_case_by_pid[number]
            if (event == "PROCESS_KILL" and number not in first_kill_target_by_pid
                    and error.startswith("KILL_TARGET_")):
                first_kill_target_by_pid[number] = error
            if event == "PREFIX_CHECK" and error in ("MATCH_TRUE", "MATCH_FALSE"):
                last_main_prefix_by_pid[number] = (origin, error)
            elif event in ("PROCESS_KILL", "SYSTEM_EXIT") and number not in first_exit_seen:
                first_exit_seen.add(number)
                if number in last_main_prefix_by_pid:
                    first_exit_prefix_by_pid[number] = last_main_prefix_by_pid[number]
    return {
        "scoped_fresh_main_pid_available": bool(pids),
        "module_armed_on_main": armed,
        "prefix_hook_reported": "PREFIX_HOOK" in kinds,
        "run_mode_hook_reported": "RUN_HOOK" in kinds,
        "run_mode_entered": "RUN_ENTER" in kinds,
        "first_exit_run_mode_groups": sorted(set(first_exit_run_case_by_pid.values())),
        "first_exit_run_mode_main_pid_count_bounded": min(len(first_exit_run_case_by_pid), 10),
        "run_mode_observation_not_replacement": True,
        "hi2_exception_categories": sorted(hi2_exception_categories),
        "hi2_signature_error_new_main_pids_bounded": min(len(sig_error_seen_by_pid), 10),
        "hi2_signature_error_precedes_mode2_in_main_pids_bounded":
            min(len(signature_before_mode2_by_pid), 10),
        "ordered_signature_mode2_aux_prefix_kill_chain_main_pids_bounded":
            min(len(full_ordered_chain_main_pids), 10),
        "ordered_chain_logcat_marker_order_not_proof_of_policy_intent": True,
        "hi2_exception_absence_inconclusive": True,
        "hi2_exception_message_or_token_never_exported": True,
        "prefix_check_observed": "PREFIX_CHECK" in kinds,
        "prefix_match_result_categories": sorted(x for x in errors if x.startswith("MATCH_")),
        "prefix_known_target_groups": sorted(x for x in origins if x in {
            "OWN_MAIN", "OWN_AUX", "ORIGINAL_MAIN", "ORIGINAL_AUX"}),
        "first_exit_has_preceding_main_prefix_by_pid_bounded": min(
            len(first_exit_prefix_by_pid), 10),
        "first_exit_preceding_main_prefix_results": sorted(set(
            err for _, err in first_exit_prefix_by_pid.values())),
        "first_exit_preceding_main_prefix_groups": sorted(set(
            origin for origin, _ in first_exit_prefix_by_pid.values())),
        "first_exit_preceding_prefix_not_causal_proof": True,
        "first_kill_target_groups": sorted(set(first_kill_target_by_pid.values())),
        "first_kill_target_observed_main_pids_bounded": min(len(first_kill_target_by_pid), 10),
        "kill_target_main_pid_only_no_raw_target_pid": True,
        "observed_events": sorted(kinds),
        "caller_groups": sorted(origins),
        "exception_categories": sorted(errors),
        "main_thread_event_count_bounded": min(main_events, 20),
        "ignored_untrusted_lines_bounded": min(untrusted, 100),
        "raw_log_or_pid_exposed": False,
        "runtime_cause_not_assumed": True,
    }
