#!/usr/bin/env python3
"""Repeatable long-lived native Android13 lifecycle A/B, exact owner APK only.

Tests full ChromaSync 3.0.1 versus its byte-identical embedded origin.apk,
unmodified and unsigned by us. No hook injection, account, media, signature
bypass, content dump, artifacts, or owner device. Categorized JSON only.
"""
from __future__ import annotations
import argparse
import json
import os
import platform
import re
import sys
import tempfile
import time
from pathlib import Path

from chromasync_exact_arm13_probe import (
    CLONE_PACKAGE, EXPECTED_SHA256, DockerGuest, package_installed,
    resumed_for_package, sha256_file
)
from chromasync_origin_unwrapped_arm13 import (
    append_read_only_exit_info, extract_exact_nested_origin
)

DURATION_SECONDS = 75
SAMPLE_INTERVAL_SECONDS = 3


def sample_guest(guest: DockerGuest, seconds: int = DURATION_SECONDS,
                 interval: int = SAMPLE_INTERVAL_SECONDS, sleep=time.sleep) -> dict:
    if not seconds or seconds % interval:
        raise RuntimeError("INVALID_BOUNDED_OBSERVATION_WINDOW")
    pids, alive_count, resumed_count, focus_count = [], 0, 0, 0
    for i in range(seconds // interval):
        sleep(interval)
        pid = guest.command("shell", "pidof", CLONE_PACKAGE, timeout=20)
        if pid.returncode not in (0, 1):
            raise RuntimeError("GUEST_PID_QUERY_FAILED")
        value = pid.stdout.strip() if (
            pid.returncode == 0 and re.fullmatch(r"\d+", pid.stdout.strip())
        ) else None
        pids.append(value)
        alive_count += int(value is not None)
        resumed = resumed_for_package(
            guest.shell("dumpsys", "activity", "activities"), CLONE_PACKAGE)
        resumed_count += int(resumed)
        if i in (0, seconds // interval - 1):
            window = guest.shell("dumpsys", "window")
            focus_count += int(any(
                CLONE_PACKAGE in line and
                ("mCurrentFocus=" in line or "mFocusedApp=" in line)
                for line in window.splitlines()
            ))
    stable = len(pids) > 0 and pids[0] is not None and len(set(pids)) == 1
    return {
        "window_seconds": seconds,
        "sample_interval_seconds": interval,
        "sample_count": len(pids),
        "main_pid_present_samples": alive_count,
        "main_activity_resumed_samples": resumed_count,
        "clone_focus_first_last_count": focus_count,
        "same_main_pid_all_samples": stable,
        "main_pid_changed_or_missing": not stable,
        "window_text_or_pids_logged": False,
    }


def run(guest: DockerGuest, outer: Path, variant: str,
        observation_seconds: int, sleep=time.sleep) -> dict:
    if variant not in ("full", "origin"):
        raise RuntimeError("INVALID_VARIANT")
    if (os.getenv("GITHUB_ACTIONS") != "true" or
            os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1" or
            platform.machine() != "aarch64" or
            guest.serial != "127.0.0.1:5555"):
        raise RuntimeError("ONLY_CLEAN_NATIVE_ARM13_CI_ALLOWED")
    if sha256_file(outer) != EXPECTED_SHA256:
        raise RuntimeError("OWNER_APK_SHA256_MISMATCH")
    if guest.shell("getprop", "ro.build.version.sdk").strip() != "33":
        raise RuntimeError("ANDROID13_REQUIRED")
    if guest.shell("getprop", "sys.boot_completed").strip() != "1":
        raise RuntimeError("ANDROID_NOT_BOOTED")
    packages = guest.shell("pm", "list", "packages")
    if package_installed(packages, CLONE_PACKAGE) or package_installed(packages, "ru.yandex.music"):
        raise RuntimeError("ANDROID_GUEST_NOT_CLEAN")

    result = {
        "variant": variant,
        "owner_apk_hash_verified": True,
        "publisher_signature_modified": False,
        "outside_module_installed": False,
        "new_bypass_used": False,
        "user_login_tested": False,
        "audio_tested": False,
        "ui_pixels_tested": False,
        "owner_phone_touched": False,
    }
    if variant == "origin":
        with tempfile.TemporaryDirectory(prefix="celikom-own-ephemeral-origin-") as folder:
            target = Path(folder) / "origin.apk"
            meta = extract_exact_nested_origin(outer, target)
            result["embedded_origin_hash_verified"] = bool(meta.get("original_nested_sha256"))
            result["nested_origin_sha256"] = meta["original_nested_sha256"]
            result["install"] = guest.install([target])
    else:
        result["install"] = guest.install([outer])
    if result["install"] != "INSTALLED":
        result["verdict"] = "INSTALL_FAILED"
        return result
    if not package_installed(guest.shell("pm", "list", "packages"), CLONE_PACKAGE):
        result["verdict"] = "PACKAGE_IDENTITY_MISMATCH"
        return result
    result["launch"] = guest.launch(CLONE_PACKAGE)
    if result["launch"] != "MAIN_LAUNCH_ACCEPTED":
        result["verdict"] = "MAIN_LAUNCH_REJECTED"
        return result
    result.update(sample_guest(guest, observation_seconds, sleep=sleep))
    if not result["same_main_pid_all_samples"]:
        append_read_only_exit_info(guest, result)
    result["verdict"] = (
        "LONG_NATIVE_MAIN_STABLE"
        if result["same_main_pid_all_samples"] and
           result["main_activity_resumed_samples"] == result["sample_count"]
        else "LONG_NATIVE_MAIN_NOT_STABLE"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outer", required=True, type=Path)
    parser.add_argument("--variant", required=True, choices=("full", "origin"))
    parser.add_argument("--seconds", type=int, default=DURATION_SECONDS)
    args = parser.parse_args()
    if args.seconds != DURATION_SECONDS:
        print(json.dumps({"verdict": "BOUNDED_TIME_ONLY"}, sort_keys=True))
        return 2
    try:
        result = run(DockerGuest(), args.outer, args.variant, args.seconds)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["verdict"] == "LONG_NATIVE_MAIN_STABLE" else 1
    except (RuntimeError, OSError) as error:
        print(json.dumps({
            "verdict": "NO_VALID_LIVE_RESULT",
            "error_class": str(error) if isinstance(error, RuntimeError) else type(error).__name__,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
