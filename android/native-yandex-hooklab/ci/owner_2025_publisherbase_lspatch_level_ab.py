#!/usr/bin/env python3
"""TRUE original-signed publisher BASE -> independent LSPatch level 0 vs 2.

This is a private, throwaway ARM Android13 causal test, never a user-facing APK.
The *input* to LSPatch is the verified publisher-signed 2025.10.4 GPR BASE,
not the re-signed own-key copy (otherwise 'originalSignature' = own-key).
All 15 config splits are re-signed with the SAME independent ephemeral key.
No publisher code, content, signing material or accounts are exported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    ORIGINAL, SPLITS, apk_name, cmd, guest, install_clones,
    lab_sdk_tool, stop, verified_orig_paths,
)
from owner_2025_same_name_own_key_arm13_control import (
    sign_same_name, observe_main_75_seconds,
)
from owner_2025_paired_issuer_vs_own_signer_arm13 import strict_75s_stable
from clone_lspatch_loader_zero import (
    download_pinned_patcher, verify_native_loader_elf_offsets,
)
from recover_stored_origin_crc import rewrite_only_if_origin_crc_mismatch

BRANCH="experiment/android-a1-2025-publisherbase-lv0-lv2-arm13-20261112"


def clean_native_guest():
    if (os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH
        or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1"
        or platform.machine()!="aarch64"):
        stop("PUBLISHERBASE_LEVEL_AB_DISPOSABLE_ARM13_ONLY")
    if (guest("getprop","sys.boot_completed").stdout.strip()!="1"
        or guest("getprop","ro.build.version.sdk").stdout.strip()!="33"):
        stop("PUBLISHERBASE_LEVEL_AB_GUEST_NOT_BOOTED")
    abis=set(guest("getprop","ro.product.cpu.abilist").stdout.strip().split(","))
    if not {"arm64-v8a","armeabi-v7a"}<=abis:
        stop("PUBLISHERBASE_LEVEL_AB_NATIVE_ABI_MISSING")
    if guest("pm","path",ORIGINAL).stdout.strip():
        stop("PUBLISHERBASE_LEVEL_AB_GUEST_NOT_FRESH")


def apk_cert_digest(path: Path) -> str:
    v=cmd([lab_sdk_tool("apksigner"),"verify","--verbose","--print-certs",
           "--min-sdk-version","24",str(path)],90)
    if v.returncode:
        stop("PUBLISHERBASE_LEVEL_AB_SIGNED_APK_NOT_VERIFIED")
    hits=re.findall(r"Signer #1 certificate SHA-256 digest:\s*([a-fA-F0-9:]+)",
                    v.stdout)
    if len(hits)!=1:
        stop("PUBLISHERBASE_LEVEL_AB_CERT_NOT_SINGLE")
    return hits[0].replace(":","").lower()


def patch_exact_original_base(original_base: Path, key: Path,
                              patcher: Path, work: Path, level: int,
                              owner_cert: str) -> Path:
    if type(level) is not int or level not in (0,2):
        stop("PUBLISHERBASE_LEVEL_AB_UNEXPECTED_LEVEL")
    if apk_cert_digest(original_base)==owner_cert:
        stop("PUBLISHERBASE_LEVEL_AB_INPUT_ALREADY_OWN_SIGNED")
    output=work/("lspatch-originalbase-level"+str(level))
    output.mkdir()
    # Pinned upstream independent patcher; no foreign module or copied code.
    process=cmd(["java","-jar",str(patcher),
                 "-k",str(key),"ephemeral-lab-only","own-key","ephemeral-lab-only",
                 "-o",str(output),"-l",str(level),str(original_base)],500)
    if process.returncode:
        stop("PUBLISHERBASE_LEVEL_AB_PATCH_COMMAND_FAILED")
    built=list(output.glob("*.apk"))
    if len(built)!=1 or built[0].stat().st_size > 115_000_000:
        stop("PUBLISHERBASE_LEVEL_AB_OUTER_APK_INVALID")
    final=built[0]
    rebuilt=work/("repair-"+str(level)+".apk")
    try:
        repaired=rewrite_only_if_origin_crc_mismatch(final,rebuilt)
    except (zipfile.BadZipFile,ValueError):
        stop("PUBLISHERBASE_LEVEL_AB_CRC_LAYOUT_INVALID")
    if repaired["layout_repacked"]:
        aligned=work/("aligned-"+str(level)+".apk")
        p=cmd([lab_sdk_tool("zipalign"),"-f","-p","4",str(rebuilt),str(aligned)],90)
        if p.returncode:
            stop("PUBLISHERBASE_LEVEL_AB_ZIPALIGN_FAILED")
        p=cmd([lab_sdk_tool("apksigner"),"sign","--ks",str(key),
               "--ks-pass","pass:ephemeral-lab-only","--ks-key-alias","own-key",
               "--key-pass","pass:ephemeral-lab-only","--min-sdk-version","24",
               "--v4-signing-enabled","false",str(aligned)],110)
        if p.returncode:
            stop("PUBLISHERBASE_LEVEL_AB_RESIGN_FAILED")
        final=aligned
    if apk_cert_digest(final)!=owner_cert:
        stop("PUBLISHERBASE_LEVEL_AB_OUTER_SIGNER_MISMATCH")
    meta=apk_name(final)
    if (meta.get("name")!=ORIGINAL or meta.get("versionCode")!="24025542"
        or meta.get("split")):
        stop("PUBLISHERBASE_LEVEL_AB_HOST_PACKAGE_DRIFT")
    try:
        with zipfile.ZipFile(final) as outer:
            cfg=json.loads(outer.read("assets/lspatch/config.json"))
            if (type(cfg.get("sigBypassLevel")) is not int
                or cfg["sigBypassLevel"]!=level
                or cfg.get("useManager") is not False
                or (level == 2 and not cfg.get("originalSignature"))
                or any(x.startswith("assets/lspatch/modules/")
                       for x in outer.namelist())):
                stop("PUBLISHERBASE_LEVEL_AB_CONFIG_INVALID")
            with zipfile.ZipFile(__import__("io").BytesIO(
                    outer.read("assets/lspatch/origin.apk"))) as nested, \
                 zipfile.ZipFile(original_base) as original:
                names=[n for n in original.namelist()
                       if re.fullmatch(r"classes\d*[.]dex",n)
                       or (n.startswith("lib/") and n.endswith(".so"))]
                if not names:
                    stop("PUBLISHERBASE_LEVEL_AB_HOST_PAYLOAD_ABSENT")
                if any(hashlib.sha256(nested.read(n)).digest()
                       !=hashlib.sha256(original.read(n)).digest()
                       for n in names):
                    stop("PUBLISHERBASE_LEVEL_AB_ORIGINAL_HOST_CODE_DRIFT")
    except (KeyError,ValueError,zipfile.BadZipFile):
        stop("PUBLISHERBASE_LEVEL_AB_NESTED_ORIGINAL_INVALID")
    try:
        loader=verify_native_loader_elf_offsets(final)
    except (ValueError,zipfile.BadZipFile):
        stop("PUBLISHERBASE_LEVEL_AB_LOADER_ELF_INVALID")
    if len(loader)!=4:
        stop("PUBLISHERBASE_LEVEL_AB_LOADER_ABI_MISSING")
    print(json.dumps({"verified_wrapped_issuer_original_base":True,
        "sigBypassLevel":level,
        "own_outer_signer_equals_fifteen_other_split_signers":True,
        "embedded_module_count":0,
        "publisher_code_modified":False,
        "source_certificate_preserved_as_wrapped_input":True,
        "third_party_apk_published":False},sort_keys=True))
    return final


def run(original_xapk: Path) -> dict:
    clean_native_guest()
    with tempfile.TemporaryDirectory(prefix="celikom-lspatch-publisherbase-level-ab-") as tmp:
        work=Path(tmp)
        originals=verified_orig_paths(original_xapk,work)
        signed,meta=sign_same_name(originals,work)
        source_base=next((x for x in originals
                          if not apk_name(x).get("split","")),None)
        if source_base is None or len(originals)!=SPLITS or len(signed)!=SPLITS:
            stop("PUBLISHERBASE_LEVEL_AB_SOURCE_SET_INCOMPLETE")
        owned=next((path for name,path in signed if name=="base"),None)
        if owned is None:
            stop("PUBLISHERBASE_LEVEL_AB_OWN_BASE_NOT_FOUND")
        owner_cert=apk_cert_digest(owned)
        if owner_cert==apk_cert_digest(source_base):
            stop("PUBLISHERBASE_LEVEL_AB_OWN_EQUALS_ISSUER")
        key=work/"unique-own-key.jks"
        if not key.is_file():
            stop("PUBLISHERBASE_LEVEL_AB_PRIVATE_KEY_MISSING")
        patcher=work/"lspatch-v1.2-487-pinned.jar"
        try:
            download_pinned_patcher(patcher)
        except (OSError,ValueError):
            stop("PUBLISHERBASE_LEVEL_AB_UPSTREAM_PIN_INVALID")
        # Build BOTH inputs before first installation to isolate runtime.
        wrapped={}
        for level in (0,2):
            wrapped[level]=patch_exact_original_base(
                source_base,key,patcher,work,level,owner_cert)
        source_configs=[(name,path) for name,path in signed if name!="base"]
        if len(source_configs)!=15:
            stop("PUBLISHERBASE_LEVEL_AB_CONFIG_SPLIT_COUNT_DRIFT")
        results={}
        for level in (0,2):
            paths=[("base",wrapped[level]),*source_configs]
            status=install_clones(paths)
            installed=status=="INSTALLED"
            observation=observe_main_75_seconds() if installed else {}
            result={"installed":installed,"installStatus":status,
                    "native_main_75s_stable":strict_75s_stable(observation)
                    if installed else False,
                    "main_exit":observation.get("exit_status",{}),
                    "main_crash":observation.get("main_crash_category",{})}
            results[str(level)]=result
            if level==0 and installed:
                removed=guest("pm","uninstall","--user","0",ORIGINAL,timeout=90)
                if removed.returncode or not removed.stdout.strip().startswith("Success"):
                    stop("PUBLISHERBASE_LEVEL_AB_BASELINE_UNINSTALL_FAILED")
                if guest("pm","path",ORIGINAL).stdout.strip():
                    stop("PUBLISHERBASE_LEVEL_AB_BASELINE_NOT_REMOVED")
        success=results["2"]["native_main_75s_stable"]
        return {"verdict":("PUBLISHERBASE_SIGCOMPAT2_NATIVE_75S_STABLE"
                          if success else "PUBLISHERBASE_SIGCOMPAT2_NOT_PROVEN"),
                "native_arm_android13":True,"real_publisher_signed_2025_source_16":True,
                "publisher_source_original_used_as_lspatch_input":True,
                "same_native_guest_and_lab_signer_between_levels":True,
                "level0":results["0"],"level2":results["2"],
                "no_user_account_media_or_drm_tested":True,
                "owner_phone_touched":False,"no_binary_or_key_published":True,
                "stage_a":"NO_GO"}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",required=True,type=Path)
    args=p.parse_args()
    try:
        print(json.dumps(run(args.xapk),sort_keys=True))
    except Exception as e:
        reason=str(e)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",reason):
            reason="PUBLISHERBASE_LEVEL_AB_PRIVATE_FAILURE"
        print(json.dumps({"verdict":"PUBLISHERBASE_LEVEL_AB_ABORTED",
            "reason":reason,"published_apk":False,
            "owner_phone_touched":False,"stage_a":"NO_GO"},sort_keys=True))
        sys.exit(2)
