#!/usr/bin/env python3
"""REAL native ARM Android13 publisher-signed original vs OWN unprivileged browser IPC.

The verified 16-publisher-signed APK install is unchanged. The independently
built CELIKOM lab APK only requests a documented PUBLIC MediaBrowserService
connection and reads two booleans. NEVER play/seek/change media or read account.
Raw app logs and APK bytes are held in the disposable runner, not published.
"""
from __future__ import annotations
import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from owner_2025_gpr_arm13_signed_control import (
    prepare, install_original, launch_main, CONTAINER
)

BRANCH="experiment/android-a1-public-browser-foreground-causal-20261112"
OWN_PACKAGE="pro.celikom.a1publicbrowserprobe"
OWN_COMPONENT=OWN_PACKAGE+"/.ProbeActivity"
TAG="CELIKOM_NATIVE_IPC"
ALLOWED={
    "CONNECTED","CONNECTION_REJECTED","CONNECTION_SUSPENDED",
    "TIMEOUT_NO_BROWSER_CALLBACK","PUBLIC_BROWSER_NOT_UNAMBIGUOUS",
    "PLATFORM_PERMISSION_DENIED","PUBLIC_BROWSER_RUNTIME_ERROR",
    "SAFE_RESULT_SERIALIZATION_FAILED",
}

def command(args: list[str], timeout: int=100) -> subprocess.CompletedProcess:
    return subprocess.run(args, text=True, capture_output=True, errors="replace",
                          timeout=timeout, check=False)

def run(xapk: Path, own: Path) -> dict:
    if (os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH
        or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1"
        or platform.machine()!="aarch64"):
        raise ValueError("DISPOSABLE_NATIVE_ARM13_CI_REQUIRED")
    prop=command(["docker","exec",CONTAINER,"getprop","ro.build.version.sdk"],40)
    ready=command(["docker","exec",CONTAINER,"getprop","sys.boot_completed"],40)
    abi=command(["docker","exec",CONTAINER,"getprop","ro.product.cpu.abilist"],40)
    installed_pre=command(["docker","exec",CONTAINER,"pm","path","ru.yandex.music"],40)
    if (prop.stdout.strip()!="33" or ready.stdout.strip()!="1"
        or not {"arm64-v8a","armeabi-v7a"} <= set(abi.stdout.strip().split(","))
        or installed_pre.stdout.strip()):
        raise ValueError("FRESH_NATIVE_ANDROID13_GUEST_REQUIRED")
    if not own.is_file() or own.is_symlink() or own.stat().st_size > 10_000_000:
        raise ValueError("OWN_PROBE_APK_MISSING_OR_TOO_LARGE")
    local=command(["aapt","dump","badging",str(own)],50)
    if local.returncode or ("name='"+OWN_PACKAGE+"'") not in local.stdout:
        raise ValueError("OWN_PROBE_PACKAGE_INVALID")
    source=prepare(xapk)
    installed=install_original(source)
    if installed.get("install_status")!="INSTALLED":
        raise ValueError("PUBLISHER_ORIGINAL_INSTALL_FAILED")
    launcher=launch_main()
    if launcher.get("launch_status")!="NATIVE_MAIN_ACTIVITY_ACCEPTED":
        raise ValueError("PUBLISHER_ORIGINAL_MAIN_START_REJECTED")
    # Existing CI already established real 75s publisher MAIN; do not rerun it.
    time.sleep(6)
    if not command(["docker","exec",CONTAINER,"pidof","ru.yandex.music"],40).stdout.strip():
        raise ValueError("PUBLISHER_NATIVE_MAIN_NOT_ALIVE")
    remote="/data/local/tmp/celikom-owned-browser-only.apk"
    try:
        copied=command(["docker","cp",str(own),f"{CONTAINER}:{remote}"],75)
        if copied.returncode:
            raise ValueError("OWN_PROBE_ANDROID_COPY_FAILED")
        app_installed=command(["docker","exec",CONTAINER,"pm","install",remote],120)
        if app_installed.returncode or not app_installed.stdout.strip().startswith("Success"):
            raise ValueError("OWN_PROBE_PACKAGE_INSTALL_FAILED")
        command(["docker","exec",CONTAINER,"logcat","-c"],30)
        start=command(["docker","exec",CONTAINER,"am","start","--user","0",
                       "-n",OWN_COMPONENT],60)
        if start.returncode or "Error:" in (start.stdout+start.stderr):
            raise ValueError("OWN_PUBLIC_BROWSER_ACTIVITY_START_FAILED")
        # Check that the publisher's native Activity has regained foreground
        # BEFORE our own Service's delayed browser connection starts (3.5s).
        time.sleep(2)
        activity=command(["docker","exec",CONTAINER,"dumpsys","activity","activities"],50)
        pub_resumed=(activity.returncode==0 and any(
            "ru.yandex.music/" in line and
            ("mResumedActivity" in line or "topResumedActivity" in line
             or "ResumedActivity:" in line)
            for line in activity.stdout.splitlines()))
        time.sleep(15)
        logs=command(["docker","exec",CONTAINER,"logcat","-d","-s",
                      TAG+":I","*:S"],60)
        if logs.returncode or len(logs.stdout)>2_000_000:
            raise ValueError("PRIVATE_ANDROID_LOG_CAPTURE_INVALID")
        records=re.findall(r"RESULT (\{[^\r\n]{5,900}\})",logs.stdout)
        if len(records)!=1:
            return {"verdict":"PUBLIC_IPC_NO_SINGLE_SAFE_CALLBACK",
                    "own_activity_launched":True, "callback_count_bounded":min(len(records),10),
                    "stage_a":"NO_GO"}
        event=json.loads(records[0])
        if (event.get("status") not in ALLOWED
            or event.get("native_android_browser_client_executed") is not True
            or type(event.get("public_browser_matches")) is not int
            or not 0 <= event["public_browser_matches"] <= 5
            or event.get("probe_uses_service_not_foreground_activity") is not True
            or event.get("transport_or_custom_commands_sent") is not False
            or event.get("private_media_or_account_read") is not False
            or event.get("before_decoder_source_replacement_proven") is not False):
            raise ValueError("PRIVATE_PROBE_RESULT_SCHEMA_REJECTED")
        return {
            "verdict":("NATIVE_FOREGROUND_NOT_CONFIRMED_INCONCLUSIVE"
                       if not pub_resumed else
                       "GENUINE_PUBLIC_MEDIA_BROWSER_CONNECTED_NO_SOURCE_SWAP_PROOF"
                       if event["status"]=="CONNECTED"
                       else "PUBLIC_MEDIA_BROWSER_NATIVE_CONNECTION_NOT_ESTABLISHED"),
            "publisher_signed_original_native_running":True,
            "publisher_native_activity_resumed_before_ipc":pub_resumed,
            "original_16_apks_issuer_verified_installed":True,
            "own_app_independently_installed":True,
            "native_guest_android_api33":True,
            **event,
            "full_native_celikom_ui_proven":False,
            "source_before_prepare_proven":False,
            "media_changed_or_played":False,
            "owner_phone_touched":False,
            "private_source_or_signed_keys_published":False,
            "stage_a":"NO_GO",
        }
    finally:
        command(["docker","exec",CONTAINER,"rm","-f",remote],25)


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    parser.add_argument("--own",type=Path,required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(run(args.xapk,args.own),sort_keys=True))
        return 0
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
        safe=str(error)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{5,85}",safe):
            safe="PRIVATE_GUEST_IPC_DIAGNOSTIC_FAILED"
        print(json.dumps({"verdict":"REAL_NATIVE_IPC_INCONCLUSIVE",
              "reason":safe,"third_party_bytes_exposed":False,
              "native_stage_a":"NO_GO"},sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())
