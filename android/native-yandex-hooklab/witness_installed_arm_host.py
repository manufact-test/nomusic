#!/usr/bin/env python3
"""CELIKOM A1 witness: observe an already-installed, separately authorized ARM lab host.

NO INSTALL, NO START, NO UNINSTALL, NO ROOT, NO LOGCAT CLEAR, NO AUDIO MUTATION.
Only whitelisted CELIKOM observer event categories are returned. Raw logs,
account data, media identifiers, URLs and package dumps are never printed or saved.
This does not attest an APK signer, Play Protect, vendor login or audible swap.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

from probe_arm_device import _adb, collect, evaluate

HOST = "ru.yandex.music"
VERSION_CODE = "24026531"
LOG_TAG = "CELIKOM-NativeLab"
CATEGORIES = {
    "module_loaded": "observer: module loaded",
    "package_ready": "observer: package ready",
    "fileinfo_armed": "observer: native file-info converter hooks armed; read-only",
    "source_lifecycle_armed": "observer: exact source lifecycle witness hooks=",
    "reader_methods_armed": "observer: reader chain methods=",
    "fileinfo_conversion": "file-info conversion count=",
    "source_lifecycle_event": "observer: source identity-only factories=",
    "reader_execution_event": "observer: reader executions=",
    "version_or_loader_rejected": "observer: unsupported host version; no hooks",
    "converter_contract_missing": "observer: no exact converter pair; original unaffected",
}


def eligible_post_install(snapshot) -> list[str]:
    """Reuse the existing STRICT preinstall gate; only change installed-host expectation."""
    gate = evaluate(snapshot)
    blockers = [b for b in gate["blockers"]
                if b != "YANDEX_ALREADY_INSTALLED_NO_OVERWRITE"]
    if not snapshot.yandex_installed:
        blockers.append("RESEARCH_HOST_NOT_INSTALLED")
    return blockers


def installed_version(adb) -> bool:
    code, output = adb("shell", "dumpsys", "package", HOST)
    if code:
        return False
    return any(x == VERSION_CODE for x in re.findall(r"\bversionCode=(\d+)", output))


def one_device(adb) -> bool:
    code, output = adb("devices")
    return code == 0 and sum(
        line.endswith("\tdevice") for line in output.splitlines()
    ) == 1


def classify(output: str) -> dict[str, int]:
    """Accept ONLY our fixed tag and category strings, never the raw log message."""
    found = {key: 0 for key in CATEGORIES}
    for line in output.splitlines():
        # Android logcat -v brief: I/CELIKOM-NativeLab( PID): message
        if not re.search(r"[VDIWEF]/" + re.escape(LOG_TAG) + r"\s*\(", line):
            continue
        message = line.partition("):")[2]
        if not message:
            continue
        for key, marker in CATEGORIES.items():
            if marker in message:
                found[key] += 1
    return found


def capture(seconds: int) -> tuple[dict[str, int], str]:
    # -T 1 means follow only the very end of the buffer; startup may already
    # have happened. No -c (clearing device-wide logs), no general logcat.
    command = ["adb", "logcat", "-T", "1", "-v", "brief",
               "-s", LOG_TAG + ":I", "*:S"]
    try:
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
    except OSError:
        return classify(""), "ADB_LOGCAT_UNAVAILABLE"
    try:
        try:
            stdout, _ = proc.communicate(timeout=seconds)
            state = "LOGCAT_ENDED_EARLY"
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                stdout, _ = proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, _ = proc.communicate(timeout=3)
            state = "OBSERVATION_WINDOW_COMPLETE"
        # Never publish, persist or emit stdout: it may contain third-party
        # data despite the tag filter. Fail shut if unexpectedly large.
        if len(stdout.encode("utf-8")) > 262144:
            return classify(""), "LOGCAT_UNEXPECTED_VOLUME_REJECTED"
        return classify(stdout), state
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def report(adb, *, seconds: int, confirmed_spare: bool,
           confirmed_protect: bool, observer=None) -> dict:
    data = {
        "purpose": "A1_NATIVE_ARM_LSPATCH_RUNTIME_WITNESS_ONLY",
        "blocked": True,
        "blockers": [],
        "device_mutations": False,
        "host_installed_by_script": False,
        "play_protect_automatic_attestation": False,
        "original_yandex_signer_verified": False,
        "native_active_decoder_verified": False,
        "native_audio_swap_verified": False,
        "owner_audible_test": False,
    }
    if not confirmed_spare or not confirmed_protect:
        data["blockers"] = ["EXPLICIT_SPARE_AND_PLAY_PROTECT_CONFIRMATION_REQUIRED"]
        return data
    if not one_device(adb):
        data["blockers"] = ["REQUIRE_EXACTLY_ONE_AUTHORIZED_ADB_DEVICE"]
        return data
    try:
        snap = collect(adb)
        problems = eligible_post_install(snap)
        if not installed_version(adb):
            problems.append("EXACT_170GPR_HOST_VERSION_NOT_VERIFIED")
        if problems:
            data["blockers"] = problems
            return data
        data["blocked"] = False
        # No force-stop or launch. Operator plays known test material manually.
        flags, state = observer(seconds) if observer is not None else capture(seconds)
        data["observation"] = state
        data["events"] = flags
        data["module_runtime_observed"] = (
            flags.get("module_loaded", 0) > 0
            or flags.get("package_ready", 0) > 0
            or flags.get("fileinfo_armed", 0) > 0
        )
        data["source_pipeline_activity_observed"] = (
            flags.get("source_lifecycle_event", 0) > 0
            or flags.get("reader_execution_event", 0) > 0
        )
        data["next_gate"] = (
            "REVIEW_HOST_LOADER_OR_VERSION; NO_AUDIO_MUTATION"
            if not data["module_runtime_observed"]
            else "PROVE_ACTIVE_NATIVE_TRACK_EDITION_DECODER_IDENTITY_BEFORE_ANY_SWAP"
        )
    except (RuntimeError, ValueError, subprocess.SubprocessError):
        data["blocked"] = True
        data["blockers"] = ["ADB_PREFLIGHT_FAILED_WITHOUT_DEVICE_MUTATION"]
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-disposable-arm-device", action="store_true")
    parser.add_argument("--confirm-play-protect-on", action="store_true")
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()
    if not 10 <= args.seconds <= 180:
        parser.error("--seconds must be between 10 and 180")
    result = report(_adb, seconds=args.seconds,
                    confirmed_spare=args.confirm_disposable_arm_device,
                    confirmed_protect=args.confirm_play_protect_on)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if result["blocked"] else 0


if __name__ == "__main__":
    sys.exit(main())
