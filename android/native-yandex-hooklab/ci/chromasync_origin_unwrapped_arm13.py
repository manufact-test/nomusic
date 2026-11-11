#!/usr/bin/env python3
"""NO-MODIFICATION A/B: test nested 2025 Yandex origin.apk WITHOUT ChromaSync shell.

The exact owner-supplied competitor APK is sourced from an UNPUBLISHED draft.
Extract a byte-identical origin.apk ONLY to an ephemeral ARM13 CI guest, no
patching, no LSPatch, no modules, no signature bypass, no account or audio.
This cannot prove the original publisher-signed 2025 host was tested.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import platform
import sys
import tempfile
import zipfile
from pathlib import Path

from chromasync_exact_arm13_probe import (
    CLONE_PACKAGE, EXPECTED_SHA256, DockerGuest,
    package_installed, sha256_file
)

EMBEDDED_NAME = "assets/lspatch/origin.apk"
MAX_ORIGIN_BYTES = 115 * 1024 * 1024


def inspect_nested_origin(data: bytes) -> dict:
    """Structural safeguards; no vendor bytecode content logged or changed."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        dex_names = [
            name for name in names
            if name == "classes.dex" or
            (name.startswith("classes") and name.endswith(".dex") and
             name[7:-4].isdigit())
        ]
        if len(dex_names) != 6 or "AndroidManifest.xml" not in names:
            raise RuntimeError("EXACT_2025_NESTED_HOST_STRUCTURE_MISMATCH")
        if "assets/lspatch/config.json" in names or "assets/lspatch/loader.dex" in names:
            raise RuntimeError("NESTED_ORIGIN_CONTAINS_OUTER_LOADER")
        libs = [x for x in names if x.startswith("lib/") and x.endswith(".so")]
        return {
            "original_nested_dex_count": len(dex_names),
            "original_nested_manifest_present": True,
            "original_nested_native_libs_present": len(libs) > 0,
            "origin_lspatch_loader_embedded": False,
        }


def extract_exact_nested_origin(source: Path, output: Path) -> dict:
    if sha256_file(source) != EXPECTED_SHA256:
        raise RuntimeError("EXACT_OWNER_CHROMASYNC_DIGEST_MISMATCH")
    with zipfile.ZipFile(source) as outer:
        info = outer.getinfo(EMBEDDED_NAME)
        if info.file_size <= 0 or info.file_size > MAX_ORIGIN_BYTES:
            raise RuntimeError("NESTED_HOST_SIZE_OUT_OF_BOUNDS")
        raw = outer.read(info)
    meta = inspect_nested_origin(raw)
    output.write_bytes(raw)
    return {
        **meta,
        "original_nested_apk_bytes": len(raw),
        "original_nested_sha256": hashlib.sha256(raw).hexdigest(),
        "exact_owner_outer_sha_verified": True,
        "nested_content_modified": False,
        "foreign_module_installed": False,
        "new_signature_bypass_applied": False,
    }


def classify_exit_info(text: str) -> dict:
    """Fixed Android ApplicationExitInfo categories for THIS exact MAIN only."""
    import re
    known = {1: "self", 2: "signaled", 3: "low_memory", 4: "crash_java",
             5: "crash_native", 6: "anr", 7: "init_failure", 8: "permission_change",
             9: "resource", 12: "dependency_died"}
    blocks = re.split(
        r"(?im)(?=^\s*(?:ApplicationExitInfo\s*#?\d+|#\d+:\s*ApplicationExitInfo))",
        text
    )
    if len(blocks) == 1:
        blocks = text.splitlines()
    reasons, statuses = set(), set()
    for block in blocks:
        name = re.search(r"\b(?:processName|process|process name)\s*[=:]\s*"
                         r"([A-Za-z0-9_.:]+)", block, re.I)
        if name is None or name.group(1) != CLONE_PACKAGE:
            continue
        for reason in re.findall(r"\breason\s*[=:]\s*(\d{1,2})\b", block, re.I):
            if 0 <= int(reason) <= 16:
                reasons.add(int(reason))
        for status in re.findall(r"\bstatus\s*[=:]\s*(-?\d{1,4})\b", block, re.I):
            if -255 <= int(status) <= 255:
                statuses.add(int(status))
    return {
        "main_exit_info_record_found": bool(reasons),
        "main_exit_reason_" + "self": 1 in reasons,
        "main_exit_reason_crash_java": 4 in reasons,
        "main_exit_reason_crash_native": 5 in reasons,
        "main_exit_reason_init_failure": 7 in reasons,
        "main_exit_reason_anr": 6 in reasons,
        "main_exit_reason_low_memory": 3 in reasons,
        "main_exit_self_status_zero": 1 in reasons and 0 in statuses,
        "main_exit_status_available": bool(statuses),
        "exit_info_available_but_not_main": bool(text.strip()) and not bool(reasons),
        "raw_android_exit_history_shared": False,
    }


def classify_process_events(text: str) -> dict:
    import re
    boundary = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(CLONE_PACKAGE) +
                          r"(?![A-Za-z0-9_.:])")
    tags = ("am_proc_start", "am_proc_died", "am_kill", "am_crash",
            "am_anr", "am_create_activity", "am_resume_activity", "am_destroy_activity")
    flags = {tag + "_main": False for tag in tags}
    for line in text.splitlines()[:6000]:
        if CLONE_PACKAGE not in line or not boundary.search(line):
            continue
        for tag in tags:
            if re.search(r"\b" + tag + r"\b", line):
                flags[tag + "_main"] = True
    return {**flags, "raw_android_event_log_shared": False}


def append_read_only_exit_info(guest: DockerGuest, result: dict) -> None:
    activity = guest.command("shell", "dumpsys", "activity", "exit-info",
                             CLONE_PACKAGE, timeout=30)
    result["exit_info_command_succeeded"] = activity.returncode == 0
    if activity.returncode == 0:
        result.update(classify_exit_info(activity.stdout))
    events = guest.command("shell", "logcat", "-b", "events", "-d", "-t", "500",
                           timeout=30)
    result["android_event_query_succeeded"] = events.returncode == 0
    if events.returncode == 0:
        result.update(classify_process_events(events.stdout))
    crash = guest.command("shell", "logcat", "-b", "crash", "-d",
                          "-v", "threadtime", "-t", "1200", timeout=30)
    result["crash_buffer_query_succeeded"] = crash.returncode == 0
    if activity.returncode == 0 and crash.returncode == 0:
        # Reuse the project's tested, privacy-safe, PID-scoped classifier.
        # Its default target is CELIKOM A1. Retarget ONLY this isolated
        # process for the exact competitor's guest; restore in finally.
        hooklab = str(Path(__file__).resolve().parents[1])
        if hooklab not in sys.path:
            sys.path.insert(0, hooklab)
        import clone_main_crash_buffer as witness
        old_package = witness.CLONE
        try:
            witness.CLONE = CLONE_PACKAGE
            scoped = witness.classify_main_crash_buffer(
                activity.stdout, crash.stdout)
        finally:
            witness.CLONE = old_package
        result["main_crash_diagnostic"] = scoped


def run(source: Path, guest: DockerGuest) -> dict:
    if (os.getenv("GITHUB_ACTIONS") != "true" or
        os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1" or
        platform.machine() != "aarch64" or guest.serial != "127.0.0.1:5555"):
        raise RuntimeError("ONLY_DISPOSABLE_NATIVE_ARM13_CI")
    if guest.shell("getprop", "sys.boot_completed").strip() != "1":
        raise RuntimeError("ANDROID_NOT_BOOTED")
    if guest.shell("getprop", "ro.build.version.sdk").strip() != "33":
        raise RuntimeError("ANDROID_NOT_API33")
    if package_installed(guest.shell("pm", "list", "packages"), CLONE_PACKAGE):
        raise RuntimeError("ANDROID_GUEST_NOT_CLEAN")
    result = {
        "mode": "extracted_nested_origin_2025_only",
        "account_login_tested": False,
        "audio_tested": False,
        "play_protect_tested": False,
        "wrapper_installed": False,
        "owner_device_touched": False,
    }
    with tempfile.TemporaryDirectory(prefix="celikom-owner-exact-unwrapped-") as folder:
        origin = Path(folder) / "origin.apk"
        result.update(extract_exact_nested_origin(source, origin))
        result["origin_install"] = guest.install([origin])
    if result["origin_install"] != "INSTALLED":
        result["verdict"] = "UNWRAPPED_HOST_INSTALL_FAILED"
        return result
    if not package_installed(guest.shell("pm", "list", "packages"), CLONE_PACKAGE):
        result["verdict"] = "UNWRAPPED_HOST_PACKAGE_MISMATCH"
        return result
    result["launch"] = guest.launch(CLONE_PACKAGE)
    if result["launch"] != "MAIN_LAUNCH_ACCEPTED":
        result["verdict"] = "UNWRAPPED_HOST_LAUNCH_FAILED"
        return result
    result.update(guest.observe(CLONE_PACKAGE))
    if not result["main_survives"]:
        append_read_only_exit_info(guest, result)
    result["verdict"] = (
        "UNWRAPPED_2025_HOST_MAIN_SAME_PID_16S"
        if result["main_survives"] and result["activity_resumed_all_samples"]
        else "UNWRAPPED_2025_HOST_MAIN_NOT_SUSTAINED"
    )
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outer", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = run(args.outer, DockerGuest())
        print(json.dumps(result, sort_keys=True))
        return 0 if result["verdict"] == "UNWRAPPED_2025_HOST_MAIN_SAME_PID_16S" else 1
    except (OSError, RuntimeError, zipfile.BadZipFile, KeyError) as error:
        # Fixed-error class and fail closed; never emit vendor strings or paths.
        reason = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(json.dumps({"verdict": "UNWRAPPED_CONTROL_NOT_COMPLETED", "reason": reason}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
