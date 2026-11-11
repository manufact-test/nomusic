#!/usr/bin/env python3
"""Native ARM Android13 LIFECYCLE control of publisher-signed owner 2025 GPR XAPK.

Not a clone, patch, hook, account/DRM test, sound test, signature bypass or
CELIKOM product acceptance. Every original APK split is reauthenticated prior
to native PackageManager session. No Android device outside ephemeral Redroid.
Only fixed and bounded Boolean/enum lifecycle evidence is printed.
"""
from __future__ import annotations
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

from uptodown_2025_gpr_ephemeral_verify import unbundle_candidate,verify_split_set
from publisher_2025_provenance_gate import GateError,private_command

CONTAINER="celikom-native-arm-android13"
PKG="ru.yandex.music"
EXPECTED_XAPK_BYTES=45961661
EXPECTED_XAPK_SHA256="8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053"
VERSION_CODE="24025542"
OBSERVE_SECONDS=75
SAMPLE_SECONDS=3
MAX_SPLITS=20
COMMIT_TIMEOUT=230

def die(reason: str):
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{3,85}", reason):
        reason="PRIVATE_NATIVE_GUEST_ERROR"
    raise RuntimeError(reason)

def host(args: list[str], timeout: int=60):
    return subprocess.run(args,capture_output=True,text=True,errors="replace",
                          timeout=timeout,check=False)

def shell(*args: str, timeout: int=45, success: bool=True) -> str:
    done=host(["docker","exec",CONTAINER,*args],timeout)
    if done.returncode and success:
        die("PRIVATE_NATIVE_DOCKER_COMMAND_FAILED")
    return done.stdout if done.returncode==0 else ""

def verify_guest():
    if (os.getenv("GITHUB_ACTIONS")!="true" or
        os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1" or
        os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic" or
        os.getenv("GITHUB_REF_NAME")!="experiment/android-a1-user-original-gpr-real-arm13-20261111" or
        platform.machine()!="aarch64"):
        die("OWNER_GPR_NATIVE_GUEST_NOT_AUTHORIZED")
    if shell("getprop","sys.boot_completed").strip()!="1":
        die("ANDROID13_NOT_BOOTED")
    if shell("getprop","ro.build.version.sdk").strip()!="33":
        die("ANDROID_API33_REQUIRED")
    abis=set(shell("getprop","ro.product.cpu.abilist").strip().split(","))
    if not {"armeabi-v7a","arm64-v8a"} <= abis or {"x86","x86_64"} & abis:
        die("NATIVE_ARMV7_ARM64_GUEST_REQUIRED")
    if shell("pm","path",PKG,success=False).strip():
        die("PUBLISHER_PACKAGE_ALREADY_PRESENT")
    return {"native_android13_api33":True,"native_arm64_and_armv7":True,
            "original_package_previously_installed":False}

def prepare(apk: Path) -> list[tuple[str,Path]]:
    if (not apk.is_file() or apk.is_symlink()
        or apk.stat().st_size != EXPECTED_XAPK_BYTES):
        die("OWNER_ORIGINAL_ARCHIVE_LENGTH_DRIFT")
    dig=hashlib.sha256()
    with apk.open("rb") as src:
        for chunk in iter(lambda:src.read(1024*1024),b""):
            dig.update(chunk)
    if dig.hexdigest()!=EXPECTED_XAPK_SHA256:
        die("OWNER_ORIGINAL_ARCHIVE_SHA256_DRIFT")
    unbundle=apk.parent/"signed-2025-splits"
    unbundle.mkdir(parents=True,exist_ok=False)
    paths=unbundle_candidate(apk,unbundle)
    if len(paths)!=16:
        die("OWNER_2025_XAPK_SPLIT_COUNT_DRIFT")
    check=verify_split_set(paths)
    if (check["verified_issuer_signed_splits"]!=16 or
        not check["all_apks_cryptographically_signed"] or
        not check["exactly_one_2025_gpr_base_manifest"]):
        die("OWNER_2025_SPLITS_NOT_ISSUER_VERIFIED")
    out=[]
    seen=set()
    for part in paths:
        badging=private_command(["aapt","dump","badging",str(part)])
        line=next((x for x in badging.splitlines() if x.startswith("package:")),"")
        if not re.search(r"\bname='ru\.yandex\.music'\b",line):
            # Check equivalent robust parser, since closing quote is a word boundary gotcha.
            if "name='ru.yandex.music'" not in line:
                die("SIGNED_SPLIT_PACKAGE_MISMATCH")
        if f"versionCode='{VERSION_CODE}'" not in line:
            die("SIGNED_SPLIT_VERSION_CODE_MISMATCH")
        m=re.search(r"\bsplit='([^']+)'",line)
        split=m.group(1) if m else "base"
        if split in seen or not re.fullmatch(r"[A-Za-z0-9_.-]{1,125}",split):
            die("DUPLICATE_OR_INVALID_SIGNED_SPLIT_NAME")
        seen.add(split)
        out.append((split,part))
    if sum(x=="base" for x,_ in out)!=1:
        die("SIGNED_BASE_NOT_UNIQUE")
    return out

def installation_status(out: str) -> str:
    if out.lstrip().startswith("Success"):
        return "INSTALLED"
    for category in (
        "INSTALL_FAILED_NO_MATCHING_ABIS","INSTALL_FAILED_INVALID_APK",
        "INSTALL_FAILED_CONFLICTING_PROVIDER","INSTALL_FAILED_DUPLICATE_PERMISSION",
        "INSTALL_FAILED_SHARED_USER_INCOMPATIBLE","INSTALL_FAILED_MISSING_SPLIT",
        "INSTALL_PARSE_FAILED","INSTALL_FAILED_VERIFICATION_FAILURE",
        "INSTALL_FAILED_UPDATE_INCOMPATIBLE","INSTALL_FAILED_USER_RESTRICTED",
    ):
        if category in out:
            return category
    return "INSTALL_FAILED_OTHER"

def install_original(parts: list[tuple[str,Path]]) -> dict:
    remote=[]
    created_session=None
    try:
        for i,(name,local) in enumerate(parts):
            destination=f"/data/local/tmp/celikom-2025-signed-{i}.apk"
            copy=host(["docker","cp",str(local),f"{CONTAINER}:{destination}"],110)
            if copy.returncode:
                die("SIGNED_ORIGINAL_SPLIT_COPY_FAILED")
            remote.append((name,destination,local.stat().st_size))
        total=sum(x[2] for x in remote)
        created=host(["docker","exec",CONTAINER,"pm","install-create",
                      "--user","0","-S",str(total)],75)
        match=re.search(r"Success:.*\[([0-9]{1,12})\]",created.stdout)
        if created.returncode or not match:
            return {"install_status":"INSTALL_CREATE_FAILED"}
        session=match.group(1)
        created_session=session
        for name,dest,size in remote:
            result=host(["docker","exec",CONTAINER,"pm","install-write",
                         "-S",str(size),session,name,dest],75)
            if result.returncode or not result.stdout.strip().startswith("Success"):
                return {"install_status":"INSTALL_WRITE_FAILED"}
        committed=host(["docker","exec",CONTAINER,"pm","install-commit",session],COMMIT_TIMEOUT)
        status=installation_status(committed.stdout+"\n"+committed.stderr)
        if status=="INSTALLED":
            created_session=None
        return {"install_status":status}
    finally:
        if created_session is not None:
            host(["docker","exec",CONTAINER,"pm","install-abandon",created_session],45)
        for _,dest,_ in remote:
            host(["docker","exec",CONTAINER,"rm","-f",dest],35)

def launch_main() -> dict:
    resolution=shell("cmd","package","resolve-activity","--brief","--user","0",
                     "-a","android.intent.action.MAIN",
                     "-c","android.intent.category.LAUNCHER","-p",PKG,
                     timeout=35)
    candidates=[x.strip() for x in resolution.splitlines()
                if re.fullmatch(r"ru\.yandex\.music/[A-Za-z0-9_.$]+",x.strip())]
    if len(candidates)!=1:
        return {"launch_status":"MAIN_COMPONENT_NOT_RESOLVED"}
    started=host(["docker","exec",CONTAINER,"am","start","--user","0",
                  "-n",candidates[0]],65)
    good=(started.returncode==0 and
          ("Starting:" in started.stdout or "Warning: Activity not started" in started.stdout)
          and "Error:" not in started.stdout and "Exception" not in started.stdout)
    return {"launch_status":"NATIVE_MAIN_ACTIVITY_ACCEPTED" if good else
                            "NATIVE_MAIN_ACTIVITY_REJECTED"}

def observe() -> dict:
    pids=[]
    alive=resumed=focus=0
    for i in range(OBSERVE_SECONDS//SAMPLE_SECONDS):
        time.sleep(SAMPLE_SECONDS)
        current=shell("pidof",PKG,timeout=30,success=False).strip()
        pid=current if re.fullmatch(r"\d+",current) else None
        pids.append(pid)
        alive+=int(pid is not None)
        activity=shell("dumpsys","activity","activities",timeout=40)
        resumed+=int(any(PKG+"/" in x and
                         ("mResumedActivity" in x or "topResumedActivity" in x or
                          "ResumedActivity:" in x) for x in activity.splitlines()))
        if i in (0,OBSERVE_SECONDS//SAMPLE_SECONDS-1):
            window=shell("dumpsys","window","windows",timeout=40,success=False)
            focus+=int(any(PKG+"/" in x and
                           ("mCurrentFocus" in x or "mFocusedApp" in x)
                           for x in window.splitlines()))
    stable=all(p is not None for p in pids) and len(set(pids))==1
    return {
        "observed_seconds":OBSERVE_SECONDS,
        "sample_count":len(pids),
        "main_alive_samples":alive,
        "resumed_activity_samples":resumed,
        "window_focus_first_last_count":focus,
        "same_exact_main_pid_all_samples":stable,
        "main_pid_or_application_data_logged":False,
    }

def run(archive: Path) -> dict:
    runtime=verify_guest()
    parts=prepare(archive)
    report={"verdict":"SIGNED_2025_NATIVE_CONTROL_NOT_YET_PROVEN",
            "original_archive_sha256_verified":True,
            "all_16_unmodified_splits_publisher_signed":True,
            "signed_release":"2025.10.4 #120.1gpr",
            "signed_version_code":VERSION_CODE,
            "split_count":len(parts),
            "original_vendor_bytes_modified":False,
            "independent_celikom_clone_tested":False,
            "account_login_tested":False,"audio_tested":False,
            "drm_or_signature_bypass_attempted":False,
            "play_protect_tested":False,"owner_honor_touched":False,
            **runtime}
    installed=install_original(parts)
    report.update(installed)
    if report["install_status"]!="INSTALLED":
        report["verdict"]="SIGNED_2025_NATIVE_INSTALL_FAILED"
        return report
    count=sum(x.startswith("package:") for x in
              shell("pm","path",PKG).splitlines())
    report["installed_split_count"]=count
    if count!=16:
        report["verdict"]="SIGNED_2025_INSTALLED_SPLIT_COUNT_DRIFT"
        return report
    report.update(launch_main())
    if report["launch_status"]!="NATIVE_MAIN_ACTIVITY_ACCEPTED":
        report["verdict"]="SIGNED_2025_NATIVE_LAUNCH_FAILED"
        return report
    report.update(observe())
    report["verdict"]=(
        "PUBLISHER_SIGNED_2025_GPR_NATIVE_MAIN_STABLE_75S"
        if report["same_exact_main_pid_all_samples"]
          and report["resumed_activity_samples"]==report["sample_count"]
        else "PUBLISHER_SIGNED_2025_GPR_NATIVE_MAIN_NOT_STABLE"
    )
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",required=True,type=Path)
    args=p.parse_args()
    try:
        result=run(args.xapk)
        print(json.dumps(result,sort_keys=True))
        sys.exit(0 if result["verdict"]=="PUBLISHER_SIGNED_2025_GPR_NATIVE_MAIN_STABLE_75S" else 1)
    except (RuntimeError,GateError,OSError,subprocess.TimeoutExpired) as error:
        reason=str(error) if isinstance(error,(RuntimeError,GateError)) else type(error).__name__
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{3,85}",reason):
            reason="SIGNED_2025_PRIVATE_RUNTIME_ERROR"
        print(json.dumps({"verdict":"PUBLISHER_SIGNED_2025_RUNTIME_ABORTED",
          "reason":reason,"no_vendor_bytes_published":True,
          "owner_phone_touched":False,"stage_a":"NO_GO"},sort_keys=True))
        sys.exit(2)
