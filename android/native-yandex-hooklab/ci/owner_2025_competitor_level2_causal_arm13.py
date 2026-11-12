#!/usr/bin/env python3
"""Disposable native ARM13: independent own-signed 2025 base wrapped in upstream LSPatch.

Reproduce only the published loader/config mechanism found in user-uploaded
ChromaSync; never embed/copy its module, APK, signer, data, or credentials.
The immutable original 16 signed APKs are verified but NEVER patched.
All own-key intermediate binaries and embedded lab APK erased with guest.
Do not call this a working CELIKOM Android sound swap or consumer product.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import re
import sys
import tempfile
import zipfile
from pathlib import Path

from clone_lspatch_loader_zero import download_pinned_patcher
from owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    guest, install_clones, verified_orig_paths, apk_name, ORIGINAL, SPLITS,
    stop, lab_sdk_tool, source, cmd
)
from owner_2025_same_name_own_key_arm13_control import (
    sign_same_name, observe_main_75_seconds
)
from owner_2025_paired_issuer_vs_own_signer_arm13 import strict_75s_stable

BRANCH="experiment/android-a1-competitor-loader-level2-causal-20261112"

def guard() -> None:
    if (os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH
        or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1"
        or os.getenv("CELIKOM_A1_COMPETITOR_SIG_MIMIC")!="1"
        or platform.machine()!="aarch64"):
        stop("LEVEL2_2025_NATIVE_DISPOSABLE_ONLY")
    if (guest("getprop","sys.boot_completed").stdout.strip()!="1"
        or guest("getprop","ro.build.version.sdk").stdout.strip()!="33"
        or guest("pm","path",ORIGINAL).stdout.strip()):
        stop("LEVEL2_2025_GUEST_NOT_FRESH_NATIVE_ARM13")

def patch_base(owned: list[tuple[str,Path]], work: Path) -> list[tuple[str,Path]]:
    base=[p for name,p in owned if name=="base"]
    if len(base)!=1 or len(owned)!=SPLITS:
        stop("LEVEL2_2025_BASE_OR_SPLITS_MISSING")
    key=work/"unique-own-key.jks"
    jar=work/"pinned-upstream-lspatch.jar"
    download_pinned_patcher(jar)
    destination=work/"own-lspatch-level2"
    destination.mkdir()
    source.action(["java","-jar",str(jar),
       "-k",str(key),"ephemeral-lab-only","own-key","ephemeral-lab-only",
       "-o",str(destination),"-l","2",str(base[0])],
       "LEVEL2_2025_UPSTREAM_LOADER_FAILED",600)
    candidates=list(destination.glob("*.apk"))
    if len(candidates)!=1:
        stop("LEVEL2_2025_ONE_WRAPPED_BASE_REQUIRED")
    wrapped=candidates[0]
    with zipfile.ZipFile(wrapped) as z, zipfile.ZipFile(base[0]) as reference:
        if "assets/lspatch/config.json" not in z.namelist() or \
            "assets/lspatch/origin.apk" not in z.namelist():
            stop("LEVEL2_2025_UPSTREAM_WRAPPER_NOT_PRESENT")
        config=json.loads(z.read("assets/lspatch/config.json"))
        if config.get("sigBypassLevel")!=2 or config.get("useManager") is not False:
            stop("LEVEL2_2025_CONFIG_WRONG")
        if any(name.startswith("assets/lspatch/modules/") for name in z.namelist()):
            stop("LEVEL2_2025_FOREIGN_MODULE_FORBIDDEN")
        nested=z.read("assets/lspatch/origin.apk")
        if len(nested)>128*1024*1024:
            stop("LEVEL2_2025_NESTED_TOO_LARGE")
        # LSPatch embeds our already independently signed and renamed lab base
        # only: original publisher source APK is never modified or embedded.
        import io
        with zipfile.ZipFile(io.BytesIO(nested)) as packed:
            for name in reference.namelist():
                if re.fullmatch(r"classes[0-9]*\.dex",name) or name.startswith("lib/"):
                    if packed.read(name)!=reference.read(name):
                        stop("LEVEL2_2025_EMBEDDED_DEX_NATIVE_PARITY_FAILED")
    meta=apk_name(wrapped)
    if meta.get("name")!=ORIGINAL or meta.get("versionCode")!="24025542" or meta.get("split"):
        stop("LEVEL2_2025_WRAPPED_BASE_ID_DRIFT")
    check=cmd([lab_sdk_tool("apksigner"),"verify","--verbose","--print-certs",str(wrapped)],120)
    if check.returncode:
        stop("LEVEL2_2025_WRAPPED_BASE_SIGNATURE_VERIFY_FAILED")
    expected=cmd([lab_sdk_tool("apksigner"),"verify","--verbose","--print-certs",str(base[0])],120)
    pat=r"Signer #1 certificate SHA-256 digest:\s*([a-fA-F0-9:]+)"
    a=re.findall(pat,check.stdout)
    b=re.findall(pat,expected.stdout)
    if len(a)!=1 or len(b)!=1 or a[0].lower()!=b[0].lower():
        stop("LEVEL2_2025_WRAPPED_BASE_NOT_SAME_OWN_SIGNER")
    return [(name,wrapped if name=="base" else apk) for name,apk in owned]

def run(xapk: Path) -> dict:
    guard()
    with tempfile.TemporaryDirectory(prefix="celikom-2025-own-lspatch2-") as tmp:
        work=Path(tmp)
        originals=verified_orig_paths(xapk,work)
        owned,_=sign_same_name(originals,work)
        wrapped=patch_base(owned,work)
        installed=install_clones(wrapped)
        report={
           "experiment":"COMPETITOR_LEVEL2_CONFIG_OWN_SIGNER_UPSTREAM_LOADER",
           "publisher_original_splits_issuer_verified":len(originals)==16,
           "original_publisher_apk_unchanged":True,
           "own_independent_splits":len(wrapped),
           "one_wrapped_base_plus_owned_splits":True,
           "no_competitor_module_binary_or_key_included":True,
           "user_account_or_audio_tested":False,
           "play_protect_tested":False,
           "owner_honor_touched":False,
           "third_party_derived_apk_published":False,
           "stage_a":"NO_GO",
           "install_status":installed,
        }
        if installed!="INSTALLED":
            report["verdict"]="COMPETITOR_LEVEL2_2025_SPLIT_INSTALL_NO_GO"
            return report
        count=sum(s.startswith("package:") for s in
                  guest("pm","path",ORIGINAL).stdout.splitlines())
        report["installed_apk_count"]=count
        if count!=16:
            report["verdict"]="COMPETITOR_LEVEL2_2025_SPLIT_COUNT_DRIFT"
            return report
        guest("logcat","-c")
        obs=observe_main_75_seconds()
        report["native_main"]=obs
        report["verdict"]=("COMPETITOR_LEVEL2_2025_OWN_HOST_MAIN_75S_STABLE"
            if strict_75s_stable(obs) else
            "COMPETITOR_LEVEL2_2025_OWN_HOST_MAIN_NOT_STABLE")
        return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    opts=parser.parse_args()
    try:
        data=run(opts.xapk)
        print(json.dumps(data,sort_keys=True))
        sys.exit(0 if data["verdict"]=="COMPETITOR_LEVEL2_2025_OWN_HOST_MAIN_75S_STABLE" else 1)
    except Exception as exc:
        err=str(exc)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{5,95}",err):
            err="COMPETITOR_LEVEL2_2025_PRIVATE_LAB_FAILURE"
        print(json.dumps({"verdict":"COMPETITOR_LEVEL2_2025_ABORTED",
            "reason":err,"owner_phone_touched":False,
            "publisher_apk_published":False,"stage_a":"NO_GO"},sort_keys=True))
        sys.exit(2)
