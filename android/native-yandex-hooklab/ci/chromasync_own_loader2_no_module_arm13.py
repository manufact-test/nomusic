#!/usr/bin/env python3
"""Native A/B: owner-provided ChromaSync NESTED host + our pinned upstream LSPatch L2, NO module.

Exact competitor's *outer* APK already worked on ARM13. Its naked embedded host
failed. This independent third variant matches only the public LSPatch wrapper
and sig level 2, without any foreign module or competitor outer executable.
The nested host is a third-party clone, never a publisher signed pristine source.
No release, account access, music, personal device, or binary output artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from clone_lspatch_loader_zero import download_pinned_patcher
from chromasync_exact_arm13_probe import (
    CLONE_PACKAGE, EXPECTED_SHA256, DockerGuest, package_installed, sha256_file
)
from chromasync_origin_unwrapped_arm13 import (
    extract_exact_nested_origin, append_read_only_exit_info
)
from chromasync_extended_lifecycle_arm13 import sample_guest

BRANCH="experiment/android-a1-competitor-loader-level2-causal-20261112"
NESTED_SHA256="d54e58c6b7720a2d161758f41ce8d3c08d7d5cc6e9587b3976383ee2f829905b"

def phase(name: str) -> None:
    """Public only predefined stage name; no sensitive process or APK details."""
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{5,65}",name):
        raise RuntimeError("INVALID_SAFE_STAGE")
    print(json.dumps({"private_phase":name},sort_keys=True),flush=True)

def command(args: list[str], timeout: int=120) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, errors="replace",
                          timeout=timeout, check=False)

def checked(args: list[str], error: str, timeout: int=120) -> None:
    result=command(args,timeout)
    if result.returncode: raise RuntimeError(error)

def require_runner(guest: DockerGuest, outer: Path) -> None:
    if (os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH
        or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1"
        or os.getenv("CELIKOM_A1_COMPETITOR_SIG_MIMIC")!="1"
        or platform.machine()!="aarch64"
        or guest.serial!="127.0.0.1:5555"):
        raise RuntimeError("COMPETITOR_ONLY_DISPOSABLE_NATIVE_ARM13")
    if sha256_file(outer)!=EXPECTED_SHA256:
        raise RuntimeError("COMPETITOR_EXACT_SHA256_DRIFT")
    if guest.shell("getprop","sys.boot_completed").strip()!="1" or \
            guest.shell("getprop","ro.build.version.sdk").strip()!="33" or \
            package_installed(guest.shell("pm","list","packages"),CLONE_PACKAGE):
        raise RuntimeError("COMPETITOR_NATIVE_FRESH_GUEST_REQUIRED")

def make_owned_wrapper(source: Path, work: Path) -> Path:
    key=work/"independent-celikom-research.jks"
    checked(["keytool","-genkeypair","-noprompt","-storetype","JKS",
             "-keystore",str(key),"-storepass","ephemeral-lab-only",
             "-keypass","ephemeral-lab-only","-alias","research",
             "-keyalg","RSA","-keysize","2048","-validity","1",
             "-dname","CN=CELIKOM Ephemeral Loader Control, O=CELIKOM, C=XX"],
            "OWN_LSPATCH_L2_KEY_CREATE_FAILED",80)
    phase("LAB_KEY_READY")
    jar=work/"upstream-pinned-lspatch-v1.2.jar"
    download_pinned_patcher(jar)
    phase("PINNED_PATCHER_READY")
    output=work/"level2-output"
    output.mkdir()
    checked(["java","-jar",str(jar),
             "-k",str(key),"ephemeral-lab-only","research","ephemeral-lab-only",
             "-o",str(output),"-l","2",str(source)],
            "OWN_LSPATCH_L2_UPSTREAM_PATCH_FAILED",600)
    phase("PATCHER_RETURNED")
    candidates=list(output.glob("*.apk"))
    if len(candidates)!=1:
        raise RuntimeError("OWN_LSPATCH_L2_OUTPUT_NOT_SINGLE_APK")
    target=candidates[0]
    with zipfile.ZipFile(target) as z:
        names=z.namelist()
        if "assets/lspatch/config.json" not in names or \
           "assets/lspatch/origin.apk" not in names:
            raise RuntimeError("OWN_LSPATCH_L2_CONFIG_OR_ORIGIN_MISSING")
        cfg=json.loads(z.read("assets/lspatch/config.json"))
        if cfg.get("sigBypassLevel")!=2 or cfg.get("useManager") is not False:
            raise RuntimeError("OWN_LSPATCH_L2_CONFIGURATION_DIFFERENT")
        if [n for n in names if n.startswith("assets/lspatch/modules/") and n.endswith(".apk")]:
            raise RuntimeError("OWN_LSPATCH_L2_MODULE_NOT_EMPTY")
        nested=z.read("assets/lspatch/origin.apk")
        # Upstream must not silently substitute any foreign proprietary host.
        # If it repacks the nested container, fail closed rather than claim
        # binary equivalence to the owner's uploaded nested input.
        if hashlib.sha256(nested).hexdigest()!=NESTED_SHA256:
            raise RuntimeError("OWN_LSPATCH_L2_ORIGIN_BYTE_IDENTITY_DRIFT")
    manifest=command(["aapt","dump","badging",str(target)],50)
    if manifest.returncode or ("name='"+CLONE_PACKAGE+"'") not in manifest.stdout:
        raise RuntimeError("OWN_LSPATCH_L2_OUTER_PACKAGE_MISMATCH")
    verified=command(["apksigner","verify","--verbose",str(target)],100)
    if verified.returncode:
        raise RuntimeError("OWN_LSPATCH_L2_SIGNATURE_VERIFY_FAILED")
    phase("WRAPPER_VERIFIED")
    return target

def run(outer: Path) -> dict:
    guest=DockerGuest()
    require_runner(guest,outer)
    phase("ANDROID_GUEST_READY")
    with tempfile.TemporaryDirectory(prefix="celikom-third-arm13-variant-") as td:
        work=Path(td)
        nested=work/"exact-third-party-nested-origin.apk"
        metadata=extract_exact_nested_origin(outer,nested)
        phase("NESTED_ORIGIN_EXTRACTED")
        if metadata["original_nested_sha256"]!=NESTED_SHA256:
            raise RuntimeError("COMPETITOR_NESTED_BYTE_IDENTITY_DRIFT")
        wrapped=make_owned_wrapper(nested,work)
        phase("OWN_WRAPPER_READY")
        installed=guest.install([wrapped])
        phase("PM_INSTALL_RETURNED")
        result={
          "experiment":"SAME_NESTED_ORIGIN_OWN_UPSTREAM_LSPATCH_L2_WITHOUT_MODULE",
          "exact_owner_full_apk_sha_verified":True,
          "nested_original_sha256_verified":True,
          "independent_own_app_signing":True,
          "upstream_lspatch_pinned_sha256":True,
          "one_integrated_apk":True,
          "module_count":0,
          "sigBypassLevel":2,
          "original_chromasync_outer_binary_used":False,
          "original_competitor_module_used":False,
          "owner_phone_touched":False,
          "account_login_or_audio_tested":False,
          "no_binary_exported":True,
          "stage_a":"NO_GO",
          "install":installed
        }
        if installed!="INSTALLED":
            result["verdict"]="THIRD_VARIANT_OWN_LSPATCH2_INSTALL_NO_GO"
            return result
        result["launch"]=guest.launch(CLONE_PACKAGE)
        if result["launch"]!="MAIN_LAUNCH_ACCEPTED":
            result["verdict"]="THIRD_VARIANT_OWN_LSPATCH2_LAUNCH_REJECTED"
            return result
        result.update(sample_guest(guest,75))
        if not result["same_main_pid_all_samples"]:
            append_read_only_exit_info(guest,result)
        result["verdict"]=(
          "THIRD_VARIANT_OWN_LSPATCH2_NATIVE_MAIN_STABLE_75S"
          if result["same_main_pid_all_samples"] and
          result["main_activity_resumed_samples"]==25
          else "THIRD_VARIANT_OWN_LSPATCH2_NATIVE_MAIN_NOT_STABLE")
        return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--outer",type=Path,required=True)
    args=ap.parse_args()
    try:
        result=run(args.outer)
        print(json.dumps(result,sort_keys=True))
        sys.exit(0 if result["verdict"]=="THIRD_VARIANT_OWN_LSPATCH2_NATIVE_MAIN_STABLE_75S" else 1)
    except Exception as exc:
        reason=str(exc)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{5,95}",reason):
            reason="THIRD_VARIANT_PRIVATE_LAB_ERROR"
        print(json.dumps({"verdict":"THIRD_VARIANT_NOT_COMPLETED",
            "reason":reason,"error_class":type(exc).__name__,"stage_a":"NO_GO",
            "competitor_or_source_apk_published":False,
            "owner_phone_touched":False},sort_keys=True))
        sys.exit(2)
