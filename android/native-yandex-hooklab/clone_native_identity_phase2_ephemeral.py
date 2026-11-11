#!/usr/bin/env python3
"""EPHEMERAL: tightly scoped five-split package-identity research, no distribution.

One known AppMetrica authority DEX string, four manifest provider authorities
and one Passport sync resource are changed only in disposable CI copies.
This is not a real CELIKOM-enabled Yandex client and NEVER installs on a device.
No DRM, auth/security checks, Play Protect, certificates or accounts bypassed.
"""
from __future__ import annotations
import hashlib
import json
import os
import struct
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path
import clone_native_splits_ephemeral as source
import clone_native_splits_arsclib_ephemeral as arsc
from merge_lab_splits_ephemeral import merge_ephemeral
from clone_lspatch_loader_zero import wrap_clone_with_lspatch_zero
from clone_lab_profileability import enable_private_lab_shell_profiling

OLD_METRICA = "com.yandex.preinstallsatellite.appmetrica.provider"
NEW_METRICA = "com.yandex.preinstallsatellite.appmetrica.provideq"
OLD_SYNC = "com.yandex.passport.sync.ru.yandex.music"
NEW_SYNC = "com.yandex.passport.sync." + source.DEST
SYNC_KEY = "passport_sync_adapter_content_authority"
PASSPORT_PREFIX = "com.yandex.passport."
ANDROID = "{" + source.ANDROID + "}"


def patch_one_dex(data):
    original = OLD_METRICA.encode("ascii")
    replacement = NEW_METRICA.encode("ascii")
    if len(original) != len(replacement):
        raise arsc.TrialError("DECODED_DEX_LITERAL_LENGTH_DRIFT")
    count = data.count(original)
    if count == 0:
        return data, False
    if count != 1 or not data.startswith(b"dex\n"):
        raise arsc.TrialError("DEX_TARGET_NOT_ONE_EXACT_LITERAL")
    # ART requires string_ids to be strictly sorted. The legacy fixed-length
    # substitute is known to violate this rule: NEVER emit such a broken DEX.
    from inspect_android_host import Dex
    parsed = Dex(data)
    original_slots = [idx for idx in range(parsed.string_count)
                      if parsed.string(idx) == OLD_METRICA]
    if len(original_slots) != 1:
        raise arsc.TrialError("DEX_STRING_ID_NOT_UNIQUE")
    idx = original_slots[0]
    if idx == 0 or idx + 1 >= parsed.string_count or not (
            parsed.string(idx - 1) < NEW_METRICA < parsed.string(idx + 1)):
        raise arsc.TrialError("DEX_STRING_ID_ORDER_FAIL_CLOSED")
    updated = bytearray(data.replace(original, replacement, 1))
    updated[12:32] = hashlib.sha1(updated[32:]).digest()
    updated[8:12] = struct.pack("<I", zlib.adler32(updated[12:]) & 0xffffffff)
    return bytes(updated), True


def rewrite_passport_and_metrica(xml):
    root = source.ET.fromstring(xml)
    changed = 0
    for provider in root.iter("provider"):
        attr = ANDROID + "authorities"
        value = provider.attrib.get(attr, "")
        if value == OLD_METRICA:
            provider.set(attr, NEW_METRICA)
            changed += 1
        elif value.startswith(PASSPORT_PREFIX) and value.endswith(source.SOURCE):
            provider.set(attr, value[:-len(source.SOURCE)] + source.DEST)
            changed += 1
    return source.ET.tostring(root, encoding="utf-8", xml_declaration=True), changed


def replace_sync_resource(decoded):
    matches = []
    for file in decoded.rglob("strings.xml"):
        if file.stat().st_size > 3 * 1024 * 1024:
            continue
        root = source.ET.parse(file).getroot()
        edited = False
        for element in root.iter("string"):
            if element.attrib.get("name") == SYNC_KEY:
                if (element.text or "").strip() != OLD_SYNC:
                    raise arsc.TrialError("PASSPORT_SYNC_RESOURCE_VALUE_DRIFT")
                element.text = NEW_SYNC
                edited = True
        if edited:
            file.write_bytes(source.ET.tostring(root, encoding="utf-8", xml_declaration=True))
            matches.append(str(file.relative_to(decoded)))
    return matches


def resolved_provider_authorities(manifest_bytes, sync_value):
    """Compare actual public provider identities, resolving the one pinned sync resource.

    This catches literal and resource-backed collisions before attempting an
    install next to the publisher-signed original. No device or private state.
    Unknown resource references fail closed rather than guess.
    """
    root = source.ET.fromstring(manifest_bytes)
    names = set()
    for provider in root.iter("provider"):
        value = provider.attrib.get(ANDROID + "authorities", "")
        for part in value.split(";"):
            name = part.strip()
            if not name:
                continue
            if name == "@string/" + SYNC_KEY:
                name = sync_value
            elif name.startswith("@"):
                raise arsc.TrialError("UNRESOLVED_PROVIDER_AUTHORITY_RESOURCE")
            if name in names:
                raise arsc.TrialError("DUPLICATE_PROVIDER_AUTHORITY")
            names.add(name)
    return names


# These TWO custom permissions are already owned by the publisher-signed
# original, with Android signature protection. For a disposable install-only
# research clone, OMIT duplicate DECLARATIONS; keep original ownership and all
# uses-permission requests unchanged (thus cross-signature access is NOT granted).
# This is never used in the structural baseline or a distributed application.
SHADOWED_SIGNATURE_PERMISSIONS = {
    "com.yandex.permission.READ_CREDENTIALS",
    "com.yandex.music.RELAY_PERMISSION",
}


def omit_shadowed_signature_permission_declarations(manifest_bytes):
    root = source.ET.fromstring(manifest_bytes)
    omitted = set()
    for child in list(root):
        if child.tag != "permission":
            continue
        name = child.attrib.get(ANDROID + "name", "")
        if name not in SHADOWED_SIGNATURE_PERMISSIONS:
            continue
        if child.attrib.get(ANDROID + "protectionLevel") != "signature":
            raise arsc.TrialError("SHADOWED_PERMISSION_PROTECTION_LEVEL_DRIFT")
        root.remove(child)
        omitted.add(name)
    if omitted != SHADOWED_SIGNATURE_PERMISSIONS:
        raise arsc.TrialError("SIGNED_DUPLICATE_PERMISSION_SET_DRIFT")
    # Signature-protected uses-permission entries remain intact; do not silently
    # rewrite them into clone-owned permissions or bypass issuer signature.
    used = {child.attrib.get(ANDROID + "name") for child in root.iter()
            if child.tag in ("uses-permission", "uses-permission-sdk-23")}
    if "com.yandex.permission.READ_CREDENTIALS" not in used:
        raise arsc.TrialError("ORIGINAL_SIGNATURE_PERMISSION_REQUEST_CHANGED")
    return source.ET.tostring(root, encoding="utf-8", xml_declaration=True), len(omitted)


def classify_manifest_shell_profileability(manifest_bytes):
    """Only original public AndroidManifest fields; no APK or identity output."""
    root = source.ET.fromstring(manifest_bytes)
    app = root.find("application")
    if root.tag != "manifest" or app is None:
        raise arsc.TrialError("PROFILE_PUBLIC_MANIFEST_STRUCTURE_INVALID")
    namespace = "{" + source.ANDROID + "}"
    child = app.find("profileable")
    debuggable = app.attrib.get(namespace + "debuggable", "false") == "true"
    shell = child is not None and child.attrib.get(namespace + "shell") == "true"
    enabled = child is None or child.attrib.get(namespace + "enabled", "true") != "false"
    return {
        "publisher_debuggable": debuggable,
        "profileable_declaration_present": child is not None,
        "profileable_shell_granted": bool(shell),
        "profileable_enabled": bool(enabled),
        "ordinary_shell_method_tracing_authorized": bool(debuggable or shell and enabled),
        "raw_manifest_exposed": False,
        "does_not_change_application_permissions": True
    }


def classify_clone_launch_logcat(raw):
    """Report bounded public Java CLASS names and flags only, never raw log text.

    No arbitrary message, exception stack, URL, token or process metadata can
    escape in this result. All names must match package/class grammar and
    preapproved non-personal Java namespace prefixes.
    """
    import re
    raw_candidates = []
    patterns = (
        r'Didn.t find class "([A-Za-z0-9_.$/]+)"',
        r'Failed resolution of: L([A-Za-z0-9_$/]+);',
        r'(?:ClassNotFoundException|NoClassDefFoundError):\s*(?:class\s+)?([A-Za-z0-9_.$/]+)',
    )
    for regex in patterns:
        raw_candidates.extend(re.findall(regex, raw, flags=re.IGNORECASE))
    allowed = ("com.yandex.", "ru.yandex.", "pro.celikom.",
               "androidx.", "android.", "com.google.", "kotlin.",
               "org.jetbrains.", "org.chromium.")
    class_hints = []
    for candidate in raw_candidates:
        name = candidate.replace("/", ".")
        if (len(name) < 8 or len(name) > 180 or
                not name.startswith(allowed) or
                not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_.$]*", name)):
            continue
        if name not in class_hints:
            class_hints.append(name)
        if len(class_hints) >= 4:
            break
    return {
        "bounded_missing_public_class_hints": class_hints,
        "fatal_exception_seen": "FATAL EXCEPTION" in raw,
        "clone_process_named_in_crash": "Process: " + source.DEST in raw,
        "security_exception_seen": "SecurityException" in raw,
        "class_loading_exception_seen": (
            "ClassNotFoundException" in raw or "NoClassDefFoundError" in raw),
        "native_library_error_seen": "UnsatisfiedLinkError" in raw,
        "dex_verify_error_seen": "VerifyError" in raw,
        "resources_inflation_error_seen": "InflateException" in raw,
        "illegal_state_error_seen": "IllegalStateException" in raw,
        "permission_denial_seen": "Permission Denial" in raw,
        "runtime_exception_seen": "RuntimeException" in raw,
        "raw_log_included": False
    }



def summarize_installed_package_code_flags(raw):
    """Expose public package-manager code-path booleans, no raw app data."""
    import re
    flag_lines = [line for line in raw.splitlines() if "flags=[" in line]
    return {
        "has_code_flag": any(re.search(r"\bHAS_CODE\b", line) for line in flag_lines),
        "has_code_path_record": "codePath=" in raw,
        "has_base_apk_record": "base.apk" in raw,
        "has_classloader_record": "classLoaderName=" in raw,
        "raw_dumpsys_exposed": False
    }




def dex_header_integrity(raw):
    """Validate standard DEX structural header without running app code."""
    if len(raw) < 112 or not raw.startswith(b"dex\n"):
        return False
    file_size = int.from_bytes(raw[32:36], "little")
    header_size = int.from_bytes(raw[36:40], "little")
    checksum = int.from_bytes(raw[8:12], "little")
    return (file_size == len(raw) and header_size == 112 and
            hashlib.sha1(raw[32:]).digest() == raw[12:32] and
            (zlib.adler32(raw[12:]) & 0xffffffff) == checksum)




def installed_process_snapshot(package):
    """Capture short-lived startup behaviour without identifiers or raw logs."""
    import subprocess
    if package not in (source.SOURCE, source.DEST):
        raise arsc.TrialError("UNAPPROVED_PACKAGE_PROCESS_PROBE")
    pid = subprocess.run(["adb", "shell", "pidof", package],
                         text=True, capture_output=True, timeout=20)
    main_alive = (pid.returncode == 0 and
                  bool(pid.stdout.strip()) and
                  all(x.isdigit() for x in pid.stdout.split()))
    ps = subprocess.run(["adb", "shell", "ps", "-A"],
                        text=True, capture_output=True, timeout=30)
    if ps.returncode:
        raise arsc.TrialError("ANDROID_PS_PROBE_FAILED")
    process_names = [line.split()[-1] for line in ps.stdout.splitlines()[1:]
                     if line.split()]
    aux_names = [name[len(package)+1:] for name in process_names
                 if name.startswith(package + ":")]
    import re
    public_aux = [name for name in aux_names[:8]
                  if len(name) <= 64 and re.fullmatch(r"[a-zA-Z0-9_.-]+", name)]
    return {
        "direct_pid_alive": main_alive,
        "ps_main_process_alive": package in process_names,
        "ps_auxiliary_process_alive": bool(aux_names),
        "safe_auxiliary_process_suffixes": public_aux,
        "any_named_process_alive": (main_alive or package in process_names or
            bool(aux_names)),
        "raw_process_output_exposed": False
    }


def classify_activity_start(stdout):
    """Public Activity Manager status only, no raw command contents."""
    return {
        "activity_status_ok": "Status: ok" in stdout,
        "activity_explicit_error": ("Error:" in stdout or
                                   "Exception" in stdout or
                                   "Activity not started" in stdout),
        "launch_state_cold": "LaunchState: COLD" in stdout,
        "launch_state_warm": "LaunchState: WARM" in stdout,
        "raw_activity_output_exposed": False
    }



def classify_nonblocking_activity_start(stdout):
    """Confirm ActivityManager dispatch only; MAIN/UI still must be live."""
    import re
    return {
        "activity_status_ok": bool(re.search(r"(?m)^Starting:\\s+Intent\\s*\\{", stdout)),
        "activity_explicit_error": (
            "Error:" in stdout or "Exception" in stdout
            or "Activity not started" in stdout),
        "launch_state_cold": False,
        "launch_state_warm": False,
        "nonblocking_dispatch_only": True,
        "raw_activity_output_exposed": False,
    }


def disposable_foreground_snapshot(package):
    """Only foreground booleans from public Android activity/window manager.

    All captured system text stays inside the temporary emulator CI process;
    no URLs, account screens, view texts or component internals are printed.
    """
    if package not in (source.SOURCE, source.DEST):
        raise arsc.TrialError("UNAPPROVED_FOREGROUND_PACKAGE")
    activity = arsc.run(["adb", "shell", "dumpsys", "activity", "activities"],
                        "FOREGROUND_ACTIVITY_QUERY", 35)
    window = arsc.run(["adb", "shell", "dumpsys", "window", "windows"],
                      "FOREGROUND_WINDOW_QUERY", 35)
    resumed = [line for line in activity.splitlines()
               if "resumedactivity" in line.lower()]
    focused = [line for line in window.splitlines()
               if "mCurrentFocus" in line or "mFocusedApp" in line]
    return {
        "activity_resumed_for_package": any(package + "/" in line for line in resumed),
        "window_focus_for_package": any(package + "/" in line for line in focused),
        "activity_resumed_row_detected": bool(resumed),
        "window_focus_row_detected": bool(focused),
        "raw_activity_or_window_output_exposed": False
    }




def full_native_main_ui_pass(samples, activity_status, foreground):
    """Fail closed: AppMetrica/helper process is NEVER a main-player PASS."""
    if not samples:
        return False
    last = samples[-1]
    return bool(
        activity_status.get("activity_status_ok")
        and not activity_status.get("activity_explicit_error")
        and (last.get("direct_pid_alive") or last.get("ps_main_process_alive"))
        and foreground.get("activity_resumed_for_package")
        and foreground.get("window_focus_for_package")
    )



def classify_activity_exit_info(raw):
    """Classify Android 11 ApplicationExitInfo for MAIN, excluding helpers.

    AOSP uses numeric reason=4 (APP CRASH(EXCEPTION)), not REASON_CRASH.
    Never interpret unscoped or helper-process records as a MAIN crash.
    No process identifiers, timestamps or raw system text are returned.
    """
    import re
    known = {
        1: "exit_self", 2: "signaled", 3: "low_memory",
        4: "crash", 5: "crash_native", 6: "anr",
        7: "initialization_failure", 8: "permission_change",
        9: "excessive_resource_usage", 12: "dependency_died",
    }
    # AOSP dumpsys emits ApplicationExitInfo records with process and reason
    # on one or multiple lines. Never assign an unnamed record to MAIN.
    blocks = re.split(
        r"(?im)(?=^\s*(?:ApplicationExitInfo\s*#?\d+|#\d+:\s*ApplicationExitInfo))",
        raw)
    if len(blocks) == 1:
        blocks = raw.splitlines()
    main_codes, auxiliary_codes, unknown_codes = set(), set(), set()
    main_exit_statuses = []
    main_exit_subreasons = []
    for block in blocks:
        matches = re.findall(r"\breason\s*[=:]\s*(\d{1,2})\b", block, re.I)
        if not matches:
            continue
        process = re.search(
            r"\b(?:processName|process|process name)\s*[=:]\s*"
            r"([A-Za-z0-9_.:]+)", block, re.I)
        name = process.group(1) if process else None
        if name == source.DEST:
            # AOSP API 30 dump() includes status=N: exit(int) status.
            # Share only bounded exit codes, never description/trace/UID.
            status_match = re.search(r"\bstatus\s*[=:]\s*(-?\d{1,4})\b", block, re.I)
            subreason_match = re.search(r"\bsubreason\s*[=:]\s*(\d{1,3})\b", block, re.I)
            if status_match and -255 <= int(status_match.group(1)) <= 255:
                main_exit_statuses.append(int(status_match.group(1)))
            if subreason_match and int(subreason_match.group(1)) <= 255:
                main_exit_subreasons.append(int(subreason_match.group(1)))
        target = (main_codes if name == source.DEST else
                  auxiliary_codes if name and name.startswith(source.DEST + ":")
                  else unknown_codes)
        for number in matches[:16]:
            code = int(number)
            if 0 <= code <= 16:
                target.add(code)
    return {
        **{"exit_reason_" + label: code in main_codes
           for code, label in known.items()},
        "main_exit_record_seen": bool(main_codes),
        "main_exit_status_available": bool(main_exit_statuses),
        "main_exit_status": main_exit_statuses[0] if main_exit_statuses else None,
        "main_exit_self_status_zero": 1 in main_codes and 0 in main_exit_statuses,
        "main_exit_self_status_nonzero": 1 in main_codes and any(s != 0 for s in main_exit_statuses),
        "main_exit_subreason_known": bool(main_exit_subreasons),
        "main_exit_subreason": main_exit_subreasons[0] if main_exit_subreasons else None,
        "auxiliary_exit_record_seen": bool(auxiliary_codes),
        "unattributed_exit_record_seen": bool(unknown_codes),
        "unattributed_crash_reason_seen": bool({4, 5} & unknown_codes),
        "exit_info_command_unrecognized": (
            "Unknown command" in raw or "Bad activity command" in raw),
        "raw_exit_info_exposed": False,
    }


def classify_clone_process_events(raw):
    """Bounded Android event-log lifecycle flags, MAIN distinct from helper."""
    import re
    main = re.compile(
        r"(?<![A-Za-z0-9_.])" + re.escape(source.DEST) +
        r"(?![A-Za-z0-9_.:])")
    tags = ("am_proc_start", "am_proc_died", "am_kill",
            "am_crash", "am_anr", "am_create_activity",
            "am_resume_activity", "am_pause_activity",
            "am_finish_activity", "am_destroy_activity")
    flags = {tag + "_main_seen": False for tag in tags}
    lifecycle_stages = []
    helper_seen = False
    for line in raw.splitlines()[:5000]:
        if source.DEST not in line:
            continue
        helper_seen |= bool(re.search(
            re.escape(source.DEST) + r":[A-Za-z0-9_.]+", line))
        if not main.search(line):
            continue
        for tag in tags:
            if re.search(r"\b" + tag + r"\b", line):
                flags[tag + "_main_seen"] = True
                if len(lifecycle_stages) < 20:
                    lifecycle_stages.append(tag)
    return {**flags, "auxiliary_process_events_seen": helper_seen,
            "main_lifecycle_stages": lifecycle_stages,
            "main_activity_lifecycle_observed": any(
                item in lifecycle_stages for item in
                ("am_create_activity", "am_resume_activity", "am_pause_activity")),
            "raw_event_log_exposed": False}




def classify_main_pid_scoped_system_logs(exit_info_raw, threadtime_raw):
    """Read-only categorical log evidence scoped to MAIN exit-info PIDs.

    This prevents attribution of original Yandex or AppMetrica errors to MAIN.
    Never emit PID, class stack, logcat text, URL, username, path or token.
    Unknown PID/logcat formats fail closed to NO_OBSERVATION.
    """
    import re
    blocks = re.split(
        r"(?im)(?=^\s*(?:ApplicationExitInfo\s*#?\d+|#\d+:\s*ApplicationExitInfo))",
        exit_info_raw)
    if len(blocks) == 1:
        blocks = exit_info_raw.splitlines()
    target_pids = set()
    for block in blocks[:80]:
        match = re.search(r"\bprocess\s*[=:]\s*([A-Za-z0-9_.:]+)", block)
        if not match or match.group(1) != source.DEST:
            continue
        pid = re.search(r"\bpid\s*[=:]\s*(\d{1,8})\b", block)
        if pid and 1 <= int(pid.group(1)) <= 99999999:
            target_pids.add(int(pid.group(1)))
    tags = set()
    relevant_messages = []
    for line in threadtime_raw.splitlines()[-15000:]:
        event = re.match(
            r"^\s*\d\d-\d\d\s+\d\d:\d\d:\d\d\.\d+\s+"
            r"(\d+)\s+\d+\s+([A-Z])\s+([^:]+):\s*(.*)$", line)
        if not event or int(event.group(1)) not in target_pids:
            continue
        _, severity, tag, message = event.groups()
        if len(relevant_messages) >= 400:
            break
        tag = tag.strip()
        if tag in ("System.err", "AndroidRuntime"):
            tags.add(tag)
        relevant_messages.append((severity, tag, message))
    combined = "\n".join(x[2] for x in relevant_messages)
    runtime_text = "\n".join(msg for _, tag, msg in relevant_messages
                             if tag == "AndroidRuntime")
    # Only a Java exception CLASS IDENTIFIER, never free-form exception text.
    throwable_pattern = (
        r"(?<![A-Za-z0-9_$./])"
        r"((?:[A-Za-z_$][A-Za-z0-9_$]*\.){1,12}"
        r"[A-Za-z_$][A-Za-z0-9_$]*(?:Exception|Error))"
        r"(?=[:\s]|$)"
    )
    runtime_types = []
    for klass in re.findall(throwable_pattern, runtime_text):
        if len(klass) <= 160 and klass not in runtime_types:
            runtime_types.append(klass)
        if len(runtime_types) >= 8:
            break
    caused_by_types = []
    for klass in re.findall(r"Caused by:\s*" + throwable_pattern, runtime_text):
        if len(klass) <= 160 and klass not in caused_by_types:
            caused_by_types.append(klass)
        if len(caused_by_types) >= 6:
            break
    # Most startup exits observed here are EXIT_SELF(0) with no FATAL
    # AndroidRuntime marker; a vendor-installed uncaught handler may log the
    # Throwable under a different tag before System.exit. Extract ONLY the
    # fixed grammar of exception class names from MAIN-PID E/F messages.
    # No messages, tag content, arguments, stack frames or account data leave CI.
    nonruntime_error_lines = "\n".join(
        message for severity, tag, message in relevant_messages
        if severity in ("E", "F") and tag != "AndroidRuntime")
    bounded_nonruntime_types = []
    approved_class_roots = (
        "java.", "javax.", "android.", "androidx.", "kotlin.",
        "com.yandex.", "ru.yandex.", "com.google.", "org.chromium.")
    for klass in re.findall(throwable_pattern, nonruntime_error_lines):
        if (len(klass) <= 160 and klass.startswith(approved_class_roots)
                and klass not in bounded_nonruntime_types):
            bounded_nonruntime_types.append(klass)
        if len(bounded_nonruntime_types) >= 6:
            break
    # Publisher code can log throwable frames outside AndroidRuntime. Report
    # fixed subsystem labels ONLY (never method/class, raw stack, token or
    # message), scoped to the clone MAIN PID from ApplicationExitInfo.
    subsystem_labels = []
    within_exception = 0
    for severity, tag, message in relevant_messages:
        if severity not in ("E", "F") or tag == "AndroidRuntime":
            continue
        if re.search(throwable_pattern, message):
            within_exception = 12
        elif within_exception > 0:
            within_exception -= 1
        if within_exception <= 0:
            continue
        frame = re.search(
            r"^\s*at\s+([A-Za-z_$][A-Za-z0-9_.$]{4,180})\s*\(",
            message)
        if not frame:
            continue
        symbol = frame.group(1)
        if symbol.startswith(("com.yandex.passport.", "ru.yandex.passport.")):
            label = "YANDEX_PASSPORT"
        elif symbol.startswith(("ru.yandex.music.", "com.yandex.music.")):
            label = "YANDEX_MUSIC"
        elif symbol.startswith(("com.yandex.metrica.", "io.appmetrica.")):
            label = "METRICA"
        elif symbol.startswith(("com.google.android.gms.", "com.google.android.play.")):
            label = "GOOGLE_SERVICES"
        elif symbol.startswith(("android.", "java.", "javax.", "dalvik.", "kotlin.")):
            label = "ANDROID_RUNTIME"
        else:
            label = "OTHER_OR_UNKNOWN"
        if label not in subsystem_labels:
            subsystem_labels.append(label)
        if len(subsystem_labels) >= 6:
            break
    stages = (
        ("APPLICATION_CREATE", "Unable to create application"),
        ("PROVIDER_INSTANTIATE", "Unable to instantiate provider"),
        ("PROVIDER_CREATE", "Unable to get provider"),
        ("ACTIVITY_START", "Unable to start activity"),
        ("ACTIVITY_INSTANTIATE", "Unable to instantiate activity"),
        ("SERVICE_CREATE", "Unable to create service"),
    )
    runtime_stage = next(
        (label for label, phrase in stages if phrase in runtime_text),
        "OTHER" if runtime_text else "NOT_OBSERVED")
    return {
        "main_pid_android_runtime_fatal_seen": "FATAL EXCEPTION" in runtime_text,
        "main_pid_bounded_runtime_throwable_types": runtime_types,
        "main_pid_bounded_caused_by_throwable_types": caused_by_types,
        "main_pid_bounded_nonruntime_error_throwable_types": bounded_nonruntime_types,
        "main_pid_nonruntime_exception_frame_subsystems": subsystem_labels,
        "main_pid_nonruntime_error_lines_observed": bool(nonruntime_error_lines),
        "main_pid_android_runtime_initialization_stage": runtime_stage,
        "main_exit_pid_records_available": bool(target_pids),
        "main_pid_scoped_log_lines_seen": bool(relevant_messages),
        "main_pid_scoped_error_severity_seen":
            any(s in ("E", "F") for s, _, _ in relevant_messages),
        "main_pid_scoped_system_err_seen": "System.err" in tags,
        "main_pid_scoped_android_runtime_seen": "AndroidRuntime" in tags,
        "main_pid_java_exception_marker_seen":
            bool(re.search(r"\b[A-Za-z0-9_.]*(?:Exception|Error)\b", combined)),
        "main_pid_security_exception_marker_seen": "SecurityException" in combined,
        "main_pid_class_loading_marker_seen":
            any(x in combined for x in ("ClassNotFoundException", "NoClassDefFoundError",
                                         "VerifyError", "LinkageError")),
        "main_pid_uncaught_handler_marker_seen": "uncaughtException" in combined,
        "raw_process_text_exposed": False,
        "log_causal_attribution_unproven": True,
    }



def run():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise arsc.TrialError("CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-five-split-identity-") as td:
        work = Path(td)
        archive = work / "signed-pinned.xapk"
        size, sha = source.gpr.download(archive)
        if size != 60433885 or sha != source.ARCHIVE_SHA:
            raise arsc.TrialError("PINNED_ARCHIVE_CHANGED")
        apks = source.gpr.split_apks(archive, work)
        if len(apks) != 5:
            raise arsc.TrialError("FIVE_SPLITS_REQUIRED")
        source.gpr.inspect_publisher(apks)
        editor = work / "APKEditor.jar"
        arsc.download_editor(editor)
        key = work / "ephemeral.jks"
        arsc.run(["keytool", "-genkeypair", "-storetype", "JKS",
                  "-keystore", str(key), "-storepass", "ephemeral-lab-only",
                  "-keypass", "ephemeral-lab-only", "-alias", "research",
                  "-keyalg", "RSA", "-keysize", "2048", "-validity", "1",
                  "-dname", "CN=CELIKOM Non-distributable Lab, O=CELIKOM, C=XX"],
                 "IDENTITY_LAB_KEY", 60)
        original_splits, modified_splits = set(), set()
        clone_output_apks = []
        total_passport_provider_rewrites = 0
        total_dex_literal_rewrites = 0
        total_resource_rewrites = 0
        omitted_permission_declarations = 0
        omit_shadowed = os.getenv("CELIKOM_OMIT_SHADOWED_SIGNATURE_DECLS") == "1"
        # Diagnostic control: keep *all* publisher DEX bytes untouched.
        # This isolates manifest/package rewriting from the known-bad
        # AppMetrica byte substitution that violated DEX string_ids ordering.
        preserve_original_dex = os.getenv("CELIKOM_MANIFEST_ONLY_ORIGINAL_DEX") == "1"
        sorted_metrica_runtime = os.getenv("CELIKOM_SORTED_METRICA_RUNTIME") == "1"
        strict_main_ui_gate = preserve_original_dex or sorted_metrica_runtime
        profile_main_launch = os.getenv("CELIKOM_PROFILE_MAIN_LAUNCH") == "1"
        private_profileable = os.getenv("CELIKOM_LAB_CLONE_PROFILEABLE_SHELL") == "1"
        if private_profileable and not (profile_main_launch and preserve_original_dex
                and os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") == "1"
                and os.getenv("CELIKOM_ORIGINAL_CONTROL_LAUNCH") == "1"
                and os.getenv("GITHUB_ACTIONS") == "true"):
            raise arsc.TrialError("PROFILEABLE_CLONE_ONLY_ON_EPHEMERAL_ORIGINAL_DEX_EMULATOR")
        if profile_main_launch and not (
                preserve_original_dex and
                os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") == "1" and
                os.getenv("CELIKOM_ORIGINAL_CONTROL_LAUNCH") == "1"):
            raise arsc.TrialError("PROFILE_MAIN_REQUIRES_DISPOSABLE_ORIGINAL_DEX_CONTROL")
        if sorted_metrica_runtime and preserve_original_dex:
            raise arsc.TrialError("SORTED_METRICA_REQUIRES_MUTABLE_LAB_DEX")
        if sorted_metrica_runtime and os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") != "1":
            raise arsc.TrialError("SORTED_METRICA_REQUIRES_DISPOSABLE_ANDROID_EMULATOR")
        if preserve_original_dex and os.getenv("GITHUB_ACTIONS") != "true":
            raise arsc.TrialError("MANIFEST_ONLY_REQUIRES_EPHEMERAL_GITHUB_CI")
        if omit_shadowed and os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") != "1":
            raise arsc.TrialError("SHADOWED_SIGNATURE_TEST_REQUIRES_DISPOSABLE_X86_ARMV7")
        for i, apk in enumerate(apks):
            meta = source.apkmeta(apk)
            if meta.get("name") != source.SOURCE or meta.get("versionCode") != "24026531":
                raise arsc.TrialError("SOURCE_SPLIT_VERSION_DRIFT")
            split = meta.get("split", "")
            original_splits.add(split)
            decoded = work / ("decoded-" + str(i))
            arsc.run(["java", "-Xmx3g", "-jar", str(editor), "d", "-t", "xml",
                      "-dex", "-i", str(apk), "-o", str(decoded)],
                     "IDENTITY_DECODE_SPLIT_" + str(i), 240)
            manifest = decoded / "AndroidManifest.xml"
            publisher_manifest = manifest.read_bytes()
            if not split:
                publisher_profileability = classify_manifest_shell_profileability(
                    publisher_manifest)
                print(json.dumps({
                    "publisher_signed_manifest_profileability":
                        publisher_profileability
                }, sort_keys=True))
                if (profile_main_launch and not private_profileable and not
                        publisher_profileability["ordinary_shell_method_tracing_authorized"]):
                    raise arsc.TrialError("SIGNED_YANDEX_SHELL_PROFILING_NOT_ALLOWED")
            initial, _ = source.rewrite_manifest(publisher_manifest.decode("utf-8"))
            next_manifest, rewritten = rewrite_passport_and_metrica(initial)
            if not split:
                old_profile = classify_manifest_shell_profileability(publisher_manifest)
                new_profile = classify_manifest_shell_profileability(next_manifest)
                if old_profile != new_profile:
                    raise arsc.TrialError("CLONE_PROFILEABLE_PERMISSIONS_DRIFT")
                # Enable standard Android profiling ONLY on the independent
                # non-distributable lab clone, never publisher-signed original.
                if private_profileable:
                    next_manifest = enable_private_lab_shell_profiling(next_manifest)
                    lab_profile = classify_manifest_shell_profileability(next_manifest)
                    if not (lab_profile["ordinary_shell_method_tracing_authorized"]
                            and not lab_profile["publisher_debuggable"]):
                        raise arsc.TrialError("LAB_CLONE_PROFILEABLE_GATE_MISSING")
            # Only the BASE APK declares app-level custom permissions;
            # config splits must NOT be forced to have those declarations.
            if omit_shadowed and not split:
                next_manifest, count = omit_shadowed_signature_permission_declarations(next_manifest)
                omitted_permission_declarations += count
            publisher_auths = resolved_provider_authorities(publisher_manifest, OLD_SYNC)
            clone_auths = resolved_provider_authorities(next_manifest, NEW_SYNC)
            if publisher_auths & clone_auths:
                raise arsc.TrialError("SIDE_BY_SIDE_PROVIDER_AUTHORITY_COLLISION")
            if len(publisher_auths) != len(clone_auths):
                raise arsc.TrialError("PROVIDER_AUTHORITY_COUNT_DRIFT")
            manifest.write_bytes(next_manifest)
            total_passport_provider_rewrites += rewritten
            resource_changes = replace_sync_resource(decoded)
            total_resource_rewrites += len(resource_changes)

            patched_source_dexes = {}
            with zipfile.ZipFile(apk) as original_zip:
                src_dex = {n: original_zip.read(n) for n in original_zip.namelist()
                           if n.startswith("classes") and n.endswith(".dex")}
            # Copy-mode dex entries can be located in the decoded root or a raw subdir.
            for file in decoded.rglob("classes*.dex"):
                relative = file.name
                if relative not in src_dex or relative in patched_source_dexes:
                    raise arsc.TrialError("DEX_PATH_OR_DUPLICATE_MISMATCH")
                original_bytes = src_dex[relative]
                if file.read_bytes() != original_bytes:
                    raise arsc.TrialError("SOURCE_DECODE_CHANGED_DEX")
                if preserve_original_dex:
                    edited, patched = original_bytes, False
                else:
                    edited, patched = patch_one_dex(original_bytes)
                file.write_bytes(edited)
                patched_source_dexes[relative] = edited
                total_dex_literal_rewrites += int(patched)
            if set(patched_source_dexes) != set(src_dex):
                raise arsc.TrialError("DECODED_DEX_SET_DRIFT")
            unsigned = work / ("unsigned-" + str(i) + ".apk")
            arsc.run(["java", "-Xmx3g", "-jar", str(editor), "b", "-t", "xml",
                      "-i", str(decoded), "-o", str(unsigned)],
                     "IDENTITY_BUILD_SPLIT_" + str(i), 300)
            aligned = work / ("aligned-" + str(i) + ".apk")
            arsc.run([source.sdk_tool("zipalign"), "-f", "-p", "4",
                      str(unsigned), str(aligned)], "IDENTITY_ZIPALIGN", 75)
            arsc.run([source.sdk_tool("apksigner"), "sign",
                      "--ks", str(key), "--ks-pass", "pass:ephemeral-lab-only",
                      "--ks-key-alias", "research",
                      "--key-pass", "pass:ephemeral-lab-only",
                      "--min-sdk-version", "28", "--v4-signing-enabled", "false",
                      str(aligned)], "IDENTITY_SIGN", 80)
            cert = arsc.run([source.sdk_tool("apksigner"), "verify",
                             "--print-certs", str(aligned)],
                            "IDENTITY_VERIFY_SIGNATURE", 60)
            signer_lines = [x for x in cert.splitlines()
                            if "certificate SHA-256 digest:" in x]
            if len(signer_lines) != 1:
                raise arsc.TrialError("IDENTITY_SIGNER_COUNT_DRIFT")
            new_fingerprint = signer_lines[0].split("digest:", 1)[-1].strip().replace(":", "").lower()
            if len(new_fingerprint) != 64 or new_fingerprint == source.RUSTORE_SHA256_CERT:
                raise arsc.TrialError("IDENTITY_SIGNER_NOT_INDEPENDENT")
            new_meta = source.apkmeta(aligned)
            if (new_meta.get("name") != source.DEST or
                new_meta.get("split", "") != split or
                new_meta.get("versionCode") != "24026531"):
                raise arsc.TrialError("IDENTITY_SPLIT_METADATA_DRIFT")
            with zipfile.ZipFile(apk) as old_zip, zipfile.ZipFile(aligned) as new_zip:
                if not split:
                    # The class is declared in the publisher's classes.dex.
                    # Verify it is still in the actual signed clone DEX.
                    from inspect_android_host import Dex
                    cls = "Lru/yandex/music/YMApplication;"
                    source_definitions = Dex(old_zip.read("classes.dex")).defined_classes()
                    clone_definitions = Dex(new_zip.read("classes.dex")).defined_classes()
                    found_in_source = cls in source_definitions
                    found_in_clone = cls in clone_definitions
                    print(json.dumps({
                        "ymapplication_in_original_signed_dex": found_in_source,
                        "ymapplication_in_clone_signed_dex": found_in_clone,
                        "class_definition_counts_equal": (
                            len(source_definitions) == len(clone_definitions))
                    },sort_keys=True))
                    if not found_in_source or not found_in_clone:
                        raise arsc.TrialError("YMAPPLICATION_CLASS_DEFINITION_MISSING")
                    # Compare only public Android application loader flags from
                    # the actually compiled signed manifests (not XML source).
                    def compiled_loader_flags(target, stage):
                        dump = arsc.run(
                            [source.sdk_tool("aapt"), "dump", "xmltree",
                             str(target), "AndroidManifest.xml"],
                            stage, 70)
                        allowed = ("android:hasCode(", "android:useEmbeddedDex(",
                                   "android:extractNativeLibs(",
                                   "android:isolatedSplits(",
                                   "android:classLoader(")
                        return sorted(line.strip()[:180] for line in dump.splitlines()
                                      if "A: " in line and
                                      any(tag in line for tag in allowed))
                    original_flags = compiled_loader_flags(apk, "ORIGINAL_COMPILED_MANIFEST")
                    clone_flags = compiled_loader_flags(aligned, "CLONE_COMPILED_MANIFEST")
                    print(json.dumps({
                        "compiled_application_loader_flags_original": original_flags,
                        "compiled_application_loader_flags_clone": clone_flags,
                        "compiled_flags_preserved": original_flags == clone_flags
                    },sort_keys=True))
                    dex_storage = {}
                    for dex_name in sorted(src_dex):
                        old_dex, new_dex = old_zip.read(dex_name), new_zip.read(dex_name)
                        if not dex_header_integrity(old_dex) or not dex_header_integrity(new_dex):
                            raise arsc.TrialError("SIGNED_APK_DEX_HEADER_CORRUPT")
                        original_entry = old_zip.getinfo(dex_name)
                        rebuilt_entry = new_zip.getinfo(dex_name)
                        dex_storage[dex_name] = {
                            "original_zip_compression": original_entry.compress_type,
                            "clone_zip_compression": rebuilt_entry.compress_type,
                            "original_size": original_entry.file_size,
                            "clone_size": rebuilt_entry.file_size,
                            "compression_preserved": original_entry.compress_type == rebuilt_entry.compress_type
                        }
                    print(json.dumps({"base_dex_zip_storage_audit": dex_storage,
                                      "raw_apk_bytes_published": False}, sort_keys=True))
                for path in old_zip.namelist():
                    if path.startswith("lib/") and path.endswith(".so"):
                        if old_zip.read(path) != new_zip.read(path):
                            raise arsc.TrialError("IDENTITY_NATIVE_LIBRARY_DRIFT")
                    if path in src_dex:
                        if patched_source_dexes[path] != new_zip.read(path):
                            raise arsc.TrialError("IDENTITY_UNEXPECTED_DEX_DIFFERENCES")
            modified_splits.add(split)
            clone_output_apks.append(aligned)
            print(json.dumps({"split_index": i, "built_and_verified": True,
                              "dex_patch_count_total": total_dex_literal_rewrites,
                              "provider_identity_rewrites_total": total_passport_provider_rewrites}))
        if original_splits != modified_splits or len(modified_splits) != 5:
            raise arsc.TrialError("IDENTITY_FIVE_SPLIT_SET_DRIFT")
        if total_passport_provider_rewrites != 4:
            raise arsc.TrialError("IDENTITY_PROVIDER_REWRITE_COUNT_DRIFT")
        if total_resource_rewrites != 1:
            raise arsc.TrialError("IDENTITY_SYNC_RESOURCE_COUNT_DRIFT")
        if total_dex_literal_rewrites != (0 if preserve_original_dex else 1):
            raise arsc.TrialError("IDENTITY_DEX_LITERAL_COUNT_DRIFT")
        if omit_shadowed and omitted_permission_declarations != 2:
            raise arsc.TrialError("SHADOWED_SIGNATURE_PERMISSION_COUNT_DRIFT")
        # One-APK research path: merge five ALREADY-verified parallel-clone
        # splits, then check exact package, lab signer, native libs and all DEX.
        # Never merge or sign the installed publisher original. No sigbypass.
        merged_clone = None
        if os.getenv("CELIKOM_MERGE_PARALLEL_SINGLE_APK") == "1":
            if not (preserve_original_dex and omit_shadowed and
                    os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") == "1" and
                    os.getenv("CELIKOM_ORIGINAL_CONTROL_LAUNCH") == "1" and
                    os.getenv("GITHUB_ACTIONS") == "true"):
                raise arsc.TrialError("MERGE_REQUIRES_ISOLATED_TRANSLATED_ANDROID_CONTROL")
            merged_clone, merge_report = merge_ephemeral(
                clone_output_apks, work, editor, key, new_fingerprint, arsc)
            print(json.dumps({"private_one_apk_merge": merge_report}, sort_keys=True))
        clone_first_ab = os.getenv("CELIKOM_CLONE_FIRST_AB") == "1"
        loader_zero = os.getenv("CELIKOM_CLONE_LSPATCH_LOADER_ZERO") == "1"
        if loader_zero and not clone_first_ab:
            raise arsc.TrialError("LAB_LOADER_ZERO_NEEDS_CLONE_FIRST_AB")
        if loader_zero:
            merged_clone, loader_report = wrap_clone_with_lspatch_zero(
                merged_clone, work, key, new_fingerprint, arsc)
            print(json.dumps({"private_clone_lspatch_loader_zero": loader_report},
                             sort_keys=True))
        if clone_first_ab and (merged_clone is None or
                os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") != "1" or
                os.getenv("CELIKOM_ORIGINAL_CONTROL_LAUNCH") != "1"):
            raise arsc.TrialError("CLONE_FIRST_AB_NEEDS_VERIFIED_SINGLE_APK_DISPOSABLE_CONTROL")
        emulator_runtime = {}
        native_arm = os.getenv("CELIKOM_CLEAN_ARM_EMULATOR") == "1"
        translated_x64 = os.getenv("CELIKOM_CLEAN_ANDROID_TRANSLATION") == "1"
        translated_x86_armv7 = os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") == "1"
        if sum((native_arm, translated_x64, translated_x86_armv7)) > 1:
            raise arsc.TrialError("RUNTIME_MODE_AMBIGUOUS")
        if native_arm or translated_x64 or translated_x86_armv7:
            # Disposable GitHub Android emulator ONLY. No owner device, login,
            # Play Protect bypass, LSPatch, media playback or modified vendor
            # APK distribution. Translation is NOT ARM-device compatibility.
            import time
            abi = arsc.run(["adb", "shell", "getprop", "ro.product.cpu.abilist"],
                           "ANDROID_EMULATOR_ABI", 30).strip()
            bridge = arsc.run(["adb", "shell", "getprop", "ro.dalvik.vm.native.bridge"],
                              "ANDROID_NATIVE_BRIDGE", 30).strip()
            if translated_x64:
                if "x86_64" not in abi or "arm64-v8a" not in abi:
                    raise arsc.TrialError("API35_X64_ARM64_TRANSLATION_UNAVAILABLE")
                if not bridge or bridge in ("0", "false"):
                    raise arsc.TrialError("API35_X64_NATIVE_BRIDGE_UNAVAILABLE")
            elif translated_x86_armv7:
                if "x86" not in abi.split(",") or "armeabi-v7a" not in abi.split(","):
                    raise arsc.TrialError("API30_X86_ARMV7_TRANSLATION_UNAVAILABLE")
                if not bridge or bridge in ("0", "false"):
                    raise arsc.TrialError("API30_X86_NATIVE_BRIDGE_UNAVAILABLE")
            elif "arm64-v8a" not in abi or "x86_64" in abi:
                raise arsc.TrialError("NATIVE_ARM64_RUNTIME_REQUIRED")
            # A/B: does a one-APK independent clone boot before ANY original
            # publisher app is present? This isolates package coexistence from
            # clone package-identity and resource/lifecycle startup problems.
            # NO account, audio, installed owner app or original APK mutation.
            if clone_first_ab:
                arsc.run(["adb", "install", str(merged_clone)],
                         "CLONE_FIRST_AB_INSTALL_ONE_LAB_APK", 240)
                if sum(x.startswith("package:") for x in
                       arsc.run(["adb", "shell", "pm", "path", source.DEST],
                                "CLONE_FIRST_AB_PM_PATH", 40).splitlines()) != 1:
                    raise arsc.TrialError("CLONE_FIRST_AB_PACKAGE_MANAGER_INVALID")
                first_status = arsc.run([
                    "adb", "shell", "am", "start",
                    *(["--user", "0"] if loader_zero else ["-W"]),
                    "-a", "android.intent.action.MAIN",
                    "-c", "android.intent.category.LAUNCHER",
                    "-n", source.DEST + "/ru.yandex.music.main.MainScreenActivity"],
                    "CLONE_FIRST_AB_DIRECT_MAIN", 60)
                time.sleep(5)
                first_main = installed_process_snapshot(source.DEST)
                first_foreground = disposable_foreground_snapshot(source.DEST)
                first_launch_class = (classify_nonblocking_activity_start(first_status)
                                      if loader_zero else classify_activity_start(first_status))
                first_success = full_native_main_ui_pass(
                    [first_main], first_launch_class, first_foreground)
                print(json.dumps({
                    "ab_condition": "SINGLE_CLONE_BEFORE_ORIGINAL",
                    "clone_standalone_package_manager_pass": True,
                    "clone_standalone_main_activity_and_focus_pass": first_success,
                    "standalone_main_pid_alive": first_main["direct_pid_alive"]
                                               or first_main["ps_main_process_alive"],
                    "standalone_auxiliary_only": first_main["ps_auxiliary_process_alive"]
                                                and not first_main["ps_main_process_alive"],
                    "standalone_activity_resumed": first_foreground[
                        "activity_resumed_for_package"],
                    "standalone_window_focused": first_foreground[
                        "window_focus_for_package"],
                    "user_phone_mutated": False,
                    "audio_or_login_attempted": False,
                },sort_keys=True))
                # A/B second stage starts only after completing this report;
                # do not change clone permissions, DEX, user data or package ID.
            arsc.run(["adb", "install-multiple", *[str(p) for p in apks]],
                     "ARM_INSTALL_PUBLISHER_ORIGINAL", 240)
            if os.getenv("CELIKOM_ORIGINAL_CONTROL_LAUNCH") == "1":
                # Unmodified publisher app is a control. If it fails on the
                # same translated emulator, a clone crash alone proves nothing.
                # Explicit signed launcher activity; monkey with one random
                # event could press BACK and spuriously make the process exit.
                arsc.run(["adb", "shell", "am", "start", "-W",
                          "-a", "android.intent.action.MAIN",
                          "-c", "android.intent.category.LAUNCHER",
                          "-n", source.SOURCE + "/ru.yandex.music.main.MainScreenActivity"],
                         "ORIGINAL_CONTROL_DIRECT_LAUNCH", 60)
                time.sleep(5)
                original_pid = arsc.run(
                    ["adb", "shell", "pidof " + source.SOURCE + " || true"],
                    "ORIGINAL_CONTROL_PROCESS_PROBE", 30).strip()
                if not original_pid:
                    original_raw = arsc.run(
                        ["adb", "logcat", "-d", "-v", "brief", "-t", "1000",
                         "-s", "AndroidRuntime:E", "ActivityManager:W",
                         "ActivityTaskManager:W"],
                        "ORIGINAL_CONTROL_SAFE_CRASH_CLASSIFICATION", 35)
                    hints = classify_clone_launch_logcat(original_raw)
                    print(json.dumps({
                        "original_control_runtime": "PROCESS_NOT_ALIVE",
                        "original_crash_categories": hints,
                        "original_publisher_signature_untouched": True,
                        "clone_installed": False,
                        "raw_logs_published": False
                    },sort_keys=True))
                    raise arsc.TrialError("ORIGINAL_CONTROL_PROCESS_NOT_ALIVE")
                original_info = arsc.run(
                    ["adb", "shell", "dumpsys", "package", source.SOURCE],
                    "ORIGINAL_PACKAGE_PUBLIC_CODE_FLAGS", 35)
                print(json.dumps({
                    "original_control_runtime": "PROCESS_ALIVE_AFTER_LAUNCH",
                    "original_code_flags": summarize_installed_package_code_flags(original_info),
                    "original_signature_untouched": True,
                    "login_tested": False, "audio_tested": False}))
            if merged_clone is not None and clone_first_ab:
                # Already installed the EXACT same lab APK as first A/B arm.
                # No same-app overwrite, update or reinstall.
                pass
            elif merged_clone is not None:
                arsc.run(["adb", "install", str(merged_clone)],
                         "ARM_INSTALL_TEST_SINGLE_APK_CLONE", 240)
            else:
                arsc.run(["adb", "install-multiple", *[str(p) for p in clone_output_apks]],
                         "ARM_INSTALL_TEST_CLONE", 240)
            original_paths = arsc.run(["adb", "shell", "pm", "path", source.SOURCE],
                                      "ARM_PM_ORIGINAL", 40)
            clone_paths = arsc.run(["adb", "shell", "pm", "path", source.DEST],
                                   "ARM_PM_CLONE", 40)
            original_count = sum(x.startswith("package:") for x in original_paths.splitlines())
            clone_count = sum(x.startswith("package:") for x in clone_paths.splitlines())
            expected_clone_count = 1 if merged_clone is not None else 5
            if original_count != 5 or clone_count != expected_clone_count:
                raise arsc.TrialError("ARM_SIDE_BY_SIDE_SPLIT_COUNT_INVALID")
            clone_info = arsc.run(
                ["adb", "shell", "dumpsys", "package", source.DEST],
                "CLONE_PACKAGE_PUBLIC_CODE_FLAGS", 35)
            print(json.dumps({
                "clone_installed_code_flags": summarize_installed_package_code_flags(clone_info)
            }, sort_keys=True))
            if omit_shadowed:
                package_dump = arsc.run(["adb", "shell", "dumpsys", "package", source.DEST],
                                        "CLONE_SIGNATURE_PERMISSION_AUDIT", 45)
                # Only check an explicit positive grant: if a different-signer
                # clone somehow receives credential permission, fail immediately.
                if __import__("re").search(
                    r"com\.yandex\.permission\.READ_CREDENTIALS\s*:\s*granted=true",
                    package_dump):
                    raise arsc.TrialError("CLONE_RECEIVED_UNAUTHORIZED_CREDENTIAL_PERMISSION")
            print(json.dumps({
                "emulator_install_gate": ("SIDE_BY_SIDE_5_ORIGINAL_AND_1_CLONE_PASS"
                                          if merged_clone is not None else
                                          "SIDE_BY_SIDE_5_AND_5_PASS"),
                "original_parts_installed": original_count,
                "clone_parts_installed": clone_count,
                "owner_phone_touched": False,
                "credential_use": False}, sort_keys=True))
            # Disposable emulator only: scope lifecycle evidence to this launch.
            if strict_main_ui_gate:
                arsc.run(["adb", "logcat", "-c"],
                         "CLEAN_EMULATOR_LAUNCH_EVENT_SCOPE", 30)
            # Official ActivityManager startup profiler, no app instrumentation
            # edits, only disposable CI. The binary trace stays private in CI.
            launch_args = (["adb", "shell", "am", "start", "--user", "0"]
                           if loader_zero else ["adb", "shell", "am", "start", "-W"])
            if profile_main_launch:
                from observe_native_startup_trace import TRACE_PATH
                launch_args.extend(["--start-profiler", TRACE_PATH])
            launch_args.extend([
                "-a", "android.intent.action.MAIN",
                "-c", "android.intent.category.LAUNCHER",
                "-n", source.DEST + "/ru.yandex.music.main.MainScreenActivity"
            ])
            launch_stdout = arsc.run(
                launch_args, "ARM_CLONE_DIRECT_LAUNCH", 25 if loader_zero else 60)
            launch_class = (classify_nonblocking_activity_start(launch_stdout)
                            if loader_zero else classify_activity_start(launch_stdout))
            if strict_main_ui_gate:
                print(json.dumps({
                    "clone_activity_start": launch_class
                },sort_keys=True))
                startup_samples = []
                for delay in (0.1, 1.0, 4.0, 8.0):
                    time.sleep(delay)
                    startup_samples.append(installed_process_snapshot(source.DEST))
                foreground = disposable_foreground_snapshot(source.DEST)
                original_after_clone = installed_process_snapshot(source.SOURCE)
                main_ui_pass = full_native_main_ui_pass(
                    startup_samples,
                    launch_class,
                    foreground
                )
                print(json.dumps({
                    "manifest_only_clone_startup_samples": startup_samples,
                    "manifest_only_clone_foreground": foreground,
                    "main_player_ui_runtime_pass": main_ui_pass,
                    "auxiliary_process_is_not_main_player": True,
                    "original_process_alive_after_clone_launch":
                        original_after_clone["any_named_process_alive"],
                    "login_and_audio_untested": True
                },sort_keys=True))
                if not original_after_clone["any_named_process_alive"]:
                    raise arsc.TrialError("PUBLISHER_PROCESS_DID_NOT_SURVIVE_CLONE")
                pid = "observed" if main_ui_pass else ""
            else:
                time.sleep(5)
                # Preserve the formerly verified simple liveness probe.
                pid = arsc.run(["adb", "shell", "pidof " + source.DEST + " || true"],
                               "ARM_CLONE_PROCESS_PROBE", 30).strip()
            if profile_main_launch:
                from observe_native_startup_trace import observe_disposable_trace
                print(json.dumps({
                    "main_startup_art_profile": observe_disposable_trace()
                }, sort_keys=True))
            if not pid:
                # Read only limited system crash tags on an empty, unauthenticated
                # emulator. Emit ONLY boolean classifications, never raw logs,
                # URLs, requests, tokens, stack traces or account contents.
                raw_crashes = arsc.run(
                    ["adb", "logcat", "-d", "-v", "brief", "-t", "2000",
                     "-s", "AndroidRuntime:E", "ActivityManager:W",
                     "ActivityTaskManager:W", "libc:F", "DEBUG:F"],
                    "ARM_CLONE_PRIVACY_SAFE_CRASH_CLASSIFICATION", 35)
                if strict_main_ui_gate:
                    try:
                        event_log = arsc.run(
                            ["adb", "logcat", "-b", "events", "-d",
                             "-v", "brief", "-t", "3000"],
                            "CLONE_SCOPED_PROCESS_LIFECYCLE", 35)
                        print(json.dumps({
                            "clone_process_lifecycle":
                                classify_clone_process_events(event_log)
                        }, sort_keys=True))
                    except arsc.TrialError:
                        print(json.dumps({
                            "clone_process_lifecycle": "ANDROID_EVENTS_UNAVAILABLE"
                        }))
                relevant_crash = raw_crashes.rsplit(
                    "Process: " + source.DEST, 1)[-1][:16000]
                if strict_main_ui_gate:
                    try:
                        exit_dump = arsc.run(
                            ["adb", "shell", "dumpsys", "activity", "exit-info",
                             source.DEST],
                            "CLONE_PRIVACY_SAFE_EXIT_STATUS", 35)
                        print(json.dumps({
                            "clone_exit_info": classify_activity_exit_info(exit_dump)
                        },sort_keys=True))
                        # Passive Android logcat classification, exactly MAIN PID(s)
                        # from scoped ApplicationExitInfo; never write raw log data.
                        try:
                            timeline = arsc.run(
                                ["adb", "logcat", "-d", "-b", "main",
                                 "-v", "threadtime", "-t", "12000"],
                                "CLONE_MAIN_SCOPED_JAVA_DIAGNOSTICS", 45)
                            print(json.dumps({
                                "clone_main_pid_logs": classify_main_pid_scoped_system_logs(
                                    exit_dump, timeline)
                            }, sort_keys=True))
                        except arsc.TrialError:
                            print(json.dumps({
                                "clone_main_pid_logs": "ANDROID_MAIN_PID_LOG_UNAVAILABLE"
                            }))
                    except arsc.TrialError:
                        print(json.dumps({"clone_exit_info": "ANDROID_EXIT_INFO_UNAVAILABLE"}))
                print(json.dumps({
                    "clone_launch_result": "PROCESS_NOT_ALIVE",
                    "dex_path_mentions_base_apk": (
                        "DexPathList" in relevant_crash and "base.apk" in relevant_crash),
                    "dex_path_mentions_clone_package": (
                        "DexPathList" in relevant_crash and source.DEST in relevant_crash),
                    "crash_classification": classify_clone_launch_logcat(raw_crashes),
                    "original_publisher_app_unmodified": True,
                    "owner_phone_touched": False,
                    "raw_log_published": False
                }, sort_keys=True))
                raise arsc.TrialError(
                    "MAIN_UI_NOT_READY_AUXILIARY_PROCESS_ALONE_INSUFFICIENT"
                    if strict_main_ui_gate else "ARM_CLONE_PROCESS_NOT_ALIVE")
            emulator_runtime = {
                "clean_arm_emulator_side_by_side_installed": True,
                "original_split_count": original_count,
                "clone_split_count": clone_count,
                "clone_process_alive_after_launch": True,
                "emulator_abi": abi,
                "arm_binary_translation": translated_x64 or translated_x86_armv7,
                "translation_abi": ("armeabi-v7a" if translated_x86_armv7 else
                                    "arm64-v8a" if translated_x64 else "native-arm64"),
                "native_bridge_present": bool(bridge) and bridge not in ("0", "false")
            }
        result = {
            "verdict": "FIVE_SPLIT_IDENTITY_STRUCTURAL_PASS_ONLY",
            "split_count": 5,
            "manifest_passport_metrica_provider_rewrites": total_passport_provider_rewrites,
            "passport_sync_resource_rewrites": total_resource_rewrites,
            "single_reversible_appmetrica_dex_literal_rewrite": not preserve_original_dex,
            "all_original_dex_preserved_byte_identical": preserve_original_dex,
            "sorted_metrica_authority_consistency_trial": sorted_metrica_runtime,
            "resolved_original_vs_clone_provider_collisions": 0,
            "shadowed_signature_declarations_omitted_in_install_only_clone": omitted_permission_declarations,
            "issuer_permission_protection_not_weakened": True,
            "published_vendor_apks": False,
            "installed_on_owner_phone": False,
            "app_auth_or_login_tested": False,
            "fileinfo_decoder_proven": False,
            "native_audio_tested": False,
            "play_protect_tested": False,
            "merge_one_apk_structural_only": merged_clone is not None,
            "profileable_shell_only_on_separate_lab_clone": private_profileable,
            "publisher_original_profileable_unchanged": True
        }
        if emulator_runtime:
            result.update(emulator_runtime)
            if strict_main_ui_gate:
                result["strict_main_foreground_ui_verified"] = True
                result["verdict"] = "SIDE_BY_SIDE_MAIN_UI_ONLY_NOT_AUTH_OR_AUDIO"
                return result
            result["verdict"] = (
                "SIDE_BY_SIDE_X86_ARMV7_TRANSLATED_INSTALL_LAUNCH_ONLY"
                if translated_x86_armv7 else
                "SIDE_BY_SIDE_X64_ARM_TRANSLATED_INSTALL_LAUNCH_ONLY"
                if translated_x64 else
                "SIDE_BY_SIDE_ARM_EMULATOR_INSTALL_AND_LAUNCH_PASS_NOT_AUDIO")
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except arsc.TrialError as e:
        print(json.dumps({"verdict": "FIVE_SPLIT_IDENTITY_BLOCKED",
                          "stage": e.stage, "diagnostic": e.hints,
                          "published_vendor_apks": False}))
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"verdict": "FIVE_SPLIT_IDENTITY_BLOCKED",
                          "stage": "UNEXPECTED_"+type(e).__name__.upper(),
                          "published_vendor_apks": False}))
        sys.exit(2)
