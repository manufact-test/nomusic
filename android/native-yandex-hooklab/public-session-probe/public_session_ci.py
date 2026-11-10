#!/usr/bin/env python3
"""CI-only public Media3 capability probe against unmodified signed Yandex.

Never patches/repacks Yandex, signs in, issues playback/playlist commands,
captures metadata, logs tokens or touches a user's primary device.
Only allow a genuine publisher-signed #170gpr host on a disposable emulator.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import clone_native_splits_ephemeral as signed

PACKAGE = "pro.celikom.nativepublicsession"
ACTIVITY = PACKAGE + "/.ProbeActivity"
TAG = "CELIKOMPublicSessionProbe"
STATES = {
    "CONNECTED_READONLY", "CONNECTION_NOT_ESTABLISHED",
    "VERSION_UNPINNED", "NO_PUBLIC_SERVICE", "AMBIGUOUS_SERVICE",
    "PUBLISHER_PACKAGE_MISSING", "PUBLIC_SESSION_PROBE_UNAVAILABLE", "TIMEOUT",
}
PATTERN = re.compile(
    r"PROBE_RESULT state=([A-Z_]+) eligible=([0-9]+)"
    r" connected=(true|false) change_items=(true|false)"
    r" set_item=(true|false) get_item=(true|false)"
    r" play_pause=(true|false) seek=(true|false)"
    r" source_replace_proven=false audio_tested=false"
)


class Blocked(Exception):
    pass


def run(argv: list[str], stage: str, timeout: int = 120) -> str:
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if completed.returncode:
        raise Blocked(stage)
    return completed.stdout


def sanitize_logcat(text: str) -> dict | None:
    for match in PATTERN.finditer(text):
        state, count, connected, change, set_item, get_item, play, seek = match.groups()
        if state not in STATES or int(count) > 8:
            continue
        if connected == "true" and state != "CONNECTED_READONLY":
            continue
        return {
            "state": state,
            "public_service_candidate_count": int(count),
            "media3_session_connected": connected == "true",
            "command_change_media_items_advertised": change == "true",
            "command_set_media_item_advertised": set_item == "true",
            "command_get_current_item_advertised": get_item == "true",
            "command_play_pause_advertised": play == "true",
            "command_seek_advertised": seek == "true",
        }
    return None


def execute() -> dict:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise Blocked("CI_ONLY")
    qemu = run(["adb", "shell", "getprop", "ro.kernel.qemu"], "DEVICE_CHECK", 25).strip()
    if qemu != "1":
        raise Blocked("NOT_DISPOSABLE_EMULATOR")
    apk = HERE / "app/build/outputs/apk/debug/app-debug.apk"
    if not apk.is_file():
        raise Blocked("OWN_PROBE_APK_NOT_BUILT")
    with tempfile.TemporaryDirectory(prefix="celikom-public-session-") as d:
        temp = Path(d)
        archive = temp / "signed-original.xapk"
        length, digest = signed.gpr.download(archive)
        if length != 60433885 or digest != signed.ARCHIVE_SHA:
            raise Blocked("PINNED_ARCHIVE_MISMATCH")
        apks = signed.gpr.split_apks(archive, temp)
        if len(apks) != 5:
            raise Blocked("PUBLISHER_SPLIT_COUNT_DRIFT")
        signed.gpr.inspect_publisher(apks)
        splits = set()
        for p in apks:
            meta = signed.apkmeta(p)
            if meta.get("name") != signed.SOURCE or meta.get("versionCode") != "24026531":
                raise Blocked("PUBLISHER_IDENTITY_DRIFT")
            splits.add(meta.get("split", ""))
        if len(splits) != 5:
            raise Blocked("PUBLISHER_SPLIT_SET_DRIFT")
        run(["adb", "install-multiple", *map(str, apks)],
            "SIGNED_ORIGINAL_INSTALL_BLOCKED", 240)
        run(["adb", "install", str(apk)], "OWN_PROBE_INSTALL_BLOCKED", 120)
        # Do not perform sign-in or media playback. Own Activity queries
        # public SessionToken commands only, with no state changes.
        run(["adb", "logcat", "-c"], "CLEAR_TEST_LOG", 30)
        run(["adb", "shell", "am", "start", "-n", ACTIVITY],
            "OWN_PROBE_LAUNCH_BLOCKED", 30)
        result = None
        for _ in range(15):
            time.sleep(2)
            output = run(["adb", "logcat", "-d", "-s", TAG + ":I", "*:S"],
                         "READ_OWN_LOG_ONLY", 30)
            result = sanitize_logcat(output)
            if result is not None:
                break
        if result is None:
            raise Blocked("PROBE_DID_NOT_REPORT")
    return {
        "verdict": "PUBLIC_ANDROID_MEDIA_SESSION_CAPABILITY_OBSERVED_ONLY",
        "publisher_original_signed_verified": True,
        "original_host_modified": False,
        "owned_companion_only": True,
        "yandex_login_or_account_access": False,
        "track_identity_or_audio_observed": False,
        "source_replacement_proven": False,
        "release_approved": False,
        **result,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(execute(), sort_keys=True))
    except Exception as exc:
        reason = str(exc) if isinstance(exc, Blocked) else "RUNTIME_TEST_UNAVAILABLE"
        print(json.dumps({
            "verdict": "PUBLIC_SESSION_RUNTIME_INCONCLUSIVE",
            "reason": reason,
            "original_host_modified": False,
            "owner_device_touched": False,
            "source_replacement_proven": False,
        }))
        sys.exit(2)
