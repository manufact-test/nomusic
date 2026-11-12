#!/usr/bin/env python3
"""Actual 2025 owner-uploaded issuer-signed native Yandex vs separately own-key
LSPatch level-2 wrapper. Research only, clean ARM13 guest, never owner handset.

Uses verified 16-split publisher original already privately uploaded in the
unpublished GitHub draft. Resigns 16 synthetic lab copies with own key, wraps
ONLY the lab base with pinned upstream LSPatch level2, installs one package.
No original APK or competitor module modified/distributed, no account/music.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import tempfile
import time
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from clone_lspatch_loader_zero import download_pinned_patcher
from ci.owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    guest, cmd, stop, verified_orig_paths, apk_name, install_clones,
    lab_sdk_tool, ORIGINAL, SPLITS,
)
from ci.owner_2025_same_name_own_key_arm13_control import (
    sign_same_name, observe_main_75_seconds,
)
from ci.owner_2025_paired_issuer_vs_own_signer_arm13 import strict_75s_stable
import clone_native_splits_ephemeral as source

BRANCH = "experiment/android-a1-2025-uploaded-lspatch2-native-arm13-20261112"
CONTAINER = "celikom-native-arm-android13"
SOURCE_VERSION_CODE = "24025542"


def guard_guest() -> None:
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("GITHUB_REPOSITORY") != "manufact-test/nomusic"
            or os.getenv("GITHUB_REF_NAME") != BRANCH
            or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1"
            or platform.machine() != "aarch64"):
        stop("LSPATCH2_ACTUAL_2025_DISPOSABLE_ARM13_REQUIRED")
    if (guest("getprop","sys.boot_completed").stdout.strip() != "1"
            or guest("getprop","ro.build.version.sdk").stdout.strip() != "33"
            or guest("pm","path",ORIGINAL).stdout.strip()):
        stop("LSPATCH2_ACTUAL_2025_FRESH_GUEST_REQUIRED")
    abis=set(guest("getprop","ro.product.cpu.abilist").stdout.strip().split(","))
    if not {"armeabi-v7a","arm64-v8a"} <= abis:
        stop("LSPATCH2_ACTUAL_2025_ABI_INVALID")


def sha_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def code_parity(apk_a: zipfile.ZipFile, apk_b: zipfile.ZipFile) -> bool:
    def hashes(z):
        return {i.filename: hashlib.sha256(z.read(i)).digest()
                for i in z.infolist()
                if re.fullmatch(r"classes[0-9]*\\.dex", i.filename)
                or (i.filename.startswith("lib/") and i.filename.endswith(".so"))}
    a,b=hashes(apk_a),hashes(apk_b)
    return bool(a) and "classes.dex" in a and a == b


def wrap_lab_base(base: Path, work: Path) -> Path:
    key=work/"unique-own-key.jks"
    if not key.is_file():
        stop("LSPATCH2_OWN_EPHEMERAL_SIGNER_NOT_FOUND")
    patcher=work/"own-pinned-upstream-lspatch.jar"
    download_pinned_patcher(patcher)
    directory=work/"private-lab-output"
    directory.mkdir()
    command=[
        "java","-jar",str(patcher),"-k",str(key),"ephemeral-lab-only",
        "own-key","ephemeral-lab-only","-o",str(directory),"-l","2",str(base)
    ]
    done=cmd(command,timeout=400)
    if done.returncode:
        stop("LSPATCH2_PINNED_PATCHER_COULD_NOT_WRAP_2025_BASE")
    outputs=list(directory.glob("*.apk"))
    if len(outputs)!=1 or outputs[0].stat().st_size > 160_000_000:
        stop("LSPATCH2_SINGLE_SIGNED_BASE_NOT_FOUND")
    wrapped=outputs[0]
    if (apk_name(wrapped).get("name")!=ORIGINAL
            or apk_name(wrapped).get("versionCode")!=SOURCE_VERSION_CODE
            or apk_name(wrapped).get("split")):
        stop("LSPATCH2_WRAPPED_BASE_PACKAGE_IDENTITY_CHANGED")
    verified=cmd([lab_sdk_tool("apksigner"),"verify","--verbose","--print-certs",
                  "--min-sdk-version","24",str(wrapped)],timeout=100)
    if verified.returncode:
        stop("LSPATCH2_WRAPPED_BASE_APK_SIGNING_NOT_VALID")
    cert=re.findall(r"Signer #1 certificate SHA-256 digest:\\s*([a-fA-F0-9:]+)",
                    verified.stdout)
    if len(cert)!=1:
        stop("LSPATCH2_WRAPPED_BASE_SIGNER_ABSENT")
    with zipfile.ZipFile(wrapped) as archive, zipfile.ZipFile(base) as original:
        if archive.testzip() is not None:
            stop("LSPATCH2_WRAPPED_BASE_ZIP_CRC_INVALID")
        names=set(archive.namelist())
        if not {"assets/lspatch/config.json","assets/lspatch/origin.apk",
                "assets/lspatch/loader.dex","classes.dex"} <= names:
            stop("LSPATCH2_REQUIRED_BOOTSTRAP_MISSING")
        cfg=json.loads(archive.read("assets/lspatch/config.json"))
        if (type(cfg.get("sigBypassLevel")) is not int or
                cfg["sigBypassLevel"]!=2 or
                cfg.get("useManager") is not False):
            stop("LSPATCH2_CONFIG_LEVEL_OR_MANAGER_DRIFT")
        if any(n.startswith("assets/lspatch/modules/") for n in names):
            stop("LSPATCH2_NO_EXTERNAL_MODULES_IN_CAUSAL_CONTROL")
        from io import BytesIO
        nested=archive.read("assets/lspatch/origin.apk")
        with zipfile.ZipFile(BytesIO(nested)) as origin:
            if not code_parity(origin,original):
                stop("LSPATCH2_NESTED_2025_HOST_CODE_DRIFT")
    return wrapped


def run(xapk: Path) -> dict:
    guard_guest()
    with tempfile.TemporaryDirectory(prefix="celikom-2025-lspatch2-causal-") as tmp:
        root=Path(tmp)
        original=verified_orig_paths(xapk,root)
        own,signer=sign_same_name(original,root)
        base=[(name,p) for name,p in own if name=="base"]
        if len(original)!=SPLITS or len(own)!=SPLITS or len(base)!=1:
            stop("LSPATCH2_2025_SOURCE_SPLIT_INVARIANT")
        result={
            "source":"USER_UPLOADED_PUBLISHER_SIGNED_2025_120_1GPR",
            "original_splits_publisher_verified":16,
            "lab_splits_independently_signed":16,
            "independent_lab_signer":True,
            "LSPatch_signature_compat_level":2,
            "original_publisher_apks_modified":False,
            "third_party_binary_published":False,
            "owner_phone_touched":False,
            "account_or_audio_tested":False,
            "stage_a":"NO_GO",
        }
        issuer_parts=[(apk_name(p).get("split","") or "base",p) for p in original]
        result["issuer_install"]=install_clones(issuer_parts)
        if result["issuer_install"]!="INSTALLED":
            result["verdict"]="2025_PUBLISHER_NATIVE_BASELINE_INSTALL_FAILED"
            return result
        result["issuer_native_75s"]=strict_75s_stable(observe_main_75_seconds())
        if not result["issuer_native_75s"]:
            result["verdict"]="2025_PUBLISHER_NATIVE_BASELINE_LIFECYCLE_FAILED"
            return result
        uninstall=guest("pm","uninstall","--user","0",ORIGINAL,timeout=90)
        if uninstall.returncode or not uninstall.stdout.startswith("Success"):
            stop("LSPATCH2_PUBLISHER_UNINSTALL_FAILED")
        for _ in range(15):
            if not guest("pm","path",ORIGINAL).stdout.strip() and not guest("pidof",ORIGINAL).stdout.strip():
                break
            time.sleep(1)
        if guest("pm","path",ORIGINAL).stdout.strip():
            stop("LSPATCH2_2025_PUBLISHER_STILL_INSTALLED")
        result["original_cleanly_uninstalled_in_disposable_guest"]=True
        wrapped=wrap_lab_base(base[0][1],root)
        result["owned_lspatch2_base_verified"]=True
        lab=[(name,wrapped if name=="base" else p) for name,p in own]
        result["lab_install"]=install_clones(lab)
        if result["lab_install"]!="INSTALLED":
            result["verdict"]="2025_INDEPENDENT_LSPATCH2_SPLITS_INSTALL_FAILED"
            return result
        result["independent_16_installed"]=sum(
            1 for line in guest("pm","path",ORIGINAL).stdout.splitlines()
            if line.startswith("package:"))==SPLITS
        if not result["independent_16_installed"]:
            result["verdict"]="2025_INDEPENDENT_LSPATCH2_SPLIT_SET_INVALID"
            return result
        guest("logcat","-c",timeout=35)
        observed=observe_main_75_seconds()
        result["independent_native_75s"]=strict_75s_stable(observed)
        if not result["independent_native_75s"]:
            result["own_key_main_exit_category"]=observed.get("exit_status",{})
            result["own_key_main_crash_category"]=observed.get("main_crash_category",{})
        result["verdict"]=(
            "2025_INDEPENDENT_LSPATCH2_MAIN_LIFECYCLE_PASS_NO_AUDIO"
            if result["independent_native_75s"]
            else "2025_INDEPENDENT_LSPATCH2_MAIN_STILL_NO_GO")
        return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    a=parser.parse_args()
    try:
        print(json.dumps(run(a.xapk),sort_keys=True))
    except Exception as error:
        code=str(error)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",code):
            code="LSPATCH2_PRIVATE_NATIVE_ARM13_ERROR"
        print(json.dumps({"verdict":"2025_INDEPENDENT_LSPATCH2_TEST_ABORTED",
                          "reason":code,"stage_a":"NO_GO",
                          "third_party_apk_uploaded":False,
                          "owner_phone_touched":False},sort_keys=True))
        sys.exit(2)
    sys.exit(0 if run is None else 0)
